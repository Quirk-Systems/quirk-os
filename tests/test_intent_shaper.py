from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator, FormatChecker
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from intent_shaper.policy import evaluate_case, evaluate_cases  # noqa: E402
from intent_shaper import policy as intent_policy  # noqa: E402
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
        self.assertEqual(36, len(results))

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


    def test_generated_ui_candidate_with_placeholder_manual_refs_blocks(self) -> None:
        results = {result["id"]: result for result in evaluate_cases(self.suite["cases"])}
        actual = results["QIS-GUI-001"]["actual"]
        self.assertEqual("blocked_manual", actual["status"])
        self.assertEqual(["MANUAL_EVIDENCE_MISSING"], actual["reason_codes"])
        self.assertEqual("missing", actual["manual_evidence_summary"]["keyboard"])

    def test_generated_ui_rejects_path_traversal_and_malformed_plan(self) -> None:
        cases = {case["id"]: case for case in self.suite["cases"]}
        traversal = copy.deepcopy(cases["QIS-GUI-005"])
        traversal["input"]["generated_ui_plan"]["component_manifests"][0]["manifest_ref"] = "../../../../etc/passwd"
        malformed = copy.deepcopy(cases["QIS-GUI-001"])
        del malformed["input"]["generated_ui_plan"]["component_manifests"][0]["data_bindings"]
        malformed_time = copy.deepcopy(cases["QIS-GUI-001"])
        malformed_time["input"]["as_of"] = "not-a-date"
        malformed_time_type = copy.deepcopy(cases["QIS-GUI-001"])
        malformed_time_type["input"]["as_of"] = []
        replay_mismatch = copy.deepcopy(cases["QIS-GUI-001"])
        replay_mismatch["input"]["generated_ui_plan"]["reconstruction_contract"]["replay_hash_sha256"] = "f" * 64

        for case in (traversal, malformed, malformed_time, malformed_time_type, replay_mismatch):
            with self.subTest(case=case["id"]):
                actual = evaluate_case(case)["actual"]
                self.assertEqual("rejected", actual["status"])
                self.assertEqual([], list(self.receipt_validator.iter_errors(actual)))
        self.assertIn("COMPONENT_MANIFEST_INACCESSIBLE", evaluate_case(traversal)["actual"]["reason_codes"])
        self.assertIn("GENERATED_UI_PLAN_INVALID", evaluate_case(malformed)["actual"]["reason_codes"])
        self.assertEqual(["GENERATED_UI_PLAN_INVALID"], evaluate_case(malformed_time)["actual"]["reason_codes"])
        self.assertEqual(["GENERATED_UI_PLAN_INVALID"], evaluate_case(malformed_time_type)["actual"]["reason_codes"])
        self.assertIn("RECONSTRUCTION_INPUTS_MISSING", evaluate_case(replay_mismatch)["actual"]["reason_codes"])

    def test_reconstruction_requires_each_pinned_component_manifest(self) -> None:
        case = copy.deepcopy(next(item for item in self.suite["cases"] if item["id"] == "QIS-GUI-001"))
        input_refs = case["input"]["generated_ui_plan"]["reconstruction_contract"]["input_refs"]
        input_refs[-1] = "examples/personalization-plan.valid.json"
        actual = evaluate_case(case)["actual"]
        self.assertEqual("rejected", actual["status"])
        self.assertIn("RECONSTRUCTION_INPUTS_MISSING", actual["reason_codes"])
        self.assertEqual([], list(self.receipt_validator.iter_errors(actual)))

    def test_generated_ui_receipt_schema_rejects_contradictory_reasons(self) -> None:
        result = next(
            item["actual"]
            for item in evaluate_cases(self.suite["cases"])
            if item["id"] == "QIS-GUI-008"
        )
        result["reason_codes"] = ["CANDIDATE_EVIDENCE_COMPLETE"]
        self.assertTrue(list(self.receipt_validator.iter_errors(result)))

    def test_generated_ui_rejects_tampered_machine_check_receipt(self) -> None:
        case = copy.deepcopy(next(item for item in self.suite["cases"] if item["id"] == "QIS-GUI-001"))
        load_json = intent_policy._contained_json

        def tampered_json(path_ref: object) -> tuple[Path, object] | None:
            loaded = load_json(path_ref)
            if (
                loaded is not None
                and str(path_ref).endswith("issue-intake-form.accessibility.json")
                and isinstance(loaded[1], dict)
            ):
                receipt = copy.deepcopy(loaded[1])
                receipt["checks"]["focus_order_declared"] = False
                return loaded[0], receipt
            return loaded

        with patch("intent_shaper.policy._contained_json", side_effect=tampered_json):
            result = evaluate_case(case)["actual"]
        self.assertEqual("rejected", result["status"])
        self.assertIn("ACCESSIBILITY_MACHINE_CHECK_FAILED", result["reason_codes"])

    def test_component_bindings_require_unique_ids_and_matching_prefixes(self) -> None:
        component_ref = "skills/quirk-intent-shaper/generated-ui/issue-intake-form.json"
        _, artifact = intent_policy._contained_json(component_ref)
        duplicate = copy.deepcopy(artifact)
        duplicate["data_bindings"].append({**duplicate["data_bindings"][0], "source_ref": "intent.details"})
        self.assertEqual(
            ["COMPONENT_MANIFEST_INACCESSIBLE"],
            intent_policy._component_contract_errors(duplicate, duplicate, "affordance.plain_answer"),
        )

        wrong_prefix = copy.deepcopy(artifact)
        wrong_prefix["data_bindings"][0]["binding_id"] = "state.shared"
        self.assertEqual(
            ["COMPONENT_MANIFEST_INACCESSIBLE"],
            intent_policy._component_contract_errors(wrong_prefix, wrong_prefix, "affordance.plain_answer"),
        )

    def test_manual_evidence_is_bound_to_component_version_and_hash(self) -> None:
        component_ref = "skills/quirk-intent-shaper/generated-ui/issue-intake-form.json"
        _, component = intent_policy._contained_json(component_ref)
        component_hash = hashlib.sha256(
            json.dumps(component, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        artifact = {
            "requirement": "keyboard",
            "observation": "Reviewed keyboard navigation in the pinned component.",
            "reviewed_by": "human.reviewer",
            "reviewed_at": "2026-08-12T00:00:00Z",
            "components": [
                {
                    "component_id": component["component_id"],
                    "version": component["version"],
                    "content_hash_sha256": component_hash,
                }
            ],
        }
        artifact_hash = hashlib.sha256(
            json.dumps(artifact, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        entry = {
            "status": "provided",
            "evidence_ref": "evals/intent-shaper/manual-evidence/keyboard.json",
            "evidence_sha256": artifact_hash,
            "reviewed_by": artifact["reviewed_by"],
            "reviewed_at": artifact["reviewed_at"],
        }
        as_of = datetime(2026, 8, 12, 12, tzinfo=timezone.utc)
        loaded = (REPO / entry["evidence_ref"], artifact)

        with patch.dict(os.environ, {"QUIRK_TRUSTED_MANUAL_EVIDENCE_SHA256": ""}):
            with patch("intent_shaper.policy._contained_json", return_value=loaded):
                self.assertFalse(intent_policy._verified_manual_evidence(entry, "keyboard", as_of, [(component, component_hash)]))

        with patch.dict(os.environ, {"QUIRK_TRUSTED_MANUAL_EVIDENCE_SHA256": artifact_hash}):
            with patch("intent_shaper.policy._contained_json", return_value=loaded):
                self.assertTrue(intent_policy._verified_manual_evidence(entry, "keyboard", as_of, [(component, component_hash)]))

        artifact["components"][0]["version"] = "9.9.9"
        entry["evidence_sha256"] = hashlib.sha256(
            json.dumps(artifact, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        with patch.dict(os.environ, {"QUIRK_TRUSTED_MANUAL_EVIDENCE_SHA256": entry["evidence_sha256"]}):
            with patch("intent_shaper.policy._contained_json", return_value=loaded):
                self.assertFalse(intent_policy._verified_manual_evidence(entry, "keyboard", as_of, [(component, component_hash)]))


    def test_generated_ui_missing_manual_evidence_blocks(self) -> None:
        results = {result["id"]: result for result in evaluate_cases(self.suite["cases"])}
        actual = results["QIS-GUI-008"]["actual"]
        self.assertEqual("blocked_manual", actual["status"])
        self.assertEqual(["MANUAL_EVIDENCE_MISSING"], actual["reason_codes"])
        self.assertEqual("missing", actual["manual_evidence_summary"]["keyboard"])


if __name__ == "__main__":
    unittest.main()
