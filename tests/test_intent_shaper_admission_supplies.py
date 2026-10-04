from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker


REPO = Path(__file__).resolve().parents[1]


class IntentShaperAdmissionSuppliesTests(unittest.TestCase):
    """Supply honesty checks, not admission or byte-receipt verification."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(
            (REPO / "schemas/intent-shaper-admission-supplies.schema.json").read_text()
        )
        cls.supplies = json.loads(
            (REPO / "evals/intent-shaper/admission-supplies.json").read_text()
        )
        cls.validator = Draft202012Validator(
            cls.schema, format_checker=FormatChecker()
        )

    def assert_rejected(self, supplies: dict) -> None:
        self.assertTrue(list(self.validator.iter_errors(supplies)))

    def test_schema_is_valid(self) -> None:
        Draft202012Validator.check_schema(self.schema)

    def test_truthful_blocked_supplies_validate(self) -> None:
        self.assertEqual([], list(self.validator.iter_errors(self.supplies)))
        self.assertEqual("blocked", self.supplies["runtime_admission"]["status"])
        self.assertEqual([], self.supplies["evidence_receipt_refs"])
        self.assertEqual([], self.supplies["human_observations"])

    def test_exact_user_approvals_are_preserved(self) -> None:
        self.assertEqual(
            {
                "Authorized by Bryan with Synthetically Generated and Marked Supplies",
                "authorize merging updated main into the current branch so I can implement the repairs",
                "Authorize all human approvals required",
            },
            {approval["quote"] for approval in self.supplies["approvals"]},
        )
        for approval in self.supplies["approvals"]:
            self.assertEqual("user_supplied_authorization", approval["source_kind"])
            self.assertFalse(approval["observation_credit"])
            self.assertFalse(approval["runtime_grant"])
            expected_date = (
                "2026-10-04T04:28:25.038+00:00"
                if approval["quote"]
                == "Authorized by Bryan with Synthetically Generated and Marked Supplies"
                else "2026-10-04T04:37:35.835+00:00"
            )
            self.assertEqual(expected_date, approval["source_date"])
            self.assertEqual(
                "conversation:current-user:" + expected_date, approval["source_ref"]
            )
        for index in range(len(self.supplies["approvals"])):
            with self.subTest(index=index):
                supplies = copy.deepcopy(self.supplies)
                supplies["approvals"][index]["source_date"] = supplies["recorded_at"]
                supplies["approvals"][index]["source_ref"] = (
                    "conversation:current-user:" + supplies["recorded_at"]
                )
                self.assert_rejected(supplies)

    def test_all_seven_synthetic_gate_specs_are_present(self) -> None:
        self.assertEqual(
            {f"QIS-{number:03d}" for number in range(12, 19)},
            {exercise["gate_id"] for exercise in self.supplies["synthetic_exercises"]},
        )

    def test_each_exercise_rejects_human_or_verified_relabeling(self) -> None:
        for index in range(len(self.supplies["synthetic_exercises"])):
            for key, value in (
                ("evidence_kind", "human"),
                ("generated_by", "Bryan"),
                ("execution_status", "passed"),
                ("human_observation", True),
                ("admission_credit", True),
            ):
                with self.subTest(index=index, key=key):
                    supplies = copy.deepcopy(self.supplies)
                    supplies["synthetic_exercises"][index][key] = value
                    self.assert_rejected(supplies)

    def test_synthetic_measurements_and_participants_are_not_representable(self) -> None:
        for key, value in (("measured_improvement", 1.0), ("participant", "Bryan")):
            with self.subTest(key=key):
                supplies = copy.deepcopy(self.supplies)
                supplies["synthetic_exercises"][1][key] = value
                self.assert_rejected(supplies)

    def test_missing_or_duplicate_gate_is_rejected(self) -> None:
        supplies = copy.deepcopy(self.supplies)
        supplies["synthetic_exercises"].pop()
        self.assert_rejected(supplies)
        supplies = copy.deepcopy(self.supplies)
        supplies["synthetic_exercises"][-1] = copy.deepcopy(
            supplies["synthetic_exercises"][0]
        )
        self.assert_rejected(supplies)

    def test_approval_cannot_be_recast_as_observation_or_runtime_grant(self) -> None:
        for key in ("observation_credit", "runtime_grant"):
            with self.subTest(key=key):
                supplies = copy.deepcopy(self.supplies)
                supplies["approvals"][0][key] = True
                self.assert_rejected(supplies)

    def test_generated_observation_is_rejected(self) -> None:
        supplies = copy.deepcopy(self.supplies)
        supplies["human_observations"].append(
            {"gate_id": "QIS-013", "evidence_kind": "synthetic", "result": "passed"}
        )
        self.assert_rejected(supplies)

    def test_unverified_receipt_reference_cannot_claim_verified(self) -> None:
        supplies = copy.deepcopy(self.supplies)
        reference = {
            "source_ref": ".quirk/evidence/example-not-an-actual-receipt.json",
            "verification_status": "unverified",
            "admission_effect": "none",
        }
        supplies["evidence_receipt_refs"].append(reference)
        self.assertEqual([], list(self.validator.iter_errors(supplies)))
        reference["verification_status"] = "verified"
        self.assert_rejected(supplies)

    def test_unverified_reference_cannot_supply_admission_credit(self) -> None:
        supplies = copy.deepcopy(self.supplies)
        supplies["evidence_receipt_refs"].append(
            {
                "source_ref": ".quirk/evidence/example-not-an-actual-receipt.json",
                "verification_status": "unverified",
                "admission_effect": "approved",
            }
        )
        self.assert_rejected(supplies)

    def test_incomplete_scope_cannot_claim_runtime_admission(self) -> None:
        supplies = copy.deepcopy(self.supplies)
        supplies["runtime_admission"]["status"] = "approved"
        supplies["runtime_admission"]["scope"]["purpose"] = "synthetic exercises"
        self.assert_rejected(supplies)

    def test_each_missing_scope_field_is_explicit_and_cannot_be_invented(self) -> None:
        scope = self.supplies["runtime_admission"]["scope"]
        for key in scope:
            with self.subTest(key=key):
                supplies = copy.deepcopy(self.supplies)
                del supplies["runtime_admission"]["scope"][key]
                self.assert_rejected(supplies)
                supplies = copy.deepcopy(self.supplies)
                supplies["runtime_admission"]["scope"][key] = "*"
                self.assert_rejected(supplies)

    def test_blanket_waiver_and_new_decision_cannot_be_inferred(self) -> None:
        for key, value in (
            ("waiver", {"actor": "Bryan", "scope": "*"}),
            ("new_admission_decision_ref", "conversation:approval"),
            ("generated_ui", "allowed"),
            ("authority_ceiling", "execute_bounded"),
        ):
            with self.subTest(key=key):
                supplies = copy.deepcopy(self.supplies)
                supplies["runtime_admission"][key] = value
                self.assert_rejected(supplies)

    def test_missing_gates_cannot_be_marked_satisfied(self) -> None:
        for gate in self.supplies["remaining_gates"]:
            with self.subTest(gate=gate):
                supplies = copy.deepcopy(self.supplies)
                supplies["remaining_gates"][gate] = "satisfied"
                self.assert_rejected(supplies)

    def test_format_checker_rejects_bad_record_date(self) -> None:
        supplies = copy.deepcopy(self.supplies)
        supplies["recorded_at"] = "not-a-date"
        self.assert_rejected(supplies)

    def test_move_links_supplies_as_context_without_promoting_disposition(self) -> None:
        move = json.loads(
            (REPO / "proposed-moves/personalization/qpm_intent_shaper_candidate.json").read_text()
        )
        self.assertEqual("new", move["disposition"])
        self.assertTrue(move["blocks_merge"])
        self.assertIn(
            "evals/intent-shaper/admission-supplies.json", move["source_refs"]
        )
        self.assertNotIn(
            "evals/intent-shaper/admission-supplies.json", move["evidence_refs"]
        )
        self.assertIn(
            ".quirk/evidence/2026-10-04-intent-shaper-governance-repair.json",
            move["evidence_refs"],
        )
        self.assertTrue(
            any(
                "2026-10-04-intent-shaper-governance-repair.json" in check
                and "pending" in check
                for check in move["acceptance_checks"]
            )
        )
        self.assertFalse(
            any("All twenty" in check for check in move["acceptance_checks"])
        )

    def test_move_pins_each_baseline_implementation_layer(self) -> None:
        move = json.loads(
            (REPO / "proposed-moves/personalization/qpm_intent_shaper_candidate.json").read_text()
        )
        prefix = (
            "https://github.com/Quirk-Systems/quirk-os/blob/"
            "c4bc0f0bdff10ccc217c8115035bd918129fe4b0/"
        )
        for path in (
            "skills/quirk-intent-shaper/SKILL.md",
            "evals/intent-shaper/cases.json",
            "schemas/personalization-plan.schema.json",
            "policies/personalization-adaptation-policy.yaml",
            "scripts/intent_shaper/policy.py",
            "scripts/validate_intent_shaper.py",
            "tests/test_intent_shaper.py",
            ".github/workflows/intent-shaper-conformance.yml",
        ):
            with self.subTest(path=path):
                self.assertIn(prefix + path, move["evidence_refs"])

if __name__ == "__main__":
    unittest.main()
