from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.applause_gate.skill_conformance import evaluate_shared_skill_case
from scripts.sync_control_plane.skill_runtime import (
    evaluate_skill_case,
    validate_manifest_integrity,
)

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "quirk-applause-gate"
EVALS = ROOT / "evals" / "skills" / "applause-gate-conformance.json"


class ApplauseGateSkillPackageTests(unittest.TestCase):
    def test_candidate_package_binds_source_manifest_registry_and_four_eval_kinds(self):
        source = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        manifest = json.loads((SKILL_DIR / "manifest.json").read_text(encoding="utf-8"))
        registry = json.loads((ROOT / "skills" / "registry.json").read_text(encoding="utf-8"))
        cases = json.loads(EVALS.read_text(encoding="utf-8"))

        self.assertEqual(manifest["status"], "candidate")
        self.assertEqual(manifest["family"], "challenge")
        self.assertEqual(manifest["authority"]["ceiling"], "infer")
        self.assertEqual(validate_manifest_integrity(manifest, source), [])
        self.assertIn("quirk-applause-gate", {entry["id"] for entry in registry["skills"]})
        self.assertEqual(len(cases), 4)
        self.assertEqual({case["kind"] for case in cases}, {"positive", "adversarial", "regression", "authority"})

    def test_shared_cases_pass_without_registering_runtime_evaluator(self):
        cases = json.loads(EVALS.read_text(encoding="utf-8"))
        for case in cases:
            with self.subTest(case=case["id"]):
                actual = evaluate_shared_skill_case(case)
                expected = case["expected"]
                self.assertEqual(actual["result"], expected["result"])
                self.assertEqual(actual["action"], expected["action"])
                self.assertEqual(actual["blocked"], expected["blocked"])
                self.assertTrue(set(expected["required_codes"]).issubset(actual["finding_codes"]))
                self.assertFalse(set(expected["prohibited_codes"]).intersection(actual["finding_codes"]))

                with self.assertRaises(ValueError):
                    evaluate_skill_case(case)


if __name__ == "__main__":
    unittest.main()
