from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from scripts.sync_control_plane.skill_runtime import (
    build_run_receipt,
    evaluate_skill_case,
    git_blob_sha,
    load_skill_for_execution,
    manifest_digest,
    validate_manifest_integrity,
    validate_skill_grant,
)


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def load_candidate(skill_id: str) -> tuple[dict, str]:
    manifest = json.loads((SKILLS / skill_id / "manifest.json").read_text(encoding="utf-8"))
    source = (SKILLS / skill_id / "SKILL.md").read_text(encoding="utf-8")
    return manifest, source


def admitted_copy(skill_id: str = "quirk-source-authority-resolver") -> tuple[dict, str]:
    manifest, source = load_candidate(skill_id)
    manifest["status"] = "admitted"
    manifest["admission"] = {
        "decision": "approved",
        "decision_ref": f"decision.{skill_id}.admit.0001",
        "requested_by": f"requester.{skill_id}",
        "approved_by": "human.bryan",
        "decided_at": "2026-08-12T03:30:00Z",
    }
    manifest["integrity"]["manifest_sha256"] = "0" * 64
    manifest["integrity"]["manifest_sha256"] = manifest_digest(manifest)
    return manifest, source


def valid_grant(manifest: dict) -> dict:
    first_action = manifest["tools"][0]["actions"][0]
    return {
        "grant_id": f"grant.{manifest['id']}.test.0001",
        "skill_id": manifest["id"],
        "skill_version": manifest["version"],
        "skill_manifest_sha256": manifest["integrity"]["manifest_sha256"],
        "decision": "approved",
        "admission_ref": manifest["admission"]["decision_ref"],
        "requested_by": "operator.test",
        "approved_by": "human.bryan",
        "issued_at": "2026-08-12T04:00:00Z",
        "expires_at": "2026-08-12T06:00:00Z",
        "authority_ceiling": manifest["authority"]["ceiling"],
        "allowed_actions": [first_action],
        "purpose": "bounded conformance proof",
        "source_refs": ["fixture.skill-runtime"],
    }


class SkillIntegrityTests(unittest.TestCase):
    def test_all_candidate_manifests_bind_exact_source_and_digest(self) -> None:
        manifests = list(SKILLS.glob("*/manifest.json"))
        self.assertEqual(len(manifests), 12)
        for path in manifests:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            source = (path.parent / "SKILL.md").read_text(encoding="utf-8")
            self.assertEqual(validate_manifest_integrity(manifest, source), [])
            self.assertEqual(manifest["integrity"]["source_blob_sha"], git_blob_sha(source))
            self.assertEqual(manifest["integrity"]["manifest_sha256"], manifest_digest(manifest))

    def test_source_tampering_is_rejected(self) -> None:
        manifest, source = load_candidate("quirk-data-refinery")
        errors = validate_manifest_integrity(manifest, source + "\nunauthorized mutation\n")
        self.assertIn("source blob sha does not match SKILL.md", errors)

    def test_manifest_tampering_is_rejected(self) -> None:
        manifest, source = load_candidate("quirk-control-loop-designer")
        manifest["purpose"] += " silently"
        errors = validate_manifest_integrity(manifest, source)
        self.assertIn("manifest sha256 does not match canonical manifest", errors)


