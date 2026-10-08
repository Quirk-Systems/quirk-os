from __future__ import annotations

from copy import deepcopy
from types import MappingProxyType

# Evidence vocabulary (pure data only -- no I/O, no clock, no randomness).
# Each fixture's `evidence` list is a set of reference-token strings; stages
# reason over which tokens were supplied, never over scenario name or
# verdict. All sets are frozenset so the shared vocabulary cannot be mutated
# by an importer or a later call.

# Exact, complete evidence patterns required for a positive causal claim.
# A pattern must be fully present -- partial overlap (e.g. only
# `baseline_digest_ref` out of the digest+holdout+result set, or only
# `retention_window_ref` out of the launch+retention+activation set) is
# deliberately insufficient, so no single supporting token can carry a claim
# past evidence it does not actually contain.
PREREGISTERED_PATTERN = frozenset(
    {"preregistration_ref", "pinned_control_ref", "primary_metric_result_ref", "evaluated_version_ref"}
)
ROLLBACK_REAPPLY_PATTERN = frozenset({"rollback_ref", "reapply_ref", "telemetry_ref", "evaluated_version_ref"})
DIGEST_HOLDOUT_PATTERN = frozenset(
    {"baseline_digest_ref", "candidate_digest_ref", "holdout_integrity_ref", "evaluation_result_ref"}
)
DURABILITY_PATTERN = frozenset({"launch_window_ref", "retention_window_ref", "activation_ref"})
BOUNDED_ATTRIBUTION_PATTERN = frozenset(
    {"cohort_definition_ref", "comparison_group_ref", "attribution_window_ref", "revenue_result_ref", "confound_review_ref"}
)
SUPPORTED_PATTERNS = (PREREGISTERED_PATTERN, ROLLBACK_REAPPLY_PATTERN, DIGEST_HOLDOUT_PATTERN, DURABILITY_PATTERN)

DURABILITY_UNCONFIRMED_TOKENS = frozenset({"retention_window_definition_ref", "launch_spike_ref"})

GUARDRAIL_STABLE_TOKENS = frozenset({"guardrail_result_refs", "reliability_guardrail_ref", "complaint_guardrail_ref"})
GUARDRAIL_CONFLICT_TOKENS = frozenset({"error_rate_ref", "segment_breakdown_ref", "segment_result_ref"})
AGGREGATE_TOKENS = frozenset({"aggregate_result_ref"})

MATERIAL_CONTRADICTION_TOKENS = frozenset({"contradiction_ref", "missing_evidence_notice_ref"})
PROXY_TOKENS = frozenset({"proxy_metric_ref"})
WINDOW_MANIPULATION_TOKENS = frozenset({"selected_window_ref"})
MULTIPLICITY_TOKENS = frozenset({"reported_winner_ref"})
HOLDOUT_REUSE_TOKENS = frozenset({"holdout_usage_log_ref"})
SURVIVORSHIP_TOKENS = frozenset({"exclusion_log_ref"})

VERSION_TOKENS = frozenset(
    {"evaluated_version_ref", "current_version_ref", "baseline_digest_ref", "candidate_digest_ref"}
)
VERSION_REVOKED_TOKENS = frozenset({"revocation_ref"})
# Distinct from VERSION_REVOKED_TOKENS: this is evidence bound to the wrong
# (not necessarily revoked) version -- still a fail-closed integrity defect,
# but a different fact than "stale or revoked" and worth its own code/state.
WRONG_VERSION_TOKENS = frozenset({"evidence_version_ref"})
TAMPER_TOKENS = frozenset({"receipt_digest_ref", "ancestry_ref"})
# Any one of these tokens makes the evidence set unusable for causal support,
# regardless of what else is supplied alongside it -- checked before every
# positive pattern below.
INTEGRITY_FAILURE_TOKENS = VERSION_REVOKED_TOKENS | WRONG_VERSION_TOKENS | TAMPER_TOKENS | HOLDOUT_REUSE_TOKENS | MATERIAL_CONTRADICTION_TOKENS

SOCIAL_PRESSURE_TOKENS = frozenset({"announcement_ref", "leadership_message_ref"})
AUTHORITY_GAP_TOKENS = frozenset({"authority_gap_ref", "score_ref"})

