import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.run_engineering_pilot import run_pilot, plan_revalidation


def source():
    return {"candidate_id": "candidate.runtime-pr2", "source_url": "https://github.com/Quirk-Systems/quirk-run/pull/2",
            "head_sha": "850e5718377751d40cff68cde2db7c943b4b7e6b", "observed_at": "2026-09-10T07:00:00Z",
            "reported_build": "passed", "reported_behavior": "not_proven", "authority": "PREPARE"}


class PilotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)

    def test_real_pointer_input_becomes_observed_local_candidate(self):
        result = run_pilot(source(), self.path, now="2026-09-10T08:00:00Z")
        self.assertEqual(result["loop"]["status"], "REVIEW_READY")
        self.assertEqual(result["action_receipt"]["status"], "VERIFIED")
        self.assertIn("behavioral", result["loop"]["candidate"]["next_proof"])
        self.assertIsNone(result["loop"]["human_usefulness"])
        self.assertEqual(result["graph_support"]["supports"], [])
        self.assertEqual(result["admission_effect"], "none")

    def test_rerun_reuses_recorded_action(self):
        first = run_pilot(source(), self.path, now="2026-09-10T08:00:00Z")
        second = run_pilot(source(), self.path, now="2026-09-10T08:01:00Z")
        self.assertEqual(first["loop"]["run_id"], second["loop"]["run_id"])
        self.assertEqual(first["action_receipt"]["action_sha256"], second["action_receipt"]["action_sha256"])
        self.assertEqual(second["action_event_count"], 2)

    def test_source_change_gets_new_run_and_marks_old_evidence_stale(self):
        first = run_pilot(source(), self.path, now="2026-09-10T08:00:00Z")
        changed = source(); changed["head_sha"] = "f" * 40
        second = run_pilot(changed, self.path, now="2026-09-10T08:01:00Z")
        self.assertNotEqual(first["loop"]["run_id"], second["loop"]["run_id"])
        self.assertIn("candidate.runtime-pr2", [x["object_id"] for x in second["revalidation"]["affected"]])

    def test_reported_build_success_never_becomes_behavior_proof(self):
        result = run_pilot(source(), self.path, now="2026-09-10T08:00:00Z")
        self.assertEqual(result["loop"]["candidate"]["behavioral_proof"], "not_observed")

    def test_authority_increase_is_not_silently_normalized(self):
        changed = source(); changed["authority"] = "PUBLISH"
        with self.assertRaisesRegex(ValueError, "authority"):
            run_pilot(changed, self.path, now="2026-09-10T08:00:00Z")

    def test_source_cannot_supply_grant_or_raw_secret(self):
        changed = source(); changed["grant"] = {"decision": "approved"}
        with self.assertRaisesRegex(ValueError, "unknown"):
            run_pilot(changed, self.path, now="2026-09-10T08:00:00Z")

    def test_source_url_rejects_controls_ports_and_noncanonical_paths(self):
        for suffix in ("\nAuthorization: Bearer SECRET_TEST", "%0Asecret", "/files", "?token=secret"):
            with self.subTest(suffix=suffix):
                changed = source(); changed["source_url"] += suffix
                with self.assertRaises(ValueError):
                    run_pilot(changed, self.path, now="2026-09-10T08:00:00Z")
        changed = source(); changed["source_url"] = "https://github.com:443/Quirk-Systems/quirk-run/pull/2"
        with self.assertRaises(ValueError):
            run_pilot(changed, self.path, now="2026-09-10T08:00:00Z")
        self.assertEqual(list(self.path.iterdir()), [])

    def test_expired_grant_pauses_current_reuse_and_preserves_history(self):
        first = run_pilot(source(), self.path, now="2026-09-10T08:00:00Z")
        second = run_pilot(source(), self.path, now="2026-09-10T10:00:00Z")
        self.assertEqual(second["status"], "PAUSED_AUTHORITY_CHANGE")
        self.assertFalse(second["current_applicability"]["applicable"])
        self.assertEqual(second["loop"], first["loop"])
        self.assertEqual(second["action_receipt"], first["action_receipt"])
        self.assertEqual(second["action_event_count"], 2)

    def test_changed_host_grant_pauses_current_reuse(self):
        first = run_pilot(source(), self.path, now="2026-09-10T08:00:00Z")
        path = next(self.path.glob("*.host-fixture-grant.json"))
        grant = json.loads(path.read_text()); grant["target"] = "resource.unrelated"
        path.write_text(json.dumps(grant))
        second = run_pilot(source(), self.path, now="2026-09-10T08:01:00Z")
        self.assertEqual(second["status"], "PAUSED_AUTHORITY_CHANGE")
        self.assertFalse(second["current_applicability"]["applicable"])
        self.assertEqual(second["action_receipt"], first["action_receipt"])


if __name__ == "__main__":
    unittest.main()
