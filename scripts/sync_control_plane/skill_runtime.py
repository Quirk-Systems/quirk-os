from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .approval import authorization_errors
from .policy import _is_independent_approver, _is_principal, validate_manifest_admission

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
    grant: Any,
    *,
    now: str,
    approval_registry: Any = None,
) -> list[str]:
    errors: list[str] = []
    if manifest.get("status") != "admitted":
        errors.append("runtime loader rejects unadmitted skill version")

    # The public loader is called directly; it cannot assume a separate schema
    # pass happened. Reject malformed containers and fields before set/time use.
    schema_path = Path(__file__).resolve().parents[2] / "schemas" / "skill-runtime-grant.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema_errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(grant),
        key=lambda error: (tuple(str(part) for part in error.absolute_path), error.message),
    )
    if schema_errors:
        errors.extend(
            f"runtime grant schema violation at {'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
            for error in schema_errors
        )
        return errors

    # Structural admission and scope checks supplement the protected registry.
    admission = manifest.get("admission") or {}
    if admission.get("decision") != "approved" or not admission.get("decision_ref"):
        errors.append("admitted skill requires external admission decision")
    if not _is_principal(admission.get("requested_by")):
        errors.append("skill admission requester must be a well-formed principal")
    if not _is_independent_approver(admission.get("approved_by")):
        errors.append("skill admission requires approval by an independent human principal")
    if admission.get("requested_by") == admission.get("approved_by"):
        errors.append("skill admission requester and approver must be distinct")

    if grant.get("decision") != "approved":
        errors.append("runtime grant decision must be approved")
    if not _is_principal(grant.get("requested_by")):
        errors.append("runtime grant requester must be a well-formed principal")
    if not _is_independent_approver(grant.get("approved_by")):
        errors.append("runtime grant requires approval by an independent human principal")
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

    errors.extend(authorization_errors(
        approval_registry, grant_id=grant["grant_id"], subject_kind="skill",
        subject_id=manifest.get("id"), subject_version=manifest.get("version"),
        subject_digest=manifest_digest(manifest), authority_ceiling=grant["authority_ceiling"],
        allowed_actions=grant["allowed_actions"], requested_by=grant["requested_by"],
        approved_by=grant["approved_by"], decision_ref=grant["admission_ref"], subject_contract={},
    ))
    return errors


def load_skill_for_execution(
    manifest: dict[str, Any],
    source_text: str,
    grant: Any,
    *,
    now: str,
    approval_registry: Any = None,
) -> dict[str, Any]:
    errors = validate_manifest_integrity(manifest, source_text)
    errors.extend(validate_skill_grant(manifest, grant, now=now, approval_registry=approval_registry))
    return {
        "loaded": not errors,
        "skill_id": manifest.get("id"),
        "skill_version": manifest.get("version"),
        "grant_id": grant.get("grant_id") if isinstance(grant, dict) else None,
        "errors": errors,
    }


