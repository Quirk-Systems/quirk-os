from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from unittest import mock

from scripts import validate_applause_gate
from scripts.applause_gate.evaluation import (
    MUTATIONS,
    evaluate_visible,
    run_cold_process_replay,
    run_mutation_testing,
    validate_held_out_receipt,
    verify_freeze,
)
from scripts.applause_gate.receipt import sha256_json_without_keys


ROOT = Path(__file__).resolve().parents[1]
EVALUATION_DIR = ROOT / "evals/applause-gate/evaluation"
FREEZE = json.loads((EVALUATION_DIR / "freeze.json").read_text(encoding="utf-8"))
SEAL_PATH = EVALUATION_DIR / "held-out-seal.json"
PUBLIC_KEY = EVALUATION_DIR / "evaluator-public-key.pem"


class ApplauseGateEvaluationTests(unittest.TestCase):
    def test_frozen_candidate_bindings_match_commit_and_working_tree(self):
        self.assertEqual(verify_freeze(ROOT, FREEZE), [])

    def test_freeze_verification_fails_closed_on_digest_or_ancestry_drift(self):
        digest_drift = copy.deepcopy(FREEZE)
        digest_drift["bindings"]["visible_fixtures"]["digest"] = "0" * 64
        self.assertTrue(verify_freeze(ROOT, digest_drift))

        missing_binding = copy.deepcopy(FREEZE)
        missing_binding["bindings"].pop("classifier")
        self.assertTrue(verify_freeze(ROOT, missing_binding))

        redirected_binding = copy.deepcopy(FREEZE)
        redirected_binding["bindings"]["classifier"]["path"] = "scripts/applause_gate/receipt.py"
        self.assertTrue(verify_freeze(ROOT, redirected_binding))

        ancestry_drift = copy.deepcopy(FREEZE)
        ancestry_drift["candidate_commit"] = "0" * 40
        self.assertTrue(verify_freeze(ROOT, ancestry_drift))

    def test_visible_report_records_required_case_evidence(self):
        report = evaluate_visible(ROOT, FREEZE)
        self.assertEqual(report["verdict"], "PASS")
        self.assertEqual(report["case_counts"], {"positive": 5, "negative": 3, "adversarial": 11})
        self.assertEqual(report["total_cases"], 19)
        for case in report["cases"]:
            self.assertIn("actual_verdict", case)
            self.assertIn("required_codes", case)
            self.assertIn("withheld_claims", case)
            self.assertIn("missing_proof", case)
            self.assertEqual(case["differences"], [])

    def test_fabricated_evidence_is_release_blocking(self):
        original = validate_applause_gate.classify_review_request

        def fabricate(request):
            review = copy.deepcopy(original(request))
            review["evidence_refs"].append("fabricated_ref")
            return review

        with mock.patch.object(validate_applause_gate, "classify_review_request", fabricate):
            report = validate_applause_gate.validate(ROOT)

        self.assertEqual(report["verdict"], "FAIL")
        self.assertGreater(report["fabricated_evidence_count"], 0)

    def test_critical_mutations_are_killed(self):
        report = run_mutation_testing(ROOT, FREEZE)
        self.assertEqual(report["verdict"], "PASS")
        self.assertEqual(report["mutation_score"], 1.0)
        self.assertEqual(report["surviving_mutations"], [])
        self.assertEqual(
            {mutation["critical_control"] for mutation in report["mutations"]},
            {"verdict_rules", "integrity_checks", "authority_guards"},
        )

    def test_mutation_infrastructure_errors_are_not_counted_as_kills(self):
        invalid = copy.deepcopy(MUTATIONS[0])
        invalid["test"] = "tests.test_missing_abg07_module"
        report = run_mutation_testing(ROOT, FREEZE, (invalid,))
        self.assertEqual(report["verdict"], "FAIL")
        self.assertEqual(report["killed_mutations"], 0)
        self.assertEqual(report["mutations"][0]["status"], "infrastructure_failure")

    def test_two_cold_processes_replay_identically(self):
        report = run_cold_process_replay(ROOT, FREEZE)
        self.assertEqual(report["verdict"], "PASS")
        self.assertTrue(report["deterministic"])
        self.assertEqual(len(report["observations"]), 2)

    def test_committed_evidence_is_content_addressed_and_redacted(self):
        index_paths = sorted(EVALUATION_DIR.glob("evaluation-index.*.json"))
        if not index_paths:
            self.skipTest("signed evaluation evidence is pending")
        self.assertEqual(len(index_paths), 1)
        index = json.loads(index_paths[0].read_text(encoding="utf-8"))
        self.assertEqual(index_paths[0].stem.split(".", 1)[1], index["receipt_hash"])
        self.assertEqual(index["verdict"], "PASS_CANDIDATE_EVIDENCE")
        self.assertEqual(index["classifications"]["skips"], [])
        self.assertEqual(index["classifications"]["warnings"], [])
        self.assertTrue(index["classifications"]["limitations"])

        evidence = {}
        for name, reference in index["evidence"].items():
            path = EVALUATION_DIR / reference["path"]
            report = json.loads(path.read_text(encoding="utf-8"))
            evidence[name] = report
            self.assertEqual(reference["receipt_hash"], report["receipt_hash"])
            self.assertEqual(
                report["receipt_hash"],
                sha256_json_without_keys(report, {"receipt_hash"}),
            )
            self.assertEqual(path.stem.split(".", 1)[1], report["receipt_hash"])

        self.assertEqual(evidence["visible_conformance"], evaluate_visible(ROOT, FREEZE))
        self.assertEqual(evidence["mutation_report"], run_mutation_testing(ROOT, FREEZE))
        self.assertEqual(evidence["determinism_proof"], run_cold_process_replay(ROOT, FREEZE))

        held_out_path = EVALUATION_DIR / index["evidence"]["held_out_receipt"]["path"]
        held_out = json.loads(held_out_path.read_text(encoding="utf-8"))
        seal = json.loads(SEAL_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            validate_held_out_receipt(
                held_out,
                FREEZE,
                seal,
                PUBLIC_KEY,
                repo=ROOT,
                seal_path=SEAL_PATH,
            ),
            [],
        )
        self.assertEqual(
            held_out["receipt_hash"],
            sha256_json_without_keys(held_out, {"receipt_hash"}),
        )
        for case in held_out["cases"]:
            self.assertNotIn("request", case)
            self.assertNotIn("input", case)
            self.assertNotIn("claim", case)

        tampered = copy.deepcopy(held_out)
        tampered["cases"][0]["actual_verdict"] = "MADE_UP"
        tampered["receipt_hash"] = sha256_json_without_keys(tampered, {"receipt_hash"})
        errors = validate_held_out_receipt(
            tampered,
            FREEZE,
            seal,
            PUBLIC_KEY,
            repo=ROOT,
            seal_path=SEAL_PATH,
        )
        self.assertIn("held-out evaluator signature is invalid", errors)
        self.assertIn("held-out per-case values violate the receipt contract", errors)


if __name__ == "__main__":
    unittest.main()