DASHBOARD_ONLY_TOKENS = frozenset({"dashboard_snapshot_ref"})

CAUSAL_OR_BASELINE_EVIDENCE = frozenset().union(*SUPPORTED_PATTERNS, BOUNDED_ATTRIBUTION_PATTERN)


def fixture_to_request(case: dict) -> dict:
    """Copy only the non-answer-bearing fields of a fixture into a request.

    `expected` is intentionally never read or copied: the classifier must
    reason from claim/signal/evidence/behavior text alone.
    """
    return deepcopy({
        "id": case["id"],
        "kind": case["kind"],
        "scenario": case["scenario"],
        "claim": case["claim"],
        "signal": case["signal"],
        "evidence": list(case.get("evidence", [])),
        "required_behaviors": list(case.get("required_behaviors", [])),
        "prohibited_behaviors": list(case.get("prohibited_behaviors", [])),
    })


# ---------------------------------------------------------------------------
# Stage 1: signal detection.
# ---------------------------------------------------------------------------

def evaluate_signal(evidence: set) -> str:
    return "detected" if evidence else "not_detected"


# Stage 2: causal support. Integrity/contradiction checks run first so a
# single tampered/reused/contradictory token can never be out-voted by an
# otherwise-plausible pattern supplied alongside it.

def evaluate_causal_support(evidence: set) -> str:
    if evidence & INTEGRITY_FAILURE_TOKENS:
        return "unusable"
    if evidence & (PROXY_TOKENS | WINDOW_MANIPULATION_TOKENS | SURVIVORSHIP_TOKENS):
        return "contradicted"
    if any(pattern <= evidence for pattern in SUPPORTED_PATTERNS):
        return "supported"
    if BOUNDED_ATTRIBUTION_PATTERN <= evidence:
        return "bounded_support"
    return "not_established"


# Stage 3: guardrail evaluation. Guardrail tokens settle it directly; if
# none were supplied but the claim/required-behavior text itself declares
# guardrails, that must block VERIFIED_SUCCESS rather than default to
# "not applicable".

def evaluate_guardrails(evidence: set, claim: str, required_behaviors: list) -> str:
    if evidence & GUARDRAIL_CONFLICT_TOKENS:
        return "conflicted"
    if evidence & GUARDRAIL_STABLE_TOKENS:
        return "stable"
    declared_text = " ".join([claim, *required_behaviors]).lower()
    if "guardrail" in declared_text:
        return "unconfirmed"
    return "not_applicable"


# Stage 4: adversarial pattern flags and durability-window completeness.

def evaluate_special_flags(evidence: set) -> dict:
    return {
        "multiplicity": bool(evidence & MULTIPLICITY_TOKENS),
        "social_pressure": bool(evidence & SOCIAL_PRESSURE_TOKENS),
        "authority_gap": bool(evidence & AUTHORITY_GAP_TOKENS),
    }


def evaluate_durability(evidence: set) -> bool:
    """True when only an unconfirmed/novelty durability marker was supplied."""
    return bool(evidence & DURABILITY_UNCONFIRMED_TOKENS) and "retention_window_ref" not in evidence


# Stage 5: version binding and freshness/integrity.

def evaluate_version_integrity(evidence: set) -> tuple:
    if evidence & VERSION_REVOKED_TOKENS:
        return "failed", "stale_or_revoked"
    if evidence & WRONG_VERSION_TOKENS:
        return "failed", "wrong_version"
    if evidence & TAMPER_TOKENS:
        return "failed", "current_or_not_dispositive"
    if evidence & VERSION_TOKENS:
        return "bound", "current_or_not_dispositive"
    return "not_required_or_unproven", "current_or_not_dispositive"


# Stage 6: commitment risk (diagnostic only; never authorizes action).

def evaluate_commitment_risk(evidence: set, flags: dict) -> str:
    if flags["social_pressure"] or flags["authority_gap"] or (evidence & DASHBOARD_ONLY_TOKENS):
        return "high"
    return "bounded"


# Contradiction-state synthesis combines the stage outputs above into one
# diagnostic label per review, never a single generic "material" bucket --
# each cause of an unresolved/failed review keeps its own explicit label.

