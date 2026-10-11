"""Turn candidate evaluator failures into inert, evidence-bound repair routes."""

from __future__ import annotations

from typing import Any

from .pack import VERSION, evaluate_authority, evaluate_completion

ROUTE_VERSION = "verification-repair-routes.v0.1.0"

# Ordered by dependency: authority and input integrity precede evidence work.
# Every action is a proposal, never an executable grant or completion decision.
ROUTES = (
    ("authority", {
        "inactive_grant", "stale_grant", "object_out_of_scope", "verb_out_of_scope",
        "scope_out_of_scope", "resource_scope_exceeds_grant", "unowned_field_claim",
        "lease_widening", "missing_human_authority_source", "non_human_initiator",
        "self_approval", "untrusted_selector", "untrusted_authorizer",
        "permit_replayed", "permit_stale_or_mismatched",
    }, "Which independently resolved grant permits this exact actor, object, verb and scope now?",
     "Reconcile the existing grant and permit with their trusted authority source. Narrow the proposal if needed; present any genuinely missing decision to its human owner.",
     "Current grant and unused permit bound to the exact proposal; actual human response only if new authority is necessary.",
     "AUTHORITY_SOURCE"),
    ("input_contract", {"invalid_fixture", "unbound_dependency_digest"},
     "Which required input or dependency binding is missing or malformed?",
     "Repair the input contract from the source record, bind required digests, then rerun validation before drawing conclusions.",
     "Complete valid input with nonempty dependency bindings and a fresh evaluator result.",
     "CONTRACT_CHECK"),
    ("trajectory", {"invalid_trajectory"},
     "Which step violated the allowed execution path, even if the final output looks correct?",
     "Inspect the actual trajectory, reconcile effects and recovery, then propose a corrected bounded run.",
     "Verified trajectory and effect reconciliation against the applicable contract.",
     "TRAJECTORY_CHECK"),
    ("resource", {"acquisition_not_quarantined", "resource_missing_requested_scope", "resource_claim_conflicts_with_resolver"},
     "What resource state and usable scope does the provider actually resolve?",
     "Reconcile provider state and quarantine through the governed resource workflow; revise claims to the resolved scope.",
     "Provider state and receipt matching the requested object and permitted scope.",
     "RESOURCE_CHECK"),
    ("freshness", {"policy_changed", "object_changed", "stale_evidence"},
     "Which source, object or policy changed after this evidence was collected?",
     "Refresh only changed dependencies and rerun affected checks against one common snapshot; preserve prior failed evidence.",
     "Affected checks rebound to the current source, object and policy digests.",
     "FRESH_EVIDENCE"),
    ("independence", {"shared_evidence_lineage", "self_signed"},
     "Who verified this obligation outside the proposing agent's evidence lineage?",
     "Collect independent verification of the same obligation; changing a validator label cannot establish independence.",
     "Resolved validator identity and independently collected evidence for the exact obligation and snapshot.",
     "INDEPENDENT_VERIFICATION"),
    ("obligations", {"missing_obligation", "unverified_obligation"},
     "Which required behavior still lacks a passing, current verification record?",
     "Inspect the missing or failed obligation, repair its behavior if needed, and run its smallest meaningful verification.",
     "Every required obligation has a passing current record; failures remain visible.",
     "OBLIGATION_CHECK"),
)


def routes_for_reasons(reasons: list[str]) -> list[dict[str, Any]]:
    """Normalize reason codes; unknown reasons block through manual diagnosis."""
    if not isinstance(reasons, list) or any(not isinstance(r, str) for r in reasons):
        raise ValueError("reasons must be a list of strings")
    pending = set(reasons)
    routes = []
    for route_id, codes, question, action, proof, gate in ROUTES:
        matched = sorted(pending & codes)
        if matched:
            routes.append({
                "id": route_id, "reasons": matched, "question": question,
                "proposed_action": action, "resume_proof": proof,
                "next_gate": gate, "state": "PROPOSED", "executable": False,
            })
            pending.difference_update(matched)
    if pending:
        # Never echo unrecognized, potentially sensitive source text.
        routes.append({
            "id": "unmapped_failure", "reason_count": len(pending),
            "question": "Which evaluator failure has no reviewed repair mapping?",
            "proposed_action": "Inspect the evaluator version and add a reviewed mapping before retrying dependent work.",
            "resume_proof": "Reviewed mapping and a fresh evaluation of the original case.",
            "next_gate": "MANUAL_DIAGNOSIS", "state": "PROPOSED", "executable": False,
        })
    return routes


def evaluate_with_routes(payload: dict[str, Any]) -> dict[str, Any]:
    """Compute status from the existing evaluator; ignore no imported verdicts."""
    if not isinstance(payload, dict) or set(payload) != {"kind", "case"}:
        raise ValueError("input requires exactly kind and case")
    kind = payload["kind"]
    if not isinstance(kind, str) or kind not in {"authority", "completion"}:
        raise ValueError("kind must be authority or completion")
    if not isinstance(payload["case"], dict):
        raise ValueError("case must be an object")
    evaluator, key = (evaluate_authority, "eligible_candidate") if kind == "authority" else (evaluate_completion, "completion_candidate")
    result = evaluator(payload["case"])
    routes = routes_for_reasons(result["reasons"])
    return {
        "version": ROUTE_VERSION, "evaluator_version": VERSION, "kind": kind,
        "status": "BLOCKED" if routes else "CANDIDATE_ONLY",
        "candidate_eligible": result[key], "authority_effect": False,
        "effects_executed": 0, "routes": routes,
        "next_route": routes[0]["id"] if routes else None,
        "limits": ["Input provenance is asserted, not authenticated.",
                   "Routes are proposals; passing fixtures cannot grant authority or establish live completion."],
    }
