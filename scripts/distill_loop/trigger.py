"""Post-run distill trigger.

Given an immutable run receipt, the trace of what happened, and the source
skill package that ran, extract the moves that worked and write them as a
distilled candidate skill. The trigger is a pure function: it returns the files
it would write and the ledger it would append to, and never touches disk itself.

Fail-closed rules:

- only `completed` receipts distill; blocked, abstained, and failed runs are
  recorded as abstentions;
- the receipt must bind the exact source manifest digest that ran;
- only moves the source skill declared and that succeeded are distilled;
- fewer than three such moves is not a skill, so the trigger abstains;
- the observed ceiling may never exceed the source ceiling;
- one receipt distills at most once, and one candidate id belongs to one receipt;
- the source skill must sit in the manifested registry at the exact digest that ran;
- a move counts only if the receipt itself lists its evidence;
- every decision, including abstention, appends a ledger entry.
"""

from __future__ import annotations

from typing import Any

from sync_control_plane.skill_runtime import declared_actions, validate_manifest_integrity

from .common import (
    AUTHORITY_RANK,
    LEDGER_PATH,
    MIN_SUCCESSFUL_MOVES,
    TRIGGER_ACTOR,
    parse_utc,
    pretty_json,
    schema_errors,
    sha256_json,
    source_registration_errors,
)
from .ledger import append_entry, distilled_entry, receipt_already_distilled
from .package import (
    build_candidate_manifest,
    build_starter_eval_suite,
    candidate_id_for,
    distilled_ceiling,
    finalize_integrity,
    render_skill_md,
)


def _abstain(
    ledger: dict[str, Any],
    *,
    codes: list[str],
    receipt: dict[str, Any],
    trace: dict[str, Any] | None,
    recorded_at: str,
    candidate_id: str | None,
) -> dict[str, Any]:
    updated, entry = append_entry(
        ledger,
        kind="abstained",
        recorded_at=recorded_at,
        actor=TRIGGER_ACTOR,
        candidate_id=candidate_id,
        source_receipt_id=str(receipt.get("receipt_id") or "receipt.unknown"),
        source_skill_id=str(receipt.get("skill_id") or "quirk-unknown"),
        source_skill_version=str(receipt.get("skill_version") or "0.0.0"),
        finding_codes=codes,
        refs={"trace_id": (trace or {}).get("trace_id")},
    )
    return {
        "outcome": "abstained",
        "finding_codes": sorted(set(codes)),
        "candidate": None,
        "files": {LEDGER_PATH: pretty_json(updated)},
        "ledger": updated,
        "ledger_entry": entry,
        "ledger_input_sha256": ledger.get("ledger_sha256"),
    }


