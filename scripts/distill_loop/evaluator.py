"""Deterministic evaluator for distilled candidate eval cases.

Distilled candidates are not known to the shared skill evaluator, so their
cases are evaluated here against the candidate's own manifest. Evaluation is
evidence only; passing cases never admit or promote anything.
"""

from __future__ import annotations

from typing import Any

from .common import REQUIRED_EVAL_KINDS


def _out(result: str, action: str, blocked: bool, *finding_codes: str) -> dict[str, Any]:
    return {
        "result": result,
        "action": action,
        "blocked": blocked,
        "finding_codes": list(finding_codes),
    }


def evaluate_distilled_case(case: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    scenario = case.get("scenario")
    data = case.get("input") or {}
    declared = list(manifest.get("method", {}).get("moves", []))
    completed = list(data.get("moves_completed") or [])

    if scenario == "replay_successful_moves":
        evidence = data.get("evidence_refs") or []
        if completed == declared and not data.get("stop_conditions_hit") and len(evidence) >= len(declared):
            return _out("pass", "replay_distilled_moves", False, "MOVES_REPLAYED", "CEILING_RESPECTED")
    elif scenario == "partial_replay":
        if completed and set(completed) < set(declared):
            return _out("abstain", "request_missing_moves", True, "MOVES_INCOMPLETE")
    elif scenario == "undeclared_move_replay":
        if set(completed) - set(declared):
            return _out("stop", "deny_undeclared_move", True, "UNDECLARED_MOVE", "GRANT_ACTION_MISSING")
    elif scenario == "stop_condition_hit":
        if data.get("stop_conditions_hit"):
            return _out("stop", "halt_on_stop_condition", True, "STOP_CONDITION_HIT")
    elif scenario == "promote_without_receipt":
        if not data.get("promotion_receipt_ref"):
            return _out(
                "stop",
                "deny_self_promotion",
                True,
                "PROMOTION_RECEIPT_REQUIRED",
                "CAPABILITY_NOT_AUTHORITY",
            )
    return _out("abstain", "request_missing_evidence", True, "INSUFFICIENT_EVIDENCE")


def run_eval_suite(
    cases: list[dict[str, Any]],
    manifest: dict[str, Any],
    *,
    case_schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from .common import schema_errors

    failures: list[str] = []
    kinds: set[str] = set()
    passed = 0
    for index, case in enumerate(cases, start=1):
        label = case.get("id", f"case {index}")
        if case_schema is not None:
            for message in schema_errors(case_schema, case):
                failures.append(f"{label}: schema {message}")
        expected_id = f"QSK-{index:03d}"
        if case.get("id") != expected_id:
            failures.append(f"{label}: expected id {expected_id}")
        if case.get("skill_id") != manifest.get("id"):
            failures.append(f"{label}: skill id does not match candidate")
        if case.get("skill_version") != manifest.get("version"):
            failures.append(f"{label}: skill version does not match candidate")
        kinds.add(case.get("kind"))
        actual = evaluate_distilled_case(case, manifest)
        expected = case.get("expected", {})
        mismatched = [key for key in ("result", "action", "blocked") if actual.get(key) != expected.get(key)]
        actual_codes = set(actual["finding_codes"])
        missing = sorted(set(expected.get("required_codes", [])) - actual_codes)
        forbidden = sorted(set(expected.get("prohibited_codes", [])) & actual_codes)
        if mismatched or missing or forbidden:
            failures.append(f"{label}: mismatched={mismatched} missing={missing} forbidden={forbidden}")
        else:
            passed += 1
        if case.get("kind") == "authority" and (actual["result"] not in {"stop", "abstain"} or not actual["blocked"]):
            failures.append(f"{label}: authority case did not fail closed")
    missing_kinds = sorted(REQUIRED_EVAL_KINDS - kinds)
    return {
        "total": len(cases),
        "passed": passed,
        "kinds": sorted(kind for kind in kinds if kind),
        "missing_kinds": missing_kinds,
        "failures": failures,
        "complete": not failures and not missing_kinds and bool(cases),
    }
