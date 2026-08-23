from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sync_control_plane.mappers import (  # noqa: E402
    binding_canonical_to_runtime,
    binding_runtime_to_canonical,
    receipt_canonical_to_runtime,
    receipt_runtime_to_canonical,
)
from sync_control_plane.policy import evaluate_fixture, validate_manifest_admission  # noqa: E402


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _active_base() -> dict:
    """Return a deep copy of the valid active manifest fixture."""
    return copy.deepcopy(load("evals/sync-control-plane/valid-active-manifest.json"))


class SyncControlPlaneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest_schema = load("schemas/runtime-manifest.schema.json")
        cls.binding_schema = load("schemas/source-binding.schema.json")
        cls.receipt_schema = load("schemas/sync-run-receipt.schema.json")
        cls.fixtures = load("evals/sync-control-plane/fixtures.json")

    def validate(self, schema, instance):
        return list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(instance))

    def test_all_eleven_fixtures(self):
        self.assertEqual(11, len(self.fixtures["fixtures"]))
        for fixture in self.fixtures["fixtures"]:
            with self.subTest(fixture=fixture["id"]):
                result = evaluate_fixture(fixture["name"], load(fixture["case_ref"]))
                self.assertEqual(fixture["expected"], result["action"])

    def test_valid_active_manifest(self):
        manifest = load("evals/sync-control-plane/valid-active-manifest.json")
        self.assertEqual([], self.validate(self.manifest_schema, manifest))
        self.assertEqual([], validate_manifest_admission(manifest))

    def test_self_promotion_rejected(self):
        manifest = load("evals/sync-control-plane/cases/SCP-011.json")["manifest"]
        self.assertTrue(self.validate(self.manifest_schema, manifest) or validate_manifest_admission(manifest))

    def test_cloudflare_deferred_binding_is_valid(self):
        binding = {
            "schema_version": "source-binding.v2",
            "binding_id": "binding.cloudflare.deferred",
            "object_key": "platform.cloudflare",
            "platform": "cloudflare",
            "external_id": "unverified",
            "authority_class": "projection",
            "sync_direction": "none",
            "state": "deferred",
            "freshness": {"status": "unknown"},
        }
        self.assertEqual([], self.validate(self.binding_schema, binding))

    def test_binding_mapper_roundtrip(self):
        runtime = {
            "schema_version": "source-binding.v2",
            "binding_key": "binding.github.repo",
            "platform": "github",
            "external_id": "Quirk-Systems/quirk-os",
            "authority_class": "canonical",
            "sync_direction": "pull",
            "state": "candidate",
            "freshness": {"status": "fresh"},
        }
        canonical = binding_runtime_to_canonical(runtime, object_key="repo.quirk-os")
        self.assertEqual([], self.validate(self.binding_schema, canonical))
        rebound = binding_canonical_to_runtime(canonical, object_id="uuid")
        self.assertEqual(runtime["binding_key"], rebound["binding_key"])

    def test_receipt_mapper_roundtrip(self):
        runtime = {
            "schema_version": "sync-run-receipt.v2",
            "receipt_key": "receipt.test",
            "idempotency_key": "receipt:test:1",
            "run_type": "validate",
            "status": "blocked",
            "started_at": "2026-08-12T00:00:00Z",
            "completed_at": "2026-08-12T00:00:01Z",
            "input_refs": [],
            "output_refs": [],
            "evidence_refs": ["test://receipt"],
            "receipt_hash": "f" * 64,
        }
        canonical = receipt_runtime_to_canonical(runtime)
        self.assertEqual([], self.validate(self.receipt_schema, canonical))
        rebound = receipt_canonical_to_runtime(canonical)
        self.assertEqual(runtime["receipt_key"], rebound["receipt_key"])


