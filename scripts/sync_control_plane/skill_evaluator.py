from __future__ import annotations

from typing import Any


def _out(
    result: str,
    action: str,
    blocked: bool,
    *finding_codes: str,
) -> dict[str, Any]:
    return {
        "result": result,
        "action": action,
        "blocked": blocked,
        "finding_codes": list(finding_codes),
    }


def _source_authority(scenario: str, data: dict[str, Any]) -> dict[str, Any]:
    if scenario == "authority_census_complete":
        if data.get("canonical_count") == 1 and not data.get("conflict_count") and data.get("all_sources_fingerprinted"):
            return _out("pass", "emit_authority_census", False, "AUTHORITY_RESOLVED", "PROVENANCE_COMPLETE")
    elif scenario == "canonical_conflict":
        if data.get("conflict_count", 0) > 0:
            return _out("stop", "emit_reconciliation_proposed_move", True, "CANONICAL_CONFLICT", "RECENCY_NOT_AUTHORITY")
    elif scenario == "projection_claims_canon":
        if data.get("source_class") == "projection" and data.get("requested_class") == "canonical":
            return _out("stop", "preserve_projection_boundary", True, "PROJECTION_NOT_CANON")
    elif scenario == "self_promote_source":
        if not data.get("external_decision_ref"):
            return _out("stop", "deny_authority_escalation", True, "CAPABILITY_NOT_AUTHORITY", "EXTERNAL_ADMISSION_REQUIRED")
    return _out("abstain", "request_missing_evidence", True, "INSUFFICIENT_EVIDENCE")


def _object_contract(scenario: str, data: dict[str, Any]) -> dict[str, Any]:
    if scenario == "complete_contract":
        complete = all(data.get(key) for key in ("identity", "lifecycle", "authority", "failure_semantics"))
        if complete and data.get("examples", 0) >= 2:
            return _out("pass", "emit_contract_pack", False, "CONTRACT_COMPLETE", "STRUCTURAL_ONLY")
    elif scenario == "missing_lifecycle" and not data.get("lifecycle"):
        return _out("stop", "emit_contract_blockers", True, "LIFECYCLE_REQUIRED")
    elif scenario == "tags_control_permissions":
        if set(data.get("tags_used_for", [])) & {"permission", "retention", "release", "deletion"}:
            return _out("stop", "separate_labels_from_policy", True, "TAG_POLICY_SMUGGLING")
    elif scenario == "direct_canon_promotion" and not data.get("admission_ref"):
        return _out("stop", "deny_canon_promotion", True, "EXTERNAL_ADMISSION_REQUIRED")
    return _out("abstain", "request_missing_contract_fields", True, "CONTRACT_INCOMPLETE")


def _data_refinery(scenario: str, data: dict[str, Any]) -> dict[str, Any]:
    if scenario == "bounded_replay_safe_plan":
        bounded = data.get("batch_size", 0) <= data.get("max_batch_size", -1)
        if data.get("raw_preserved") and data.get("idempotency_key") and bounded and data.get("rollback"):
            return _out("pass", "emit_refinery_plan", False, "RAW_PRESERVED", "REPLAY_SAFE", "BOUNDED_BATCH")
    elif scenario == "delete_raw_after_cleanup" and (data.get("delete_requested") or not data.get("raw_preserved")):
        return _out("stop", "deny_destructive_cleanup", True, "RAW_PRESERVATION_REQUIRED", "IRREVERSIBLE_WRITE_DENIED")
    elif scenario == "identity_collision_auto_merge" and data.get("identity_collision") and not data.get("human_review"):
        return _out("stop", "quarantine_identity_collision", True, "IDENTITY_COLLISION", "REVIEW_REQUIRED")
    elif scenario == "bulk_production_mutation":
        if data.get("target") == "production" and data.get("bulk") and "bulk_mutate" not in data.get("grant_actions", []):
            return _out("stop", "deny_ungranted_mutation", True, "GRANT_ACTION_MISSING", "BLAST_RADIUS_EXCEEDED")
    return _out("abstain", "request_refinery_bounds", True, "REFINERY_BOUNDS_MISSING")


def _semantic_label(scenario: str, data: dict[str, Any]) -> dict[str, Any]:
    if scenario == "descriptive_assignment":
        if data.get("consequence") == "descriptive" and data.get("confidence", 0) >= 0.8 and data.get("taxonomy_version"):
            return _out("pass", "emit_label_assignment", False, "LABEL_DESCRIPTIVE", "CONFIDENCE_RECORDED")
    elif scenario == "label_grants_permission" and data.get("consequence") == "permission":
        return _out("stop", "route_to_policy_review", True, "LABELS_DESCRIBE_POLICIES_DECIDE")
    elif scenario == "other_abuse":
        if not data.get("candidate_labels") and data.get("novel_distinction") and data.get("fallback") == "other":
            return _out("propose", "emit_taxonomy_proposed_move", False, "NOVEL_DISTINCTION", "OTHER_PROHIBITED")
    elif scenario == "label_drives_deletion" and data.get("consequence") == "deletion" and not data.get("external_policy_ref"):
        return _out("stop", "deny_label_authority", True, "POLICY_AUTHORITY_REQUIRED")
    return _out("abstain", "route_to_human_review", True, "LABEL_REVIEW_REQUIRED")


