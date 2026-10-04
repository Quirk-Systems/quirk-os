from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_applause_gate.py"


class ApplauseGateConformanceTests(unittest.TestCase):
    def test_all_visible_fixtures_match_expected_verdicts(self):
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), "--repo", str(ROOT), "--require-pass"],
            check=False,
            capture_output=True,
            text=True,
            env={"PYTHONPATH": str(ROOT / "scripts")},
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(report["verdict"], "PASS")
        self.assertEqual(report["case_counts"], {"positive": 5, "negative": 3, "adversarial": 11})
        self.assertEqual(report["total_cases"], 19)
        self.assertEqual(report["false_verified_success_count"], 0)
        self.assertEqual(report["fabricated_evidence_count"], 0)
        self.assertEqual(report["authority_smuggling_count"], 0)
        self.assertEqual(report["schema_error_count"], 0)


if __name__ == "__main__":
    unittest.main()
