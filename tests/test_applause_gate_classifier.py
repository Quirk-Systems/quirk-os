from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas" / "applause-review.schema.json").read_text(encoding="utf-8"))
CASES = json.loads((ROOT / "evals" / "applause-gate" / "cases.json").read_text(encoding="utf-8"))["cases"]


def case_by_id(case_id: str) -> dict:
    return next(case for case in CASES if case["id"] == case_id)


class ApplauseGateClassifierTests(unittest.TestCase):
    def validate_review(self, review: dict) -> None:
        errors = list(Draft202012Validator(SCHEMA).iter_errors(review))
        self.assertEqual(errors, [])

    def classify(self, case_id: str) -> dict:
        from applause_gate.classifier import classify_review_request, fixture_to_request

        case = case_by_id(case_id)
        request = fixture_to_request(case)
        self.assertNotIn("expected", request)
        review = classify_review_request(request)
        self.validate_review(review)
        self.assertEqual(review["authority_effect"], "none")
        self.assertTrue(set(review["evidence_refs"]).issubset(set(case["evidence"])))
        return review

    def test_preregistered_ab_test_returns_verified_success(self):
        self.assertEqual(self.classify("ABG-P01")["verdict"], "VERIFIED_SUCCESS")

    def test_dashboard_only_claim_returns_signal_only(self):
        review = self.classify("ABG-N01")
        self.assertEqual(review["verdict"], "SIGNAL_ONLY")
        self.assertIn("BASELINE_OR_CAUSAL_EVIDENCE_MISSING", review["required_codes"])

    def test_proxy_substitution_returns_false_positive(self):
        review = self.classify("ABG-A01")
        self.assertEqual(review["verdict"], "FALSE_POSITIVE")
        self.assertIn("PROXY_NOT_PRIMARY_OUTCOME", review["required_codes"])

    def test_holdout_leakage_returns_integrity_failure(self):
        review = self.classify("ABG-A04")
        self.assertEqual(review["verdict"], "EVIDENCE_INTEGRITY_FAILURE")
        self.assertIn("EVALUATION_LEAKAGE", review["required_codes"])

    def test_confidence_does_not_authorize_rollout(self):
        review = self.classify("ABG-A10")
        self.assertEqual(review["verdict"], "UNRESOLVED")
        self.assertIn("SCORE_NOT_AUTHORITY", review["required_codes"])
        self.assertEqual(review["authority_effect"], "none")


# ---------------------------------------------------------------------------
# One explicit decision-rule assertion per one of the 19 frozen fixtures.
#
# Each row locks not just the verdict but every separated diagnostic stage
# (signal, causal support, guardrail evaluation, contradiction handling,
# freshness/version integrity, commitment risk) and the exact required
# codes, so a future change to any single stage function is caught here
# even if the aggregate conformance runner would still show 19/19 verdicts
# matching (e.g. a stage regressing to the right verdict for the wrong
# reason).
# ---------------------------------------------------------------------------

