from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ValidatorMetricsTests(unittest.TestCase):
    def _run(self, script: str, *args: str, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            [sys.executable, str(ROOT / script), *args],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )

    def test_validate_sync_control_plane_writes_metrics(self):
        with tempfile.TemporaryDirectory() as temporary:
            metrics_path = Path(temporary) / "sync-metrics.json"
            result = self._run(
                "scripts/validate_sync_control_plane.py",
                "--repo",
                str(ROOT),
                "--metrics-output",
                str(metrics_path),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            self.assertEqual(metrics["validator"], "validate_sync_control_plane.py")
            self.assertIn("elapsed_seconds", metrics)
            self.assertIn("fixture_count", metrics)

    def test_validate_skills_writes_metrics(self):
        with tempfile.TemporaryDirectory() as temporary:
            metrics_path = Path(temporary) / "skills-metrics.json"
            result = self._run(
                "scripts/validate_skills.py",
                "--repo",
                str(ROOT),
                "--metrics-output",
                str(metrics_path),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            self.assertEqual(metrics["validator"], "validate_skills.py")
            self.assertEqual(metrics["status"], "pass")
            self.assertGreaterEqual(metrics["combined_case_count"], 48)

    def test_validate_deck_grammar_writes_metrics(self):
        with tempfile.TemporaryDirectory() as temporary:
            metrics_path = Path(temporary) / "deck-metrics.json"
            result = self._run(
                "scripts/validate_deck_grammar.py",
                "--repo",
                str(ROOT),
                "--metrics-output",
                str(metrics_path),
                extra_env={"PYTHONPATH": str(ROOT / "scripts")},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            self.assertEqual(metrics["validator"], "validate_deck_grammar.py")
            self.assertIn("schema_check_count", metrics)
            self.assertTrue(metrics["passed"])


if __name__ == "__main__":
    unittest.main()
