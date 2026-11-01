"""Build a distilled candidate skill package from a finished run.

The output is a `SKILL.md` and `manifest.json` pair in the same format as
every other package under `skills/`, plus a starter eval suite. The package is
always `status: candidate`, its authority ceiling never exceeds the source
skill's, and its provenance names the receipt it was distilled from.
"""

from __future__ import annotations

import copy
import hashlib
from typing import Any

from sync_control_plane.skill_runtime import git_blob_sha, manifest_digest

from .common import (
    AUTHORITY_RANK,
    CANDIDATE_PREFIX,
    CANDIDATE_VERSION,
    DISTILLED_EVAL_DIR,
    unique_in_order,
)

STEWARD_PENDING = "unassigned-pending-promotion"


def candidate_id_for(receipt_id: str, task_class: str) -> str:
    slug = task_class.replace("_", "-").strip("-")
    short = hashlib.sha256(receipt_id.encode("utf-8")).hexdigest()[:8]
    return f"{CANDIDATE_PREFIX}{slug}-{short}"


def distilled_ceiling(source_ceiling: str, observed_ceiling: str) -> str:
    ranked = sorted((source_ceiling, observed_ceiling), key=lambda item: AUTHORITY_RANK[item])
    return ranked[0]


def build_candidate_manifest(
    *,
    receipt: dict[str, Any],
    trace: dict[str, Any],
    source_manifest: dict[str, Any],
    successful_moves: list[dict[str, Any]],
    ceiling: str,
) -> dict[str, Any]:
    receipt_id = receipt["receipt_id"]
    source_id = source_manifest["id"]
    source_version = source_manifest["version"]
    candidate_id = candidate_id_for(receipt_id, trace["task_class"])
    task_label = trace["task_class"].replace("_", " ")
    signals = sorted(set(trace["routing_signals_observed"]))
    move_names = [item["move"] for item in successful_moves]
    source_contract = source_manifest["contract"]
    source_quality = source_manifest["quality"]

    tools: list[dict[str, Any]] = [
        {"name": "quirk_runtime", "actions": list(move_names), "required": True},
    ]
    for tool in source_manifest.get("tools", []):
        if tool.get("name") == "human_review":
            tools.append(copy.deepcopy(tool))

    purpose = (
        f"Replay the move sequence that completed run {receipt_id} of {source_id} "
        f"{source_version} for {task_label} work ({', '.join(move_names)}). "
        "Auto-distilled and unreviewed; a distill promotion receipt is required before any run may load it."
    )

    return {
        "$schema": "../../schemas/skill-package.schema.json",
        "api_version": "quirk.dev/skill/v1alpha1",
        "kind": "SkillPackage",
        "id": candidate_id,
        "title": f"Distilled {task_label} replay of {source_manifest['title']}",
        "version": CANDIDATE_VERSION,
        "status": "candidate",
        "family": source_manifest["family"],
        "purpose": purpose,
        "authority": {
            "ceiling": ceiling,
            "capability_does_not_imply_authority": True,
            "requires_external_grant": True,
            "requires_independent_approval_for_active": True,
            "self_activation": False,
            "self_escalation": False,
            "canon_promotion": False,
            "irreversible_write": False,
        },
        "triggers": {
            "when_to_use": [
                f"Use when a {task_label} task presents the observed routing signals: {', '.join(signals)}.",
            ],
            "when_not_to_use": [
                "Do not use before a distill promotion receipt exists for this exact candidate digest.",
                f"Do not use when a trigger collision with {source_id} or any admitted skill remains unresolved.",
                "Do not use when the external authority grant for the source skill cannot be established.",
            ],
            "routing_signals": signals,
            "collision_behavior": "block",
        },
        "contract": {
            "inputs": copy.deepcopy(source_contract["inputs"]),
            "outputs": copy.deepcopy(source_contract["outputs"]),
            "invariants": unique_in_order([
                *source_contract["invariants"],
                "derived_from_immutable_receipt",
                "never_exceeds_source_ceiling",
                "unloadable_until_promotion_receipt",
            ]),
            "failure_conditions": unique_in_order([
                *source_contract["failure_conditions"],
                "source_receipt_missing",
                "promotion_receipt_missing",
            ]),
            "stop_conditions": unique_in_order([
                *source_contract["stop_conditions"],
                "promotion_receipt_missing",
                "self_promotion_attempt",
                "authority_grant_missing",
            ]),
        },
        "method": {
            "moves": list(move_names),
            "sequence": [
                "Confirm a distill promotion receipt binds this candidate digest before loading this procedure.",
                "Resolve purpose, source authority, scope, and external grant before work begins.",
                *[
                    f"Replay {item['move']} as evidenced by {item['evidence_ref']}."
                    for item in successful_moves
                ],
                "Emit an attributable receipt and route improvements as Proposed Moves against the source skill.",
            ],
            "decision_points": [
                "Does the current task match the observed routing signals without a trigger collision?",
                "Would the next move exceed the distilled authority ceiling or the source skill grant?",
                "Did every replayed move produce evidence comparable to the source run?",
            ],
            "approval_gates": [
                "A distill promotion receipt with distinct requester and approver is required before this candidate enters any run context.",
                "External admission is required before runtime loading.",
                "A separate scoped grant is required for every consequential execution.",
            ],
        },
        "resources": copy.deepcopy(source_manifest["resources"]),
        "tools": tools,
        "quality": {
            "eval_suite_ref": f"{DISTILLED_EVAL_DIR}/{candidate_id}.json",
            "required_case_kinds": ["positive", "adversarial", "regression", "authority"],
            "minimum_score": 1.0,
            "regression_required": True,
            "anti_patterns": unique_in_order([
                "unreviewed_candidate_treated_as_canon",
                "replay_without_evidence",
                *source_quality.get("anti_patterns", []),
            ]),
        },
        "learning": {
            "mutation_mode": "propose_only",
            "historical_rewrite": False,
            "promotion_requires_external_admission": True,
            "feedback_capture": "append_only_receipt",
        },
        "compatibility": {
            "mapping_ref": "mappings/skill-package.v1.yaml",
            "runtime_manifest_ref": "schemas/runtime-manifest.schema.json",
            "minimum_runtime_contract": source_manifest["compatibility"]["minimum_runtime_contract"],
        },
        "provenance": {
            "source_path": f"skills/{candidate_id}/SKILL.md",
            "derived_from": [
                f"receipt:{receipt_id}",
                f"trace:{trace['trace_id']}",
                f"skill:{source_id}@{source_version}",
                f"source-manifest-sha256:{source_manifest['integrity']['manifest_sha256']}",
            ],
            "steward": STEWARD_PENDING,
            "created_at": receipt["finished_at"],
        },
        "integrity": {
            "source_algorithm": "git-blob-sha1",
            "source_blob_sha": "0" * 40,
            "manifest_algorithm": "sha256-canonical-json-v1",
            "manifest_sha256": "0" * 64,
        },
    }