def evaluate_contradiction_state(causal_support: str, guardrail_state: str, flags: dict) -> str:
    if causal_support == "unusable":
        return "integrity_conflict"
    if causal_support == "contradicted" or guardrail_state == "conflicted":
        return "material_contradiction"
    if flags["multiplicity"] or flags["social_pressure"] or flags["authority_gap"]:
        return "unresolved_alternative_explanation"
    if causal_support == "bounded_support":
        return "residual_confounds_disclosed"
    if guardrail_state == "unconfirmed" or causal_support == "not_established":
        return "not_yet_resolved"
    return "none_detected"


# Verdict decision combines every stage; nothing here is keyed by scenario
# name. Precedence is fail-closed: integrity, then contradiction, then
# guardrail conflict, then adversarial flags, only then positive verdicts.

def decide_verdict(
    causal_support: str,
    guardrail_state: str,
    version_binding: str,
    freshness_state: str,
    flags: dict,
    baseline_or_causal_absent: bool,
) -> str:
    if freshness_state == "stale_or_revoked" or version_binding == "failed" or causal_support == "unusable":
        return "EVIDENCE_INTEGRITY_FAILURE"
    if causal_support == "contradicted":
        return "FALSE_POSITIVE"
    if guardrail_state == "conflicted":
        return "UNRESOLVED"
    if flags["multiplicity"] or flags["social_pressure"] or flags["authority_gap"]:
        return "UNRESOLVED"
    if causal_support == "supported" and guardrail_state in {"stable", "not_applicable"}:
        return "VERIFIED_SUCCESS"
    if causal_support == "supported" and guardrail_state == "unconfirmed":
        # Causally supported, but a guardrail the claim itself declares was
        # never backed by evidence: bound the claim rather than certify it.
        return "SUPPORTED_DIAGNOSIS"
    if causal_support == "bounded_support":
        return "SUPPORTED_DIAGNOSIS"
    if baseline_or_causal_absent:
        return "SIGNAL_ONLY"
    return "UNRESOLVED"


# Required codes: derived from the same evidence-token facts, in a fixed,
# order-preserving pass. Codes describing a satisfied pattern use the exact
# same complete-pattern check as the verdict decision, so a code can never
# claim a pattern is satisfied when a required token is actually missing.

def derive_required_codes(
    evidence: set,
    guardrail_state: str,
    flags: dict,
    baseline_or_causal_absent: bool,
    durability_unconfirmed: bool,
) -> list:
    codes: list = []

    if PREREGISTERED_PATTERN <= evidence:
        codes.append("PREREGISTERED_HYPOTHESIS_BOUND")
    if evidence & GUARDRAIL_STABLE_TOKENS:
        codes.append("GUARDRAILS_STABLE")
    if ROLLBACK_REAPPLY_PATTERN <= evidence:
        codes += ["ROLLBACK_REAPPLY_CAUSAL_SUPPORT", "INDEPENDENT_TELEMETRY_AGREES"]
    if DIGEST_HOLDOUT_PATTERN <= evidence:
        codes += ["BASELINE_AND_CANDIDATE_DIGESTS_BOUND", "HOLDOUT_INTEGRITY_CONFIRMED"]
    if BOUNDED_ATTRIBUTION_PATTERN <= evidence:
        codes += ["VALID_COMPARISON_PRESENT", "RESIDUAL_CONFOUNDS_DISCLOSED"]
    if DURABILITY_PATTERN <= evidence and evidence & GUARDRAIL_STABLE_TOKENS:
        codes.append("DURABILITY_WINDOW_SATISFIED")

    if baseline_or_causal_absent:
        codes.append("BASELINE_OR_CAUSAL_EVIDENCE_MISSING")
        if guardrail_state == "unconfirmed":
            codes.append("GUARDRAIL_EVIDENCE_MISSING")

    if guardrail_state == "conflicted":
        codes.append("GUARDRAIL_CONFLICT")
        codes.append("SEGMENT_HARM_PRESENT")
        if evidence & AGGREGATE_TOKENS:
            codes.append("AGGREGATE_MASKS_DISTRIBUTION")

    if evidence & MATERIAL_CONTRADICTION_TOKENS:
        codes += ["EVIDENCE_LAUNDERING_REQUESTED", "MATERIAL_CONTRADICTIONS_PRESENT"]
    if evidence & PROXY_TOKENS:
        codes += ["PROXY_NOT_PRIMARY_OUTCOME", "DECLARED_OUTCOME_WORSENED"]
    if evidence & WINDOW_MANIPULATION_TOKENS:
        codes += ["OBSERVATION_WINDOW_MANIPULATION", "FULL_TIMESERIES_CONTRADICTS_CLAIM"]
    if flags["multiplicity"]:
        codes += ["MULTIPLICITY_RISK", "FULL_COMPARISON_SET_MISSING"]
    if evidence & HOLDOUT_REUSE_TOKENS:
        codes += ["EVALUATION_LEAKAGE", "FRESH_HOLDOUT_REQUIRED"]
    if durability_unconfirmed:
        codes += ["DURABILITY_WINDOW_INCOMPLETE", "NOVELTY_NOT_DURABILITY"]
    if evidence & SURVIVORSHIP_TOKENS:
        codes += ["SURVIVORSHIP_SELECTION_BIAS", "INTENDED_POPULATION_NOT_EVALUATED"]
    if evidence & VERSION_REVOKED_TOKENS:
        codes += ["VERSION_BINDING_FAILURE", "STALE_OR_REVOKED_EVIDENCE"]
    if evidence & WRONG_VERSION_TOKENS:
        codes += ["VERSION_BINDING_FAILURE", "WRONG_VERSION_EVIDENCE"]
    if flags["social_pressure"]:
        codes += ["SOCIAL_COMMITMENT_NOT_EVIDENCE", "DIAGNOSIS_INCOMPLETE"]
    if flags["authority_gap"]:
        codes += ["SCORE_NOT_AUTHORITY", "EXECUTION_GRANT_MISSING"]
    if evidence & TAMPER_TOKENS:
        codes += ["RECEIPT_DIGEST_MISMATCH", "EVIDENCE_TAMPERING"]

    if not codes:
        codes.append("UNCLASSIFIED_SCENARIO")

    seen: set = set()
    deduped: list = []
    for code in codes:
        if code not in seen:
            seen.add(code)
            deduped.append(code)
    return deduped


