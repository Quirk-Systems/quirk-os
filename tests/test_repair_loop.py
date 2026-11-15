import copy
import json
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from agent_reliability.repair_loop import plan_loop


def safe():
    pack = json.loads((ROOT / "evals/agent-reliability/v0.1.2/fixtures.json").read_text())
    return copy.deepcopy(next(f["case"] for f in pack["completion"] if f["expected"]))


def observation(case, mutation="baseline"):
    return {"evaluation": {"kind": "completion", "case": case}, "mutation_id": mutation}


def loop(*observations):
    return plan_loop({"goal_id": "verify-original-goal", "round_limit": 3, "observations": list(observations)})


class RepairLoopTests(unittest.TestCase):
    def test_loop_cli_runs_and_recovers_from_invalid_input(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "loop.json"
            path.write_text(json.dumps({"goal_id":"goal", "round_limit":3, "observations":[observation(safe())]}))
            run = subprocess.run([sys.executable, "scripts/route_agent_verification.py", "--loop", str(path)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(0, run.returncode)
            self.assertEqual("CANDIDATE_REVIEW", json.loads(run.stdout)["stop_reason"])
            path.write_text('{"goal_id":"SECRET","round_limit":4,"observations":[]}')
            run = subprocess.run([sys.executable, "scripts/route_agent_verification.py", "--loop", str(path)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(2, run.returncode)
            self.assertNotIn("SECRET", run.stderr)

    def test_steps_are_ordered_and_have_proof(self):
        case = safe(); case["obligations"][0]["status"] = "failed"
        result = loop(observation(case))
        steps = result["frames"][0]["steps"]
        self.assertEqual(["inspect", "propose", "verify"], [s["phase"] for s in steps])
        self.assertEqual([], steps[0]["requires"])
        self.assertEqual([steps[0]["id"]], steps[1]["requires"])
        self.assertTrue(all(s["completion_proof"] and not s["executable"] for s in steps))
        self.assertEqual("AWAIT_OBSERVATION", result["stop_reason"])

    def test_repair_reduces_blockers_but_does_not_claim_user_benefit(self):
        broken = safe(); broken["obligations"][0]["status"] = "failed"
        result = loop(observation(broken), observation(safe(), "repair-check"))
        self.assertEqual("BLOCKERS_REDUCED", result["frames"][1]["comparison"])
        self.assertEqual("CANDIDATE_REVIEW", result["stop_reason"])
        self.assertEqual("NOT_MEASURED", result["benefit_status"])
        self.assertFalse(result["authority_effect"])
        self.assertEqual(0, result["effects_executed"])

    def test_surprise_tradeoff_is_preserved_and_stops(self):
        first = safe(); first["current"]["source_digest"] = "changed"
        second = safe(); second["obligations"][0]["validator"] = "model:planner"
        result = loop(observation(first), observation(second, "refresh-exposed-self-signoff"))
        frame = result["frames"][1]
        self.assertEqual("TRADEOFF", frame["comparison"])
        self.assertIn("stale_evidence", frame["resolved_reasons"])
        self.assertIn("self_signed", frame["new_reasons"])
        self.assertEqual("REGRESSION_REVIEW", result["stop_reason"])

    def test_goal_shrinking_cannot_manufacture_improvement(self):
        first = safe(); first["obligations"][0]["status"] = "failed"
        second = safe(); second["required_ids"] = ["different-goal"]
        with self.assertRaisesRegex(ValueError, "goal or requested authority changed"):
            loop(observation(first), observation(second, "drop-required-behavior"))

    def test_two_nonimproving_rounds_stop(self):
        case = safe(); case["obligations"][0]["status"] = "failed"
        result = loop(observation(case), observation(case, "retry-1"), observation(case, "retry-2"))
        self.assertEqual("NO_PROGRESS", result["stop_reason"])

    def test_observations_after_candidate_stop_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "beyond stop"):
            loop(observation(safe()), observation(safe(), "keep-going"))

    def test_authority_failure_stops_before_any_retry(self):
        pack = json.loads((ROOT / "evals/agent-reliability/v0.1.2/fixtures.json").read_text())
        case = next(f["case"] for f in pack["authority"] if not f["expected"])
        item = {"evaluation": {"kind": "authority", "case": case}, "mutation_id": "baseline"}
        self.assertEqual("AUTHORITY_RECONCILIATION", loop(item)["stop_reason"])

    def test_budget_and_imported_approval_fail_closed(self):
        item = observation(safe())
        for budget in (True, 0, 4, "3"):
            with self.subTest(budget=budget), self.assertRaises(ValueError):
                plan_loop({"goal_id":"goal", "round_limit":budget, "observations":[item]})
        with self.assertRaises(ValueError):
            plan_loop({"goal_id":"goal", "round_limit":3, "observations":[item], "approved":True})

    def test_repeated_mutation_and_input_changes_do_not_hide_failures(self):
        case = safe(); case["obligations"][0]["status"] = "failed"
        before = copy.deepcopy(case)
        with self.assertRaisesRegex(ValueError, "repeated mutation"):
            loop(observation(case), observation(case))
        self.assertEqual(before, case)


if __name__ == "__main__":
    unittest.main()