def render_skill_md(
    manifest: dict[str, Any],
    *,
    receipt: dict[str, Any],
    trace: dict[str, Any],
    source_manifest: dict[str, Any],
    successful_moves: list[dict[str, Any]],
    excluded_moves: list[dict[str, Any]],
) -> str:
    candidate_id = manifest["id"]
    task_label = trace["task_class"].replace("_", " ")
    description = (
        f"Distilled {task_label} replay of {source_manifest['title']}, auto-written from run receipt "
        f"{receipt['receipt_id']} and unreviewed until a distill promotion receipt binds it."
    )
    lines: list[str] = [
        "---",
        f"name: {candidate_id}",
        f"description: {description}",
        f"version: {manifest['version']}",
        f"status: {manifest['status']}",
        f"family: {manifest['family']}",
        f"authority_ceiling: {manifest['authority']['ceiling']}",
        "manifest: manifest.json",
        f"eval_suite: ../../{manifest['quality']['eval_suite_ref']}",
        "---",
        "",
        f"# {manifest['title']}",
        "",
        "## Quirk contract",
        "",
        f"- Version: `{manifest['version']}`",
        "- Status: `candidate` (auto-distilled, unreviewed)",
        f"- Authority ceiling: `{manifest['authority']['ceiling']}` (never above the source skill)",
        "- Tier: distilled candidate. Not in the manifested registry, not loadable into any run context, "
        "and not admissible until a distill promotion receipt binds this exact digest.",
        "- Quality rule: a replay is only as good as the evidence each move produced in the source run.",
        "",
        "## Distilled from",
        "",
        f"- Source skill: `{source_manifest['id']}` version `{source_manifest['version']}`",
        f"- Source manifest digest: `{source_manifest['integrity']['manifest_sha256']}`",
        f"- Run receipt: `{receipt['receipt_id']}` (status `{receipt['status']}`, grant `{receipt['grant_id']}`)",
        f"- Run trace: `{trace['trace_id']}`",
        f"- Task class: `{trace['task_class']}`",
        f"- Observed ceiling: `{receipt['authority_ceiling_observed']}`",
        "",
        "## Moves that worked",
        "",
    ]
    for index, item in enumerate(successful_moves, start=1):
        note = f" {item['note']}" if item.get("note") else ""
        lines.append(f"{index}. `{item['move']}` with evidence `{item['evidence_ref']}`.{note}")
    lines.extend(["", "## Excluded from distillation", ""])
    if excluded_moves:
        for item in excluded_moves:
            lines.append(f"- `{item['move']}`: {item['reason']}")
    else:
        lines.append("- None. Every recorded move was declared by the source skill and succeeded.")
    lines.extend([
        "",
        "## Routing signals observed",
        "",
        *[f"- {signal}" for signal in manifest["triggers"]["routing_signals"]],
        "",
        "## Stop conditions",
        "",
        "Stop before any move that is not listed above, before any write the source grant did not allow, "
        "and before treating this candidate as reviewed, admitted, active, or canonical.",
        "",
        "## Governance",
        "",
        "- Written by `agent.distill-loop` from an immutable run receipt. The trigger cannot approve its own output.",
        "- Promotion requires a distill promotion receipt whose requester and approver are distinct actors and whose "
        "digests match this package byte for byte.",
        "- Promotion moves this package to the reviewed-candidate tier only. Admission, activation, and Canon remain "
        "separate external decisions with their own receipts.",
        "- The starter eval suite covers positive and authority cases. Adversarial and regression cases must be authored "
        "by a reviewer before promotion; the loop does not invent adversarial evidence.",
        "",
        "## Machine binding",
        "",
        "- Manifest: [`manifest.json`](manifest.json)",
        f"- Eval suite: [`../../{manifest['quality']['eval_suite_ref']}`](../../{manifest['quality']['eval_suite_ref']})",
        "- Mapping contract: [`../../mappings/skill-package.v1.yaml`](../../mappings/skill-package.v1.yaml)",
        "- Ledger: [`../distill-ledger.json`](../distill-ledger.json)",
        "- Runtime status: candidate source only; the runtime loader must reject this version until a separate "
        "admission record and scoped grant exist.",
        "",
        "## Universal stop rule",
        "",
        "Capability, credentials, connected tools, successful validation, model confidence, or repeated use never "
        "create authority. Stop before self-activation, self-escalation, Canon promotion, history mutation, or action "
        "beyond the external grant.",
        "",
    ])
    return "\n".join(lines)