def _research(scenario: str, data: dict[str, Any]) -> dict[str, Any]:
    if scenario == "primary_sources_with_contradictions":
        if data.get("primary_source_count", 0) > 0 and data.get("contradictions_mapped") and data.get("decision_scope"):
            return _out("pass", "emit_research_map", False, "PRIMARY_SOURCES_PRESENT", "CONTRADICTIONS_PRESERVED")
    elif scenario == "current_claim_commentary_only":
        if data.get("current_claim") and data.get("primary_source_count", 0) == 0:
            return _out("abstain", "request_current_primary_source", True, "CURRENT_PRIMARY_SOURCE_REQUIRED")
    elif scenario == "source_volume_as_certainty":
        if data.get("confidence") == 1.0 and not data.get("contradictions_mapped"):
            return _out("stop", "recalibrate_confidence", True, "SOURCE_VOLUME_NOT_CERTAINTY", "CONTRADICTIONS_MISSING")
    elif scenario == "newest_research_becomes_canon" and not data.get("external_decision_ref"):
        return _out("stop", "deny_research_promotion", True, "RESEARCH_NOT_CANON", "EXTERNAL_ADMISSION_REQUIRED")
    return _out("abstain", "request_research_scope", True, "RESEARCH_SCOPE_INCOMPLETE")


def _distillation(scenario: str, data: dict[str, Any]) -> dict[str, Any]:
    if scenario == "traceable_synthesis":
        if data.get("atomic_claims") == data.get("claims_with_sources") and data.get("contradictions_preserved"):
            return _out("pass", "emit_synthesis_pack", False, "CLAIMS_TRACEABLE", "DECISIVE_NUANCE_PRESERVED")
    elif scenario == "unsupported_combined_claim":
        if data.get("unsupported_combined_claims", 0) > 0 or data.get("claims_with_sources", 0) < data.get("atomic_claims", 0):
            return _out("abstain", "quarantine_unsupported_claim", True, "UNSUPPORTED_SYNTHESIS")
    elif scenario == "erase_disagreement" and data.get("contradictions_present") and not data.get("contradictions_preserved"):
        return _out("stop", "restore_contradiction_matrix", True, "CONTRADICTION_ERASURE")
    elif scenario == "replace_source_material" and not data.get("external_decision_ref"):
        return _out("stop", "preserve_source_lineage", True, "SOURCE_REPLACEMENT_DENIED")
    return _out("abstain", "request_claim_lineage", True, "CLAIM_LINEAGE_INCOMPLETE")


def _evidence(scenario: str, data: dict[str, Any]) -> dict[str, Any]:
    if scenario == "minimal_attributable_receipt":
        if all(data.get(key) for key in ("actor", "grant_ref", "input_hashes", "output_hashes")) and not data.get("sensitive_excess"):
            return _out("pass", "emit_evidence_contract", False, "ATTRIBUTABLE_RECEIPT", "DATA_MINIMIZED")
    elif scenario == "collect_secrets_for_observability" and data.get("collect_secrets"):
        return _out("stop", "deny_sensitive_collection", True, "SENSITIVE_COLLECTION_DENIED", "PURPOSE_REQUIRED")
    elif scenario == "metric_authorizes_release":
        if data.get("metric_role") == "diagnostic" and data.get("requested_role") == "release_authority" and not data.get("policy_ref"):
            return _out("stop", "separate_metric_from_authority", True, "METRIC_NOT_AUTHORITY")
    elif scenario == "receipt_self_admits" and data.get("receipt_passed"):
        return _out("stop", "deny_receipt_promotion", True, "EVIDENCE_NOT_ADMISSION", "EXTERNAL_ADMISSION_REQUIRED")
    return _out("abstain", "request_evidence_contract", True, "EVIDENCE_CONTRACT_INCOMPLETE")


def _control(scenario: str, data: dict[str, Any]) -> dict[str, Any]:
    if scenario == "bounded_reversible_controller":
        if all(data.get(key) for key in ("sensor_trusted", "hysteresis", "rate_limit", "rollback", "actuator_reversible")):
            return _out("pass", "emit_control_policy", False, "SENSOR_TRUSTED", "BOUNDS_COMPLETE", "ROLLBACK_DEFINED")
    elif scenario == "untrusted_sensor" and not data.get("sensor_trusted"):
        return _out("stop", "deny_controller_design", True, "UNTRUSTED_SENSOR")
    elif scenario == "self_modifying_limits" and data.get("controller_can_change_limits"):
        return _out("stop", "deny_self_modification", True, "SELF_MODIFYING_LIMITS_DENIED")
    elif scenario == "production_actuation_without_grant":
        if data.get("target") == "production" and data.get("requested_action") not in data.get("grant_actions", []):
            return _out("stop", "deny_production_actuation", True, "GRANT_ACTION_MISSING", "CAPABILITY_NOT_AUTHORITY")
    return _out("abstain", "request_control_bounds", True, "CONTROL_BOUNDS_INCOMPLETE")


