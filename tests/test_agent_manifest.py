from __future__ import annotations

import json
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
COPIED_TREES = ("agents", "policies", "schemas", "evals/sync-control-plane")


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

    def test_properly_admitted_active_agent_passes(self) -> None:
        report = self.mutate(lambda manifest: self.admit(manifest))
        self.assertEqual(report["findings"], [])

    # --- adversarial cases -------------------------------------------------

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


if __name__ == "__main__":
    unittest.main()
