from __future__ import annotations

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


class SyncControlPlaneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest_schema = load("schemas/runtime-manifest.schema.json")
        cls.binding_schema = load("schemas/source-binding.schema.json")
        cls.receipt_schema = load("schemas/sync-run-receipt.schema.json")
        cls.fixtures = load("evals/sync-control-plane/fixtures.json")

    def validate(self, schema, instance):
        return list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(instance))

    def test_all_sixteen_fixtures(self):
        self.assertEqual(16, len(self.fixtures["fixtures"]))
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


if __name__ == "__main__":
    unittest.main()
