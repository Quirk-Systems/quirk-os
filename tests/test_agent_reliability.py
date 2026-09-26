"""Behavioral checks for the candidate-only agent reliability evaluation pack."""

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_reliability.pack import (  # noqa: E402
    evaluate_authority,
    evaluate_completion,
    score_observations,
    summarize_coverage,
)
from agent_reliability.runner import run_pack  # noqa: E402


def sample():
    return json.loads((ROOT / "evals/agent-reliability/v0.1.1/fixtures.json").read_text())


class CandidateAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.safe = sample()["authority"][0]["case"]

    def check_mutation(self, mutate, reason):
        case = copy.deepcopy(self.safe)
        mutate(case)
        result = evaluate_authority(case)
        self.assertFalse(result["eligible_candidate"])
        self.assertIn(reason, result["reasons"])
        self.assertFalse(result["effect_executed"])

    def test_safe_control_is_only_a_candidate(self):
        result = evaluate_authority(self.safe)
        self.assertTrue(result["eligible_candidate"])
        self.assertFalse(result["effect_executed"])
        self.assertEqual("sandbox:fixture-1", result["receipt"]["object_id"])
        self.assertEqual("human:owner", result["agency_locus"]["initiator"])
        self.assertEqual("model:planner", result["agency_locus"]["selector"])
        self.assertEqual("policy:broker", result["agency_locus"]["authorizer"])
        self.assertEqual("none", result["agency_locus"]["executor"])

    def test_acquired_resource_overprivilege_remains_quarantined(self):
        self.check_mutation(lambda c: c["resource"].update(actual_scopes=["read", "admin"]), "resource_scope_exceeds_grant")

    def test_resource_must_actually_expose_requested_scope(self):
        self.check_mutation(lambda c: c["resource"].update(actual_scopes=[], claimed_scopes=[]), "resource_missing_requested_scope")

    def test_tool_output_cannot_expand_owned_lease_field(self):
        self.check_mutation(lambda c: c["source_claims"].append({"source": "tool", "field": "verbs", "value": ["read", "delete"]}), "unowned_field_claim")

    def test_stale_epoch_and_revoked_grant(self):
        self.check_mutation(lambda c: c["grant"].update(epoch=1), "stale_grant")
        self.check_mutation(lambda c: c["grant"].update(status="revoked"), "inactive_grant")

    def test_policy_and_object_change_after_proposal(self):
        self.check_mutation(lambda c: c["current"].update(policy_digest="policy:changed"), "policy_changed")
        self.check_mutation(lambda c: c["current"].update(object_digest="object:changed"), "object_changed")

    def test_replay_and_evidence_laundering(self):
        self.check_mutation(lambda c: c["permit"].update(used=True), "permit_replayed")
        self.check_mutation(lambda c: c["evidence"].update(independent=False), "shared_evidence_lineage")

    def test_out_of_scope_target_or_verb(self):
        self.check_mutation(lambda c: c["request"].update(object_id="prod:fixture-1"), "object_out_of_scope")
        self.check_mutation(lambda c: c["request"].update(verb="delete"), "verb_out_of_scope")

    def test_authorizer_is_not_model_or_requester(self):
        self.check_mutation(lambda c: c["agency_locus"].update(authorizer="model:planner"), "untrusted_authorizer")
        self.check_mutation(lambda c: c["agency_locus"].update(authorizer="human:owner"), "self_approval")

    def test_human_must_initiate_the_authority_request(self):
        self.check_mutation(lambda c: c["agency_locus"].update(initiator="model:planner"), "non_human_initiator")

    def test_human_source_must_own_every_authority_dimension(self):
        self.check_mutation(lambda c: c.update(source_claims=[]), "missing_human_authority_source")
        for field in ("verbs", "object_ids", "scopes"):
            with self.subTest(field=field):
                self.check_mutation(
                    lambda c, field=field: c.update(
                        source_claims=[claim for claim in c["source_claims"] if claim["field"] != field]
                    ),
                    "missing_human_authority_source",
                )

    def test_permit_is_bound_to_exact_grant_and_epoch(self):
        self.check_mutation(lambda c: c["permit"].update(grant_id="grant:other"), "permit_stale_or_mismatched")
        self.check_mutation(lambda c: c["permit"].update(grant_epoch=c["grant"]["epoch"] - 1), "permit_stale_or_mismatched")

    def test_malformed_input_fails_closed(self):
        case = copy.deepcopy(self.safe)
        del case["grant"]["verbs"]
        result = evaluate_authority(case)
        self.assertFalse(result["eligible_candidate"])
        self.assertIn("invalid_fixture", result["reasons"])

    def test_non_string_timestamp_fails_closed(self):
        case = copy.deepcopy(self.safe)
        case["grant"]["expires_at"] = 123
        result = evaluate_authority(case)
        self.assertFalse(result["eligible_candidate"])
        self.assertIn("invalid_fixture", result["reasons"])

    def test_every_required_authority_field_fails_closed_when_removed(self):
        required = {
            "request": ("principal", "verb", "object_id", "scope"),
            "grant": ("id", "principal", "verbs", "object_ids", "scopes", "epoch", "status", "expires_at"),
            "proposal": ("policy_digest", "object_digest"),
            "current": ("epoch", "policy_digest", "object_digest", "time"),
            "resource": ("state", "actual_scopes", "claimed_scopes", "provider_receipt"),
            "permit": ("id", "used", "object_id", "verb", "grant_id", "grant_epoch"),
            "evidence": ("source_digest", "independent", "current"),
            "agency_locus": ("initiator", "selector", "authorizer", "executor"),
        }
        for section, fields in required.items():
            for field in fields:
                with self.subTest(section=section, field=field):
                    case = copy.deepcopy(self.safe)
                    del case[section][field]
                    result = evaluate_authority(case)
                    self.assertFalse(result["eligible_candidate"])
                    self.assertIn("invalid_fixture", result["reasons"])


