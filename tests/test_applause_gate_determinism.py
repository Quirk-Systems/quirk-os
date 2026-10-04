from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_applause_gate.py"


class ApplauseGateDeterminismTests(unittest.TestCase):
    def run_validator(self) -> dict:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), "--repo", str(ROOT), "--require-pass"],
            check=False,
            capture_output=True,
            text=True,
            env={"PYTHONPATH": str(ROOT / "scripts")},
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        return json.loads(result.stdout)

    def test_two_cold_processes_produce_same_receipt_hash(self):
        first = self.run_validator()
        second = self.run_validator()
        self.assertEqual(first["receipt_hash"], second["receipt_hash"])
        self.assertEqual(first, second)

    def test_receipt_hash_omits_itself(self):
        from applause_gate.receipt import sha256_json_without_keys

        report = self.run_validator()
        self.assertEqual(
            report["receipt_hash"],
            sha256_json_without_keys(report, omitted_keys={"receipt_hash"}),
        )


if __name__ == "__main__":
    unittest.main()
