from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_quirk_arcade_receipt_run as validator
from quirk_arcade.simulation import (
    ContractError,
    EffectKind,
    EffectState,
    Phase,
    canonical_bytes,
    command_from_data,
    digest,
    policy_from_data,
    replay_matches,
    run_fixture,
)


def load_json(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class QuirkArcadeReceiptRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cabinet = load_json(validator.CABINET_PATH)
        cls.activation = load_json(validator.ACTIVATION_PATH)
        cls.manifest = load_json(validator.FIXTURE_MANIFEST_PATH)
        cls.fixture = load_json(cls.manifest["fixture_path"])
        cls.golden = load_json(validator.GOLDEN_TRACE_PATH)
        cls.lock = load_json(cls.cabinet["dependency_lock_ref"])
        cls.trace, cls.final, cls.commands, cls.policy = run_fixture(
            cls.fixture, cls.cabinet
        )

    def test_cabinet_and_activation_are_schema_valid(self):
        cabinet_schema = load_json(validator.CABINET_SCHEMA_PATH)
        activation_schema = load_json(validator.ACTIVATION_SCHEMA_PATH)
        Draft202012Validator.check_schema(cabinet_schema)
        self.assertEqual(validator.schema_errors(self.cabinet, cabinet_schema), [])
        self.assertEqual(validator.schema_errors(self.activation, activation_schema), [])

    def test_dependency_lock_binds_exact_parent_contracts(self):
        passed, errors = validator.dependency_lock_matches(
            repo=ROOT, cabinet=self.cabinet, lock=self.lock
        )
        self.assertTrue(passed, errors)
        self.assertEqual(
            self.lock["activation_parent_sha"],
            "381a2df04f6c1986f9d921459bdfbdeb869d2e8c",
        )
        self.assertEqual(len(self.lock["imports"]), 7)

    def test_dependency_lock_rejects_repository_base_role_path_and_url_drift(self):
        mutations = []
        repository = deepcopy(self.lock)
        repository["repository"] = "Quirk-Systems/lookalike"
        mutations.append(repository)
        base = deepcopy(self.lock)
        base["repository_base_sha"] = "0" * 40
        mutations.append(base)
        role = deepcopy(self.lock)
        role["imports"][0]["contract_role"] = "lookalike"
        mutations.append(role)
        path = deepcopy(self.lock)
        path["imports"][0]["path"] = "schemas/asset.schema.json"
        mutations.append(path)
        url = deepcopy(self.lock)
        url["imports"][0]["source_url"] = "https://example.com/lookalike.json"
        mutations.append(url)
        status = deepcopy(self.lock)
        status["status"] = "ADMITTED"
        mutations.append(status)
        authority = deepcopy(self.lock)
        authority["authority_effect"] = "expanded"
        mutations.append(authority)
        for mutated in mutations:
            passed, errors = validator.dependency_lock_matches(
                repo=ROOT, cabinet=self.cabinet, lock=mutated
            )
            self.assertFalse(passed)
            self.assertTrue(errors)

    def test_game_loop_reaches_candidate_complete_through_all_phases(self):
        self.assertEqual(self.final.phase, Phase.CANDIDATE_COMPLETE)
        self.assertEqual(
            self.trace["phase_trace"],
            [
                "setup",
                "observe",
                "shape",
                "test",
                "test",
                "test",
                "test",
                "test",
                "test",
                "receipt",
                "candidate_complete",
            ],
        )

    def test_each_protected_effect_is_denied_without_mutation(self):
        attempts = self.trace["effect_attempts"]
        attempted = {
            effect for attempt in attempts for effect in attempt["effect_kinds"]
        }
        self.assertEqual(attempted, {effect.value for effect in EffectKind})
        self.assertTrue(all(attempt["decision"] == "DENY" for attempt in attempts))
        self.assertEqual(self.final.effects, EffectState())
        self.assertEqual(self.trace["continuity"]["external_effects_completed"], 0)

    def test_composite_card_is_denied_atomically(self):
        composite = next(
            attempt
            for attempt in self.trace["effect_attempts"]
            if attempt["command_id"] == "command.cosplay.008.composite"
        )
        self.assertEqual(composite["decision"], "DENY")
        self.assertEqual(set(composite["effect_kinds"]), {e.value for e in EffectKind})
        event = next(
            event
            for event in self.trace["events"]
            if event["command_id"] == composite["command_id"]
        )
        self.assertEqual(event["pre_effect_digest"], event["post_effect_digest"])
        self.assertEqual(len(event["reason_codes"]), 4)

    def test_event_chain_binds_order_and_contents(self):
        previous = None
        for event in self.trace["events"]:
            self.assertEqual(event["previous_event_digest"], previous)
            body = dict(event)
            expected = body.pop("event_digest")
            self.assertEqual(digest(body), expected)
            previous = expected
        body = dict(self.trace)
        expected = body.pop("trace_record_digest")
        self.assertEqual(digest(body), expected)

    def test_golden_trace_replays_byte_identically(self):
        self.assertEqual(canonical_bytes(self.trace), canonical_bytes(self.golden))
        self.assertTrue(replay_matches(self.fixture, self.cabinet, self.golden))

    def test_player_action_no_op_ablation_fails_lineage(self):
        outcome = validator.no_op_ablation(
            fixture=self.fixture,
            cabinet=self.cabinet,
            commands=self.commands,
            policy=self.policy,
        )
        self.assertEqual(outcome, Phase.FAILED_LINEAGE)
        self.assertNotEqual(outcome, self.final.phase)

    def test_policy_cannot_drop_one_protected_effect(self):
        mutated = deepcopy(self.fixture["policy"])
        mutated["prohibited_effects"].remove("PUBLISH_EXTERNAL")
        with self.assertRaises(ContractError):
            policy_from_data(mutated)

    def test_unknown_permission_or_secret_material_fails_closed(self):
        unknown = deepcopy(self.fixture["commands"][3])
        unknown["permissions"] = ["deploy.write"]
        with self.assertRaises(ContractError):
            command_from_data(unknown)

        secret = deepcopy(self.fixture["commands"][5])
        secret["effects"][0]["target_ref"] = "raw-secret-not-a-reference"
        with self.assertRaises(ContractError):
            command_from_data(secret)

    def test_command_tamper_breaks_replay(self):
        mutated = deepcopy(self.fixture)
        mutated["commands"][7]["card_ref"] = "hostile-card.changed-after-review"
        self.assertFalse(replay_matches(mutated, self.cabinet, self.golden))

    def test_policy_tamper_is_rejected_before_execution(self):
        mutated = deepcopy(self.fixture)
        mutated["policy"]["maximum_right"] = "execute_protected"
        with self.assertRaises(ContractError):
            run_fixture(mutated, self.cabinet)

        for field in (
            "cards_cannot_expand_authority",
            "representations_cannot_expand_authority",
            "local_only",
        ):
            string_boolean = deepcopy(self.fixture)
            string_boolean["policy"][field] = "false"
            with self.assertRaises(ContractError):
                run_fixture(string_boolean, self.cabinet)

    def test_command_identifiers_must_be_unique(self):
        mutated = deepcopy(self.fixture)
        mutated["commands"][1]["command_id"] = mutated["commands"][0]["command_id"]
        with self.assertRaises(ContractError):
            run_fixture(mutated, self.cabinet)

    def test_authorization_is_bound_but_explicitly_unverified(self):
        self.assertFalse(self.trace["authority"]["verified_external_grant"])
        self.assertNotIn("grant_ref", self.trace["authority"])
        self.assertIn("verified external authority grant", self.trace["claims_withheld"])
        mutated = deepcopy(self.fixture)
        mutated["policy"]["authorization_assertion_ref"] = "authority.self-asserted.root"
        with self.assertRaises(ContractError):
            run_fixture(mutated, self.cabinet)

    def test_cabinet_tamper_breaks_replay_binding(self):
        mutated = deepcopy(self.cabinet)
        mutated["title"] = "Receipt Run, rewritten after review"
        self.assertFalse(replay_matches(self.fixture, mutated, self.golden))

    def test_representational_sources_never_become_controllers_or_grants(self):
        identities = self.cabinet["identity_model"]
        self.assertEqual(identities["active_agent_refs"], [])
        self.assertFalse(identities["authority_inheritance"])
        self.assertTrue(
            all(item["authority_effect"] == "none" for item in identities["representational_sources"])
        )
        self.assertTrue(
            all(item["may_hold_grant"] is False for item in identities["representational_sources"])
        )
        self.assertTrue(
            all(event["controller_ref"] == "human.bryan" for event in self.trace["events"])
        )

    def test_unbound_or_mislabeled_identity_source_fails_closed(self):
        unbound = deepcopy(self.fixture)
        unbound["commands"][3]["source_ref"] = "character.unbound-admin"
        with self.assertRaises(ContractError):
            run_fixture(unbound, self.cabinet)

        mislabeled = deepcopy(self.fixture)
        mislabeled["commands"][3]["source_kind"] = "familiar"
        with self.assertRaises(ContractError):
            run_fixture(mislabeled, self.cabinet)

        controller_drift = deepcopy(self.cabinet)
        controller_drift["identity_model"]["representational_sources"][0][
            "controller_ref"
        ] = "human.other"
        with self.assertRaises(ContractError):
            run_fixture(self.fixture, controller_drift)

    def test_provider_bindings_are_projection_only_or_deferred(self):
        providers = self.cabinet["provider_bindings"]
        self.assertEqual({item["provider"] for item in providers}, validator.EXPECTED_PROVIDER_SET)
        self.assertEqual(
            {item["provider"]: item["binding_state"] for item in providers},
            validator.EXPECTED_PROVIDER_STATES,
        )
        self.assertTrue(all(item["canonical"] is False for item in providers))
        self.assertTrue(all(item["authority_effect"] == "none" for item in providers))
        self.assertTrue(
            all(
                item["binding_state"] != "source_only" or item["provider"] == "github"
                for item in providers
            )
        )
        mutated = deepcopy(self.cabinet)
        next(
            item for item in mutated["provider_bindings"] if item["provider"] == "supabase"
        )["binding_state"] = "source_only"
        self.assertTrue(validator.provider_binding_errors(mutated))

    def test_terminal_vocabulary_contains_no_authority_state(self):
        terminals = self.cabinet["play_spec"]["terminal_states"]
        self.assertEqual(terminals, validator.EXPECTED_TERMINALS)
        self.assertFalse(set(terminals) & validator.FORBIDDEN_LIFECYCLE_WORDS)
        self.assertEqual(self.trace["object_lifecycle"], "CANDIDATE")
        self.assertEqual(self.trace["canon_state"], "NOT_PROMOTED")

    def test_playspec_transition_graph_cannot_diverge_from_reducer(self):
        mutated = deepcopy(self.cabinet)
        mutated["play_spec"]["legal_transitions"][0] = {
            "from": "setup",
            "verb": "finalize_candidate",
            "to": "candidate_complete",
        }
        cabinet_schema = load_json(validator.CABINET_SCHEMA_PATH)
        self.assertTrue(validator.schema_errors(mutated, cabinet_schema))
        with self.assertRaises(ContractError):
            run_fixture(self.fixture, mutated)

    def test_activation_is_cross_bound_to_cabinet(self):
        mutations = []
        activation_id = deepcopy(self.activation)
        activation_id["activation_id"] = "activation.lookalike"
        mutations.append(activation_id)
        plane = deepcopy(self.activation)
        plane["world_route"]["plane"] = "Work"
        mutations.append(plane)
        location = deepcopy(self.activation)
        location["world_route"]["location"] = "Quirk Workshop"
        mutations.append(location)
        activation_format = deepcopy(self.activation)
        activation_format["activation_format"] = "dispatch"
        mutations.append(activation_format)
        effect_class = deepcopy(self.activation)
        effect_class["rules_and_gates"]["effect_class"] = "READ"
        mutations.append(effect_class)
        human_authority = deepcopy(self.activation)
        human_authority["human_gate"]["publisher"] = "agent.self"
        mutations.append(human_authority)
        for mutated in mutations:
            self.assertTrue(validator.activation_binding_errors(self.cabinet, mutated))

    def test_fixture_oracle_fields_cannot_be_relabelled(self):
        self.assertEqual(
            validator.fixture_expectation_errors(self.fixture["expected"]), []
        )
        mutations = []
        denied = deepcopy(self.fixture["expected"])
        denied["denied_effects"] = []
        mutations.append(denied)
        ablation = deepcopy(self.fixture["expected"])
        ablation["no_op_ablation_outcome"] = "candidate_complete"
        mutations.append(ablation)
        replay = deepcopy(self.fixture["expected"])
        replay["replay"] = "best_effort"
        mutations.append(replay)
        for mutated in mutations:
            self.assertTrue(validator.fixture_expectation_errors(mutated))

    def test_minimum_fixture_count_is_exact(self):
        mutated = deepcopy(self.cabinet)
        mutated["proof_contract"]["minimum_adversarial_fixtures"] = 100
        cabinet_schema = load_json(validator.CABINET_SCHEMA_PATH)
        self.assertTrue(validator.schema_errors(mutated, cabinet_schema))
        self.assertNotEqual(
            mutated["proof_contract"]["minimum_adversarial_fixtures"],
            len(validator.EXPECTED_ASSURANCE_CASES),
        )

    def test_commands_after_terminal_are_rejected_not_hidden(self):
        mutated = deepcopy(self.fixture)
        extra = deepcopy(mutated["commands"][0])
        extra["command_id"] = "command.cosplay.011.hidden-after-terminal"
        mutated["commands"].append(extra)
        with self.assertRaises(ContractError):
            run_fixture(mutated, self.cabinet)

    def test_assurance_manifest_mapping_and_expected_result_are_immutable(self):
        remapped = deepcopy(self.manifest)
        for case in remapped["cases"]:
            case["evaluator"] = "byte_identical_replay"
        self.assertTrue(validator.assurance_manifest_errors(remapped))

        inverted = deepcopy(self.manifest)
        inverted["cases"][0]["expected"] = "FAIL"
        self.assertTrue(validator.assurance_manifest_errors(inverted))

        relabeled = deepcopy(self.manifest)
        relabeled["suite_id"] = "eval.lookalike"
        self.assertTrue(validator.assurance_manifest_errors(relabeled))

        weakened = deepcopy(self.manifest)
        weakened["critical_failure_policy"] = "average the score"
        self.assertTrue(validator.assurance_manifest_errors(weakened))

    def test_parent_dependency_is_known_permissive_and_remains_unadmitted(self):
        activation_schema = load_json("schemas/quirkverse-activation.schema.json")
        self_declared = deepcopy(self.activation)
        self_declared["status"] = "CANON"
        self_declared["capability_pursuit"]["current_state"] = "CANON"
        self.assertEqual(validator.schema_errors(self_declared, activation_schema), [])

        receipt_schema = load_json("schemas/quirkverse-receipt.schema.json")
        self_reviewed_receipt = {
            "schema_version": "quirk.quirkverse-receipt/0.1",
            "receipt_id": "receipt.activation.parent-permissiveness",
            "activation_ref": "activation.parent-permissiveness",
            "recorded_at": "2026-08-28T00:00:00Z",
            "result_state": "CANON",
            "origin": {"signal_refs": ["source.test"], "initiator": "agent.self"},
            "authority": {
                "grant_ref": "claim.self-asserted",
                "effect_class": "PREPARE",
                "scope_fingerprint": "sha256:" + "0" * 64,
                "scope_delta_state": "UNCHANGED",
            },
            "execution": {
                "artifact_refs": [""],
                "actions_taken": [],
                "stop_conditions_triggered": [],
            },
            "independent_proof": {
                "reviewer": "agent.self",
                "rubric_ref": "rubric.self",
                "fixture_results": [],
                "claims_withheld": [],
            },
            "outcome": {
                "real_world_change": "none",
                "value_evidence": [],
                "harm_or_externality": [],
                "admitted_work": False,
            },
            "disposition": "CANON",
            "final_human_owner": "agent.self",
            "authority_effect": "canon",
        }
        self.assertEqual(
            validator.schema_errors(self_reviewed_receipt, receipt_schema), []
        )

        delta_schema = load_json("schemas/quirkverse-world-state-delta.schema.json")
        agent_delta = {
            "schema_version": "quirk.quirkverse-world-state-delta/0.1",
            "delta_id": "delta.world.parent-permissiveness",
            "activation_ref": "activation.parent-permissiveness",
            "recorded_at": "2026-08-28T00:00:00Z",
            "proof_ref": "claim.agent-self-review",
            "changes": {
                "residents": [],
                "relationships": [],
                "locations": [],
                "storylines": [],
                "capabilities": [],
                "preferences": [],
                "open_world": [],
            },
            "explicit_non_changes": ["No evidence-backed change exists."],
            "reversibility": "irreversible",
            "approved_by": "agent.self",
            "canon_effect": "canon_update",
        }
        self.assertEqual(validator.schema_errors(agent_delta, delta_schema), [])
        self.assertEqual(self.trace["replay"]["independent_review_state"], "NOT_RUN")

    def test_all_ten_assurance_cases_execute_to_pass(self):
        report, _ = validator.evaluate(ROOT)
        self.assertEqual(report["status"], "passed", report["checks"])
        self.assertEqual(len(report["assurance_results"]), 10)
        self.assertTrue(all(item["passed"] for item in report["assurance_results"]))
        self.assertTrue(all(value == 0 for value in report["protected_actions"].values()))

    def test_trace_is_stable_across_python_hash_seeds(self):
        outputs = []
        for seed in ("1", "777"):
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT / "scripts")
            environment["PYTHONHASHSEED"] = seed
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/validate_quirk_arcade_receipt_run.py"),
                    "--repo",
                    str(ROOT),
                    "--print-trace",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=environment,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            outputs.append(result.stdout)
        self.assertEqual(outputs[0], outputs[1])


if __name__ == "__main__":
    unittest.main()