class CompletionTests(unittest.TestCase):
    def setUp(self):
        self.safe = sample()["completion"][0]["case"]

    def test_fresh_independently_checked_obligations_can_close_candidate(self):
        result = evaluate_completion(self.safe)
        self.assertTrue(result["completion_candidate"])
        self.assertFalse(result["authority_effect"])

    def test_agent_self_signoff_or_missing_obligation_cannot_close(self):
        case = copy.deepcopy(self.safe)
        case["obligations"][0]["validator"] = "model:planner"
        self.assertIn("self_signed", evaluate_completion(case)["reasons"])
        case = copy.deepcopy(self.safe)
        case["obligations"].pop()
        self.assertIn("missing_obligation", evaluate_completion(case)["reasons"])

    def test_source_object_and_policy_mutation_invalidates_prior_evidence(self):
        for field in ("source_digest", "object_digest", "policy_digest"):
            with self.subTest(field=field):
                case = copy.deepcopy(self.safe)
                case["current"][field] = "changed"
                self.assertIn("stale_evidence", evaluate_completion(case)["reasons"])

    def test_correct_output_does_not_excuse_invalid_trajectory(self):
        case = copy.deepcopy(self.safe)
        case["trajectory_valid"] = False
        self.assertIn("invalid_trajectory", evaluate_completion(case)["reasons"])

    def test_empty_dependency_digests_cannot_close(self):
        case = copy.deepcopy(self.safe)
        for field in ("source_digest", "object_digest", "policy_digest"):
            case["current"][field] = ""
            for obligation in case["obligations"]:
                obligation[field] = ""
        result = evaluate_completion(case)
        self.assertFalse(result["completion_candidate"])
        self.assertIn("unbound_dependency_digest", result["reasons"])

    def test_every_required_completion_binding_fails_closed_when_removed(self):
        for field in ("source_digest", "object_digest", "policy_digest"):
            with self.subTest(location="current", field=field):
                case = copy.deepcopy(self.safe)
                del case["current"][field]
                self.assertIn("invalid_fixture", evaluate_completion(case)["reasons"])
            with self.subTest(location="obligation", field=field):
                case = copy.deepcopy(self.safe)
                del case["obligations"][0][field]
                self.assertIn("invalid_fixture", evaluate_completion(case)["reasons"])


