"""Run synthetic fixture expectations without executing any proposed action."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .pack import VERSION, evaluate_authority, evaluate_completion, score_observations, summarize_coverage


def run_pack(pack: dict[str, Any], observations: dict[str, Any] | None = None) -> dict[str, Any]:
    if pack.get("version") != VERSION:
        raise ValueError(f"expected fixture version {VERSION}")
    digest = hashlib.sha256(json.dumps(pack, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    failed: list[str] = []
    counts: dict[str, int] = {}
    checks = (
        ("authority", evaluate_authority, "eligible_candidate"),
        ("completion", evaluate_completion, "completion_candidate"),
    )
    for name, checker, key in checks:
        cases = pack[name]
        ids = [item["id"] for item in cases]
        if len(set(ids)) != len(ids) or not cases:
            raise ValueError(f"duplicate or missing {name} fixture IDs")
        counts[name] = len(cases)
        for item in cases:
            result = checker(item["case"])
            if type(item["expected"]) is not bool or result[key] is not item["expected"]:
                failed.append(item["id"])
    report: dict[str, Any] = {
        "version": VERSION,
        "fixture_digest_sha256": digest,
        "fixture_status": "FAIL_SYNTHETIC_FIXTURES" if failed else "PASS_SYNTHETIC_FIXTURES",
        "failed_fixture_ids": failed,
        "fixture_counts": counts,
        "coverage": summarize_coverage(pack["coverage"]),
        "observation_status": "NO_OBSERVATIONS",
        "effects_executed": 0,
        "authority_effect": False,
    }
    if observations is not None:
        if not isinstance(observations, dict) or not {"panels", "revisions", "simulation", "persona", "provenance"}.issubset(observations):
            raise ValueError("observations require panels, revisions, simulation, persona, and provenance")
        report["observations"] = score_observations(observations)
        report["observation_status"] = "SYNTHETIC_EXAMPLE" if observations.get("provenance") == "synthetic_example" else "UNVERIFIED_TRACE"
    return report