def post_run_distill(
    *,
    receipt: dict[str, Any],
    trace: dict[str, Any],
    source_manifest: dict[str, Any],
    source_text: str,
    ledger: dict[str, Any],
    schemas: dict[str, dict[str, Any]],
    registry: dict[str, Any],
    recorded_at: str | None = None,
) -> dict[str, Any]:
    recorded_at = recorded_at or str(receipt.get("finished_at") or "")
    codes: list[str] = []

    receipt_problems = schema_errors(schemas["skill_run_receipt"], receipt)
    if receipt_problems:
        return _abstain(ledger, codes=["RECEIPT_INVALID"], receipt=receipt, trace=None,
                        recorded_at=recorded_at or "1970-01-01T00:00:00Z", candidate_id=None)

    trace_problems = schema_errors(schemas["distill_run_trace"], trace)
    if trace_problems:
        return _abstain(ledger, codes=["TRACE_INVALID"], receipt=receipt, trace=None,
                        recorded_at=recorded_at, candidate_id=None)

    candidate_id = candidate_id_for(receipt["receipt_id"], trace["task_class"])

    if trace["receipt_id"] != receipt["receipt_id"]:
        return _abstain(ledger, codes=["TRACE_RECEIPT_MISMATCH"], receipt=receipt, trace=trace,
                        recorded_at=recorded_at, candidate_id=candidate_id)

    if receipt["status"] != "completed":
        return _abstain(ledger, codes=["RUN_NOT_COMPLETED"], receipt=receipt, trace=trace,
                        recorded_at=recorded_at, candidate_id=candidate_id)

    try:
        if parse_utc(receipt["finished_at"]) < parse_utc(receipt["started_at"]):
            raise ValueError("finished before started")
    except (ValueError, TypeError):
        return _abstain(ledger, codes=["RECEIPT_TIME_INVALID"], receipt=receipt, trace=trace,
                        recorded_at=recorded_at, candidate_id=candidate_id)

    if validate_manifest_integrity(source_manifest, source_text):
        return _abstain(ledger, codes=["SOURCE_INTEGRITY_FAILURE"], receipt=receipt, trace=trace,
                        recorded_at=recorded_at, candidate_id=candidate_id)

    source_digest = source_manifest["integrity"]["manifest_sha256"]
    if (
        receipt["skill_id"] != source_manifest["id"]
        or receipt["skill_version"] != source_manifest["version"]
        or receipt["skill_manifest_sha256"] != source_digest
        or trace["skill_id"] != source_manifest["id"]
        or trace["skill_version"] != source_manifest["version"]
    ):
        return _abstain(ledger, codes=["RECEIPT_SOURCE_MISMATCH"], receipt=receipt, trace=trace,
                        recorded_at=recorded_at, candidate_id=candidate_id)

    if source_registration_errors(registry, source_manifest):
        return _abstain(ledger, codes=["SOURCE_NOT_REGISTERED"], receipt=receipt, trace=trace,
                        recorded_at=recorded_at, candidate_id=candidate_id)

    if source_manifest["id"].startswith("quirk-distilled-"):
        return _abstain(ledger, codes=["RECURSIVE_DISTILLATION_DENIED"], receipt=receipt, trace=trace,
                        recorded_at=recorded_at, candidate_id=candidate_id)

    source_ceiling = source_manifest["authority"]["ceiling"]
    observed_ceiling = receipt["authority_ceiling_observed"]
    if AUTHORITY_RANK[observed_ceiling] > AUTHORITY_RANK[source_ceiling]:
        return _abstain(ledger, codes=["CEILING_ESCALATION_OBSERVED"], receipt=receipt, trace=trace,
                        recorded_at=recorded_at, candidate_id=candidate_id)

    if receipt_already_distilled(ledger, receipt["receipt_id"]):
        return _abstain(ledger, codes=["ALREADY_DISTILLED"], receipt=receipt, trace=trace,
                        recorded_at=recorded_at, candidate_id=candidate_id)

    prior = distilled_entry(ledger, candidate_id)
    if prior is not None and prior.get("source_receipt_id") != receipt["receipt_id"]:
        return _abstain(ledger, codes=["CANDIDATE_ID_COLLISION"], receipt=receipt, trace=trace,
                        recorded_at=recorded_at, candidate_id=candidate_id)

    receipted_refs = set(receipt["evidence_refs"]) | set(receipt["output_refs"]) | set(receipt["input_refs"])
    declared = declared_actions(source_manifest)
    successful: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in trace["moves"]:
        move = item["move"]
        if item["outcome"] != "succeeded":
            excluded.append({"move": move, "reason": f"outcome was {item['outcome']}"})
            continue
        if move not in declared:
            excluded.append({"move": move, "reason": "not declared by the source skill; excluded, never distilled"})
            codes.append("UNDECLARED_MOVE_EXCLUDED")
            continue
        if item["evidence_ref"] not in receipted_refs:
            excluded.append({"move": move, "reason": "evidence is not listed on the run receipt; excluded"})
            codes.append("EVIDENCE_UNRECEIPTED")
            continue
        if move in seen:
            excluded.append({"move": move, "reason": "duplicate of an earlier successful move"})
            continue
        seen.add(move)
        successful.append(item)

    if trace["stop_conditions_hit"]:
        return _abstain(ledger, codes=[*codes, "STOP_CONDITION_HIT"], receipt=receipt, trace=trace,
                        recorded_at=recorded_at, candidate_id=candidate_id)

    if len(successful) < MIN_SUCCESSFUL_MOVES:
        return _abstain(ledger, codes=[*codes, "INSUFFICIENT_SUCCESSFUL_MOVES"], receipt=receipt, trace=trace,
                        recorded_at=recorded_at, candidate_id=candidate_id)

    if not trace["routing_signals_observed"]:
        return _abstain(ledger, codes=[*codes, "ROUTING_SIGNALS_MISSING"], receipt=receipt, trace=trace,
                        recorded_at=recorded_at, candidate_id=candidate_id)

    ceiling = distilled_ceiling(source_ceiling, observed_ceiling)
    manifest = build_candidate_manifest(
        receipt=receipt,
        trace=trace,
        source_manifest=source_manifest,
        successful_moves=successful,
        ceiling=ceiling,
    )
    skill_text = render_skill_md(
        manifest,
        receipt=receipt,
        trace=trace,
        source_manifest=source_manifest,
        successful_moves=successful,
        excluded_moves=excluded,
    )
    manifest = finalize_integrity(manifest, skill_text)

    manifest_problems = schema_errors(schemas["skill_package"], manifest)
    if manifest_problems:
        return _abstain(ledger, codes=[*codes, "CANDIDATE_SCHEMA_FAILURE"], receipt=receipt, trace=trace,
                        recorded_at=recorded_at, candidate_id=candidate_id)

    eval_suite = build_starter_eval_suite(manifest, successful_moves=successful)
    eval_suite_ref = manifest["quality"]["eval_suite_ref"]
    codes.append("DISTILLED_CANDIDATE_WRITTEN")
    codes.append("PROMOTION_REQUIRED")
    codes.append("EVAL_KINDS_INCOMPLETE")

    updated, entry = append_entry(
        ledger,
        kind="distilled",
        recorded_at=recorded_at,
        actor=TRIGGER_ACTOR,
        candidate_id=candidate_id,
        source_receipt_id=receipt["receipt_id"],
        source_skill_id=source_manifest["id"],
        source_skill_version=source_manifest["version"],
        finding_codes=codes,
        refs={
            "trace_id": trace["trace_id"],
            "manifest_sha256": manifest["integrity"]["manifest_sha256"],
            "source_blob_sha": manifest["integrity"]["source_blob_sha"],
            "eval_suite_ref": eval_suite_ref,
            "eval_suite_sha256": sha256_json(eval_suite),
            "source_manifest_sha256": source_digest,
            "excluded_moves": sorted({item["move"] for item in excluded}),
        },
    )

    files = {
        f"skills/{candidate_id}/SKILL.md": skill_text,
        f"skills/{candidate_id}/manifest.json": pretty_json(manifest),
        eval_suite_ref: pretty_json(eval_suite),
        LEDGER_PATH: pretty_json(updated),
    }
    return {
        "outcome": "distilled",
        "finding_codes": sorted(set(codes)),
        "candidate": {
            "candidate_id": candidate_id,
            "version": manifest["version"],
            "status": manifest["status"],
            "tier": "distilled",
            "authority_ceiling": ceiling,
            "manifest_sha256": manifest["integrity"]["manifest_sha256"],
            "source_blob_sha": manifest["integrity"]["source_blob_sha"],
            "source_path": f"skills/{candidate_id}/SKILL.md",
            "manifest_path": f"skills/{candidate_id}/manifest.json",
            "eval_suite_ref": eval_suite_ref,
            "loadable_next_run": False,
            "promotion_receipt_ref": None,
        },
        "manifest": manifest,
        "skill_text": skill_text,
        "eval_suite": eval_suite,
        "files": files,
        "ledger": updated,
        "ledger_entry": entry,
        "ledger_input_sha256": ledger.get("ledger_sha256"),
    }
