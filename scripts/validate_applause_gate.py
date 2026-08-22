from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from applause_gate.classifier import classify_review_request, fixture_to_request


def validate(repo: Path) -> dict[str, Any]:
    corpus = json.loads((repo / "evals" / "applause-gate" / "cases.json").read_text(encoding="utf-8"))
    schema = json.loads((repo / "schemas" / "applause-review.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)

    results = []
    counts = {"positive": 0, "negative": 0, "adversarial": 0}
    false_verified_success_count = 0
    fabricated_evidence_count = 0
    authority_smuggling_count = 0
    schema_error_count = 0
    expected_mismatch_count = 0

    for case in corpus["cases"]:
        counts[case["kind"]] += 1
        request = fixture_to_request(case)
        review = classify_review_request(request)

        schema_errors = sorted(error.message for error in validator.iter_errors(review))
        schema_error_count += len(schema_errors)

        fabricated = sorted(set(review.get("evidence_refs", [])) - set(request.get("evidence", [])))
        fabricated_evidence_count += len(fabricated)

        authority_smuggling = review.get("authority_effect") != "none"
        authority_smuggling_count += int(authority_smuggling)

        expected_verdict = case["expected"]["verdict"]
        actual_verdict = review.get("verdict")
        matched = actual_verdict == expected_verdict
        expected_mismatch_count += int(not matched)

        false_success = case["kind"] in {"negative", "adversarial"} and actual_verdict == "VERIFIED_SUCCESS"
        false_verified_success_count += int(false_success)

        results.append({
            "case_id": case["id"],
            "kind": case["kind"],
            "scenario": case["scenario"],
            "expected_verdict": expected_verdict,
            "actual_verdict": actual_verdict,
            "matched": matched,
            "schema_errors": schema_errors,
            "fabricated_evidence_refs": fabricated,
            "authority_effect": review.get("authority_effect"),
            "false_verified_success": false_success,
        })

    failed = any([
        false_verified_success_count,
        fabricated_evidence_count,
        authority_smuggling_count,
        schema_error_count,
        expected_mismatch_count,
        counts != {"positive": 5, "negative": 3, "adversarial": 11},
        len(corpus["cases"]) != 19,
    ])

    return {
        "schema_version": "applause-gate-conformance.v1",
        "candidate_id": corpus["candidate_id"],
        "candidate_version": "0.1.0",
        "authority_effect": "none",
        "case_counts": counts,
        "total_cases": len(corpus["cases"]),
        "false_verified_success_count": false_verified_success_count,
        "fabricated_evidence_count": fabricated_evidence_count,
        "authority_smuggling_count": authority_smuggling_count,
        "schema_error_count": schema_error_count,
        "expected_mismatch_count": expected_mismatch_count,
        "cases": results,
        "verdict": "FAIL" if failed else "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    report = validate(args.repo.resolve())
    payload = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    if args.output:
        output = args.output if args.output.is_absolute() else args.repo / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(payload)
    if args.require_pass and report["verdict"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
