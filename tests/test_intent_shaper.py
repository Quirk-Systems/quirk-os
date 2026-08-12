from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft202012Validator

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from intent_shaper.policy import evaluate_cases  # noqa: E402


class IntentShaperContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads((REPO / "schemas/personalization-plan.schema.json").read_text())
        cls.sample = json.loads((REPO / "examples/personalization-plan.valid.json").read_text())
        cls.suite = json.loads((REPO / "evals/intent-shaper/cases.json").read_text())
        cls.validator = Draft202012Validator(cls.schema)

    def test_schema_is_valid_draft_2020_12(self) -> None:
        Draft202012Validator.check_schema(self.schema)

    def test_representative_plan_is_valid(self) -> None:
        self.assertEqual([], list(self.validator.iter_errors(self.sample)))

    def test_approved_plan_requires_approval_ref(self) -> None:
        plan = copy.deepcopy(self.sample)
        plan["status"] = "approved"
        errors = list(self.validator.iter_errors(plan))
        self.assertTrue(any("approval_ref" in error.message for error in errors))

    def test_learning_cannot_auto_apply(self) -> None:
        plan = copy.deepcopy(self.sample)
        plan["learning"]["auto_apply"] = True
        errors = list(self.validator.iter_errors(plan))
        self.assertTrue(any("False was expected" in error.message for error in errors))

    def test_all_eleven_policy_cases_pass(self) -> None:
        results = evaluate_cases(self.suite["cases"])
        failures = [result for result in results if not result["passed"]]
        self.assertEqual([], failures)
        self.assertEqual(11, len(results))

    def test_personalization_off_has_no_saved_retrieval(self) -> None:
        results = {result["id"]: result for result in evaluate_cases(self.suite["cases"])}
        actual = results["QIS-010"]["actual"]
        self.assertFalse(actual["stored_retrieval"])
        self.assertFalse(actual["saved_profile_loaded"])
        self.assertEqual([], actual["persona_hand"])

    def test_adaptation_never_self_promotes(self) -> None:
        results = {result["id"]: result for result in evaluate_cases(self.suite["cases"])}
        actual = results["QIS-011"]["actual"]
        self.assertFalse(actual["auto_apply"])
        self.assertFalse(actual["memory_updated"])
        self.assertFalse(actual["settings_updated"])
        self.assertFalse(actual["canon_updated"])
        self.assertTrue(actual["human_admission_required"])


if __name__ == "__main__":
    unittest.main()
