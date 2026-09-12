"""Run and resolve bounded evaluation evidence using existing Quirk work objects.

Run files are unsigned observations. Resolve verifies their declared case set,
outcomes and exact source binding; it does not authenticate a human, issue a
grant, or substitute for retrieving evidence from a trusted execution source.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import traceback
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / "tests" / "exact_digest_publish"
EVIDENCE = ROOT / "evals" / "exact_digest_publish"
CASE_PREFIX = "test_enforcement.EnforcementTests."
REQUIRED_CASES = tuple(CASE_PREFIX + name for name in (
    "test_01_synthetic_authorizer_permits_exact_bytes_and_receipt",
    "test_02_one_thousand_evaluations_cannot_create_any_grant",
    "test_03_evaluator_and_composer_cannot_issue_or_forge_human_grants",
    "test_04_additional_fields_cannot_turn_evidence_into_authority",
    "test_05_kernel_denies_both_workers_direct_writes",
    "test_06_kernel_peer_identity_cannot_be_impersonated",
    "test_07_roles_cannot_borrow_each_others_actions",
    "test_08_each_subject_dimension_is_bound_to_approval",
    "test_09_scope_digest_and_decision_must_match_human_request",
    "test_10_current_evaluation_must_pass_and_not_be_invalidated",
    "test_11_policy_revision_invalidates_old_evidence_and_grant",
    "test_12_revocation_before_dispatch_blocks_publication",
    "test_13_expired_approval_is_not_effective",
    "test_14_stale_evaluation_cannot_use_current_grant",
    "test_15_grant_is_single_use_and_request_replay_has_no_duplicate_effect",
    "test_16_grant_and_request_ids_cannot_be_rebound",
    "test_17_staging_new_bytes_does_not_redirect_old_approval",
    "test_18_changed_snapshot_bytes_fail_closed",
    "test_19_second_broker_cannot_own_the_same_state",
    "test_20_revocation_after_dispatch_preserves_historical_receipt",
    "test_21_expiry_after_dispatch_preserves_historical_receipt",
    "test_22_crash_before_dispatch_consumes_grant_and_does_not_retry",
    "test_23_crash_after_dispatch_reconciles_one_exact_effect",
    "test_24_unexpected_output_is_unknown_and_never_redispatched",
    "test_25_grant_expiry_during_dispatch_preparation_blocks_effect",
    "test_26_evaluation_expiry_during_dispatch_preparation_blocks_effect",
))
REQUIRED_SOURCES = {
    "scripts/exact_digest_publish/__init__.py",
    "scripts/exact_digest_publish/broker.py",
    "scripts/exact_digest_publish/client.py",
    "scripts/exact_digest_publish/authorizer.py",
    "scripts/exact_digest_publish/model.py",
    "scripts/exact_digest_publish/proof.py",
    "tests/exact_digest_publish/test_enforcement.py",
    "tests/exact_digest_publish/peer_client.py",
    "docs/exact_digest_publish/PLAN.md",
    ".github/workflows/exact-digest-publishing.yml",
    "schemas/proposed-move.schema.json",
    "schemas/artifact.schema.json",
}
ASSUMPTIONS = (
    "Linux kernel and root test supervisor are trusted; broker and workers are distinct non-root UIDs.",
    "Broker code/configuration and their ancestors are controlled by the trusted deployment authority.",
    "Authorizer UID and credentials are not controlled by evaluator or composer processes.",
    "No privileged file descriptor or privileged process capability is delegated to worker identities.",
    "The protected local filesystem sink is the complete publication effect under test.",
    "Evidence is retrieved from a trusted execution source; these JSON run records are unsigned.",
)
WITHHELD = (
    "Actual human presence, understanding, and consent: automated authorizer is a synthetic fixture.",
    "Production authentication, deployment admission, external publishing adapters, and cloud credential isolation.",
    "Protection against compromised root, kernel, broker, deployment authority, or authorizer session.",
    "Canonical admission, live activation, or permission manufactured by evaluation success.",
)
BOUNDED_CLAIMS = (
    "Passing evaluations alone do not create grants or authorize publication.",
    "Kernel-authenticated evaluator and composer identities cannot invoke authorizer operations or write protected state and sink paths.",
    "Publication binds artifact identity, payload digest, operation, destination and current policy; time validity is rechecked immediately before publication.",
    "Missing, expired, revoked, used or scope-mismatched grants and non-current evaluation passes block new publication.",
    "Exact staged bytes, single-use grants, request idempotency and crash reconciliation constrain the local effect and its receipt.",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def encoded(value) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_manifest() -> dict:
    names = set(REQUIRED_SOURCES)
    for directory in (ROOT / "scripts" / "exact_digest_publish", TESTS):
        names.update(str(path.relative_to(ROOT)) for path in directory.rglob("*.py"))
    files = {}
    for name in sorted(names):
        path = ROOT / name
        if not path.is_file() or path.is_symlink():
            raise ValueError("Missing or symlinked proof source: " + name)
        data = path.read_bytes()
        files[name] = {"sha256": digest(data), "bytes": len(data)}
    return {"algorithm": "sha256", "files": files, "manifest_sha256": digest(encoded(files))}


def read_optional(path: str):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def environment() -> dict:
    return {"platform": sys.platform, "kernel": platform.release(), "machine": platform.machine(),
            "python": sys.version, "executable": sys.executable,
            "uid": os.getuid(), "euid": os.geteuid(), "gid": os.getgid(),
            "egid": os.getegid(), "supplementary_groups": os.getgroups(),
            "uid_map": read_optional("/proc/self/uid_map"),
            "gid_map": read_optional("/proc/self/gid_map"),
            "runner": {key: os.environ[key] for key in
                       ("GITHUB_REPOSITORY", "GITHUB_SHA", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT",
                        "GITHUB_WORKFLOW", "GITHUB_JOB") if key in os.environ}}


def test_ids(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from test_ids(test)
        else:
            yield test.id()


class ObservedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cases = {}
        self.suite_errors = []

    def startTest(self, test):
        self.cases[test.id()] = {"id": test.id(), "outcome": "running", "started_at": now(),
                                 "finished_at": None, "details": []}
        super().startTest(test)

    def record(self, test, outcome, detail=None):
        if test.id() not in self.cases:
            self.suite_errors.append({"id": test.id(), "outcome": outcome, "detail": detail})
            return
        case = self.cases[test.id()]
        case["outcome"] = outcome
        if detail:
            case["details"].append(detail)

    def stopTest(self, test):
        self.cases[test.id()]["finished_at"] = now()
        super().stopTest(test)

    def addSuccess(self, test):
        self.record(test, "passed")
        super().addSuccess(test)

    def addFailure(self, test, err):
        self.record(test, "failed", self._exc_info_to_string(err, test))
        super().addFailure(test, err)

    def addError(self, test, err):
        self.record(test, "error", self._exc_info_to_string(err, test))
        super().addError(test, err)

    def addSkip(self, test, reason):
        self.record(test, "skipped", reason)
        super().addSkip(test, reason)

    def addExpectedFailure(self, test, err):
        self.record(test, "expected_failure", self._exc_info_to_string(err, test))
        super().addExpectedFailure(test, err)

    def addUnexpectedSuccess(self, test):
        self.record(test, "unexpected_success")
        super().addUnexpectedSuccess(test)

    def addSubTest(self, test, subtest, err):
        if err is not None:
            self.record(test, "failed", {"subtest": subtest.id(),
                                         "traceback": self._exc_info_to_string(err, subtest)})
        super().addSubTest(test, subtest, err)


def evaluate_run(record: dict, current_manifest: dict) -> tuple[bool, list[str]]:
    """Recompute eligibility; neither a claimed pass nor a count is sufficient."""
    errors = []
    if record.get("format_version") != 1 or record.get("authority_mode") != "test_fixture":
        errors.append("UNRECOGNIZED_RUN_FORMAT_OR_AUTHORITY_MODE")
    required = list(REQUIRED_CASES)
    if record.get("required_cases") != required:
        errors.append("REQUIRED_CASE_CONTRACT_CHANGED")
    discovered = record.get("discovered_cases")
    if not isinstance(discovered, list) or sorted(discovered) != sorted(required):
        errors.append("MISSING_EXTRA_OR_DUPLICATE_DISCOVERED_CASES")
    cases = record.get("cases")
    if not isinstance(cases, list):
        cases = []
        errors.append("MALFORMED_CASE_RESULTS")
    ids = [case.get("id") if isinstance(case, dict) else None for case in cases]
    if any(type(value) is not str for value in ids) or len(ids) != len(required) or set(ids) != set(required):
        errors.append("MISSING_EXTRA_OR_DUPLICATE_EXECUTED_CASES")
    if any(not isinstance(case, dict) or case.get("outcome") != "passed" for case in cases):
        errors.append("A_CASE_DID_NOT_PASS")
    if record.get("suite_errors") != []:
        errors.append("SUITE_OR_PREFLIGHT_ERRORS")
    summary = record.get("result", {})
    if (not isinstance(summary, dict) or type(summary.get("tests_run")) is not int
            or summary.get("tests_run") != len(required)
            or summary.get("was_successful") is not True
            or any(summary.get(name) != 0 for name in
                   ("failures", "errors", "skipped", "expected_failures", "unexpected_successes"))):
        errors.append("UNSUCCESSFUL_OR_INCOMPLETE_TEST_RESULT")
    env = record.get("environment", {})
    if not isinstance(env, dict) or env.get("platform") != "linux" or env.get("euid") != 0:
        errors.append("PROCESS_PROOF_ENVIRONMENT_NOT_ESTABLISHED")
    if (record.get("source_manifest") != current_manifest
            or record.get("source_manifest_after") != current_manifest):
        errors.append("SOURCE_BINDING_MISMATCH_OR_CHANGED_DURING_RUN")
    if record.get("trust_assumptions") != list(ASSUMPTIONS):
        errors.append("TRUST_ASSUMPTIONS_MISMATCH")
    return not errors, errors


def run(output: Path) -> int:
    before = source_manifest()
    record = {"format_version": 1, "run_id": str(uuid.uuid4()),
              "evaluation_ref": "eval.exact-digest-publish.process-isolation.v1",
              "authority_mode": "test_fixture", "started_at": now(),
              "environment": environment(), "source_manifest": before,
              "required_cases": list(REQUIRED_CASES), "trust_assumptions": list(ASSUMPTIONS),
              "command": [sys.executable, "-m", "scripts.exact_digest_publish.proof", "run",
                          "--output", str(output)],
              "test_command": [sys.executable, "-m", "unittest", "discover", "-s",
                               "tests/exact_digest_publish", "-v"],
              "execution_method": "unittest discovery and TestResult in this runner process",
              "evidence_origin": "Unsigned observed unittest result; verify the execution source separately."}
    try:
        suite = unittest.TestLoader().discover(str(TESTS), pattern="test_*.py")
        record["discovered_cases"] = list(test_ids(suite))
        result = unittest.TextTestRunner(verbosity=2, resultclass=ObservedResult).run(suite)
        record["cases"] = list(result.cases.values())
        record["suite_errors"] = result.suite_errors
        record["result"] = {"tests_run": result.testsRun, "was_successful": result.wasSuccessful(),
                            "failures": len(result.failures), "errors": len(result.errors),
                            "skipped": len(result.skipped), "expected_failures": len(result.expectedFailures),
                            "unexpected_successes": len(result.unexpectedSuccesses)}
    except Exception:
        record.setdefault("discovered_cases", [])
        record["cases"] = []
        record["suite_errors"] = [{"id": "runner", "outcome": "error", "detail": traceback.format_exc()}]
        record["result"] = {"tests_run": 0, "was_successful": False, "failures": 0, "errors": 1,
                            "skipped": 0, "expected_failures": 0, "unexpected_successes": 0}
    record["finished_at"] = now()
    try:
        after = source_manifest()
    except (OSError, ValueError) as error:
        after = {"error": str(error)}
    record["source_manifest_after"] = after
    verified, blockers = evaluate_run(record, before)
    record["bounded_verified"] = verified
    record["blockers"] = blockers
    record["verified_claims"] = list(BOUNDED_CLAIMS) if verified else []
    record["withheld_claims"] = list(WITHHELD)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(encoded(record))
    print(json.dumps({"run_id": record["run_id"], "bounded_verified": verified,
                      "tests_run": record["result"]["tests_run"], "output": str(output),
                      "blockers": blockers}, sort_keys=True))
    return 0 if verified else 1


def artifact(identifier, title, artifact_type, content_ref, data, run_ref, verified):
    return {"artifact_id": identifier, "title": title, "artifact_type": artifact_type,
            "created_by": "agent.codex", "created_at": now(), "run_receipt_ref": run_ref,
            "source_refs": [run_ref, "https://github.com/Quirk-Systems/quirk-core/pull/10"],
            "version": "0.1.0", "rights": {"status": "unclear", "owner_ref": None,
                                            "provenance_complete": False},
            "status": "produced", "content_ref": content_ref, "content_hash": digest(data),
            "evaluation": {"bounded_verified": verified, "authority_mode": "test_fixture",
                           "authority_effect": "none"},
            "metadata": {"maturity": "candidate", "owner_repository": "Quirk-Systems/quirk-os",
                         "schema_ref": "schemas/artifact.schema.json"}}


def resolve(run_path: Path) -> int:
    # Load validation before any writes; do not silently replace schema checking
    # with an ad hoc approximation when the repository dependency is unavailable.
    from jsonschema import Draft202012Validator, FormatChecker

    raw = run_path.read_bytes()
    record = json.loads(raw)
    if not isinstance(record, dict):
        raise ValueError("Run record must be a JSON object")
    current = source_manifest()
    verified, blockers = evaluate_run(record, current)
    relative = "evals/exact_digest_publish/"
    # Preserve previous run records by content identity; no history overwrite.
    run_name = "run-" + digest(raw) + ".json"
    run_ref = relative + run_name
    manifest_data = encoded(current)
    implementation = artifact("artifact.exact-digest-publish.implementation",
                              "Exact digest publication implementation manifest", "source_manifest",
                              relative + "manifest.json", manifest_data, run_ref, verified)
    proof = artifact("artifact.exact-digest-publish.proof", "Exact digest publication evaluation evidence",
                     "evaluation_evidence", run_ref, raw, run_ref, verified)
    proof["evaluation"].update({"blockers": blockers,
                                "verified_claims": list(BOUNDED_CLAIMS) if verified else [],
                                "withheld_claims": list(WITHHELD), "trust_assumptions": list(ASSUMPTIONS),
                                "source_manifest_sha256": current["manifest_sha256"],
                                "evidence_origin": "Unsigned run record; source authenticity is externally verified."})
    move_path = EVIDENCE / "proposed-move.json"
    move = json.loads(move_path.read_bytes())
    move["disposition"] = "verified" if verified else "implemented"
    move["implementation_ref"] = relative + "implementation-artifact.json"
    move["eval_refs"] = ["eval.exact-digest-publish.process-isolation.v1", run_ref]
    move["evidence_refs"] = [relative + "proof-artifact.json", run_ref, relative + "manifest.json"]
    move["receipt_ref"] = run_ref
    note = ("Constrain: verified only for the exact recorded sources and Linux local protected-sink boundary, "
            "using synthetic authorizer identities. " if verified else
            "Constrain: implementation exists; local boundary proof remains unresolved. Blockers: "
            + ", ".join(blockers) + ". ")
    move["resolution_note"] = note + "Actual human presence, production deployment, external publication, and Canon admission remain unproven; evaluation grants no authority."
    move["resolution_artifacts"] = list(dict.fromkeys(move["resolution_artifacts"] + [
        relative + "implementation-artifact.json", relative + "proof-artifact.json", relative + "manifest.json", run_ref]))
    checker = FormatChecker()
    for instance, schema_name in ((implementation, "artifact.schema.json"), (proof, "artifact.schema.json"),
                                   (move, "proposed-move.schema.json")):
        schema = json.loads((ROOT / "schemas" / schema_name).read_bytes())
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema, format_checker=checker).validate(instance)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / run_name).write_bytes(raw)
    (EVIDENCE / "manifest.json").write_bytes(manifest_data)
    (EVIDENCE / "implementation-artifact.json").write_bytes(encoded(implementation))
    (EVIDENCE / "proof-artifact.json").write_bytes(encoded(proof))
    move_path.write_bytes(encoded(move))
    print(json.dumps({"bounded_verified": verified, "disposition": move["disposition"],
                      "source_manifest_sha256": current["manifest_sha256"],
                      "proof_artifact": relative + "proof-artifact.json", "blockers": blockers}, sort_keys=True))
    return 0 if verified else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run_parser = commands.add_parser("run")
    run_parser.add_argument("--output", type=Path, required=True)
    resolve_parser = commands.add_parser("resolve")
    resolve_parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    try:
        return run(args.output) if args.command == "run" else resolve(args.run)
    except (ValueError, OSError, ImportError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