class AdmissionPolicyRegressionTests(unittest.TestCase):
    """One test per rule in policies/manifest-admission-policy.yaml.

    Each test must fail if its corresponding rule is removed from
    validate_manifest_admission(). Add a new test here whenever a new
    rule is added to the policy YAML so the invariant is durable.
    """

    @classmethod
    def setUpClass(cls):
        cls.manifest_schema = json.loads(
            (ROOT / "schemas/runtime-manifest.schema.json").read_text(encoding="utf-8")
        )

    def _schema_errors(self, manifest: dict) -> list:
        return list(
            Draft202012Validator(self.manifest_schema, format_checker=FormatChecker()).iter_errors(manifest)
        )

    # rule: no_self_approval — requester may not approve its own transition
    def test_no_self_approval(self):
        m = _active_base()
        m["admission"]["approved_by"] = m["admission"]["requested_by"]
        self.assertTrue(validate_manifest_admission(m), "no_self_approval rule must reject requester==approver")

    # rule: evaluated_hash_matches — evaluated_content_hash must equal content_hash
    def test_evaluated_hash_must_match_content_hash(self):
        m = _active_base()
        m["admission"]["evaluated_content_hash"] = "e" * 64
        self.assertTrue(validate_manifest_admission(m), "evaluated_hash_matches rule must reject hash mismatch")

    # rule: explicit_grant — authority_grant_ref required for active
    def test_active_requires_authority_grant_ref(self):
        m = _active_base()
        m["admission"]["authority_grant_ref"] = ""
        errors = validate_manifest_admission(m)
        self.assertTrue(errors, "explicit_grant rule must reject missing authority_grant_ref")

    # rule: legal_transition — transition_ref required for active
    def test_active_requires_transition_ref(self):
        m = _active_base()
        m["admission"]["transition_ref"] = ""
        errors = validate_manifest_admission(m)
        self.assertTrue(errors, "legal_transition rule must reject missing transition_ref")

    # rule: active_requires_evidence — decision_ref required for active
    def test_active_requires_decision_ref(self):
        m = _active_base()
        m["admission"]["decision_ref"] = ""
        errors = validate_manifest_admission(m)
        self.assertTrue(errors, "active_requires_evidence rule must reject missing decision_ref")

    # rule: active_requires_evidence — admission block must exist on active
    def test_active_requires_admission_block(self):
        m = _active_base()
        m["admission"] = None
        errors = validate_manifest_admission(m)
        self.assertTrue(errors, "active_requires_evidence rule must reject null admission on active manifest")

    # rule: active_requires_evidence — eval_refs required (schema layer)
    def test_active_requires_eval_refs(self):
        m = _active_base()
        m["eval_refs"] = []
        schema_errors = self._schema_errors(m)
        self.assertTrue(schema_errors, "schema must reject active manifest with empty eval_refs")

    # rule: active_requires_evidence — stop_conditions required (schema layer)
    def test_active_requires_stop_conditions(self):
        m = _active_base()
        m["stop_conditions"] = []
        schema_errors = self._schema_errors(m)
        self.assertTrue(schema_errors, "schema must reject active manifest with empty stop_conditions")

    # rule: active_requires_evidence — evidence_refs required (schema + policy layers)
    def test_active_requires_evidence_refs(self):
        m = _active_base()
        m["admission"]["evidence_refs"] = []
        schema_errors = self._schema_errors(m)
        self.assertTrue(schema_errors, "schema must reject active admission with empty evidence_refs")

    # rule: rights_before_productization
    def test_rights_before_productization(self):
        m = _active_base()
        m["manifest_key"] = "capability.data-test"
        m["manifest_kind"] = "capability"
        m["domains"] = ["data_productization"]
        m["rights_review"] = {
            "outcome": "deferred",
            "license_verified": False,
            "privacy_review": "blocked",
            "provenance_complete": False,
            "reviewed_by": "human.bryan",
            "reviewed_at": "2026-08-12T00:00:00Z",
            "evidence_refs": ["rights://blocked"],
        }
        policy_errors = validate_manifest_admission(m)
        self.assertTrue(policy_errors, "rights_before_productization rule must reject unapproved rights review")

    # rule: collisions_fail_closed — orchestrator with multiple skill_refs needs trigger_contract
    def test_collisions_fail_closed(self):
        m = _active_base()
        m["manifest_key"] = "orchestrator.collision-test"
        m["manifest_kind"] = "orchestrator"
        m["skill_refs"] = ["skill.alpha", "skill.beta"]
        m.pop("trigger_contract", None)
        policy_errors = validate_manifest_admission(m)
        schema_errors = self._schema_errors(m)
        self.assertTrue(
            policy_errors or schema_errors,
            "collisions_fail_closed rule must reject orchestrator without trigger_contract",
        )

    # correction route: only a superseding receipt may amend append-only evidence
    def test_candidate_manifest_passes_without_admission(self):
        """Regression: candidate status must not require admission fields."""
        m = _active_base()
        m["status"] = "candidate"
        m["requested_status"] = "candidate"
        m.pop("admission", None)
        m.pop("eval_refs", None)
        m.pop("stop_conditions", None)
        errors = validate_manifest_admission(m)
        self.assertEqual([], errors, "candidate manifest must pass without admission block")


if __name__ == "__main__":
    unittest.main()
