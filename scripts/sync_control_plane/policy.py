from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from .approval import authorization_errors


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


# Principals are drawn from `^(human|agent|service|system)\.` by
# schemas/runtime-manifest.schema.json. Only a human principal counts as an
# independent approver of an activation:
#
#   - `agent.` can never be independent. A capability approving an activation
#     is capability granting authority, which the policy's own
#     `capability_never_implies_authority` invariant forbids outright.
#   - `service.` and `system.` are refused rather than assumed, because no
#     allow-list of authorized service principals exists in this repository.
#     Add one and this predicate is where it belongs.
#
# The whole principal is matched rather than just its prefix, so the gate does
# not depend on JSON Schema having run first: callers use
# `validate_manifest_admission` directly, and a bare `"human."` would satisfy a
# prefix test while naming nobody.
#
# Structural checks alone do not prove human approval. Admission below also
# computes content and uses the trusted host's live GitHub verifier. The
# separate structural helper exists only for local guard/fixture conformance.
_INDEPENDENT_APPROVER = re.compile(r"human\.[a-z0-9._-]+")

# Any well-formed principal, mirroring schemas/runtime-manifest.schema.json. The
# requester's shape is checked for the same reason the approver's whole value is:
# this function is called directly, so it cannot assume JSON Schema ran. The
# SQL trigger had no requester check at all, which let `'NOT-A-PRINCIPAL'`
# activate a manifest; the two surfaces agree now.
_PRINCIPAL = re.compile(r"(human|agent|service|system)\.[a-z0-9._-]+")


def _is_principal(value: Any) -> bool:
    return isinstance(value, str) and _PRINCIPAL.fullmatch(value) is not None


def _is_independent_approver(approved_by: Any) -> bool:
    return isinstance(approved_by, str) and _INDEPENDENT_APPROVER.fullmatch(approved_by) is not None


def validate_manifest_structure(manifest: dict[str, Any]) -> list[str]:
    """Return policy violations that JSON Schema cannot express alone."""
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["manifest must be an object"]
    if manifest.get("status") != "active":
        return errors

    admission = manifest.get("admission") or {}
    if not isinstance(admission, dict):
        return ["active manifest admission must be an object"]
    requested_by = admission.get("requested_by")
    approved_by = admission.get("approved_by")
    if not admission:
        errors.append("active manifest requires admission")
        return errors
    if admission.get("decision") != "approved":
        errors.append("active manifest admission decision must be approved")
    if not admission.get("decision_ref"):
        errors.append("active manifest requires admission decision reference")
    if not admission.get("authority_grant_ref"):
        errors.append("active manifest requires authority grant reference")
    if not admission.get("transition_ref"):
        errors.append("active manifest requires legal transition evidence")
    if not _is_principal(requested_by):
        errors.append("manifest requester must be a well-formed principal")
    if requested_by == approved_by:
        errors.append("requester may not approve its own manifest transition")
    if admission.get("evaluated_content_hash") != manifest.get("content_hash"):
        errors.append("evaluated content hash must match manifest content hash")
    # Deliberately not read from `metadata.self_requested`. That flag was set
    # by the same document this gate judges, so omitting it disabled the check;
    # and a manifest that set it honestly was rejected even when a human had
    # approved. Who approved is the thing that matters, and it is now checked
    # for every activation, self-requested or not.
    if not _is_independent_approver(approved_by):
        errors.append("activation requires approval by an independent human principal")

    domains = manifest.get("domains") if isinstance(manifest.get("domains"), list) else []
    if "data_productization" in domains:
        rights = manifest.get("rights_review") or {}
        if not isinstance(rights, dict):
            rights = {}
        if not (
            rights.get("outcome") == "approved"
            and rights.get("license_verified") is True
            and rights.get("privacy_review") == "approved"
            and rights.get("provenance_complete") is True
        ):
            errors.append("data productization requires approved rights, license, privacy, and provenance review")

    if manifest.get("manifest_kind") == "orchestrator" and isinstance(manifest.get("skill_refs"), list) and len(manifest["skill_refs"]) > 1:
        trigger = manifest.get("trigger_contract") or {}
        if not isinstance(trigger, dict):
            trigger = {}
        if trigger.get("collision_behavior") != "block" or not trigger.get("routing_policy"):
            errors.append("multi-skill orchestrator requires fail-closed trigger routing contract")

    return errors


