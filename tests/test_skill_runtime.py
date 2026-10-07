from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock
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
        "requested_by": f"agent.{skill_id}",
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
        "requested_by": "agent.test",
        "approved_by": "human.bryan",
        "issued_at": "2026-08-12T04:00:00Z",
        "expires_at": "2026-08-12T06:00:00Z",
        "authority_ceiling": manifest["authority"]["ceiling"],
        "allowed_actions": [first_action],
        "purpose": "bounded conformance proof",
        "source_refs": ["fixture.skill-runtime"],
    }


class SkillIntegrityTests(unittest.TestCase):
    def test_intent_shaper_draft_conforms_without_manifest_or_registry_admission(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/validate_skills.py"), "--repo", str(ROOT)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertFalse((SKILLS / "quirk-intent-shaper/manifest.json").exists())
        registry = json.loads((SKILLS / "registry.json").read_text())
        self.assertNotIn("quirk-intent-shaper", {entry["id"] for entry in registry["skills"]})

    def test_intent_shaper_draft_exception_cannot_hide_skill_drift_or_self_admission(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            for path in ("schemas", "scripts", "mappings", "evals"):
                (repo / path).symlink_to(ROOT / path, target_is_directory=True)
            shutil.copytree(SKILLS, repo / "skills", ignore=shutil.ignore_patterns("__pycache__"))
            attacks = (
                ("unknown", "SKILL_SET_DRIFT"),
                ("manifest", "DRAFT_SKILL_MANIFEST_PRESENT"),
                ("status", "DRAFT_SKILL_STATUS"),
                ("frontmatter_status", "DRAFT_SKILL_STATUS"),
                ("duplicate_contract_active", "DRAFT_SKILL_STATUS"),
                ("duplicate_quirk_contract_active", "DRAFT_SKILL_STATUS"),
                ("duplicate_contract_candidate", "DRAFT_SKILL_STATUS"),
                ("unquoted_active_status", "DRAFT_SKILL_STATUS"),
                ("unquoted_candidate_status", "DRAFT_SKILL_STATUS"),
                ("duplicate_unquoted_active_status", "DRAFT_SKILL_STATUS"),
                ("duplicate_quoted_candidate_status", "DRAFT_SKILL_STATUS"),
                ("outside_active_status", "DRAFT_SKILL_STATUS"),
                ("outside_candidate_status", "DRAFT_SKILL_STATUS"),
                ("outside_star_status", "DRAFT_SKILL_STATUS"),
                ("outside_lowercase_status", "DRAFT_SKILL_STATUS"),
                ("moved_candidate_status", "DRAFT_SKILL_STATUS"),
                ("formatted_bold_status", "DRAFT_SKILL_STATUS"),
                ("formatted_italic_status", "DRAFT_SKILL_STATUS"),
                ("formatted_code_status", "DRAFT_SKILL_STATUS"),
                ("formatted_ordered_status", "DRAFT_SKILL_STATUS"),
                ("formatted_link_status", "DRAFT_SKILL_STATUS"),
                ("formatted_html_status", "DRAFT_SKILL_STATUS"),
                ("formatted_quoted_status", "DRAFT_SKILL_STATUS"),
                ("formatted_entity_status", "DRAFT_SKILL_STATUS"),
                ("formatted_strikethrough_status", "DRAFT_SKILL_STATUS"),
                ("formatted_reference_status", "DRAFT_SKILL_STATUS"),
                ("formatted_collapsed_status", "DRAFT_SKILL_STATUS"),
                ("formatted_shortcut_status", "DRAFT_SKILL_STATUS"),
                ("html_list_status", "DRAFT_SKILL_STATUS"),
                ("html_paragraph_status", "DRAFT_SKILL_STATUS"),
                ("heading_bold_contract", "DRAFT_SKILL_STATUS"),
                ("heading_closing_contract", "DRAFT_SKILL_STATUS"),
                ("heading_setext_contract", "DRAFT_SKILL_STATUS"),
                ("heading_nested_contract", "DRAFT_SKILL_STATUS"),
                ("registry", "REGISTRY_SKILL_DRIFT"),
            )
            for attack, expected_code in attacks:
                with self.subTest(attack=attack):
                    candidate = repo / "skills/quirk-intent-shaper"
                    source = candidate / "SKILL.md"
                    original_source = source.read_text()
                    registry_path = repo / "skills/registry.json"
                    original_registry = registry_path.read_text()
                    if attack == "unknown":
                        unknown = repo / "skills/quirk-unregistered"
                        unknown.mkdir()
                        (unknown / "SKILL.md").write_text(original_source)
                    elif attack == "manifest":
                        (candidate / "manifest.json").write_text("{}\n")
                    elif attack == "status":
                        source.write_text(original_source.replace("Status: `candidate`", "Status: `active`"))
                    elif attack == "frontmatter_status":
                        source.write_text(original_source.replace("name: quirk-intent-shaper\n",
                                                                 "name: quirk-intent-shaper\nstatus: active\n", 1))
                    elif attack.startswith("html_"):
                        declaration = "<ul><li><strong>Status:</strong> active</li></ul>" if attack == "html_list_status" else "<p>Status: active</p>"
                        source.write_text(original_source + "\n" + declaration + "\n")
                    elif attack.startswith("heading_"):
                        heading = {
                            "heading_bold_contract": "## **Contract**",
                            "heading_closing_contract": "## Contract ##",
                            "heading_setext_contract": "Contract\n--------",
                            "heading_nested_contract": "### Contract",
                        }[attack]
                        source.write_text(original_source + "\n" + heading + "\n")
                    elif attack.startswith("formatted_"):
                        declarations = {
                            "formatted_bold_status": "- **Status:** active",
                            "formatted_italic_status": "- _Status_: active",
                            "formatted_code_status": "- `Status`: active",
                            "formatted_ordered_status": "1. **Status:** active",
                            "formatted_link_status": "- [Status](#contract): active",
                            "formatted_html_status": "- <strong>Status:</strong> active",
                            "formatted_quoted_status": "> - **Status:** active",
                            "formatted_entity_status": "- Status&#58; active",
                            "formatted_strikethrough_status": "- ~~Status:~~ active",
                            "formatted_reference_status": "- [Status:][contract] active\n\n[contract]: #contract",
                            "formatted_collapsed_status": "- [Status:][] active\n\n[Status:]: #contract",
                            "formatted_shortcut_status": "- [Status:] active\n\n[Status:]: #contract",
                        }
                        source.write_text(original_source + "\n## Admission posture\n\n" + declarations[attack] + "\n")
                    elif attack in {"outside_star_status", "outside_lowercase_status", "moved_candidate_status"}:
                        declaration = "* Status: active" if attack == "outside_star_status" else "- status: active"
                        text = original_source
                        if attack == "moved_candidate_status":
                            text = text.replace("- Status: `candidate`", "", 1)
                            declaration = "- Status: `candidate`"
                        source.write_text(text + f"\n## Admission posture\n\n{declaration}\n")
                    elif attack in {"outside_active_status", "outside_candidate_status"}:
                        status = "active" if attack == "outside_active_status" else "`candidate`"
                        source.write_text(original_source + f"\n## Admission posture\n\n- Status: {status}\n")
                    elif attack in {"unquoted_active_status", "unquoted_candidate_status"}:
                        status = "active" if attack == "unquoted_active_status" else "candidate"
                        source.write_text(original_source.replace("- Status: `candidate`", f"- Status: {status}", 1))
                    elif attack in {"duplicate_unquoted_active_status", "duplicate_quoted_candidate_status"}:
                        status = "active" if attack == "duplicate_unquoted_active_status" else "`candidate`"
                        source.write_text(original_source.replace("- Status: `candidate`", f"- Status: `candidate`\n- Status: {status}", 1))
                    elif attack.startswith("duplicate_"):
                        heading = "Quirk contract" if attack == "duplicate_quirk_contract_active" else "Contract"
                        status = "candidate" if attack == "duplicate_contract_candidate" else "active"
                        source.write_text(original_source + f"\n## {heading}\n\n- Status: `{status}`\n")
                    else:
                        registry = json.loads(original_registry)
                        registry["skills"].append({"id": "quirk-intent-shaper"})
                        registry_path.write_text(json.dumps(registry))
                    result = subprocess.run(
                        [sys.executable, str(ROOT / "scripts/validate_skills.py"), "--repo", str(repo)],
                        capture_output=True, text=True, check=False,
                    )
                    self.assertEqual(1, result.returncode, result.stderr)
                    self.assertIn(expected_code, result.stderr)
                    if attack == "unknown":
                        shutil.rmtree(unknown)
                    (candidate / "manifest.json").unlink(missing_ok=True)
                    source.write_text(original_source)
                    registry_path.write_text(original_registry)

    def test_all_candidate_manifests_bind_exact_source_and_digest(self) -> None:
        manifests = [
            path for path in SKILLS.glob("*/manifest.json")
            if not path.parent.name.startswith("quirk-distilled-")
        ]
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
        result = load_skill_for_execution(manifest, source, grant, now=self.NOW, approval_registry=Mock(allows=Mock(return_value=True)))
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
        self.assertTrue(any("schema violation at allowed_actions" in error for error in errors))

    def test_malformed_grants_fail_closed_without_raising(self) -> None:
        manifest, source = admitted_copy()
        grant = valid_grant(manifest)
        malformed = [None, [], "grant.invalid", {}, {**grant, "allowed_actions": [["nested"]]},
                     {**grant, "allowed_actions": "read"}, {**grant, "issued_at": 123},
                     {**grant, "grant_id": "invalid"}, {**grant, "purpose": "x"},
                     {**grant, "revoked": True}, {**grant, "decision": "revoked"}]
        for candidate in malformed:
            with self.subTest(grant=candidate):
                result = load_skill_for_execution(manifest, source, candidate, now=self.NOW)
                self.assertFalse(result["loaded"])
                self.assertTrue(any("runtime grant schema violation" in error for error in result["errors"]))

    def test_nonhuman_or_malformed_approvers_are_rejected(self) -> None:
        manifest, source = admitted_copy()
        for approver in ["agent.other", "service.other", "system.other", "human.", "human.Bryan", "human.bryan\n"]:
            for boundary in ["admission", "grant"]:
                with self.subTest(approver=approver, boundary=boundary):
                    candidate = copy.deepcopy(manifest)
                    if boundary == "admission":
                        candidate["admission"]["approved_by"] = approver
                        candidate["integrity"]["manifest_sha256"] = manifest_digest(candidate)
                    grant = valid_grant(candidate)
                    if boundary == "grant":
                        grant["approved_by"] = approver
                    result = load_skill_for_execution(candidate, source, grant, now=self.NOW)
                    self.assertFalse(result["loaded"])
                    self.assertIn(
                        f"{'skill admission' if boundary == 'admission' else 'runtime grant'} requires approval by an independent human principal",
                        result["errors"],
                    )

    def test_malformed_requester_is_rejected_at_both_boundaries(self) -> None:
        manifest, _ = admitted_copy()
        grant = valid_grant(manifest)
        manifest["admission"]["requested_by"] = "operator.test"
        grant["requested_by"] = "agent."
        errors = validate_skill_grant(manifest, grant, now=self.NOW)
        self.assertIn("skill admission requester must be a well-formed principal", errors)
        self.assertIn("runtime grant requester must be a well-formed principal", errors)


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
