"""Promotion of a distilled candidate by receipt.

A promotion receipt is the only thing that moves a distilled candidate from the
unreviewed tier to the reviewed-candidate tier. It must bind the exact digests
on disk, name two distinct actors, neither of which is the trigger itself, and
be backed by a complete four-kind eval suite that passes. Promotion changes the
ledger only. It never edits the candidate package, never marks it admitted, and
never gives it runtime authority.
"""

from __future__ import annotations

from typing import Any

from sync_control_plane.skill_runtime import validate_manifest_integrity

from .common import (
    LEDGER_PATH,
    TRIGGER_ACTOR,
    parse_utc,
    pretty_json,
    schema_errors,
    sha256_json,
    sha256_json_without_keys,
)
from .evaluator import run_eval_suite
from .ledger import append_entry, candidate_state, distilled_entry, promotion_receipt_used


def promotion_attestation(receipt: dict[str, Any]) -> str:
    return sha256_json_without_keys(receipt, {"attestation"})


def attest_promotion(receipt: dict[str, Any]) -> dict[str, Any]:
    sealed = dict(receipt)
    sealed["attestation"] = {
        "algorithm": "sha256-canonical-json-v1",
        "digest": promotion_attestation(receipt),
    }
    return sealed


def validate_promotion_receipt(
    receipt: dict[str, Any],
    *,
    candidate_manifest: dict[str, Any],
    candidate_source: str,
    eval_suite: list[dict[str, Any]],
    ledger: dict[str, Any],
    schemas: dict[str, dict[str, Any]],
) -> list[str]:
    errors = [f"receipt schema: {message}" for message in schema_errors(schemas["distill_promotion_receipt"], receipt)]
    if errors:
        return errors

    if receipt["attestation"]["digest"] != promotion_attestation(receipt):
        errors.append("promotion attestation digest does not match receipt body")
    if receipt["requested_by"] == receipt["approved_by"]:
        errors.append("promotion requester and approver must be distinct")
    if TRIGGER_ACTOR in (receipt["requested_by"], receipt["approved_by"]):
        errors.append("the distill trigger may neither request nor approve promotion of its own output")

    candidate_id = receipt["candidate_id"]
    if candidate_manifest.get("id") != candidate_id:
        errors.append("promotion receipt names a different candidate than the package supplied")
    if candidate_manifest.get("version") != receipt["candidate_version"]:
        errors.append("promotion receipt candidate version mismatch")
    if candidate_manifest.get("status") != "candidate":
        errors.append("only candidate packages may be promoted; status drifted")
    integrity_errors = validate_manifest_integrity(candidate_manifest, candidate_source)
    errors.extend(f"candidate integrity: {message}" for message in integrity_errors)
    integrity = candidate_manifest.get("integrity", {})
    if integrity.get("manifest_sha256") != receipt["candidate_manifest_sha256"]:
        errors.append("promotion receipt manifest digest does not match candidate on disk")
    if integrity.get("source_blob_sha") != receipt["candidate_source_blob_sha"]:
        errors.append("promotion receipt source blob sha does not match candidate on disk")

    if promotion_receipt_used(ledger, receipt["receipt_id"]):
        errors.append("promotion receipt id already recorded in the ledger; receipts are single use")

    entry = distilled_entry(ledger, candidate_id)
    if entry is None:
        errors.append("candidate has no distilled ledger entry; unknown provenance cannot be promoted")
    else:
        try:
            if parse_utc(receipt["decided_at"]) < parse_utc(entry["recorded_at"]):
                errors.append("promotion decided before the candidate was distilled")
        except (ValueError, TypeError, KeyError):
            errors.append("promotion or distillation timestamp is invalid")
        if entry.get("source_receipt_id") != receipt["source_run_receipt_ref"]:
            errors.append("promotion receipt source run reference does not match ledger provenance")
        refs = entry.get("refs", {})
        if refs.get("manifest_sha256") != receipt["candidate_manifest_sha256"]:
            errors.append("ledger provenance digest does not match promotion receipt")
        if refs.get("eval_suite_ref") != receipt["eval_suite_ref"]:
            errors.append("promotion receipt eval suite reference does not match ledger provenance")
    state = candidate_state(ledger, candidate_id)
    if state == "promoted":
        errors.append("candidate already promoted; promotion is not repeatable")
    if state == "rejected":
        errors.append("candidate already rejected; a rejected digest cannot be promoted")

    if candidate_manifest.get("quality", {}).get("eval_suite_ref") != receipt["eval_suite_ref"]:
        errors.append("promotion receipt eval suite reference does not match candidate manifest")
    if sha256_json(eval_suite) != receipt["eval_suite_sha256"]:
        errors.append("promotion receipt eval suite digest does not match supplied suite")

    if receipt["decision"] == "promote":
        report = run_eval_suite(eval_suite, candidate_manifest, case_schema=schemas["skill_eval_case"])
        if report["missing_kinds"]:
            errors.append(
                "promotion requires all four eval kinds; missing: " + ", ".join(report["missing_kinds"])
            )
        errors.extend(f"eval failure: {message}" for message in report["failures"])
        if report["total"] and report["passed"] != report["total"]:
            errors.append(f"promotion requires every eval case to pass ({report['passed']}/{report['total']})")

    return errors


def apply_promotion(
    receipt: dict[str, Any],
    *,
    candidate_manifest: dict[str, Any],
    candidate_source: str,
    eval_suite: list[dict[str, Any]],
    ledger: dict[str, Any],
    schemas: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    errors = validate_promotion_receipt(
        receipt,
        candidate_manifest=candidate_manifest,
        candidate_source=candidate_source,
        eval_suite=eval_suite,
        ledger=ledger,
        schemas=schemas,
    )
    if errors:
        return {"outcome": "refused", "errors": errors, "ledger": ledger, "files": {},
                "ledger_input_sha256": ledger.get("ledger_sha256")}

    kind = "promoted" if receipt["decision"] == "promote" else "rejected"
    entry_source = distilled_entry(ledger, receipt["candidate_id"]) or {}
    updated, entry = append_entry(
        ledger,
        kind=kind,
        recorded_at=receipt["decided_at"],
        actor=receipt["approved_by"],
        candidate_id=receipt["candidate_id"],
        source_receipt_id=receipt["source_run_receipt_ref"],
        source_skill_id=str(entry_source.get("source_skill_id")),
        source_skill_version=str(entry_source.get("source_skill_version")),
        finding_codes=[
            "PROMOTED_TO_REVIEWED_CANDIDATE" if kind == "promoted" else "PROMOTION_REJECTED",
            "ADMISSION_EFFECT_NONE",
            "CANON_EFFECT_NONE",
            "RUNTIME_EFFECT_NONE",
        ],
        refs={
            "manifest_sha256": receipt["candidate_manifest_sha256"],
            "source_blob_sha": receipt["candidate_source_blob_sha"],
            "eval_suite_ref": receipt["eval_suite_ref"],
            "eval_suite_sha256": receipt["eval_suite_sha256"],
            "promotion_receipt_ref": receipt["receipt_id"],
        },
    )
    return {
        "outcome": kind,
        "errors": [],
        "ledger": updated,
        "ledger_entry": entry,
        "files": {
            LEDGER_PATH: pretty_json(updated),
            receipt["eval_suite_ref"]: pretty_json(eval_suite),
        },
        "ledger_input_sha256": ledger.get("ledger_sha256"),
    }
