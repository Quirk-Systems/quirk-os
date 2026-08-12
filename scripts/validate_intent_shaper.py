#!/usr/bin/env python3
"""Validate the Quirk Intent Shaper candidate contracts and fixtures."""

from __future__ import annotations

import argparse
import hashlib
from importlib.metadata import version as package_version
import json
import platform
from pathlib import Path
import subprocess
import sys

from jsonschema import Draft202012Validator, FormatChecker

from intent_shaper.policy import evaluate_cases

EVALUATED_CANDIDATE_SHA = "f5effa3d6da3e5879e10007492aeff39a1c643be"


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def git_output(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--candidate-sha", default=EVALUATED_CANDIDATE_SHA)
    args = parser.parse_args()

    repo = args.repo.resolve()
    schema_path = repo / "schemas/personalization-plan.schema.json"
    receipt_schema_path = repo / "schemas/generated-ui-gate-receipt.schema.json"
    sample_path = repo / "examples/personalization-plan.valid.json"
    cases_path = repo / "evals/intent-shaper/cases.json"

    schema = json.loads(schema_path.read_text())
    receipt_schema = json.loads(receipt_schema_path.read_text())
    sample = json.loads(sample_path.read_text())
    suite = json.loads(cases_path.read_text())

    Draft202012Validator.check_schema(schema)
    Draft202012Validator.check_schema(receipt_schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    receipt_validator = Draft202012Validator(receipt_schema, format_checker=FormatChecker())
    sample_errors = sorted(validator.iter_errors(sample), key=lambda error: list(error.path))
    results = evaluate_cases(suite["cases"])

    errors: list[str] = []
    errors.extend(f"sample:{'/'.join(map(str, error.path))}:{error.message}" for error in sample_errors)
    errors.extend(f"fixture:{result['id']}" for result in results if not result["passed"])
    for result in results:
        if result["operation"] == "generated_ui_gate":
            receipt_errors = sorted(receipt_validator.iter_errors(result["actual"]), key=lambda error: list(error.path))
            errors.extend(
                f"receipt:{result['id']}:{'/'.join(map(str, error.path))}:{error.message}" for error in receipt_errors
            )

    head_sha = git_output(repo, "rev-parse", "HEAD")
    base_sha = git_output(repo, "rev-parse", "HEAD^1") if git_output(repo, "rev-list", "--count", "HEAD") != "1" else head_sha
    merge_base_sha = git_output(repo, "merge-base", args.candidate_sha, head_sha)
    ancestry_exit = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", args.candidate_sha, head_sha], check=False
    ).returncode

    report = {
        "suite_id": suite["suite_id"],
        "status": "passed" if not errors else "failed",
        "schema_valid": True,
        "generated_ui_receipt_schema_valid": True,
        "sample_valid": not sample_errors,
        "fixtures_passed": sum(1 for result in results if result["passed"]),
        "fixtures_total": len(results),
        "fixture_ids": [result["id"] for result in results],
        "results": results,
        "errors": errors,
        "git": {
            "candidate_sha": args.candidate_sha,
            "base_sha": base_sha,
            "head_sha": head_sha,
            "merge_base_sha": merge_base_sha,
            "candidate_ancestor_of_head": ancestry_exit == 0,
        },
        "relevant_inputs": {
            "schema": str(schema_path.relative_to(repo)),
            "receipt_schema": str(receipt_schema_path.relative_to(repo)),
            "fixtures": str(cases_path.relative_to(repo)),
            "tests": ["tests/test_intent_shaper.py"],
            "component_manifests": ["skills/quirk-intent-shaper/generated-ui/issue-intake-form.json"],
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "jsonschema": package_version("jsonschema"),
            "git": git_output(repo, "--version"),
        },
        "verdict": "REVISE" if errors else "candidate_evidence_complete",
        "runtime_authorized": False,
        "deployment_authorized": False,
        "limitations": [
            "Manual accessibility evidence is recorded by reference only; this harness does not invent human observations."
        ],
    }
    report["content_hash"] = canonical_hash(report)

    output_path = args.output or (repo / "evals/intent-shaper/conformance-results/qis-014.generated-ui-gate.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n")

    print(json.dumps({key: report[key] for key in ("status", "sample_valid", "fixtures_passed", "fixtures_total", "content_hash")}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
