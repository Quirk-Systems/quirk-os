from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any, Callable

import yaml

from scripts.validate_agents import (
    build_registry_entry,
    content_sha256,
    load_agent_yaml,
    main,
    seal_registry,
    validate_repository,
)


ROOT = Path(__file__).resolve().parents[1]
AGENT = "quirk-sync-steward"
COPIED_TREES = ("agents", "policies", "schemas", "evals/sync-control-plane", "supabase/tests")


def codes(report: dict[str, Any]) -> set[str]:
    return {finding["code"] for finding in report["findings"]}


class AgentManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        for tree in COPIED_TREES:
            shutil.copytree(ROOT / tree, self.root / tree)
        (self.root / "skills").mkdir()
        shutil.copy2(ROOT / "skills" / "registry.json", self.root / "skills" / "registry.json")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def manifest_path(self, slug: str = AGENT) -> Path:
        return self.root / "agents" / slug / "agent.yaml"

    def load(self, slug: str = AGENT) -> dict[str, Any]:
        return load_agent_yaml(self.manifest_path(slug).read_bytes())

    def write(self, manifest: dict[str, Any], slug: str = AGENT) -> None:
        path = self.manifest_path(slug)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    def reseal(self) -> None:
        registry_path = self.root / "agents" / "registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry["agents"] = [
            build_registry_entry(self.root, path) for path in sorted((self.root / "agents").glob("*/agent.yaml"))
        ]
        registry_path.write_text(json.dumps(seal_registry(registry), indent=2) + "\n", encoding="utf-8")

    def mutate(self, change: Callable[[dict[str, Any]], None], reseal: bool = True) -> dict[str, Any]:
        manifest = self.load()
        change(manifest)
        self.write(manifest)
        if reseal:
            self.reseal()
        return validate_repository(self.root)

    @staticmethod
    def admit(manifest: dict[str, Any], **overrides: Any) -> None:
        manifest["metadata"]["status"] = "active"
        manifest.pop("admission", None)
        manifest["eval_refs"] = ["evals/sync-control-plane/cases/SCP-008.json"]
        admission = {
            "decision": "approved",
            "decision_ref": "decision.agent.quirk-sync-steward.admit.0001",
            "authority_grant_ref": "grant.agent.quirk-sync-steward.0001",
            "granted_ceiling": manifest["authority"]["ceiling"],
            "requested_by": "agent.quirk-sync-steward",
            "approved_by": "human.bryan",
            "evaluated_content_hash": content_sha256(manifest),
            "transition_ref": "transition.agent.quirk-sync-steward.candidate-active.0001",
            "decided_at": "2026-10-04T00:00:00Z",
            "evidence_refs": ["evals/sync-control-plane/cases/SCP-008.json"],
        }
        admission.update(overrides)
        manifest["admission"] = admission

    # --- positive controls -------------------------------------------------

    def test_real_repository_passes(self) -> None:
        report = validate_repository(ROOT)
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["status"], "pass")
        self.assertIn(f"agent.{AGENT}", report["manifest_digests"])
        self.assertFalse(report["authority"]["admits_agents"])

    def test_cli_writes_report_and_metrics(self) -> None:
        self.assertEqual(main(["--repo", str(self.root), "--output", "out/report.json", "--metrics-output", "out/metrics.json"]), 0)
        report = json.loads((self.root / "out" / "report.json").read_text(encoding="utf-8"))
        metrics = json.loads((self.root / "out" / "metrics.json").read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "pass")
        self.assertGreater(metrics["files_scanned"], 0)
        self.assertGreater(metrics["bytes_scanned"], 0)

    def test_active_fixture_passes_structural_checks_without_granting_authority(self) -> None:
        report = self.mutate(lambda manifest: self.admit(manifest))
        self.assertEqual(report["findings"], [])

    # --- adversarial cases -------------------------------------------------

    def test_phantom_registry_id_cannot_reuse_valid_manifest(self) -> None:
        path = self.root / "agents/registry.json"
        registry = json.loads(path.read_text())
        phantom = dict(registry["agents"][0], id="agent.phantom")
        registry["agents"].append(phantom)
        path.write_text(json.dumps(seal_registry(registry)))
        report = validate_repository(self.root)
        self.assertIn("REGISTRY_MANIFEST_DRIFT", codes(report))
        self.assertNotIn("REGISTRY_ORPHAN", codes(report))

    def test_reused_versions_reject_line_breaks(self) -> None:
        report = self.mutate(lambda m: m["metadata"].update(version="0.2.0\n"))
        self.assertIn("AGENT_SCHEMA", codes(report))
        self.assertIn("REGISTRY_SCHEMA", codes(report))
        self.assertEqual(report["manifest_digests"], {})

    def test_rights_review_principal_rejects_line_breaks(self) -> None:
        original = self.load()
        for domains in (["sync"], ["data_productization"]):
            for principal in ("human.reviewer", "human.reviewer\n", "human.reviewer\r\n"):
                with self.subTest(domains=domains, principal=principal):
                    manifest = json.loads(json.dumps(original))
                    manifest["domains"] = domains
                    manifest["rights_review"] = {
                        "outcome": "approved", "license_verified": True,
                        "privacy_review": "approved", "provenance_complete": True,
                        "reviewed_by": principal, "reviewed_at": "2026-10-04T00:00:00Z",
                        "evidence_refs": ["evals/sync-control-plane/cases/SCP-008.json"],
                    }
                    self.write(manifest)
                    self.reseal()
                    report = validate_repository(self.root)
                    if principal == "human.reviewer":
                        self.assertEqual(report["findings"], [])
                    else:
                        self.assertIn("AGENT_SCHEMA", codes(report))
                        self.assertEqual(report["manifest_digests"], {})

    def test_symlink_manifest_cannot_claim_target_as_source_blob(self) -> None:
        path = self.manifest_path()
        target = self.root / "original-agent.yaml"
        path.rename(target)
        path.symlink_to(target)
        self.assertEqual(main(["--repo", str(self.root), "--output", "out/report.json", "--metrics-output", "out/metrics.json"]), 1)
        report = json.loads((self.root / "out/report.json").read_text())
        self.assertIn("AGENT_SOURCE_SYMLINK", codes(report))
        self.assertEqual(report["manifest_digests"], {})
        self.assertTrue((self.root / "out/metrics.json").is_file())
        with self.assertRaisesRegex(ValueError, "symlink"):
            build_registry_entry(self.root, path)

    def test_symlink_agent_directory_is_rejected(self) -> None:
        directory = self.manifest_path().parent
        target = self.root / "original-agent"
        directory.rename(target)
        directory.symlink_to(target, target_is_directory=True)
        self.assertIn("AGENT_SOURCE_SYMLINK", codes(validate_repository(self.root)))
        with self.assertRaisesRegex(ValueError, "symlink"):
            build_registry_entry(self.root, self.manifest_path())

    def test_self_approval_fails(self) -> None:
        report = self.mutate(lambda manifest: self.admit(manifest, approved_by="agent.quirk-sync-steward"))
        self.assertIn("AGENT_SELF_APPROVAL", codes(report))

    def test_ceiling_above_grant_fails(self) -> None:
        report = self.mutate(lambda manifest: self.admit(manifest, granted_ceiling="infer"))
        self.assertIn("AGENT_CEILING_EXCEEDS_GRANT", codes(report))

    def test_evaluated_hash_mismatch_fails(self) -> None:
        report = self.mutate(lambda manifest: self.admit(manifest, evaluated_content_hash="0" * 64))
        self.assertIn("AGENT_EVALUATED_HASH_MISMATCH", codes(report))

    def test_active_without_admission_fails(self) -> None:
        report = self.mutate(lambda manifest: manifest["metadata"].update(status="active"))
        self.assertIn("AGENT_SCHEMA", codes(report))

    def test_active_without_admission_evidence_fails(self) -> None:
        report = self.mutate(lambda manifest: self.admit(manifest, evidence_refs=[]))
        self.assertIn("AGENT_SCHEMA", codes(report))

    def test_missing_prohibited_action_fails(self) -> None:
        report = self.mutate(lambda manifest: manifest["authority"]["prohibited"].remove("deploy_production"))
        self.assertIn("AGENT_SCHEMA", codes(report))

    def test_capability_implying_authority_fails(self) -> None:
        report = self.mutate(lambda manifest: manifest["authority"].update(capability_does_not_imply_authority=False))
        self.assertIn("AGENT_SCHEMA", codes(report))

    def test_unknown_skill_fails(self) -> None:
        report = self.mutate(lambda manifest: manifest["skills"].append("skill.quirk-nonexistent"))
        self.assertIn("AGENT_UNKNOWN_SKILL", codes(report))

    def test_distilled_skill_fails(self) -> None:
        report = self.mutate(lambda manifest: manifest["skills"].append("skill.quirk-distilled-example"))
        self.assertIn("AGENT_DISTILLED_SKILL", codes(report))

    def test_skill_ceiling_above_agent_fails(self) -> None:
        report = self.mutate(lambda manifest: manifest["authority"].update(ceiling="observe"))
        self.assertIn("AGENT_SKILL_CEILING_EXCEEDS_AGENT", codes(report))

    def test_collision_fail_open_fails(self) -> None:
        report = self.mutate(lambda manifest: manifest["trigger_contract"].update(collision_behavior="first_match"))
        self.assertIn("AGENT_SCHEMA", codes(report))

    def test_missing_stop_conditions_fails(self) -> None:
        report = self.mutate(lambda manifest: manifest.pop("stop_conditions"))
        self.assertIn("AGENT_SCHEMA", codes(report))

    def test_missing_referenced_file_fails(self) -> None:
        report = self.mutate(lambda manifest: manifest["trigger_contract"].update(evidence_refs=["evals/missing.json"]))
        self.assertIn("AGENT_REF_MISSING", codes(report))

    def test_data_productization_without_rights_review_fails(self) -> None:
        report = self.mutate(lambda manifest: manifest.update(domains=["sync", "data_productization"]))
        self.assertIn("AGENT_SCHEMA", codes(report))

    def test_registry_digest_tampering_fails(self) -> None:
        registry_path = self.root / "agents" / "registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry["agents"][0]["authority_ceiling"] = "execute_protected"
        registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
        report = validate_repository(self.root)
        self.assertIn("REGISTRY_DIGEST_FAILURE", codes(report))
        self.assertIn("REGISTRY_MANIFEST_DRIFT", codes(report))

    def test_unsealed_manifest_edit_fails(self) -> None:
        report = self.mutate(lambda manifest: manifest.update(purpose=manifest["purpose"] + " Edited."), reseal=False)
        self.assertIn("REGISTRY_MANIFEST_DRIFT", codes(report))

    def test_agent_folder_missing_from_registry_fails(self) -> None:
        manifest = self.load()
        manifest["metadata"]["id"] = "agent.quirk-shadow"
        self.write(manifest, slug="quirk-shadow")
        report = validate_repository(self.root)
        self.assertIn("AGENT_UNREGISTERED", codes(report))

    def test_registry_orphan_fails(self) -> None:
        shutil.rmtree(self.root / "agents" / AGENT)
        report = validate_repository(self.root)
        self.assertIn("REGISTRY_ORPHAN", codes(report))

    def test_folder_id_drift_fails(self) -> None:
        report = self.mutate(lambda manifest: manifest["metadata"].update(id="agent.quirk-other"))
        self.assertIn("AGENT_ID_DRIFT", codes(report))

    def test_duplicate_yaml_key_fails(self) -> None:
        path = self.manifest_path()
        path.write_text(path.read_text(encoding="utf-8") + "receipt_required: false\n", encoding="utf-8")
        report = validate_repository(self.root)
        self.assertIn("AGENT_PARSE_FAILURE", codes(report))


    def test_active_requires_nonempty_eval_refs(self) -> None:
        for refs in (None, [], 1, [""]):
            with self.subTest(refs=refs):
                manifest = self.load()
                self.admit(manifest)
                if refs is None:
                    manifest.pop("eval_refs")
                else:
                    manifest["eval_refs"] = refs
                self.write(manifest)
                self.reseal()
                self.assertIn("AGENT_SCHEMA", codes(validate_repository(self.root)))

    def test_all_evidence_refs_must_resolve_inside_repository(self) -> None:
        original = self.load()
        outside = self.root.parent / (self.root.name + "-outside.json")
        outside.write_text("{}")
        self.addCleanup(outside.unlink)
        (self.root / "escape.json").symlink_to(outside)
        for block in ("eval_refs", "admission", "rights_review"):
            for ref in ("missing.json", "https://example.com/proof", "../" + outside.name, "escape.json", "schemas"):
                with self.subTest(block=block, ref=ref):
                    manifest = json.loads(json.dumps(original))
                    self.admit(manifest)
                    if block == "eval_refs":
                        manifest[block] = [ref]
                    elif block == "admission":
                        manifest[block]["evidence_refs"] = [ref]
                    else:
                        manifest["domains"] = ["data_productization"]
                        manifest[block] = {
                            "outcome": "approved", "license_verified": True,
                            "privacy_review": "approved", "provenance_complete": True,
                            "reviewed_by": "human.fixture", "reviewed_at": "2026-10-04T00:00:00Z",
                            "evidence_refs": [ref],
                        }
                    manifest["admission"]["evaluated_content_hash"] = content_sha256(manifest)
                    self.write(manifest)
                    self.reseal()
                    report = validate_repository(self.root)
                    self.assertIn("AGENT_REF_MISSING", codes(report))
                    self.assertNotIn("AGENT_SCHEMA", codes(report))

    def test_schema_invalid_cli_still_writes_failure_evidence(self) -> None:
        original = self.load()
        changes = (
            lambda m: m["trigger_contract"].update(evidence_refs=1),
            lambda m: m["authority"].update(prohibited=[[]]),
            lambda m: m.update(skills=[{}]),
            lambda m: m["authority"].update(ceiling=[]),
            lambda m: m.update(metadata=[]),
            lambda m: m.update(admission=1),
            lambda m: m.update(rights_review=[]),
        )
        for change in changes:
            with self.subTest(change=change):
                manifest = json.loads(json.dumps(original))
                change(manifest)
                self.write(manifest)
                self.assertEqual(main(["--repo", str(self.root), "--output", "out/report.json", "--metrics-output", "out/metrics.json"]), 1)
                report = json.loads((self.root / "out/report.json").read_text())
                metrics = json.loads((self.root / "out/metrics.json").read_text())
                self.assertEqual(report["status"], "fail")
                self.assertIn("AGENT_SCHEMA", codes(report))
                self.assertEqual(report["manifest_digests"], {})
                self.assertGreater(metrics["finding_count"], 0)
                self.assertFalse(any(value for key, value in report["authority"].items() if key != "meaning"))

    def test_duplicate_registry_keys_rejected_even_when_last_value_is_sealed(self) -> None:
        path = self.root / "agents/registry.json"
        original = path.read_text()
        variants = (
            original.replace('{', '{"agents": [], ', 1),
            original.replace('"status": "candidate"', '"status": "active", "status": "candidate"', 1),
            original.replace('"id":', '"id": "agent.fake", "id":', 1),
        )
        for payload in variants:
            with self.subTest(payload=payload):
                self.assertEqual(json.loads(payload), json.loads(original))
                path.write_text(payload)
                report = validate_repository(self.root)
                self.assertIn("REGISTRY_INVALID", codes(report))
                self.assertTrue(any("duplicate key" in f["message"] for f in report["findings"]))

    def test_policy_drift_fails_closed(self) -> None:
        path = self.root / "policies/manifest-admission-policy.yaml"
        original = yaml.safe_load(path.read_text())
        changes = (
            lambda p: p["rules"].append({"id": "unknown", "require": "new_requirement"}),
            lambda p: p["rules"].pop(),
            lambda p: p["rules"][0].update(require="true"),
            lambda p: p["rules"][-1].update(when="false"),
            lambda p: p["protected_actions"].remove("activate_manifest"),
        )
        for change in changes:
            with self.subTest(change=change):
                policy = json.loads(json.dumps(original))
                change(policy)
                path.write_text(yaml.safe_dump(policy))
                self.assertIn("POLICY_DRIFT", codes(validate_repository(self.root)))
        path.write_text(yaml.safe_dump(original) + "rules: []\n")
        self.assertIn("POLICY_INVALID", codes(validate_repository(self.root)))

    def test_missing_schema_fails_closed_without_semantic_processing(self) -> None:
        (self.root / "schemas/agent-manifest.schema.json").unlink()
        manifest = self.load()
        manifest["authority"]["prohibited"] = [[]]
        self.write(manifest)
        report = validate_repository(self.root)
        self.assertIn("SCHEMA_INVALID", codes(report))
        self.assertIn("AGENT_SCHEMA", codes(report))
        self.assertEqual(report["manifest_digests"], {})


    def test_reference_resolution_errors_preserve_cli_failure_artifacts(self) -> None:
        (self.root / "loop").symlink_to("loop")
        for ref in ("bad\0path", "loop", str(self.root / "schemas/runtime-manifest.schema.json")):
            with self.subTest(ref=ref):
                manifest = self.load()
                manifest["trigger_contract"]["evidence_refs"] = [ref]
                self.write(manifest)
                self.reseal()
                self.assertEqual(main(["--repo", str(self.root), "--output", "out/report.json", "--metrics-output", "out/metrics.json"]), 1)
                report = json.loads((self.root / "out/report.json").read_text())
                self.assertIn("AGENT_REF_MISSING", codes(report))
                self.assertGreater(json.loads((self.root / "out/metrics.json").read_text())["finding_count"], 0)

    def test_filesystem_errors_are_unresolved_references(self) -> None:
        from unittest.mock import patch
        from scripts.validate_agents import _repo_file, _is_file
        for error in (ValueError("invalid path"), RuntimeError("symlink loop"), OSError("unavailable")):
            with self.subTest(error=error):
                with patch.object(Path, "resolve", side_effect=error):
                    self.assertIsNone(_repo_file(self.root, "evidence.json"))
                with patch.object(Path, "is_file", side_effect=error):
                    self.assertFalse(_is_file(self.root / "evidence.json"))

    def test_invalid_existing_manifest_is_not_an_orphan(self) -> None:
        path = self.manifest_path()
        for payload in ("metadata: [", "{}", "[]"):
            with self.subTest(payload=payload):
                path.write_text(payload)
                report = validate_repository(self.root)
                self.assertEqual(report["status"], "fail")
                self.assertNotIn("REGISTRY_ORPHAN", codes(report))
                self.assertNotIn("REGISTRY_MANIFEST_DRIFT", codes(report))
                self.assertEqual(report["manifest_digests"], {})
        path.unlink()
        self.assertIn("REGISTRY_ORPHAN", codes(validate_repository(self.root)))

    def test_registry_cannot_point_at_an_absent_manifest_under_an_existing_id(self) -> None:
        path = self.root / "agents/registry.json"
        registry = json.loads(path.read_text())
        registry["agents"][0]["manifest_path"] = "agents/quirk-missing/agent.yaml"
        path.write_text(json.dumps(seal_registry(registry)))
        self.assertIn("REGISTRY_ORPHAN", codes(validate_repository(self.root)))

    def test_current_policy_rejects_nonhuman_approval_and_malformed_requester(self) -> None:
        for principal in ("agent.other", "service.other", "system.other", "human.", "human.test\n"):
            with self.subTest(principal=principal):
                report = self.mutate(lambda m: self.admit(m, approved_by=principal))
                self.assertEqual(report["status"], "fail")
                self.assertTrue(codes(report) & {"AGENT_INDEPENDENT_APPROVAL_REQUIRED", "AGENT_SCHEMA"})
        report = self.mutate(lambda m: self.admit(m, requested_by="NOT-A-PRINCIPAL"))
        self.assertIn("AGENT_SCHEMA", codes(report))
        report = self.mutate(lambda m: self.admit(m, requested_by="agent.test\n"))
        self.assertEqual(report["status"], "fail")
        self.assertTrue(codes(report) & {"AGENT_REQUESTER_INVALID", "AGENT_SCHEMA"})

    def test_verification_contract_drift_is_not_silently_accepted(self) -> None:
        path = self.root / "policies/manifest-admission-policy.yaml"
        policy = yaml.safe_load(path.read_text())
        policy["verification_contract"]["bootstrap"] = "allow_without_approval"
        path.write_text(yaml.safe_dump(policy))
        self.assertIn("POLICY_DRIFT", codes(validate_repository(self.root)))

    def test_observability_is_strict_and_does_not_require_generated_metrics(self) -> None:
        self.assertFalse((self.root / "evals/golden-pack/validate-golden-pack-metrics.json").exists())
        self.assertEqual(validate_repository(self.root)["status"], "pass")
        report = self.mutate(lambda m: m["observability"].update(unrecognized=True))
        self.assertIn("AGENT_SCHEMA", codes(report))
        m = self.load(); m["observability"].pop("unrecognized"); self.write(m)
        report = self.mutate(lambda m: m["observability"].update(ci_metrics_refs=["../escaped.json"]))
        self.assertIn("AGENT_METRICS_PATH_INVALID", codes(report))
        report = self.mutate(lambda m: m["observability"].update(benchmark_refs=["missing.sql"]))
        self.assertIn("AGENT_REF_MISSING", codes(report))


    def test_schema_enum_order_cannot_change_authority(self) -> None:
        path = self.root / "schemas/runtime-manifest.schema.json"
        schema = json.loads(path.read_text())
        schema["properties"]["authority_ceiling"]["enum"].reverse()
        path.write_text(json.dumps(schema))
        def escalate(m: dict[str, Any]) -> None:
            m["authority"]["ceiling"] = "execute_protected"
            self.admit(m, granted_ceiling="enforce_invariant")
        report = self.mutate(escalate)
        self.assertIn("AGENT_CEILING_EXCEEDS_GRANT", codes(report))
        self.assertNotIn("CEILING_VOCABULARY_DRIFT", codes(report))
        report = self.mutate(lambda m: self.admit(m, granted_ceiling="execute_protected"))
        self.assertEqual(report["status"], "pass")
        report = self.mutate(lambda m: m["authority"].update(ceiling="observe"))
        self.assertIn("AGENT_SKILL_CEILING_EXCEEDS_AGENT", codes(report))

    def test_authority_vocabulary_drift_fails_closed(self) -> None:
        path = self.root / "schemas/runtime-manifest.schema.json"
        original = json.loads(path.read_text())
        for value in (True, {"enum": ["observe"]}, {"enum": [["observe"]]}, {"enum": ["unknown"]}):
            with self.subTest(value=value):
                schema = json.loads(json.dumps(original))
                schema["properties"]["authority_ceiling"] = value
                path.write_text(json.dumps(schema))
                self.assertIn("CEILING_VOCABULARY_DRIFT", codes(validate_repository(self.root)))

    def test_schema_resources_use_explicit_draft_and_preserve_reports(self) -> None:
        for name in ("runtime-manifest.schema.json", "agent-manifest.schema.json", "agent-registry.schema.json"):
            path = self.root / "schemas" / name
            schema = json.loads(path.read_text()); schema.pop("$schema"); path.write_text(json.dumps(schema))
        self.assertEqual(main(["--repo", str(self.root), "--output", "out/report.json", "--metrics-output", "out/metrics.json"]), 0)
        path = self.root / "schemas/agent-manifest.schema.json"
        schema = json.loads(path.read_text()); schema["$schema"] = "https://example.invalid/unknown-draft"; path.write_text(json.dumps(schema))
        self.assertEqual(main(["--repo", str(self.root), "--output", "out/report.json", "--metrics-output", "out/metrics.json"]), 1)
        self.assertIn("SCHEMA_INVALID", codes(json.loads((self.root / "out/report.json").read_text())))
        self.assertGreater(json.loads((self.root / "out/metrics.json").read_text())["finding_count"], 0)

    def test_schema_duplicate_keys_fail_before_contract_interpretation(self) -> None:
        for name in ("runtime-manifest.schema.json", "agent-manifest.schema.json", "agent-registry.schema.json"):
            path = self.root / "schemas" / name
            original = path.read_text()
            path.write_text(original.replace('"properties":', '"properties": {}, "properties":', 1))
            report = validate_repository(self.root)
            self.assertIn("SCHEMA_INVALID", codes(report))
            path.write_text(original)

    def test_windows_paths_do_not_become_literal_posix_evidence(self) -> None:
        for ref in (r"..\outside.json", r"C:\outside.json", "C:outside.json", r"\\server\share\file.json", "proof.json:stream"):
            with self.subTest(ref=ref):
                # On Linux these can exist as ordinary filenames; still reject them.
                if os.name != "nt":
                    (self.root / ref).write_text("{}")
                report = self.mutate(lambda m: m["trigger_contract"].update(evidence_refs=[ref]))
                self.assertIn("AGENT_REF_MISSING", codes(report))

    def test_malformed_skill_ceiling_preserves_cli_artifacts(self) -> None:
        path = self.root / "skills/registry.json"
        original = json.loads(path.read_text())
        for ceiling in ({}, [], None, 1, "not_a_ceiling"):
            with self.subTest(ceiling=ceiling):
                registry = json.loads(json.dumps(original))
                registry["skills"][0]["authority_ceiling"] = ceiling
                path.write_text(json.dumps(registry))
                self.assertEqual(main(["--repo", str(self.root), "--output", "out/report.json", "--metrics-output", "out/metrics.json"]), 1)
                self.assertIn("SKILL_REGISTRY_INVALID", codes(json.loads((self.root / "out/report.json").read_text())))
                self.assertGreater(json.loads((self.root / "out/metrics.json").read_text())["finding_count"], 0)

    def test_agent_ci_covers_arbitrary_evidence_changes(self) -> None:
        workflow = yaml.safe_load((ROOT / ".github/workflows/validate-agents.yml").read_text())
        triggers = workflow.get("on", workflow.get(True))
        for event in ("pull_request", "push"):
            self.assertEqual(triggers[event]["paths"], ["**"])
        evidence = self.root / "other/approval.json"
        evidence.parent.mkdir(); evidence.write_text("{}")
        report = self.mutate(lambda m: m["trigger_contract"].update(evidence_refs=["other/approval.json"]))
        self.assertEqual(report["status"], "pass")
        evidence.unlink()
        self.assertIn("AGENT_REF_MISSING", codes(validate_repository(self.root)))

    def test_identifier_line_terminators_fail_schema(self) -> None:
        original = self.load()
        changes = (
            lambda m: m.update(stop_conditions=["missing_authority\n"]),
            lambda m: m["tools"]["github"].update(allowed=["read\n"]),
            lambda m: m["tools"].update({"unsafe\n": {"allowed": ["read"]}}),
            lambda m: m["tools"]["vercel"].update(deployment="prohibited_until_admitted\n"),
            lambda m: m["tools"]["cloudflare"].update(state="deferred_unbound\n"),
        )
        for change in changes:
            with self.subTest(change=change):
                self.write(json.loads(json.dumps(original)))
                self.assertIn("AGENT_SCHEMA", codes(self.mutate(change)))


if __name__ == "__main__":
    unittest.main()
