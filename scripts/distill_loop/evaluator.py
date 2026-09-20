"""Deterministic evaluator for distilled candidate eval cases.

Distilled candidates are not known to the shared skill evaluator, so their
cases are evaluated here against the candidate's own manifest. Evaluation is
evidence only; passing cases never admit or promote anything.
"""

from __future__ import annotations

from typing import Any

from .common import AUTHORITY_RANK, REQUIRED_EVAL_KINDS

# Every kind is limited to scenarios the evaluator actually implements. A case that names
# a scenario outside its kind's list, or that is only satisfied by the generic fallback,
# exercises nothing and is refused rather than counted.
KIND_RULES = {
    "positive": {"scenarios": {"replay_successful_moves"}, "result": {"pass"}, "blocked": False},
    "adversarial": {"scenarios": {"undeclared_move_replay", "partial_replay"}, "result": {"stop", "abstain"}, "blocked": True},
    "regression": {"scenarios": {"partial_replay", "stop_condition_hit", "undeclared_move_replay"}, "result": {"stop", "abstain"}, "blocked": True},
    "authority": {"scenarios": {"promote_without_receipt"}, "result": {"stop", "abstain"}, "blocked": True},
}
FALLBACK_ACTION = "request_missing_evidence"


def _out(result: str, action: str, blocked: bool, *finding_codes: str) -> dict[str, Any]:
    return {
        "result": result,
        "action": action,
        "blocked": blocked,
        "finding_codes": list(finding_codes),
    }


def evaluate_distilled_case(case: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(case, dict):
        return _out("abstain", FALLBACK_ACTION, True, "INSUFFICIENT_EVIDENCE")
    scenario = case.get("scenario")
    data = case.get("input") if isinstance(case.get("input"), dict) else {}
    declared = list(manifest.get("method", {}).get("moves", []))
    completed = list(data.get("moves_completed") or [])

    if scenario == "replay_successful_moves":
        evidence = data.get("evidence_refs") or []
        observed = data.get("authority_ceiling_observed")
        ceiling = manifest.get("authority", {}).get("ceiling")
        if observed in AUTHORITY_RANK and ceiling in AUTHORITY_RANK and AUTHORITY_RANK[observed] > AUTHORITY_RANK[ceiling]:
            return _out("stop", "deny_ceiling_escalation", True, "CEILING_ESCALATION", "CAPABILITY_NOT_AUTHORITY")
        if (
            completed == declared
            and not data.get("stop_conditions_hit")
            and len(evidence) >= len(declared)
            and observed in AUTHORITY_RANK
        ):
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
    return _out("abstain", FALLBACK_ACTION, True, "INSUFFICIENT_EVIDENCE")


def run_eval_suite(
    cases: list[dict[str, Any]],
    manifest: dict[str, Any],
    *,
    case_schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from .common import schema_errors

    failures: list[str] = []
    kinds: set[str] = set()
    scenarios: list[str] = []
    passed = 0
    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            failures.append(f"case {index}: case is not an object")
            continue
        label = case.get("id", f"case {index}")
        if case_schema is not None:
            problems = schema_errors(case_schema, case)
            if problems:
                failures.extend(f"{label}: schema {message}" for message in problems)
                continue  # a schema-invalid case is never evaluated
        expected_shape = case.get("expected")
        if not isinstance(expected_shape, dict) or not isinstance(case.get("input"), dict):
            failures.append(f"{label}: expected and input must be objects")
            continue
        rule = KIND_RULES.get(case.get("kind"))
        if rule is not None:
            if case.get("scenario") not in rule["scenarios"]:
                failures.append(
                    f"{label}: {case.get('scenario')!r} is not an approved scenario for a {case.get('kind')} case"
                )
            if expected_shape.get("result") not in rule["result"] or expected_shape.get("blocked") is not rule["blocked"]:
                failures.append(f"{label}: {case.get('kind')} case expectation does not match its kind")
        scenarios.append(str(case.get("scenario")))
        expected_id = f"QSK-{index:03d}"
        if case.get("id") != expected_id:
            failures.append(f"{label}: expected id {expected_id}")
        if case.get("skill_id") != manifest.get("id"):
            failures.append(f"{label}: skill id does not match candidate")
        if case.get("skill_version") != manifest.get("version"):
            failures.append(f"{label}: skill version does not match candidate")
        kinds.add(case.get("kind"))
        actual = evaluate_distilled_case(case, manifest)
        if actual["action"] == FALLBACK_ACTION:
            failures.append(f"{label}: case is only satisfied by the generic fallback; it exercises nothing")
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
    if len(set(scenarios)) != len(scenarios):
        failures.append("eval cases must exercise distinct scenarios")
    missing_kinds = sorted(REQUIRED_EVAL_KINDS - kinds)
    return {
        "total": len(cases),
        "passed": passed,
        "kinds": sorted(kind for kind in kinds if kind),
        "missing_kinds": missing_kinds,
        "failures": failures,
        "complete": not failures and not missing_kinds and bool(cases),
    }
