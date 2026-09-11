from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SKILL_DIR = ROOT / "skills" / "quirk-applause-gate"
PACK_SCRIPT = ROOT / "evals" / "applause-gate" / "plugin-eval" / "premature-certainty" / "evaluate.py"
VERIFIER_SCRIPT = (
    ROOT
    / "evals"
    / "applause-gate"
    / "plugin-eval"
    / "premature-certainty"
    / "verify_benchmark_output.py"
)


def load_metric_pack():
    spec = importlib.util.spec_from_file_location("premature_certainty", PACK_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def load_verifier():
    spec = importlib.util.spec_from_file_location("verify_benchmark_output", VERIFIER_SCRIPT)
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

    def test_pack_rejects_usage_without_a_matching_benchmark_result(self):
        metric_pack = load_metric_pack()
        with tempfile.TemporaryDirectory() as temp_dir:
            usage_path = Path(temp_dir) / "usage.jsonl"
            usage_path.write_text(
                json.dumps({"usage": {"input_tokens": 100, "output_tokens": 20, "total_tokens": 120}}) + "\n",
                encoding="utf-8",
            )
            payload = metric_pack.build_payload(SKILL_DIR, usage_path)

        checks = {check["id"]: check for check in payload["checks"]}
        metrics = {metric["id"]: metric for metric in payload["metrics"]}
        self.assertEqual(checks["pc-observed-token-usage"]["status"], "fail")
        self.assertEqual(metrics["pc_observed_usage_sample_count"]["value"], 0)

    def test_pack_uses_only_complete_bound_observed_usage(self):
        metric_pack = load_metric_pack()
        config = json.loads((ROOT / ".plugin-eval" / "benchmark.json").read_text())
        scenarios = config["scenarios"]
        verifier_commands = config["verifiers"]["commands"]
        with tempfile.TemporaryDirectory() as temp_dir:
            usage_path = Path(temp_dir) / "usage.jsonl"
            result_path = Path(temp_dir) / "result.json"
            usage_path.write_text(
                "\n".join(
                    json.dumps(
                        {
                            "usage": {
                                "input_tokens": 100 + index * 40,
                                "output_tokens": 20 + index * 10,
                                "total_tokens": 120 + index * 50,
                            },
                            "metadata": {
                                "scenario_id": scenario["id"],
                                "scenario": scenario["title"],
                                "benchmark_target_name": "quirk-applause-gate",
                                "benchmark_target_kind": "skill",
                            },
                        }
                    )
                    for index, scenario in enumerate(scenarios)
                )
                + "\n",
                encoding="utf-8",
            )
            result_path.write_text(
                json.dumps(
                    {
                        "kind": "benchmark-run",
                        "mode": "codex-cli",
                        "codexVersion": "codex-cli test",
                        "target": {"path": str(SKILL_DIR), "name": "quirk-applause-gate", "kind": "skill"},
                        "config": {
                            "source": "explicit",
                            "path": str(ROOT / ".plugin-eval" / "benchmark.json"),
                            "scenarioCount": len(scenarios),
                            "model": config["runner"]["model"],
                            "sandbox": config["runner"]["sandbox"],
                            "approvalPolicy": config["runner"]["approvalPolicy"],
                            "workspaceSourcePath": config["workspace"]["sourcePath"],
                            "workspaceSetupMode": config["workspace"]["setupMode"],
                            "workspacePreserve": config["workspace"]["preserve"],
                            "targetProvisioningMode": config["targetProvisioning"]["mode"],
                            "verifierCount": len(verifier_commands),
                        },
                        "usageLogPath": str(usage_path),
                        "resultPath": str(result_path),
                        "summary": {
                            "completedScenarios": len(scenarios),
                            "failedScenarios": 0,
                            "sampleCount": len(scenarios),
                            "usageAvailability": "present",
                        },
                        "scenarios": [
                            {
                                "id": scenario["id"],
                                "title": scenario["title"],
                                "purpose": scenario["purpose"],
                                "prompt": scenario["userInput"],
                                "successChecklist": scenario["successChecklist"],
                                "status": "completed",
                                "usageAvailability": "present",
                                "usage": {
                                    "input_tokens": 100 + index * 40,
                                    "output_tokens": 20 + index * 10,
                                    "total_tokens": 120 + index * 50,
                                },
                                "verifierResults": [
                                    {"status": "passed", "command": command}
                                    for command in verifier_commands
                                ],
                            }
                            for index, scenario in enumerate(scenarios)
                        ],
                    }
                ),
                encoding="utf-8",
            )
            payload = metric_pack.build_payload(SKILL_DIR, usage_path, result_path)
            usage_lines = [json.loads(line) for line in usage_path.read_text().splitlines()]
            usage_lines[0]["metadata"]["benchmark_target_name"] = "unrelated-skill"
            usage_path.write_text(
                "\n".join(json.dumps(line) for line in usage_lines) + "\n",
                encoding="utf-8",
            )
            wrong_target_payload = metric_pack.build_payload(SKILL_DIR, usage_path, result_path)

            usage_lines[0]["metadata"]["benchmark_target_name"] = "quirk-applause-gate"
            usage_path.write_text(
                "\n".join(json.dumps(line) for line in usage_lines) + "\n",
                encoding="utf-8",
            )
            result = json.loads(result_path.read_text())
            result["scenarios"][0]["verifierResults"][0]["command"] = "legacy weak verifier"
            result_path.write_text(json.dumps(result), encoding="utf-8")
            stale_result_payload = metric_pack.build_payload(SKILL_DIR, usage_path, result_path)

        checks = {check["id"]: check for check in payload["checks"]}
        metrics = {metric["id"]: metric for metric in payload["metrics"]}
        self.assertEqual(checks["pc-observed-token-usage"]["status"], "pass")
        self.assertEqual(metrics["pc_observed_usage_sample_count"]["value"], 3)
        self.assertEqual(metrics["pc_observed_input_tokens_total"]["value"], 420)
        self.assertEqual(metrics["pc_observed_output_tokens_total"]["value"], 90)
        self.assertEqual(metrics["pc_observed_total_tokens"]["value"], 510)
        self.assertEqual(
            {check["id"]: check for check in wrong_target_payload["checks"]}["pc-observed-token-usage"]["status"],
            "fail",
        )
        self.assertEqual(
            {check["id"]: check for check in stale_result_payload["checks"]}["pc-observed-token-usage"]["status"],
            "fail",
        )

    def test_pack_rejects_an_unrelated_skill(self):
        metric_pack = load_metric_pack()
        with self.assertRaisesRegex(ValueError, "only supports quirk-applause-gate"):
            metric_pack.build_payload(ROOT / "skills" / "quirk-control-loop-designer")
        with tempfile.TemporaryDirectory() as temp_dir:
            copied_target = Path(temp_dir) / "skills" / "quirk-applause-gate"
            shutil.copytree(SKILL_DIR, copied_target)
            with self.assertRaisesRegex(ValueError, "only supports quirk-applause-gate"):
                metric_pack.build_payload(copied_target)

    def test_benchmark_verifier_enforces_case_behavior(self):
        from applause_gate.classifier import classify_review_request, fixture_to_request

        verifier = load_verifier()
        cases = json.loads((ROOT / "evals" / "applause-gate" / "cases.json").read_text())["cases"]
        schema = json.loads((ROOT / "schemas" / "applause-review.schema.json").read_text())
        for scenario_id, case_id in verifier.SCENARIO_CASES.items():
            case = next(case for case in cases if case["id"] == case_id)
            verifier.verify_review(classify_review_request(fixture_to_request(case)), schema, case_id)
            workspace = Path("/tmp") / f"plugin-eval-{scenario_id}-test" / "workspace"
            self.assertEqual(verifier.scenario_id_from_workspace(workspace), scenario_id)

        tampered = classify_review_request(fixture_to_request(next(case for case in cases if case["id"] == "ABG-N01")))
        tampered["verdict"] = "VERIFIED_SUCCESS"
        with self.assertRaisesRegex(ValueError, "verdict=VERIFIED_SUCCESS"):
            verifier.verify_review(tampered, schema, "ABG-N01")

        with self.assertRaisesRegex(ValueError, "case_id=ABG-N01; expected=ABG-N02"):
            verifier.verify_review(
                classify_review_request(fixture_to_request(next(case for case in cases if case["id"] == "ABG-N01"))),
                schema,
                "ABG-N02",
            )


if __name__ == "__main__":
    unittest.main()
