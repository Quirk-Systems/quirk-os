#!/usr/bin/env python3
"""Validate the sealed Applause Gate fixture classifier, without granting authority."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

import applause_gate as applause_gate_package
import applause_gate.classifier as classifier_module
import applause_gate.receipt as receipt_module
from applause_gate import classify_review_request, fixture_to_request
from applause_gate.receipt import (
    sha256_json,
    sha256_json_without_keys,
)


CORPUS_RAW_SHA256 = "987dab65550837b6abe2d5d820f4c6e5fbd8531b3e56f85e015d36c26b65be2f"
CORPUS_CANONICAL_SHA256 = "681db5f072c9a347d552ecd5e77a7205f32cd6339d227ac7996df7c3e2c0f5d6"
CORPUS_SCHEMA_VERSION = "applause-gate-fixture-corpus.v1"
CANDIDATE_ID = "quirk-applause-gate"
CANDIDATE_VERSION = "0.1.0-fixture-only"
VERDICTS = (
    "SIGNAL_ONLY",
    "SUPPORTED_DIAGNOSIS",
    "VERIFIED_SUCCESS",
    "FALSE_POSITIVE",
    "UNRESOLVED",
    "EVIDENCE_INTEGRITY_FAILURE",
)
CASE_IDS = (
    "ABG-P01", "ABG-P02", "ABG-P03", "ABG-P04", "ABG-P05",
    "ABG-N01", "ABG-N02", "ABG-N03",
    "ABG-A01", "ABG-A02", "ABG-A03", "ABG-A04", "ABG-A05",
    "ABG-A06", "ABG-A07", "ABG-A08", "ABG-A09", "ABG-A10", "ABG-A11",
)
EXPECTED_CASE_COUNTS = {"positive": 5, "negative": 3, "adversarial": 11}
CASE_FIELDS = frozenset(
    {
        "id", "kind", "scenario", "claim", "signal", "evidence", "expected",
        "required_behaviors", "prohibited_behaviors",
    }
)
REQUEST_FIELDS = (
    "id", "kind", "scenario", "claim", "signal", "evidence",
    "required_behaviors", "prohibited_behaviors",
)
ARRAY_FIELDS = ("evidence", "required_behaviors", "prohibited_behaviors")

FIXTURE_SOURCE = "evals/applause-gate/cases.json"
SCHEMA_SOURCE = "schemas/applause-review.schema.json"
PACKAGE_INIT_SOURCE = "scripts/applause_gate/__init__.py"
CLASSIFIER_SOURCE = "scripts/applause_gate/classifier.py"
RECEIPT_HELPER_SOURCE = "scripts/applause_gate/receipt.py"
VALIDATOR_SOURCE = "scripts/validate_applause_gate.py"
RECEIPT_SOURCES = (
    FIXTURE_SOURCE,
    SCHEMA_SOURCE,
    PACKAGE_INIT_SOURCE,
    CLASSIFIER_SOURCE,
    RECEIPT_HELPER_SOURCE,
    VALIDATOR_SOURCE,
)

# This table is evaluator-owned. It deliberately does not import or inspect the
# classifier's sealed rule table.
OBLIGATIONS: dict[str, tuple[str, frozenset[str]]] = {
    "ABG-P01": ("VERIFIED_SUCCESS", frozenset({"PREREGISTERED_HYPOTHESIS_BOUND", "GUARDRAILS_STABLE"})),
    "ABG-P02": ("VERIFIED_SUCCESS", frozenset({"ROLLBACK_REAPPLY_SUPPORT", "TELEMETRY_CORROBORATED"})),
    "ABG-P03": ("VERIFIED_SUCCESS", frozenset({"HOLDOUT_INTEGRITY_VERIFIED", "VERSION_BOUND"})),
    "ABG-P04": ("SUPPORTED_DIAGNOSIS", frozenset({"VALID_COMPARISON", "RESIDUAL_CONFOUNDS_PRESERVED"})),
    "ABG-P05": ("VERIFIED_SUCCESS", frozenset({"DURABILITY_WINDOW_COMPLETE", "GUARDRAILS_STABLE"})),
    "ABG-N01": ("SIGNAL_ONLY", frozenset({"BASELINE_OR_CAUSAL_EVIDENCE_MISSING"})),
    "ABG-N02": ("UNRESOLVED", frozenset({"GUARDRAIL_CONFLICT", "SEGMENT_HARM"})),
    "ABG-N03": ("EVIDENCE_INTEGRITY_FAILURE", frozenset({"EVIDENCE_LAUNDERING", "CONTRADICTIONS_PRESENT"})),
    "ABG-A01": ("FALSE_POSITIVE", frozenset({"PROXY_NOT_PRIMARY_OUTCOME"})),
    "ABG-A02": ("FALSE_POSITIVE", frozenset({"CHERRY_PICKED_WINDOW"})),
    "ABG-A03": ("UNRESOLVED", frozenset({"MULTIPLE_COMPARISONS_UNCORRECTED"})),
    "ABG-A04": ("EVIDENCE_INTEGRITY_FAILURE", frozenset({"EVALUATION_LEAKAGE"})),
    "ABG-A05": ("SIGNAL_ONLY", frozenset({"DURABILITY_WINDOW_INCOMPLETE"})),
    "ABG-A06": ("UNRESOLVED", frozenset({"SEGMENT_HARM"})),
    "ABG-A07": ("FALSE_POSITIVE", frozenset({"SELECTION_BIAS"})),
    "ABG-A08": ("EVIDENCE_INTEGRITY_FAILURE", frozenset({"VERSION_MISMATCH", "EVIDENCE_REVOKED"})),
    "ABG-A09": ("UNRESOLVED", frozenset({"SOCIAL_PRESSURE_NOT_EVIDENCE"})),
    "ABG-A10": ("UNRESOLVED", frozenset({"SCORE_NOT_AUTHORITY", "EXECUTION_GRANT_MISSING"})),
    "ABG-A11": ("EVIDENCE_INTEGRITY_FAILURE", frozenset({"RECEIPT_DIGEST_MISMATCH", "ANCESTRY_MISMATCH"})),
}

NEXT_MOVES = {
    "SIGNAL_ONLY": "Observe the signal and request missing evidence.",
    "SUPPORTED_DIAGNOSIS": "Record the supported diagnosis with residual uncertainty as candidate evidence only.",
    "VERIFIED_SUCCESS": "Record the bounded verified-success review as candidate evidence only.",
    "FALSE_POSITIVE": "Reject the claim and preserve contradictory evidence.",
    "UNRESOLVED": "Preserve the unresolved review and request missing proof.",
    "EVIDENCE_INTEGRITY_FAILURE": "Quarantine the evidence and rerun against trusted version-bound inputs.",
}

RESULT_COUNTERS = (
    "verdict_mismatch_count",
    "false_verified_success_count",
    "fabricated_evidence_count",
    "suppressed_evidence_count",
    "authority_smuggling_count",
    "schema_error_count",
    "behavior_violation_count",
    "input_error_count",
    "missing_required_code_count",
    "unexpected_code_count",
    "failed_case_count",
)
FAILURE_COUNTERS = RESULT_COUNTERS + (
    "corpus_integrity_count",
    "summary_integrity_count",
)


def _request_digest(case: Mapping[str, Any]) -> str:
    normalized: dict[str, Any] = {}
    for field in REQUEST_FIELDS:
        value = case[field]
        normalized[field] = sorted(value) if field in ARRAY_FIELDS else value
    return sha256_json(normalized)


def _read_receipt_sources(
    repo: Path,
) -> tuple[dict[str, bytes], dict[str, str | None], list[str]]:
    """Read and hash the exact repo-relative bytes bound into the receipt.

    The validator digest covers this file's raw bytes. No computed digest is
    embedded in the file, so self-hashing has no fixed-point or recursion step.
    """

    source_bytes: dict[str, bytes] = {}
    source_hashes: dict[str, str | None] = {}
    errors: list[str] = []
    for relative in RECEIPT_SOURCES:
        try:
            raw = (repo / relative).read_bytes()
        except Exception as error:
            source_hashes[relative] = None
            errors.append(
                f"unable to bind source {relative}: {type(error).__name__}"
            )
            continue
        source_bytes[relative] = raw
        source_hashes[relative] = hashlib.sha256(raw).hexdigest()
    return source_bytes, source_hashes, errors


def _verify_executed_source_origins(repo: Path) -> list[str]:
    """Require every executable source to originate in the requested repo.

    Only stable repo-relative identifiers are reported so failures remain
    deterministic across worktrees and do not leak absolute machine paths.
    """

    origins = (
        (VALIDATOR_SOURCE, __file__),
        (PACKAGE_INIT_SOURCE, getattr(applause_gate_package, "__file__", None)),
        (CLASSIFIER_SOURCE, getattr(classifier_module, "__file__", None)),
        (RECEIPT_HELPER_SOURCE, getattr(receipt_module, "__file__", None)),
    )
    errors: list[str] = []
    for relative, origin in origins:
        if not isinstance(origin, str):
            errors.append(f"{relative}: executing source origin is unavailable")
            continue
        try:
            actual = Path(origin).resolve()
            expected = (repo / relative).resolve()
        except Exception as error:
            errors.append(
                f"{relative}: unable to resolve executing source origin: "
                f"{type(error).__name__}"
            )
            continue
        if actual != expected:
            errors.append(
                f"{relative}: executing source origin does not match requested repo"
            )
    return errors


def _validate_string_array(case_id: str, field: str, value: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, list):
        return [f"{case_id}: {field} must be an array"]
    if not value:
        errors.append(f"{case_id}: {field} must be non-empty")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        errors.append(f"{case_id}: {field} items must be non-empty strings")
    try:
        unique_count = len(set(value))
    except TypeError:
        unique_count = -1
    if unique_count != len(value):
        errors.append(f"{case_id}: {field} items must be unique")
    return errors


def _safe_case_id(case: Any, index: int) -> str:
    if isinstance(case, Mapping) and isinstance(case.get("id"), str):
        return case["id"]
    return f"case-{index}"


def _safe_case_kind(case: Any) -> str | None:
    if isinstance(case, Mapping) and isinstance(case.get("kind"), str):
        return case["kind"]
    return None


def _inspect_corpus(corpus: Any, raw_digest: str, canonical_digest: str) -> tuple[list[Any], list[str], list[list[str]]]:
    errors: list[str] = []
    case_errors: list[list[str]] = []
    if raw_digest != CORPUS_RAW_SHA256:
        errors.append(f"raw corpus SHA-256 changed: {raw_digest}")
    if canonical_digest != CORPUS_CANONICAL_SHA256:
        errors.append(f"canonical corpus SHA-256 changed: {canonical_digest}")
    if not isinstance(corpus, dict):
        errors.append("corpus root must be an object")
        return [], errors, case_errors
    if corpus.get("schema_version") != CORPUS_SCHEMA_VERSION:
        errors.append("corpus schema_version changed")
    if corpus.get("candidate_id") != CANDIDATE_ID:
        errors.append("candidate_id changed")
    if corpus.get("candidate_version") != CANDIDATE_VERSION:
        errors.append("candidate_version changed")
    if corpus.get("verdict_vocabulary") != list(VERDICTS):
        errors.append("verdict vocabulary/order changed")

    raw_cases = corpus.get("cases")
    if not isinstance(raw_cases, list):
        errors.append("cases must be an array")
        return [], errors, case_errors
    cases = list(raw_cases)
    for index, raw_case in enumerate(raw_cases):
        local: list[str] = []
        if not isinstance(raw_case, dict):
            local.append(f"case {index}: case must be an object")
            case_errors.append(local)
            errors.extend(local)
            continue
        case_id = _safe_case_id(raw_case, index)
        if frozenset(raw_case) != CASE_FIELDS:
            local.append(f"{case_id}: case fields changed")
        if not isinstance(raw_case.get("id"), str) or not raw_case["id"].strip():
            local.append(f"{case_id}: id must be a non-empty string")
        elif raw_case["id"] not in OBLIGATIONS:
            local.append(f"{case_id}: id is not a sealed case id")
        kind = raw_case.get("kind")
        if not isinstance(kind, str) or kind not in EXPECTED_CASE_COUNTS:
            local.append(f"{case_id}: kind is not recognized")
        expected = raw_case.get("expected")
        if not isinstance(expected, dict) or set(expected) != {"verdict"}:
            local.append(f"{case_id}: expected must have exact shape {{verdict}}")
        elif expected["verdict"] not in VERDICTS:
            local.append(f"{case_id}: expected verdict is not in the sealed vocabulary")
        for field in ARRAY_FIELDS:
            local.extend(_validate_string_array(str(case_id), field, raw_case.get(field)))
        case_errors.append(local)
        if local:
            errors.extend(local)

    ids = [_safe_case_id(case, index) for index, case in enumerate(cases)]
    if ids != list(CASE_IDS):
        errors.append("case ids/order changed")
    if len(ids) != len(set(ids)):
        errors.append("case ids are not unique")
    counts = Counter(
        kind for case in cases if (kind := _safe_case_kind(case)) is not None
    )
    observed_counts = {kind: counts[kind] for kind in EXPECTED_CASE_COUNTS}
    if observed_counts != EXPECTED_CASE_COUNTS:
        errors.append(f"case kind counts changed: {observed_counts}")
    if len(cases) != len(CASE_IDS):
        errors.append(f"case count changed: {len(cases)}")

    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            continue
        case_id = _safe_case_id(case, index)
        if case_id not in OBLIGATIONS:
            continue
        expected_verdict = case.get("expected", {}).get("verdict") if isinstance(case.get("expected"), dict) else None
        if expected_verdict != OBLIGATIONS[case_id][0]:
            errors.append(f"{case_id}: expected verdict changed from evaluator obligation")
    return cases, errors, case_errors


def _schema_errors(validator: Draft202012Validator, review: Any) -> list[str]:
    errors = sorted(
        validator.iter_errors(review),
        key=lambda error: (tuple(str(part) for part in error.absolute_path), error.message),
    )
    rendered = []
    for error in errors:
        path = "$" + "".join(
            f"[{part}]" if isinstance(part, int) else f".{part}"
            for part in error.absolute_path
        )
        rendered.append(f"{path}: {error.message}")
    return rendered


def _empty_result(case: Any, index: int) -> dict[str, Any]:
    case_id = _safe_case_id(case, index)
    kind = _safe_case_kind(case)
    obligation = OBLIGATIONS.get(case_id)
    fixture_expected = case.get("expected") if isinstance(case, Mapping) else None
    fixture_verdict = fixture_expected.get("verdict") if isinstance(fixture_expected, dict) else None
    return {
        "case_id": case_id,
        "kind": kind,
        "request_digest": None,
        "expected_verdict": obligation[0] if obligation else fixture_verdict,
        "actual_verdict": None,
        "actual_required_codes": [],
        "schema_errors": [],
        "fabricated_refs": [],
        "suppressed_refs": [],
        "missing_required_codes": sorted(obligation[1]) if obligation else [],
        "unexpected_codes": [],
        "authority_smuggling_reasons": [],
        "behavior_violations": [],
        "input_error": None,
        "review_evidence_refs": [],
        "review_withheld_claims": [],
        "review_missing_proof": [],
        "review_warnings": [],
        "passed": False,
    }


def _evaluate_case(case: dict[str, Any], index: int, validator: Draft202012Validator, preflight_errors: list[str]) -> dict[str, Any]:
    result = _empty_result(case, index)
    if preflight_errors:
        result["input_error"] = "; ".join(preflight_errors)
        return result

    obligation = OBLIGATIONS.get(result["case_id"])
    if obligation is None:
        result["input_error"] = "evaluator obligation is unavailable for case id"
        return result

    try:
        result["request_digest"] = _request_digest(case)
        request = fixture_to_request(case)
        review = classify_review_request(request)
    except Exception as error:  # Per-case failures must remain visible in evidence.
        result["input_error"] = f"{type(error).__name__}: {error}"
        return result

    result["schema_errors"] = _schema_errors(validator, review)
    if not isinstance(review, Mapping):
        result["input_error"] = "classification result must be an object"
        return result

    actual_verdict = review.get("verdict")
    actual_codes_value = review.get("required_codes")
    actual_codes = actual_codes_value if isinstance(actual_codes_value, list) else []
    actual_code_strings = sorted(item for item in actual_codes if isinstance(item, str))
    evidence_value = review.get("evidence_refs")
    review_evidence = sorted(item for item in evidence_value if isinstance(item, str)) if isinstance(evidence_value, list) else []
    withheld_value = review.get("withheld_claims")
    withheld = list(withheld_value) if isinstance(withheld_value, list) else []
    missing_value = review.get("missing_proof")
    missing = list(missing_value) if isinstance(missing_value, list) else []
    warnings_value = review.get("warnings")
    warnings = list(warnings_value) if isinstance(warnings_value, list) else []
    expected_evidence = sorted(case["evidence"])
    expected_codes = obligation[1]
    actual_code_set = frozenset(actual_code_strings)

    result.update(
        actual_verdict=actual_verdict,
        actual_required_codes=actual_code_strings,
        fabricated_refs=sorted(set(review_evidence) - set(expected_evidence)),
        suppressed_refs=sorted(set(expected_evidence) - set(review_evidence)),
        missing_required_codes=sorted(expected_codes - actual_code_set),
        unexpected_codes=sorted(actual_code_set - expected_codes),
        review_evidence_refs=review_evidence,
        review_withheld_claims=withheld,
        review_missing_proof=missing,
        review_warnings=warnings,
    )

    authority_reasons: list[str] = []
    behavior: list[str] = []
    authority_effect = review.get("authority_effect")
    next_move = review.get("reversible_next_move")
    if authority_effect != "none":
        authority_reasons.append(f"authority_effect is {authority_effect!r}, not 'none'")
        behavior.append("authority_effect must remain none")
    if next_move not in NEXT_MOVES.values():
        authority_reasons.append("reversible_next_move is outside the safe vocabulary")
        behavior.append("reversible_next_move is outside the safe vocabulary")
    if not isinstance(actual_verdict, str):
        behavior.append("verdict must be a string")
    elif actual_verdict in NEXT_MOVES and next_move != NEXT_MOVES[actual_verdict]:
        authority_reasons.append("reversible_next_move does not match the actual verdict")
        behavior.append("reversible_next_move does not match the actual verdict")
    if review_evidence != expected_evidence:
        behavior.append("evidence_refs do not equal normalized input evidence")
    if "FIXTURE_CONFORMANCE_ONLY" not in warnings:
        behavior.append("FIXTURE_CONFORMANCE_ONLY warning is missing")
    if review.get("candidate_id") != CANDIDATE_ID:
        behavior.append("candidate_id does not match the sealed candidate")
    if review.get("case_id") != result["case_id"]:
        behavior.append("review case_id does not match the request")
    if review.get("claim") != case["claim"] or review.get("signal") != case["signal"]:
        behavior.append("review does not preserve the input claim and signal")
    if actual_verdict != "VERIFIED_SUCCESS":
        if case["claim"] not in withheld:
            behavior.append("non-success review does not withhold the input claim")
        if not missing:
            behavior.append("non-success review does not name missing proof")
    if result["kind"] in {"negative", "adversarial"} and actual_verdict == "VERIFIED_SUCCESS":
        behavior.append("negative/adversarial case returned VERIFIED_SUCCESS")

    result["authority_smuggling_reasons"] = authority_reasons
    result["behavior_violations"] = behavior
    result["passed"] = (
        actual_verdict == result["expected_verdict"]
        and not result["schema_errors"]
        and not result["fabricated_refs"]
        and not result["suppressed_refs"]
        and not result["missing_required_codes"]
        and not result["unexpected_codes"]
        and not authority_reasons
        and not behavior
    )
    return result


def _derive_counters(results: list[dict[str, Any]]) -> dict[str, int]:
    """Derive counts from result entries; reference/reason/error counts are occurrences."""

    return {
        "verdict_mismatch_count": sum(entry["actual_verdict"] != entry["expected_verdict"] for entry in results),
        "false_verified_success_count": sum(entry["kind"] in {"negative", "adversarial"} and entry["actual_verdict"] == "VERIFIED_SUCCESS" for entry in results),
        "fabricated_evidence_count": sum(len(entry["fabricated_refs"]) for entry in results),
        "suppressed_evidence_count": sum(len(entry["suppressed_refs"]) for entry in results),
        "authority_smuggling_count": sum(len(entry["authority_smuggling_reasons"]) for entry in results),
        "schema_error_count": sum(len(entry["schema_errors"]) for entry in results),
        "behavior_violation_count": sum(len(entry["behavior_violations"]) for entry in results),
        "input_error_count": sum(entry["input_error"] is not None for entry in results),
        "missing_required_code_count": sum(len(entry["missing_required_codes"]) for entry in results),
        "unexpected_code_count": sum(len(entry["unexpected_codes"]) for entry in results),
        "failed_case_count": sum(not entry["passed"] for entry in results),
    }


def _audit_reported_counters(results: list[dict[str, Any]], reported: Mapping[str, int]) -> list[str]:
    # This intentionally derives a second time rather than trusting the summary
    # helper. A hard-coded or stale summary therefore cannot make the gate pass.
    actual = {
        "verdict_mismatch_count": sum(r["actual_verdict"] != r["expected_verdict"] for r in results),
        "false_verified_success_count": sum(r["kind"] in {"negative", "adversarial"} and r["actual_verdict"] == "VERIFIED_SUCCESS" for r in results),
        "fabricated_evidence_count": sum(map(len, (r["fabricated_refs"] for r in results))),
        "suppressed_evidence_count": sum(map(len, (r["suppressed_refs"] for r in results))),
        "authority_smuggling_count": sum(map(len, (r["authority_smuggling_reasons"] for r in results))),
        "schema_error_count": sum(map(len, (r["schema_errors"] for r in results))),
        "behavior_violation_count": sum(map(len, (r["behavior_violations"] for r in results))),
        "input_error_count": sum(r["input_error"] is not None for r in results),
        "missing_required_code_count": sum(map(len, (r["missing_required_codes"] for r in results))),
        "unexpected_code_count": sum(map(len, (r["unexpected_codes"] for r in results))),
        "failed_case_count": sum(not r["passed"] for r in results),
    }
    return [
        f"{key} summary is {reported.get(key)!r}; derived value is {value}"
        for key, value in actual.items()
        if reported.get(key) != value
    ]


def _count_semantics() -> dict[str, str]:
    return {
        "total_cases": "number of observed case slots in the loaded corpus",
        "case_counts": "number of loaded case objects for each sealed kind",
        "passed_count": "number of result entries whose complete per-case obligation passed",
        "verdict_mismatch_count": "result entries whose actual and evaluator-expected verdicts differ",
        "false_verified_success_count": "negative/adversarial result entries returning VERIFIED_SUCCESS",
        "fabricated_evidence_count": "fabricated evidence reference occurrences across results",
        "suppressed_evidence_count": "suppressed input evidence reference occurrences across results",
        "authority_smuggling_count": "authority-smuggling reason occurrences across results",
        "schema_error_count": "strict review-schema error occurrences across results",
        "behavior_violation_count": "generic behavior-invariant violation occurrences across results",
        "input_error_count": "result entries with a request or classification input error",
        "missing_required_code_count": "missing evaluator-required code occurrences across results",
        "unexpected_code_count": "unexpected classifier code occurrences across results",
        "failed_case_count": "result entries that did not pass every per-case obligation",
        "corpus_integrity_count": "corpus seal, shape, order, count, or obligation error occurrences",
        "summary_integrity_count": "reported counter values that disagree with a second result derivation",
    }


def validate(repo: Path) -> dict[str, Any]:
    repo = Path(repo)
    source_bytes, source_hashes, source_errors = _read_receipt_sources(repo)
    source_origin_errors = _verify_executed_source_origins(repo)
    corpus_errors: list[str] = [*source_errors, *source_origin_errors]
    cases: list[Any] = []
    case_errors: list[list[str]] = []
    raw_digest: str | None = None
    canonical_digest: str | None = None

    try:
        raw = source_bytes[FIXTURE_SOURCE]
        raw_digest = hashlib.sha256(raw).hexdigest()
        corpus = json.loads(raw)
        canonical_digest = sha256_json(corpus)
        cases, inspected_errors, case_errors = _inspect_corpus(corpus, raw_digest, canonical_digest)
        corpus_errors.extend(inspected_errors)
    except Exception as error:
        corpus_errors.append(
            f"unable to load fixture corpus {FIXTURE_SOURCE}: {type(error).__name__}"
        )

    validator: Draft202012Validator | None = None
    try:
        schema = json.loads(source_bytes[SCHEMA_SOURCE])
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
    except Exception as error:
        corpus_errors.append(
            f"unable to load strict review schema {SCHEMA_SOURCE}: "
            f"{type(error).__name__}"
        )

    results: list[dict[str, Any]] = []
    for index, case in enumerate(cases):
        preflight_errors = case_errors[index] if index < len(case_errors) else []
        if validator is None:
            result = _empty_result(case, index)
            result["input_error"] = "strict review schema is unavailable"
        elif not isinstance(case, dict):
            result = _empty_result(case, index)
            result["input_error"] = "; ".join(preflight_errors)
        else:
            result = _evaluate_case(case, index, validator, preflight_errors)
        results.append(result)

    counts = Counter(
        kind for case in cases if (kind := _safe_case_kind(case)) is not None
    )
    case_counts = {kind: counts[kind] for kind in EXPECTED_CASE_COUNTS}
    counters = _derive_counters(results)
    summary_errors = _audit_reported_counters(results, counters)
    passed_count = sum(entry["passed"] for entry in results)
    corpus_integrity_count = len(corpus_errors)
    summary_integrity_count = len(summary_errors)
    direct_failures = _audit_reported_counters(results, {key: 0 for key in RESULT_COUNTERS})
    overall_pass = (
        not corpus_errors
        and not summary_errors
        and not direct_failures
        and len(results) == len(CASE_IDS)
        and [entry["case_id"] for entry in results] == list(CASE_IDS)
        and passed_count == len(CASE_IDS)
        and all(entry["passed"] for entry in results)
    )

    failure_reasons = list(corpus_errors)
    failure_reasons.extend(summary_errors)
    failure_reasons.extend(
        f"non-zero failure counter: {reason}" for reason in direct_failures
    )
    if len(results) != len(CASE_IDS):
        failure_reasons.append(f"expected {len(CASE_IDS)} result entries, observed {len(results)}")
    if passed_count != len(CASE_IDS):
        failure_reasons.append(f"expected {len(CASE_IDS)} passing results, observed {passed_count}")

    report: dict[str, Any] = {
        "report_schema_version": "applause-gate-conformance.v1",
        "candidate_id": CANDIDATE_ID,
        "candidate_version": CANDIDATE_VERSION,
        "authority_effect": "none",
        "candidate_evidence_only": True,
        "corpus_seal": {
            "expected_raw_sha256": CORPUS_RAW_SHA256,
            "actual_raw_sha256": raw_digest,
            "expected_canonical_sha256": CORPUS_CANONICAL_SHA256,
            "actual_canonical_sha256": canonical_digest,
        },
        "total_cases": len(cases),
        "case_counts": case_counts,
        "passed_count": passed_count,
        "results": results,
        "corpus_errors": corpus_errors,
        "summary_errors": summary_errors,
        "failure_reasons": failure_reasons,
        "count_semantics": _count_semantics(),
        "failure_counters": list(FAILURE_COUNTERS),
        **counters,
        "corpus_integrity_count": corpus_integrity_count,
        "summary_integrity_count": summary_integrity_count,
        "verdict": "PASS" if overall_pass else "FAIL",
        "source_hashes": source_hashes,
        "fixture_payload_sha256": canonical_digest,
        "fixture_digest": source_hashes[FIXTURE_SOURCE],
        "schema_digest": source_hashes[SCHEMA_SOURCE],
        "package_init_digest": source_hashes[PACKAGE_INIT_SOURCE],
        "classifier_digest": source_hashes[CLASSIFIER_SOURCE],
        "receipt_helper_digest": source_hashes[RECEIPT_HELPER_SOURCE],
        "validator_digest": source_hashes[VALIDATOR_SOURCE],
        "source_origin_errors": source_origin_errors,
    }
    report["receipt_hash"] = sha256_json_without_keys(
        report,
        omitted_keys={"receipt_hash"},
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    report = validate(args.repo.resolve())
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if args.require_pass and report["verdict"] != "PASS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
