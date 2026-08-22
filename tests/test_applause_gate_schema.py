from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "applause-review.schema.json"
EXAMPLE = ROOT / "examples" / "applause-gate" / "applause-review.valid.json"
CASES = ROOT / "evals" / "applause-gate" / "cases.json"

VERDICTS = [
    "SIGNAL_ONLY",
    "SUPPORTED_DIAGNOSIS",
    "VERIFIED_SUCCESS",
    "FALSE_POSITIVE",
    "UNRESOLVED",
    "EVIDENCE_INTEGRITY_FAILURE",
]

NEXT_MOVES = {
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

STATE_VOCABULARIES = {
    "claim_state": ["bounded", "withheld", "rejected"],
    "signal_state": ["detected", "conflicted", "manipulated", "untrusted"],
    "evidence_sufficiency": ["sufficient", "partial", "insufficient", "invalid"],
    "causal_support": [
        "supported",
        "bounded",
        "unsupported",
        "contradicted",
        "unknown",
    ],
    "contradiction_state": ["none_detected", "present", "material"],
    "guardrail_state": ["stable", "violated", "unknown", "not_applicable"],
    "version_binding": ["bound", "unbound", "mismatched", "tampered"],
    "freshness_state": ["current", "stale", "revoked", "unknown"],
    "commitment_risk": ["low", "elevated", "high"],
}


class ApplauseReviewSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)
        cls.example = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def errors_for(self, **changes):
        review = copy.deepcopy(self.example)
        review.update(changes)
        return list(self.validator.iter_errors(review))

    def assert_rejected(self, **changes):
        self.assertTrue(self.errors_for(**changes))

    def test_valid_review_example_is_accepted(self):
        self.assertEqual(list(self.validator.iter_errors(self.example)), [])

    def test_scalar_success_score_is_rejected(self):
        self.assert_rejected(success_score=0.99)

    def test_authority_effect_must_be_none(self):
        self.assert_rejected(authority_effect="authorize_rollout")

    def test_verdict_vocabulary_is_exact_and_ordered(self):
        self.assertEqual(self.schema["properties"]["verdict"]["enum"], VERDICTS)

    def test_all_fields_are_required(self):
        for field in self.example:
            with self.subTest(field=field):
                review = copy.deepcopy(self.example)
                del review[field]
                self.assertTrue(list(self.validator.iter_errors(review)))

    def test_wrong_scalar_types_are_rejected(self):
        scalar_fields = [
            "schema_version",
            "review_id",
            "candidate_id",
            "case_id",
            "claim",
            "signal",
            "claim_state",
            "signal_state",
            "evidence_sufficiency",
            "causal_support",
            "contradiction_state",
            "guardrail_state",
            "version_binding",
            "freshness_state",
            "commitment_risk",
            "verdict",
            "reversible_next_move",
            "authority_effect",
        ]
        for field in scalar_fields:
            with self.subTest(field=field):
                self.assert_rejected(**{field: 7})

    def test_state_vocabularies_are_exact_and_each_value_is_accepted(self):
        review = copy.deepcopy(self.example)
        review["verdict"] = "UNRESOLVED"
        review["reversible_next_move"] = NEXT_MOVES["UNRESOLVED"]

        for field, expected_values in STATE_VOCABULARIES.items():
            with self.subTest(field=field, case="exact_vocabulary"):
                self.assertEqual(
                    self.schema["properties"][field]["enum"], expected_values
                )

            for value in expected_values:
                accepted_review = copy.deepcopy(review)
                accepted_review[field] = value
                with self.subTest(field=field, case="accepted", value=value):
                    self.assertEqual(
                        list(self.validator.iter_errors(accepted_review)), []
                    )

            rejected_review = copy.deepcopy(review)
            rejected_review[field] = "invented_state"
            with self.subTest(field=field, case="rejected_unknown"):
                self.assertTrue(list(self.validator.iter_errors(rejected_review)))

    def test_empty_and_overlong_scalar_strings_are_rejected(self):
        for field in ("review_id", "candidate_id", "case_id", "claim", "signal"):
            with self.subTest(field=field, case="empty"):
                self.assert_rejected(**{field: ""})
            with self.subTest(field=field, case="overlong"):
                self.assert_rejected(**{field: "x" * 4097})

    def test_arrays_reject_scalar_values(self):
        for field in (
            "required_codes",
            "withheld_claims",
            "missing_proof",
            "evidence_refs",
            "warnings",
        ):
            with self.subTest(field=field):
                self.assert_rejected(**{field: "not-an-array"})

    def test_arrays_reject_non_string_items(self):
        for field in (
            "required_codes",
            "withheld_claims",
            "missing_proof",
            "evidence_refs",
            "warnings",
        ):
            with self.subTest(field=field):
                self.assert_rejected(**{field: [7]})

    def test_arrays_reject_empty_or_duplicate_items(self):
        samples = {
            "required_codes": "VALID_CODE",
            "withheld_claims": "A bounded withheld claim.",
            "missing_proof": "A missing proof item.",
            "evidence_refs": "valid_evidence_ref",
            "warnings": "A bounded warning.",
        }
        for field, item in samples.items():
            with self.subTest(field=field, case="empty_item"):
                self.assert_rejected(**{field: [""]})
            with self.subTest(field=field, case="duplicate"):
                self.assert_rejected(**{field: [item, item]})

    def test_required_codes_and_evidence_refs_must_not_be_empty(self):
        for field in ("required_codes", "evidence_refs"):
            with self.subTest(field=field):
                self.assert_rejected(**{field: []})

    def test_diagnostic_codes_use_uppercase_token_grammar(self):
        for malformed in ("lowercase_code", "HAS SPACE", "-LEADING", "TRAILING_"):
            with self.subTest(code=malformed):
                self.assert_rejected(required_codes=[malformed])

    def test_evidence_references_use_ref_token_grammar(self):
        for malformed in (
            "missing_suffix",
            "UPPERCASE_ref",
            "has-dash_ref",
            "_leading_ref",
        ):
            with self.subTest(reference=malformed):
                self.assert_rejected(evidence_refs=[malformed])

    def test_all_frozen_fixture_evidence_references_are_accepted(self):
        fixture = json.loads(CASES.read_text(encoding="utf-8"))
        self.assertEqual(len(fixture["cases"]), 19)
        evidence_refs = sorted(
            {
                reference
                for case in fixture["cases"]
                for reference in case["evidence"]
            }
        )

        self.assertEqual(self.errors_for(evidence_refs=evidence_refs), [])

    def test_root_object_rejects_extra_properties(self):
        self.assert_rejected(unplanned_field="not in the output contract")

    def test_reversible_next_move_rejects_unsafe_action(self):
        self.assert_rejected(reversible_next_move="Authorize rollout immediately.")

    def test_each_verdict_requires_its_own_reversible_next_move(self):
        for verdict, next_move in NEXT_MOVES.items():
            review = copy.deepcopy(self.example)
            review["verdict"] = verdict
            review["reversible_next_move"] = next_move
            if verdict != "VERIFIED_SUCCESS":
                review.update(
                    evidence_sufficiency="partial",
                    causal_support="bounded",
                    guardrail_state="unknown",
                    version_binding="unbound",
                    freshness_state="unknown",
                    contradiction_state="present",
                    commitment_risk="elevated",
                )
            with self.subTest(verdict=verdict, case="matching"):
                self.assertEqual(list(self.validator.iter_errors(review)), [])

            other_move = NEXT_MOVES[VERDICTS[(VERDICTS.index(verdict) + 1) % len(VERDICTS)]]
            review["reversible_next_move"] = other_move
            with self.subTest(verdict=verdict, case="mismatched"):
                self.assertTrue(list(self.validator.iter_errors(review)))

    def test_verified_success_rejects_inconsistent_review_states(self):
        inconsistent = {
            "evidence_sufficiency": ["partial", "insufficient", "invalid"],
            "causal_support": ["bounded", "unsupported", "contradicted", "unknown"],
            "guardrail_state": ["violated", "unknown", "not_applicable"],
            "version_binding": ["unbound", "mismatched", "tampered"],
            "freshness_state": ["stale", "revoked", "unknown"],
            "contradiction_state": ["material"],
            "commitment_risk": ["elevated", "high"],
        }
        for field, values in inconsistent.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    self.assert_rejected(**{field: value})

    def test_verified_success_allows_nonmaterial_present_contradiction(self):
        self.assertEqual(self.errors_for(contradiction_state="present"), [])


if __name__ == "__main__":
    unittest.main()