class ObservationalScoringTests(unittest.TestCase):
    def test_panels_preserve_attack_fraction_and_do_not_create_authority(self):
        result = score_observations(sample()["observations"])
        panels = result["panels"]
        self.assertEqual([0, 0.2, 0.4], [p["attacker_fraction"] for p in panels])
        self.assertEqual([0, 0.25, 0.5], [p["honest_defection_rate"] for p in panels])
        self.assertFalse(result["authority_effect"])

    def test_unobserved_panel_is_not_reported_as_success(self):
        data = copy.deepcopy(sample()["observations"])
        data["panels"] = []
        self.assertEqual("NO_OBSERVATIONS", score_observations(data)["panel_status"])

    def test_forced_revision_reports_evidence_quality_and_cost(self):
        result = score_observations(sample()["observations"])
        self.assertEqual(1, result["revisions"]["matched_pairs"])
        self.assertEqual(0, result["revisions"]["evidence_coverage_delta"])
        self.assertEqual(1, result["revisions"]["hedging_delta"])

    def test_simulation_rank_is_separate_from_deployment_and_safety(self):
        result = score_observations(sample()["observations"])
        self.assertEqual(1.0, result["simulation"]["kendall_tau"])
        self.assertFalse(result["simulation"]["runtime_safety_proven"])
        self.assertEqual("MOCKED_TOOL_EFFECTS", result["simulation"]["unobserved_boundary"])

    def test_persona_voice_and_behavior_drift_are_distinct(self):
        result = score_observations(sample()["observations"])
        self.assertTrue(result["persona"]["voice_changed"])
        self.assertFalse(result["persona"]["goal_changed"])
        self.assertFalse(result["persona"]["tool_changed"])
        self.assertFalse(result["persona"]["policy_changed"])
        self.assertFalse(result["persona"]["permission_changed"])

    def test_invalid_pairs_and_missing_live_results_are_not_claimed(self):
        data = copy.deepcopy(sample()["observations"])
        data["revisions"][0]["forced"]["fixture_id"] = "wrong"
        self.assertEqual("INVALID_MATCH", score_observations(data)["revision_status"])
        data = copy.deepcopy(sample()["observations"])
        data["simulation"][0].pop("production_score")
        self.assertEqual("NO_MATCHED_PRODUCTION", score_observations(data)["simulation_status"])

    def test_invalid_panel_counts_are_rejected(self):
        data = copy.deepcopy(sample()["observations"])
        data["panels"][0]["attackers"] = -1
        self.assertEqual("INVALID_MATCH", score_observations(data)["panel_status"])
        data = copy.deepcopy(sample()["observations"])
        data["panels"][0]["attackers"] = "1"
        self.assertEqual("INVALID_MATCH", score_observations(data)["panel_status"])

    def test_defection_rate_uses_initially_correct_population(self):
        data = copy.deepcopy(sample()["observations"])
        data["panels"] = [{
            "fixture_id": "panel-imperfect-baseline",
            "honest_correct_before": [True, False],
            "honest_correct_after": [False, False],
            "agent_count": 2,
            "attackers": 0,
            "authorization": "external",
        }]
        self.assertEqual(1.0, score_observations(data)["panels"][0]["honest_defection_rate"])

    def test_tied_rankings_use_tie_adjusted_kendall_tau_b(self):
        data = copy.deepcopy(sample()["observations"])
        data["simulation"] = [
            {"variant": "a", "simulation_score": 0.5, "production_score": 0.5, "tool_effects": "mocked"},
            {"variant": "b", "simulation_score": 0.5, "production_score": 0.5, "tool_effects": "mocked"},
            {"variant": "c", "simulation_score": 0.8, "production_score": 0.8, "tool_effects": "mocked"},
        ]
        self.assertEqual(1.0, score_observations(data)["simulation"]["kendall_tau_b"])

    def test_malformed_observation_lanes_fail_closed_without_crashing(self):
        corruptions = (
            ("revisions", [{}], "revision_status"),
            ("simulation", [{"variant": "a"}] * 3, "simulation_status"),
            ("persona", [{}], "persona_status"),
        )
        for lane, value, status in corruptions:
            with self.subTest(lane=lane):
                data = copy.deepcopy(sample()["observations"])
                data[lane] = value
                self.assertEqual("INVALID_MATCH", score_observations(data)[status])


