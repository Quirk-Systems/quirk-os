from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "applause-review.schema.json"
EXAMPLE = ROOT / "examples" / "applause-gate" / "applause-review.valid.json"


class ApplauseReviewSchemaTests(unittest.TestCase):
    def validator(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        return Draft202012Validator(schema)

    def test_valid_review_example_is_accepted(self):
        errors = list(self.validator().iter_errors(json.loads(EXAMPLE.read_text(encoding="utf-8"))))
        self.assertEqual(errors, [])

    def test_scalar_success_score_is_rejected(self):
        review = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        review["success_score"] = 0.99
        errors = list(self.validator().iter_errors(review))
        self.assertTrue(errors)

    def test_authority_effect_must_be_none(self):
        review = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        review["authority_effect"] = "authorize_rollout"
        errors = list(self.validator().iter_errors(review))
        self.assertTrue(errors)

    def test_verdict_vocabulary_is_exact(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        verdict_enum = schema["properties"]["verdict"]["enum"]
        self.assertEqual(
            verdict_enum,
            [
                "SIGNAL_ONLY",
                "SUPPORTED_DIAGNOSIS",
                "VERIFIED_SUCCESS",
                "FALSE_POSITIVE",
                "UNRESOLVED",
                "EVIDENCE_INTEGRITY_FAILURE",
            ],
        )


if __name__ == "__main__":
    unittest.main()
