"""Run synthetic fixture expectations without executing any proposed action."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .pack import VERSION, evaluate_authority, evaluate_completion, score_observations, summarize_coverage

REQUIRED_AUTHORITY_PAIRS = {f"A{number:02d}" for number in range(1, 13)}
REQUIRED_COMPLETION_IDS = {"C00-safe-control", "C01-agent-signoff", "C02-stale-source", "C03-bad-trajectory"}


def _validate_inventory(pack: dict[str, Any]) -> None:
    if not {"authority", "completion", "coverage"}.issubset(pack):
        raise ValueError("missing fixture pack sections")
    authority = pack["authority"]
    completion = pack["completion"]
    if not isinstance(authority, list) or not all(
        isinstance(item, dict) and {"id", "pair_id", "expected", "case"}.issubset(item)
        for item in authority
    ):
        raise ValueError("invalid authority fixture inventory")
    pair_members = {
        pair_id: [item for item in authority if item["pair_id"] == pair_id]
        for pair_id in {item["pair_id"] for item in authority}
    }
    matched_pairs = (
        set(pair_members) == REQUIRED_AUTHORITY_PAIRS
        and len(authority) == 24
        and all(len(items) == 2 and {item["expected"] for item in items} == {True, False} for items in pair_members.values())
    )
    if not matched_pairs:
        raise ValueError("invalid authority fixture inventory: require 12 matched safe/unsafe pairs")
    if not isinstance(completion, list) or {
        item.get("id") for item in completion if isinstance(item, dict)
    } != REQUIRED_COMPLETION_IDS or len(completion) != 4:
        raise ValueError("invalid completion fixture inventory: require four registered cases")


def run_pack(pack: dict[str, Any], observations: dict[str, Any] | None = None) -> dict[str, Any]:
    if pack.get("version") != VERSION:
        raise ValueError(f"expected fixture version {VERSION}")
    _validate_inventory(pack)
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
        try:
            scored = score_observations(observations)
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("invalid observations") from error
        if any(
            scored.get(status) == "INVALID_MATCH"
            for status in ("panel_status", "revision_status", "simulation_status", "persona_status")
        ):
            raise ValueError("invalid observations")
        report["observations"] = scored
        report["observation_status"] = "SYNTHETIC_EXAMPLE" if observations.get("provenance") == "synthetic_example" else "UNVERIFIED_TRACE"
    return report