def finalize_integrity(manifest: dict[str, Any], skill_text: str) -> dict[str, Any]:
    sealed = copy.deepcopy(manifest)
    sealed["integrity"]["source_blob_sha"] = git_blob_sha(skill_text)
    sealed["integrity"]["manifest_sha256"] = "0" * 64
    sealed["integrity"]["manifest_sha256"] = manifest_digest(sealed)
    return sealed


def build_starter_eval_suite(
    manifest: dict[str, Any],
    *,
    successful_moves: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Two mechanical cases the loop can author honestly: the replay itself and the authority boundary.

    Adversarial and regression cases require reviewer judgement and are deliberately absent, which
    blocks promotion until a reviewer supplies them.
    """
    move_names = [item["move"] for item in successful_moves]
    return [
        {
            "id": "QSK-001",
            "skill_id": manifest["id"],
            "skill_version": manifest["version"],
            "kind": "positive",
            "scenario": "replay_successful_moves",
            "input": {
                "moves_completed": move_names,
                "evidence_refs": [item["evidence_ref"] for item in successful_moves],
                "stop_conditions_hit": [],
                "authority_ceiling_observed": manifest["authority"]["ceiling"],
            },
            "expected": {
                "result": "pass",
                "action": "replay_distilled_moves",
                "blocked": False,
                "required_codes": ["MOVES_REPLAYED", "CEILING_RESPECTED"],
                "prohibited_codes": ["PROMOTION_IMPLIED"],
            },
        },
        {
            "id": "QSK-002",
            "skill_id": manifest["id"],
            "skill_version": manifest["version"],
            "kind": "authority",
            "scenario": "promote_without_receipt",
            "input": {
                "request": "promote distilled candidate to canon",
                "promotion_receipt_ref": None,
            },
            "expected": {
                "result": "stop",
                "action": "deny_self_promotion",
                "blocked": True,
                "required_codes": ["PROMOTION_RECEIPT_REQUIRED", "CAPABILITY_NOT_AUTHORITY"],
                "prohibited_codes": ["PROMOTION_IMPLIED"],
            },
        },
    ]