class SkillLoaderTests(unittest.TestCase):
    NOW = "2026-08-12T05:00:00Z"

    def test_candidate_is_not_loadable(self) -> None:
        manifest, source = load_candidate("quirk-source-authority-resolver")
        admitted, _ = admitted_copy("quirk-source-authority-resolver")
        grant = valid_grant(admitted)
        grant["skill_manifest_sha256"] = manifest["integrity"]["manifest_sha256"]
        grant["admission_ref"] = "decision.missing"
        result = load_skill_for_execution(manifest, source, grant, now=self.NOW)
        self.assertFalse(result["loaded"])
        self.assertIn("runtime loader rejects unadmitted skill version", result["errors"])

    def test_separately_admitted_version_with_scoped_grant_loads(self) -> None:
        manifest, source = admitted_copy()
        grant = valid_grant(manifest)
        result = load_skill_for_execution(manifest, source, grant, now=self.NOW)
        self.assertTrue(result["loaded"], result["errors"])

    def test_over_ceiling_grant_is_rejected(self) -> None:
        manifest, _ = admitted_copy()
        grant = valid_grant(manifest)
        grant["authority_ceiling"] = "propose"
        errors = validate_skill_grant(manifest, grant, now=self.NOW)
        self.assertIn("runtime grant exceeds manifest authority ceiling", errors)

    def test_self_approved_grant_is_rejected(self) -> None:
        manifest, _ = admitted_copy()
        grant = valid_grant(manifest)
        grant["approved_by"] = grant["requested_by"]
        errors = validate_skill_grant(manifest, grant, now=self.NOW)
        self.assertIn("runtime grant requester and approver must be distinct", errors)

    def test_self_approved_admission_is_rejected(self) -> None:
        manifest, _ = admitted_copy()
        manifest["admission"]["approved_by"] = manifest["admission"]["requested_by"]
        manifest["integrity"]["manifest_sha256"] = "0" * 64
        manifest["integrity"]["manifest_sha256"] = manifest_digest(manifest)
        grant = valid_grant(manifest)
        errors = validate_skill_grant(manifest, grant, now=self.NOW)
        self.assertIn("skill admission requester and approver must be distinct", errors)

    def test_expired_grant_is_rejected(self) -> None:
        manifest, _ = admitted_copy()
        grant = valid_grant(manifest)
        grant["expires_at"] = "2026-08-12T04:30:00Z"
        errors = validate_skill_grant(manifest, grant, now=self.NOW)
        self.assertIn("runtime grant is expired", errors)

    def test_undeclared_action_is_rejected(self) -> None:
        manifest, _ = admitted_copy()
        grant = valid_grant(manifest)
        grant["allowed_actions"] = ["promote_canon"]
        errors = validate_skill_grant(manifest, grant, now=self.NOW)
        self.assertTrue(any("undeclared actions" in error for error in errors))

    def test_digest_mismatch_is_rejected(self) -> None:
        manifest, _ = admitted_copy()
        grant = valid_grant(manifest)
        grant["skill_manifest_sha256"] = "f" * 64
        errors = validate_skill_grant(manifest, grant, now=self.NOW)
        self.assertIn("grant manifest digest mismatch", errors)

    def test_empty_action_scope_is_rejected(self) -> None:
        manifest, _ = admitted_copy()
        grant = valid_grant(manifest)
        grant["allowed_actions"] = []
        errors = validate_skill_grant(manifest, grant, now=self.NOW)
        self.assertTrue(any("missing required fields" in error for error in errors))
        self.assertIn("runtime grant must allow at least one declared action", errors)


class SkillContractTests(unittest.TestCase):
    def test_runtime_grant_and_receipt_validate(self) -> None:
        manifest, _ = admitted_copy()
        grant = valid_grant(manifest)
        grant_schema = json.loads(
            (ROOT / "schemas" / "skill-runtime-grant.schema.json").read_text(encoding="utf-8")
        )
        receipt_schema = json.loads(
            (ROOT / "schemas" / "skill-run-receipt.schema.json").read_text(encoding="utf-8")
        )
        format_checker = FormatChecker()
        grant_errors = list(
            Draft202012Validator(grant_schema, format_checker=format_checker).iter_errors(grant)
        )
        self.assertEqual(grant_errors, [])

        receipt = build_run_receipt(
            manifest,
            grant,
            receipt_id="receipt.quirk-source-authority-resolver.test.0001",
            status="completed",
            started_at="2026-08-12T05:00:00Z",
            finished_at="2026-08-12T05:01:00Z",
            input_refs=["fixture.authority-census"],
            output_refs=["asset.authority-census.test"],
            evidence_refs=["eval.QSK-001"],
            finding_codes=["AUTHORITY_RESOLVED"],
            proposed_mutations=[],
        )
        receipt_errors = list(
            Draft202012Validator(receipt_schema, format_checker=format_checker).iter_errors(receipt)
        )
        self.assertEqual(receipt_errors, [])
        self.assertTrue(receipt["immutable"])
        self.assertTrue(receipt["no_authority_escalation"])

    def test_all_44_cases_execute_to_declared_expectations(self) -> None:
        cases = json.loads(
            (ROOT / "evals" / "skills" / "conformance.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(cases), 44)
        for case in cases:
            actual = evaluate_skill_case(case)
            expected = case["expected"]
            with self.subTest(case=case["id"]):
                self.assertEqual(actual["result"], expected["result"])
                self.assertEqual(actual["action"], expected["action"])
                self.assertEqual(actual["blocked"], expected["blocked"])
                self.assertTrue(
                    set(expected["required_codes"]).issubset(actual["finding_codes"])
                )
                self.assertFalse(
                    set(expected["prohibited_codes"]).intersection(actual["finding_codes"])
                )


if __name__ == "__main__":
    unittest.main()
