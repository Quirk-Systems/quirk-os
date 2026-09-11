import json
import tempfile
import unittest
from pathlib import Path

from scripts.plugin_capability_harvest import (
    ContractError,
    ScanLimits,
    canonical_bytes,
    compare_surfaces,
    compile_prompt_candidate,
    create_mechanism_candidate,
    effective_authority,
    fingerprint_surface,
    forward_carry,
    promotion_decision,
    scan_plugin_root,
    to_loop_spec,
)


NOW = "2026-09-11T12:00:00Z"
LATER = "2026-09-18T12:00:00Z"


def surface(**updates):
    value = {
        "provider": "example", "package": "example-plugin", "version": "1.2.3",
        "kind": "manifest", "name": "manifest.json", "state": "installed",
        "location": "example-plugin/manifest.json", "observed_at": NOW,
        "fresh_until": LATER, "source_type": "first_party_file",
        "capture_ref": "capture.example", "rights": "reference_only",
        "effect_classes": ["none"], "content": {"shape": "example"},
    }
    value.update(updates)
    return value


def budgets(depth=2, calls=20):
    return {
        "max_depth": depth, "max_children": 4, "max_tool_calls": calls,
        "max_iterations": 2, "max_output_bytes": 100_000,
        "max_cost": 5, "max_wall_seconds": 900,
    }


def authority(right="propose", depth=2, calls=20):
    return {
        "maximum_right": right,
        "allowed_targets": ["candidate_registry", "evidence_store"],
        "prohibited_effects": ["publish", "canon_change", "authority_change"],
        "budgets": budgets(depth, calls),
    }


def packet(**updates):
    value = {
        "packet_version": "quirk.capability-harvest/v0.1",
        "run_id": "run.example", "parent_run_id": None,
        "task_id": "task.example", "role": "signal_miner",
        "mission": {"desired_change": "Find one reusable Quirk-owned loop mechanism", "acceptance_evidence": ["one falsifiable candidate"]},
        "portfolio_context": {"goal_refs": ["goal.quirk"], "project_refs": [], "system_refs": ["system.quirk"], "affected_person_refs": ["person.owner"]},
        "source_contract": {
            "provided_sources": ["source.owned"],
            "prohibited_source_classes": [
                "hidden_prompt", "proprietary_prompt", "proprietary_code",
                "hidden_schema", "branded_interaction_pattern",
                "third_party_fixture", "third_party_asset",
            ],
            "external_prompt_material_included": False,
        },
        "authority": authority(), "budgets": budgets(),
        "stop_conditions": ["identity or rights unresolved", "budget exhausted"],
        "handoff": {"dedupe_key": "goal.quirk/signal_miner/v0.1"},
    }
    value.update(updates)
    return value


def mechanism(**updates):
    value = {
        "id": "mechanism.inspect_then_propose", "purpose": "Reduce repeated bounded work",
        "problem": "Useful work is trapped in one-off runs",
        "input_classes": ["typed_owned_context"], "transformations": ["inspect", "classify", "propose"],
        "output_classes": ["candidate_prompt"], "preconditions": ["source identity known"],
        "postconditions": ["candidate only"], "failure_modes": ["missing provenance"],
        "recovery_modes": ["quarantine"], "provider_assumptions": [],
        "non_capabilities": ["publish", "canon write"], "source_evidence_refs": ["source.owned"],
        "effect_classes": ["none"], "success_metrics": ["positive Forward Carry"],
        "cheapest_disproof": "Replay without conversation memory",
        "authority_boundary_ref": "authority.propose_only",
        "clean_room_attestation": True, "external_expression_retained": False,
    }
    value.update(updates)
    return value