def _tool_registry_by_ref(tool_registry: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Index a versioned tool registry without guessing or silently replacing entries."""
    errors: list[str] = []
    if tool_registry.get("schema_version") != "tool-registry.v1":
        return {}, ["unsupported tool registry schema version"]

    indexed: dict[str, dict[str, Any]] = {}
    for tool in tool_registry.get("tools", []):
        ref = tool.get("ref")
        if not isinstance(ref, str) or not ref:
            errors.append("tool registry entry is missing ref")
            continue
        if ref in indexed:
            errors.append(f"tool registry contains duplicate ref: {ref}")
            continue
        indexed[ref] = tool
    return indexed, errors


def _model_tool_name(ref: str, action: str) -> str:
    """Create a stable model-visible name from an immutable tool ref and action."""
    tool_key = ref.split("@", 1)[0].removeprefix("tool.")
    return f"{tool_key.replace('.', '_').replace('-', '_')}__{action}"


def map_skill_tools_to_runtime_bindings(
    skill_manifest: dict[str, Any],
    tool_registry: dict[str, Any],
) -> dict[str, Any]:
    """Project canonical Skill tools onto concrete, version-pinned runtime refs.

    This mapping changes representation only. It neither admits a candidate nor
    grants authority; an unmapped name/action fails closed instead of being
    carried forward as an ambiguous runtime capability.
    """
    registry_by_ref, errors = _tool_registry_by_ref(tool_registry)
    registry_by_name: dict[str, dict[str, Any]] = {}
    for registered in registry_by_ref.values():
        canonical_name = registered.get("canonical_name")
        if not isinstance(canonical_name, str) or not canonical_name:
            errors.append(f"tool registry entry is missing canonical_name: {registered.get('ref')}")
            continue
        if canonical_name in registry_by_name:
            errors.append(f"tool registry contains duplicate canonical name: {canonical_name}")
            continue
        registry_by_name[canonical_name] = registered

    bindings: list[dict[str, Any]] = []
    if not errors:
        for declared in skill_manifest.get("tools", []):
            name = declared.get("name")
            registered = registry_by_name.get(name)
            if not registered:
                errors.append(f"canonical tool name is not registered: {name}")
                continue
            registered_actions = {action.get("name") for action in registered.get("actions", [])}
            missing_actions = sorted(set(declared.get("actions", [])) - registered_actions)
            if missing_actions:
                errors.append(
                    f"canonical tool actions are not registered: {name}#{', '.join(missing_actions)}"
                )
                continue
            bindings.append(
                {
                    "ref": registered["ref"],
                    "allowed_actions": list(declared.get("actions", [])),
                }
            )

    return {
        "mapped": not errors,
        "bindings": bindings if not errors else [],
        "errors": errors,
    }


def resolve_model_visible_tools(
    runtime_manifest: dict[str, Any],
    tool_registry: dict[str, Any],
) -> dict[str, Any]:
    """Resolve allowlisted tool actions into model-visible function schemas.

    This is deliberately a projection, not an authority grant. Candidate, paused,
    or policy-invalid manifests return no functions. Unknown refs and actions fail
    closed rather than falling back to a broad vendor tool definition.
    """
    errors: list[str] = []
    if runtime_manifest.get("status") != "active":
        errors.append("model tool adapter rejects non-active runtime manifest")
    errors.extend(validate_manifest_admission(runtime_manifest))

    registry_by_ref, registry_errors = _tool_registry_by_ref(tool_registry)
    errors.extend(registry_errors)
    emitted: list[dict[str, Any]] = []
    names: set[str] = set()

    if not errors:
        for binding in runtime_manifest.get("tools", []):
            ref = binding.get("ref")
            registered = registry_by_ref.get(ref)
            if not registered:
                errors.append(f"tool ref is not registered: {ref}")
                continue

            actions = {action.get("name"): action for action in registered.get("actions", [])}
            if len(actions) != len(registered.get("actions", [])):
                errors.append(f"tool registry contains duplicate action names: {ref}")
                continue
            for action_name in binding.get("allowed_actions", []):
                action = actions.get(action_name)
                if not action:
                    errors.append(f"tool action is not registered: {ref}#{action_name}")
                    continue
                try:
                    Draft202012Validator.check_schema(action["parameter_schema"])
                except Exception as exc:  # jsonschema exposes several exception types.
                    errors.append(f"invalid parameter schema for {ref}#{action_name}: {exc}")
                    continue
                name = _model_tool_name(ref, action_name)
                if name in names:
                    errors.append(f"duplicate model-visible tool name: {name}")
                    continue
                names.add(name)
                emitted.append(
                    {
                        "type": "function",
                        "function": {
                            "name": name,
                            "description": action["description"],
                            "parameters": action["parameter_schema"],
                            "strict": True,
                        },
                    }
                )

    return {
        "resolved": not errors,
        "manifest_key": runtime_manifest.get("manifest_key"),
        "tools": emitted if not errors else [],
        "errors": errors,
    }


def serialize_model_request(
    runtime_manifest: dict[str, Any],
    tool_registry: dict[str, Any],
    *,
    model: str,
    messages: list[dict[str, Any]],
) -> dict[str, Any]:
    """Produce the exact request payload that a provider adapter may submit.

    The function has no network side effects. It refuses serialization before the
    tool projection is resolved, so a later request adapter cannot accidentally
    emit a forbidden action schema.
    """
    if not model:
        raise ValueError("model is required")
    if not messages:
        raise ValueError("at least one message is required")
    resolution = resolve_model_visible_tools(runtime_manifest, tool_registry)
    if not resolution["resolved"]:
        raise ValueError("cannot serialize model request: " + "; ".join(resolution["errors"]))
    return {
        "model": model,
        "messages": messages,
        "tools": resolution["tools"],
    }


def build_model_tool_request_receipt(
    request: dict[str, Any],
    *,
    receipt_id: str,
    serialized_at: str,
    metrics: dict[str, int | float | None] | None = None,
) -> dict[str, Any]:
    """Capture schema exposure and cost/effort measurements without inventing data."""
    metric_names = (
        "input_tokens",
        "output_tokens",
        "cash_cost_usd",
        "latency_ms",
        "human_effort_minutes",
        "updater_upkeep_minutes",
    )
    observed = metrics or {}
    unknown = set(observed) - set(metric_names)
    if unknown:
        raise ValueError(f"unknown model request metrics: {', '.join(sorted(unknown))}")
    normalized = {name: observed.get(name) for name in metric_names}
    for name, value in normalized.items():
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0):
            raise ValueError(f"metric {name} must be a non-negative number or null")

    known_count = sum(value is not None for value in normalized.values())
    state = "not_observed" if known_count == 0 else "observed" if known_count == len(normalized) else "partial"
    names = [tool["function"]["name"] for tool in request.get("tools", [])]
    if not names:
        raise ValueError("model request receipt requires at least one emitted tool")
    return {
        "receipt_id": receipt_id,
        "request_sha256": hashlib.sha256(canonical_json_bytes(request)).hexdigest(),
        "serialized_at": serialized_at,
        "emitted_tool_names": names,
        "measurement_state": state,
        "metrics": normalized,
        "immutable": True,
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
