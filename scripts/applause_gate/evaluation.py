from __future__ import annotations

import copy
import hashlib
import hmac
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .classifier import classify_review_request, fixture_to_request
from .receipt import canonical_json, sha256_json_without_keys


EXPECTED_COUNTS = {"positive": 5, "negative": 3, "adversarial": 11}
EXPECTED_HELD_OUT_COVERAGE = {
    "ambiguous_success",
    "mixed_guardrails",
    "weak_causality",
    "version_drift",
    "evidence_tampering",
}


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _git_blob_sha(payload: bytes) -> str:
    return hashlib.sha1(f"blob {len(payload)}\0".encode("utf-8") + payload).hexdigest()


def _manifest_digest(payload: bytes) -> str:
    manifest = json.loads(payload)
    manifest = copy.deepcopy(manifest)
    manifest.get("integrity", {}).pop("manifest_sha256", None)
    return _sha256_bytes(canonical_json(manifest).encode("utf-8"))


def _binding_digest(payload: bytes, algorithm: str) -> str:
    if algorithm == "sha256":
        return _sha256_bytes(payload)
    if algorithm == "git-blob-sha1":
        return _git_blob_sha(payload)
    if algorithm == "sha256-canonical-json-v1":
        return _manifest_digest(payload)
    raise ValueError(f"unsupported binding algorithm: {algorithm}")


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def verify_freeze(repo: Path, freeze: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    commit = freeze["candidate_commit"]

    commit_check = _git(repo, "cat-file", "-e", f"{commit}^{{commit}}", check=False)
    if commit_check.returncode:
        return [f"frozen candidate commit is unavailable: {commit}"]

    tree = _git(repo, "rev-parse", f"{commit}^{{tree}}").stdout.strip()
    if tree != freeze["candidate_tree"]:
        errors.append("frozen candidate tree digest changed")

    ancestry = _git(repo, "merge-base", "--is-ancestor", commit, "HEAD", check=False)
    if ancestry.returncode:
        errors.append("frozen candidate commit is not an ancestor of HEAD")

    for name, binding in sorted(freeze["bindings"].items()):
        path = binding["path"]
        algorithm = binding["algorithm"]
        expected = binding["digest"]
        working_path = repo / path
        if not working_path.is_file():
            errors.append(f"{name} is missing from the working tree")
            continue

        working_digest = _binding_digest(working_path.read_bytes(), algorithm)
        if not hmac.compare_digest(working_digest, expected):
            errors.append(f"{name} working-tree digest differs from freeze")

        committed = _git(repo, "show", f"{commit}:{path}", check=False)
        if committed.returncode:
            errors.append(f"{name} is missing from the frozen commit")
            continue
        committed_digest = _binding_digest(committed.stdout.encode("utf-8"), algorithm)
        if not hmac.compare_digest(committed_digest, expected):
            errors.append(f"{name} frozen-commit digest differs from freeze")

    return errors


def evaluate_visible(repo: Path, freeze: dict[str, Any]) -> dict[str, Any]:
    corpus = json.loads((repo / "evals/applause-gate/cases.json").read_text(encoding="utf-8"))
    schema = json.loads((repo / "schemas/applause-review.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    counts = {kind: 0 for kind in EXPECTED_COUNTS}
    results = []

    for case in corpus["cases"]:
        counts[case["kind"]] += 1
        request = fixture_to_request(case)
        review = classify_review_request(request)
        expected = case["expected"]["verdict"]
        actual = review.get("verdict")
        fabricated = sorted(set(review.get("evidence_refs", [])) - set(request["evidence"]))
        schema_errors = sorted(error.message for error in validator.iter_errors(review))
        false_success = case["kind"] in {"negative", "adversarial"} and actual == "VERIFIED_SUCCESS"
        differences = [] if actual == expected else [f"verdict: expected {expected}, actual {actual}"]
        results.append(
            {
                "case_id": case["id"],
                "kind": case["kind"],
                "actual_verdict": actual,
                "expected_verdict": expected,
                "matched": not differences,
                "required_codes": review.get("required_codes", []),
                "withheld_claims": review.get("withheld_claims", []),
                "missing_proof": review.get("missing_proof", []),
                "schema_errors": schema_errors,
                "fabricated_evidence_refs": fabricated,
                "authority_effect": review.get("authority_effect"),
                "false_verified_success": false_success,
                "differences": differences,
            }
        )

    failed = (
        counts != EXPECTED_COUNTS
        or len(results) != 19
        or any(
            not result["matched"]
            or result["schema_errors"]
            or result["fabricated_evidence_refs"]
            or result["authority_effect"] != "none"
            or result["false_verified_success"]
            for result in results
        )
    )
    report = {
        "schema_version": "applause-gate-conformance-report.v1",
        "candidate_id": freeze["candidate_id"],
        "candidate_version": freeze["candidate_version"],
        "candidate_commit": freeze["candidate_commit"],
        "freeze_bindings": freeze["bindings"],
        "case_counts": counts,
        "total_cases": len(results),
        "false_verified_success_count": sum(item["false_verified_success"] for item in results),
        "fabricated_evidence_count": sum(len(item["fabricated_evidence_refs"]) for item in results),
        "authority_smuggling_count": sum(item["authority_effect"] != "none" for item in results),
        "schema_error_count": sum(len(item["schema_errors"]) for item in results),
        "expected_mismatch_count": sum(not item["matched"] for item in results),
        "cases": results,
        "classifications": {
            "skips": [],
            "warnings": [],
            "limitations": [
                "Visible fixture expectations are public and therefore establish conformance, not held-out generalization."
            ],
        },
        "authority_effect": "none",
        "verdict": "FAIL" if failed else "PASS",
    }
    report["receipt_hash"] = sha256_json_without_keys(report, {"receipt_hash"})
    return report


def run_cold_process_replay(repo: Path, freeze: dict[str, Any]) -> dict[str, Any]:
    command = [
        sys.executable,
        str(repo / "scripts/validate_applause_gate.py"),
        "--repo",
        str(repo),
        "--require-pass",
    ]
    observations = []
    for process_number in (1, 2):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo / "scripts")
        result = subprocess.run(command, check=False, capture_output=True, text=True, env=env)
        payload = result.stdout.strip()
        parsed = json.loads(payload) if payload else {}
        observations.append(
            {
                "cold_process": process_number,
                "exit_code": result.returncode,
                "payload_sha256": _sha256_bytes(payload.encode("utf-8")),
                "receipt_hash": parsed.get("receipt_hash"),
                "verdict": parsed.get("verdict"),
            }
        )

    deterministic = (
        all(item["exit_code"] == 0 and item["verdict"] == "PASS" for item in observations)
        and observations[0]["payload_sha256"] == observations[1]["payload_sha256"]
        and observations[0]["receipt_hash"] == observations[1]["receipt_hash"]
    )
    report = {
        "schema_version": "applause-gate-determinism-proof.v1",
        "candidate_commit": freeze["candidate_commit"],
        "process_isolation": "two separate subprocess invocations with fresh interpreters",
        "observations": observations,
        "deterministic": deterministic,
        "classifications": {"skips": [], "warnings": [], "limitations": []},
        "authority_effect": "none",
        "verdict": "PASS" if deterministic else "FAIL",
    }
    report["receipt_hash"] = sha256_json_without_keys(report, {"receipt_hash"})
    return report


MUTATIONS = (
    {
        "id": "verdict-rule-negative-to-verified-success",
        "path": "scripts/applause_gate/classifier.py",
        "original": '"graph_went_up_victory_announcement": "SIGNAL_ONLY"',
        "replacement": '"graph_went_up_victory_announcement": "VERIFIED_SUCCESS"',
        "test": "tests.test_applause_gate_conformance",
        "critical_control": "verdict_rules",
    },
    {
        "id": "integrity-ignore-fabricated-evidence",
        "path": "scripts/validate_applause_gate.py",
        "original": 'fabricated = sorted(set(review.get("evidence_refs", [])) - set(request.get("evidence", [])))',
        "replacement": "fabricated = []",
        "test": (
            "tests.test_applause_gate_evaluation."
            "ApplauseGateEvaluationTests.test_fabricated_evidence_is_release_blocking"
        ),
        "critical_control": "integrity_checks",
    },
    {
        "id": "authority-guard-accept-effect",
        "path": "schemas/applause-review.schema.json",
        "original": '"authority_effect": {"const": "none"}',
        "replacement": '"authority_effect": {"type": "string"}',
        "test": "tests.test_applause_gate_schema",
        "critical_control": "authority_guards",
    },
)


def run_mutation_testing(repo: Path, freeze: dict[str, Any]) -> dict[str, Any]:
    results = []
    for mutation in MUTATIONS:
        with tempfile.TemporaryDirectory(prefix="abg07-mutant-") as temp_dir:
            mutant_root = Path(temp_dir) / "repo"
            shutil.copytree(
                repo,
                mutant_root,
                ignore=shutil.ignore_patterns(
                    ".git",
                    "__pycache__",
                    "*.pyc",
                    ".pytest_cache",
                ),
            )
            target = mutant_root / mutation["path"]
            source = target.read_text(encoding="utf-8")
            occurrences = source.count(mutation["original"])
            if occurrences != 1:
                results.append(
                    {
                        "mutation_id": mutation["id"],
                        "critical_control": mutation["critical_control"],
                        "status": "not_applied",
                        "reason": f"expected one mutation point, found {occurrences}",
                    }
                )
                continue
            target.write_text(
                source.replace(mutation["original"], mutation["replacement"]),
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["PYTHONPATH"] = str(mutant_root / "scripts")
            completed = subprocess.run(
                [sys.executable, "-m", "unittest", mutation["test"], "-v"],
                cwd=mutant_root,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            results.append(
                {
                    "mutation_id": mutation["id"],
                    "critical_control": mutation["critical_control"],
                    "mutated_path": mutation["path"],
                    "mutant_sha256": _sha256_bytes(target.read_bytes()),
                    "test": mutation["test"],
                    "test_exit_code": completed.returncode,
                    "status": "killed" if completed.returncode != 0 else "survived",
                }
            )

    killed = sum(result["status"] == "killed" for result in results)
    survivors = [result["mutation_id"] for result in results if result["status"] != "killed"]
    report = {
        "schema_version": "applause-gate-mutation-report.v1",
        "candidate_commit": freeze["candidate_commit"],
        "total_mutations": len(results),
        "killed_mutations": killed,
        "mutation_score": killed / len(results) if results else 0,
        "surviving_mutations": survivors,
        "mutations": results,
        "classifications": {"skips": [], "warnings": [], "limitations": []},
        "authority_effect": "none",
        "verdict": "PASS" if killed == len(results) and results else "FAIL",
    }
    report["receipt_hash"] = sha256_json_without_keys(report, {"receipt_hash"})
    return report


def validate_held_out_receipt(receipt: dict[str, Any], freeze: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_hash = sha256_json_without_keys(receipt, {"receipt_hash"})
    if not hmac.compare_digest(receipt.get("receipt_hash", ""), expected_hash):
        errors.append("held-out receipt hash mismatch")
    if receipt.get("candidate_commit") != freeze["candidate_commit"]:
        errors.append("held-out candidate commit mismatch")
    if receipt.get("candidate_version") != freeze["candidate_version"]:
        errors.append("held-out candidate version mismatch")
    if receipt.get("freeze_bindings") != freeze["bindings"]:
        errors.append("held-out freeze bindings mismatch")
    if receipt.get("implementation_author") == receipt.get("evaluator"):
        errors.append("held-out evaluator is not independent")
    if not receipt.get("independence_disclosure"):
        errors.append("held-out evaluator independence disclosure is missing")
    seal_digest = receipt.get("seal_digest", "")
    if len(seal_digest) != 64 or any(character not in "0123456789abcdef" for character in seal_digest):
        errors.append("held-out seal digest is invalid")
    if receipt.get("case_count") != 5:
        errors.append("held-out receipt must cover exactly five cases")
    if set(receipt.get("coverage", [])) != EXPECTED_HELD_OUT_COVERAGE:
        errors.append("held-out coverage is incomplete")
    if receipt.get("false_verified_success_count") != 0:
        errors.append("held-out receipt contains a false VERIFIED_SUCCESS")
    if receipt.get("fabricated_evidence_count") != 0:
        errors.append("held-out receipt contains fabricated evidence")
    if receipt.get("authority_smuggling_count") != 0:
        errors.append("held-out receipt contains authority smuggling")
    if receipt.get("expected_mismatch_count") != 0:
        errors.append("held-out receipt contains expectation differences")
    cases = receipt.get("cases", [])
    required_case_fields = {
        "redacted_case_id",
        "expected_verdict",
        "actual_verdict",
        "matched",
        "required_codes",
        "withheld_claims",
        "missing_proof",
        "schema_errors",
        "fabricated_evidence_refs",
        "authority_effect",
        "false_verified_success",
        "differences",
    }
    if len(cases) != 5 or any(not required_case_fields.issubset(case) for case in cases):
        errors.append("held-out per-case evidence is incomplete")
    if len({case.get("redacted_case_id") for case in cases}) != len(cases):
        errors.append("held-out redacted case identities are not unique")
    if any("request" in case or "input" in case or "claim" in case for case in cases):
        errors.append("held-out receipt discloses sealed case content")
    if any(
        not case.get("matched")
        or case.get("actual_verdict") != case.get("expected_verdict")
        or case.get("schema_errors")
        or case.get("fabricated_evidence_refs")
        or case.get("authority_effect") != "none"
        or case.get("false_verified_success")
        or case.get("differences")
        for case in cases
    ):
        errors.append("held-out per-case evidence contains a critical failure")
    classifications = receipt.get("classifications", {})
    if not all(name in classifications for name in ("skips", "warnings", "limitations")):
        errors.append("held-out classifications are incomplete")
    if classifications.get("skips"):
        errors.append("held-out evaluation contains skipped cases")
    if receipt.get("verdict") != "PASS_CANDIDATE_EVIDENCE":
        errors.append("independent evaluator did not pass candidate evidence")
    return errors


def write_content_addressed(output_dir: Path, stem: str, report: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{stem}.{report['receipt_hash']}.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def build_evaluation_index(
    freeze: dict[str, Any],
    visible: dict[str, Any],
    held_out: dict[str, Any],
    mutation: dict[str, Any],
    determinism: dict[str, Any],
    evidence_paths: dict[str, Path],
) -> dict[str, Any]:
    held_out_errors = validate_held_out_receipt(held_out, freeze)
    pass_candidate = (
        visible["verdict"] == "PASS"
        and not held_out_errors
        and mutation["verdict"] == "PASS"
        and determinism["verdict"] == "PASS"
    )
    reports = (visible, held_out, mutation, determinism)
    classifications = {
        name: list(
            dict.fromkeys(
                item
                for report in reports
                for item in report.get("classifications", {}).get(name, [])
            )
        )
        for name in ("skips", "warnings", "limitations")
    }
    index = {
        "schema_version": "applause-gate-evaluation-index.v1",
        "candidate_id": freeze["candidate_id"],
        "candidate_version": freeze["candidate_version"],
        "candidate_commit": freeze["candidate_commit"],
        "candidate_tree": freeze["candidate_tree"],
        "freeze_bindings": freeze["bindings"],
        "implementation_author": held_out.get("implementation_author"),
        "independent_evaluator": held_out.get("evaluator"),
        "evidence": {
            name: {
                "path": path.name,
                "receipt_hash": report["receipt_hash"],
            }
            for name, path, report in (
                ("visible_conformance", evidence_paths["visible"], visible),
                ("held_out_receipt", evidence_paths["held_out"], held_out),
                ("mutation_report", evidence_paths["mutation"], mutation),
                ("determinism_proof", evidence_paths["determinism"], determinism),
            )
        },
        "held_out_receipt_errors": held_out_errors,
        "classifications": classifications,
        "authority_effect": "none",
        "verdict": "PASS_CANDIDATE_EVIDENCE" if pass_candidate else "REVISE",
    }
    index["receipt_hash"] = sha256_json_without_keys(index, {"receipt_hash"})
    return index
