from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from typing import Any

AUTHORITY_RANK = {
    "observe": 0,
    "infer": 1,
    "propose": 2,
    "execute_bounded": 3,
}


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def git_blob_sha(text: str) -> str:
    payload = text.encode("utf-8")
    header = f"blob {len(payload)}\0".encode("utf-8")
    return hashlib.sha1(header + payload).hexdigest()


def manifest_digest(manifest: dict[str, Any]) -> str:
    candidate = copy.deepcopy(manifest)
    candidate.get("integrity", {}).pop("manifest_sha256", None)
    return hashlib.sha256(canonical_json_bytes(candidate)).hexdigest()


def _parse_dt(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return parsed.astimezone(timezone.utc)


def validate_manifest_integrity(
    manifest: dict[str, Any],
    source_text: str,
) -> list[str]:
    errors: list[str] = []
    integrity = manifest.get("integrity") or {}
    if integrity.get("source_blob_sha") != git_blob_sha(source_text):
        errors.append("source blob sha does not match SKILL.md")
    if integrity.get("manifest_sha256") != manifest_digest(manifest):
        errors.append("manifest sha256 does not match canonical manifest")
    source_path = manifest.get("provenance", {}).get("source_path")
    expected_path = f"skills/{manifest.get('id')}/SKILL.md"
    if source_path != expected_path:
        errors.append("manifest source path does not match skill identity")
    return errors


def declared_actions(manifest: dict[str, Any]) -> set[str]:
    return {
        action
        for tool in manifest.get("tools", [])
        for action in tool.get("actions", [])
    }


def validate_skill_grant(
    manifest: dict[str, Any],
    grant: dict[str, Any],
    *,
    now: str,
) -> list[str]:
    errors: list[str] = []
    if manifest.get("status") != "admitted":
        errors.append("runtime loader rejects unadmitted skill version")

    required_grant_fields = (
        "grant_id",
        "skill_id",
        "skill_version",
        "skill_manifest_sha256",
        "decision",
        "admission_ref",
        "requested_by",
        "approved_by",
        "issued_at",
        "expires_at",
        "authority_ceiling",
        "allowed_actions",
        "purpose",
    )
    missing_fields = [
        field for field in required_grant_fields
        if grant.get(field) in (None, "", [])
    ]
    if missing_fields:
        errors.append(f"runtime grant missing required fields: {', '.join(missing_fields)}")

    admission = manifest.get("admission") or {}
    if admission.get("decision") != "approved" or not admission.get("decision_ref"):
        errors.append("admitted skill requires external admission decision")
    if admission.get("requested_by") == admission.get("approved_by"):
        errors.append("skill admission requester and approver must be distinct")

    if grant.get("decision") != "approved":
        errors.append("runtime grant decision must be approved")
    if grant.get("requested_by") == grant.get("approved_by"):
        errors.append("runtime grant requester and approver must be distinct")
    if grant.get("skill_id") != manifest.get("id"):
        errors.append("grant skill id mismatch")
    if grant.get("skill_version") != manifest.get("version"):
        errors.append("grant skill version mismatch")
    if grant.get("skill_manifest_sha256") != manifest.get("integrity", {}).get("manifest_sha256"):
        errors.append("grant manifest digest mismatch")
    if grant.get("admission_ref") != admission.get("decision_ref"):
        errors.append("grant admission reference mismatch")

    manifest_ceiling = manifest.get("authority", {}).get("ceiling")
    grant_ceiling = grant.get("authority_ceiling")
    if manifest_ceiling not in AUTHORITY_RANK or grant_ceiling not in AUTHORITY_RANK:
        errors.append("unknown authority ceiling")
    elif AUTHORITY_RANK[grant_ceiling] > AUTHORITY_RANK[manifest_ceiling]:
        errors.append("runtime grant exceeds manifest authority ceiling")

    requested_actions = set(grant.get("allowed_actions", []))
    if not requested_actions:
        errors.append("runtime grant must allow at least one declared action")
    undeclared = sorted(requested_actions - declared_actions(manifest))
    if undeclared:
        errors.append(f"grant contains undeclared actions: {', '.join(undeclared)}")

    try:
        instant = _parse_dt(now)
        issued = _parse_dt(grant["issued_at"])
        expires = _parse_dt(grant["expires_at"])
        if issued >= expires:
            errors.append("runtime grant expiry must follow issuance")
        if instant < issued:
            errors.append("runtime grant is not yet valid")
        if instant >= expires:
            errors.append("runtime grant is expired")
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(f"invalid runtime grant time contract: {exc}")

    return errors


def load_skill_for_execution(
    manifest: dict[str, Any],
    source_text: str,
    grant: dict[str, Any],
    *,
    now: str,
) -> dict[str, Any]:
    errors = validate_manifest_integrity(manifest, source_text)
    errors.extend(validate_skill_grant(manifest, grant, now=now))
    return {
        "loaded": not errors,
        "skill_id": manifest.get("id"),
        "skill_version": manifest.get("version"),
        "grant_id": grant.get("grant_id"),
        "errors": errors,
    }


def build_run_receipt(
    manifest: dict[str, Any],
    grant: dict[str, Any],
    *,
    receipt_id: str,
    status: str,
    started_at: str,
    finished_at: str,
    input_refs: list[str],
    output_refs: list[str],
    evidence_refs: list[str],
    finding_codes: list[str],
    proposed_mutations: list[str],
) -> dict[str, Any]:
    return {
        "receipt_id": receipt_id,
        "skill_id": manifest["id"],
        "skill_version": manifest["version"],
        "skill_manifest_sha256": manifest["integrity"]["manifest_sha256"],
        "grant_id": grant["grant_id"],
        "status": status,
        "started_at": started_at,
        "finished_at": finished_at,
        "input_refs": input_refs,
        "output_refs": output_refs,
        "evidence_refs": evidence_refs,
        "finding_codes": finding_codes,
        "proposed_mutations": proposed_mutations,
        "authority_ceiling_observed": grant["authority_ceiling"],
        "no_authority_escalation": True,
        "immutable": True,
    }


from .skill_evaluator import evaluate_skill_case
