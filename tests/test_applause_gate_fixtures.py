from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "evals" / "applause-gate" / "cases.json"
VALIDATOR = ROOT / "scripts" / "validate_applause_gate_fixtures.py"


class ApplauseGateFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = json.loads(FIXTURES.read_text(encoding="utf-8"))
        cls.cases = cls.corpus["cases"]

    def test_exact_fixture_counts(self):
        counts = {kind: 0 for kind in ("positive", "negative", "adversarial")}
        for case in self.cases:
            counts[case["kind"]] += 1
        self.assertEqual(counts, {"positive": 5, "negative": 3, "adversarial": 11})
        self.assertEqual(len(self.cases), 19)

    def test_ids_are_unique_and_partitioned(self):
        ids = [case["id"] for case in self.cases]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(
            ids,
            [
                "ABG-P01", "ABG-P02", "ABG-P03", "ABG-P04", "ABG-P05",
                "ABG-N01", "ABG-N02", "ABG-N03",
                "ABG-A01", "ABG-A02", "ABG-A03", "ABG-A04", "ABG-A05",
                "ABG-A06", "ABG-A07", "ABG-A08", "ABG-A09", "ABG-A10", "ABG-A11",
            ],
        )

    def test_every_case_is_evidence_bound_and_non_executing(self):
        required = {
            "id", "kind", "scenario", "claim", "signal", "evidence", "expected",
            "required_behaviors", "prohibited_behaviors",
        }
        for case in self.cases:
            self.assertTrue(required.issubset(case), case["id"])
            self.assertTrue(case["evidence"], case["id"])
            self.assertIn("verdict", case["expected"], case["id"])
            self.assertNotIn("execute", case["expected"], case["id"])

    def test_candidate_boundary_is_locked(self):
        boundary = self.corpus["candidate_boundary"]
        self.assertEqual(boundary["status"], "candidate_fixture_only")
        self.assertEqual(boundary["authority_ceiling"], "infer")
        self.assertFalse(boundary["evaluator_implementation_present"])
        self.assertFalse(boundary["supabase_mutation_authorized"])
        self.assertFalse(boundary["plugin_packaging_authorized"])
        self.assertFalse(boundary["submission_drafting_authorized"])
        self.assertFalse(boundary["merge_authorized"])
        self.assertFalse(boundary["publication_authorized"])

    def test_false_positive_attacks_never_expect_verified_success(self):
        for case in self.cases:
            if case["kind"] in {"negative", "adversarial"}:
                self.assertNotEqual(case["expected"]["verdict"], "VERIFIED_SUCCESS", case["id"])

    def test_validator_reports_pass(self):
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), "--repo", str(ROOT), "--require-pass"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(report["verdict"], "PASS")
        self.assertEqual(report["case_counts"], {"positive": 5, "negative": 3, "adversarial": 11})
        self.assertEqual(report["total_cases"], 19)


if __name__ == "__main__":
    unittest.main()
