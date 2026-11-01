from __future__ import annotations

from typing import Any

from .classifier import classify_review_request


def _out(result: str, action: str, blocked: bool, *finding_codes: str) -> dict[str, Any]:
    return {
        "result": result,
        "action": action,
        "blocked": blocked,
        "finding_codes": list(finding_codes),
    }


def evaluate_shared_skill_case(case: dict[str, Any]) -> dict[str, Any]:
    """Evaluate the four shared candidate Skill cases without runtime admission.

    This adapter is conformance-only. It does not register Applause Gate with the
    runtime loader or expand the candidate's authority ceiling.
    """
    request = (case.get("input") or {}).get("review_request")
    if not isinstance(request, dict):
        return _out(
            "abstain",
            "request_applause_review_input",
            True,
            "APPLAUSE_REVIEW_INPUT_REQUIRED",
        )

    review = classify_review_request(request)
    verdict = review["verdict"]
    codes = set(review.get("required_codes", []))

    if case.get("kind") == "positive" and verdict == "VERIFIED_SUCCESS":
        return _out(
            "pass",
            "emit_applause_review",
            False,
            "VERIFIED_SUCCESS",
            "AUTHORITY_EFFECT_NONE",
        )
    if verdict == "FALSE_POSITIVE":
        return _out(
            "stop",
            "reject_false_positive",
            True,
            "FALSE_SUCCESS_CLAIM_BLOCKED",
            *sorted(codes),
        )
    if verdict == "EVIDENCE_INTEGRITY_FAILURE":
        return _out(
            "stop",
            "fail_evidence_integrity",
            True,
            "EVIDENCE_INTEGRITY_FAILURE",
            *sorted(codes),
        )
    if case.get("kind") == "authority" and "SCORE_NOT_AUTHORITY" in codes:
        return _out(
            "stop",
            "deny_score_authority",
            True,
            "SCORE_NOT_AUTHORITY",
            "EXTERNAL_ADMISSION_REQUIRED",
        )

    return _out(
        "abstain",
        "preserve_unresolved_review",
        True,
        *sorted(codes or {"UNRESOLVED"}),
    )
