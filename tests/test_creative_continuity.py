"""Synthetic regressions for an existing resolver, not an agent or human trial."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from context_continuity import ContractError, canonical, resolve

FIXTURE = ROOT / "examples" / "creative-continuity.request.json"


class CreativeContinuityTests(unittest.TestCase):
    def request(self):
        self.assertTrue(FIXTURE.is_file(), "Missing approved creative continuation fixture")
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def run_request(self, **changes):
        request = self.request()
        request.update(changes)
        return resolve(**request)

    @staticmethod
    def selected(package):
        return {r["id"]: r for field in ("instructions", "references") for r in package[field]}

    def test_exact_source_and_protected_choice_survive(self):
        request = self.request()
        result = self.selected(resolve(**request))
        for record in request["records"]:
            if record["id"] in result:
                self.assertEqual(result[record["id"]]["original"], record["original"])
                self.assertEqual(result[record["id"]]["revision"], record["revision"])
                self.assertEqual(result[record["id"]]["original_sha256"], hashlib.sha256(record["original"].encode()).hexdigest())
        self.assertIn("protected-choice", result)
        self.assertIn("Keep the deliberate gap.", result["protected-choice"]["original"])

    def test_plan_is_excluded_from_play_scope(self):
        result = self.run_request()
        self.assertEqual(result["status"], "complete")
        self.assertNotIn("plugin-planning", self.selected(result))
        self.assertIn({"id": "plugin-planning", "decision": "exclude", "reason": "outside task domain"}, result["decisions"])

    def test_planner_scope_reuses_same_record_without_promoting_it(self):
        result = self.run_request(domains=["plugin-planning"])
        self.assertIn("plugin-planning", self.selected(result))
        self.assertEqual(result["authority_effect"], "none")
        self.assertEqual(self.selected(result)["plugin-planning"]["kind"], "reference")

    def test_fictional_success_cannot_supply_an_instruction(self):
        request = self.request()
        for record in request["records"]:
            if record["id"] == "fictional-unlock":
                record["kind"] = "instruction"
                record["state"] = "successful"
        result = resolve(**request)
        self.assertNotIn("fictional-unlock", self.selected(result))
        self.assertEqual(result["authority_effect"], "none")

    def test_preference_bypass_preserves_task_and_novel_option(self):
        result = self.run_request(bypass_preferences=True)
        selected = self.selected(result)
        self.assertNotIn("taste-context", selected)
        self.assertNotIn("taste-derived", selected)
        self.assertIn("protected-choice", selected)
        self.assertIn("unfamiliar-option", selected)
        self.assertEqual(result["status"], "complete")

    def test_preference_does_not_transfer_to_another_person(self):
        result = self.run_request(audience="participant-b")
        self.assertNotIn("taste-context", self.selected(result))
        self.assertNotIn("taste-derived", self.selected(result))
        self.assertIn("protected-choice", self.selected(result))
        self.assertEqual(result["status"], "complete")

    def test_private_source_and_derivative_do_not_leak(self):
        request = self.request()
        with_private = resolve(**request)
        request["records"] = [r for r in request["records"] if r["id"] not in {"private-note", "private-derived"}]
        self.assertEqual(with_private, resolve(**request))
        self.assertNotIn("PRIVATE_SENTINEL", canonical(with_private))

    def test_withdrawal_removes_derivative_without_stopping_other_work(self):
        result = self.run_request(withdrawn_ids=["taste-context"])
        self.assertEqual(result["status"], "complete")
        self.assertNotIn("taste-context", self.selected(result))
        self.assertNotIn("taste-derived", self.selected(result))
        self.assertIn("unfamiliar-option", self.selected(result))

    def test_optional_blocker_does_not_block_the_task(self):
        result = self.run_request()
        self.assertEqual(result["status"], "complete")
        self.assertNotIn("remote-return", self.selected(result))
        self.assertEqual(result["authority_effect"], "none")

    def test_blocked_return_needs_both_requested_reconsideration_and_change(self):
        for change in ({"reconsider_ids": ["remote-return"]}, {"changed_conditions": ["returned-artifact"]}):
            self.assertNotIn("remote-return", self.selected(self.run_request(**change)))
        result = self.run_request(reconsider_ids=["remote-return"], changed_conditions=["returned-artifact"], exploration_slots=2)
        self.assertIn("remote-return", self.selected(result))
        self.assertEqual(self.selected(result)["remote-return"]["state"], "blocked")

    def test_budget_omits_instead_of_truncating_and_marks_incomplete(self):
        result = self.run_request(budget_chars=1)
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(self.selected(result), {})
        self.assertIn("budget; original not truncated", {d["reason"] for d in result["decisions"]})

    def test_unknown_human_benefit_and_loading_remain_unknown(self):
        result = self.run_request()
        self.assertIsNone(result["cost"]["human_effort"])
        self.assertIsNone(result["cost"]["interruptions"])
        self.assertEqual(result["coverage"], {"delivered": False, "loaded": False, "behavior_tested": False})
        self.assertNotIn("quality_score", result)

    def test_replay_is_identical_and_input_is_not_mutated(self):
        request = self.request()
        before = copy.deepcopy(request)
        first = resolve(**request)
        request["records"].reverse()
        second = resolve(**request)
        self.assertEqual(first, second)
        request["records"].reverse()
        self.assertEqual(request, before)

    def test_revision_change_changes_lineage_without_changing_original(self):
        request = self.request()
        before = self.selected(resolve(**request))
        next(r for r in request["records"] if r["id"] == "taste-context")["revision"] = "synthetic-v2"
        after = self.selected(resolve(**request))
        self.assertNotEqual(before["taste-derived"]["lineage_sha256"], after["taste-derived"]["lineage_sha256"])
        self.assertEqual(before["taste-derived"]["original"], after["taste-derived"]["original"])

    def test_cyclic_lineage_is_rejected(self):
        request = self.request()
        next(r for r in request["records"] if r["id"] == "taste-context")["derived_from"] = ["taste-derived"]
        with self.assertRaises(ContractError):
            resolve(**request)

    def test_real_cli_json_and_markdown(self):
        self.request()
        command = [sys.executable, str(ROOT / "scripts" / "context_continuity.py"), str(FIXTURE)]
        data = subprocess.run(command, check=True, capture_output=True, text=True)
        result = json.loads(data.stdout)
        self.assertEqual(result, self.run_request())
        rendered = subprocess.run(command + ["--format", "markdown"], check=True, capture_output=True, text=True)
        self.assertIn("Keep the deliberate gap.", rendered.stdout)
        self.assertNotIn("PRIVATE_SENTINEL", rendered.stdout)
        self.assertIn("grants no execution authority", rendered.stdout)


if __name__ == "__main__":
    unittest.main()
