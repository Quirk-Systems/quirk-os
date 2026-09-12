from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from scripts.engineering.loop import LoopRunner, LoopStore, spec_digest


def spec():
    return {
        "schema_version": "loop-spec/v1", "run_id": "run.pilot", "objective": "Prepare the next proof",
        "source_digest": "a" * 64, "evaluator_digest": "b" * 64,
        "acceptance": {"required": ["next_proof", "source_ref"]},
        "authority": "CANDIDATE_PREPARE", "limits": {"steps": 3, "repairs": 2, "seconds": 30},
    }


def outcome(value="ready", *, evidence=True, verified=True):
    return {"strategy": "direct", "candidate": {"next_proof": value, "source_ref": "fixture.source"},
            "action_receipt": {"status": "VERIFIED" if verified else "UNCERTAIN", "evidence": ["fixture.observed"] if evidence else []}}


def verify(candidate, acceptance):
    missing = [field for field in acceptance["required"] if not candidate.get(field)]
    return {"passed": not missing, "reasons": missing}


class LoopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "loop.sqlite"
        self.store = LoopStore(self.path)
        self.runner = LoopRunner(self.store)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def run_loop(self, step, **kwargs):
        return self.runner.run(spec(), step, verify, evaluator_digest="b" * 64, **kwargs)

    def test_verified_candidate_is_review_ready_without_claiming_human_benefit(self):
        result = self.run_loop(lambda context: outcome())
        self.assertEqual(result["status"], "REVIEW_READY")
        self.assertIsNone(result["human_usefulness"])
        self.assertEqual(result["steps"], 1)

    def test_completed_run_resumes_without_another_action(self):
        self.run_loop(lambda context: outcome())
        result = self.run_loop(lambda context: self.fail("must not dispatch completed run"))
        self.assertEqual(result["status"], "REVIEW_READY")

    def test_repeated_failed_state_stops(self):
        result = self.run_loop(lambda context: outcome(value=""))
        self.assertEqual(result["status"], "STALLED")
        self.assertEqual(result["steps"], 2)

    def test_missing_observation_cannot_pass_fluent_candidate(self):
        result = self.run_loop(lambda context: outcome(evidence=False))
        self.assertNotEqual(result["status"], "REVIEW_READY")
        self.assertIn("OBSERVATION_MISSING", result["reasons"])

    def test_uncertain_effect_pauses_before_retry(self):
        result = self.run_loop(lambda context: outcome(verified=False))
        self.assertEqual(result["status"], "PAUSED_UNCERTAIN_EFFECT")
        self.assertEqual(result["steps"], 1)

    def test_changed_criteria_on_resume_do_not_rewrite_run(self):
        self.run_loop(lambda context: outcome())
        changed = spec()
        changed["acceptance"] = {"required": []}
        with self.assertRaisesRegex(ValueError, "spec changed"):
            self.runner.run(changed, lambda context: outcome(), verify, evaluator_digest="b" * 64)
        self.assertEqual(self.store.get("run.pilot")["spec_digest"], spec_digest(spec()))

    def test_different_evaluator_is_rejected_before_dispatch(self):
        with self.assertRaisesRegex(ValueError, "evaluator"):
            self.runner.run(spec(), lambda context: self.fail("no dispatch"), verify, evaluator_digest="c" * 64)

    def test_authority_change_pauses_without_action(self):
        changed = spec()
        changed["authority"] = "PUBLISH"
        result = self.runner.run(changed, lambda context: self.fail("no dispatch"), verify, evaluator_digest="b" * 64)
        self.assertEqual(result["status"], "PAUSED_AUTHORITY_CHANGE")

    def test_repairs_are_bounded_and_partial_is_kept(self):
        result = self.run_loop(lambda context: {**outcome(value=""), "strategy": f"repair-{context['step']}"})
        self.assertEqual(result["status"], "BUDGET_EXHAUSTED")
        self.assertEqual(result["steps"], 3)
        self.assertIsNotNone(result["candidate"])

    def test_interrupt_and_reopen_preserves_the_same_step_identity(self):
        calls = []
        def interrupted(context):
            calls.append(context["step_id"])
            raise InterruptedError("worker interrupted")
        self.assertEqual(self.run_loop(interrupted)["status"], "INTERRUPTED")
        self.store.close()
        self.store = LoopStore(self.path)
        self.runner = LoopRunner(self.store)
        def resume(context):
            calls.append(context["step_id"])
            return outcome()
        self.assertEqual(self.run_loop(resume)["status"], "REVIEW_READY")
        self.assertEqual(calls[0], calls[1])

    def test_step_cannot_mutate_acceptance_by_reference(self):
        original = spec()
        def step(context):
            context["acceptance"]["required"].clear()
            return outcome(value="")
        result = self.runner.run(original, step, verify, evaluator_digest="b" * 64)
        self.assertNotEqual(result["status"], "REVIEW_READY")
        self.assertEqual(original, spec())

    def test_time_budget_is_checked_after_step(self):
        ticks = [0.0]
        def slow(context):
            ticks[0] = 31.0
            return outcome()
        result = self.run_loop(slow, clock=lambda: ticks[0])
        self.assertEqual(result["status"], "BUDGET_EXHAUSTED")

    def test_slow_verifier_cannot_pass_outside_time_budget(self):
        ticks = [0.0]
        def slow(candidate, acceptance):
            ticks[0] += 35
            return verify(candidate, acceptance)
        result = self.runner.run(spec(), lambda context: outcome(), slow, evaluator_digest="b" * 64, clock=lambda: ticks[0])
        self.assertEqual(result["status"], "BUDGET_EXHAUSTED")

    def test_interrupted_time_counts_across_resume(self):
        ticks = [0.0]
        def slow(context):
            ticks[0] += 29
            raise InterruptedError("late interruption")
        self.run_loop(slow, clock=lambda: ticks[0])
        result = self.run_loop(slow, clock=lambda: ticks[0])
        self.assertEqual(result["status"], "BUDGET_EXHAUSTED")
        self.assertGreaterEqual(result["elapsed_seconds"], 30)

    def test_store_blocks_historical_event_mutation(self):
        self.run_loop(lambda context: outcome())
        with self.assertRaises(Exception):
            self.store.connection.execute("DELETE FROM loop_events")

    def test_false_outcome_fails_even_when_receipt_says_verified(self):
        result = self.runner.run(spec(), lambda context: outcome(), lambda candidate, criteria: {"passed": False, "reasons": ["WRONG_DISPOSITION"]}, evaluator_digest="b" * 64)
        self.assertNotEqual(result["status"], "REVIEW_READY")
        self.assertIn("WRONG_DISPOSITION", result["reasons"])

    def test_crash_after_checkpoint_resumes_next_step(self):
        original_record = self.store.record
        def crash_after_record(state, event, owner):
            original_record(state, event, owner)
            if event == "REPAIR_NEEDED":
                raise SystemExit("simulated process exit")
        self.store.record = crash_after_record
        with self.assertRaises(SystemExit):
            self.run_loop(lambda context: outcome(value=""))
        self.store.record = original_record
        seen = []
        def resume(context):
            seen.append(context["step"])
            return outcome()
        result = self.run_loop(resume)
        self.assertEqual(result["status"], "REVIEW_READY")
        self.assertEqual(seen, [1])

    def test_original_spec_mutation_cannot_leak_lease(self):
        original = spec()
        def interrupted(context):
            original["run_id"] = "different"
            raise InterruptedError("interrupted")
        self.runner.run(original, interrupted, verify, evaluator_digest="b" * 64)
        self.assertEqual(self.run_loop(lambda context: outcome())["status"], "REVIEW_READY")

    def test_no_history_cannot_hide_forged_completed_projection(self):
        state = self.store.open_run(spec())
        state["status"] = "REVIEW_READY"
        import json
        with self.store.connection:
            self.store.connection.execute("UPDATE loop_runs SET state_json=?", (json.dumps(state),))
        with self.assertRaisesRegex(ValueError, "initial state"):
            self.run_loop(lambda context: outcome())

    def test_repeated_interruptions_exhaust_dispatch_budget(self):
        def interrupted(context):
            raise InterruptedError("interrupt")
        for _ in range(4):
            result = self.run_loop(interrupted)
        self.assertEqual(result["status"], "BUDGET_EXHAUSTED")

    def test_elapsed_budget_is_reloaded_after_lease_acquisition(self):
        acquire = self.store.acquire
        def interleaved(run_id, duration):
            owner = acquire(run_id, duration)
            state = self.store.get(run_id)["state"]
            state.update(status="INTERRUPTED", elapsed_seconds=29)
            self.store.record(state, "INTERRUPTED", owner)
            return owner
        self.store.acquire = interleaved
        ticks = [0.0]
        def step(context):
            ticks[0] += 2
            return outcome()
        self.assertEqual(self.run_loop(step, clock=lambda: ticks[0])["status"], "BUDGET_EXHAUSTED")


if __name__ == "__main__":
    unittest.main()