DECISION_RULE_TABLE = {
    "ABG-P01": {
        "verdict": "VERIFIED_SUCCESS",
        "required_codes": ["GUARDRAILS_STABLE", "PREREGISTERED_HYPOTHESIS_BOUND"],
        "signal_state": "detected",
        "causal_support": "supported",
        "guardrail_state": "stable",
        "contradiction_state": "none_detected",
        "version_binding": "bound",
        "freshness_state": "current_or_not_dispositive",
        "commitment_risk": "bounded",
    },
    "ABG-P02": {
        "verdict": "VERIFIED_SUCCESS",
        "required_codes": ["INDEPENDENT_TELEMETRY_AGREES", "ROLLBACK_REAPPLY_CAUSAL_SUPPORT"],
        "signal_state": "detected",
        "causal_support": "supported",
        "guardrail_state": "not_applicable",
        "contradiction_state": "none_detected",
        "version_binding": "bound",
        "freshness_state": "current_or_not_dispositive",
        "commitment_risk": "bounded",
    },
    "ABG-P03": {
        "verdict": "VERIFIED_SUCCESS",
        "required_codes": ["BASELINE_AND_CANDIDATE_DIGESTS_BOUND", "HOLDOUT_INTEGRITY_CONFIRMED"],
        "signal_state": "detected",
        "causal_support": "supported",
        "guardrail_state": "not_applicable",
        "contradiction_state": "none_detected",
        "version_binding": "bound",
        "freshness_state": "current_or_not_dispositive",
        "commitment_risk": "bounded",
    },
    "ABG-P04": {
        "verdict": "SUPPORTED_DIAGNOSIS",
        "required_codes": ["RESIDUAL_CONFOUNDS_DISCLOSED", "VALID_COMPARISON_PRESENT"],
        "signal_state": "detected",
        "causal_support": "bounded_support",
        "guardrail_state": "not_applicable",
        "contradiction_state": "residual_confounds_disclosed",
        "version_binding": "not_required_or_unproven",
        "freshness_state": "current_or_not_dispositive",
        "commitment_risk": "bounded",
    },
    "ABG-P05": {
        "verdict": "VERIFIED_SUCCESS",
        "required_codes": ["DURABILITY_WINDOW_SATISFIED", "GUARDRAILS_STABLE"],
        "signal_state": "detected",
        "causal_support": "supported",
        "guardrail_state": "stable",
        "contradiction_state": "none_detected",
        "version_binding": "not_required_or_unproven",
        "freshness_state": "current_or_not_dispositive",
        "commitment_risk": "bounded",
    },
    "ABG-N01": {
        "verdict": "SIGNAL_ONLY",
        "required_codes": ["BASELINE_OR_CAUSAL_EVIDENCE_MISSING", "GUARDRAIL_EVIDENCE_MISSING"],
        "signal_state": "detected",
        "causal_support": "not_established",
        "guardrail_state": "unconfirmed",
        "contradiction_state": "not_yet_resolved",
        "version_binding": "not_required_or_unproven",
        "freshness_state": "current_or_not_dispositive",
        "commitment_risk": "high",
    },
    "ABG-N02": {
        "verdict": "UNRESOLVED",
        "required_codes": ["BASELINE_OR_CAUSAL_EVIDENCE_MISSING", "GUARDRAIL_CONFLICT", "SEGMENT_HARM_PRESENT"],
        "signal_state": "detected",
        "causal_support": "not_established",
        "guardrail_state": "conflicted",
        "contradiction_state": "material_contradiction",
        "version_binding": "not_required_or_unproven",
        "freshness_state": "current_or_not_dispositive",
        "commitment_risk": "bounded",
    },
    "ABG-N03": {
        "verdict": "EVIDENCE_INTEGRITY_FAILURE",
        "required_codes": [
            "BASELINE_OR_CAUSAL_EVIDENCE_MISSING",
            "EVIDENCE_LAUNDERING_REQUESTED",
            "MATERIAL_CONTRADICTIONS_PRESENT",
        ],
        "signal_state": "detected",
        "causal_support": "unusable",
        "guardrail_state": "not_applicable",
        "contradiction_state": "integrity_conflict",
        "version_binding": "not_required_or_unproven",
        "freshness_state": "current_or_not_dispositive",
        "commitment_risk": "bounded",
    },
    "ABG-A01": {
        "verdict": "FALSE_POSITIVE",
        "required_codes": [
            "BASELINE_OR_CAUSAL_EVIDENCE_MISSING",
            "DECLARED_OUTCOME_WORSENED",
            "PROXY_NOT_PRIMARY_OUTCOME",
        ],
        "signal_state": "detected",
        "causal_support": "contradicted",
        "guardrail_state": "not_applicable",
        "contradiction_state": "material_contradiction",
        "version_binding": "not_required_or_unproven",
        "freshness_state": "current_or_not_dispositive",
        "commitment_risk": "bounded",
    },
    "ABG-A02": {
        "verdict": "FALSE_POSITIVE",
        "required_codes": [
            "BASELINE_OR_CAUSAL_EVIDENCE_MISSING",
            "FULL_TIMESERIES_CONTRADICTS_CLAIM",
            "OBSERVATION_WINDOW_MANIPULATION",
        ],
        "signal_state": "detected",
        "causal_support": "contradicted",
        "guardrail_state": "not_applicable",
        "contradiction_state": "material_contradiction",
        "version_binding": "not_required_or_unproven",
        "freshness_state": "current_or_not_dispositive",
        "commitment_risk": "bounded",
    },
    "ABG-A03": {
        "verdict": "UNRESOLVED",
        "required_codes": [
            "BASELINE_OR_CAUSAL_EVIDENCE_MISSING",
            "FULL_COMPARISON_SET_MISSING",
            "MULTIPLICITY_RISK",
        ],
        "signal_state": "detected",
        "causal_support": "not_established",
        "guardrail_state": "not_applicable",
        "contradiction_state": "unresolved_alternative_explanation",
        "version_binding": "not_required_or_unproven",
        "freshness_state": "current_or_not_dispositive",
        "commitment_risk": "bounded",
    },
    "ABG-A04": {
        "verdict": "EVIDENCE_INTEGRITY_FAILURE",
        "required_codes": [
            "BASELINE_OR_CAUSAL_EVIDENCE_MISSING",
            "EVALUATION_LEAKAGE",
            "FRESH_HOLDOUT_REQUIRED",
        ],
        "signal_state": "detected",
        "causal_support": "unusable",
        "guardrail_state": "not_applicable",
        "contradiction_state": "integrity_conflict",
        "version_binding": "not_required_or_unproven",
        "freshness_state": "current_or_not_dispositive",
        "commitment_risk": "bounded",
    },
    "ABG-A05": {
        "verdict": "SIGNAL_ONLY",
        "required_codes": [
            "BASELINE_OR_CAUSAL_EVIDENCE_MISSING",
            "DURABILITY_WINDOW_INCOMPLETE",
            "NOVELTY_NOT_DURABILITY",
        ],
        "signal_state": "detected",
        "causal_support": "not_established",
        "guardrail_state": "not_applicable",
        "contradiction_state": "not_yet_resolved",
        "version_binding": "not_required_or_unproven",
        "freshness_state": "current_or_not_dispositive",
        "commitment_risk": "bounded",
    },
    "ABG-A06": {
        "verdict": "UNRESOLVED",
        "required_codes": [
            "AGGREGATE_MASKS_DISTRIBUTION",
            "BASELINE_OR_CAUSAL_EVIDENCE_MISSING",
            "GUARDRAIL_CONFLICT",
            "SEGMENT_HARM_PRESENT",
        ],
        "signal_state": "detected",
        "causal_support": "not_established",
        "guardrail_state": "conflicted",
        "contradiction_state": "material_contradiction",
        "version_binding": "not_required_or_unproven",
        "freshness_state": "current_or_not_dispositive",
        "commitment_risk": "bounded",
    },
    "ABG-A07": {
        "verdict": "FALSE_POSITIVE",
        "required_codes": [
            "BASELINE_OR_CAUSAL_EVIDENCE_MISSING",
            "INTENDED_POPULATION_NOT_EVALUATED",
            "SURVIVORSHIP_SELECTION_BIAS",
        ],
        "signal_state": "detected",
        "causal_support": "contradicted",
        "guardrail_state": "not_applicable",
        "contradiction_state": "material_contradiction",
        "version_binding": "not_required_or_unproven",
        "freshness_state": "current_or_not_dispositive",
        "commitment_risk": "bounded",
    },
    "ABG-A08": {
        "verdict": "EVIDENCE_INTEGRITY_FAILURE",
        "required_codes": [
            "BASELINE_OR_CAUSAL_EVIDENCE_MISSING",
            "STALE_OR_REVOKED_EVIDENCE",
            "VERSION_BINDING_FAILURE",
            "WRONG_VERSION_EVIDENCE",
        ],
        "signal_state": "detected",
        "causal_support": "unusable",
        "guardrail_state": "not_applicable",
        "contradiction_state": "integrity_conflict",
        "version_binding": "failed",
        "freshness_state": "stale_or_revoked",
        "commitment_risk": "bounded",
    },
    "ABG-A09": {
        "verdict": "UNRESOLVED",
        "required_codes": [
            "BASELINE_OR_CAUSAL_EVIDENCE_MISSING",
            "DIAGNOSIS_INCOMPLETE",
            "SOCIAL_COMMITMENT_NOT_EVIDENCE",
        ],
        "signal_state": "detected",
        "causal_support": "not_established",
        "guardrail_state": "not_applicable",
        "contradiction_state": "unresolved_alternative_explanation",
        "version_binding": "not_required_or_unproven",
        "freshness_state": "current_or_not_dispositive",
        "commitment_risk": "high",
    },
    "ABG-A10": {
        "verdict": "UNRESOLVED",
        "required_codes": [
            "BASELINE_OR_CAUSAL_EVIDENCE_MISSING",
            "EXECUTION_GRANT_MISSING",
            "SCORE_NOT_AUTHORITY",
        ],
        "signal_state": "detected",
        "causal_support": "not_established",
        "guardrail_state": "not_applicable",
        "contradiction_state": "unresolved_alternative_explanation",
        "version_binding": "not_required_or_unproven",
        "freshness_state": "current_or_not_dispositive",
        "commitment_risk": "high",
    },
    "ABG-A11": {
        "verdict": "EVIDENCE_INTEGRITY_FAILURE",
        "required_codes": ["EVIDENCE_TAMPERING", "RECEIPT_DIGEST_MISMATCH"],
        "signal_state": "detected",
        "causal_support": "unusable",
        "guardrail_state": "not_applicable",
        "contradiction_state": "integrity_conflict",
        "version_binding": "failed",
        "freshness_state": "current_or_not_dispositive",
        "commitment_risk": "bounded",
    },
}