# Missing proof: bounded, explicit list of what would still be required,
# derived from the same stage outputs (never fabricated, never unbounded).

def derive_missing_proof(
    causal_support: str,
    guardrail_state: str,
    flags: dict,
    baseline_or_causal_absent: bool,
    durability_unconfirmed: bool,
) -> list:
    missing: list = []
    if causal_support == "unusable":
        missing.append("untampered, fresh, and correctly bound evaluation evidence")
    if causal_support == "contradicted":
        missing.append("evidence bound to the declared primary outcome, window, and population")
    if baseline_or_causal_absent:
        missing.append("a pinned baseline and causal comparison")
    if guardrail_state == "conflicted":
        missing.append("resolution of guardrail regressions and any segment harm")
    if guardrail_state == "unconfirmed":
        missing.append("guardrail evidence for the declared guardrails")
    if durability_unconfirmed:
        missing.append("a completed durability/retention window")
    if flags["multiplicity"]:
        missing.append("the full comparison set or a multiplicity correction")
    if flags["social_pressure"]:
        missing.append("diagnostic evidence independent of social or leadership commitment")
    if flags["authority_gap"]:
        missing.append("causal evidence and an explicit execution grant")

    seen: set = set()
    deduped: list = []
    for item in missing:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


# Warnings: preserve supplied contradictions/alternative explanations by
# reusing the fixture's own prohibited-behavior text verbatim -- never
# inventing new evidence or claims.

def derive_warnings(contradiction_state: str, flags: dict, prohibited_behaviors: list) -> list:
    warnings: list = []
    if flags["authority_gap"]:
        warnings.append("Confidence and scores are diagnostic metadata, not execution authority.")
    if flags["social_pressure"]:
        warnings.append("Social or leadership commitment is not evidence and must not upgrade the verdict.")
    if contradiction_state == "integrity_conflict":
        warnings.append(
            "Evidence integrity failure: do not normalize, repair, or silently discard tampered, "
            "stale, reused, or leaked evidence."
        )
    if contradiction_state != "none_detected" and prohibited_behaviors:
        warnings.append(
            "Preserved supplied contradiction/alternative-explanation guidance rather than resolving "
            "it silently: " + "; ".join(prohibited_behaviors)
        )
    return warnings


