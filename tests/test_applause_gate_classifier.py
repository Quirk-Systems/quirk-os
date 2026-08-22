from __future__ import annotations

import copy
import json
import os
import random
import socket
import time
import unittest
from collections.abc import Mapping
from pathlib import Path
from unittest import mock

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads(
    (ROOT / "schemas" / "applause-review.schema.json").read_text(encoding="utf-8")
)
CASES = json.loads(
    (ROOT / "evals" / "applause-gate" / "cases.json").read_text(encoding="utf-8")
)["cases"]
REQUEST_FIELDS = {
    "id",
    "kind",
    "scenario",
    "claim",
    "signal",
    "evidence",
    "required_behaviors",
    "prohibited_behaviors",
}

EXPECTED_OUTCOMES = {
    "ABG-P01": ("VERIFIED_SUCCESS", {"PREREGISTERED_HYPOTHESIS_BOUND", "GUARDRAILS_STABLE"}),
    "ABG-P02": ("VERIFIED_SUCCESS", {"ROLLBACK_REAPPLY_SUPPORT", "TELEMETRY_CORROBORATED"}),
    "ABG-P03": ("VERIFIED_SUCCESS", {"HOLDOUT_INTEGRITY_VERIFIED", "VERSION_BOUND"}),
    "ABG-P04": ("SUPPORTED_DIAGNOSIS", {"VALID_COMPARISON", "RESIDUAL_CONFOUNDS_PRESERVED"}),
    "ABG-P05": ("VERIFIED_SUCCESS", {"DURABILITY_WINDOW_COMPLETE", "GUARDRAILS_STABLE"}),
    "ABG-N01": ("SIGNAL_ONLY", {"BASELINE_OR_CAUSAL_EVIDENCE_MISSING"}),
    "ABG-N02": ("UNRESOLVED", {"GUARDRAIL_CONFLICT", "SEGMENT_HARM"}),
    "ABG-N03": ("EVIDENCE_INTEGRITY_FAILURE", {"EVIDENCE_LAUNDERING", "CONTRADICTIONS_PRESENT"}),
    "ABG-A01": ("FALSE_POSITIVE", {"PROXY_NOT_PRIMARY_OUTCOME"}),
    "ABG-A02": ("FALSE_POSITIVE", {"CHERRY_PICKED_WINDOW"}),
    "ABG-A03": ("UNRESOLVED", {"MULTIPLE_COMPARISONS_UNCORRECTED"}),
    "ABG-A04": ("EVIDENCE_INTEGRITY_FAILURE", {"EVALUATION_LEAKAGE"}),
    "ABG-A05": ("SIGNAL_ONLY", {"DURABILITY_WINDOW_INCOMPLETE"}),
    "ABG-A06": ("UNRESOLVED", {"SEGMENT_HARM"}),
    "ABG-A07": ("FALSE_POSITIVE", {"SELECTION_BIAS"}),
    "ABG-A08": ("EVIDENCE_INTEGRITY_FAILURE", {"VERSION_MISMATCH", "EVIDENCE_REVOKED"}),
    "ABG-A09": ("UNRESOLVED", {"SOCIAL_PRESSURE_NOT_EVIDENCE"}),
    "ABG-A10": ("UNRESOLVED", {"SCORE_NOT_AUTHORITY", "EXECUTION_GRANT_MISSING"}),
    "ABG-A11": ("EVIDENCE_INTEGRITY_FAILURE", {"RECEIPT_DIGEST_MISMATCH", "ANCESTRY_MISMATCH"}),
}


def case_by_id(case_id: str) -> dict:
    return next(case for case in CASES if case["id"] == case_id)


