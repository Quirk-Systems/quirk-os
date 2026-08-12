from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def validate_manifest_admission(manifest: dict[str, Any]) -> list[str]:
    """Return policy violations that JSON Schema cannot express alone."""
    errors: list[str] = []
    if manifest.get("status") != "active":
        return errors

    admission = manifest.get("admission") or {}
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
    if requested_by == approved_by:
        errors.append("requester may not approve its own manifest transition")
    if admission.get("evaluated_content_hash") != manifest.get("content_hash"):
        errors.append("evaluated content hash must match manifest content hash")
    if manifest.get("metadata", {}).get("self_requested") and requested_by == manifest.get("manifest_key"):
        errors.append("self-requested activation requires independent human or authorized service approval")

    domains = set(manifest.get("domains", []))
    if "data_productization" in domains:
        rights = manifest.get("rights_review") or {}
        if not (
            rights.get("outcome") == "approved"
            and rights.get("license_verified") is True
            and rights.get("privacy_review") == "approved"
            and rights.get("provenance_complete") is True
        ):
            errors.append("data productization requires approved rights, license, privacy, and provenance review")

    if manifest.get("manifest_kind") == "orchestrator" and len(manifest.get("skill_refs", [])) > 1:
        trigger = manifest.get("trigger_contract") or {}
        if trigger.get("collision_behavior") != "block" or not trigger.get("routing_policy"):
            errors.append("multi-skill orchestrator requires fail-closed trigger routing contract")

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
}


def evaluate_fixture(name: str, case: dict[str, Any]) -> dict[str, Any]:
    try:
        handler = _HANDLERS[name]
    except KeyError as exc:
        raise ValueError(f"unknown fixture: {name}") from exc
    return handler(case)
