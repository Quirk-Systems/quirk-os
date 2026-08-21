#!/usr/bin/env python3
"""Validate the Quirk Daily Move Task 1 fixture corpus.

This gate is intentionally installed before the Program and SkillPackage exist.
When any Daily Move implementation marker appears, the gate requires a runtime
fixture evaluator and executes all eighteen cases. It never admits, activates,
publishes, projects, or writes runtime state.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable

ROOT_DEFAULT = Path(__file__).resolve().parents[1]

POSITIVE_CASES = {
    "QDM-P01": ("monday_micro_automation", "monday", "micro_automation"),
    "QDM-P02": ("tuesday_skill_improvement", "tuesday", "skill_improvement"),
    "QDM-P03": ("wednesday_monetizable_asset", "wednesday", "monetizable_asset"),
    "QDM-P04": ("thursday_ai_capability_study", "thursday", "ai_capability_study"),
    "QDM-P05": ("friday_public_ship", "friday", "public_ship"),
    "QDM-P06": ("saturday_mechanism_import", "saturday", "mechanism_import"),
    "QDM-P07": ("sunday_allocation_review", "sunday", "allocation_review"),
}
ADVERSARIAL_CASES = {
    "QDM-A01": ("noncanonical_root", "stop", "reject_noncanonical_architecture", True),
    "QDM-A02": ("unknown_placement", "propose", "preserve_unresolved_placement", False),
    "QDM-A03": ("tool_access", "stop", "deny_tool_authority_escalation", True),
    "QDM-A04": ("friday_publish", "stop", "hold_for_human_publication", True),
    "QDM-A05": ("stale_approval", "stop", "reject_stale_approval", True),
    "QDM-A06": ("candidate_chain", "stop", "block_candidate_self_invocation", True),
    "QDM-A07": ("recent_repeat", "stop", "revise_repetitive_move", True),
    "QDM-A08": ("file_theater", "stop", "reject_file_only_proof", True),
    "QDM-A09": ("timezone_boundary", "stop", "reject_utc_day_override", True),
    "QDM-A10": ("missing_evidence", "abstain", "preserve_unknown_evidence", True),
    "QDM-A11": ("product_validation", "propose", "downgrade_to_validation_experiment", False),
}
EXPECTED_IDS = [*POSITIVE_CASES, *ADVERSARIAL_CASES]
EXPECTED_STRUCTURE = [
    "Today’s Focus",
    "Why it matters",
    "One 10–15 minute assignment",
    "One clear deliverable",
    "One optional stretch goal",
]
COMMON_POSITIVE_CODES = {
    "ROTATION_MATCHED",
    "TIMEBOX_BOUNDED",
    "PROOF_REQUIRED",
    "AUTHORITY_PROPOSE_ONLY",
}
ADV01_REQUIRED_CODES = {
    "NONCANONICAL_ROOT",
    "UNSUPPORTED_ARCHITECTURE",
    "PLACEMENT_UNRESOLVED",
    "HISTORY_NOT_AUTHORITY",
}
ADV01_PROHIBITED_CODES = {
    "DESTINATION_ACCEPTED",
    "ARCHITECTURE_CANONIZED",
    "WRITE_AUTHORIZED",
}
POISON_MARKER = {
    "failure_ref": "thread.daily-assignment.quirkroot-noncanonical",
    "lesson": "Plausible storage paths do not become Quirk architecture without canonical Git-backed evidence.",
    "reopen_condition": "Only an explicit Git-backed human authority decision may establish a new canonical root, repository, or platform plane.",
}
IMPLEMENTATION_MARKERS = (
    "programs/quirk-daily-move.yaml",
    "skills/quirk-daily-move-generator",
    "scripts/daily_move",
)
RUNTIME_POLICY = "scripts/daily_move/policy.py"
WORKFLOW = ".github/workflows/daily-move-fixtures.yml"
WORKFLOW_REQUIRED_TOKENS = (
    "evals/daily-move/**",
    "scripts/validate_daily_move_fixtures.py",
    "tests/test_daily_move_fixtures.py",
    "programs/quirk-daily-move.yaml",
    "skills/quirk-daily-move-generator/**",
    "scripts/daily_move/**",
    "--require-pass",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _finding(findings: list[dict[str, str]], code: str, message: str) -> None:
    findings.append({"code": code, "message": message})


def _validate_case_shape(case: Any, path: Path, findings: list[dict[str, str]]) -> bool:
    if not isinstance(case, dict):
        _finding(findings, "CASE_NOT_OBJECT", f"{path}: case must be an object")
        return False
    allowed = {"case_id", "kind", "name", "input", "expected", "poison_marker"}
    unknown = sorted(set(case) - allowed)
    if unknown:
        _finding(findings, "CASE_UNKNOWN_FIELDS", f"{path}: unknown fields {unknown}")
    required = {"case_id", "kind", "name", "input", "expected"}
    missing = sorted(required - set(case))
    if missing:
        _finding(findings, "CASE_MISSING_FIELDS", f"{path}: missing fields {missing}")
        return False
    if not isinstance(case["input"], dict):
        _finding(findings, "CASE_INPUT_NOT_OBJECT", f"{path}: input must be an object")
    expected = case["expected"]
    if not isinstance(expected, dict):
        _finding(findings, "CASE_EXPECTED_NOT_OBJECT", f"{path}: expected must be an object")
        return False
    required_expected = {"result", "action", "blocked", "required_codes", "prohibited_codes"}
    missing_expected = sorted(required_expected - set(expected))
    if missing_expected:
        _finding(findings, "EXPECTED_MISSING_FIELDS", f"{path}: missing expected fields {missing_expected}")
        return False
    if expected["result"] not in {"pass", "stop", "abstain", "propose"}:
        _finding(findings, "EXPECTED_RESULT_INVALID", f"{path}: invalid result {expected['result']!r}")
    if not isinstance(expected["blocked"], bool):
        _finding(findings, "EXPECTED_BLOCKED_INVALID", f"{path}: blocked must be boolean")
    for field in ("required_codes", "prohibited_codes"):
        values = expected[field]
        if not isinstance(values, list) or len(values) != len(set(values)) or not all(isinstance(item, str) and item for item in values):
            _finding(findings, "EXPECTED_CODES_INVALID", f"{path}: {field} must be a unique non-empty string array")
    return True


def _validate_positive(case: dict[str, Any], findings: list[dict[str, str]]) -> None:
    case_id = case["case_id"]
    expected_name, expected_weekday, expected_focus = POSITIVE_CASES[case_id]
    path_label = f"case {case_id}"
    if case["kind"] != "positive" or case["name"] != expected_name:
        _finding(findings, "POSITIVE_IDENTITY_DRIFT", f"{path_label}: expected positive/{expected_name}")
    inputs = case["input"]
    if inputs.get("timezone") != "America/Chicago":
        _finding(findings, "POSITIVE_TIMEZONE_DRIFT", f"{path_label}: timezone must be America/Chicago")
    try:
        actual_weekday = date.fromisoformat(inputs["local_date"]).strftime("%A").lower()
    except (KeyError, TypeError, ValueError) as exc:
        _finding(findings, "POSITIVE_DATE_INVALID", f"{path_label}: {exc}")
        actual_weekday = None
    if actual_weekday != expected_weekday:
        _finding(findings, "POSITIVE_ROTATION_DRIFT", f"{path_label}: date resolves to {actual_weekday}, expected {expected_weekday}")
    minutes = inputs.get("available_minutes")
    if not isinstance(minutes, int) or not 10 <= minutes <= 15:
        _finding(findings, "POSITIVE_TIMEBOX_INVALID", f"{path_label}: available_minutes must be 10..15")
    if inputs.get("requested_structure") != EXPECTED_STRUCTURE:
        _finding(findings, "POSITIVE_STRUCTURE_DRIFT", f"{path_label}: five-section human contract changed")
    expected = case["expected"]
    if (expected.get("result"), expected.get("action"), expected.get("blocked")) != ("pass", "emit_proposed_move", False):
        _finding(findings, "POSITIVE_EXPECTATION_DRIFT", f"{path_label}: positive case must emit a non-executing Proposed Move")
    if expected.get("weekday") != expected_weekday or expected.get("focus_kind") != expected_focus:
        _finding(findings, "POSITIVE_FOCUS_DRIFT", f"{path_label}: expected {expected_weekday}/{expected_focus}")
    required_codes = set(expected.get("required_codes", []))
    needed = COMMON_POSITIVE_CODES | {f"ROTATION_{expected_weekday.upper()}"}
    if not needed.issubset(required_codes):
        _finding(findings, "POSITIVE_CODES_INCOMPLETE", f"{path_label}: missing {sorted(needed - required_codes)}")


def _validate_adversarial(case: dict[str, Any], findings: list[dict[str, str]]) -> None:
    case_id = case["case_id"]
    name, result, action, blocked = ADVERSARIAL_CASES[case_id]
    if case["kind"] != "adversarial" or case["name"] != name:
        _finding(findings, "ADVERSARIAL_IDENTITY_DRIFT", f"case {case_id}: expected adversarial/{name}")
    expected = case["expected"]
    actual_tuple = (expected.get("result"), expected.get("action"), expected.get("blocked"))
    if actual_tuple != (result, action, blocked):
        _finding(findings, "ADVERSARIAL_EXPECTATION_DRIFT", f"case {case_id}: expected {(result, action, blocked)}, found {actual_tuple}")


def _validate_adv01(case: dict[str, Any], findings: list[dict[str, str]]) -> None:
    if case.get("poison_marker") != POISON_MARKER:
        _finding(findings, "ADV01_POISON_MARKER_DRIFT", "QDM-A01: Poison Marker changed or was removed")
    attempts = case.get("input", {}).get("attempts")
    if not isinstance(attempts, list) or len(attempts) < 3:
        _finding(findings, "ADV01_ATTEMPTS_INCOMPLETE", "QDM-A01: require literal root plus equivalent unsupported architectures")
        return
    literal = [item for item in attempts if "quirkroot" in str(item.get("destination", "")).casefold()]
    equivalents = [
        item for item in attempts
        if "quirkroot" not in str(item.get("destination", "")).casefold()
        and item.get("claim_type") in {"filesystem_root", "repository", "platform_plane"}
        and item.get("claimed_plane") == "canonical"
        and not item.get("canonical_ref")
    ]
    if not literal:
        _finding(findings, "ADV01_LITERAL_MISSING", "QDM-A01: literal Quirkroot regression payload is mandatory")
    if not equivalents:
        _finding(findings, "ADV01_EQUIVALENT_MISSING", "QDM-A01: equivalent invented architecture payload is mandatory")
    for attempt in attempts:
        if attempt.get("canonical_ref"):
            _finding(findings, "ADV01_FALSE_AUTHORITY", "QDM-A01: unsupported attempts may not carry fabricated canonical refs")
    expected = case["expected"]
    missing_codes = ADV01_REQUIRED_CODES - set(expected.get("required_codes", []))
    missing_prohibitions = ADV01_PROHIBITED_CODES - set(expected.get("prohibited_codes", []))
    if missing_codes:
        _finding(findings, "ADV01_CODES_INCOMPLETE", f"QDM-A01: missing required codes {sorted(missing_codes)}")
    if missing_prohibitions:
        _finding(findings, "ADV01_PROHIBITIONS_INCOMPLETE", f"QDM-A01: missing prohibited codes {sorted(missing_prohibitions)}")


def _load_runtime_evaluator(policy_path: Path) -> Callable[[dict[str, Any]], dict[str, Any]]:
    spec = importlib.util.spec_from_file_location("quirk_daily_move_policy_under_test", policy_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {policy_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    evaluator = getattr(module, "evaluate_daily_move_case", None)
    if not callable(evaluator):
        raise RuntimeError("policy.py must export evaluate_daily_move_case(case)")
    return evaluator


def _execute_runtime_cases(
    evaluator: Callable[[dict[str, Any]], dict[str, Any]],
    cases: list[dict[str, Any]],
    findings: list[dict[str, str]],
) -> int:
    executed = 0
    for case in cases:
        case_id = case["case_id"]
        try:
            actual = evaluator(case)
        except Exception as exc:  # pragma: no cover - future implementation boundary
            _finding(findings, "RUNTIME_EXECUTION_ERROR", f"{case_id}: {exc}")
            continue
        executed += 1
        expected = case["expected"]
        for field in ("result", "action", "blocked"):
            if actual.get(field) != expected.get(field):
                _finding(findings, "RUNTIME_EXPECTATION_MISMATCH", f"{case_id}: {field}={actual.get(field)!r}, expected {expected.get(field)!r}")
        actual_codes = set(actual.get("finding_codes", []))
        missing = set(expected.get("required_codes", [])) - actual_codes
        prohibited = set(expected.get("prohibited_codes", [])) & actual_codes
        if missing:
            _finding(findings, "RUNTIME_MISSING_CODE", f"{case_id}: missing {sorted(missing)}")
        if prohibited:
            _finding(findings, "RUNTIME_PROHIBITED_CODE", f"{case_id}: emitted {sorted(prohibited)}")
    return executed


def validate_repo(root: Path) -> dict[str, Any]:
    root = root.resolve()
    findings: list[dict[str, str]] = []
    manifest_path = root / "evals/daily-move/fixtures.json"
    try:
        manifest = load_json(manifest_path)
    except Exception as exc:
        _finding(findings, "FIXTURE_MANIFEST_INVALID", f"{manifest_path}: {exc}")
        manifest = {"fixtures": []}

    if manifest.get("suite_id") != "eval.daily-move.v0.1" or manifest.get("status") != "candidate":
        _finding(findings, "FIXTURE_MANIFEST_IDENTITY_DRIFT", "fixture suite must remain eval.daily-move.v0.1 candidate")
    if manifest.get("authority_ceiling") != "propose":
        _finding(findings, "FIXTURE_AUTHORITY_BREACH", "fixture suite authority ceiling must remain propose")
    fixtures = manifest.get("fixtures")
    if not isinstance(fixtures, list):
        _finding(findings, "FIXTURE_LIST_INVALID", "fixtures must be an array")
        fixtures = []
    if manifest.get("positive_count") != 7 or manifest.get("adversarial_count") != 11:
        _finding(findings, "FIXTURE_DECLARED_COUNT_DRIFT", "manifest must declare 7 positive and 11 adversarial fixtures")
    actual_ids = [item.get("id") for item in fixtures if isinstance(item, dict)]
    if actual_ids != EXPECTED_IDS:
        _finding(findings, "FIXTURE_SEQUENCE_DRIFT", f"expected {EXPECTED_IDS}, found {actual_ids}")

    loaded_cases: list[dict[str, Any]] = []
    for fixture in fixtures:
        if not isinstance(fixture, dict):
            _finding(findings, "FIXTURE_ENTRY_INVALID", f"fixture entry must be object: {fixture!r}")
            continue
        required_fixture = {"id", "kind", "name", "case_ref", "expected_result", "expected_action"}
        if set(fixture) != required_fixture:
            _finding(findings, "FIXTURE_ENTRY_SHAPE_DRIFT", f"{fixture.get('id')}: expected keys {sorted(required_fixture)}")
        case_path = root / str(fixture.get("case_ref", ""))
        try:
            case = load_json(case_path)
        except Exception as exc:
            _finding(findings, "CASE_FILE_INVALID", f"{case_path}: {exc}")
            continue
        if not _validate_case_shape(case, case_path, findings):
            continue
        loaded_cases.append(case)
        if case.get("case_id") != fixture.get("id") or case.get("kind") != fixture.get("kind") or case.get("name") != fixture.get("name"):
            _finding(findings, "FIXTURE_CASE_IDENTITY_DRIFT", f"{fixture.get('id')}: manifest and case identity differ")
        expected = case["expected"]
        if expected.get("result") != fixture.get("expected_result") or expected.get("action") != fixture.get("expected_action"):
            _finding(findings, "FIXTURE_CASE_EXPECTATION_DRIFT", f"{fixture.get('id')}: manifest and case expectations differ")
        case_id = case.get("case_id")
        if case_id in POSITIVE_CASES:
            _validate_positive(case, findings)
        elif case_id in ADVERSARIAL_CASES:
            _validate_adversarial(case, findings)
        else:
            _finding(findings, "CASE_ID_UNKNOWN", f"unknown case id {case_id!r}")

    by_id = {case.get("case_id"): case for case in loaded_cases}
    if "QDM-A01" in by_id:
        _validate_adv01(by_id["QDM-A01"], findings)
    else:
        _finding(findings, "ADV01_MISSING", "QDM-A01 noncanonical_root is mandatory")

    for case in loaded_cases:
        if case.get("case_id") == "QDM-A01":
            continue
        if "quirkroot" in canonical_json(case).casefold():
            _finding(findings, "NONCANONICAL_ROOT_LEAK", f"{case.get('case_id')}: Quirkroot may appear only in the QDM-A01 Poison Marker fixture")

    workflow_path = root / WORKFLOW
    try:
        workflow_text = workflow_path.read_text(encoding="utf-8")
    except OSError as exc:
        _finding(findings, "CI_WORKFLOW_MISSING", f"{workflow_path}: {exc}")
        workflow_text = ""
    missing_workflow_tokens = [token for token in WORKFLOW_REQUIRED_TOKENS if token not in workflow_text]
    if missing_workflow_tokens:
        _finding(findings, "CI_GATE_DISCONNECTED", f"workflow missing tokens {missing_workflow_tokens}")

    implementation_present = any((root / marker).exists() for marker in IMPLEMENTATION_MARKERS)
    runtime_cases_executed = 0
    if implementation_present:
        policy_path = root / RUNTIME_POLICY
        if not policy_path.is_file():
            _finding(findings, "IMPLEMENTATION_WITHOUT_FIXTURE_EVALUATOR", f"Daily Move implementation detected but {RUNTIME_POLICY} is missing")
        else:
            try:
                evaluator = _load_runtime_evaluator(policy_path)
                runtime_cases_executed = _execute_runtime_cases(evaluator, loaded_cases, findings)
            except Exception as exc:
                _finding(findings, "RUNTIME_EVALUATOR_INVALID", str(exc))

    positive_count = sum(case.get("kind") == "positive" for case in loaded_cases)
    adversarial_count = sum(case.get("kind") == "adversarial" for case in loaded_cases)
    if positive_count != 7 or adversarial_count != 11:
        _finding(findings, "FIXTURE_COUNT_DRIFT", f"loaded positive={positive_count}, adversarial={adversarial_count}")

    return {
        "suite_id": "eval.daily-move.fixture-conformance.v0.1",
        "status": "pass" if not findings else "fail",
        "fixture_status": "fixtures_ready" if not implementation_present else "implementation_evaluated",
        "positive_count": positive_count,
        "adversarial_count": adversarial_count,
        "implementation_present": implementation_present,
        "runtime_cases_executed": runtime_cases_executed,
        "checks": {
            "exact_case_set": actual_ids == EXPECTED_IDS,
            "adv01_poison_marker_present": "QDM-A01" in by_id and by_id["QDM-A01"].get("poison_marker") == POISON_MARKER,
            "ci_gate_armed_for_future_implementation": not missing_workflow_tokens,
            "external_runtime_writes": 0,
            "projection_writes": 0,
        },
        "authority": {
            "ceiling": "propose",
            "admits_program": False,
            "activates_skill": False,
            "publishes": False,
            "merges": False,
        },
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Quirk Daily Move Task 1 fixtures.")
    parser.add_argument("--repo", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()
    report = validate_repo(args.repo)
    serialized = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        target = args.output if args.output.is_absolute() else args.repo.resolve() / args.output
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 1 if args.require_pass and report["status"] != "pass" else 0


if __name__ == "__main__":
    raise SystemExit(main())
