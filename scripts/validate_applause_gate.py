from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from applause_gate.classifier import classify_review_request, fixture_to_request
from applause_gate.receipt import sha256_json_without_keys


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(repo: Path) -> dict[str, Any]:
    fixture_path = repo / "evals" / "applause-gate" / "cases.json"
    schema_path = repo / "schemas" / "applause-review.schema.json"
    classifier_path = repo / "scripts" / "applause_gate" / "classifier.py"
    validator_path = repo / "scripts" / "validate_applause_gate.py"

    corpus = json.loads(fixture_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
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

    source_hashes = {
        "fixture_digest": _sha256_file(fixture_path),
        "schema_digest": _sha256_file(schema_path),
        "classifier_digest": _sha256_file(classifier_path),
        "validator_digest": _sha256_file(validator_path),
    }

    report = {
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
        "fixture_digest": source_hashes["fixture_digest"],
        "schema_digest": source_hashes["schema_digest"],
        "classifier_digest": source_hashes["classifier_digest"],
        "validator_digest": source_hashes["validator_digest"],
        "source_hashes": source_hashes,
        "cases": results,
        "verdict": "FAIL" if failed else "PASS",
    }
    report["receipt_hash"] = sha256_json_without_keys(report, omitted_keys={"receipt_hash"})
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--metrics-output", type=Path, help="Optional JSON output path for performance/workload metrics.")
    parser.add_argument("--write-step-summary", action="store_true", help="Append metrics to GitHub step summary when available.")
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()
    started = time.perf_counter()

    repo = args.repo.resolve()
    report = validate(repo)
    payload = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    if args.output:
        output = args.output if args.output.is_absolute() else repo / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    metrics = {
        "validator": "validate_applause_gate.py",
        "elapsed_seconds": time.perf_counter() - started,
        "total_cases": report["total_cases"],
        "schema_error_count": report["schema_error_count"],
        "expected_mismatch_count": report["expected_mismatch_count"],
        "verdict": report["verdict"],
    }
    if args.metrics_output:
        metrics_output = args.metrics_output if args.metrics_output.is_absolute() else repo / args.metrics_output
        metrics_output.parent.mkdir(parents=True, exist_ok=True)
        metrics_output.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.write_step_summary and os.environ.get("GITHUB_STEP_SUMMARY"):
        summary_lines = [
            "## validate_applause_gate performance",
            "",
            "| metric | value |",
            "| --- | ---: |",
            f"| elapsed_seconds | {metrics['elapsed_seconds']:.6f} |",
            f"| total_cases | {metrics['total_cases']} |",
            f"| schema_error_count | {metrics['schema_error_count']} |",
            f"| expected_mismatch_count | {metrics['expected_mismatch_count']} |",
            f"| verdict | {metrics['verdict']} |",
            "",
        ]
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as handle:
            handle.write("\n".join(summary_lines))

    print(payload)
    if args.require_pass and report["verdict"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
