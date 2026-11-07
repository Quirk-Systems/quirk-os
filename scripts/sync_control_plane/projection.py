"""Prepare an exact payload for the verifier-only database projection lane.

No database connection, role provisioning, admission, or publication here.
"""
from __future__ import annotations

import copy

from .content import manifest_content_hash
from .attestation import ApprovalError
from .policy import validate_manifest_structure


def prepare_projection(candidate: dict, context: dict, verifier) -> dict:
    manifest = copy.deepcopy(candidate)
    digest = manifest_content_hash(manifest)
    if manifest["content_hash"] != digest:
        raise ApprovalError("candidate declares incorrect content hash")
    if manifest["status"] not in ("candidate", "paused") or manifest.get("admission") is not None:
        raise ApprovalError("source must be an unadmitted candidate")
    record = verifier.verify(manifest, context)
    subject = record["subject"]
    manifest.update(status="active", requested_status="active")
    manifest["admission"] = {
        "decision": "approved", "decision_ref": record["decision_ref"],
        "authority_grant_ref": record["authority_grant_ref"],
        "transition_ref": record["transition_ref"], "approved_by": record["approved_by"],
        "requested_by": subject["requested_by"], "decided_at": record["decided_at"],
        "evaluated_content_hash": digest, "evidence_refs": subject["evidence_refs"],
    }
    errors = validate_manifest_structure(manifest)
    if errors:
        raise ApprovalError("; ".join(errors))
    if manifest_content_hash(manifest) != digest:
        raise ApprovalError("projection changed approved content")
    return {"schema_version": "verified-manifest-projection.v1", "manifest": manifest,
            "approval": record, "expected_from_status": subject["from_status"],
            "database_verification": "projection", "authority_effect": "none"}