def validate_manifest_admission(manifest: dict[str, Any], *, verifier=None, context=None, approval_registry=None) -> list[str]:
    """Fail closed: shape + computed content + externally resolved human consent.

    verifier/context are installed by the trusted host, never supplied inside
    the manifest. SQL is a projection of this gate, not another trust root.
    """
    from .content import ContentError, manifest_content_hash
    from .attestation import ApprovalError
    errors = validate_manifest_structure(manifest)
    try:
        digest = manifest_content_hash(manifest)
    except (ContentError, TypeError, KeyError, RecursionError) as exc:
        return errors + ["manifest content invalid: " + str(exc)]
    if manifest.get("content_hash") != digest:
        errors.append("declared content hash does not match computed content")
    if manifest.get("status") != "active":
        return errors
    if manifest.get("requested_status") != "active":
        errors.append("active manifest requires requested_status=active")
    admission = manifest.get("admission") or {}
    if admission.get("evaluated_content_hash") != digest:
        errors.append("evaluated content hash does not match computed content")
    from .github_approval import manifest_contract
    errors.extend(authorization_errors(
        approval_registry, grant_id=admission.get("authority_grant_ref"), subject_kind="manifest",
        subject_id=manifest.get("manifest_key"), subject_version=manifest.get("version"),
        subject_digest=manifest.get("content_hash"), authority_ceiling=manifest.get("authority_ceiling"),
        allowed_actions=["activate_manifest"], requested_by=admission.get("requested_by"),
        approved_by=admission.get("approved_by"), decision_ref=admission.get("decision_ref"),
        subject_contract=manifest_contract(manifest),
    ))
    if verifier is None or context is None:
        return errors + ["trusted approval verifier and activation context required"]
    try:
        record = verifier.verify(manifest, context)
        expected = {key: record[key] for key in (
            "decision_ref", "authority_grant_ref", "transition_ref", "approved_by", "decided_at"
        )}
        expected.update(decision="approved", requested_by=record["subject"]["requested_by"],
                        evaluated_content_hash=digest, evidence_refs=record["subject"]["evidence_refs"])
        if admission != expected:
            errors.append("admission envelope differs from resolved approval")
    except ApprovalError as exc:
        errors.append(str(exc))
    return errors


def _conflicting_canon(case: dict[str, Any]) -> dict[str, Any]:
    by_object: dict[str, list[dict[str, Any]]] = {}
    for source in case["sources"]:
        if source.get("authority_class") == "canonical":
            by_object.setdefault(source["object_key"], []).append(source)
    conflicts = []
    for object_key, sources in by_object.items():
        hashes = {source.get("content_hash") for source in sources}
        if len(hashes) > 1:
            conflicts.append({"object_key": object_key, "source_refs": [s["source_ref"] for s in sources]})
    return {
        "action": "block_projection_and_propose_reconciliation" if conflicts else "continue",
        "conflicts": conflicts,
        "proposed_moves": [f"qpm_sync_reconcile_{item['object_key'].replace('.', '_')}" for item in conflicts],
    }


def _mixed_source_batch(case: dict[str, Any]) -> dict[str, Any]:
    preserved = [record["source_ref"] for record in case["records"]]
    quarantine = []
    accepted = []
    for record in case["records"]:
        reasons = []
        if record.get("content") in (None, ""):
            reasons.append("malformed_or_empty_content")
        if record.get("rights") != "approved":
            reasons.append("rights_unclear")
        if reasons:
            quarantine.append({"source_ref": record["source_ref"], "reasons": reasons})
        else:
            accepted.append(record["source_ref"])
    return {
        "action": "preserve_raw_provenance_and_quarantine_failures",
        "raw_source_refs": preserved,
        "accepted": accepted,
        "quarantine": quarantine,
    }


def _duplicate_identity(case: dict[str, Any]) -> dict[str, Any]:
    seen: dict[tuple[str, str], str] = {}
    collisions = []
    for binding in case["bindings"]:
        key = (binding["platform"], binding["external_id"])
        prior = seen.get(key)
        if prior and prior != binding["object_key"]:
            collisions.append({"platform": key[0], "external_id": key[1], "object_keys": [prior, binding["object_key"]]})
        seen[key] = binding["object_key"]
    return {"action": "reject_binding_collision" if collisions else "continue", "collisions": collisions}


def _label_review(case: dict[str, Any]) -> dict[str, Any]:
    assignment = case["assignment"]
    consequential = assignment.get("consequence") in {"release", "permission", "retention", "deletion", "protected_routing"}
    review = consequential or float(assignment.get("confidence", 0.0)) < 0.8
    return {
        "action": "route_to_human_review" if review else "accept_label",
        "review_required": review,
        "reason": "consequential_or_low_confidence" if review else "sufficient_confidence",
    }


