#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

EXPECTED_IDS = [
    "ABG-P01", "ABG-P02", "ABG-P03", "ABG-P04", "ABG-P05",
    "ABG-N01", "ABG-N02", "ABG-N03",
    "ABG-A01", "ABG-A02", "ABG-A03", "ABG-A04", "ABG-A05",
    "ABG-A06", "ABG-A07", "ABG-A08", "ABG-A09", "ABG-A10", "ABG-A11",
]
EXPECTED_COUNTS = {"positive": 5, "negative": 3, "adversarial": 11}
EXPECTED_VERDICTS = {
    "SIGNAL_ONLY",
    "SUPPORTED_DIAGNOSIS",
    "VERIFIED_SUCCESS",
    "FALSE_POSITIVE",
    "UNRESOLVED",
    "EVIDENCE_INTEGRITY_FAILURE",
}
REQUIRED_CASE_FIELDS = {
    "id", "kind", "scenario", "claim", "signal", "evidence", "expected",
    "required_behaviors", "prohibited_behaviors",
}


def validate(repo: Path) -> dict:
    path = repo / "evals" / "applause-gate" / "cases.json"
    errors: list[str] = []
    corpus = json.loads(path.read_text(encoding="utf-8"))
    cases = corpus.get("cases", [])

    if corpus.get("schema_version") != "applause-gate-fixture-corpus.v1":
        errors.append("unexpected schema_version")
    if corpus.get("candidate_id") != "quirk-applause-gate":
        errors.append("unexpected candidate_id")

    boundary = corpus.get("candidate_boundary", {})
    expected_boundary = {
        "status": "candidate_fixture_only",
        "authority_ceiling": "infer",
        "evaluator_implementation_present": False,
        "supabase_mutation_authorized": False,
        "plugin_packaging_authorized": False,
        "submission_drafting_authorized": False,
        "merge_authorized": False,
        "publication_authorized": False,
    }
    for key, expected in expected_boundary.items():
        if boundary.get(key) != expected:
            errors.append(f"candidate boundary mismatch: {key}")

    ids = [case.get("id") for case in cases]
    if ids != EXPECTED_IDS:
        errors.append("fixture IDs or ordering changed")
    if len(ids) != len(set(ids)):
        errors.append("fixture IDs are not unique")

    counts = Counter(case.get("kind") for case in cases)
    count_map = {kind: counts.get(kind, 0) for kind in EXPECTED_COUNTS}
    if count_map != EXPECTED_COUNTS or len(cases) != 19:
        errors.append(f"fixture counts changed: {count_map}, total={len(cases)}")

    for case in cases:
        case_id = case.get("id", "<missing>")
        missing = REQUIRED_CASE_FIELDS.difference(case)
        if missing:
            errors.append(f"{case_id}: missing fields {sorted(missing)}")
            continue
        if not case["evidence"]:
            errors.append(f"{case_id}: evidence refs must not be empty")
        verdict = case["expected"].get("verdict")
        if verdict not in EXPECTED_VERDICTS:
            errors.append(f"{case_id}: unknown verdict {verdict!r}")
        if case["kind"] in {"negative", "adversarial"} and verdict == "VERIFIED_SUCCESS":
            errors.append(f"{case_id}: negative/adversarial fixture cannot expect VERIFIED_SUCCESS")
        if not case["required_behaviors"]:
            errors.append(f"{case_id}: required_behaviors must not be empty")
        if not case["prohibited_behaviors"]:
            errors.append(f"{case_id}: prohibited_behaviors must not be empty")

    return {
        "schema_version": "applause-gate-fixture-validation.v1",
        "candidate_id": "quirk-applause-gate",
        "candidate_status": boundary.get("status"),
        "verdict": "PASS" if not errors else "FAIL",
        "case_counts": count_map,
        "total_cases": len(cases),
        "errors": errors,
        "authority_ceiling": boundary.get("authority_ceiling"),
        "admission_effect": "none",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Applause Gate fixture-only candidate corpus.")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--output")
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    report = validate(Path(args.repo).resolve())
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = Path(args.output)
        if not output.is_absolute():
            output = Path(args.repo).resolve() / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if args.require_pass and report["verdict"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
