#!/usr/bin/env python3
"""Executable admission conformance for Quirk Sync Control Plane v0.2.

The runner proves candidate eligibility. It never performs human admission,
activates a manifest, promotes Canon, or deploys production.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

HERE = Path(__file__).resolve()
ROOT_DEFAULT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))

from sync_control_plane.mappers import (  # noqa: E402
    binding_canonical_to_runtime,
    binding_runtime_to_canonical,
    receipt_canonical_to_runtime,
    receipt_runtime_to_canonical,
)
from sync_control_plane.policy import evaluate_fixture, validate_manifest_admission  # noqa: E402


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(schema: dict[str, Any], instance: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [error.message for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.path))]


def static_migration_checks(sql: str) -> dict[str, bool]:
    lower = sql.lower()
    tokens = {
        "manifest_guard": "guard_manifest_activation",
        "append_only_receipts": "prevent_append_only_mutation",
        "transition_ledger": "manifest_transition_ledger",
        "proposed_move_store": "create table if not exists quirk_sync.proposed_moves",
        "atomic_outbox_claim": "claim_projection_outbox",
        "bounded_dead_letter": "dead_lettered_at",
        "drift_controller": "observe_binding",
        "projection_rebuild": "rebuild_projection_snapshot",
        "cloudflare_binding": "'cloudflare'",
        "browser_roles_revoked": "revoke all on schema quirk_sync from authenticated",
    }
    return {name: token in lower for name, token in tokens.items()}


def mapping_roundtrip(binding_schema: dict[str, Any], receipt_schema: dict[str, Any]) -> dict[str, Any]:
    runtime_binding = {
        "binding_key": "binding.github.example",
        "schema_version": "source-binding.v2",
        "platform": "github",
        "external_id": "Quirk-Systems/quirk-os#5",
        "external_url": "https://github.com/Quirk-Systems/quirk-os/pull/5",
        "authority_class": "canonical",
        "sync_direction": "bidirectional_proposal",
        "state": "candidate",
        "last_seen_hash": "a" * 64,
        "freshness": {"status": "fresh"},
        "cursor": {},
        "metadata": {},
    }
    canonical_binding = binding_runtime_to_canonical(runtime_binding, object_key="program.quirk-sync-control-plane")
    binding_errors = validate(binding_schema, canonical_binding)
    rebound = binding_canonical_to_runtime(canonical_binding, object_id="00000000-0000-0000-0000-000000000001")

    runtime_receipt = {
        "schema_version": "sync-run-receipt.v2",
        "receipt_key": "receipt.mapping.test",
        "idempotency_key": "mapping:test:0001",
        "run_type": "validate",
        "status": "succeeded",
        "actor_ref": "human.bryan",
        "authority_ref": "grant.mapping.test",
        "started_at": "2026-08-12T00:00:00Z",
        "completed_at": "2026-08-12T00:00:01Z",
        "input_refs": [],
        "output_refs": [],
        "evidence_refs": ["test://mapping"],
        "metrics": {},
        "receipt_hash": "b" * 64,
        "outcome": {},
    }
    canonical_receipt = receipt_runtime_to_canonical(runtime_receipt)
    receipt_errors = validate(receipt_schema, canonical_receipt)
    rereceipt = receipt_canonical_to_runtime(canonical_receipt)
    return {
        "binding_schema_errors": binding_errors,
        "receipt_schema_errors": receipt_errors,
        "binding_roundtrip_stable": rebound["binding_key"] == runtime_binding["binding_key"] and rebound["platform"] == runtime_binding["platform"],
        "receipt_roundtrip_stable": rereceipt["receipt_key"] == runtime_receipt["receipt_key"] and rereceipt["idempotency_key"] == runtime_receipt["idempotency_key"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--output", type=Path, default=Path("evals/sync-control-plane/conformance-results.json"))
    parser.add_argument("--require-admit", action="store_true", help="Exit nonzero unless candidate is eligible for a human admission decision.")
    args = parser.parse_args()
    repo = args.repo.resolve()

    schemas = {
        "manifest": load_json(repo / "schemas/runtime-manifest.schema.json"),
        "binding": load_json(repo / "schemas/source-binding.schema.json"),
        "receipt": load_json(repo / "schemas/sync-run-receipt.schema.json"),
        "transition": load_json(repo / "schemas/manifest-transition.schema.json"),
        "decision": load_json(repo / "schemas/sync-decision.schema.json"),
        "projection": load_json(repo / "schemas/projection-envelope.schema.json"),
    }
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)

    fixtures = load_json(repo / "evals/sync-control-plane/fixtures.json")
    results = []
    for fixture in fixtures["fixtures"]:
        case = load_json(repo / fixture["case_ref"])
        actual = evaluate_fixture(fixture["name"], case)
        passed = actual.get("action") == fixture["expected"]
        results.append({**fixture, "passed": passed, "actual": actual})

    valid_active = load_json(repo / "evals/sync-control-plane/valid-active-manifest.json")
    valid_schema_errors = validate(schemas["manifest"], valid_active)
    valid_policy_errors = validate_manifest_admission(valid_active)

    self_promotion = load_json(repo / "evals/sync-control-plane/cases/SCP-011.json")["manifest"]
    self_schema_errors = validate(schemas["manifest"], self_promotion)
    self_policy_errors = validate_manifest_admission(self_promotion)

    rights_unclear = {
        **valid_active,
        "manifest_key": "capability.data-productization",
        "manifest_kind": "capability",
        "version": "1.0.1",
        "domains": ["data_productization"],
        "rights_review": {
            "outcome": "deferred",
            "license_verified": False,
            "privacy_review": "blocked",
            "provenance_complete": False,
            "reviewed_by": "human.bryan",
            "reviewed_at": "2026-08-12T00:00:00Z",
            "evidence_refs": ["rights://blocked"],
        },
    }
    rights_schema_errors = validate(schemas["manifest"], rights_unclear)

    collision = {
        **valid_active,
        "manifest_key": "orchestrator.collision",
        "manifest_kind": "orchestrator",
        "version": "1.0.1",
        "skill_refs": ["skill.alpha", "skill.beta"],
    }
    collision.pop("trigger_contract", None)
    collision_schema_errors = validate(schemas["manifest"], collision)

    migration_paths = sorted((repo / "supabase/migrations").glob("2026081203000*_sync_control_plane_*.sql"))
    migration_sql = "\n".join(path.read_text(encoding="utf-8") for path in migration_paths)
    static = static_migration_checks(migration_sql)
    mappings = mapping_roundtrip(schemas["binding"], schemas["receipt"])

    checks = {
        "fixture_count_11": len(results) == 11,
        "all_fixtures_pass": all(item["passed"] for item in results),
        "valid_active_manifest_passes_schema": not valid_schema_errors,
        "valid_active_manifest_passes_policy": not valid_policy_errors,
        "self_promotion_rejected_by_schema_or_policy": bool(self_schema_errors or self_policy_errors),
        "rights_unclear_rejected": bool(rights_schema_errors),
        "trigger_collision_rejected": bool(collision_schema_errors),
        "migration_hardening_complete": all(static.values()),
        "mapping_roundtrip_passes": not mappings["binding_schema_errors"] and not mappings["receipt_schema_errors"] and mappings["binding_roundtrip_stable"] and mappings["receipt_roundtrip_stable"],
    }
    eligible = all(checks.values())
    payload = {
        "suite_id": "eval.sync-control-plane.conformance.v0.2",
        "decision": "ELIGIBLE_FOR_HUMAN_ADMISSION" if eligible else "REVISE",
        "automatic_activation": False,
        "checks": checks,
        "fixtures": results,
        "schema_attacks": {
            "valid_active_schema_errors": valid_schema_errors,
            "valid_active_policy_errors": valid_policy_errors,
            "self_promotion_schema_errors": self_schema_errors,
            "self_promotion_policy_errors": self_policy_errors,
            "rights_unclear_schema_errors": rights_schema_errors,
            "trigger_collision_schema_errors": collision_schema_errors,
        },
        "migration_static": static,
        "mapping_proof": mappings,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["content_hash_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    output = args.output if args.output.is_absolute() else repo / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 1 if args.require_admit and not eligible else 0


if __name__ == "__main__":
    raise SystemExit(main())
