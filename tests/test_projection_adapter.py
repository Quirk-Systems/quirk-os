"""Tests for the bounded projection-adapter vertical slice (issue #9).

Validates acceptance criteria:
  - No projection edit becomes Canon.
  - Same idempotency key produces no duplicate mutation.
  - Every state change has an immutable receipt.
  - Retry timing and compensation are inspectable.
  - Drift is not silently repaired.
  - Reconstruction is demonstrated without altering existing user content.
  - Blast radius remains exactly one fixture object.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sync_control_plane.policy import evaluate_fixture  # noqa: E402


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


OBJECT_KEY = "fixture.projection-adapter-v0-2"
IDEMPOTENCY_KEY = "projection:fixture.projection-adapter-v0-2:deliver:0001"


class ProjectionDeliveryTests(unittest.TestCase):

    def _base_case(self) -> dict:
        return {
            "idempotency_key": IDEMPOTENCY_KEY,
            "projection": {
                "object_key": OBJECT_KEY,
                "authority_class": "projection",
                "platforms": ["drive", "airtable", "notion"],
            },
            "prior_receipts": [],
        }

    def test_fresh_delivery_claims_projection(self):
        result = evaluate_fixture("projection_delivery", self._base_case())
        self.assertEqual("claim_projection_delivery", result["action"])
        self.assertFalse(result["duplicate"])
        self.assertEqual(["drive", "airtable", "notion"], result["platforms"])

    def test_authority_class_is_projection_not_canon(self):
        """No projection edit may become Canon."""
        result = evaluate_fixture("projection_delivery", self._base_case())
        for receipt in result["receipts"]:
            self.assertEqual("projection", receipt["authority_class"])

    def test_receipts_are_immutable(self):
        """Every state change has an immutable receipt."""
        result = evaluate_fixture("projection_delivery", self._base_case())
        for receipt in result["receipts"]:
            self.assertTrue(receipt["immutable"])

    def test_idempotency_key_on_each_receipt(self):
        result = evaluate_fixture("projection_delivery", self._base_case())
        for receipt in result["receipts"]:
            self.assertEqual(IDEMPOTENCY_KEY, receipt["idempotency_key"])

    def test_duplicate_idempotency_key_skipped(self):
        """Same idempotency key must not produce a duplicate mutation."""
        case = self._base_case()
        case["prior_receipts"] = [{"idempotency_key": IDEMPOTENCY_KEY, "status": "delivered"}]
        result = evaluate_fixture("projection_delivery", case)
        self.assertEqual("skip_duplicate_delivery", result["action"])
        self.assertTrue(result["duplicate"])
        self.assertIsNone(result["receipt"])

    def test_eval_case_scp012(self):
        case = load("evals/sync-control-plane/cases/SCP-012.json")
        result = evaluate_fixture("projection_delivery", case)
        self.assertEqual("claim_projection_delivery", result["action"])

    def test_eval_case_scp013(self):
        case = load("evals/sync-control-plane/cases/SCP-013.json")
        result = evaluate_fixture("projection_delivery", case)
        self.assertEqual("skip_duplicate_delivery", result["action"])


class ObserveBindingTests(unittest.TestCase):

    def _binding(self) -> dict:
        return {
            "schema_version": "source-binding.v2",
            "binding_id": "binding.notion.fixture-projection-adapter-v0-2",
            "object_key": OBJECT_KEY,
            "platform": "notion",
            "external_id": "fixture-notion",
            "authority_class": "projection",
            "sync_direction": "push",
            "state": "active",
            "freshness": {"status": "fresh"},
        }

    def test_consistent_binding_is_stable(self):
        case = {
            "expected_hash": "a" * 64,
            "observed_hash": "a" * 64,
            "binding": self._binding(),
        }
        result = evaluate_fixture("observe_binding", case)
        self.assertEqual("binding_consistent", result["action"])
        self.assertFalse(result["drift_detected"])

    def test_drift_marks_binding_not_silently_repaired(self):
        """Drift must not be silently repaired."""
        case = {
            "expected_hash": "a" * 64,
            "observed_hash": "b" * 64,
            "binding": self._binding(),
        }
        result = evaluate_fixture("observe_binding", case)
        self.assertEqual("mark_drift_and_propose_reconciliation", result["action"])
        self.assertTrue(result["drift_detected"])
        self.assertFalse(result["silent_repair_attempted"])

    def test_drift_emits_typed_proposed_move(self):
        case = {
            "expected_hash": "a" * 64,
            "observed_hash": "b" * 64,
            "binding": self._binding(),
        }
        result = evaluate_fixture("observe_binding", case)
        pm = result["proposed_move"]
        self.assertEqual("proposed-move.v1", pm["schema_version"])
        self.assertEqual("migration", pm["lane"])
        self.assertEqual("new", pm["disposition"])
        self.assertFalse(pm["blocks_merge"])

    def test_drift_binding_state_recorded(self):
        case = {
            "expected_hash": "a" * 64,
            "observed_hash": "b" * 64,
            "binding": self._binding(),
        }
        result = evaluate_fixture("observe_binding", case)
        self.assertEqual("drifted", result["binding_state"])

    def test_eval_case_scp014(self):
        case = load("evals/sync-control-plane/cases/SCP-014.json")
        result = evaluate_fixture("observe_binding", case)
        self.assertEqual("mark_drift_and_propose_reconciliation", result["action"])


class RetryDeliveryTests(unittest.TestCase):

    def _attempts(self, n: int) -> list:
        return [
            {
                "attempt": i + 1,
                "status": "failed",
                "error": "connection_timeout",
                "attempted_at": f"2026-08-12T01:0{i}:00Z",
            }
            for i in range(n)
        ]

    def test_below_max_returns_retry(self):
        case = {
            "idempotency_key": "delivery:test:0001",
            "attempts": self._attempts(3),
        }
        result = evaluate_fixture("retry_delivery", case)
        self.assertEqual("retry_delivery", result["action"])
        self.assertFalse(result["dead_lettered"])

    def test_at_max_returns_dead_letter(self):
        """After 5 attempts the delivery must be dead-lettered."""
        case = {
            "idempotency_key": "delivery:test:0002",
            "attempts": self._attempts(5),
        }
        result = evaluate_fixture("retry_delivery", case)
        self.assertEqual("dead_letter_delivery", result["action"])
        self.assertTrue(result["dead_lettered"])
        self.assertEqual(5, result["attempt_count"])

    def test_retry_timing_is_inspectable(self):
        """Retry timing and compensation must be inspectable."""
        case = {
            "idempotency_key": "delivery:test:0003",
            "attempts": self._attempts(5),
        }
        result = evaluate_fixture("retry_delivery", case)
        self.assertTrue(result["retry_timing_inspectable"])
        self.assertTrue(result["compensation_inspectable"])

    def test_evidence_is_preserved(self):
        case = {
            "idempotency_key": "delivery:test:0004",
            "attempts": self._attempts(5),
        }
        result = evaluate_fixture("retry_delivery", case)
        self.assertEqual(5, len(result["preserved_evidence"]))
        for evidence in result["preserved_evidence"]:
            self.assertTrue(evidence["immutable"])

    def test_eval_case_scp015(self):
        case = load("evals/sync-control-plane/cases/SCP-015.json")
        result = evaluate_fixture("retry_delivery", case)
        self.assertEqual("dead_letter_delivery", result["action"])


class ReconstructProjectionTests(unittest.TestCase):

    def test_reconstruction_from_consistent_state(self):
        case = {
            "object_key": OBJECT_KEY,
            "git_state": {"content_hash": "c" * 64},
            "supabase_state": {"content_hash": "c" * 64},
        }
        result = evaluate_fixture("reconstruct_projection", case)
        self.assertEqual("reconstruct_projection_from_git_and_supabase", result["action"])
        self.assertTrue(result["reconstructed"])
        self.assertTrue(result["state_consistent"])

    def test_no_existing_user_content_altered(self):
        """Reconstruction must not alter existing user content."""
        case = {
            "object_key": OBJECT_KEY,
            "git_state": {"content_hash": "c" * 64},
            "supabase_state": {"content_hash": "c" * 64},
        }
        result = evaluate_fixture("reconstruct_projection", case)
        self.assertFalse(result["existing_user_content_altered"])

    def test_blast_radius_is_one_object(self):
        """Blast radius must be exactly one fixture object."""
        case = {
            "object_key": OBJECT_KEY,
            "git_state": {"content_hash": "c" * 64},
            "supabase_state": {"content_hash": "c" * 64},
        }
        result = evaluate_fixture("reconstruct_projection", case)
        self.assertEqual([OBJECT_KEY], result["blast_radius"])

    def test_inconsistent_state_is_flagged(self):
        case = {
            "object_key": OBJECT_KEY,
            "git_state": {"content_hash": "a" * 64},
            "supabase_state": {"content_hash": "b" * 64},
        }
        result = evaluate_fixture("reconstruct_projection", case)
        self.assertFalse(result["state_consistent"])

    def test_eval_case_scp016(self):
        case = load("evals/sync-control-plane/cases/SCP-016.json")
        result = evaluate_fixture("reconstruct_projection", case)
        self.assertEqual("reconstruct_projection_from_git_and_supabase", result["action"])


if __name__ == "__main__":
    unittest.main()