class ApplauseGateDecisionRuleTableTests(unittest.TestCase):
    """One focused decision-rule assertion for every one of the 19 fixtures.

    Every stage exposed by ``classify_review_request`` (signal, causal
    support, guardrail evaluation, contradiction handling, freshness/version
    integrity, and commitment risk) is asserted explicitly per case, not
    just the final verdict, so drift in any single separated stage is
    caught here.
    """

    def setUp(self):
        self.assertEqual(
            {case["id"] for case in CASES},
            set(DECISION_RULE_TABLE),
            "decision-rule table must cover exactly the 19 frozen fixture IDs",
        )

    def test_each_fixture_matches_its_explicit_decision_rule(self):
        from applause_gate.classifier import classify_review_request, fixture_to_request

        for case in CASES:
            expected = DECISION_RULE_TABLE[case["id"]]
            with self.subTest(case_id=case["id"], scenario=case["scenario"]):
                request = fixture_to_request(case)
                self.assertNotIn("expected", request)

                review = classify_review_request(request)
                errors = list(Draft202012Validator(SCHEMA).iter_errors(review))
                self.assertEqual(errors, [])

                self.assertEqual(review["verdict"], case["expected"]["verdict"])
                self.assertEqual(review["verdict"], expected["verdict"])
                self.assertEqual(sorted(review["required_codes"]), expected["required_codes"])
                self.assertEqual(review["signal_state"], expected["signal_state"])
                self.assertEqual(review["causal_support"], expected["causal_support"])
                self.assertEqual(review["guardrail_state"], expected["guardrail_state"])
                self.assertEqual(review["contradiction_state"], expected["contradiction_state"])
                self.assertEqual(review["version_binding"], expected["version_binding"])
                self.assertEqual(review["freshness_state"], expected["freshness_state"])
                self.assertEqual(review["commitment_risk"], expected["commitment_risk"])
                self.assertEqual(review["authority_effect"], "none")

                # Never fabricate evidence: every returned evidence_ref must
                # trace back to evidence the fixture actually supplied.
                self.assertTrue(set(review["evidence_refs"]).issubset(set(case["evidence"])))

                # Preservation: whenever a case is not the clean success
                # path, the fixture's own prohibited-behavior/alternative-
                # explanation text must survive into the output rather than
                # being silently dropped.
                if review["contradiction_state"] != "none_detected" and case["prohibited_behaviors"]:
                    joined_warnings = " ".join(review["warnings"])
                    for prohibited in case["prohibited_behaviors"]:
                        self.assertIn(prohibited, joined_warnings)

                # missing_proof must stay bounded (never empty prose, never
                # unbounded free text). It is empty exactly when the claim
                # is fully verified, or when the residual gap was already
                # disclosed as bounded (nothing further to withhold), and
                # non-empty whenever material evidence is genuinely missing
                # or unresolved.
                self.assertIsInstance(review["missing_proof"], list)
                if review["verdict"] == "VERIFIED_SUCCESS":
                    self.assertEqual(review["missing_proof"], [])
                elif review["contradiction_state"] == "residual_confounds_disclosed":
                    self.assertEqual(review["missing_proof"], [])
                else:
                    self.assertTrue(review["missing_proof"])


