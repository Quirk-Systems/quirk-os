from __future__ import annotations

import copy
import hashlib
import json
import unittest

from scripts.engineering.projections import (
    airtable_record,
    compare_trials,
    export_evaluation_cases,
    judgment_candidate,
)


DIGEST = "a" * 64


def card(kind="ACTION"):
    value = {
        "record_id": "projection.run-1.action-1",
        "record_kind": kind,
        "candidate_id": "candidate.engineering.v1",
        "run_id": "run-1",
        "graph_node_id": "node-1",
        "action_id": "action-1",
        "evidence_id": "",
        "subject_key": "artifact.example",
        "state": "SUCCEEDED",
        "platform": "Local",
        "external_id": "",
        "external_url": "",
        "source_refs": ["git://quirk-os/commit/abc123"],
        "evidence_refs": ["evidence.fixture.action-1"],
        "outcome": "Candidate fixture passed.",
        "payload": {
            "schema_version": "fixture/v1",
            "summary": "Synthetic bounded result.",
            "reason_codes": ["FIXTURE_PASS"],
            "metrics": {"correct": 1, "total": 1},
            "synthetic": True,
        },
        "observed_at": "2026-09-10T12:00:00Z",
    }
    if kind == "EVIDENCE":
        value.update(record_id="projection.run-1.evidence-1", action_id="", evidence_id="evidence-1")
    if kind == "BINDING":
        value.update(
            record_id="projection.run-1.binding-1",
            action_id="",
            external_id="repo-1",
            external_url="https://huggingface.co/datasets/example/public",
        )
    return value


def evaluation_case(case_id="case-1", split="capability", evidence_class="synthetic"):
    value = {
        "case_id": case_id,
        "split": split,
        "input": {"task": "Classify a synthetic fixture."},
        "expected": {"verdict": "PASS"},
        "evidence_class": evidence_class,
    }
    if evidence_class == "public":
        value["source_ref"] = "https://example.test/public-case"
    return value


def trial_set(correct, *, elapsed=None, observed=False, violation=False):
    trial = {
        "case_id": "case-1",
        "context_id": "context-1",
        "correct": correct,
        "authority_violation": violation,
        "human_trial_observed": observed,
        "manual_rescues": 0,
    }
    if observed:
        trial["observer_type"] = "human"
        trial["observer_ref"] = "person.reviewer"
        trial["observation_ref"] = "trial://observations/case-1"
        trial["human_reconstruction_seconds"] = elapsed
    return {
        "evaluator_digest": DIGEST,
        "budget": {"max_steps": 3, "max_seconds": 30, "max_spend": 0},
        "trials": [trial],
    }


