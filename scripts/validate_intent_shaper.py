#!/usr/bin/env python3
"""Validate the Quirk Intent Shaper candidate contracts and fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

from intent_shaper.policy import evaluate_cases


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    repo = args.repo.resolve()
    schema_path = repo / "schemas/personalization-plan.schema.json"
    sample_path = repo / "examples/personalization-plan.valid.json"
    cases_path = repo / "evals/intent-shaper/cases.json"

    schema = json.loads(schema_path.read_text())
    sample = json.loads(sample_path.read_text())
    suite = json.loads(cases_path.read_text())

    Draft202012Validator.check_schema(schema)
    sample_errors = sorted(Draft202012Validator(schema).iter_errors(sample), key=lambda error: list(error.path))
    results = evaluate_cases(suite["cases"])

    errors: list[str] = []
    errors.extend(f"sample:{'/'.join(map(str, error.path))}:{error.message}" for error in sample_errors)
    errors.extend(f"fixture:{result['id']}" for result in results if not result["passed"])

    report = {
        "suite_id": suite["suite_id"],
        "status": "passed" if not errors else "failed",
        "schema_valid": True,
        "sample_valid": not sample_errors,
        "fixtures_passed": sum(1 for result in results if result["passed"]),
        "fixtures_total": len(results),
        "results": results,
        "errors": errors,
    }
    report["content_hash"] = canonical_hash(report)

    output_path = args.output or (repo / "evals/intent-shaper/conformance-results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n")

    print(json.dumps({key: report[key] for key in ("status", "sample_valid", "fixtures_passed", "fixtures_total", "content_hash")}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
