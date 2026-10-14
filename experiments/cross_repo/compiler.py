"""Local synthetic projection experiment; no network, authority grants, or canon writes."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import html

DOMAINS = ("music", "arcade", "town")
BREADTH = ["creative medium", "capability ecosystem", "participatory world"]
VERSION = "cross-repo-fixture/0.1"


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def load(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    def bad_constant(value):
        raise ValueError("non-finite JSON value")
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs, parse_constant=bad_constant)


def compile_pack(source):
    source = copy.deepcopy(source)
    canonical(source)  # Reject non-finite data even when called directly.
    if set(source) != {"fixture_version", "id", "revision", "words", "attribution", "rights", "visibility", "status", "freshness", "conflicts", "branches", "extensions"}:
        raise ValueError("unknown or missing top-level fixture fields")
    if source["fixture_version"] != VERSION:
        raise ValueError("unsupported fixture version")
    if source["status"] != "candidate":
        raise ValueError("self-promotion denied")
    if source["rights"] != "synthetic-local-only" or source["visibility"] != "synthetic":
        raise ValueError("only synthetic local content permitted")
    if source["freshness"] != "fixture-pinned" or source["conflicts"] != []:
        raise ValueError("stale or conflicting input")
    for field in ("id", "revision", "words", "attribution"):
        if not isinstance(source[field], str) or not source[field].strip():
            raise ValueError("missing source identity, words, revision or attribution")
    if not isinstance(source["extensions"], dict):
        raise ValueError("extensions must be an object")
    if not isinstance(source["branches"], dict) or set(source["branches"]) != set(DOMAINS):
        raise ValueError("three supported branches required")
    for body in source["branches"].values():
        if not isinstance(body, str) or not body.strip():
            raise ValueError("branch must have authored meaning")
    source_hash = digest(source)
    projections = []
    for domain in DOMAINS:
        projections.append({
            "schema_version": "projection-envelope.v1",
            "object_key": source["id"] + "." + domain,
            "kind": "synthetic-creative-branch",
            "canonical_uri": None,
            "canonical_version": source["revision"],
            "content_hash": source_hash,
            "authority_class": "projection",
            "projection": {
                "status": "candidate", "domain": domain, "breadth": list(BREADTH),
                "words": source["words"], "attribution": source["attribution"],
                "interpretation": source["branches"][domain],
                "extensions": copy.deepcopy(source["extensions"]),
                "permissions": [], "live_effect": None,
            },
            "source_bindings": [{"source_id": source["id"], "revision": source["revision"], "sha256": source_hash}],
            "generated_at": "2026-10-14T00:00:00Z",
            "generator_ref": VERSION,
        })
    # Fixed timestamp belongs to this reproducibility fixture, not a runtime clock.
    return {"source": source, "source_sha256": source_hash, "projections": projections}


def write_pack(pack, destination):
    destination = Path(destination)
    if destination.exists():
        raise ValueError("destination exists; preserve generated edits and select a new path")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=".cross-repo-", dir=destination.parent))
    try:
        payload = {"pack.json": pack}
        for projection in pack["projections"]:
            payload[projection["projection"]["domain"] + ".json"] = projection
        hashes = {}
        for name, value in payload.items():
            encoded = (canonical(value) + "\n").encode("utf-8")
            (temp / name).write_bytes(encoded)
            hashes[name] = hashlib.sha256(encoded).hexdigest()
        styles = Path(__file__).with_name("styles")
        css = (styles / "quirk.css").read_text(encoding="utf-8")
        lock = load(styles / "style-lock.json")
        if hashlib.sha256(css.encode("utf-8")).hexdigest() != lock["output_sha256"]["quirk.css"]:
            raise ValueError("style projection digest mismatch")
        cards = "".join(
            '<section class="quirk-card"><h2>' + html.escape(p["projection"]["domain"].title()) +
            '</h2><p>' + html.escape(p["projection"]["interpretation"]) + '</p></section>'
            for p in pack["projections"])
        styled = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Quirk Branchwork</title><link rel="stylesheet" href="quirk.css"><body class="quirk-document"><p>Borrowed Tomorrow · candidate branches</p><h1>' + html.escape(pack["source"]["words"]) + '</h1><p>' + html.escape(pack["source"]["attribution"]) + '</p><div class="quirk-grid">' + cards + '</div><p>Source revision: ' + html.escape(pack["source"]["revision"]) + '</p><p><code>' + pack["source_sha256"] + '</code></p><p>No human preference, commitment or creative grade is recorded.</p></body></html>\n'
        for name, content in {"index.html": styled, "quirk.css": css, "style-lock.json": canonical(lock) + "\n"}.items():
            encoded = content.encode("utf-8")
            (temp / name).write_bytes(encoded)
            hashes[name] = hashlib.sha256(encoded).hexdigest()
        (temp / "receipt.json").write_text(canonical({
            "workflow": VERSION, "status": "candidate", "source_sha256": pack["source_sha256"],
            "output_sha256": hashes, "effect": "local synthetic files",
            "accepted": False, "reused": False, "observed_effect": None,
            "rollback": "remove only this new output directory; retain source and receipt",
        }) + "\n", encoding="utf-8")
        os.rename(temp, destination)
    except BaseException:
        shutil.rmtree(temp)
        raise


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    write_pack(compile_pack(load(args.source)), args.destination)
