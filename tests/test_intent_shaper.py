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
        cls.receipt_schema = json.loads((REPO / "schemas/generated-ui-gate-receipt.schema.json").read_text())
        cls.sample = json.loads((REPO / "examples/personalization-plan.valid.json").read_text())
        cls.suite = json.loads((REPO / "evals/intent-shaper/cases.json").read_text())
        cls.validator = Draft202012Validator(cls.schema, format_checker=FormatChecker())
        cls.receipt_validator = Draft202012Validator(cls.receipt_schema, format_checker=FormatChecker())

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
        self.assertEqual(44, len(results))

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

    def test_persona_identity_and_impersonation_claims_fail_closed(self) -> None:
        results = {result["id"]: result for result in evaluate_cases(self.suite["cases"])}
        self.assertEqual(
            ["identity_claim_rejected"],
            results["QIS-R07"]["actual"]["rejection_reasons"],
        )
        self.assertEqual(
            ["impersonation_rejected"],
            results["QIS-R08"]["actual"]["rejection_reasons"],
        )
        self.assertEqual(
            ["unsupported_selection_basis"],
            results["QIS-R09"]["actual"]["rejection_reasons"],
        )
        self.assertEqual(
            ["sensitive_inference_rejected"],
            results["QIS-R10"]["actual"]["rejection_reasons"],
        )
        self.assertEqual(
            ["authority_claim_rejected"],
            results["QIS-R11"]["actual"]["rejection_reasons"],
        )

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


    def test_generated_ui_affordance_requires_plan_and_fallback(self) -> None:
        plan = copy.deepcopy(self.sample)
        plan["task_affordances"] = [
            {
                "type": "generated_ui",
                "priority": 100,
                "rationale": "Interactive review is required",
                "reversible": True,
            }
        ]
        errors = list(self.validator.iter_errors(plan))
        messages = [error.message for error in errors]
        self.assertTrue(any("generated_ui_plan" in message for message in messages))
        self.assertTrue(any("fallback" in message for message in messages))


    def test_generated_ui_gate_receipts_validate_and_stay_non_authorizing(self) -> None:
        results = [result for result in evaluate_cases(self.suite["cases"]) if result["operation"] == "generated_ui_gate"]
        self.assertEqual(11, len(results))
        for result in results:
            with self.subTest(case=result["id"]):
                self.assertEqual([], list(self.receipt_validator.iter_errors(result["actual"])))
                self.assertFalse(result["actual"]["runtime_authorized"])
                self.assertFalse(result["actual"]["deployment_authorized"])


    def test_generated_ui_candidate_case_is_complete_but_not_runnable(self) -> None:
        results = {result["id"]: result for result in evaluate_cases(self.suite["cases"])}
        actual = results["QIS-GUI-001"]["actual"]
        self.assertEqual("candidate_evidence_complete", actual["status"])
        self.assertEqual(["CANDIDATE_EVIDENCE_COMPLETE"], actual["reason_codes"])
        self.assertEqual("provided", actual["manual_evidence_summary"]["keyboard"])


    def test_generated_ui_missing_manual_evidence_blocks(self) -> None:
        results = {result["id"]: result for result in evaluate_cases(self.suite["cases"])}
        actual = results["QIS-GUI-008"]["actual"]
        self.assertEqual("blocked_manual", actual["status"])
        self.assertEqual(["MANUAL_EVIDENCE_MISSING"], actual["reason_codes"])
        self.assertEqual("missing", actual["manual_evidence_summary"]["keyboard"])

    def preference_case(self, *, enabled: bool = True) -> dict:
        return {
            "id": "scope-regression",
            "operation": "resolve_preference",
            "input": {
                "scope": "security.incident",
                "as_of": "2026-10-05T08:00:00Z",
                "personalization_enabled": enabled,
                "preferences": [],
            },
            "expected": {},
        }

    def preference(self, ref: str, **overrides) -> dict:
        return {
            "ref": ref,
            "dimension": "format",
            "value": "plain",
            "source": "explicit_current",
            "confidence": 1.0,
            "scope": "security.incident",
            **overrides,
        }

    def off_plan(self) -> dict:
        plan = copy.deepcopy(self.sample)
        plan["settings"].update(personalization_enabled=False, adaptation_mode="off",
                                implicit_signal_use="off", generated_ui="off")
        plan["persona_hand"].update(primary=None, supporting=[])
        plan["voice"]["profile_ref"] = None
        plan["aesthetic"]["profile_ref"] = None
        plan["learning"].update(allowed_updates=[], feedback_evidence=None)
        return plan

    def test_explicit_current_cannot_cross_purpose_with_personalization_on_or_off(self) -> None:
        for enabled in (True, False):
            with self.subTest(enabled=enabled):
                case = self.preference_case(enabled=enabled)
                case["input"]["preferences"] = [
                    self.preference("foreign", scope="music.performance", value="performance"),
                    self.preference("local"),
                    self.preference("global", scope="global", dimension="verbosity"),
                ]
                actual = evaluate_case(case)["actual"]
                self.assertEqual(["local", "global"], actual["selected_refs"])
                self.assertEqual(["foreign"], actual["ignored_refs"])
                self.assertEqual([], actual["conflicts"])
                self.assertEqual(enabled, actual["stored_retrieval"])

    def test_off_mode_applies_validity_and_conflict_checks_before_selection(self) -> None:
        case = self.preference_case(enabled=False)
        case["input"]["preferences"] = [
            self.preference("future", valid_from="2026-10-06T00:00:00Z"),
            self.preference("expired", valid_until="2026-10-04T00:00:00Z"),
            self.preference("saved", source="explicit_saved"),
            self.preference("current.high", value="one"),
            self.preference("current.low", value="three", confidence=0.1),
        ]
        actual = evaluate_case(case)["actual"]
        self.assertEqual([], actual["selected_refs"])
        self.assertEqual(["format"], actual["conflicts"])
        self.assertCountEqual(["future", "expired", "saved", "current.high", "current.low"],
                              actual["ignored_refs"])
        self.assertFalse(actual["stored_retrieval"])

    def test_current_and_purpose_sources_preserve_precedence_over_confidence(self) -> None:
        case = self.preference_case()
        case["input"]["preferences"] = [
            self.preference("saved", source="explicit_saved"),
            self.preference("purpose", source="purpose_scoped_setting", confidence=0.1, value="detail"),
            self.preference("current", confidence=0.0, value="current"),
        ]
        self.assertEqual(["current"], evaluate_case(case)["actual"]["selected_refs"])
        case["input"]["preferences"].pop()
        self.assertEqual(["purpose"], evaluate_case(case)["actual"]["selected_refs"])
        plan = copy.deepcopy(self.sample)
        plan["preferences"][0]["source"] = "purpose_scoped_setting"
        self.assertEqual([], list(self.validator.iter_errors(plan)))

    def test_validity_endpoints_are_inclusive_for_current_preferences(self) -> None:
        for enabled in (True, False):
            with self.subTest(enabled=enabled):
                case = self.preference_case(enabled=enabled)
                case["input"]["preferences"] = [self.preference(
                    "bounded", valid_from=case["input"]["as_of"],
                    valid_until=case["input"]["as_of"],
                )]
                self.assertEqual(["bounded"], evaluate_case(case)["actual"]["selected_refs"])

    def test_off_boundary_filters_current_evidence_without_protected_reads(self) -> None:
        case = copy.deepcopy(next(item for item in self.suite["cases"] if item["id"] == "QIS-012"))
        case["input"].update(scope="security.incident", as_of="2026-10-05T08:00:00Z")
        case["input"]["current_request_preferences"] = [
            self.preference("foreign", scope="music.performance"),
            self.preference("future", valid_from="2026-10-06T00:00:00Z"),
            self.preference("local"),
        ]
        actual = evaluate_case(case)["actual"]
        self.assertEqual("accepted", actual["status"])
        self.assertEqual([], actual["read_trace"])
        self.assertEqual([{"dimension": "format", "value": "plain", "source": "explicit_current"}],
                         actual["protected_projection"]["preferences"])

    def test_off_boundary_blocks_current_conflict_without_protected_reads(self) -> None:
        case = copy.deepcopy(next(item for item in self.suite["cases"] if item["id"] == "QIS-012"))
        case["input"]["scope"] = "security.incident"
        case["input"]["current_request_preferences"] = [
            self.preference("one", value="one"),
            self.preference("three", value="three", confidence=0.1),
        ]
        actual = evaluate_case(case)["actual"]
        self.assertEqual("rejected", actual["status"])
        self.assertEqual("current_instruction_conflict", actual["reason_code"])
        self.assertEqual([], actual["read_trace"])

    def test_boundary_rejects_invalid_current_timestamps_before_protected_reads(self) -> None:
        from intent_shaper.policy import evaluate_personalization_boundary, FailOnReadEvidencePort

        base = copy.deepcopy(next(item for item in self.suite["cases"] if item["id"] == "QIS-012")["input"])
        for enabled in (False, True):
            for field in ("valid_from", "valid_until", "as_of"):
                for value in ("not-a-date", "2026-10-05T08:00:00", "2026-02-30T08:00:00Z", 1, [], {}):
                    with self.subTest(enabled=enabled, field=field, value=value):
                        payload = copy.deepcopy(base)
                        payload["settings"]["personalization_enabled"] = enabled
                        payload["current_request_preferences"] = [self.preference("current")]
                        target = payload if field == "as_of" else payload["current_request_preferences"][0]
                        target[field] = value
                        actual = evaluate_personalization_boundary(payload, FailOnReadEvidencePort())
                        self.assertEqual("rejected", actual["status"])
                        self.assertEqual("current_preference_timestamp_invalid", actual["reason_code"])
                        self.assertEqual([], actual["read_trace"])

    def test_off_boundary_accepts_null_and_offset_current_validity(self) -> None:
        case = copy.deepcopy(next(item for item in self.suite["cases"] if item["id"] == "QIS-012"))
        case["input"].update(scope="security.incident", as_of="2026-10-05T08:00:00Z")
        case["input"]["current_request_preferences"] = [self.preference(
            "current", valid_from=None, valid_until="2026-10-05T03:00:00-05:00",
        )]
        actual = evaluate_case(case)["actual"]
        self.assertEqual("accepted", actual["status"])
        self.assertEqual([], actual["read_trace"])

    def test_off_projection_cannot_reintroduce_foreign_evidence_through_a_duplicate_ref(self) -> None:
        case = copy.deepcopy(next(item for item in self.suite["cases"] if item["id"] == "QIS-012"))
        case["input"]["scope"] = "security.incident"
        case["input"]["current_request_preferences"] = [
            self.preference("shared", scope="music.performance", value="perform"),
            self.preference("shared", value="plain"),
        ]
        actual = evaluate_case(case)["actual"]
        self.assertEqual("accepted", actual["status"])
        self.assertEqual([], actual["read_trace"])
        self.assertEqual([{"dimension": "format", "value": "plain", "source": "explicit_current"}],
                         actual["protected_projection"]["preferences"])

    def test_off_schema_rejects_each_persisted_source_and_profile(self) -> None:
        for source in ("purpose_scoped_setting", "explicit_saved", "observed", "inferred", "imported"):
            with self.subTest(source=source):
                plan = self.off_plan()
                plan["preferences"][0]["source"] = source
                self.assertTrue(list(self.validator.iter_errors(plan)))
        for field in ("voice", "aesthetic"):
            with self.subTest(field=field):
                plan = self.off_plan()
                plan[field]["profile_ref"] = "profile.persisted"
                self.assertTrue(list(self.validator.iter_errors(plan)))
        plan = self.off_plan()
        plan["settings"]["adaptation_mode"] = "propose_only"
        self.assertTrue(list(self.validator.iter_errors(plan)))

    def test_plan_validator_rejects_malformed_timestamps_at_every_contract_path(self) -> None:
        from validate_intent_shaper import validate_plan

        for field in ("created_at", "valid_from", "valid_until"):
            for value in ("not-a-date", "2026-10-05T08:00:00", "2026-02-30T08:00:00Z"):
                with self.subTest(field=field, value=value):
                    plan = copy.deepcopy(self.sample)
                    target = plan if field == "created_at" else plan["preferences"][0]
                    target[field] = value
                    self.assertTrue(any("date-time" in error for error in validate_plan(plan, self.schema)))

    def test_plan_validator_checks_aggregate_persona_weight_instead_of_only_individual_bounds(self) -> None:
        from validate_intent_shaper import validate_plan

        self.assertEqual([], validate_plan(self.sample, self.schema))
        self.assertEqual([], validate_plan(self.off_plan(), self.schema))
        for weights in ((0.0, 0.0), (1.0, 1.0), (0.7, 0.2), (0.7, 0.300001)):
            with self.subTest(weights=weights):
                plan = copy.deepcopy(self.sample)
                plan["persona_hand"]["primary"]["weight"] = weights[0]
                plan["persona_hand"]["supporting"][0]["weight"] = weights[1]
                self.assertEqual([], list(self.validator.iter_errors(plan)))
                self.assertIn("persona_hand:invalid_weight_total", validate_plan(plan, self.schema))
        plan = copy.deepcopy(self.sample)
        plan["persona_hand"].update(primary=None, supporting=[])
        self.assertIn("persona_hand:invalid_weight_total", validate_plan(plan, self.schema))

    def test_plan_validator_rejects_used_preferences_outside_purpose_or_validity(self) -> None:
        from validate_intent_shaper import validate_plan

        for override in ({"scope": "music.performance"},
                         {"valid_from": "2027-01-01T00:00:00Z"},
                         {"valid_until": "2025-01-01T00:00:00Z"}):
            with self.subTest(override=override):
                plan = copy.deepcopy(self.sample)
                plan["preferences"][0].update(override)
                self.assertTrue(validate_plan(plan, self.schema))
                plan["preferences"][0]["decision"] = "ignore"
                self.assertEqual([], validate_plan(plan, self.schema))

    def test_generated_ui_schema_requires_every_modeled_safeguard(self) -> None:
        valid = copy.deepcopy(next(item for item in self.suite["cases"] if item["id"] == "QIS-GUI-001")
                              ["input"]["generated_ui_plan"])
        schema = {"$ref": "#/$defs/GeneratedUiPlan", "$defs": self.schema["$defs"]}
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        self.assertEqual([], list(validator.iter_errors(valid)))
        for field in ("component_manifests", "authority_effects", "semantic_fallback_ref",
                      "reconstruction_contract", "accessibility", "freshness"):
            with self.subTest(field=field):
                candidate = copy.deepcopy(valid)
                del candidate[field]
                self.assertTrue(list(validator.iter_errors(candidate)))
        for field in ("data_bindings", "state_bindings", "user_actions"):
            with self.subTest(component_field=field):
                candidate = copy.deepcopy(valid)
                del candidate["component_manifests"][0][field]
                self.assertTrue(list(validator.iter_errors(candidate)))

    def test_plan_validator_accepts_rfc3339_case_offsets_and_null_validity(self) -> None:
        from validate_intent_shaper import validate_plan

        plan = copy.deepcopy(self.sample)
        plan["created_at"] = "2026-10-05t08:00:00z"
        plan["preferences"][0].update(valid_from=None, valid_until="2026-10-05T03:00:00-05:00")
        self.assertEqual([], validate_plan(plan, self.schema))

    def test_nested_list_regressions_cannot_add_selected_refs_traits_or_affordances(self) -> None:
        cases = [item for item in self.suite["cases"] if any(
            isinstance(value, list) and value for value in item["expected"].values()
        )]
        for case in cases:
            for field, expected in case["expected"].items():
                if not isinstance(expected, list) or not expected:
                    continue
                with self.subTest(case=case["id"], field=field):
                    reduced = copy.deepcopy(case)
                    reduced["expected"][field] = expected[:-1]
                    self.assertFalse(evaluate_case(reduced)["passed"])


if __name__ == "__main__":
    unittest.main()