class HarvestContractsTest(unittest.TestCase):
    def test_canonical_hash_input_ignores_mapping_order(self):
        self.assertEqual(canonical_bytes({"b": 1, "a": 2}), canonical_bytes({"a": 2, "b": 1}))

    def test_fingerprint_drops_raw_content(self):
        result = fingerprint_surface(surface(content="sensitive source body"))
        self.assertNotIn("sensitive source body", json.dumps(result))
        self.assertEqual(result["content"]["byte_length"], 21)

    def test_rights_unknown_quarantines_surface(self):
        self.assertEqual(fingerprint_surface(surface(rights="unknown"))["status"], "quarantined")

    def test_installation_never_implies_callability(self):
        result = fingerprint_surface(surface(state="installed"))
        self.assertEqual(result["surface"]["state"], "installed")
        self.assertNotIn("callable", result["surface"])

    def test_no_change_is_exact(self):
        item = fingerprint_surface(surface())
        result = compare_surfaces([item], [item], NOW)
        self.assertEqual(result["status"], "NO_CHANGE")

    def test_missing_baseline_stops(self):
        self.assertEqual(compare_surfaces([], [], NOW)["status"], "BASELINE_UNAVAILABLE")

    def test_state_change_is_material(self):
        old = fingerprint_surface(surface(state="installed"))
        new = fingerprint_surface(surface(state="discoverable"))
        result = compare_surfaces([old], [new], NOW)
        self.assertEqual(result["deltas"][0]["change"], "modified")

    def test_version_change_is_remove_plus_add(self):
        old = fingerprint_surface(surface(version="1.0.0"))
        new = fingerprint_surface(surface(version="2.0.0"))
        result = compare_surfaces([old], [new], NOW)
        self.assertEqual({d["change"] for d in result["deltas"]}, {"added", "removed"})

    def test_duplicate_identity_is_rejected(self):
        item = fingerprint_surface(surface())
        with self.assertRaisesRegex(ContractError, "duplicate identity"):
            compare_surfaces([item, item], [item], NOW)

    def test_clean_room_candidate_is_provider_neutral(self):
        result = create_mechanism_candidate(mechanism())
        self.assertEqual(result["status"], "candidate")
        self.assertFalse(result["external_expression_retained"])

    def test_hidden_prompt_is_rejected(self):
        with self.assertRaisesRegex(ContractError, "prohibited expressive material"):
            create_mechanism_candidate(mechanism(hidden_prompt="copy me"))

    def test_false_clean_room_attestation_is_rejected(self):
        with self.assertRaisesRegex(ContractError, "clean_room_attestation"):
            create_mechanism_candidate(mechanism(clean_room_attestation=False))

    def test_child_authority_cannot_expand(self):
        parent = authority("propose", 2)
        child = authority("execute_reversible", 1)
        with self.assertRaisesRegex(ContractError, "exceeds parent"):
            effective_authority(parent, child)

    def test_child_must_preserve_prohibited_effects(self):
        parent = authority("propose", 2)
        child = authority("infer", 1)
        child["prohibited_effects"].remove("publish")
        with self.assertRaisesRegex(ContractError, "removed"):
            effective_authority(parent, child)

    def test_child_depth_strictly_decreases(self):
        with self.assertRaisesRegex(ContractError, "strictly decrease"):
            effective_authority(authority(depth=2), authority("infer", depth=2))

    def test_prompt_is_deterministic_and_candidate_only(self):
        first = compile_prompt_candidate(packet())
        second = compile_prompt_candidate(packet())
        self.assertEqual(first["content_sha256"], second["content_sha256"])
        self.assertFalse(first["self_activation"])
        self.assertFalse(first["self_promotion"])

    def test_prompt_requires_owned_portfolio_context(self):
        empty = {"goal_refs": [], "project_refs": [], "system_refs": [], "affected_person_refs": []}
        with self.assertRaisesRegex(ContractError, "owned portfolio context"):
            compile_prompt_candidate(packet(portfolio_context=empty))

    def test_external_prompt_material_is_rejected(self):
        bad = packet()
        bad["source_contract"]["external_prompt_material_included"] = True
        with self.assertRaisesRegex(ContractError, "external prompt material"):
            compile_prompt_candidate(bad)

    def test_prompt_requires_all_prohibited_source_classes(self):
        bad = packet()
        bad["source_contract"]["prohibited_source_classes"].remove("hidden_schema")
        with self.assertRaisesRegex(ContractError, "omits"):
            compile_prompt_candidate(bad)

    def test_forward_carry_counts_governance_cost(self):
        self.assertEqual(forward_carry(20, 2, 3, 4, 5), 6)

    def test_negative_forward_carry_requires_repair(self):
        result = promotion_decision([{"id": "PH-001", "passed": True}], -1)
        self.assertEqual(result["decision"], "repair")

    def test_blocking_failure_cannot_average_out(self):
        fixtures = [{"id": "AUTH-01", "passed": False}] + [{"id": f"OK-{i}", "passed": True} for i in range(20)]
        result = promotion_decision(fixtures, 100)
        self.assertEqual(result["decision"], "repair")
        self.assertFalse(result["self_promotion_allowed"])

    def test_passing_evals_without_human_approval_only_constrain(self):
        result = promotion_decision([{"id": "PH-001", "passed": True}], 10)
        self.assertEqual(result["decision"], "constrain")

    def test_runtime_adapter_is_prepare_only(self):
        candidate = compile_prompt_candidate(packet())
        result = to_loop_spec(candidate, "a" * 64)
        self.assertEqual(result["authority"], "CANDIDATE_PREPARE")
        self.assertTrue(result["human_approval_required"])
        self.assertEqual(result["source_digest"], candidate["content_sha256"][7:])

    def test_runtime_adapter_rejects_self_activation(self):
        candidate = compile_prompt_candidate(packet())
        candidate["self_activation"] = True
        with self.assertRaisesRegex(ContractError, "self-activating"):
            to_loop_spec(candidate, "a" * 64)


