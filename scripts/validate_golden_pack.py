#!/usr/bin/env python3
"""Fail-closed structural checks for the Quirk Core Golden Project Pack.

Candidate repository merge and Golden admission are intentionally separate gates.
A PROPOSED candidate may be structurally safe to merge while admission blockers remain
open. Admission-status objects fail closed until every merge-blocking Proposed Move is
resolved with evidence and a receipt.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "docs/golden-project-pack/README.md",
    "docs/golden-project-pack/ADMISSION.md",
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
CANDIDATE_STATUSES = {"PROPOSED", "CANDIDATE", "DRAFT", "EXPERIMENTAL"}
ADMISSION_STATUSES = {"GOLDEN", "ADMITTED", "LIVE", "CURRENT", "ACTIVE", "CHOOSEABLE", "USEABLE"}

MOVE_REQUIRED = {
    "id", "schema_version", "lane", "title", "desired_change", "expected_outcome",
    "proposer", "source_refs", "affected_objects", "authority_required", "risk",
    "reversibility", "disposition", "created_at", "dependency_class", "blocks_merge",
    "finding_ref", "hidden_context_dependencies", "resolution_artifacts", "acceptance_checks",
}
MOVE_OPTIONAL = {
    "evidence_refs", "contradiction_refs", "dependencies", "implementation_ref",
    "eval_refs", "outcome_due_at", "receipt_ref", "resolution_note",
}
LANES = {
    "canon", "policy", "schema", "capability", "skill", "prompt", "eval", "gate",
    "research-adoption", "media-release", "migration", "forgetting", "poison",
}
DISPOSITIONS = {
    "new", "triage", "experiment", "revise", "awaiting_authority", "approved",
    "rejected", "deferred", "poisoned", "boneyard", "implemented", "verified",
}
RESOLVED_BLOCKER_DISPOSITIONS = {"verified", "rejected", "poisoned", "boneyard"}
DEPENDENCY_CLASSES = {
    "hidden_bryan_context", "oral_tradition", "implicit_authority", "undefined_vocabulary",
    "undocumented_topology", "missing_operator_contract", "missing_personalization_boundary",
    "missing_execution_contract", "missing_evidence_contract", "missing_security_contract",
    "undocumented_provider_state", "missing_projection_contract", "missing_release_control",
    "missing_portability_contract",
}
RISK_CLASSES = {"L0", "L1", "L2", "L3", "L4", "L5"}
STRANGE_RISKS = {"none", "low", "medium", "high"}
REVERSIBILITY = {"trivial", "reversible", "compensatable", "irreversible"}
ACTOR_TYPES = {"human", "agent", "service"}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)


def hold(message: str) -> None:
    print(f"HOLD: {message}")


def load_json(relative: str) -> Any:
    path = ROOT / relative
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{relative}: {exc}") from exc


def nonempty(value: Any, field: str, source: str) -> int:
    if not isinstance(value, str) or not value.strip():
        fail(f"{source}: {field} must be a non-empty string")
        return 1
    return 0


def string_array(value: Any, field: str, source: str, minimum: int = 0) -> int:
    if not isinstance(value, list):
        fail(f"{source}: {field} must be an array")
        return 1
    errors = 0
    if len(value) < minimum:
        fail(f"{source}: {field} requires at least {minimum} item(s)")
        errors += 1
    serialized = [json.dumps(item, sort_keys=True) for item in value]
    if len(set(serialized)) != len(serialized):
        fail(f"{source}: {field} contains duplicate items")
        errors += 1
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            fail(f"{source}: {field}[{index}] must be a non-empty string")
            errors += 1
    return errors


def pack_status() -> str | None:
    path = ROOT / "docs/golden-project-pack/README.md"
    if not path.is_file():
        return None
    match = re.search(r"^\*\*Status:\*\*\s*([A-Za-z_-]+)", path.read_text(encoding="utf-8"), re.MULTILINE)
    return match.group(1).upper() if match else None


def validate_move(move: Any, source: str) -> int:
    if not isinstance(move, dict):
        fail(f"{source}: move must be an object")
        return 1

    errors = 0
    keys = set(move)
    for key in sorted(MOVE_REQUIRED - keys):
        fail(f"{source}: missing required field {key}")
        errors += 1
    for key in sorted(keys - MOVE_REQUIRED - MOVE_OPTIONAL):
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

    for field in ("title", "desired_change", "expected_outcome", "finding_ref", "created_at"):
        errors += nonempty(move.get(field), field, source)
    for field, minimum in (
        ("source_refs", 1), ("affected_objects", 1), ("authority_required", 1),
        ("hidden_context_dependencies", 1), ("resolution_artifacts", 1), ("acceptance_checks", 1),
        ("evidence_refs", 0), ("contradiction_refs", 0), ("dependencies", 0), ("eval_refs", 0),
    ):
        if field in move or minimum:
            errors += string_array(move.get(field, []), field, source, minimum)

    proposer = move.get("proposer")
    if not isinstance(proposer, dict):
        fail(f"{source}: proposer must be an object")
        errors += 1
    else:
        if set(proposer) != {"actor_id", "actor_type"}:
            fail(f"{source}: proposer must contain only actor_id and actor_type")
            errors += 1
        errors += nonempty(proposer.get("actor_id"), "proposer.actor_id", source)
        if proposer.get("actor_type") not in ACTOR_TYPES:
            fail(f"{source}: invalid proposer.actor_type {proposer.get('actor_type')!r}")
            errors += 1

    risk = move.get("risk")
    if not isinstance(risk, dict):
        fail(f"{source}: risk must be an object")
        errors += 1
    else:
        if set(risk) - {"class", "rights_or_safety_impact", "strange_intact_risk"}:
            fail(f"{source}: risk contains unknown fields")
            errors += 1
        if risk.get("class") not in RISK_CLASSES:
            fail(f"{source}: invalid risk.class {risk.get('class')!r}")
            errors += 1
        errors += nonempty(risk.get("rights_or_safety_impact"), "risk.rights_or_safety_impact", source)
        if risk.get("strange_intact_risk") not in STRANGE_RISKS:
            fail(f"{source}: invalid risk.strange_intact_risk {risk.get('strange_intact_risk')!r}")
            errors += 1

    if move.get("reversibility") not in REVERSIBILITY:
        fail(f"{source}: invalid reversibility {move.get('reversibility')!r}")
        errors += 1

    if move.get("disposition") in RESOLVED_BLOCKER_DISPOSITIONS:
        errors += nonempty(move.get("receipt_ref"), "receipt_ref", source)
        errors += nonempty(move.get("resolution_note"), "resolution_note", source)
        if not move.get("evidence_refs"):
            fail(f"{source}: resolved move requires evidence_refs")
            errors += 1
    return errors


def validate_tribunal_queue(relative: str, status: str) -> tuple[int, list[str]]:
    errors = 0
    try:
        queue = load_json(relative)
    except ValueError as exc:
        fail(str(exc))
        return 1, []

    required = {
        "id", "schema_version", "tribunal_id", "source_repository", "source_pull_request",
        "source_commit", "verdict", "generated_at", "blocking_move_ids", "move_refs",
    }
    if not isinstance(queue, dict):
        fail(f"{relative}: queue must be an object")
        return 1, []
    for field in sorted(required - set(queue)):
        fail(f"{relative}: missing required field {field}")
        errors += 1
    if errors:
        return errors, []

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
        return errors + 1, []

    moves: list[dict[str, Any]] = []
    move_ids: list[str] = []
    move_paths: list[str] = []
    for index, ref in enumerate(move_refs):
        source = f"{relative}#move_refs[{index}]"
        if not isinstance(ref, dict) or set(ref) != {"id", "path"}:
            fail(f"{source}: reference must contain only id and path")
            errors += 1
            continue
        move_id, move_path = ref.get("id"), ref.get("path")
        if not isinstance(move_id, str) or re.fullmatch(r"qpm_[A-Za-z0-9_-]+", move_id) is None:
            fail(f"{source}: invalid id {move_id!r}")
            errors += 1
            continue
        if not isinstance(move_path, str) or not move_path.startswith("proposed-moves/pr-3/"):
            fail(f"{source}: invalid path {move_path!r}")
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
            fail(f"{source}: id does not match {move_path}")
            errors += 1
        moves.append(move)
        move_ids.append(move_id)
        move_paths.append(move_path)

    if len(set(move_ids)) != len(move_ids):
        fail(f"{relative}: duplicate Proposed Move ids")
        errors += 1
    if len(set(move_paths)) != len(move_paths):
        fail(f"{relative}: duplicate Proposed Move paths")
        errors += 1

    known_ids = set(move_ids)
    for move in moves:
        for dependency in move.get("dependencies", []):
            if dependency not in known_ids:
                fail(f"{move.get('id')}: dependency {dependency!r} does not reference this queue")
                errors += 1

    unresolved = [
        move["id"] for move in moves
        if move.get("blocks_merge") is True
        and move.get("disposition") not in RESOLVED_BLOCKER_DISPOSITIONS
    ]
    if queue.get("blocking_move_ids") != unresolved:
        fail(f"{relative}: blocking_move_ids must exactly match unresolved blocks_merge moves in queue order")
        errors += 1
    if unresolved and queue.get("verdict") == "pass":
        fail(f"{relative}: verdict cannot be pass while admission blockers remain")
        errors += 1
    if not unresolved and queue.get("verdict") == "block":
        fail(f"{relative}: verdict cannot be block when no blocking moves remain")
        errors += 1

    # Historical tribunal evidence is immutable evidence, not a live projection of the queue.
    # Validate its own consistency and references without forcing it to mutate whenever the queue evolves.
    evidence_relative = "tribunals/ship-without-bryan/pr-3/EVIDENCE.json"
    try:
        evidence = load_json(evidence_relative)
    except ValueError as exc:
        fail(str(exc))
        errors += 1
    else:
        evidence_ids = evidence.get("blocking_move_ids", [])
        if not isinstance(evidence_ids, list):
            fail(f"{evidence_relative}: blocking_move_ids must be an array")
            errors += 1
        else:
            if evidence.get("blocking_move_count") != len(evidence_ids):
                fail(f"{evidence_relative}: blocking_move_count must match its historical blocker list")
                errors += 1
            unknown = [move_id for move_id in evidence_ids if move_id not in known_ids]
            if unknown:
                fail(f"{evidence_relative}: historical evidence references unknown move ids {unknown}")
                errors += 1
        head_sha = evidence.get("repository", {}).get("head_sha")
        if re.fullmatch(r"[a-f0-9]{40}", str(head_sha or "")) is None:
            fail(f"{evidence_relative}: repository.head_sha must be a 40-character lowercase SHA")
            errors += 1

    report_path = ROOT / "tribunals/ship-without-bryan/pr-3/REPORT.md"
    if report_path.is_file():
        report = report_path.read_text(encoding="utf-8")
        for move_id in move_ids:
            if move_id not in report:
                fail(f"{report_path.relative_to(ROOT)} missing move id {move_id}")
                errors += 1

    if unresolved:
        if status in ADMISSION_STATUSES:
            for move_id in unresolved:
                fail(f"admission blocked by unresolved Proposed Move: {move_id}")
            errors += len(unresolved)
        else:
            for move_id in unresolved:
                hold(f"Golden admission blocked by unresolved Proposed Move: {move_id}")
    return errors, unresolved


def main() -> int:
    errors = 0
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            fail(f"missing required file: {relative}")
            errors += 1

    status = pack_status()
    if status is None:
        fail("docs/golden-project-pack/README.md must declare **Status:**")
        errors += 1
        status = "UNKNOWN"
    elif status not in CANDIDATE_STATUSES | ADMISSION_STATUSES:
        fail(f"unsupported Golden Project Pack status {status!r}")
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

    unresolved: list[str] = []
    queue_relative = "proposed-moves/pr-3/queue.json"
    if (ROOT / queue_relative).is_file():
        queue_errors, unresolved = validate_tribunal_queue(queue_relative, status)
        errors += queue_errors

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

    if unresolved and status in CANDIDATE_STATUSES:
        print(
            f"Candidate merge gates passed with {len(unresolved)} Golden-admission hold(s). "
            "No admission, activation, canonization, or runtime authority is implied."
        )
    else:
        print("Golden structural and admission gates passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