class FixturePackTests(unittest.TestCase):
    def test_every_registered_authority_and_completion_case_has_expected_outcome(self):
        pack = sample()
        self.assertEqual("agent-reliability.v0.1.1", pack["version"])
        self.assertEqual(12, sum(f["expected"] for f in pack["authority"]))
        self.assertEqual(12, sum(not f["expected"] for f in pack["authority"]))
        self.assertEqual(12, len({f["pair_id"] for f in pack["authority"]}))
        for category, fn, key in (("authority", evaluate_authority, "eligible_candidate"), ("completion", evaluate_completion, "completion_candidate")):
            for fixture in pack[category]:
                with self.subTest(fixture=fixture["id"]):
                    self.assertEqual(fixture["expected"], fn(fixture["case"])[key])

    def test_coverage_deduplicates_and_exposes_omissions(self):
        coverage = summarize_coverage(sample()["coverage"])
        self.assertEqual(3, coverage["raw_tool_count"])
        self.assertEqual(2, coverage["unique_tool_count"])
        self.assertIn("production_side_effects", coverage["omitted_surfaces"])
        self.assertFalse(coverage["exhaustive"])

    def test_versioned_receipt_is_bound_to_fixture_and_denies_authority(self):
        pack = sample()
        receipt = json.loads(
            (ROOT / "evals/agent-reliability/v0.1.1/verification-receipt.json").read_text()
        )
        report = run_pack(pack)
        self.assertEqual(pack["version"], receipt["version"])
        self.assertEqual(report["fixture_digest_sha256"], receipt["fixture_digest_sha256"])
        self.assertEqual("none", receipt["authority_effect"])
        self.assertIn("Live-model reliability", receipt["claims_not_supported"])

    def test_runner_fails_closed_on_bad_expectation_and_never_claims_observed_success(self):
        fixture = sample()
        result = run_pack(fixture)
        self.assertEqual("PASS_SYNTHETIC_FIXTURES", result["fixture_status"])
        self.assertEqual("NO_OBSERVATIONS", result["observation_status"])
        self.assertEqual(0, result["effects_executed"])
        self.assertEqual(64, len(result["fixture_digest_sha256"]))
        fixture["authority"][0]["expected"] = False
        with self.assertRaisesRegex(ValueError, "authority fixture inventory"):
            run_pack(fixture)

    def test_runner_rejects_wrong_pack_version(self):
        fixture = sample()
        fixture["version"] = "agent-reliability.v9"
        with self.assertRaises(ValueError):
            run_pack(fixture)

    def test_runner_rejects_truncated_fixture_inventory(self):
        fixture = sample()
        fixture["authority"] = fixture["authority"][:2]
        with self.assertRaisesRegex(ValueError, "authority fixture inventory"):
            run_pack(fixture)

    def test_runner_rejects_unmatched_authority_pairs(self):
        fixture = sample()
        fixture["authority"][1]["pair_id"] = "pair:wrong"
        with self.assertRaisesRegex(ValueError, "authority fixture inventory"):
            run_pack(fixture)

    def test_runner_rejects_fixture_manifest_as_observation_trace(self):
        with self.assertRaises(ValueError):
            run_pack(sample(), sample())
        example = run_pack(sample(), sample()["observations"])
        self.assertEqual("SYNTHETIC_EXAMPLE", example["observation_status"])

    def test_runner_rejects_malformed_nested_observations(self):
        data = copy.deepcopy(sample()["observations"])
        data["revisions"] = [{}]
        with self.assertRaises(ValueError):
            run_pack(sample(), data)

    def test_cli_invalid_observation_is_a_clean_error(self):
        fixture_path = "evals/agent-reliability/v0.1.1/fixtures.json"
        result = subprocess.run([sys.executable, "scripts/validate_agent_reliability.py", "--observations", fixture_path], cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(2, result.returncode)
        self.assertIn("invalid observations", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_cli_malformed_json_is_a_clean_error(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as temp_dir:
            observation_path = Path(temp_dir) / "observations.json"
            observation_path.write_text("{not-json", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "scripts/validate_agent_reliability.py", "--observations", str(observation_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(2, result.returncode)
        self.assertIn("invalid observations or fixture input", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_cli_malformed_nested_observation_is_a_clean_error(self):
        data = copy.deepcopy(sample()["observations"])
        data["revisions"] = [{}]
        with tempfile.TemporaryDirectory(dir="/tmp") as temp_dir:
            observation_path = Path(temp_dir) / "observations.json"
            observation_path.write_text(json.dumps(data), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "scripts/validate_agent_reliability.py", "--observations", str(observation_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(2, result.returncode)
        self.assertIn("invalid observations", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
