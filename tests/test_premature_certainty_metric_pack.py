from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "quirk-applause-gate"
PACK_SCRIPT = ROOT / "evals" / "applause-gate" / "plugin-eval" / "premature-certainty" / "evaluate.py"


def load_metric_pack():
    spec = importlib.util.spec_from_file_location("premature_certainty", PACK_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class PrematureCertaintyMetricPackTests(unittest.TestCase):
    def test_pack_emits_only_schema_compatible_extension_fields(self):
        metric_pack = load_metric_pack()
        payload = metric_pack.build_payload(SKILL_DIR, ROOT / ".plugin-eval" / "not-present.jsonl")

        self.assertEqual(set(payload), {"checks", "metrics", "artifacts"})
        self.assertEqual({check["id"] for check in payload["checks"]}, metric_pack.CHECK_IDS)
        for check in payload["checks"]:
            self.assertEqual(
                set(check),
                {"id", "category", "severity", "status", "message", "evidence", "remediation", "source"},
            )
            self.assertIn(check["severity"], {"info", "warning", "error"})
            self.assertIn(check["status"], {"pass", "warn", "fail", "info"})
        for metric in payload["metrics"]:
            self.assertEqual(set(metric), {"id", "category", "value", "unit", "band", "source"})

        checks = {check["id"]: check for check in payload["checks"]}
        for check_id in metric_pack.CHECK_IDS - {"pc-observed-token-usage"}:
            self.assertEqual(checks[check_id]["status"], "pass")
        self.assertEqual(checks["pc-observed-token-usage"]["status"], "fail")

    def test_pack_uses_observed_usage_without_estimation(self):
        metric_pack = load_metric_pack()
        with tempfile.TemporaryDirectory() as temp_dir:
            usage_path = Path(temp_dir) / "usage.jsonl"
            usage_path.write_text(
                "\n".join(
                    [
                        json.dumps({"usage": {"input_tokens": 100, "output_tokens": 20, "total_tokens": 120}}),
                        json.dumps({"usage": {"input_tokens": 140, "output_tokens": 30, "total_tokens": 170}}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            payload = metric_pack.build_payload(SKILL_DIR, usage_path)

        checks = {check["id"]: check for check in payload["checks"]}
        metrics = {metric["id"]: metric for metric in payload["metrics"]}
        self.assertEqual(checks["pc-observed-token-usage"]["status"], "pass")
        self.assertEqual(metrics["pc_observed_usage_sample_count"]["value"], 2)
        self.assertEqual(metrics["pc_observed_input_tokens_total"]["value"], 240)
        self.assertEqual(metrics["pc_observed_output_tokens_total"]["value"], 50)
        self.assertEqual(metrics["pc_observed_total_tokens"]["value"], 290)


if __name__ == "__main__":
    unittest.main()