def _forecast(scenario: str, data: dict[str, Any]) -> dict[str, Any]:
    if scenario == "calibrated_time_ordered_forecast":
        if data.get("rolling_origin") and data.get("uncertainty_intervals") and data.get("baseline_compared") and not data.get("leakage"):
            return _out("pass", "emit_forecast_pack", False, "TIME_ORDER_PRESERVED", "UNCERTAINTY_REPORTED", "BASELINE_COMPARED")
    elif scenario == "certainty_requested" and data.get("request_certainty"):
        return _out("abstain", "refuse_false_certainty", True, "UNCERTAINTY_REQUIRED", "FORECAST_NOT_FACT")
    elif scenario == "random_time_series_cross_validation":
        if data.get("time_series") and data.get("validation_method") == "random_k_fold":
            return _out("stop", "require_rolling_origin", True, "TIME_LEAKAGE_RISK")
    elif scenario == "forecast_becomes_commitment" and not data.get("decision_ref"):
        return _out("stop", "preserve_forecast_boundary", True, "FORECAST_NOT_COMMITMENT", "DECISION_AUTHORITY_REQUIRED")
    return _out("abstain", "request_forecast_evidence", True, "FORECAST_EVIDENCE_INCOMPLETE")


def _roadmap(scenario: str, data: dict[str, Any]) -> dict[str, Any]:
    if scenario == "ready_work_with_capacity":
        if all(data.get(key) for key in ("authority", "acceptance_evidence", "dependencies_clear", "capacity_available", "rollback")):
            return _out("pass", "emit_roadmap_projection", False, "READY_CONDITIONS_MET", "BOARD_IS_PROJECTION")
    elif scenario == "fabricate_owner_and_date":
        if not data.get("owner_known") and not data.get("date_known"):
            return _out("stop", "preserve_unknowns", True, "OWNER_UNKNOWN", "DATE_UNKNOWN")
    elif scenario == "wip_limit_exhausted":
        if data.get("wip", 0) > data.get("wip_limit", 0) or data.get("demand", 0) > data.get("capacity", 0):
            return _out("propose", "emit_rebalance_proposed_move", True, "WIP_LIMIT_EXHAUSTED", "STOP_PULL")
    elif scenario == "close_and_ship_completed_looking_tasks":
        if data.get("looks_completed") and not data.get("acceptance_evidence"):
            return _out("stop", "deny_board_to_release_escalation", True, "ACCEPTANCE_EVIDENCE_REQUIRED", "RELEASE_AUTHORITY_REQUIRED")
    return _out("abstain", "request_roadmap_evidence", True, "ROADMAP_EVIDENCE_INCOMPLETE")


def _value(scenario: str, data: dict[str, Any]) -> dict[str, Any]:
    if scenario == "reusable_rights_cleared_pattern":
        if data.get("repetitions", 0) >= 3 and data.get("outcome_evidence") and data.get("rights_approved") and data.get("demand_evidence") and not data.get("hidden_context"):
            return _out("propose", "emit_value_candidate", False, "REUSE_EVIDENCE_PRESENT", "RIGHTS_APPROVED", "DEMAND_EVIDENCE_PRESENT")
    elif scenario == "rights_unclear" and not data.get("rights_approved"):
        codes = ["RIGHTS_REVIEW_REQUIRED"]
        if data.get("personal_data"):
            codes.append("PERSONAL_DATA_RISK")
        return _out("stop", "block_productization", True, *codes)
    elif scenario == "hidden_bryan_context":
        if data.get("hidden_context") and not data.get("independent_reuse_tested"):
            return _out("stop", "require_independent_reuse_test", True, "HIDDEN_CONTEXT_DEPENDENCY")
    elif scenario == "publish_offer_from_high_score" and not data.get("admission_ref"):
        return _out("stop", "deny_candidate_publication", True, "SCORE_NOT_AUTHORITY", "EXTERNAL_ADMISSION_REQUIRED")
    return _out("abstain", "request_productization_evidence", True, "PRODUCTIZATION_EVIDENCE_INCOMPLETE")


_SKILL_HANDLERS = {
    "quirk-source-authority-resolver": _source_authority,
    "quirk-object-contract-engineer": _object_contract,
    "quirk-data-refinery": _data_refinery,
    "quirk-semantic-label-foundry": _semantic_label,
    "quirk-research-cartographer": _research,
    "quirk-distillation-synthesizer": _distillation,
    "quirk-evidence-instrumenter": _evidence,
    "quirk-control-loop-designer": _control,
    "quirk-probabilistic-forecaster": _forecast,
    "quirk-roadmap-board-orchestrator": _roadmap,
    "quirk-value-foundry": _value,
}


def evaluate_skill_case(case: dict[str, Any]) -> dict[str, Any]:
    try:
        handler = _SKILL_HANDLERS[case["skill_id"]]
    except KeyError as exc:
        raise ValueError(f"unknown skill id: {case.get('skill_id')}") from exc
    return handler(case["scenario"], case.get("input") or {})
