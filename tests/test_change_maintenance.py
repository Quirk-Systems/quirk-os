import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sync_control_plane.change_maintenance import plan_changes, prepare_marked_update, digest, START, END


def graph():
    def n(key, kind, platform, deps):
        return dict(object_key=key, kind=kind, platform=platform, version="v1", owner="human.bryan",
                    binding_id=key, dependencies=deps, availability="online")
    return [n("goal", "goal", "github", []), n("plan", "plan", "drive", ["goal"]),
            n("agent", "agent", "supabase", ["plan"]), n("view", "projection", "device", ["agent"])]


class ChangeMaintenanceTests(unittest.TestCase):
    def plan(self, nodes=None, **kw):
        return plan_changes(nodes or graph(), dict(object_key="goal", version="v1", disposition="proposed"), **kw)

    def test_cross_provider_transitive_impact_preserves_prerequisites(self):
        result = self.plan()
        self.assertEqual([a["object_key"] for a in result["actions"]], ["goal", "plan", "agent", "view"])
        self.assertEqual(result["actions"][-1]["requires"], ["agent"])
        self.assertFalse(any(a["executable"] for a in result["actions"]))
        self.assertEqual(result["effects_executed"], 0)

    def test_order_independent_and_input_immutable(self):
        g = graph(); before = copy.deepcopy(g)
        self.assertEqual(self.plan(g), self.plan(list(reversed(g))))
        self.assertEqual(g, before)

    def test_dependency_order_overrides_kind_priority(self):
        g = graph(); g[-1]["kind"] = "authority"
        self.assertEqual(self.plan(g)["actions"][-1]["next_gate"], "HUMAN_DECISION")

    def test_old_event_refreshes_source_and_invalidates_keys(self):
        g = graph(); g[0]["version"] = "v2"
        r = self.plan(g)
        self.assertTrue(r["event_version_stale"])
        self.assertTrue(all(a["idempotency_key"] != b["idempotency_key"] for a, b in zip(r["actions"], self.plan()["actions"])))

    def test_duplicate_completion_keys_suppress_only_completed_proposals(self):
        keys = [a["idempotency_key"] for a in self.plan()["actions"]]
        self.assertTrue(all(a["state"] == "unchanged" for a in self.plan(completed_keys=keys)["actions"]))

    def test_offline_and_unknown_propagate_deferral(self):
        for status in ("offline", "unknown"):
            g = graph(); g[1]["availability"] = status
            self.assertEqual([a["state"] for a in self.plan(g)["actions"]], ["proposed", "deferred", "deferred", "deferred"])

    def test_disconnected_unavailable_prerequisite_defers_consumer(self):
        g = graph(); other = copy.deepcopy(g[0]); other.update(object_key="other", binding_id="other", availability="offline")
        g.append(other); g[1]["dependencies"].append("other")
        self.assertEqual(self.plan(g)["actions"][1]["state"], "deferred")

    def test_cycles_missing_dependencies_and_binding_collisions_reject(self):
        for modify in (lambda g: g[0]["dependencies"].append("view"),
                       lambda g: g[1]["dependencies"].append("missing"),
                       lambda g: g.append(copy.deepcopy(g[0]))):
            g = graph(); modify(g)
            with self.assertRaises(ValueError): self.plan(g)
        g = graph(); g[1].update(platform="github", binding_id="goal")
        with self.assertRaises(ValueError): self.plan(g)

    def test_unknown_contract_and_injected_authority_reject(self):
        for modify in (lambda g: g[0].update(approved=True), lambda g: g[0].update(kind="magic"),
                       lambda g: g[0].update(dependencies=[[]])):
            g = graph(); modify(g)
            with self.assertRaises(ValueError): self.plan(g)

    def test_budget_rejects(self):
        with self.assertRaises(ValueError): plan_changes(graph() * 65, {})

    def test_owner_binding_and_transitive_versions_invalidate_deduplication(self):
        baseline = self.plan()
        for field in ("owner", "binding_id", "version"):
            g = graph(); g[1][field] = "new"
            result = self.plan(g)
            self.assertNotEqual(result["actions"][-1]["idempotency_key"], baseline["actions"][-1]["idempotency_key"])

    def test_marked_write_preserves_surrounding_bytes_and_deduplicates(self):
        original = "prefix \n" + START + "\nold\n" + END + "\n suffix  "
        r = prepare_marked_update(original, digest(original), "new")
        self.assertEqual(r["text"], original.replace("\nold\n", "\nnew\n"))
        self.assertEqual(prepare_marked_update(r["text"], digest(r["text"]), "new")["status"], "unchanged")

    def test_concurrent_edit_aborts(self):
        with self.assertRaisesRegex(ValueError, "concurrent"):
            prepare_marked_update("edited", digest("original"), "new")

    def test_ambiguous_markers_never_overwrite(self):
        for s in (START, END, END + START, START + END + START + END):
            with self.assertRaisesRegex(ValueError, "ambiguous"):
                prepare_marked_update(s, digest(s), "new")

    def test_injected_markers_reject(self):
        with self.assertRaises(ValueError): prepare_marked_update("", digest(""), START)

    def test_append_preserves_trailing_whitespace(self):
        s = "original  \n"; r = prepare_marked_update(s, digest(s), "new")
        self.assertTrue(r["text"].startswith(s))


if __name__ == "__main__": unittest.main()