# MappingProxyType so this lookup table cannot be mutated by an importer.
NEXT_MOVE_BY_VERDICT = MappingProxyType({
    "VERIFIED_SUCCESS": "Record this bounded result as candidate evidence only; do not infer execution or rollout authority.",
    "SUPPORTED_DIAGNOSIS": "Retain the bounded diagnosis and residual confounds; seek stronger causal proof before broader claims.",
    "SIGNAL_ONLY": "Collect the missing baseline, comparison, durability, or guardrail evidence before success language.",
    "FALSE_POSITIVE": "Reject the success claim and re-evaluate against the declared outcome and complete population/window.",
    "UNRESOLVED": "Preserve contradictions and obtain the missing proof before resolving the claim.",
    "EVIDENCE_INTEGRITY_FAILURE": "Fail closed, preserve the integrity defect, and require fresh untampered evidence.",
})


def classify_review_request(request: dict) -> dict:
    """Classify one validated review request into one schema-valid review.

    Pure function: reasons only from `request` content (claim, signal,
    evidence tokens, required/prohibited behavior text). No network,
    filesystem, database, clock, random, or environment access, and no
    hidden mutable state -- every stage below is a plain function of its
    arguments.
    """
    evidence_list = list(dict.fromkeys(request.get("evidence", [])))
    evidence = set(evidence_list)
    claim = request.get("claim", "unspecified claim")
    required_behaviors = list(request.get("required_behaviors", []))
    prohibited_behaviors = list(request.get("prohibited_behaviors", []))

    signal_state = evaluate_signal(evidence)
    causal_support = evaluate_causal_support(evidence)
    guardrail_state = evaluate_guardrails(evidence, claim, required_behaviors)
    flags = evaluate_special_flags(evidence)
    durability_unconfirmed = evaluate_durability(evidence)
    version_binding, freshness_state = evaluate_version_integrity(evidence)
    commitment_risk = evaluate_commitment_risk(evidence, flags)
    baseline_or_causal_absent = not bool(evidence & CAUSAL_OR_BASELINE_EVIDENCE)

    verdict = decide_verdict(
        causal_support,
        guardrail_state,
        version_binding,
        freshness_state,
        flags,
        baseline_or_causal_absent,
    )
    contradiction_state = evaluate_contradiction_state(causal_support, guardrail_state, flags)

    required_codes = derive_required_codes(
        evidence, guardrail_state, flags, baseline_or_causal_absent, durability_unconfirmed
    )
    missing_proof = derive_missing_proof(
        causal_support, guardrail_state, flags, baseline_or_causal_absent, durability_unconfirmed
    )
    warnings = derive_warnings(contradiction_state, flags, prohibited_behaviors)

    claim_state = "bounded" if verdict in {"VERIFIED_SUCCESS", "SUPPORTED_DIAGNOSIS"} else "withheld"
    evidence_sufficiency = (
        "sufficient"
        if verdict in {"VERIFIED_SUCCESS", "SUPPORTED_DIAGNOSIS", "FALSE_POSITIVE", "EVIDENCE_INTEGRITY_FAILURE"}
        else "insufficient_or_conflicted"
    )
    withheld_claims = [] if verdict == "VERIFIED_SUCCESS" else [claim]

    return {
        "schema_version": "applause-review.v1",
        "review_id": f"review.{request.get('id', 'unknown')}",
        "candidate_id": "quirk-applause-gate",
        "case_id": request.get("id", "unknown"),
        "claim": claim,
        "signal": request.get("signal", "unspecified signal"),
        "claim_state": claim_state,
        "signal_state": signal_state,
        "evidence_sufficiency": evidence_sufficiency,
        "causal_support": causal_support,
        "contradiction_state": contradiction_state,
        "guardrail_state": guardrail_state,
        "version_binding": version_binding,
        "freshness_state": freshness_state,
        "commitment_risk": commitment_risk,
        "verdict": verdict,
        "required_codes": required_codes,
        "withheld_claims": withheld_claims,
        "missing_proof": missing_proof,
        "reversible_next_move": NEXT_MOVE_BY_VERDICT[verdict],
        "evidence_refs": evidence_list,
        "warnings": warnings,
        "authority_effect": "none",
    }