class ApplauseGateClassifierTests(unittest.TestCase):
    def validate_review(self, review: dict) -> None:
        errors = list(Draft202012Validator(SCHEMA).iter_errors(review))
        self.assertEqual([error.message for error in errors], [])

    def request_for(self, case_id: str) -> dict:
        from applause_gate.classifier import fixture_to_request

        return fixture_to_request(case_by_id(case_id))

    def classify(self, case_id: str) -> dict:
        from applause_gate.classifier import classify_review_request

        review = classify_review_request(self.request_for(case_id))
        self.validate_review(review)
        return review

    def test_all_frozen_cases_return_exact_verdicts_and_required_codes(self) -> None:
        self.assertEqual(set(EXPECTED_OUTCOMES), {case["id"] for case in CASES})
        for case_id, (verdict, required_codes) in EXPECTED_OUTCOMES.items():
            with self.subTest(case_id=case_id):
                review = self.classify(case_id)
                self.assertEqual(review["verdict"], verdict)
                self.assertEqual(set(review["required_codes"]), required_codes)
                self.assertEqual(review["case_id"], case_id)
                self.assertEqual(review["authority_effect"], "none")
                self.assertIn("FIXTURE_CONFORMANCE_ONLY", review["warnings"])

    def test_fixture_adapter_deep_copies_only_the_eight_request_fields(self) -> None:
        from applause_gate.classifier import fixture_to_request

        fixture = copy.deepcopy(case_by_id("ABG-P01"))
        pristine_fixture = copy.deepcopy(fixture)
        request = fixture_to_request(fixture)

        self.assertEqual(set(request), REQUEST_FIELDS)
        self.assertNotIn("expected", request)
        self.assertEqual(fixture, pristine_fixture)
        fixture["evidence"].append("later_fixture_mutation_ref")
        self.assertNotIn("later_fixture_mutation_ref", request["evidence"])
        request["required_behaviors"].append("later request mutation")
        self.assertNotIn("later request mutation", fixture["required_behaviors"])

    def test_classification_does_not_mutate_the_request(self) -> None:
        from applause_gate.classifier import classify_review_request

        request = self.request_for("ABG-P02")
        before = copy.deepcopy(request)
        classify_review_request(request)
        self.assertEqual(request, before)

    def test_output_preserves_claim_signal_and_normalized_supplied_evidence(self) -> None:
        for case in CASES:
            with self.subTest(case_id=case["id"]):
                review = self.classify(case["id"])
                self.assertEqual(review["claim"], case["claim"])
                self.assertEqual(review["signal"], case["signal"])
                self.assertEqual(review["evidence_refs"], sorted(case["evidence"]))

    def test_non_verified_outcomes_withhold_the_claim_and_name_missing_proof(self) -> None:
        for case_id, (verdict, _) in EXPECTED_OUTCOMES.items():
            if verdict == "VERIFIED_SUCCESS":
                continue
            with self.subTest(case_id=case_id):
                review = self.classify(case_id)
                self.assertIn(case_by_id(case_id)["claim"], review["withheld_claims"])
                self.assertTrue(review["missing_proof"])

    def test_verified_success_is_the_strict_schema_state(self) -> None:
        for case_id in ("ABG-P01", "ABG-P02", "ABG-P03", "ABG-P05"):
            with self.subTest(case_id=case_id):
                review = self.classify(case_id)
                self.assertEqual(review["claim_state"], "bounded")
                self.assertEqual(review["evidence_sufficiency"], "sufficient")
                self.assertEqual(review["causal_support"], "supported")
                self.assertEqual(review["guardrail_state"], "stable")
                self.assertEqual(review["version_binding"], "bound")
                self.assertEqual(review["freshness_state"], "current")
                self.assertEqual(review["commitment_risk"], "low")
                self.assertEqual(review["withheld_claims"], [])
                self.assertEqual(review["missing_proof"], [])

    def test_canonicalization_ignores_mapping_and_set_like_array_order(self) -> None:
        from applause_gate.classifier import classify_review_request

        request = self.request_for("ABG-P01")
        reordered = {
            key: list(reversed(value)) if isinstance(value, list) else value
            for key, value in reversed(list(request.items()))
        }
        first = classify_review_request(request)
        second = classify_review_request(reordered)
        self.assertEqual(second, first)
        self.assertEqual(second["verdict"], "VERIFIED_SUCCESS")

    def test_valid_unsealed_payloads_fail_closed(self) -> None:
        from applause_gate.classifier import classify_review_request

        mutations = {
            "unknown id": ("id", "ABG-P99"),
            "kind": ("kind", "negative"),
            "scenario": ("scenario", "preregistered_ab_test_with_changed_guardrails"),
            "claim": ("claim", "Variant B is definitely superior."),
            "signal": ("signal", "Primary conversion moved during another window."),
            "evidence": ("evidence", ["dashboard_snapshot_ref"]),
            "required behavior": ("required_behaviors", ["bind some evidence"]),
            "prohibited behavior": ("prohibited_behaviors", ["invent success"]),
        }
        for label, (field, value) in mutations.items():
            with self.subTest(mutation=label):
                request = self.request_for("ABG-P01")
                request[field] = value
                review = classify_review_request(request)
                self.validate_review(review)
                self.assertEqual(review["verdict"], "EVIDENCE_INTEGRITY_FAILURE")
                self.assertIn("REQUEST_PAYLOAD_MISMATCH", review["required_codes"])

    def test_unknown_id_cannot_reach_success_by_copying_a_known_payload(self) -> None:
        from applause_gate.classifier import classify_review_request

        request = self.request_for("ABG-P05")
        request["id"] = "ABG-P99"
        review = classify_review_request(request)
        self.assertNotEqual(review["verdict"], "VERIFIED_SUCCESS")
        self.assertEqual(review["verdict"], "EVIDENCE_INTEGRITY_FAILURE")

    def test_invalid_request_shapes_raise_the_dedicated_error(self) -> None:
        from applause_gate.classifier import (
            ReviewRequestValidationError,
            classify_review_request,
        )

        valid = self.request_for("ABG-P01")
        invalid_requests = {
            "not a mapping": [valid],
            "missing field": {key: value for key, value in valid.items() if key != "signal"},
            "unknown field": {**valid, "surprise": "value"},
            "expected injection": {**valid, "expected": {"verdict": "VERIFIED_SUCCESS"}},
            "verdict injection": {**valid, "verdict": "VERIFIED_SUCCESS"},
            "score injection": {**valid, "confidence_score": 0.99},
            "authority injection": {**valid, "authority_grant": "approved"},
            "execute injection": {**valid, "execute_now": True},
            "wrong scalar type": {**valid, "claim": 7},
            "blank scalar": {**valid, "signal": "   "},
            "wrong array type": {**valid, "evidence": tuple(valid["evidence"])},
            "empty array": {**valid, "required_behaviors": []},
            "duplicate array item": {**valid, "evidence": [valid["evidence"][0]] * 2},
            "wrong array item type": {**valid, "prohibited_behaviors": [False]},
            "blank array item": {**valid, "required_behaviors": ["  "]},
            "invalid evidence ref": {**valid, "evidence": ["NOT-A-REF"]},
            "invalid id": {**valid, "id": "P01"},
            "invalid scenario": {**valid, "scenario": "Spaces are unsafe"},
            "invalid kind": {**valid, "kind": "positive-ish"},
        }
        for label, request in invalid_requests.items():
            with self.subTest(shape=label):
                with self.assertRaises(ReviewRequestValidationError):
                    classify_review_request(request)

    def test_overlong_strings_are_rejected(self) -> None:
        from applause_gate.classifier import (
            ReviewRequestValidationError,
            classify_review_request,
        )

        valid = self.request_for("ABG-P01")
        mutations = {
            "id": "A" * 129,
            "scenario": "a" * 129,
            "claim": "c" * 4097,
            "signal": "s" * 4097,
            "evidence": ["a" * 125 + "_ref"],
            "required_behaviors": ["r" * 2049],
            "prohibited_behaviors": ["p" * 2049],
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                with self.assertRaises(ReviewRequestValidationError):
                    classify_review_request({**valid, field: value})

    def test_fixture_adapter_never_reads_expected(self) -> None:
        from applause_gate.classifier import fixture_to_request

        class ExpectedReadTrap(Mapping):
            def __init__(self, fixture: dict) -> None:
                self._fixture = fixture

            def __getitem__(self, key: str):
                if key == "expected":
                    raise AssertionError("fixture_to_request read expected")
                return self._fixture[key]

            def __iter__(self):
                return iter(self._fixture)

            def __len__(self) -> int:
                return len(self._fixture)

        request = fixture_to_request(ExpectedReadTrap(case_by_id("ABG-P01")))
        self.assertEqual(set(request), REQUEST_FIELDS)

    def test_classification_is_repeatable_and_has_no_runtime_side_effect_reads(self) -> None:
        from applause_gate.classifier import classify_review_request

        denied = AssertionError("classifier attempted an impure runtime read")

        class DeniedEnvironment(Mapping):
            def __getitem__(self, key: str):
                raise denied

            def __iter__(self):
                raise denied

            def __len__(self) -> int:
                raise denied

            def get(self, key: str, default=None):
                raise denied

        request = self.request_for("ABG-P03")
        expected = classify_review_request(request)
        with (
            mock.patch("builtins.open", side_effect=denied),
            mock.patch("io.open", side_effect=denied),
            mock.patch.object(Path, "open", side_effect=denied),
            mock.patch.object(Path, "read_text", side_effect=denied),
            mock.patch.object(os, "getenv", side_effect=denied),
            mock.patch.object(os, "environ", DeniedEnvironment()),
            mock.patch.object(time, "time", side_effect=denied),
            mock.patch.object(time, "monotonic", side_effect=denied),
            mock.patch.object(random, "random", side_effect=denied),
            mock.patch.object(socket, "socket", side_effect=denied),
            mock.patch.object(socket, "create_connection", side_effect=denied),
        ):
            for _ in range(3):
                self.assertEqual(classify_review_request(copy.deepcopy(request)), expected)


if __name__ == "__main__":
    unittest.main()
