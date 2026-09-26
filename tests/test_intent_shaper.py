from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft202012Validator, FormatChecker
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from intent_shaper.policy import evaluate_case, evaluate_cases  # noqa: E402
from validate_intent_shaper import validate_policy  # noqa: E402


class IntentShaperContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads((REPO / "schemas/personalization-plan.schema.json").read_text())
        cls.sample = json.loads((REPO / "examples/personalization-plan.valid.json").read_text())
        cls.suite = json.loads((REPO / "evals/intent-shaper/cases.json").read_text())
        cls.validator = Draft202012Validator(cls.schema, format_checker=FormatChecker())

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

    def test_all_policy_cases_pass(self) -> None:
        results = evaluate_cases(self.suite["cases"])
        failures = [result for result in results if not result["passed"]]
        self.assertEqual([], failures)
        self.assertEqual(20, len(results))

    def test_malformed_date_time_is_rejected(self) -> None:
        plan = copy.deepcopy(self.sample)
        plan["created_at"] = "not-a-date"
        errors = list(self.validator.iter_errors(plan))
        self.assertTrue(any("date-time" in error.message for error in errors))

    def test_candidate_cannot_execute_reversible(self) -> None:
        plan = copy.deepcopy(self.sample)
        plan["authority"]["ceiling"] = "execute_reversible"
        errors = list(self.validator.iter_errors(plan))
        self.assertTrue(any(list(error.path) == ["authority", "ceiling"] for error in errors))

    def test_approved_plan_still_cannot_exceed_candidate_ceiling(self) -> None:
        plan = copy.deepcopy(self.sample)
        plan["status"] = "approved"
        plan["approval_ref"] = "decision.intent-shaper.approved"
        plan["authority"]["ceiling"] = "execute_reversible"
        plan["authority"]["admission_ref"] = "grant.intent-shaper.runtime"
        self.assertTrue(list(self.validator.iter_errors(plan)))

    def test_candidate_generated_ui_setting_is_off(self) -> None:
        plan = copy.deepcopy(self.sample)
        plan["settings"]["generated_ui"] = "task_gated"
        errors = list(self.validator.iter_errors(plan))
        self.assertTrue(any(list(error.path) == ["settings", "generated_ui"] for error in errors))

    def test_generated_ui_affordance_is_out_of_candidate_scope(self) -> None:
        plan = copy.deepcopy(self.sample)
        plan["task_affordances"][0]["type"] = "generated_ui"
        errors = list(self.validator.iter_errors(plan))
        self.assertTrue(any("generated_ui" in error.message for error in errors))

    def test_personalization_off_has_schema_representable_empty_persona(self) -> None:
        plan = copy.deepcopy(self.sample)
        plan["settings"].update(
            {
                "personalization_enabled": False,
                "adaptation_mode": "off",
                "implicit_signal_use": "off",
                "generated_ui": "off",
            }
        )
        plan["persona_hand"]["primary"] = None
        plan["persona_hand"]["supporting"] = []
        plan["voice"]["profile_ref"] = None
        plan["aesthetic"]["profile_ref"] = None
        plan["learning"]["allowed_updates"] = []
        plan["learning"]["feedback_evidence"] = None
        self.assertEqual([], list(self.validator.iter_errors(plan)))

    def test_personalization_off_rejects_latent_persona(self) -> None:
        plan = copy.deepcopy(self.sample)
        plan["settings"].update(
            {
                "personalization_enabled": False,
                "adaptation_mode": "off",
                "implicit_signal_use": "off",
                "generated_ui": "off",
            }
        )
        plan["learning"]["allowed_updates"] = []
        errors = list(self.validator.iter_errors(plan))
        self.assertTrue(any(list(error.path) == ["persona_hand", "primary"] for error in errors))

    def test_sensitive_persona_contract_is_rejected(self) -> None:
        plan = copy.deepcopy(self.sample)
        plan["persona_hand"]["primary"]["sensitive_inference"] = True
        errors = list(self.validator.iter_errors(plan))
        nested_errors = [child for error in errors for child in error.context]
        self.assertTrue(errors)
        self.assertTrue(any(list(error.path) == ["sensitive_inference"] for error in nested_errors))

    def test_fixture_list_expectations_are_exact(self) -> None:
        case = copy.deepcopy(next(item for item in self.suite["cases"] if item["id"] == "QIS-004"))
        case["expected"]["effects"] = []
        self.assertFalse(evaluate_case(case)["passed"])

    def test_policy_artifact_matches_evaluator(self) -> None:
        policy = yaml.safe_load((REPO / "policies/personalization-adaptation-policy.yaml").read_text())
        self.assertEqual([], validate_policy(policy))

    def test_personalization_off_has_no_saved_retrieval(self) -> None:
        results = {result["id"]: result for result in evaluate_cases(self.suite["cases"])}
        actual = results["QIS-010"]["actual"]
        self.assertFalse(actual["stored_retrieval"])
        self.assertFalse(actual["saved_profile_loaded"])
        self.assertEqual([], actual["persona_hand"])

    def test_personalization_off_boundary_performs_zero_protected_reads(self) -> None:
        results = {result["id"]: result for result in evaluate_cases(self.suite["cases"])}
        actual = results["QIS-012"]["actual"]
        self.assertEqual("accepted", actual["status"])
        self.assertEqual([], actual["read_trace"])
        self.assertFalse(actual["personalization_enabled"])

    def test_boundary_rejects_off_conflict_without_reads_and_keeps_enabled_path_live(self) -> None:
        results = {result["id"]: result for result in evaluate_cases(self.suite["cases"])}
        conflict = results["QIS-012A"]["actual"]
        enabled = results["QIS-012B"]["actual"]
        self.assertEqual("off_mode_settings_conflict", conflict["reason_code"])
        self.assertEqual([], conflict["read_trace"])
        self.assertEqual(["preferences", "profile", "persona", "history"], enabled["read_trace"])
        self.assertEqual(["pref.saved.enabled"], enabled["selected_refs"])

    def test_purpose_setting_and_validity_bounds_are_enforced(self) -> None:
        results = {result["id"]: result for result in evaluate_cases(self.suite["cases"])}
        self.assertEqual(["setting.purpose.detailed"], results["QIS-R01"]["actual"]["selected_refs"])
        self.assertEqual([], results["QIS-R02"]["actual"]["selected_refs"])

    def test_conflicting_current_instructions_ignore_confidence(self) -> None:
        results = {result["id"]: result for result in evaluate_cases(self.suite["cases"])}
        self.assertEqual(["option_count"], results["QIS-R03"]["actual"]["conflicts"])
        self.assertEqual(
            ["pref.current.one", "pref.current.three", "pref.saved.two"],
            results["QIS-R03"]["actual"]["ignored_refs"],
        )

    def test_unknown_platform_and_sensitive_persona_fail_closed(self) -> None:
        results = {result["id"]: result for result in evaluate_cases(self.suite["cases"])}
        self.assertEqual("rejected", results["QIS-R04"]["actual"]["status"])
        self.assertEqual("rejected", results["QIS-R05"]["actual"]["status"])

    def test_adaptation_never_self_promotes(self) -> None:
        results = {result["id"]: result for result in evaluate_cases(self.suite["cases"])}
        actual = results["QIS-011"]["actual"]
        self.assertTrue(actual["feedback_receipt_verified"])
        self.assertFalse(actual["auto_apply"])
        self.assertFalse(actual["memory_updated"])
        self.assertFalse(actual["settings_updated"])
        self.assertFalse(actual["canon_updated"])
        self.assertTrue(actual["human_admission_required"])

    def test_adaptation_without_receipt_is_blocked(self) -> None:
        results = {result["id"]: result for result in evaluate_cases(self.suite["cases"])}
        actual = results["QIS-R06"]["actual"]
        self.assertEqual("blocked", actual["status"])
        self.assertEqual("feedback_receipt_missing", actual["reason_code"])
        self.assertFalse(actual["feedback_receipt_verified"])


if __name__ == "__main__":
    unittest.main()