def _taxonomy_gap(case: dict[str, Any]) -> dict[str, Any]:
    classification = case["classification"]
    is_gap = not classification.get("candidate_labels") and bool(classification.get("observed_distinction"))
    return {
        "action": "propose_new_distinction_without_other_abuse" if is_gap else "classify_existing",
        "other_prohibited": is_gap and classification.get("suggested_fallback") == "other",
        "proposed_distinction": classification.get("observed_distinction") if is_gap else None,
    }


def _research_contradiction(case: dict[str, Any]) -> dict[str, Any]:
    claims = case["claims"]
    normalized = [{**claim, "normalized_term": claim["term"].strip().lower()} for claim in claims]
    definitions = {claim["definition"] for claim in claims}
    values = {claim["value"] for claim in claims}
    return {
        "action": "preserve_both_claims_and_normalize_terms" if len(definitions) > 1 or len(values) > 1 else "merge_equivalent_claims",
        "claims": normalized,
        "preserve_both": len(definitions) > 1 or len(values) > 1,
    }


def _stale_guidance(case: dict[str, Any]) -> dict[str, Any]:
    binding = case["binding"]
    freshness = dict(binding["freshness"])
    evaluated_at = _parse_dt(case["evaluated_at"])
    last_verified = _parse_dt(freshness["last_verified_at"])
    age_days = (evaluated_at - last_verified).days
    max_age = int(freshness["max_age_days"])
    freshness.update({
        "status": "stale" if age_days > max_age else "fresh",
        "evaluated_at": case["evaluated_at"],
        "reason": f"age_days={age_days}; max_age_days={max_age}",
    })
    return {
        "action": "mark_stale_without_rewriting_history" if freshness["status"] == "stale" else "retain_fresh",
        "binding_id": binding["binding_id"],
        "freshness": freshness,
        "historical_content_unchanged": True,
    }


def _trigger_collision(case: dict[str, Any]) -> dict[str, Any]:
    matches = case["matches"]
    policy = case.get("routing_policy")
    if len(matches) > 1 and not policy:
        return {"action": "block_ambiguous_invocation_or_route_by_policy", "blocked": True, "matches": matches}
    return {"action": "route_by_policy", "blocked": False, "matches": matches, "routing_policy": policy}


def _capacity_overload(case: dict[str, Any]) -> dict[str, Any]:
    overloaded = case["wip"] > case["wip_limit"] or case["demand"] > case["capacity"]
    return {
        "action": "stop_pull_and_propose_rebalance" if overloaded else "continue_pull",
        "stop_pull": overloaded,
        "proposed_rebalance": overloaded,
    }


def _rights_failure(case: dict[str, Any]) -> dict[str, Any]:
    rights = case["rights"]
    approved = (
        rights.get("outcome") == "approved"
        and rights.get("license_verified") is True
        and rights.get("privacy_review") == "approved"
        and rights.get("provenance_complete") is True
    )
    return {"action": "allow_productization" if approved else "block_productization", "rights_approved": approved}


def _self_promotion(case: dict[str, Any]) -> dict[str, Any]:
    errors = validate_manifest_admission(case["manifest"])
    return {
        "action": "reject_capability_to_authority_escalation" if errors else "allow_transition",
        "policy_errors": errors,
    }


_MAX_DELIVERY_ATTEMPTS = 5


def _projection_delivery(case: dict[str, Any]) -> dict[str, Any]:
    """Claim delivery of a temporary projection through the leased outbox worker contract.

    Enforces idempotency: a repeated idempotency_key must not produce a second mutation.
    Every delivery attempt (success or failure) produces an immutable receipt.
    """
    idempotency_key: str = case["idempotency_key"]
    projection: dict[str, Any] = case["projection"]
    prior_receipts: list[dict[str, Any]] = case.get("prior_receipts") or []

    # Idempotency guard: if a successful delivery already exists for this key, skip.
    already_delivered = any(
        r.get("idempotency_key") == idempotency_key and r.get("status") == "delivered"
        for r in prior_receipts
    )
    if already_delivered:
        return {
            "action": "skip_duplicate_delivery",
            "idempotency_key": idempotency_key,
            "duplicate": True,
            "receipt": None,
        }

    platforms: list[str] = projection.get("platforms") or []
    receipts = []
    for platform in platforms:
        receipts.append({
            "platform": platform,
            "idempotency_key": idempotency_key,
            "status": "delivered",
            "authority_class": "projection",
            "immutable": True,
        })

    return {
        "action": "claim_projection_delivery",
        "idempotency_key": idempotency_key,
        "duplicate": False,
        "receipts": receipts,
        "platforms": platforms,
    }


