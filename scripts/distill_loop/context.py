"""Select which distilled candidates the next run may see.

This is the Hermes "loads next time" step with governance attached: only
candidates with a `promoted` ledger state whose on-disk digests still match
their ledger provenance are offered as context sources. Distilled-but-unreviewed
candidates are listed as pending so they are visible, never loaded. Being a
context source is not runtime admission; the runtime loader still rejects every
candidate version.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sync_control_plane.skill_runtime import validate_manifest_integrity

from .common import CANDIDATE_PREFIX
from .ledger import verify_ledger


def next_run_context(ledger: dict[str, Any], *, root: Path | None = None) -> dict[str, Any]:
    ledger_errors = verify_ledger(ledger)
    context: dict[str, Any] = {
        "api_version": "quirk.dev/distill-run-context/v1alpha1",
        "kind": "DistillRunContext",
        "authority": {
            "runtime_authority": False,
            "canon_promotion": False,
            "admission_effect": "none",
            "meaning": "promoted distilled candidates offered as candidate source context only",
        },
        "ledger_sha256": ledger.get("ledger_sha256"),
        "ledger_errors": ledger_errors,
        "context_sources": [],
        "pending_review": [],
        "rejected": [],
        "quarantined": [],
    }
    if ledger_errors:
        return context

    latest: dict[str, dict[str, Any]] = {}
    for entry in ledger.get("entries", []):
        candidate_id = entry.get("candidate_id")
        if not candidate_id or not candidate_id.startswith(CANDIDATE_PREFIX):
            continue
        kind = entry.get("kind")
        if kind == "distilled":
            latest.setdefault(candidate_id, {"state": "distilled", "distilled": entry, "decision": None})
        elif kind in {"promoted", "rejected"} and candidate_id in latest:
            latest[candidate_id]["state"] = kind
            latest[candidate_id]["decision"] = entry

    for candidate_id in sorted(latest):
        record = latest[candidate_id]
        state = record["state"]
        if state == "distilled":
            context["pending_review"].append(candidate_id)
            continue
        if state == "rejected":
            context["rejected"].append(candidate_id)
            continue
        decision = record["decision"]
        refs = decision.get("refs", {})
        source = {
            "candidate_id": candidate_id,
            "state": "promoted",
            "tier": "reviewed_candidate",
            "source_path": f"skills/{candidate_id}/SKILL.md",
            "manifest_path": f"skills/{candidate_id}/manifest.json",
            "manifest_sha256": refs.get("manifest_sha256"),
            "source_blob_sha": refs.get("source_blob_sha"),
            "promotion_receipt_ref": refs.get("promotion_receipt_ref"),
            "runtime_loadable": False,
        }
        if root is not None:
            problems = _on_disk_problems(root, source)
            if problems:
                context["quarantined"].append({"candidate_id": candidate_id, "problems": problems})
                continue
        context["context_sources"].append(source)
    return context


def _on_disk_problems(root: Path, source: dict[str, Any]) -> list[str]:
    manifest_path = root / source["manifest_path"]
    skill_path = root / source["source_path"]
    if not manifest_path.exists() or not skill_path.exists():
        return ["promoted candidate package is missing from disk"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    skill_text = skill_path.read_text(encoding="utf-8")
    problems = validate_manifest_integrity(manifest, skill_text)
    if manifest.get("integrity", {}).get("manifest_sha256") != source["manifest_sha256"]:
        problems.append("on-disk manifest digest drifted from promoted digest")
    if manifest.get("integrity", {}).get("source_blob_sha") != source["source_blob_sha"]:
        problems.append("on-disk source blob drifted from promoted blob")
    if manifest.get("status") != "candidate":
        problems.append("promoted candidate status drifted from candidate")
    return problems
