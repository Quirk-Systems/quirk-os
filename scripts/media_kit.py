#!/usr/bin/env python3
"""Pack and verify an unsigned, candidate-only Quirk Media kit. Standard library only."""

from __future__ import annotations

import argparse
import copy
import hashlib
import html
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile
from typing import Any
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.0"
MAX_FILE = 64 * 1024 * 1024
MAX_TOTAL = 128 * 1024 * 1024
MAX_JSON = 1024 * 1024
MAX_MEMBERS = 66
EXTENSIONS = {".txt", ".md", ".json", ".srt", ".vtt", ".pdf", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".wav", ".mp3", ".m4a", ".flac", ".ogg", ".mp4", ".webm", ".mov"}
SCHEMA_FILES = ("media-kit-project.schema.json", "media-derivative.schema.json")
AUTHORITY = {"ceiling": "candidate", "publish_allowed": False, "graph_application_allowed": False, "training_allowed": False, "canon_promotion_allowed": False}


class KitError(ValueError):
    """An actionable input or integrity error; no admission is implied by success."""


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pairs_without_duplicates(pairs: list[tuple[str, Any]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise KitError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json(data: bytes, label: str) -> Any:
    if len(data) > MAX_JSON:
        raise KitError(f"{label}: JSON exceeds the 1 MiB limit")
    try:
        return json.loads(data, object_pairs_hook=pairs_without_duplicates,
                          parse_constant=lambda value: (_ for _ in ()).throw(KitError(f"Non-finite JSON value: {value}")))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise KitError(f"{label}: invalid JSON") from exc


def validate_shape(value: Any, schema: dict, schemas: dict, where: str = "project") -> None:
    """Enforce the audited subset used by these two schemas; fail on new keywords.

    This is not a general JSON Schema engine. References resolve only to the two
    bundled files. A future schema feature needs implementation and fixtures.
    """
    supported = {"$schema", "$id", "$ref", "title", "description", "type", "properties", "required", "additionalProperties", "items", "minItems", "maxItems", "uniqueItems", "minLength", "maxLength", "pattern", "enum", "const"}
    unknown = set(schema) - supported
    if unknown:
        raise KitError(f"Unsupported schema keywords at {where}: {sorted(unknown)}")
    if "$ref" in schema:
        if set(schema) != {"$ref"} or schema["$ref"] not in schemas:
            raise KitError(f"Unsupported schema reference at {where}")
        validate_shape(value, schemas[schema["$ref"]], schemas, where)
        return
    kinds = {"object": dict, "array": list, "string": str, "boolean": bool}
    expected = schema.get("type")
    if expected is not None and (expected not in kinds or type(value) is not kinds[expected]):
        raise KitError(f"{where}: expected {expected}")
    if "const" in schema and canonical(value) != canonical(schema["const"]):
        raise KitError(f"{where}: must remain {schema['const']!r}")
    if expected is None and "const" in schema and set(schema) <= {"const", "title", "description"}:
        return
    if expected not in kinds or type(value) is not kinds[expected]:
        raise KitError(f"{where}: expected {expected}")
    if "enum" in schema and not any(canonical(value) == canonical(item) for item in schema["enum"]):
        raise KitError(f"{where}: unsupported value")
    if expected == "object":
        missing = set(schema.get("required", [])) - set(value)
        extra = set(value) - set(schema.get("properties", {}))
        if missing or (schema.get("additionalProperties") is False and extra):
            raise KitError(f"{where}: missing {sorted(missing)}, unexpected {sorted(extra)}")
        for key, item in value.items():
            if key in schema.get("properties", {}):
                validate_shape(item, schema["properties"][key], schemas, f"{where}.{key}")
    elif expected == "array":
        if not schema.get("minItems", 0) <= len(value) <= schema.get("maxItems", 256):
            raise KitError(f"{where}: invalid item count")
        if schema.get("uniqueItems") and len({canonical(item) for item in value}) != len(value):
            raise KitError(f"{where}: duplicate items")
        for index, item in enumerate(value):
            validate_shape(item, schema["items"], schemas, f"{where}[{index}]")
    elif expected == "string":
        if not schema.get("minLength", 0) <= len(value) <= schema.get("maxLength", 8192):
            raise KitError(f"{where}: invalid text length")
        if schema.get("minLength", 0) and not value.strip():
            raise KitError(f"{where}: text must not be blank")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            raise KitError(f"{where}: invalid text format")


def safe_relative(path: str) -> PurePosixPath:
    if not isinstance(path, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._ /-]*", path):
        raise KitError(f"Unsafe relative file path: {path!r}")
    parts = path.split("/")
    if any(part in {"", ".", ".."} or part.endswith((" ", ".")) for part in parts):
        raise KitError(f"Unsafe relative file path: {path!r}")
    parsed = PurePosixPath(path)
    if parsed.suffix.lower() not in EXTENSIONS:
        raise KitError(f"Unsupported file type: {path}. Use a media, text, caption, JSON, or PDF file.")
    return parsed


def validate_project(project: Any) -> None:
    schemas = {name: parse_json((ROOT / "schemas" / name).read_bytes(), name) for name in SCHEMA_FILES}
    validate_shape(project, schemas[SCHEMA_FILES[0]], schemas)
    source_ids = [source["id"] for source in project["sources"]]
    derivative_ids = [item["metadata"]["id"] for item in project["derivatives"]]
    if len(set(source_ids)) != len(source_ids) or len(set(derivative_ids)) != len(derivative_ids):
        raise KitError("Source and derivative IDs must be unique within their groups")
    sources = {source["id"]: source for source in project["sources"]}
    paths = []
    for item in project["sources"] + project["derivatives"]:
        safe_relative(item["path"])
        paths.append(item["path"].casefold())
    if len(set(paths)) != len(paths):
        raise KitError("Each source and derivative must name a distinct file path")
    for item in project["derivatives"]:
        source = sources.get(item["source_id"])
        if source is None:
            raise KitError(f"{item['metadata']['id']}: missing source {item['source_id']}")
        metadata = item["metadata"]
        expected = {key: source[key] for key in ("object_ref", "version", "receipt_ref")}
        if metadata["canonical_source"] != expected:
            raise KitError(f"{metadata['id']}: source identity, version, or receipt does not match")
        if metadata["status"] not in {"draft", "review"} or "release_receipt_ref" in metadata:
            raise KitError(f"{metadata['id']}: a candidate kit accepts only draft/review derivatives without a release receipt")
    if project["selection"]["derivative_id"] not in derivative_ids:
        raise KitError("The unsigned selection must refer to an included derivative")


def layout(project: dict) -> list[dict]:
    result = []
    groups = [("source", project["sources"]), ("derivative", project["derivatives"])]
    for role, items in groups:
        for item in items:
            name = re.sub(r"[^A-Za-z0-9._-]", "-", PurePosixPath(item["path"]).name)
            result.append({"ref": item["id"] if role == "source" else item["metadata"]["id"], "role": role,
                           "archive_path": f"assets/{len(result):03d}-{name}", "sha256": item["sha256"]})
    return result


def read_declared(root: Path, relative: str) -> bytes:
    parsed = safe_relative(relative)
    path = root
    for part in parsed.parts:
        path = path / part
        if path.is_symlink():
            raise KitError(f"Symlinks are not packaged: {relative}")
    if not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
        raise KitError(f"Missing regular file: {relative}")
    with path.open("rb") as handle:
        data = handle.read(MAX_FILE + 1)
    if len(data) > MAX_FILE:
        raise KitError(f"{relative}: file exceeds the 64 MiB limit")
    return data


def render_index(manifest: dict) -> bytes:
    """A script-free view. User text is escaped; links use generated archive paths."""
    project = manifest["project"]
    selection = project["selection"]
    entries = {item["ref"]: item for item in manifest["files"]}
    esc = lambda value: html.escape(str(value), quote=True)
    def link(ref: str, label: str) -> str:
        return f'<a download href="{esc(entries[ref]["archive_path"])}">{esc(label)}</a>'
    source_cards = []
    for source in project["sources"]:
        source_cards.append(f'''<article class="card"><div class="eyebrow">SOURCE · {esc(source['source_status'])}</div>
<h3>{link(source['id'], PurePosixPath(source['path']).name)}</h3><p>{esc(source['rights_note'])}</p>
<details><summary>Inspect identity and fingerprint</summary><dl><dt>Object</dt><dd>{esc(source['object_ref'])}</dd><dt>Version</dt><dd>{esc(source['version'])}</dd><dt>Capture reference</dt><dd>{esc(source['receipt_ref'])}</dd><dt>SHA-256</dt><dd><code>{esc(source['sha256'])}</code></dd></dl></details></article>''')
    derivative_cards = []
    for item in project["derivatives"]:
        meta = item["metadata"]
        chosen = meta["id"] == selection["derivative_id"]
        derivative_cards.append(f'''<article class="card {'chosen' if chosen else ''}"><div class="eyebrow">{'SELECTED CANDIDATE' if chosen else 'ALTERNATIVE'} · {esc(meta['medium'])}</div>
<h3>{link(meta['id'], PurePosixPath(item['path']).name)}</h3><p>{esc(meta['job'])}</p>
<p class="muted">For {esc(', '.join(meta['audience']))} · Adds {esc(', '.join(meta['medium_native_affordance']))}</p>
<p>Source: {link(item['source_id'], item['source_id'])}</p><details><summary>Inspect changes and review needs</summary>
<dl><dt>Preserved</dt><dd>{esc('; '.join(meta['claims']['preserved']) or 'None declared')}</dd><dt>Added</dt><dd>{esc('; '.join(meta['claims']['added']) or 'None declared')}</dd><dt>Omitted</dt><dd>{esc('; '.join(meta['claims']['omitted']) or 'None declared')}</dd><dt>Rights check</dt><dd>{'Declared checked; independently unverified' if meta['rights']['source_permissions_verified'] else 'Open'}</dd><dt>Accessibility</dt><dd>{esc(meta['accessibility']['status'])} (declared)</dd><dt>SHA-256</dt><dd><code>{esc(item['sha256'])}</code></dd></dl></details></article>''')
    output = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>{esc(project['title'])} · Quirk Media</title><style>
:root{{color-scheme:light;--ink:#172c32;--paper:#f4f2e9;--line:#cad0c7;--muted:#4c6265;--accent:#d4ef91}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:17px/1.55 system-ui,sans-serif}}main{{max-width:1080px;margin:auto;padding:32px 24px 64px}}
header{{display:flex;align-items:center;justify-content:space-between;gap:20px;border-bottom:1px solid var(--line);padding-bottom:18px}}nav{{display:flex;gap:18px;flex-wrap:wrap}}a{{color:#135b58;text-underline-offset:4px}}a:focus-visible,summary:focus-visible{{outline:3px solid #346721;outline-offset:5px}}h1{{font-size:clamp(2.1rem,6vw,4rem);line-height:1.05;letter-spacing:-.04em;max-width:850px;margin:28px 0 16px}}h2{{font-size:1.6rem;margin:36px 0 14px}}h3{{font-size:1.1rem;margin:10px 0}}p{{margin:12px 0}}.eyebrow{{font-size:.76rem;letter-spacing:.12em;font-weight:750}}.muted{{color:var(--muted)}}.lead{{max-width:750px;font-size:1.15rem}}.badges{{display:flex;gap:8px;flex-wrap:wrap;margin:24px 0}}.badge{{background:white;border:1px solid var(--line);padding:5px 10px;border-radius:4px;font-size:.8rem;font-weight:650}}.choice{{padding:26px;background:var(--ink);color:#fff;border-radius:12px}}.choice a{{color:var(--accent)}}.choice .eyebrow{{color:var(--accent)}}.choice p{{max-width:800px}}.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}}.card{{padding:22px;background:#fff;border:1px solid var(--line);border-radius:10px;overflow-wrap:anywhere}}.chosen{{border-top:5px solid #477b27}}details{{border-top:1px solid var(--line);margin-top:18px;padding-top:12px}}summary{{cursor:pointer;font-weight:600}}dl{{font-size:.9rem}}dt{{font-weight:650;margin-top:12px}}dd{{margin:2px 0 0;overflow-wrap:anywhere}}code{{font-size:.82rem;overflow-wrap:anywhere}}.foot{{margin-top:36px;border-top:1px solid var(--line);padding-top:20px;font-size:.9rem}}@media(max-width:650px){{main{{padding:22px 16px 44px}}header{{align-items:flex-start;flex-direction:column;gap:12px}}.grid{{grid-template-columns:1fr}}.choice,.card{{padding:20px}}}}
</style></head><body><main><header><strong>QUIRK / MEDIA</strong><nav aria-label="Kit sections"><a href="#choice">Choice</a><a href="#sources">Sources</a><a href="#versions">Versions</a></nav></header>
<h1>{esc(project['title'])}</h1><p class="lead">{esc(project['purpose'])}</p>
<div class="badges"><span class="badge">CANDIDATE</span><span class="badge">UNSIGNED</span><span class="badge">{len(project['sources'])} source(s) · {len(project['derivatives'])} version(s)</span></div>
<section id="choice" class="choice"><div class="eyebrow">THE CHOICE THAT TRAVELS WITH THE FILES</div><h2>{esc(selection['derivative_id'])}</h2><p>{esc(selection['rationale'])}</p><p><strong>Finished when:</strong> {esc(selection['completion_condition'])}</p><p>Recorded by {esc(selection['actor']['id'])} · {esc(selection['actor']['type'])} · self-declared and unsigned.</p></section>
<section id="sources"><h2>Where did this come from?</h2><p class="muted">Included source files, pinned versions, and capture references. Status and rights notes are declarations.</p><div class="grid">{''.join(source_cards)}</div></section>
<section id="versions"><h2>What came from it?</h2><div class="grid">{''.join(derivative_cards)}</div></section>
<section class="foot"><h2>Reopen with the whole kit</h2><p>Extract the ZIP into one folder and keep this page beside <code>assets/</code> and <code>kit-manifest.json</code>. The file links work offline. Downloads may open in your device’s file viewer.</p><p>After transfer, run <code>python3 scripts/media_kit.py verify PATH_TO_KIT.zip</code> from the Quirk OS checkout. This checks the included bytes and selection record against the manifest; the unsigned manifest does not authenticate an author or approve a release.</p><p>Publishing, Preference Graph application, training, and canon promotion remain disabled. Human benefit has not been observed by this packer.</p><details><summary>Kit fingerprint</summary><p><code>{esc(manifest['content_sha256'])}</code></p><p>Quirk Media Kit {VERSION} · {esc(project['id'])}</p></details></section>
</main></body></html>'''
    return output.encode("utf-8")


def receipt(manifest: dict, operation: str) -> dict:
    project = manifest["project"]
    return {"schema_version": "media-kit-check.v1", "operation": operation,
            "kit_id": project["id"], "tool_version": VERSION, "integrity": "verified",
            "scope": "local package consistency; not authenticity, source truth, rights clearance, or release approval",
            "file_count": len(manifest["files"]), "file_bytes": sum(item["size_bytes"] for item in manifest["files"]),
            "content_sha256": manifest["content_sha256"], "project_sha256": manifest["project_sha256"],
            "selection_actor_type": project["selection"]["actor"]["type"], "signature_status": "unsigned",
            "authority": copy.deepcopy(AUTHORITY), "human_benefit": "unobserved",
            "open_reviews": {"rights": [item["metadata"]["id"] for item in project["derivatives"] if not item["metadata"]["rights"]["source_permissions_verified"]],
                             "accessibility": [item["metadata"]["id"] for item in project["derivatives"] if item["metadata"]["accessibility"]["status"] != "passed"]}}


def pack(project: dict, root: Path, output: Path) -> dict:
    validate_project(project)
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise KitError("--root must be a directory")
    if output.exists() or output.is_symlink():
        raise KitError("Output already exists; choose a new filename to preserve history")
    files = layout(project)
    payloads = {}
    total = 0
    for entry, item in zip(files, project["sources"] + project["derivatives"]):
        data = read_declared(root, item["path"])
        if digest(data) != item["sha256"]:
            raise KitError(f"{item['path']}: SHA-256 mismatch; inspect the changed file and deliberately repin it")
        total += len(data)
        if total > MAX_TOTAL:
            raise KitError("Kit exceeds the 128 MiB total file limit")
        entry["size_bytes"] = len(data)
        payloads[entry["archive_path"]] = data
    core = {"schema_version": "media-kit.v1", "tool_version": VERSION, "project": copy.deepcopy(project),
            "project_sha256": digest(canonical(project)), "files": files}
    manifest = {**core, "content_sha256": digest(canonical(core))}
    manifest_bytes = canonical(manifest)
    if len(manifest_bytes) > MAX_JSON:
        raise KitError("Manifest exceeds the 1 MiB limit")
    payloads["kit-manifest.json"] = manifest_bytes
    payloads["index.html"] = render_index(manifest)
    if len(payloads["index.html"]) > MAX_JSON:
        raise KitError("Rendered index exceeds the 1 MiB limit")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="quirk-media-", dir=output.parent) as temporary:
        pending = Path(temporary) / "kit.zip"
        with zipfile.ZipFile(pending, "w", compression=zipfile.ZIP_STORED) as archive:
            for name, data in sorted(payloads.items()):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data)
        verified = verify(pending)
        # Same-filesystem, exclusive publication of the private output; never overwrite.
        os.link(pending, output)
    return {**verified, "operation": "pack"}


def verify(path: Path) -> dict:
    if path.stat().st_size > MAX_TOTAL + 4 * MAX_JSON:
        raise KitError("ZIP exceeds the bounded archive size")
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            names = [item.filename for item in members]
            if len(members) > MAX_MEMBERS or len(set(names)) != len(names):
                raise KitError("Too many or duplicate ZIP members")
            total = 0
            for member in members:
                if member.is_dir() or member.flag_bits & 1 or member.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
                    raise KitError("Unsupported ZIP member")
                mode = member.external_attr >> 16
                if stat.S_IFMT(mode) not in {0, stat.S_IFREG}:
                    raise KitError("ZIP symlinks and special files are not accepted")
                limit = MAX_JSON if member.filename in {"kit-manifest.json", "index.html"} else MAX_FILE
                if member.file_size > limit:
                    raise KitError("ZIP member exceeds its size limit")
                total += member.file_size
            if total > MAX_TOTAL + 2 * MAX_JSON:
                raise KitError("ZIP exceeds its uncompressed size limit")
            if "kit-manifest.json" not in names:
                raise KitError("Missing kit-manifest.json")
            manifest = parse_json(archive.read("kit-manifest.json"), "kit manifest")
            fields = {"schema_version", "tool_version", "project", "project_sha256", "files", "content_sha256"}
            if type(manifest) is not dict or set(manifest) != fields:
                raise KitError("Invalid manifest fields")
            if manifest["schema_version"] != "media-kit.v1" or manifest["tool_version"] != VERSION:
                raise KitError("Unsupported kit/tool version; use its matching verifier")
            project = manifest["project"]
            validate_project(project)
            if manifest["project_sha256"] != digest(canonical(project)):
                raise KitError("Project or unsigned selection fingerprint mismatch")
            core = {key: value for key, value in manifest.items() if key != "content_sha256"}
            if manifest["content_sha256"] != digest(canonical(core)):
                raise KitError("Manifest fingerprint mismatch")
            expected = layout(project)
            if type(manifest["files"]) is not list or len(manifest["files"]) != len(expected):
                raise KitError("Manifest file inventory does not match the project")
            expected_names = {"kit-manifest.json", "index.html"}
            asset_total = 0
            for entry, planned in zip(manifest["files"], expected):
                if type(entry) is not dict or set(entry) != set(planned) | {"size_bytes"}:
                    raise KitError("Invalid file inventory fields")
                if any(entry[key] != value for key, value in planned.items()):
                    raise KitError("File inventory identity or path mismatch")
                if type(entry["size_bytes"]) is not int or not 0 <= entry["size_bytes"] <= MAX_FILE:
                    raise KitError("Invalid file byte count")
                name = entry["archive_path"]
                expected_names.add(name)
                if name not in names:
                    raise KitError(f"Missing included file: {name}")
                data = archive.read(name)
                if len(data) != entry["size_bytes"] or digest(data) != entry["sha256"]:
                    raise KitError(f"Included file changed: {name}")
                asset_total += len(data)
            if asset_total > MAX_TOTAL:
                raise KitError("Kit exceeds the total file limit")
            if set(names) != expected_names:
                raise KitError("Missing or unlisted ZIP members")
            if archive.read("index.html") != render_index(manifest):
                raise KitError("Readable index differs from the verified manifest")
    except (zipfile.BadZipFile, KeyError, RuntimeError, NotImplementedError, EOFError, zlib.error) as exc:
        raise KitError(f"Unreadable or incomplete ZIP: {exc}") from exc
    return receipt(manifest, "verify")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("pack", help="Create a new candidate ZIP without overwriting an earlier kit")
    build.add_argument("--project", type=Path, required=True)
    build.add_argument("--root", type=Path, required=True, help="Explicit directory containing the declared files")
    build.add_argument("--output", type=Path, required=True)
    check = commands.add_parser("verify", help="Check a kit without extracting or running its contents")
    check.add_argument("kit", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "pack":
            with args.project.open("rb") as handle:
                project = parse_json(handle.read(MAX_JSON + 1), "project")
            result = pack(project, args.root, args.output)
        else:
            result = verify(args.kit)
        print(json.dumps(result, indent=2))
        return 0
    except (KitError, OSError, ValueError, RecursionError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