class ApplauseGateMutationTests(unittest.TestCase):
    """Mutation checks: missing material evidence must never remain
    VERIFIED_SUCCESS, and injected integrity defects must dominate an
    otherwise-clean positive case.
    """

    def classify_mutated(self, case_id: str, evidence: list) -> dict:
        from applause_gate.classifier import classify_review_request, fixture_to_request

        case = case_by_id(case_id)
        request = fixture_to_request(case)
        request["evidence"] = evidence
        review = classify_review_request(request)
        errors = list(Draft202012Validator(SCHEMA).iter_errors(review))
        self.assertEqual(errors, [])
        return review

    def test_removing_declared_guardrail_evidence_blocks_verified_success(self):
        from applause_gate.classifier import classify_review_request, fixture_to_request

        baseline = case_by_id("ABG-P01")
        # Sanity check: the unmutated fixture is still VERIFIED_SUCCESS.
        self.assertEqual(
            classify_review_request(fixture_to_request(baseline))["verdict"],
            "VERIFIED_SUCCESS",
        )
        mutated_evidence = [e for e in baseline["evidence"] if e != "guardrail_result_refs"]
        review = self.classify_mutated("ABG-P01", mutated_evidence)
        self.assertNotEqual(review["verdict"], "VERIFIED_SUCCESS")
        self.assertEqual(review["guardrail_state"], "unconfirmed")
        self.assertIn("guardrail evidence for the declared guardrails", review["missing_proof"])

    def test_removing_baseline_and_causal_evidence_blocks_verified_success(self):
        review = self.classify_mutated("ABG-P01", [])
        self.assertNotEqual(review["verdict"], "VERIFIED_SUCCESS")
        self.assertEqual(review["causal_support"], "not_established")
        self.assertIn("a pinned baseline and causal comparison", review["missing_proof"])

    def test_retention_window_alone_does_not_yield_verified_success(self):
        """Regression: retention_window_ref alone must not satisfy the P05
        durability pattern (launch + retention + activation), even with
        stable guardrail evidence present alongside it."""
        baseline = case_by_id("ABG-P05")
        mutated_evidence = [e for e in baseline["evidence"] if e not in ("launch_window_ref", "activation_ref")]
        review = self.classify_mutated("ABG-P05", mutated_evidence)
        self.assertNotEqual(review["verdict"], "VERIFIED_SUCCESS")
        self.assertEqual(review["causal_support"], "not_established")
        self.assertNotIn("DURABILITY_WINDOW_SATISFIED", review["required_codes"])

    def test_missing_reapply_blocks_p02_verified_success(self):
        baseline = case_by_id("ABG-P02")
        mutated_evidence = [e for e in baseline["evidence"] if e != "reapply_ref"]
        review = self.classify_mutated("ABG-P02", mutated_evidence)
        self.assertNotEqual(review["verdict"], "VERIFIED_SUCCESS")
        self.assertEqual(review["causal_support"], "not_established")
        self.assertNotIn("ROLLBACK_REAPPLY_CAUSAL_SUPPORT", review["required_codes"])

    def test_missing_evaluation_result_blocks_p03_verified_success(self):
        baseline = case_by_id("ABG-P03")
        mutated_evidence = [e for e in baseline["evidence"] if e != "evaluation_result_ref"]
        review = self.classify_mutated("ABG-P03", mutated_evidence)
        self.assertNotEqual(review["verdict"], "VERIFIED_SUCCESS")
        self.assertEqual(review["causal_support"], "not_established")
        self.assertNotIn("BASELINE_AND_CANDIDATE_DIGESTS_BOUND", review["required_codes"])

    def test_missing_evaluated_version_or_primary_result_blocks_p01_verified_success(self):
        baseline = case_by_id("ABG-P01")
        for dropped_token in ("evaluated_version_ref", "primary_metric_result_ref"):
            with self.subTest(dropped_token=dropped_token):
                mutated_evidence = [e for e in baseline["evidence"] if e != dropped_token]
                review = self.classify_mutated("ABG-P01", mutated_evidence)
                self.assertNotEqual(review["verdict"], "VERIFIED_SUCCESS")
                self.assertEqual(review["causal_support"], "not_established")
                self.assertNotIn("PREREGISTERED_HYPOTHESIS_BOUND", review["required_codes"])

    def test_evidence_version_token_alone_forces_integrity_failure(self):
        """`evidence_version_ref` is a distinct wrong-version integrity
        defect from `revocation_ref` (stale/revoked) and must fail closed
        on its own, without a revocation token present."""
        baseline = case_by_id("ABG-A08")
        mutated_evidence = [e for e in baseline["evidence"] if e != "revocation_ref"]
        self.assertIn("evidence_version_ref", mutated_evidence)
        review = self.classify_mutated("ABG-A08", mutated_evidence)
        self.assertEqual(review["verdict"], "EVIDENCE_INTEGRITY_FAILURE")
        self.assertEqual(review["version_binding"], "failed")
        self.assertEqual(review["freshness_state"], "wrong_version")
        self.assertIn("WRONG_VERSION_EVIDENCE", review["required_codes"])

    def test_injecting_a_revoked_evidence_token_forces_integrity_failure(self):
        baseline = case_by_id("ABG-P01")
        mutated_evidence = list(baseline["evidence"]) + ["revocation_ref"]
        review = self.classify_mutated("ABG-P01", mutated_evidence)
        self.assertEqual(review["verdict"], "EVIDENCE_INTEGRITY_FAILURE")
        self.assertEqual(review["freshness_state"], "stale_or_revoked")

    def test_injecting_a_tampered_receipt_token_forces_integrity_failure_even_with_full_positive_evidence(self):
        baseline = case_by_id("ABG-P03")
        mutated_evidence = list(baseline["evidence"]) + ["receipt_digest_ref", "ancestry_ref"]
        review = self.classify_mutated("ABG-P03", mutated_evidence)
        self.assertEqual(review["verdict"], "EVIDENCE_INTEGRITY_FAILURE")
        self.assertEqual(review["version_binding"], "failed")

    def test_token_vocabulary_is_frozen_and_results_are_not_aliased(self):
        """Hidden-mutable-state guard: the module's evidence vocabulary is
        frozenset (cannot be mutated by an importer), and two calls with
        equal input never share a mutable result object -- mutating one
        call's returned lists must not affect a second, independent call.
        """
        import applause_gate.classifier as clf

        for name in (
            "PREREGISTERED_PATTERN",
            "ROLLBACK_REAPPLY_PATTERN",
            "DIGEST_HOLDOUT_PATTERN",
            "DURABILITY_PATTERN",
            "BOUNDED_ATTRIBUTION_PATTERN",
            "GUARDRAIL_STABLE_TOKENS",
            "INTEGRITY_FAILURE_TOKENS",
            "CAUSAL_OR_BASELINE_EVIDENCE",
        ):
            value = getattr(clf, name)
            self.assertIsInstance(value, frozenset, name)
            with self.assertRaises(AttributeError):
                value.add("tampered")

        case = case_by_id("ABG-P01")
        request = clf.fixture_to_request(case)
        first = clf.classify_review_request(request)
        second = clf.classify_review_request(request)
        for key in ("required_codes", "missing_proof", "warnings", "evidence_refs", "withheld_claims"):
            self.assertIsNot(first[key], second[key])
            first[key].append("__mutated_by_test__")
            self.assertNotIn("__mutated_by_test__", second[key])
        self.assertNotIn("__mutated_by_test__", clf.classify_review_request(request)["required_codes"])


if __name__ == "__main__":
    unittest.main()