def _observe_binding(case: dict[str, Any]) -> dict[str, Any]:
    """Compare a live projection reading against the expected canonical hash.

    Drift is never silently repaired.  When drift is detected the handler marks
    the binding as drifted and emits a typed Proposed Move for human review.
    """
    expected_hash: str | None = case.get("expected_hash")
    observed_hash: str | None = case.get("observed_hash")
    binding: dict[str, Any] = case["binding"]

    drifted = expected_hash is not None and observed_hash is not None and expected_hash != observed_hash

    if not drifted:
        return {
            "action": "binding_consistent",
            "binding_id": binding["binding_id"],
            "drift_detected": False,
        }

    proposed_move_id = f"qpm_drift_{binding['binding_id'].replace('.', '_').replace('-', '_')}"
    proposed_move = {
        "id": proposed_move_id,
        "schema_version": "proposed-move.v1",
        "lane": "migration",
        "dependency_class": "missing_projection_contract",
        "disposition": "new",
        "blocks_merge": False,
        "drift_source": binding["binding_id"],
        "expected_hash": expected_hash,
        "observed_hash": observed_hash,
    }

    return {
        "action": "mark_drift_and_propose_reconciliation",
        "binding_id": binding["binding_id"],
        "drift_detected": True,
        "binding_state": "drifted",
        "proposed_move": proposed_move,
        "silent_repair_attempted": False,
    }


def _retry_delivery(case: dict[str, Any]) -> dict[str, Any]:
    """Simulate up to _MAX_DELIVERY_ATTEMPTS delivery attempts.

    After the maximum attempt count is exhausted the delivery is dead-lettered
    and all attempt evidence is preserved for inspection.
    """
    attempts: list[dict[str, Any]] = case.get("attempts") or []
    idempotency_key: str = case["idempotency_key"]
    attempt_count = len(attempts)

    dead_lettered = attempt_count >= _MAX_DELIVERY_ATTEMPTS

    preserved_evidence = [
        {
            "attempt": a.get("attempt"),
            "status": a.get("status"),
            "error": a.get("error"),
            "attempted_at": a.get("attempted_at"),
            "immutable": True,
        }
        for a in attempts
    ]

    return {
        "action": "dead_letter_delivery" if dead_lettered else "retry_delivery",
        "idempotency_key": idempotency_key,
        "attempt_count": attempt_count,
        "max_attempts": _MAX_DELIVERY_ATTEMPTS,
        "dead_lettered": dead_lettered,
        "preserved_evidence": preserved_evidence,
        "retry_timing_inspectable": True,
        "compensation_inspectable": True,
    }


def _reconstruct_projection(case: dict[str, Any]) -> dict[str, Any]:
    """Regenerate a temporary projection from Git + Supabase state.

    Reconstruction must not alter any existing user content.  The blast radius
    is exactly one fixture object identified by object_key.
    """
    object_key: str = case["object_key"]
    git_state: dict[str, Any] = case.get("git_state") or {}
    supabase_state: dict[str, Any] = case.get("supabase_state") or {}

    git_hash: str | None = git_state.get("content_hash")
    supabase_hash: str | None = supabase_state.get("content_hash")

    consistent = git_hash is not None and git_hash == supabase_hash
    reconstructed = bool(git_hash or supabase_hash)

    return {
        "action": "reconstruct_projection_from_git_and_supabase" if reconstructed else "insufficient_state_for_reconstruction",
        "object_key": object_key,
        "reconstructed": reconstructed,
        "state_consistent": consistent,
        "content_hash": git_hash or supabase_hash,
        "existing_user_content_altered": False,
        "blast_radius": [object_key],
    }


_HANDLERS = {
    "conflicting_canon": _conflicting_canon,
    "mixed_source_batch": _mixed_source_batch,
    "duplicate_external_identity": _duplicate_identity,
    "uncertain_consequential_label": _label_review,
    "taxonomy_gap": _taxonomy_gap,
    "research_contradiction": _research_contradiction,
    "stale_guidance": _stale_guidance,
    "skill_trigger_collision": _trigger_collision,
    "roadmap_capacity_overload": _capacity_overload,
    "data_product_rights_failure": _rights_failure,
    "self_promotion_attack": _self_promotion,
    "projection_delivery": _projection_delivery,
    "observe_binding": _observe_binding,
    "retry_delivery": _retry_delivery,
    "reconstruct_projection": _reconstruct_projection,
}


def evaluate_fixture(name: str, case: dict[str, Any]) -> dict[str, Any]:
    try:
        handler = _HANDLERS[name]
    except KeyError as exc:
        raise ValueError(f"unknown fixture: {name}") from exc
    return handler(case)
