#!/usr/bin/env python3
"""Fail-closed structural and tribunal checks for the Quirk Core Golden Project Pack."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "docs/golden-project-pack/README.md",
    "docs/golden-project-pack/ARCHITECTURE.md",
    "docs/golden-project-pack/CURRENT-RESEARCH.md",
    "docs/golden-project-pack/TOP-MINDS.md",
    "docs/golden-project-pack/MULTIMEDIA-MULTIPLIZIERT.md",
    "prompts/QUIRK-GOLDEN-PROMPTS.md",
    "schemas/ledger-transition.schema.json",
    "schemas/proposed-move.schema.json",
    "schemas/proposed-move-queue.schema.json",
    "schemas/research-claim.schema.json",
    "schemas/media-derivative.schema.json",
    "proposed-moves/pr-3/queue.json",
    "tribunals/ship-without-bryan/pr-3/REPORT.md",
    "tribunals/ship-without-bryan/pr-3/EVIDENCE.json",
    "supabase/migrations/20260811113009_ship_without_bryan_projection.sql",
]

CORE_LAWS = [
    "Every consequential mutation owes a receipt.",
    "History is not authority.",
    "Storage is not consent.",
    "Comments are not commands.",
    "No Zombie Truth.",
    "Every decision eventually owes an outcome.",
]

PROMPT_IDS = [
    "prompt.golden_project_pack_compiler",
    "prompt.accountable_transition_designer",
    "prompt.ledger_fuckery_detector",
    "prompt.eval_suite_foundry",
    "prompt.golden_gate_architect",
    "prompt.capability_and_agent_skill_forge",
    "prompt.proposed_move_queue_operator",
    "prompt.current_research_currentizer",
    "prompt.top_minds_council",
    "prompt.multimedia_multipliziert",
    "prompt.ship_it_without_bryan_tribunal",
]

FORBIDDEN_PLACEHOLDERS = ("TODO", "FIXME", "[INSERT", "LOREM IPSUM")

MOVE_REQUIRED = {
    "id",
    "schema_version",
    "lane",
    "title",
    "desired_change",
    "expected_outcome",
    "proposer",
    "source_refs",
    "affected_objects",
    "authority_required",
    "risk",
    "reversibility",
    "disposition",
    "created_at",
    "dependency_class",
    "blocks_merge",
    "finding_ref",
    "hidden_context_dependencies",
    "resolution_artifacts",
    "acceptance_checks",
}

MOVE_OPTIONAL = {
    "evidence_refs",
    "contradiction_refs",
    "dependencies",
    "implementation_ref",
    "eval_refs",
    "outcome_due_at",
    "receipt_ref",
    "resolution_note",
}

LANES = {
    "canon",
    "policy",
    "schema",
    "capability",
    "skill",
    "prompt",
    "eval",
    "gate",
    "research-adoption",
    "media-release",
    "migration",
    "forgetting",
    "poison",
}

DISPOSITIONS = {
    "new",
    "triage",
    "experiment",
    "revise",
    "awaiting_authority",
    "approved",
    "rejected",
    "deferred",
    "poisoned",
    "boneyard",
    "implemented",
    "verified",
}

RESOLVED_BLOCKER_DISPOSITIONS = {"verified", "rejected", "poisoned", "boneyard"}

DEPENDENCY_CLASSES = {
    "hidden_bryan_context",
    "oral_tradition",
    "implicit_authority",
    "undefined_vocabulary",
    "undocumented_topology",
    "missing_operator_contract",
    "missing_personalization_boundary",
    "missing_execution_contract",
    "missing_evidence_contract",
    "missing_security_contract",
    "undocumented_provider_state",
    "missing_projection_contract",
    "missing_release_control",
    "missing_portability_contract",
}

RISK_CLASSES = {"L0", "L1", "L2", "L3", "L4", "L5"}
STRANGE_RISKS = {"none", "low", "medium", "high"}
REVERSIBILITY = {"trivial", "reversible", "compensatable", "irreversible"}
ACTOR_TYPES = {"human", "agent", "service"}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)


def load_json(relative: str) -> Any:
    path = ROOT / relative
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{relative}: {exc}") from exc


def validate_nonempty_string(value: Any, field: str, source: str) -> int:
    if not isinstance(value, str) or not value.strip():
        fail(f"{source}: {field} must be a non-empty string")
        return 1
    return 0


def validate_string_array(
    value: Any,
    field: str,
    source: str,
    *,
    minimum: int = 0,
) -> int:
    errors = 0
    if not isinstance(value, list):
        fail(f"{source}: {field} must be an array")
        return 1
    if len(value) < minimum:
        fail(f"{source}: {field} requires at least {minimum} item(s)")
        errors += 1
    if len({json.dumps(item, sort_keys=True) for item in value}) != len(value):
        fail(f"{source}: {field} contains duplicate items")
        errors += 1
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            fail(f"{source}: {field}[{index}] must be a non-empty string")
            errors += 1
    return errors


def validate_move(move: Any, source: str) -> int:
    errors = 0
    if not isinstance(move, dict):
        fail(f"{source}: move must be an object")
        return 1

    keys = set(move)
    missing = MOVE_REQUIRED - keys
    unknown = keys - MOVE_REQUIRED - MOVE_OPTIONAL
    for key in sorted(missing):
        fail(f"{source}: missing required field {key}")
        errors += 1
    for key in sorted(unknown):
        fail(f"{source}: unknown field {key}")
        errors += 1

    move_id = move.get("id")
    if not isinstance(move_id, str) or re.fullmatch(r"qpm_[A-Za-z0-9_-]+", move_id) is None:
        fail(f"{source}: invalid Proposed Move id {move_id!r}")
        errors += 1

    if move.get("schema_version") != "proposed-move.v1":
        fail(f"{source}: schema_version must be proposed-move.v1")
        errors += 1

    if move.get("lane") not in LANES:
        fail(f"{source}: invalid lane {move.get('lane')!r}")
        errors += 1

    if move.get("disposition") not in DISPOSITIONS:
        fail(f"{source}: invalid disposition {move.get('disposition')!r}")
        errors += 1

    if move.get("dependency_class") not in DEPENDENCY_CLASSES:
        fail(f"{source}: invalid dependency_class {move.get('dependency_class')!r}")
        errors += 1

    if not isinstance(move.get("blocks_merge"), bool):
        fail(f"{source}: blocks_merge must be boolean")
        errors += 1

    for field in (
        "title",
        "desired_change",
        "expected_outcome",
        "finding_ref",
        "created_at",
    ):
        errors += validate_nonempty_string(move.get(field), field, source)

    for field, minimum in (
        ("source_refs", 1),
        ("affected_objects", 1),
        ("authority_required", 1),
        ("hidden_context_dependencies", 1),
        ("resolution_artifacts", 1),
        ("acceptance_checks", 1),
        ("evidence_refs", 0),
        ("contradiction_refs", 0),
        ("dependencies", 0),
        ("eval_refs", 0),
    ):
        if field in move or minimum:
            errors += validate_string_array(move.get(field, []), field, source, minimum=minimum)

    proposer = move.get("proposer")
    if not isinstance(proposer, dict):
        fail(f"{source}: proposer must be an object")
        errors += 1
    else:
        if set(proposer) != {"actor_id", "actor_type"}:
            fail(f"{source}: proposer must contain only actor_id and actor_type")
            errors += 1
        errors += validate_nonempty_string(proposer.get("actor_id"), "proposer.actor_id", source)
        if proposer.get("actor_type") not in ACTOR_TYPES:
            fail(f"{source}: invalid proposer.actor_type {proposer.get('actor_type')!r}")
            errors += 1

    risk = move.get("risk")
    if not isinstance(risk, dict):
        fail(f"{source}: risk must be an object")
        errors += 1
    else:
        allowed_risk_fields = {"class", "rights_or_safety_impact", "strange_intact_risk"}
        if set(risk) - allowed_risk_fields:
            fail(f"{source}: risk contains unknown fields")
            errors += 1
        if risk.get("class") not in RISK_CLASSES:
            fail(f"{source}: invalid risk.class {risk.get('class')!r}")
            errors += 1
        errors += validate_nonempty_string(
            risk.get("rights_or_safety_impact"),
            "risk.rights_or_safety_impact",
            source,
        )
        if risk.get("strange_intact_risk") not in STRANGE_RISKS:
            fail(
                f"{source}: invalid risk.strange_intact_risk "
                f"{risk.get('strange_intact_risk')!r}"
            )
            errors += 1

    if move.get("reversibility") not in REVERSIBILITY:
        fail(f"{source}: invalid reversibility {move.get('reversibility')!r}")
        errors += 1

    if move.get("disposition") in RESOLVED_BLOCKER_DISPOSITIONS:
        errors += validate_nonempty_string(move.get("receipt_ref"), "receipt_ref", source)
        errors += validate_nonempty_string(move.get("resolution_note"), "resolution_note", source)
        if not move.get("evidence_refs"):
            fail(f"{source}: resolved move requires evidence_refs")
            errors += 1

    return errors


def validate_tribunal_queue(relative: str) -> int:
    errors = 0
    try:
        queue = load_json(relative)
    except ValueError as exc:
        fail(str(exc))
        return 1

    if not isinstance(queue, dict):
        fail(f"{relative}: queue must be an object")
        return 1

    required = {
        "id",
        "schema_version",
        "tribunal_id",
        "source_repository",
        "source_pull_request",
        "source_commit",
        "verdict",
        "generated_at",
        "blocking_move_ids",
        "move_refs",
    }
    missing = required - set(queue)
    if missing:
        for field in sorted(missing):
            fail(f"{relative}: missing required field {field}")
        return len(missing)

    if queue.get("schema_version") != "proposed-move-queue.v1":
        fail(f"{relative}: invalid schema_version")
        errors += 1
    if queue.get("verdict") not in {"block", "hold", "pass"}:
        fail(f"{relative}: invalid verdict")
        errors += 1
    if re.fullmatch(r"[a-f0-9]{40}", str(queue.get("source_commit", ""))) is None:
        fail(f"{relative}: source_commit must be a 40-character lowercase SHA")
        errors += 1

    move_refs = queue.get("move_refs")
    if not isinstance(move_refs, list) or not move_refs:
        fail(f"{relative}: move_refs must be a non-empty array")
        return errors + 1

    moves: list[dict[str, Any]] = []
    move_ids: list[str] = []
    for index, move_ref in enumerate(move_refs):
        ref_source = f"{relative}#move_refs[{index}]"
        if not isinstance(move_ref, dict) or set(move_ref) != {"id", "path"}:
            fail(f"{ref_source}: reference must contain only id and path")
            errors += 1
            continue
        move_id = move_ref.get("id")
        move_path = move_ref.get("path")
        if not isinstance(move_id, str) or re.fullmatch(r"qpm_[A-Za-z0-9_-]+", move_id) is None:
            fail(f"{ref_source}: invalid id {move_id!r}")
            errors += 1
            continue
        if not isinstance(move_path, str) or not move_path.startswith("proposed-moves/pr-3/"):
            fail(f"{ref_source}: invalid path {move_path!r}")
            errors += 1
            continue
        try:
            move = load_json(move_path)
        except ValueError as exc:
            fail(str(exc))
            errors += 1
            continue
        errors += validate_move(move, move_path)
        if move.get("id") != move_id:
            fail(f"{ref_source}: id does not match {move_path}")
            errors += 1
        moves.append(move)
        move_ids.append(move_id)

    if len(set(move_ids)) != len(move_ids):
        fail(f"{relative}: duplicate Proposed Move ids")
        errors += 1
    if len({ref.get("path") for ref in move_refs if isinstance(ref, dict)}) != len(move_refs):
        fail(f"{relative}: duplicate Proposed Move paths")
        errors += 1

    known_ids = set(move_ids)
    for move in moves:
        for dependency in move.get("dependencies", []):
            if dependency not in known_ids:
                fail(
                    f"{move.get('id')}: dependency {dependency!r} "
                    "does not reference a move in this queue"
                )
                errors += 1

    derived_blocking_ids = [
        move["id"]
        for move in moves
        if move.get("blocks_merge") is True
        and move.get("disposition") not in RESOLVED_BLOCKER_DISPOSITIONS
    ]
    declared_blocking_ids = queue.get("blocking_move_ids")
    if declared_blocking_ids != derived_blocking_ids:
        fail(
            f"{relative}: blocking_move_ids must exactly match unresolved "
            "blocks_merge moves in queue order"
        )
        errors += 1

    evidence_relative = "tribunals/ship-without-bryan/pr-3/EVIDENCE.json"
    try:
        evidence = load_json(evidence_relative)
    except ValueError as exc:
        fail(str(exc))
        errors += 1
    else:
        if evidence.get("blocking_move_ids") != declared_blocking_ids:
            fail(f"{evidence_relative}: blocking_move_ids drift from queue")
            errors += 1
        if evidence.get("blocking_move_count") != len(declared_blocking_ids):
            fail(f"{evidence_relative}: blocking_move_count drift from queue")
            errors += 1
        if evidence.get("repository", {}).get("head_sha") != queue.get("source_commit"):
            fail(f"{evidence_relative}: evaluated head SHA drift from queue")
            errors += 1

    report_path = ROOT / "tribunals/ship-without-bryan/pr-3/REPORT.md"
    if report_path.is_file():
        report = report_path.read_text(encoding="utf-8")
        for move_id in move_ids:
            if move_id not in report:
                fail(f"{report_path.relative_to(ROOT)} missing move id {move_id}")
                errors += 1

    if derived_blocking_ids:
        for move_id in derived_blocking_ids:
            fail(f"merge blocked by unresolved Proposed Move: {move_id}")
        errors += len(derived_blocking_ids)

    return errors

def main() -> int:
    errors = 0

    for relative in REQUIRED_FILES:
        path = ROOT / relative
        if not path.is_file():
            fail(f"missing required file: {relative}")
            errors += 1

    for path in sorted((ROOT / "schemas").glob("*.schema.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
            errors += 1
            continue

        for key in ("$schema", "$id", "title", "type"):
            if key not in value:
                fail(f"{path.relative_to(ROOT)} missing {key}")
                errors += 1

    pack_path = ROOT / "docs/golden-project-pack/README.md"
    if pack_path.is_file():
        pack = pack_path.read_text(encoding="utf-8")
        for law in CORE_LAWS:
            if law not in pack:
                fail(f"core law missing from pack: {law}")
                errors += 1

    prompt_path = ROOT / "prompts/QUIRK-GOLDEN-PROMPTS.md"
    if prompt_path.is_file():
        prompt_text = prompt_path.read_text(encoding="utf-8")
        for prompt_id in PROMPT_IDS:
            if prompt_id not in prompt_text:
                fail(f"Golden Prompt missing: {prompt_id}")
                errors += 1

    queue_relative = "proposed-moves/pr-3/queue.json"
    if (ROOT / queue_relative).is_file():
        errors += validate_tribunal_queue(queue_relative)

    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() not in {".md", ".json", ".yaml", ".yml", ".py", ".sql"}:
            continue
        if path.resolve() == Path(__file__).resolve():
            continue
        text = path.read_text(encoding="utf-8", errors="replace").upper()
        for placeholder in FORBIDDEN_PLACEHOLDERS:
            if placeholder in text:
                fail(f"unresolved placeholder {placeholder!r} in {path.relative_to(ROOT)}")
                errors += 1

    if errors:
        print(f"Golden gates failed with {errors} error(s).", file=sys.stderr)
        return 1

    print("Golden structural and Ship It Without Bryan gates passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
