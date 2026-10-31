from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.applause_gate.skill_conformance import evaluate_shared_skill_case
from scripts.sync_control_plane.skill_runtime import (
    canonical_json_bytes,
    evaluate_skill_case,
    load_skill_for_execution,
    validate_manifest_integrity,
)

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "quirk-applause-gate"
EVALS = ROOT / "evals" / "skills" / "applause-gate-conformance.json"


def byte_difference_count(left: bytes, right: bytes) -> int:
    return abs(len(left) - len(right)) + sum(
        left_byte != right_byte
        for left_byte, right_byte in zip(left, right)
    )


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

    def test_routing_contract_is_precise_and_excludes_professional_and_generic_analytics(self):
        source = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        manifest = json.loads((SKILL_DIR / "manifest.json").read_text(encoding="utf-8"))
        triggers = manifest["triggers"]

        self.assertIn("claimed success", " ".join(triggers["when_to_use"]).lower())
        self.assertIn("bounded evidence analysis", " ".join(triggers["when_to_use"]).lower())
        non_triggers = " ".join(triggers["when_not_to_use"]).lower()
        for boundary in ("medical diagnosis", "legal", "financial", "safety", "generic analytics"):
            self.assertIn(boundary, non_triggers)
        self.assertTrue(
            {"success", "win", "uplift", "evidence"}.isdisjoint(triggers["routing_signals"])
        )

        for heading in (
            "## Triggers",
            "## Non-triggers",
            "## Input contract",
            "## Output contract",
            "## Method",
            "## Quality gates",
            "## Stop conditions",
        ):
            self.assertIn(heading, source)
        self.assertIn("../../evals/applause-gate/cases.json", source)
        self.assertIn("../../docs/applause-gate/H0-B-EVIDENCE.md", source)

    def test_one_byte_source_tamper_is_rejected(self):
        source = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        manifest = json.loads((SKILL_DIR / "manifest.json").read_text(encoding="utf-8"))
        tampered_source = source.replace("Applause", "applause", 1)

        self.assertEqual(
            byte_difference_count(source.encode(), tampered_source.encode()),
            1,
        )
        self.assertIn(
            "source blob sha does not match SKILL.md",
            validate_manifest_integrity(manifest, tampered_source),
        )

    def test_one_byte_canonical_manifest_tamper_is_rejected(self):
        source = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        manifest = json.loads((SKILL_DIR / "manifest.json").read_text(encoding="utf-8"))
        tampered_manifest = copy.deepcopy(manifest)
        tampered_manifest["title"] = tampered_manifest["title"].replace("Quirk", "quirk", 1)

        self.assertEqual(
            byte_difference_count(
                canonical_json_bytes(manifest),
                canonical_json_bytes(tampered_manifest),
            ),
            1,
        )
        self.assertIn(
            "manifest sha256 does not match canonical manifest",
            validate_manifest_integrity(tampered_manifest, source),
        )

    def test_candidate_loader_rejects_package_without_admission_and_scoped_grant(self):
        source = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        manifest = json.loads((SKILL_DIR / "manifest.json").read_text(encoding="utf-8"))

        result = load_skill_for_execution(
            manifest,
            source,
            {},
            now="2026-08-22T14:25:00Z",
        )

        self.assertFalse(result["loaded"])
        self.assertIn("runtime loader rejects unadmitted skill version", result["errors"])
        self.assertTrue(any("runtime grant missing required fields" in error for error in result["errors"]))
        self.assertNotIn("admission", manifest)
        self.assertEqual(
            {
                resource["access"]
                for resource in manifest["resources"]
            },
            {"read", "reference"},
        )
        declared_actions = {
            action
            for tool in manifest["tools"]
            for action in tool["actions"]
        }
        for forbidden_action in ("publish", "mutate", "admit", "activate", "execute"):
            self.assertFalse(
                any(forbidden_action in action for action in declared_actions)
            )
        self.assertEqual(
            {output["name"] for output in manifest["contract"]["outputs"]},
            {"applause_review", "candidate_receipt"},
        )
        self.assertFalse(manifest["authority"]["irreversible_write"])
        self.assertFalse(manifest["authority"]["self_activation"])
        self.assertFalse(manifest["authority"]["canon_promotion"])

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
