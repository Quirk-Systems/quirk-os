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


if __name__ == "__main__":
    unittest.main()
