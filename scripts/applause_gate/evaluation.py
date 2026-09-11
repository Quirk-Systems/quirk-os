from __future__ import annotations

import base64
import binascii
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
VERDICTS = {
    "SIGNAL_ONLY",
    "SUPPORTED_DIAGNOSIS",
    "VERIFIED_SUCCESS",
    "FALSE_POSITIVE",
    "UNRESOLVED",
    "EVIDENCE_INTEGRITY_FAILURE",
}
REQUIRED_FREEZE_BINDINGS = {
    "classifier": ("scripts/applause_gate/classifier.py", "sha256"),
    "conformance_validator": ("scripts/validate_applause_gate.py", "sha256"),
    "manifest": ("skills/quirk-applause-gate/manifest.json", "sha256-canonical-json-v1"),
    "receipt": ("scripts/applause_gate/receipt.py", "sha256"),
    "schema": ("schemas/applause-review.schema.json", "sha256"),
    "skill_source": ("skills/quirk-applause-gate/SKILL.md", "git-blob-sha1"),
    "visible_fixtures": ("evals/applause-gate/cases.json", "sha256"),
}
EVALUATOR_ID = "copilot-agent/abg07-independent-evaluator"
IMPLEMENTATION_AUTHOR = "copilot-agent/abg07-implementation"
EVALUATOR_KEY_FINGERPRINT = "d8f77318f9d5257c71a7619368780f3937d58081ae671cfd76958899b0a04b3d"
REQUIRED_EVALUATOR_PATHS = {
    "evaluation_cli": "scripts/evaluate_applause_gate_candidate.py",
    "evaluation_harness": "scripts/applause_gate/evaluation.py",
    "evaluation_tests": "tests/test_applause_gate_evaluation.py",
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
    commit = freeze.get("candidate_commit", "")
    bindings = freeze.get("bindings", {})

    if set(bindings) != set(REQUIRED_FREEZE_BINDINGS):
        errors.append("freeze binding inventory is incomplete or contains unexpected entries")
    for name, (required_path, required_algorithm) in REQUIRED_FREEZE_BINDINGS.items():
        binding = bindings.get(name, {})
        if binding.get("path") != required_path:
            errors.append(f"{name} freeze path differs from the required path")
        if binding.get("algorithm") != required_algorithm:
            errors.append(f"{name} freeze algorithm differs from the required algorithm")

    commit_check = _git(repo, "cat-file", "-e", f"{commit}^{{commit}}", check=False)
    if commit_check.returncode:
        return [f"frozen candidate commit is unavailable: {commit}"]

    tree = _git(repo, "rev-parse", f"{commit}^{{tree}}").stdout.strip()
    if tree != freeze["candidate_tree"]:
        errors.append("frozen candidate tree digest changed")

    ancestry = _git(repo, "merge-base", "--is-ancestor", commit, "HEAD", check=False)
    if ancestry.returncode:
        errors.append("frozen candidate commit is not an ancestor of HEAD")

    for name, binding in sorted(bindings.items()):
        path = binding.get("path")
        algorithm = binding.get("algorithm")
        expected = binding.get("digest")
        if not all(isinstance(value, str) and value for value in (path, algorithm, expected)):
            errors.append(f"{name} freeze binding is incomplete")
            continue
        working_path = repo / path
        if not working_path.is_file():
            errors.append(f"{name} is missing from the working tree")
            continue

        try:
            working_digest = _binding_digest(working_path.read_bytes(), algorithm)
        except (ValueError, json.JSONDecodeError):
            errors.append(f"{name} working-tree binding cannot be evaluated")
            continue
        if not hmac.compare_digest(working_digest, expected):
            errors.append(f"{name} working-tree digest differs from freeze")

        committed = _git(repo, "show", f"{commit}:{path}", check=False)
        if committed.returncode:
            errors.append(f"{name} is missing from the frozen commit")
            continue
        try:
            committed_digest = _binding_digest(committed.stdout.encode("utf-8"), algorithm)
        except (ValueError, json.JSONDecodeError):
            errors.append(f"{name} frozen-commit binding cannot be evaluated")
            continue
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


def _run_unittest(root: Path, test: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "scripts")
    return subprocess.run(
        [sys.executable, "-m", "unittest", test, "-v"],
        cwd=root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


def _is_assertion_kill(result: subprocess.CompletedProcess[str]) -> bool:
    output = result.stdout + result.stderr
    return (
        result.returncode == 1
        and "FAILED (failures=" in output
        and "ERROR:" not in output
        and "_FailedTest" not in output
    )


def run_mutation_testing(
    repo: Path,
    freeze: dict[str, Any],
    mutations: tuple[dict[str, str], ...] | None = None,
) -> dict[str, Any]:
    results = []
    for mutation in mutations or MUTATIONS:
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
            baseline = _run_unittest(mutant_root, mutation["test"])
            if baseline.returncode:
                results.append(
                    {
                        "mutation_id": mutation["id"],
                        "critical_control": mutation["critical_control"],
                        "status": "infrastructure_failure",
                        "reason": "unmutated baseline test did not pass",
                        "baseline_test_exit_code": baseline.returncode,
                    }
                )
                continue
            target.write_text(
                source.replace(mutation["original"], mutation["replacement"]),
                encoding="utf-8",
            )
            completed = _run_unittest(mutant_root, mutation["test"])
            if completed.returncode == 0:
                status = "survived"
            elif _is_assertion_kill(completed):
                status = "killed"
            else:
                status = "infrastructure_failure"
            results.append(
                {
                    "mutation_id": mutation["id"],
                    "critical_control": mutation["critical_control"],
                    "mutated_path": mutation["path"],
                    "mutant_sha256": _sha256_bytes(target.read_bytes()),
                    "test": mutation["test"],
                    "baseline_test_exit_code": baseline.returncode,
                    "test_exit_code": completed.returncode,
                    "status": status,
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


def evaluator_bindings(repo: Path) -> dict[str, dict[str, str]]:
    return {
        name: {
            "path": path,
            "algorithm": "sha256",
            "digest": _sha256_bytes((repo / path).read_bytes()),
        }
        for name, path in sorted(REQUIRED_EVALUATOR_PATHS.items())
    }


def _signed_receipt_payload(receipt: dict[str, Any]) -> bytes:
    payload = {
        key: value
        for key, value in receipt.items()
        if key not in {"receipt_hash", "signature"}
    }
    return canonical_json(payload).encode("utf-8")


def _public_key_fingerprint(public_key: Path) -> str:
    result = subprocess.run(
        ["openssl", "pkey", "-pubin", "-in", str(public_key), "-outform", "DER"],
        check=False,
        capture_output=True,
    )
    return _sha256_bytes(result.stdout) if result.returncode == 0 else ""


def _signature_is_valid(receipt: dict[str, Any], public_key: Path) -> bool:
    signature = receipt.get("signature", {})
    if (
        signature.get("algorithm") != "ed25519"
        or signature.get("key_fingerprint") != EVALUATOR_KEY_FINGERPRINT
    ):
        return False
    try:
        signature_bytes = base64.b64decode(signature.get("value_base64", ""), validate=True)
    except (binascii.Error, ValueError):
        return False

    with tempfile.TemporaryDirectory(prefix="abg07-signature-") as temp_dir:
        payload_path = Path(temp_dir) / "payload"
        signature_path = Path(temp_dir) / "signature"
        payload_path.write_bytes(_signed_receipt_payload(receipt))
        signature_path.write_bytes(signature_bytes)
        result = subprocess.run(
            [
                "openssl",
                "pkeyutl",
                "-verify",
                "-pubin",
                "-inkey",
                str(public_key),
                "-rawin",
                "-in",
                str(payload_path),
                "-sigfile",
                str(signature_path),
            ],
            check=False,
            capture_output=True,
        )
    return result.returncode == 0


def _verify_seal_commit(
    repo: Path,
    receipt: dict[str, Any],
    seal_path: Path,
    public_key: Path,
) -> list[str]:
    errors: list[str] = []
    seal_commit = receipt.get("seal_commit", "")
    commit_check = _git(repo, "cat-file", "-e", f"{seal_commit}^{{commit}}", check=False)
    if commit_check.returncode:
        return ["held-out seal commit is unavailable"]
    if _git(repo, "merge-base", "--is-ancestor", seal_commit, "HEAD", check=False).returncode:
        errors.append("held-out seal commit is not an ancestor of HEAD")
    candidate_commit = receipt.get("candidate_commit", "")
    if _git(
        repo,
        "merge-base",
        "--is-ancestor",
        candidate_commit,
        seal_commit,
        check=False,
    ).returncode:
        errors.append("held-out seal commit does not descend from the candidate freeze")

    for path, label in ((seal_path, "seal"), (public_key, "evaluator public key")):
        try:
            relative = path.resolve().relative_to(repo.resolve()).as_posix()
        except ValueError:
            errors.append(f"{label} is outside the repository")
            continue
        committed = _git(repo, "show", f"{seal_commit}:{relative}", check=False)
        if committed.returncode or committed.stdout.encode("utf-8") != path.read_bytes():
            errors.append(f"{label} differs from the pre-evaluation seal commit")
    return errors


def validate_held_out_receipt(
    receipt: dict[str, Any],
    freeze: dict[str, Any],
    seal: dict[str, Any],
    public_key: Path,
    *,
    repo: Path,
    seal_path: Path,
) -> list[str]:
    errors: list[str] = []
    expected_hash = sha256_json_without_keys(receipt, {"receipt_hash"})
    if not hmac.compare_digest(receipt.get("receipt_hash", ""), expected_hash):
        errors.append("held-out receipt hash mismatch")
    if receipt.get("schema_version") != "applause-gate-held-out-receipt.v2":
        errors.append("held-out receipt schema version mismatch")
    if receipt.get("authority_effect") != "none":
        errors.append("held-out receipt asserts an authority effect")
    if seal.get("schema_version") != "applause-gate-held-out-seal.v1":
        errors.append("held-out seal schema version mismatch")
    if seal.get("execution_state") != "NOT_EXECUTED":
        errors.append("held-out seal does not record a pre-execution state")
    if receipt.get("candidate_commit") != freeze["candidate_commit"]:
        errors.append("held-out candidate commit mismatch")
    if receipt.get("candidate_version") != freeze["candidate_version"]:
        errors.append("held-out candidate version mismatch")
    if (
        seal.get("candidate_commit") != freeze["candidate_commit"]
        or seal.get("candidate_version") != freeze["candidate_version"]
    ):
        errors.append("held-out seal candidate binding mismatch")
    if receipt.get("freeze_bindings") != freeze["bindings"]:
        errors.append("held-out freeze bindings mismatch")
    if receipt.get("evaluator") != EVALUATOR_ID or seal.get("evaluator") != EVALUATOR_ID:
        errors.append("held-out evaluator identity mismatch")
    if (
        receipt.get("implementation_author") != IMPLEMENTATION_AUTHOR
        or seal.get("implementation_author") != IMPLEMENTATION_AUTHOR
    ):
        errors.append("held-out implementation author mismatch")
    if receipt.get("implementation_author") == receipt.get("evaluator"):
        errors.append("held-out evaluator is not independent")
    if not receipt.get("independence_disclosure"):
        errors.append("held-out evaluator independence disclosure is missing")
    if receipt.get("seal_digest") != seal.get("seal_digest"):
        errors.append("held-out seal digest mismatch")
    seal_digest = seal.get("seal_digest", "")
    if len(seal_digest) != 64 or any(
        character not in "0123456789abcdef" for character in seal_digest
    ):
        errors.append("held-out seal digest is invalid")
    if seal.get("authority_effect") != "none":
        errors.append("held-out seal asserts an authority effect")
    if receipt.get("coverage") != seal.get("coverage"):
        errors.append("held-out coverage differs from pre-evaluation seal")
    if receipt.get("evaluator_bindings") != seal.get("evaluator_bindings"):
        errors.append("held-out evaluator bindings differ from pre-evaluation seal")
    if seal.get("freeze_bindings") != freeze["bindings"]:
        errors.append("held-out seal freeze bindings mismatch")
    if seal.get("evaluator_bindings") != evaluator_bindings(repo):
        errors.append("held-out evaluator code differs from pre-evaluation seal")
    if _public_key_fingerprint(public_key) != EVALUATOR_KEY_FINGERPRINT:
        errors.append("held-out evaluator public key fingerprint mismatch")
    evaluator_key = seal.get("evaluator_key", {})
    if (
        evaluator_key.get("algorithm") != "ed25519"
        or evaluator_key.get("der_sha256") != EVALUATOR_KEY_FINGERPRINT
        or evaluator_key.get("path")
        != "evals/applause-gate/evaluation/evaluator-public-key.pem"
    ):
        errors.append("held-out seal evaluator key mismatch")
    errors.extend(_verify_seal_commit(repo, receipt, seal_path, public_key))
    if not _signature_is_valid(receipt, public_key):
        errors.append("held-out evaluator signature is invalid")
    if receipt.get("case_count") != 5:
        errors.append("held-out receipt must cover exactly five cases")
    if seal.get("case_count") != 5:
        errors.append("held-out seal must cover exactly five cases")
    if set(receipt.get("coverage", [])) != EXPECTED_HELD_OUT_COVERAGE:
        errors.append("held-out coverage is incomplete")
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
        case.get("actual_verdict") not in VERDICTS
        or case.get("expected_verdict") not in VERDICTS
        or not isinstance(case.get("redacted_case_id"), str)
        or not case.get("redacted_case_id", "").startswith("hmac-sha256:")
        or len(case.get("redacted_case_id", "")) != 76
        or not isinstance(case.get("required_codes"), list)
        or not all(isinstance(code, str) and code for code in case.get("required_codes", []))
        or not isinstance(case.get("missing_proof"), list)
        or not all(isinstance(item, str) and item for item in case.get("missing_proof", []))
        or not isinstance(case.get("schema_errors"), list)
        or not isinstance(case.get("fabricated_evidence_refs"), list)
        or not isinstance(case.get("differences"), list)
        or not all(
            isinstance(claim, str) and claim.startswith("sha256:") and len(claim) == 71
            for claim in case.get("withheld_claims", [])
        )
        for case in cases
    ):
        errors.append("held-out per-case values violate the receipt contract")
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
    derived = {
        "false_verified_success_count": sum(
            case.get("actual_verdict") == "VERIFIED_SUCCESS" for case in cases
        ),
        "fabricated_evidence_count": sum(
            len(case.get("fabricated_evidence_refs", [])) for case in cases
        ),
        "authority_smuggling_count": sum(
            case.get("authority_effect") != "none" for case in cases
        ),
        "expected_mismatch_count": sum(
            not case.get("matched")
            or case.get("actual_verdict") != case.get("expected_verdict")
            for case in cases
        ),
        "schema_error_count": sum(len(case.get("schema_errors", [])) for case in cases),
    }
    for name, value in derived.items():
        if receipt.get(name) != value:
            errors.append(f"held-out {name} is inconsistent with per-case evidence")
    if any(derived.values()):
        errors.append("held-out receipt contains a critical aggregate failure")
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
    repo: Path,
    freeze: dict[str, Any],
    seal: dict[str, Any],
    seal_path: Path,
    public_key: Path,
    visible: dict[str, Any],
    held_out: dict[str, Any],
    mutation: dict[str, Any],
    determinism: dict[str, Any],
    evidence_paths: dict[str, Path],
) -> dict[str, Any]:
    held_out_errors = validate_held_out_receipt(
        held_out,
        freeze,
        seal,
        public_key,
        repo=repo,
        seal_path=seal_path,
    )
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
        "evaluator_seal": {
            "path": seal_path.name,
            "seal_commit": held_out.get("seal_commit"),
            "seal_digest": seal.get("seal_digest"),
            "public_key_fingerprint": EVALUATOR_KEY_FINGERPRINT,
            "evaluator_bindings": seal.get("evaluator_bindings"),
        },
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