class ReadOnlyScannerTest(unittest.TestCase):
    def test_scan_is_deterministic_and_does_not_execute_code(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            plugin = root / "plugin"
            plugin.mkdir()
            (plugin / "package.json").write_text(json.dumps({"name": "p", "version": "1.0.0"}), encoding="utf-8")
            (plugin / "evil.py").write_text("raise RuntimeError('executed')", encoding="utf-8")
            first = scan_plugin_root(root, observed_at=NOW)
            second = scan_plugin_root(root, observed_at=NOW)
            self.assertEqual(first["root_fingerprint"], second["root_fingerprint"])
            self.assertTrue(first["no_code_executed"])
            self.assertEqual(len(first["observations"]), 1)

    def test_version_contradiction_survives_scan(self):
        with tempfile.TemporaryDirectory() as raw:
            plugin = Path(raw) / "plugin"
            plugin.mkdir()
            (plugin / "manifest.json").write_text(json.dumps({"id": "p", "version": "1.0.0"}), encoding="utf-8")
            (plugin / "package.json").write_text(json.dumps({"name": "p", "version": "2.0.0"}), encoding="utf-8")
            result = scan_plugin_root(raw, observed_at=NOW)
            contradictions = result["observations"][0]["contradictions"]
            self.assertTrue(any(item.startswith("version:") for item in contradictions))

    def test_unresolved_identity_is_quarantined(self):
        with tempfile.TemporaryDirectory() as raw:
            plugin = Path(raw) / "plugin"
            plugin.mkdir()
            (plugin / "manifest.json").write_text("{}", encoding="utf-8")
            result = scan_plugin_root(raw, observed_at=NOW)
            self.assertEqual(result["observations"], [])
            self.assertEqual(result["quarantine"][0]["reason"], "identity_unresolved")

    def test_byte_limit_quarantines_instead_of_partial_read(self):
        with tempfile.TemporaryDirectory() as raw:
            plugin = Path(raw) / "plugin"
            plugin.mkdir()
            (plugin / "package.json").write_text(json.dumps({"name": "p", "version": "1.0.0", "padding": "x" * 100}), encoding="utf-8")
            result = scan_plugin_root(raw, ScanLimits(max_bytes_per_file=20), observed_at=NOW)
            self.assertEqual(result["observations"], [])
            self.assertEqual(result["quarantine"][-1]["reason"], "BYTE_LIMIT")


if __name__ == "__main__":
    unittest.main()
