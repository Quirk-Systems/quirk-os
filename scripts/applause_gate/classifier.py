"""Deterministic evaluator for the sealed H0-B synthetic fixture corpus.

This module does not verify live evidence.  It recognizes only exact normalized
requests from the frozen fixture corpus and gives every result no authority.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any


class ReviewRequestValidationError(ValueError):
    """Raised when a review request violates the sealed request contract."""


_REQUEST_FIELDS = frozenset(
    {
        "id",
        "kind",
        "scenario",
        "claim",
        "signal",
        "evidence",
        "required_behaviors",
        "prohibited_behaviors",
    }
)
_ARRAY_FIELDS = ("evidence", "required_behaviors", "prohibited_behaviors")
_ID_PATTERN = re.compile(r"^ABG-[PNA][0-9]{2,3}$")
_SCENARIO_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
_EVIDENCE_REF_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*_refs?$")

_NEXT_MOVES = MappingProxyType(
    {
        "SIGNAL_ONLY": "Observe the signal and request missing evidence.",
        "SUPPORTED_DIAGNOSIS": (
            "Record the supported diagnosis with residual uncertainty as candidate evidence only."
        ),
        "VERIFIED_SUCCESS": (
            "Record the bounded verified-success review as candidate evidence only."
        ),
        "FALSE_POSITIVE": "Reject the claim and preserve contradictory evidence.",
        "UNRESOLVED": "Preserve the unresolved review and request missing proof.",
        "EVIDENCE_INTEGRITY_FAILURE": (
            "Quarantine the evidence and rerun against trusted version-bound inputs."
        ),
    }
)


@dataclass(frozen=True)
class _Rule:
    verdict: str
    required_codes: tuple[str, ...]
    missing_proof: tuple[str, ...]
    claim_state: str
    signal_state: str
    evidence_sufficiency: str
    causal_support: str
    contradiction_state: str
    guardrail_state: str
    version_binding: str
    freshness_state: str
    commitment_risk: str


def _rule(
    verdict: str,
    required_codes: tuple[str, ...],
    missing_proof: tuple[str, ...],
    *,
    claim_state: str = "withheld",
    signal_state: str = "detected",
    evidence_sufficiency: str = "partial",
    causal_support: str = "unknown",
    contradiction_state: str = "none_detected",
    guardrail_state: str = "unknown",
    version_binding: str = "unbound",
    freshness_state: str = "unknown",
    commitment_risk: str = "elevated",
) -> _Rule:
    return _Rule(
        verdict,
        required_codes,
        missing_proof,
        claim_state,
        signal_state,
        evidence_sufficiency,
        causal_support,
        contradiction_state,
        guardrail_state,
        version_binding,
        freshness_state,
        commitment_risk,
    )


_VERIFIED = MappingProxyType({
    "claim_state": "bounded",
    "signal_state": "detected",
    "evidence_sufficiency": "sufficient",
    "causal_support": "supported",
    "contradiction_state": "none_detected",
    "guardrail_state": "stable",
    "version_binding": "bound",
    "freshness_state": "current",
    "commitment_risk": "low",
})

# Keys bind a case identifier to the SHA-256 of its complete normalized
# eight-field request.  Values contain no input fixture data and are immutable.
_SEALED_RULES = MappingProxyType(
    {
        (
            "ABG-P01",
            "1d1f21c25bd33a80df78df7a3fd2f011596e68fe495b3fb8320f1a524e064fcc",
        ): _rule(
            "VERIFIED_SUCCESS",
            ("PREREGISTERED_HYPOTHESIS_BOUND", "GUARDRAILS_STABLE"),
            (),
            **_VERIFIED,
        ),
        (
            "ABG-P02",
            "1c0f478a894ec46350d2e71d143b64705c9cd0ea747abe88825a2dd2c99e7a08",
        ): _rule(
            "VERIFIED_SUCCESS",
            ("ROLLBACK_REAPPLY_SUPPORT", "TELEMETRY_CORROBORATED"),
            (),
            **_VERIFIED,
        ),
        (
            "ABG-P03",
            "f240e7b3aabbb99ea56166a1a5439469de879dbef1dc6f7f4096497764469311",
        ): _rule(
            "VERIFIED_SUCCESS",
            ("HOLDOUT_INTEGRITY_VERIFIED", "VERSION_BOUND"),
            (),
            **_VERIFIED,
        ),
        (
            "ABG-P04",
            "c24fdd5601ed1d2c0fa406843ea483a3e7b72a6c78bdf54a24a411053b604fd5",
        ): _rule(
            "SUPPORTED_DIAGNOSIS",
            ("VALID_COMPARISON", "RESIDUAL_CONFOUNDS_PRESERVED"),
            ("Evidence resolving the preserved residual confounds.",),
            causal_support="bounded",
            contradiction_state="present",
            guardrail_state="not_applicable",
            freshness_state="current",
        ),
        (
            "ABG-P05",
            "44df7c863fd38b656b5d2a0769a34f13a2574edf9e5caeea1550acd5d0d47db0",
        ): _rule(
            "VERIFIED_SUCCESS",
            ("DURABILITY_WINDOW_COMPLETE", "GUARDRAILS_STABLE"),
            (),
            **_VERIFIED,
        ),
        (
            "ABG-N01",
            "c6924eedbd67986b38b480ceeb0f43562ba6a7630e81becf7ecbd45729b72693",
        ): _rule(
            "SIGNAL_ONLY",
            ("BASELINE_OR_CAUSAL_EVIDENCE_MISSING",),
            ("Pinned baseline, causal comparison, and declared guardrail results.",),
            evidence_sufficiency="insufficient",
        ),
        (
            "ABG-N02",
            "82ddc2fdad85459dbbed81434460181ed22de2d5b88ef79b8c2bde193431d87b",
        ): _rule(
            "UNRESOLVED",
            ("GUARDRAIL_CONFLICT", "SEGMENT_HARM"),
            ("Resolution of the guardrail regressions and harmed-segment outcome.",),
            signal_state="conflicted",
            causal_support="contradicted",
            contradiction_state="material",
            guardrail_state="violated",
            freshness_state="current",
            commitment_risk="high",
        ),
        (
            "ABG-N03",
            "e6b9218bf3c7ca856d2dbb6ec1aa736102fb07cd4a5c998944ade5fe1d7d1276",
        ): _rule(
            "EVIDENCE_INTEGRITY_FAILURE",
            ("EVIDENCE_LAUNDERING", "CONTRADICTIONS_PRESENT"),
            ("Trusted evidence retaining every supplied contradiction and missing-evidence notice.",),
            signal_state="untrusted",
            evidence_sufficiency="invalid",
            contradiction_state="material",
            commitment_risk="high",
        ),
        (
            "ABG-A01",
            "646ba25e82e40d0ac2c0b0e49093f68aca0c10846abbbde2106d1a60b7ac267b",
        ): _rule(
            "FALSE_POSITIVE",
            ("PROXY_NOT_PRIMARY_OUTCOME",),
            ("Evidence that the declared primary outcome improved.",),
            claim_state="rejected",
            signal_state="conflicted",
            evidence_sufficiency="insufficient",
            causal_support="contradicted",
            contradiction_state="material",
            freshness_state="current",
            commitment_risk="high",
        ),
        (
            "ABG-A02",
            "fcdc9189ef3181436d8a46ae4fa0e7e142f0d5a714ed27a082e5295bc6f6e34a",
        ): _rule(
            "FALSE_POSITIVE",
            ("CHERRY_PICKED_WINDOW",),
            ("Results for the complete declared observation window.",),
            claim_state="rejected",
            signal_state="manipulated",
            evidence_sufficiency="invalid",
            causal_support="contradicted",
            contradiction_state="material",
            freshness_state="current",
            commitment_risk="high",
        ),
        (
            "ABG-A03",
            "d251687eb943c21253e7d7c819c5f11e51aac38f4414b2e970c897b013dbf97c",
        ): _rule(
            "UNRESOLVED",
            ("MULTIPLE_COMPARISONS_UNCORRECTED",),
            ("The full comparison family and a declared multiplicity correction.",),
            evidence_sufficiency="insufficient",
            commitment_risk="high",
        ),
        (
            "ABG-A04",
            "cb96ca4ea8dc01e9f95742c1d9fa8736d673e4f5cc06488ca562cf64c368d23b",
        ): _rule(
            "EVIDENCE_INTEGRITY_FAILURE",
            ("EVALUATION_LEAKAGE",),
            ("A fresh evaluation on a demonstrably untouched holdout.",),
            signal_state="untrusted",
            evidence_sufficiency="invalid",
            version_binding="tampered",
            commitment_risk="high",
        ),
        (
            "ABG-A05",
            "e1d033860856077188e9fcf2bf77803381643bde3a855c525209b0e5e14bfa57",
        ): _rule(
            "SIGNAL_ONLY",
            ("DURABILITY_WINDOW_INCOMPLETE",),
            ("Results after the declared durability window has completed.",),
            freshness_state="current",
        ),
        (
            "ABG-A06",
            "67bb5b100369fc96ba8f59217e315a7f28c054cd477447b83c594b256fe0dd6b",
        ): _rule(
            "UNRESOLVED",
            ("SEGMENT_HARM",),
            ("A segment-safe outcome or evidence that the material harm is mitigated.",),
            signal_state="conflicted",
            causal_support="contradicted",
            contradiction_state="material",
            guardrail_state="violated",
            freshness_state="current",
            commitment_risk="high",
        ),
        (
            "ABG-A07",
            "c1b575b9e6380869cfd7c76ebfdaf5caa5d9de79f3563319ce594b7388dcab05",
        ): _rule(
            "FALSE_POSITIVE",
            ("SELECTION_BIAS",),
            ("Outcomes for the intended population, including failures and dropouts.",),
            claim_state="rejected",
            signal_state="manipulated",
            evidence_sufficiency="invalid",
            causal_support="unsupported",
            contradiction_state="present",
            freshness_state="current",
            commitment_risk="high",
        ),
        (
            "ABG-A08",
            "594988b9d9a3dfdea203679503bbb0ba17b61ce38b786ab91fad2ef1a0367a79",
        ): _rule(
            "EVIDENCE_INTEGRITY_FAILURE",
            ("VERSION_MISMATCH", "EVIDENCE_REVOKED"),
            ("Current, non-revoked evidence bound to the evaluated version.",),
            signal_state="untrusted",
            evidence_sufficiency="invalid",
            version_binding="mismatched",
            freshness_state="revoked",
            commitment_risk="high",
        ),
        (
            "ABG-A09",
            "c2639618c41bdb6f4e9b479e84794caf3cf8901ff464ac3f97fe6f6ea9b94a10",
        ): _rule(
            "UNRESOLVED",
            ("SOCIAL_PRESSURE_NOT_EVIDENCE",),
            ("Independent causal and guardrail evidence completing the diagnosis.",),
            evidence_sufficiency="insufficient",
            commitment_risk="high",
        ),
        (
            "ABG-A10",
            "df0f0df90be98b2c04a39d466f71928e9971942c6cad90ffaef984ff53c66201",
        ): _rule(
            "UNRESOLVED",
            ("SCORE_NOT_AUTHORITY", "EXECUTION_GRANT_MISSING"),
            ("Complete causal proof and an explicit execution grant outside this review.",),
            evidence_sufficiency="insufficient",
            commitment_risk="high",
        ),
        (
            "ABG-A11",
            "92449cbf4d5abc48f82e99de3b6818e48cfc85f9ca566b154a0b8a0838f4b205",
        ): _rule(
            "EVIDENCE_INTEGRITY_FAILURE",
            ("RECEIPT_DIGEST_MISMATCH", "ANCESTRY_MISMATCH"),
            ("A receipt whose candidate digest and ancestry both match the evaluated candidate.",),
            signal_state="untrusted",
            evidence_sufficiency="invalid",
            version_binding="tampered",
            commitment_risk="high",
        ),
    }
)

_PAYLOAD_MISMATCH_RULE = _rule(
    "EVIDENCE_INTEGRITY_FAILURE",
    ("REQUEST_PAYLOAD_MISMATCH",),
    ("An exact request from the sealed synthetic fixture corpus.",),
    signal_state="untrusted",
    evidence_sufficiency="invalid",
    commitment_risk="high",
)


def fixture_to_request(case: dict[str, Any]) -> dict[str, Any]:
    """Deep-copy only the eight classifier inputs from a fixture case."""

    return {field: copy.deepcopy(case[field]) for field in _fixture_field_order()}


def classify_review_request(request: Mapping[str, Any]) -> dict[str, Any]:
    """Classify one exact sealed fixture request without I/O or runtime state."""

    normalized = _validate_and_normalize_request(request)
    digest = _request_digest(normalized)
    rule = _SEALED_RULES.get((normalized["id"], digest), _PAYLOAD_MISMATCH_RULE)
    return _build_review(normalized, digest, rule)


def _fixture_field_order() -> tuple[str, ...]:
    return (
        "id",
        "kind",
        "scenario",
        "claim",
        "signal",
        "evidence",
        "required_behaviors",
        "prohibited_behaviors",
    )


def _validate_and_normalize_request(request: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(request, Mapping):
        raise ReviewRequestValidationError("request must be a mapping")

    keys = frozenset(request.keys())
    if keys != _REQUEST_FIELDS:
        missing = sorted(_REQUEST_FIELDS - keys)
        unexpected = sorted(keys - _REQUEST_FIELDS, key=str)
        details = []
        if missing:
            details.append(f"missing fields: {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected fields: {', '.join(map(str, unexpected))}")
        raise ReviewRequestValidationError("; ".join(details))

    _validate_string("id", request["id"], maximum=128, pattern=_ID_PATTERN)
    _validate_string("kind", request["kind"], maximum=128)
    if request["kind"] not in {"positive", "negative", "adversarial"}:
        raise ReviewRequestValidationError("kind is not recognized")
    _validate_string(
        "scenario", request["scenario"], maximum=128, pattern=_SCENARIO_PATTERN
    )
    _validate_string("claim", request["claim"], maximum=4096)
    _validate_string("signal", request["signal"], maximum=4096)

    normalized: dict[str, Any] = {
        field: request[field]
        for field in ("id", "kind", "scenario", "claim", "signal")
    }
    for field in _ARRAY_FIELDS:
        normalized[field] = _validate_and_normalize_array(field, request[field])
    return normalized


def _validate_string(
    field: str,
    value: Any,
    *,
    maximum: int,
    pattern: re.Pattern[str] | None = None,
) -> None:
    if not isinstance(value, str):
        raise ReviewRequestValidationError(f"{field} must be a string")
    if not value.strip():
        raise ReviewRequestValidationError(f"{field} must not be blank")
    if len(value) > maximum:
        raise ReviewRequestValidationError(f"{field} exceeds {maximum} characters")
    if pattern is not None and pattern.fullmatch(value) is None:
        raise ReviewRequestValidationError(f"{field} has an invalid format")


def _validate_and_normalize_array(field: str, value: Any) -> list[str]:
    if not isinstance(value, list):
        raise ReviewRequestValidationError(f"{field} must be an array")
    if not 1 <= len(value) <= 64:
        raise ReviewRequestValidationError(f"{field} must contain 1 through 64 items")
    maximum = 128 if field == "evidence" else 2048
    pattern = _EVIDENCE_REF_PATTERN if field == "evidence" else None
    for item in value:
        _validate_string(field, item, maximum=maximum, pattern=pattern)
    if len(set(value)) != len(value):
        raise ReviewRequestValidationError(f"{field} items must be unique")
    return sorted(value)


def _request_digest(normalized: Mapping[str, Any]) -> str:
    payload = json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _build_review(
    normalized: Mapping[str, Any], digest: str, rule: _Rule
) -> dict[str, Any]:
    withheld_claims = [] if rule.verdict == "VERIFIED_SUCCESS" else [normalized["claim"]]
    warnings = ["FIXTURE_CONFORMANCE_ONLY"]
    if rule.verdict == "EVIDENCE_INTEGRITY_FAILURE":
        warnings.append("Evidence is quarantined; this result verifies no live claim.")
    return {
        "schema_version": "applause-review.v1",
        "review_id": f"fixture-review-{normalized['id'].lower()}-{digest[:16]}",
        "candidate_id": "quirk-applause-gate",
        "case_id": normalized["id"],
        "claim": normalized["claim"],
        "signal": normalized["signal"],
        "claim_state": rule.claim_state,
        "signal_state": rule.signal_state,
        "evidence_sufficiency": rule.evidence_sufficiency,
        "causal_support": rule.causal_support,
        "contradiction_state": rule.contradiction_state,
        "guardrail_state": rule.guardrail_state,
        "version_binding": rule.version_binding,
        "freshness_state": rule.freshness_state,
        "commitment_risk": rule.commitment_risk,
        "verdict": rule.verdict,
        "required_codes": list(rule.required_codes),
        "withheld_claims": withheld_claims,
        "missing_proof": list(rule.missing_proof),
        "reversible_next_move": _NEXT_MOVES[rule.verdict],
        "evidence_refs": list(normalized["evidence"]),
        "warnings": warnings,
        "authority_effect": "none",
    }
