from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _iso(value: Any) -> Any:
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return str(value)


def binding_runtime_to_canonical(row: dict[str, Any], *, object_key: str) -> dict[str, Any]:
    """Project one runtime source_bindings row into the canonical v2 contract."""
    return {
        "schema_version": row.get("schema_version", "source-binding.v2"),
        "binding_id": row["binding_key"],
        "object_key": object_key,
        "platform": row["platform"],
        "external_id": row["external_id"],
        "external_url": row.get("external_url"),
        "authority_class": row["authority_class"],
        "sync_direction": row["sync_direction"],
        "state": row["state"],
        "canonical_uri": row.get("canonical_uri"),
        "content_hash": row.get("last_seen_hash"),
        "last_seen_at": _iso(row.get("last_seen_at")),
        "last_synced_at": _iso(row.get("last_synced_at")),
        "freshness": row.get("freshness") or {"status": "unknown"},
        "cursor": row.get("cursor") or {},
        "metadata": row.get("metadata") or {},
    }


def binding_canonical_to_runtime(binding: dict[str, Any], *, object_id: str) -> dict[str, Any]:
    return {
        "binding_key": binding["binding_id"],
        "object_id": object_id,
        "schema_version": binding["schema_version"],
        "platform": binding["platform"],
        "external_id": binding["external_id"],
        "external_url": binding.get("external_url"),
        "authority_class": binding["authority_class"],
        "sync_direction": binding["sync_direction"],
        "state": binding["state"],
        "last_seen_hash": binding.get("content_hash"),
        "cursor": binding.get("cursor") or {},
        "freshness": binding.get("freshness") or {"status": "unknown"},
        "metadata": binding.get("metadata") or {},
    }


def receipt_runtime_to_canonical(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": row.get("schema_version", "sync-run-receipt.v2"),
        "receipt_id": row["receipt_key"],
        "idempotency_key": row["idempotency_key"],
        "run_type": row["run_type"],
        "status": row["status"],
        "immutable": True,
        "actor_ref": row.get("actor_ref"),
        "authority_ref": row.get("authority_ref"),
        "agent_ref": row.get("agent_ref"),
        "skill_ref": row.get("skill_ref"),
        "manifest_version": row.get("manifest_version"),
        "trace_id": row.get("trace_id"),
        "started_at": _iso(row["started_at"]),
        "completed_at": _iso(row.get("completed_at")),
        "input_refs": row.get("input_refs") or [],
        "output_refs": row.get("output_refs") or [],
        "evidence_refs": row.get("evidence_refs") or [],
        "metrics": row.get("metrics") or {},
        "error": row.get("error"),
        "proposed_move_ref": row.get("proposed_move_ref"),
        "content_hashes": row.get("content_hashes") or {},
        "receipt_hash": row.get("receipt_hash"),
        "supersedes_receipt_id": row.get("supersedes_receipt_key"),
        "correction_reason": row.get("correction_reason"),
        "outcome": row.get("outcome") or {},
    }


def receipt_canonical_to_runtime(receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": receipt["schema_version"],
        "receipt_key": receipt["receipt_id"],
        "idempotency_key": receipt["idempotency_key"],
        "run_type": receipt["run_type"],
        "status": receipt["status"],
        "actor_ref": receipt.get("actor_ref"),
        "authority_ref": receipt.get("authority_ref"),
        "agent_ref": receipt.get("agent_ref"),
        "skill_ref": receipt.get("skill_ref"),
        "manifest_version": receipt.get("manifest_version"),
        "trace_id": receipt.get("trace_id"),
        "started_at": receipt["started_at"],
        "completed_at": receipt.get("completed_at"),
        "input_refs": receipt.get("input_refs") or [],
        "output_refs": receipt.get("output_refs") or [],
        "evidence_refs": receipt.get("evidence_refs") or [],
        "metrics": receipt.get("metrics") or {},
        "error": receipt.get("error"),
        "proposed_move_ref": receipt.get("proposed_move_ref"),
        "content_hashes": receipt.get("content_hashes") or {},
        "receipt_hash": receipt.get("receipt_hash"),
        "supersedes_receipt_key": receipt.get("supersedes_receipt_id"),
        "correction_reason": receipt.get("correction_reason"),
        "outcome": receipt.get("outcome") or {},
    }


# ---------------------------------------------------------------------------
# Projection Envelope  (schema: projection-envelope.v1)
#
# The projection envelope has no separate runtime-column remapping: all fields
# are canonical-side identifiers.  The mapper pair is provided so that every
# admitted object family can be tested in a round-trip.
# ---------------------------------------------------------------------------


def envelope_canonical_to_runtime(envelope: dict[str, Any]) -> dict[str, Any]:
    """Pass canonical projection envelope fields through to runtime storage.

    All fields are already canonical.  source_bindings within the envelope are
    stored as-is; no UUID column injection is permitted.
    """
    return {
        "schema_version": envelope["schema_version"],
        "object_key": envelope["object_key"],
        "kind": envelope["kind"],
        "canonical_uri": envelope.get("canonical_uri"),
        "canonical_version": envelope.get("canonical_version"),
        "content_hash": envelope.get("content_hash"),
        "authority_class": envelope["authority_class"],
        "projection": envelope.get("projection") or {},
        "source_bindings": envelope.get("source_bindings") or [],
        "generated_at": envelope["generated_at"],
        "generator_ref": envelope["generator_ref"],
    }


def envelope_runtime_to_canonical(row: dict[str, Any]) -> dict[str, Any]:
    """Reconstruct a canonical projection envelope from a runtime row.

    No runtime-UUID columns may appear in the output.  object_key and every
    binding_id within source_bindings must already be stable Quirk identifiers.
    """
    return {
        "schema_version": row.get("schema_version", "projection-envelope.v1"),
        "object_key": row["object_key"],
        "kind": row["kind"],
        "canonical_uri": row.get("canonical_uri"),
        "canonical_version": row.get("canonical_version"),
        "content_hash": row.get("content_hash"),
        "authority_class": "projection",
        "projection": row.get("projection") or {},
        "source_bindings": row.get("source_bindings") or [],
        "generated_at": _iso(row["generated_at"]),
        "generator_ref": row["generator_ref"],
    }