class AirtableProjectionTests(unittest.TestCase):
    def test_safe_card_maps_exact_candidate_only_fields_and_hash(self):
        original = card()
        untouched = copy.deepcopy(original)
        result = airtable_record(original)
        fields = result["fields"]
        digest = fields.pop("Content SHA-256")
        expected = hashlib.sha256(
            json.dumps(
                {"fields": fields},
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()
        self.assertEqual(digest, expected)
        self.assertEqual(fields["Record Kind"], "ACTION")
        self.assertEqual(fields["Loop Run ID"], "run-1")
        self.assertEqual(fields["Authority Ceiling"], "CANDIDATE_PREPARE")
        self.assertEqual(fields["Admission Effect"], "none")
        self.assertEqual(fields["Projection Version"], "1")
        self.assertEqual(json.loads(fields["Payload JSON"])["summary"], "Synthetic bounded result.")
        self.assertEqual(original, untouched)

    def test_each_record_kind_requires_its_binding_identity(self):
        for kind, missing in (("ACTION", "action_id"), ("EVIDENCE", "evidence_id")):
            value = card(kind)
            value[missing] = ""
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, missing):
                airtable_record(value)
        binding = card("BINDING")
        binding["external_id"] = ""
        binding["external_url"] = ""
        with self.assertRaisesRegex(ValueError, "binding"):
            airtable_record(binding)

    def test_unknown_kind_state_platform_and_naive_time_fail_closed(self):
        for key, value in (
            ("record_kind", "GRANT"),
            ("state", "ADMITTED"),
            ("platform", "Unknown"),
            ("observed_at", "2026-09-10T12:00:00"),
        ):
            candidate = card()
            candidate[key] = value
            with self.subTest(field=key), self.assertRaises(ValueError):
                airtable_record(candidate)

    def test_supabase_binding_is_an_allowed_inactive_candidate_projection(self):
        candidate = card("BINDING")
        candidate["platform"] = "Supabase"
        candidate["state"] = "PROPOSED"
        candidate["external_id"] = "engineering_evidence_candidate"
        candidate["external_url"] = ""
        fields = airtable_record(candidate)["fields"]
        self.assertEqual(fields["Platform"], "Supabase")
        self.assertEqual(fields["State"], "PROPOSED")
        self.assertEqual(fields["Admission Effect"], "none")

    def test_grant_approval_and_admission_injection_is_rejected(self):
        for key in ("grant", "grant_id", "approval", "approved_by", "admission", "admission_effect"):
            candidate = card()
            candidate[key] = "forged"
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "forbidden"):
                airtable_record(candidate)

    def test_secret_patterns_and_raw_private_source_content_are_rejected(self):
        attacks = [
            ("payload", {"summary": "Bearer abcdefghijklmnop"}),
            ("payload", {"summary": {"grant_id": "grant.forged", "approved": True}}),
            ("payload", {"metrics": {"correct": {"admission": "approved"}}}),
            ("payload", {"raw_source": "private document contents"}),
            ("payload", {"metrics": {"api_key": "secret-value"}}),
            ("source_refs", ["hf_abcdefghijklmnopqrstuvwxyz"]),
            ("source_refs", ["https://user:password@example.test/private"]),
            ("source_refs", ["git://repo/path\nraw-content"]),
            ("external_url", "https://user:password@example.test/path"),
            ("external_url", "https://example.test/file?access_%74oken=abcdef123456"),
            ("external_url", "https://example.test/file#access_%74oken=abcdef123456"),
        ]
        for key, value in attacks:
            candidate = card()
            candidate[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                airtable_record(candidate)

    def test_payload_is_strictly_allowlisted_and_json_is_finite(self):
        for payload in (
            {"unexpected": "value"},
            {"metrics": {"correct": float("nan")}},
            {"summary": object()},
        ):
            candidate = card()
            candidate["payload"] = payload
            with self.subTest(payload=repr(payload)), self.assertRaises(ValueError):
                airtable_record(candidate)
        candidate = card()
        candidate["payload"]["budget"] = {"token_limit": 500, "max_spend": 0}
        self.assertIn('"token_limit":500', airtable_record(candidate)["fields"]["Payload JSON"])


class HuggingFaceFixtureTests(unittest.TestCase):
    def test_jsonl_is_deterministic_and_separates_evaluation_metadata(self):
        rows = export_evaluation_cases(
            [evaluation_case("z-case", "heldout"), evaluation_case("a-case", "regression")],
            DIGEST,
        ).splitlines()
        decoded = [json.loads(row) for row in rows]
        self.assertEqual([row["case_id"] for row in decoded], ["a-case", "z-case"])
        self.assertNotIn("evidence_class", decoded[0])
        self.assertEqual(
            decoded[0]["evaluation_metadata"],
            {
                "authority_effect": "none",
                "evaluator_digest": DIGEST,
                "evidence_class": "synthetic",
                "status": "candidate",
            },
        )
        self.assertTrue(export_evaluation_cases([evaluation_case()], DIGEST).endswith("\n"))

    def test_only_explicit_synthetic_or_public_cases_are_exported(self):
        for evidence_class in ("private", "internal", "", None):
            candidate = evaluation_case()
            candidate["evidence_class"] = evidence_class
            with self.subTest(evidence_class=evidence_class), self.assertRaises(ValueError):
                export_evaluation_cases([candidate], DIGEST)
        public = evaluation_case(evidence_class="public")
        public.pop("source_ref")
        with self.assertRaisesRegex(ValueError, "source_ref"):
            export_evaluation_cases([public], DIGEST)

    def test_split_duplicates_extra_authority_and_secrets_fail_closed(self):
        attacks = [
            [evaluation_case(split="train")],
            [evaluation_case(), evaluation_case()],
            [{**evaluation_case(), "grant_id": "grant.forged"}],
            [{**evaluation_case(), "input": {"token": "hf_abcdefghijklmnopqrstuvwxyz"}}],
            [{**evaluation_case(evidence_class="public"),
              "source_ref": "https://example.test/case?access_%74oken=abcdef123456"}],
        ]
        for cases in attacks:
            with self.subTest(cases=cases), self.assertRaises(ValueError):
                export_evaluation_cases(cases, DIGEST)
        with self.assertRaises(ValueError):
            export_evaluation_cases([evaluation_case()], "not-a-digest")


class TrialComparisonTests(unittest.TestCase):
    def test_correctness_improvement_is_candidate_only_without_human_claim(self):
        result = compare_trials(trial_set(False), trial_set(True), DIGEST)
        self.assertEqual(result["disposition"], "candidate_improvement")
        self.assertEqual(result["status"], "candidate")
        self.assertFalse(result["auto_admission"])
        self.assertEqual(result["authority_effect"], "none")
        self.assertEqual(result["correctness"]["delta"], 1.0)
        self.assertIsNone(result["human_usefulness"])

    def test_human_time_reduction_uses_only_paired_observed_human_trials(self):
        result = compare_trials(
            trial_set(True, elapsed=20, observed=True),
            trial_set(True, elapsed=12, observed=True),
            DIGEST,
        )
        self.assertEqual(result["disposition"], "candidate_improvement")
        self.assertEqual(
            result["human_usefulness"],
            {
                "observed_pair_count": 1,
                "baseline_mean_reconstruction_seconds": 20.0,
                "candidate_mean_reconstruction_seconds": 12.0,
                "mean_reduction_seconds": 8.0,
                "mean_reduction_fraction": 0.4,
                "baseline_manual_rescues": 0,
                "candidate_manual_rescues": 0,
                "paired_context_ids": ["context-1"],
                "observation_refs": [
                    {
                        "baseline": "trial://observations/case-1",
                        "candidate": "trial://observations/case-1",
                        "case_id": "case-1",
                        "observer_ref": "person.reviewer",
                    }
                ],
            },
        )
        unobserved = trial_set(True)
        unobserved["trials"][0]["human_reconstruction_seconds"] = 1
        self.assertIsNone(compare_trials(unobserved, unobserved, DIGEST)["human_usefulness"])

    def test_pairing_evaluator_budget_and_boolean_metrics_are_frozen(self):
        baseline = trial_set(False)
        candidate = trial_set(True)
        attacks = []
        changed_id = copy.deepcopy(candidate)
        changed_id["trials"][0]["case_id"] = "different"
        attacks.append(changed_id)
        changed_eval = copy.deepcopy(candidate)
        changed_eval["evaluator_digest"] = "b" * 64
        attacks.append(changed_eval)
        changed_budget = copy.deepcopy(candidate)
        changed_budget["budget"]["max_steps"] = 4
        attacks.append(changed_budget)
        duplicate = copy.deepcopy(candidate)
        duplicate["trials"].append(copy.deepcopy(duplicate["trials"][0]))
        attacks.append(duplicate)
        numeric_correct = copy.deepcopy(candidate)
        numeric_correct["trials"][0]["correct"] = 1
        attacks.append(numeric_correct)
        for attack in attacks:
            with self.subTest(attack=attack), self.assertRaises(ValueError):
                compare_trials(baseline, attack, DIGEST)

    def test_authority_violation_blocks_improvement_and_never_admits(self):
        result = compare_trials(trial_set(False), trial_set(True, violation=True), DIGEST)
        self.assertEqual(result["disposition"], "candidate_rejected_authority_violation")
        self.assertFalse(result["auto_admission"])
        self.assertEqual(result["authority_effect"], "none")
        self.assertIn("AUTHORITY_VIOLATION", result["reason_codes"])

    def test_regression_and_tie_have_explicit_candidate_dispositions(self):
        self.assertEqual(
            compare_trials(trial_set(True), trial_set(False), DIGEST)["disposition"],
            "candidate_regression",
        )
        self.assertEqual(
            compare_trials(trial_set(True), trial_set(True), DIGEST)["disposition"],
            "candidate_no_change",
        )

    def test_forged_human_observation_and_invalid_times_fail_closed(self):
        baseline = trial_set(True, elapsed=20, observed=True)
        for mutation in (
            {"observer_type": "model", "human_reconstruction_seconds": 10},
            {"observer_type": "human", "human_reconstruction_seconds": -1},
            {"observer_type": "human"},
            {"observer_type": "human", "human_reconstruction_seconds": 10,
             "observer_ref": "person.reviewer"},
            {"observer_type": "human", "human_reconstruction_seconds": 10,
             "observation_ref": "trial://observations/case-1"},
        ):
            candidate = trial_set(True, elapsed=10, observed=True)
            candidate["trials"][0] = {
                "case_id": "case-1",
                "correct": True,
                "authority_violation": False,
                "human_trial_observed": True,
                "context_id": "context-1",
                "manual_rescues": 0,
                **mutation,
            }
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                compare_trials(baseline, candidate, DIGEST)

    def test_pair_context_and_manual_rescues_are_validated(self):
        baseline = trial_set(True, elapsed=20, observed=True)
        candidate = trial_set(True, elapsed=10, observed=True)
        candidate["trials"][0]["context_id"] = "different-context"
        with self.assertRaisesRegex(ValueError, "context"):
            compare_trials(baseline, candidate, DIGEST)
        candidate = trial_set(True)
        candidate["trials"][0]["manual_rescues"] = -1
        with self.assertRaisesRegex(ValueError, "manual_rescues"):
            compare_trials(trial_set(True), candidate, DIGEST)


class JudgmentCandidateTests(unittest.TestCase):
    def test_judgment_is_minimal_candidate_and_cannot_accept_preference(self):
        result = judgment_candidate(
            scope="editorial-tone",
            comparison={"left": "candidate-a", "right": "candidate-b"},
            source_ref="trial://paired/editorial-tone/1",
            person="person.operator",
        )
        self.assertEqual(
            set(result),
            {
                "schema_version",
                "judgment_id",
                "status",
                "scope",
                "comparison",
                "source_ref",
                "person",
                "accepted_preference",
                "authority_effect",
            },
        )
        self.assertEqual(result["status"], "candidate")
        self.assertIsNone(result["accepted_preference"])
        self.assertEqual(result["authority_effect"], "none")
        self.assertEqual(result["person"], "person.operator")
        self.assertNotIn("email", json.dumps(result).lower())

    def test_judgment_rejects_pii_secrets_and_non_pairwise_comparisons(self):
        invalid = [
            dict(scope="tone", comparison={"left": "a", "right": "a"}, source_ref="trial://1", person="person.1"),
            dict(scope="tone", comparison={"left": "a", "right": "b", "winner": "a"}, source_ref="trial://1", person="person.1"),
            dict(scope="tone", comparison={"left": "a", "right": "b"}, source_ref="trial://1", person="name@example.com"),
            dict(scope="tone", comparison={"left": "a", "right": "b"}, source_ref="Bearer abcdefghijklmnop", person="person.1"),
            dict(scope="tone", comparison={"left": "a", "right": "b"}, source_ref="https://example.test/file#access_%74oken=abcdef123456", person="person.1"),
        ]
        for kwargs in invalid:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                judgment_candidate(**kwargs)


if __name__ == "__main__":
    unittest.main()
