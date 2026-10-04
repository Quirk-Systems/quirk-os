from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class ValidatorMetricsTests(unittest.TestCase):
    def test_golden_metrics_output_is_excluded_from_repeated_scans(self):
        import validate_golden_pack

        for absolute in (False, True):
            with self.subTest(absolute=absolute), tempfile.TemporaryDirectory() as temporary:
                repo = Path(temporary)
                source = repo / "source.md"
                source.write_text("Stable scan input.\n", encoding="utf-8")
                metrics_path = repo / "metrics.json"
                output = str(metrics_path) if absolute else "metrics.json"
                with patch.object(validate_golden_pack, "ROOT", repo), \
                     patch.object(validate_golden_pack, "REQUIRED_FILES", []), \
                     patch.object(validate_golden_pack, "pack_status", return_value="CANDIDATE"), \
                     patch.object(sys, "argv", ["validate_golden_pack.py", "--metrics-output", output]):
                    self.assertEqual(validate_golden_pack.main(), 0)
                    first = json.loads(metrics_path.read_text(encoding="utf-8"))
                    self.assertEqual(validate_golden_pack.main(), 0)
                    second = json.loads(metrics_path.read_text(encoding="utf-8"))
                for metrics in (first, second):
                    self.assertEqual(metrics["files_scanned"], 1)
                    self.assertEqual(metrics["bytes_scanned"], source.stat().st_size)
                    self.assertEqual(metrics["placeholder_hits"], 0)

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
