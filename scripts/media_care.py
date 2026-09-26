#!/usr/bin/env python3
"""Inspect a verified Quirk Media kit and its candidate care record, without extraction."""

from __future__ import annotations

import argparse
import copy
from datetime import date
import html
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile

import media_kit as kit

REGISTRY_PATH = kit.ROOT / "docs/media-kit/classification.v1.json"
SCHEMA_PATH = kit.ROOT / "schemas/media-care.schema.json"
COMPANION_TYPES = {"captions": {".srt", ".vtt"}, "transcript": {".txt", ".md"},
                   "speaker_notes": {".txt", ".md"}, "audio_description": {".txt", ".md"}}


def calendar_date(value: str) -> date:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise kit.KitError("Dates must use YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise kit.KitError(f"Invalid calendar date: {value}") from exc


def classification() -> dict:
    registry = kit.parse_json(REGISTRY_PATH.read_bytes(), "classification registry")
    expected = {"image", "video", "audio", "presentation", "document", "data", "unknown"}
    if registry.get("schema_version") != "media-classification.v1" or set(registry.get("families", {})) != expected:
        raise kit.KitError("Unsupported classification registry")
    extensions = [ext for family in registry["families"].values() for ext in family["extensions"]]
    if len(set(extensions)) != len(extensions) or set(extensions) != kit.EXTENSIONS:
        raise kit.KitError("Classification registry and supported file extensions disagree")
    for family in registry["families"].values():
        if set(family["review_material"]) - (set(COMPANION_TYPES) | {"alt_text"}):
            raise kit.KitError("Unsupported review material in classification registry")
    return registry


def validate_care(care: dict, manifest: dict) -> dict:
    schema = kit.parse_json(SCHEMA_PATH.read_bytes(), "media care schema")
    kit.validate_shape(care, schema, {}, "care")
    if care["kit_content_sha256"] != manifest["content_sha256"]:
        raise kit.KitError("Care record belongs to a different kit; inspect and deliberately rebind it")
    refs = [item["asset_ref"] for item in care["assets"]]
    if len(set(refs)) != len(refs) or set(refs) != {item["ref"] for item in manifest["files"]}:
        raise kit.KitError("Care inventory must cover every included asset exactly once")
    records = {item["asset_ref"]: item for item in care["assets"]}
    for ref, item in records.items():
        calendar_date(item["review_on"])
        replacement = item.get("replacement_ref")
        if item["state"] == "superseded" and replacement is None:
            raise kit.KitError(f"{ref}: superseded assets need an included replacement")
        if replacement is not None and item["state"] != "superseded":
            raise kit.KitError(f"{ref}: replacement_ref is only valid for a superseded asset")
        if replacement is not None and (replacement not in records or replacement == ref):
            raise kit.KitError(f"{ref}: missing or self-referencing replacement")
        for target in item.get("companions", {}).values():
            if target not in records or target == ref:
                raise kit.KitError(f"{ref}: companions must refer to another included asset")
    for ref in records:
        seen = set()
        cursor = ref
        while cursor in records:
            if cursor in seen:
                raise kit.KitError(f"{ref}: replacement cycle")
            seen.add(cursor)
            cursor = records[cursor].get("replacement_ref")
    return records


def inspect(archive_path: Path, care: dict, as_of: str) -> dict:
    day = calendar_date(as_of)
    registry = classification()
    findings = []

    def flag(code: str, ref: str | None, message: str) -> None:
        findings.append({"code": code, "asset_ref": ref, "message": message})

    # The same open archive supplies verification and companion inspection.
    # No extraction, network request, media decoding, or embedded code execution.
    with kit.verified_archive(archive_path) as (manifest, archive):
        records = validate_care(care, manifest)
        entries = {item["ref"]: item for item in manifest["files"]}
        project = manifest["project"]
        selected = project["selection"]["derivative_id"]
        dependencies = {ref: set(item.get("companions", {}).values()) for ref, item in records.items()}
        for item in project["derivatives"]:
            dependencies[item["metadata"]["id"]].add(item["source_id"])
        selection_refs = set()
        pending = [selected]
        while pending:
            ref = pending.pop()
            if ref not in selection_refs:
                selection_refs.add(ref)
                pending.extend(dependencies[ref] - selection_refs)
        if care["maintenance_owner"].strip().casefold() == "unassigned":
            flag("owner_needed", None, "Nominate a maintenance owner and record their acceptance separately.")
        titles = {}
        for ref, item in records.items():
            titles.setdefault(item["title"].strip().casefold(), []).append(ref)
        for refs in titles.values():
            if len(refs) > 1:
                for ref in refs:
                    flag("ambiguous_title", ref, "This title is shared by another asset; add its purpose or version.")
        assets = []
        for ref, entry in entries.items():
            item = records[ref]
            suffix = PurePosixPath(entry["archive_path"]).suffix.lower()
            suggested = next((name for name, family in registry["families"].items() if suffix in family["extensions"]), "unknown")
            if item["family"] != suggested:
                flag("family_mismatch", ref, f"Declared family {item['family']} differs from extension evidence {suggested}; inspect the actual file.")
            if item["origin"] == "unknown":
                flag("origin_unknown", ref, "Origin is unknown; inspect source evidence before describing how this was made.")
            if calendar_date(item["review_on"]) <= day:
                flag("review_due", ref, f"Care review is due on {item['review_on']}; inspect before continued use.")
            if item["state"] != "candidate":
                flag("asset_" + item["state"], ref, item["state_reason"])
            if item["sensitivity"] != "public":
                flag("sharing_review_needed", ref, f"Sensitivity is {item['sensitivity']}. The kit is unencrypted; choose an appropriate storage and sharing boundary.")
            companion_evidence = {}
            for kind, target in item.get("companions", {}).items():
                target_entry = entries[target]
                target_suffix = PurePosixPath(target_entry["archive_path"]).suffix.lower()
                readable = False
                if target_suffix in COMPANION_TYPES[kind] and target_entry["size_bytes"] <= kit.MAX_JSON:
                    try:
                        content = archive.read(target_entry["archive_path"]).decode("utf-8-sig")
                        readable = bool(content.strip()) and "\x00" not in content
                    except UnicodeError:
                        pass
                companion_evidence[kind] = {"asset_ref": target, "presence": "readable_text" if readable else "unusable_text", "quality": "unverified"}
                if not readable:
                    flag("companion_unusable", ref, f"{kind}: {target} must be nonempty UTF-8 text in a supported format, at most 1 MiB.")
                target_care = records[target]
                if target_care["state"] != "candidate" or calendar_date(target_care["review_on"]) <= day:
                    flag("companion_needs_review", ref, f"{kind}: linked asset {target} is due for review or is not a current candidate.")
            # A misleading declared family cannot hide extension-based review needs.
            required = set(registry["families"][suggested]["review_material"]) | set(registry["families"][item["family"]]["review_material"])
            for kind in sorted(required):
                present = bool(item.get("alt_text")) if kind == "alt_text" else kind in companion_evidence
                if not present:
                    flag("review_material_missing", ref, f"Provide {kind.replace('_', ' ')} for review, or record a human explanation of its applicability separately.")
            if suffix in {".pdf", ".pptx", ".odp"}:
                flag("document_review_needed", ref, "Inspect reading order, visual descriptions, fonts, links, and embedded objects in a suitable viewer; none were evaluated here.")
            assets.append({"asset_ref": ref, "title": item["title"], "archive_path": entry["archive_path"],
                           "provenance_role": entry["role"], "family": item["family"], "extension_family": suggested,
                           "origin": item["origin"], "use_role": item["use_role"], "sensitivity": item["sensitivity"],
                           "state": item["state"], "state_reason": item["state_reason"], "review_on": item["review_on"],
                           "replacement_ref": item.get("replacement_ref"), "selected": ref == selected,
                           "depends_on": sorted(dependencies[ref]),
                           "alt_text_presence": "declared" if item.get("alt_text") else "absent",
                           "companions": companion_evidence})
        for derivative in project["derivatives"]:
            meta = derivative["metadata"]
            ref = meta["id"]
            source = records[derivative["source_id"]]
            if source["state"] != "candidate" or calendar_date(source["review_on"]) <= day:
                flag("source_needs_review", ref, f"Primary source {source['asset_ref']} needs care; review this derivative too. No file was changed.")
            if not meta["rights"]["source_permissions_verified"]:
                flag("rights_review_open", ref, "Source permissions have not been declared verified; inspect rights evidence before sharing.")
            if meta["accessibility"]["status"] != "passed":
                flag("accessibility_review_open", ref, "Accessibility review remains open. Companion presence alone cannot close it.")
        return {"schema_version": "media-care-check.v1", "tool_version": kit.VERSION, "as_of": as_of,
                "kit_id": project["id"], "kit_content_sha256": manifest["content_sha256"],
                "care_sha256": kit.digest(kit.canonical(care)), "classification_sha256": kit.digest(kit.canonical(registry)),
                "integrity": "verified", "status": "needs_attention" if findings else "prepared_for_human_review",
                "authority": copy.deepcopy(kit.AUTHORITY), "human_benefit": "unobserved",
                "scope": "Internal consistency, declared care, extension evidence, and companion text presence; not authenticity, decoding, malware scanning, rights clearance, accessibility quality, or release approval.",
                "maintenance_owner": care["maintenance_owner"], "owner_acceptance": "unverified",
                "proposed_by": care["proposed_by"], "selection": {"asset_ref": selected,
                    "needs_attention": any(item["asset_ref"] is None or item["asset_ref"] in selection_refs for item in findings),
                    "review_refs": sorted(selection_refs),
                    "actor_type": project["selection"]["actor"]["type"], "signature_status": "unsigned"},
                "assets": assets, "findings": findings, "art_direction": copy.deepcopy(care["art_direction"])}


def render_report(report: dict) -> bytes:
    esc = lambda value: html.escape(str(value), quote=True)
    rows = "".join(f"<tr><th scope='row'>{esc(item['title'])}<small>{esc(item['asset_ref'])}{' · SELECTED' if item['selected'] else ''}</small></th><td>{esc(item['family'])}<small>{esc(item['origin'])}</small></td><td>{esc(item['use_role'])}<small>{esc(item['sensitivity'])}</small></td><td>{esc(item['state'])}<small>Review {esc(item['review_on'])}</small></td></tr>" for item in report["assets"])
    titles = {item["asset_ref"]: item["title"] for item in report["assets"]}
    findings = "".join(f"<li><strong>{esc(titles.get(item['asset_ref'], 'Whole kit'))}</strong> — {esc(item['message'])}<small>{esc(item['code'])}</small></li>" for item in report["findings"]) or "<li>No mechanical care findings. Human review remains open.</li>"
    art = report["art_direction"]
    bullets = lambda values: "".join(f"<li>{esc(value)}</li>" for value in values)
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>Quirk Media — care review</title><style>
:root{{color-scheme:light}}*{{box-sizing:border-box}}body{{margin:0;background:#f4f2e9;color:#172c32;font:17px/1.55 system-ui,sans-serif}}main{{max-width:1060px;margin:auto;padding:32px 24px 64px}}h1{{font-size:clamp(2.1rem,6vw,3.7rem);line-height:1.1;letter-spacing:-.03em}}h2{{margin-top:36px}}.lead{{max-width:760px;font-size:1.15rem}}.summary{{padding:22px;background:#172c32;color:white;border-radius:10px}}.summary strong{{color:#d4ef91}}.scroll{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;background:#fff}}th,td{{text-align:left;vertical-align:top;padding:16px;border-bottom:1px solid #cad0c7;overflow-wrap:anywhere}}thead th{{font-size:.85rem}}small{{display:block;font-size:.8rem;font-weight:400}}li{{margin:14px 0}}.craft{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}code{{font-size:.8rem;overflow-wrap:anywhere}}details{{margin-top:32px;border-top:1px solid #cad0c7;padding-top:18px}}summary:focus-visible{{outline:3px solid #346721;outline-offset:4px}}@media(max-width:650px){{main{{padding:22px 16px 44px}}.craft{{grid-template-columns:1fr}}th,td{{padding:10px}}}}
</style></head><body><main><p>QUIRK / MEDIA · CANDIDATE CARE REVIEW</p><h1>Keep the work worth carrying.</h1>
<p class="lead">Readable names, declared care, and the questions a person still needs to answer. This is a saved inspection as of {esc(report['as_of'])}.</p>
<div class="summary"><strong>{esc(report['status'].replace('_', ' ').capitalize())}</strong><p>{len(report['assets'])} assets · {len(report['findings'])} findings. Maintenance owner: {esc(report['maintenance_owner'])} (acceptance unverified).</p><p>Selected: {esc(titles[report['selection']['asset_ref']])}. {'Inspect its care findings before continued use.' if report['selection']['needs_attention'] else 'Prepared for a person to judge.'}</p></div>
<h2>What exists</h2><div class="scroll"><table><thead><tr><th scope="col">Asset / identity</th><th scope="col">Family / origin</th><th scope="col">Use / sensitivity</th><th scope="col">State / review</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>What needs attention</h2><ul>{findings}</ul>
<h2>What the work should feel and do</h2><p>{esc(art['intent'])}</p><div class="craft"><div><h3>Preserve</h3><ul>{bullets(art['preserve'])}</ul></div><div><h3>Avoid</h3><ul>{bullets(art['avoid'])}</ul></div></div><h3>Ask a person</h3><ol>{bullets(art['craft_questions'])}</ol>
<p>Human judgment and benefit remain unobserved. This report grants no publishing, graph application, training, or canon authority.</p>
<details><summary>Inspect evidence and limits</summary><p>{esc(report['scope'])}</p><p>Kit: <code>{esc(report['kit_content_sha256'])}</code></p><p>Care: <code>{esc(report['care_sha256'])}</code></p><p>Classification: <code>{esc(report['classification_sha256'])}</code></p><p>Quirk Media Kit {esc(report['tool_version'])}. To inspect again, run the care inspector with the kit, its care record, and an explicit review date. The page itself performs no live checks.</p></details></main></body></html>"""
    data = page.encode("utf-8")
    if len(data) > kit.MAX_JSON:
        raise kit.KitError("Care page exceeds the 1 MiB limit")
    return data


def write_new(path: Path, data: bytes) -> None:
    if path.exists() or path.is_symlink():
        raise kit.KitError("Report output already exists; choose a new filename")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="quirk-care-", dir=path.parent) as temporary:
        pending = Path(temporary) / "report"
        with os.fdopen(os.open(pending, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "wb") as handle:
            handle.write(data)
        os.link(pending, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("inspect", help="Read care declarations against the exact verified kit")
    command.add_argument("kit", type=Path)
    command.add_argument("--care", type=Path, required=True)
    command.add_argument("--as-of", required=True, help="Explicit YYYY-MM-DD; no clock or background scheduler")
    command.add_argument("--html", type=Path, help="Optionally save a new script-free report without overwriting")
    args = parser.parse_args(argv)
    try:
        with args.care.open("rb") as handle:
            care = kit.parse_json(handle.read(kit.MAX_JSON + 1), "care record")
        result = inspect(args.kit, care, args.as_of)
        if args.html:
            write_new(args.html, render_report(result))
        print(json.dumps(result, indent=2))
        return 0  # Findings are data, not approval. Nonzero means inspection failed.
    except (kit.KitError, OSError, ValueError, RecursionError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
