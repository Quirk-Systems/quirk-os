#!/usr/bin/env python3
"""Validate the Quirk Intent Shaper candidate contracts and fixtures."""

from __future__ import annotations

import argparse
import hashlib
from importlib import metadata
import json
import platform
from pathlib import Path
import subprocess
import sys

from jsonschema import Draft202012Validator

from intent_shaper.policy import (
    canonical_hash,
    evaluate_cases,
    evaluate_reconstruction_adversarial_cases,
    evaluate_reconstruction_mutations,
    evaluate_reconstruction_plan,
)
def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_sha(repo: Path, rev: str) -> str | None:
    completed = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", rev],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def run_cold_reconstruction(repo: Path) -> dict[str, object]:
    completed = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--repo",
            str(repo),
            "--emit-reconstruction-run",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(completed.stdout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--emit-reconstruction-run", action="store_true")
    parser.add_argument(
        "--candidate-sha",
        default="f5effa3d6da3e5879e10007492aeff39a1c643be",
    )
    parser.add_argument("--base-sha")
    parser.add_argument("--head-sha")
    args = parser.parse_args()

    repo = args.repo.resolve()
    schema_path = repo / "schemas/personalization-plan.schema.json"
    sample_path = repo / "examples/personalization-plan.valid.json"
    generated_ui_sample_path = repo / "examples/personalization-plan.generated-ui.valid.json"
    cases_path = repo / "evals/intent-shaper/cases.json"

    schema = json.loads(schema_path.read_text())
    sample = json.loads(sample_path.read_text())
    generated_ui_sample = json.loads(generated_ui_sample_path.read_text())
    suite = json.loads(cases_path.read_text())

    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    sample_errors = sorted(validator.iter_errors(sample), key=lambda error: list(error.path))
    generated_ui_sample_errors = sorted(validator.iter_errors(generated_ui_sample), key=lambda error: list(error.path))
    results = evaluate_cases(suite["cases"])
    reconstruction_suite = suite["reconstruction_suite"]
    reconstruction_result = evaluate_reconstruction_plan(generated_ui_sample, validator)

    if args.emit_reconstruction_run:
        print(json.dumps(reconstruction_result, sort_keys=True))
        return 1 if reconstruction_result["status"] != "passed" else 0

    cold_runs = [run_cold_reconstruction(repo), run_cold_reconstruction(repo)]
    mutation_results = evaluate_reconstruction_mutations(
        generated_ui_sample,
        reconstruction_suite["mutations"],
        validator,
    )
    adversarial_results = evaluate_reconstruction_adversarial_cases(
        generated_ui_sample,
        reconstruction_suite["adversarial_cases"],
        validator,
    )

    errors: list[str] = []
    errors.extend(f"sample:{'/'.join(map(str, error.path))}:{error.message}" for error in sample_errors)
    errors.extend(
        f"generated_ui_sample:{'/'.join(map(str, error.path))}:{error.message}"
        for error in generated_ui_sample_errors
    )
    errors.extend(f"fixture:{result['id']}" for result in results if not result["passed"])
    if reconstruction_result["status"] != "passed":
        critical = reconstruction_result["critical_failure"]
        errors.append(f"reconstruction:{critical['code']}:{critical['message']}")
    expected = reconstruction_suite["expected"]
    if any(run["semantic_hash"] != expected["semantic_hash"] or run["subhashes"] != expected["subhashes"] for run in cold_runs):
        errors.append("reconstruction:EXPECTED_HASH_MISMATCH")
    if cold_runs[0] != cold_runs[1]:
        errors.append("reconstruction:NONDETERMINISTIC_COLD_RUN")
    errors.extend(f"mutation:{result['id']}" for result in mutation_results if not result["passed"])
    errors.extend(f"adversarial:{result['id']}" for result in adversarial_results if not result["passed"])

    report = {
        "issue": "QIS-015",
        "suite_id": suite["suite_id"],
        "status": "passed" if not errors else "failed",
        "verdict": "candidate_evidence_only",
        "schema_valid": True,
        "sample_valid": not sample_errors,
        "generated_ui_sample_valid": not generated_ui_sample_errors,
        "fixtures_passed": sum(1 for result in results if result["passed"]),
        "fixtures_total": len(results),
        "results": results,
        "reconstruction": {
            "case_id": reconstruction_suite["case_id"],
            "expected": expected,
            "cold_runs": cold_runs,
            "deterministic": cold_runs[0] == cold_runs[1],
            "mutations": mutation_results,
            "adversarial_cases": adversarial_results,
        },
        "shas": {
            "candidate_sha": args.candidate_sha,
            "base_sha": args.base_sha or git_sha(repo, "refs/remotes/origin/agent/quirk-intent-shaper") or args.candidate_sha,
            "head_sha": args.head_sha or git_sha(repo, "HEAD") or "unknown",
        },
        "relevant_files": {
            "schemas/personalization-plan.schema.json": file_hash(schema_path),
            "scripts/intent_shaper/policy.py": file_hash(repo / "scripts/intent_shaper/policy.py"),
            "scripts/validate_intent_shaper.py": file_hash(repo / "scripts/validate_intent_shaper.py"),
            "evals/intent-shaper/cases.json": file_hash(cases_path),
            "examples/personalization-plan.generated-ui.valid.json": file_hash(generated_ui_sample_path),
            "tests/test_intent_shaper.py": file_hash(repo / "tests/test_intent_shaper.py"),
        },
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "tool_versions": {
            "jsonschema": metadata.version("jsonschema"),
        },
        "test_counts": {
            "policy_cases": len(results),
            "cold_reconstructions": len(cold_runs),
            "mutation_cases": len(mutation_results),
            "adversarial_cases": len(adversarial_results),
        },
        "critical_failures": [
            reconstruction_result["critical_failure"]
        ] if reconstruction_result["status"] != "passed" else [],
        "limitations": [
            "Evidence remains candidate-only and does not admit, activate, deploy, or persist generated UI.",
            "Cold reconstruction proves deterministic semantic projection only for the pinned fixture and declared mutation suite.",
        ],
        "authority": {
            "admits_generated_ui": False,
            "deploys_generated_ui": False,
            "writes_settings": False,
            "meaning": "candidate-local reconstruction evidence only",
        },
        "errors": errors,
    }
    report["content_hash"] = canonical_hash(report, omit_hash_fields=True)

    output_path = args.output or (repo / "evals/intent-shaper/conformance-results/qis-015.reconstruction.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n")

    print(
        json.dumps(
            {
                key: report[key]
                for key in ("status", "sample_valid", "generated_ui_sample_valid", "fixtures_passed", "fixtures_total", "content_hash")
            },
            indent=2,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
