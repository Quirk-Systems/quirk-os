"""Full-object and command-line regressions; all observations are synthetic."""

from __future__ import annotations

import contextlib
import copy
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from intent_shaper.contracts import validate_personalization_plan, validate_proposed_move
from intent_shaper.policy import evaluate_case, persona_weight_total_valid
import validate_golden_pack


class IntentFullValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads((REPO / "schemas/personalization-plan.schema.json").read_text())
        cls.sample = json.loads((REPO / "examples/personalization-plan.valid.json").read_text())
        cls.move_schema = json.loads((REPO / "schemas/proposed-move.schema.json").read_text())
        cls.move = json.loads(
            (REPO / "proposed-moves/personalization/qpm_intent_shaper_candidate.json").read_text()
        )

    def off_plan(self) -> dict:
        plan = copy.deepcopy(self.sample)
        plan["settings"].update(
            personalization_enabled=False, adaptation_mode="off",
            implicit_signal_use="off", generated_ui="off",
        )
        plan["persona_hand"].update(primary=None, supporting=[])
        plan["voice"]["profile_ref"] = None
        plan["aesthetic"]["profile_ref"] = None
        plan["learning"].update(allowed_updates=[], feedback_evidence=None)
        return plan

    def test_complete_plan_and_off_empty_hand_pass(self) -> None:
        self.assertEqual([], validate_personalization_plan(self.sample, self.schema))
        self.assertEqual([], validate_personalization_plan(self.off_plan(), self.schema))

    def test_enabled_empty_hand_rejected(self) -> None:
        plan = copy.deepcopy(self.sample)
        plan["persona_hand"].update(primary=None, supporting=[])
        self.assertTrue(validate_personalization_plan(plan, self.schema))

    def test_aggregate_policy_is_shared_with_evaluator(self) -> None:
        for weights, valid in [
            ([0.7, 0.3], True),
            ([0.333333, 0.333333, 0.333333], True),
            ([0.7, 0.299999], True),
            ([0.7, 0.300001], True),
            ([0.7, 0.2999989], False),
            ([0.7, 0.3000011], False),
            ([0.4, 0.4], False),
            ([0.8, 0.8], False),
            ([0, 0], False),
        ]:
            with self.subTest(weights=weights):
                plan = copy.deepcopy(self.sample)
                template = plan["persona_hand"]["primary"]
                selections = [dict(template, weight=weight) for weight in weights]
                plan["persona_hand"].update(primary=selections[0], supporting=selections[1:])
                self.assertEqual(valid, not validate_personalization_plan(plan, self.schema))
                result = evaluate_case({
                    "id": "synthetic.persona.total", "operation": "persona_hand",
                    "input": plan["persona_hand"],
                })["actual"]
                self.assertEqual("accepted" if valid else "rejected", result["status"])
        for weights in [[], [True], [float("nan")], [float("inf")], [-0.1, 1.1]]:
            self.assertFalse(persona_weight_total_valid([{"weight": w} for w in weights]))

    def test_actual_plan_rejects_persona_claim_not_just_operation_fixture(self) -> None:
        plan = copy.deepcopy(self.sample)
        plan["persona_hand"]["primary"]["role"] = "permanent_identity"
        self.assertIn("persona_hand/0:identity_claim_rejected", validate_personalization_plan(plan, self.schema))

    def test_candidate_generated_ui_must_be_explicitly_off(self) -> None:
        for value in [None, "task_gated", "preferred"]:
            plan = copy.deepcopy(self.sample)
            if value is None:
                del plan["settings"]["generated_ui"]
            else:
                plan["settings"]["generated_ui"] = value
            self.assertTrue(validate_personalization_plan(plan, self.schema))

    def test_dates_and_authority_fail_in_full_validator(self) -> None:
        for value in ["not-a-date", "2026-10-04T12:00:00", "2026-02-30T12:00:00Z"]:
            plan = copy.deepcopy(self.sample)
            plan["created_at"] = value
            self.assertTrue(validate_personalization_plan(plan, self.schema))
            plan = copy.deepcopy(self.sample)
            plan["preferences"][0]["valid_from"] = value
            self.assertTrue(validate_personalization_plan(plan, self.schema))
        for status in ["candidate", "approved", "applied"]:
            plan = copy.deepcopy(self.sample)
            plan.update(status=status, approval_ref="synthetic.approval")
            plan["authority"].update(ceiling="execute_reversible", admission_ref="synthetic.grant")
            self.assertTrue(validate_personalization_plan(plan, self.schema))

    def test_off_rejects_each_latent_saved_state(self) -> None:
        mutations = [
            ("persona_hand", "primary", self.sample["persona_hand"]["primary"]),
            ("persona_hand", "supporting", self.sample["persona_hand"]["supporting"]),
            ("voice", "profile_ref", "saved.voice"),
            ("aesthetic", "profile_ref", "saved.aesthetic"),
            ("settings", "adaptation_mode", "propose_only"),
            ("settings", "implicit_signal_use", "limited"),
            ("settings", "generated_ui", "task_gated"),
            ("learning", "allowed_updates", ["propose_preference_edge"]),
            ("learning", "feedback_evidence", {
                "receipt_ref": "synthetic.receipt", "receipt_digest": "a" * 64,
                "immutable": True, "proposal_ref": "synthetic.proposal",
            }),
        ]
        for section, key, value in mutations:
            with self.subTest(section=section, key=key):
                plan = self.off_plan()
                plan[section][key] = value
                self.assertTrue(validate_personalization_plan(plan, self.schema))
        plan = self.off_plan()
        plan["preferences"][0]["source"] = "explicit_saved"
        self.assertTrue(validate_personalization_plan(plan, self.schema))

    def test_candidate_move_passes_without_admission(self) -> None:
        self.assertEqual([], validate_proposed_move(self.move, self.move_schema))

    def test_resolved_move_requires_real_nonempty_refs_not_just_present_keys(self) -> None:
        move = copy.deepcopy(self.move)
        move.update(disposition="verified", receipt_ref="synthetic.receipt",
                    resolution_note="Synthetic resolution", evidence_refs=["synthetic.evidence"])
        self.assertEqual([], validate_proposed_move(move, self.move_schema))
        for field, value in [
            ("evidence_refs", None), ("evidence_refs", []), ("evidence_refs", [" "]),
            ("receipt_ref", ""), ("receipt_ref", " "), ("resolution_note", " "),
            ("resolution_artifacts", [" "]), ("created_at", "not-a-date"),
        ]:
            with self.subTest(field=field, value=value):
                invalid = copy.deepcopy(move)
                if value is None:
                    del invalid[field]
                else:
                    invalid[field] = value
                self.assertTrue(validate_proposed_move(invalid, self.move_schema))

    def test_golden_scans_unqueued_canonical_move_and_rejects_invalid_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "schemas").mkdir()
            (root / "schemas/proposed-move.schema.json").write_text(json.dumps(self.move_schema))
            path = root / "proposed-moves/personalization/qpm_synthetic.json"
            path.parent.mkdir(parents=True)
            move = copy.deepcopy(self.move)
            path.write_text(json.dumps(move))
            with patch.object(validate_golden_pack, "ROOT", root):
                self.assertEqual(0, validate_golden_pack.validate_canonical_moves())
                move["created_at"] = "not-a-date"
                path.write_text(json.dumps(move))
                with contextlib.redirect_stderr(io.StringIO()) as output:
                    self.assertGreater(validate_golden_pack.validate_canonical_moves(), 0)
                self.assertIn("date-time", output.getvalue())

    def test_golden_legacy_exception_is_explicit_and_not_a_canonical_bypass(self) -> None:
        relative = "proposed-moves/sync-control-plane/qpm_sync_control_plane_bootstrap.json"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "schemas").mkdir()
            (root / "schemas/proposed-move.schema.json").write_text(json.dumps(self.move_schema))
            path = root / relative
            path.parent.mkdir(parents=True)
            shutil.copyfile(REPO / relative, path)
            with patch.object(validate_golden_pack, "ROOT", root):
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(0, validate_golden_pack.validate_canonical_moves())
                self.assertIn("EXCEPTION:", output.getvalue())
                self.assertIn("not canonical conformance or admission proof", output.getvalue())
                move = copy.deepcopy(self.move)
                move["created_at"] = "not-a-date"
                path.write_text(json.dumps(move))
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertGreater(validate_golden_pack.validate_canonical_moves(), 0)

    def test_non_pr3_blocker_holds_candidates_and_fails_every_admission_status(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "schemas").mkdir()
            (root / "schemas/proposed-move.schema.json").write_text(json.dumps(self.move_schema))
            path = root / "proposed-moves/personalization/qpm_synthetic.json"
            path.parent.mkdir(parents=True)
            move = copy.deepcopy(self.move)
            move.update(blocks_merge=True, disposition="new")
            path.write_text(json.dumps(move))
            with patch.object(validate_golden_pack, "ROOT", root):
                for status in sorted(validate_golden_pack.CANDIDATE_STATUSES):
                    with self.subTest(status=status):
                        unresolved = []
                        with contextlib.redirect_stdout(io.StringIO()) as output:
                            errors = validate_golden_pack.validate_canonical_moves(status, unresolved)
                        self.assertEqual(0, errors)
                        self.assertEqual([move["id"]], unresolved)
                        self.assertIn("HOLD:", output.getvalue())
                for status in sorted(validate_golden_pack.ADMISSION_STATUSES):
                    with self.subTest(status=status):
                        unresolved = []
                        with contextlib.redirect_stderr(io.StringIO()) as output:
                            errors = validate_golden_pack.validate_canonical_moves(status, unresolved)
                        self.assertEqual(1, errors)
                        self.assertEqual([move["id"]], unresolved)
                        self.assertIn("admission blocked", output.getvalue())

                move["blocks_merge"] = False
                path.write_text(json.dumps(move))
                unresolved = []
                self.assertEqual(0, validate_golden_pack.validate_canonical_moves("LIVE", unresolved))
                self.assertEqual([], unresolved)

                move.update(
                    blocks_merge=True, disposition="verified", receipt_ref="synthetic.receipt",
                    resolution_note="Synthetic resolution", evidence_refs=["synthetic.evidence"],
                )
                path.write_text(json.dumps(move))
                unresolved = []
                self.assertEqual(0, validate_golden_pack.validate_canonical_moves("ADMITTED", unresolved))
                self.assertEqual([], unresolved)
                del move["evidence_refs"]
                path.write_text(json.dumps(move))
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertGreater(validate_golden_pack.validate_canonical_moves("ADMITTED"), 0)

    def test_pr3_candidate_holds_do_not_become_test_admission_requirements(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()) as output:
            errors, candidate_unresolved = validate_golden_pack.validate_tribunal_queue(
                "proposed-moves/pr-3/queue.json", "PROPOSED"
            )
        self.assertEqual(0, errors)
        self.assertTrue(candidate_unresolved)
        self.assertIn("HOLD:", output.getvalue())
        with contextlib.redirect_stderr(io.StringIO()):
            errors, admission_unresolved = validate_golden_pack.validate_tribunal_queue(
                "proposed-moves/pr-3/queue.json", "ADMITTED"
            )
        self.assertEqual(candidate_unresolved, admission_unresolved)
        self.assertEqual(len(admission_unresolved), errors)

    def test_cli_uses_full_plan_and_actual_move_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in [
                "schemas/personalization-plan.schema.json", "schemas/proposed-move.schema.json",
                "schemas/intent-shaper-admission-supplies.schema.json",
                "examples/personalization-plan.valid.json", "evals/intent-shaper/cases.json",
                "evals/intent-shaper/admission-supplies.json",
                "policies/personalization-adaptation-policy.yaml",
                "proposed-moves/personalization/qpm_intent_shaper_candidate.json",
            ]:
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(REPO / relative, destination)
            def run():
                result = subprocess.run(
                    [sys.executable, str(REPO / "scripts/validate_intent_shaper.py"),
                     "--repo", str(root), "--output", str(root / "report.json")],
                    capture_output=True, text=True,
                )
                return result, json.loads((root / "report.json").read_text())

            result, report = run()
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue(report["proposed_move_valid"])
            self.assertTrue(report["admission_supplies_valid"])
            plan = copy.deepcopy(self.sample)
            plan["persona_hand"]["primary"]["weight"] = 0.2
            (root / "examples/personalization-plan.valid.json").write_text(json.dumps(plan))
            result, report = run()
            self.assertEqual(1, result.returncode)
            self.assertFalse(report["sample_valid"])
            self.assertIn("sample:persona_hand:invalid_weight_total", report["errors"])
            (root / "examples/personalization-plan.valid.json").write_text(json.dumps(self.sample))
            move = copy.deepcopy(self.move)
            move["created_at"] = "not-a-date"
            (root / "proposed-moves/personalization/qpm_intent_shaper_candidate.json").write_text(json.dumps(move))
            result, report = run()
            self.assertEqual(1, result.returncode)
            self.assertFalse(report["proposed_move_valid"])
            self.assertEqual(25, report["fixtures_passed"])
            (root / "proposed-moves/personalization/qpm_intent_shaper_candidate.json").write_text(
                json.dumps(self.move)
            )
            supplies_path = root / "evals/intent-shaper/admission-supplies.json"
            supplies = json.loads(supplies_path.read_text())
            supplies["runtime_admission"]["status"] = "approved"
            supplies_path.write_text(json.dumps(supplies))
            result, report = run()
            self.assertEqual(1, result.returncode)
            self.assertFalse(report["admission_supplies_valid"])
            self.assertTrue(report["sample_valid"])
            self.assertTrue(report["proposed_move_valid"])
            self.assertTrue(any(error.startswith("admission_supplies:") for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
