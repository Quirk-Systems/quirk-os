from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from furniture_brief.compiler import compile_and_receipt
from furniture_brief.receipt import verify_chain


def validate(repo: Path) -> dict[str, Any]:
    fixture_path = repo / "evals" / "furniture-brief" / "cases.json"
    schema_path = repo / "schemas" / "furniture-brief-contract.schema.json"

    corpus = json.loads(fixture_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    request_validator = Draft202012Validator({"$ref": "#/$defs/compile_request", **schema})
    brief_validator = Draft202012Validator({"$ref": "#/$defs/song_brief", **schema})
    receipt_validator = Draft202012Validator({"$ref": "#/$defs/generation_receipt_entry", **schema})

    chain: list[dict[str, Any]] = []
    results = []
    counts = {"positive": 0, "negative": 0}
    decision_mismatch_count = 0
    refusal_code_mismatch_count = 0
    schema_error_count = 0

    for case in corpus["cases"]:
        counts[case["kind"]] = counts.get(case["kind"], 0) + 1

        request_errors = sorted(e.message for e in request_validator.iter_errors(case["request"]))
        schema_error_count += len(request_errors)

        outcome = compile_and_receipt(case["request"], chain)

        decision_matched = outcome["decision"] == case["expected"]["decision"]
        codes_matched = sorted(outcome["refusal_codes"]) == sorted(case["expected"]["refusal_codes"])
        decision_mismatch_count += int(not decision_matched)
        refusal_code_mismatch_count += int(not codes_matched)

        brief_errors: list[str] = []
        if outcome["song_brief"] is not None:
            brief_errors = sorted(e.message for e in brief_validator.iter_errors(outcome["song_brief"]))
            schema_error_count += len(brief_errors)

        receipt_errors = sorted(e.message for e in receipt_validator.iter_errors(outcome["receipt_entry"]))
        schema_error_count += len(receipt_errors)

        results.append({
            "case_id": case["id"],
            "kind": case["kind"],
            "expected_decision": case["expected"]["decision"],
            "actual_decision": outcome["decision"],
            "decision_matched": decision_matched,
            "expected_refusal_codes": sorted(case["expected"]["refusal_codes"]),
            "actual_refusal_codes": sorted(outcome["refusal_codes"]),
            "refusal_codes_matched": codes_matched,
            "grip_total": outcome["grip"]["total"],
            "furniture_load_bearing": outcome["furniture_assessment"]["load_bearing"],
            "lineage_valid": outcome["lineage"]["valid"],
            "receipt_id": outcome["receipt_entry"]["receipt_id"],
            "request_schema_errors": request_errors,
            "brief_schema_errors": brief_errors,
            "receipt_schema_errors": receipt_errors,
        })

    chain_verdict = verify_chain(chain)

    summary = {
        "fixture_count": len(corpus["cases"]),
        "counts": counts,
        "decision_mismatch_count": decision_mismatch_count,
        "refusal_code_mismatch_count": refusal_code_mismatch_count,
        "schema_error_count": schema_error_count,
        "receipt_chain_valid": chain_verdict["valid"],
        "receipt_chain_length": len(chain),
        "results": results,
        "passed": (
            decision_mismatch_count == 0
            and refusal_code_mismatch_count == 0
            and schema_error_count == 0
            and chain_verdict["valid"]
        ),
    }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    summary = validate(args.repo)
    print(json.dumps(summary, indent=2))

    if args.require_pass and not summary["passed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
