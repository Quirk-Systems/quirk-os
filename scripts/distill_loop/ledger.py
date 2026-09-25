"""Append-only, hash-chained distill ledger.

Every trigger decision (distilled or abstained) and every promotion or
rejection appends one entry. Entries are never edited; a correction is a new
entry. The ledger is a rebuildable projection with no authority of its own.
"""

from __future__ import annotations

import copy
from typing import Any

from .common import GENESIS_SHA256, TRIGGER_ACTOR, sha256_json_without_keys

ENTRY_KINDS = ("distilled", "abstained", "promoted", "rejected")


def new_ledger() -> dict[str, Any]:
    ledger = {
        "api_version": "quirk.dev/distill-ledger/v1alpha1",
        "kind": "DistillLedger",
        "status": "candidate",
        "trigger_actor": TRIGGER_ACTOR,
        "authority": {
            "semantic_authority": False,
            "runtime_authority": False,
            "canon_promotion": False,
            "admission_effect": "none",
            "projection_only": True,
        },
        "entries": [],
        "ledger_sha256": GENESIS_SHA256,
    }
    return seal_ledger(ledger)


def ledger_digest(ledger: dict[str, Any]) -> str:
    return sha256_json_without_keys(ledger, {"ledger_sha256"})


def entry_digest(entry: dict[str, Any]) -> str:
    return sha256_json_without_keys(entry, {"entry_sha256"})


def seal_ledger(ledger: dict[str, Any]) -> dict[str, Any]:
    sealed = copy.deepcopy(ledger)
    sealed["ledger_sha256"] = ledger_digest(sealed)
    return sealed


def append_entry(
    ledger: dict[str, Any],
    *,
    kind: str,
    recorded_at: str,
    actor: str,
    candidate_id: str | None,
    source_receipt_id: str,
    source_skill_id: str,
    source_skill_version: str,
    finding_codes: list[str],
    refs: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return (new_ledger, entry). The input ledger is never mutated."""
    if kind not in ENTRY_KINDS:
        raise ValueError(f"unknown ledger entry kind: {kind}")
    if kind == "distilled" and not (refs.get("manifest_sha256") and refs.get("source_manifest_sha256")):
        raise ValueError("a distilled entry must carry manifest_sha256 and source_manifest_sha256 provenance")
    errors = verify_ledger(ledger)
    if errors:
        raise ValueError("refusing to append to a ledger that fails verification: " + "; ".join(errors))
    entries = ledger.get("entries", [])
    prev = entries[-1]["entry_sha256"] if entries else GENESIS_SHA256
    entry = {
        "entry_id": f"dl.{len(entries) + 1:06d}",
        "kind": kind,
        "recorded_at": recorded_at,
        "actor": actor,
        "candidate_id": candidate_id,
        "source_receipt_id": source_receipt_id,
        "source_skill_id": source_skill_id,
        "source_skill_version": source_skill_version,
        "finding_codes": sorted(set(finding_codes)),
        "refs": {key: value for key, value in sorted(refs.items()) if value not in (None, [], "")},
        "prev_entry_sha256": prev,
        "entry_sha256": GENESIS_SHA256,
    }
    entry["entry_sha256"] = entry_digest(entry)
    updated = copy.deepcopy(ledger)
    updated["entries"] = [*entries, entry]
    return seal_ledger(updated), entry


def verify_ledger(ledger: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if ledger.get("ledger_sha256") != ledger_digest(ledger):
        errors.append("ledger sha256 does not match canonical ledger")
    if ledger.get("trigger_actor") != TRIGGER_ACTOR:
        errors.append("ledger trigger actor drifted")
    prev = GENESIS_SHA256
    for index, entry in enumerate(ledger.get("entries", []), start=1):
        expected_id = f"dl.{index:06d}"
        if entry.get("entry_id") != expected_id:
            errors.append(f"entry {index}: expected id {expected_id}, found {entry.get('entry_id')}")
        if entry.get("prev_entry_sha256") != prev:
            errors.append(f"entry {index}: hash chain broken")
        if entry.get("entry_sha256") != entry_digest(entry):
            errors.append(f"entry {index}: entry sha256 does not match entry body")
        if entry.get("kind") not in ENTRY_KINDS:
            errors.append(f"entry {index}: unknown kind {entry.get('kind')!r}")
        prev = entry.get("entry_sha256", prev)
    return errors


def candidate_state(ledger: dict[str, Any], candidate_id: str) -> str | None:
    """Fold the ledger into the candidate's current tier.

    distilled -> unreviewed candidate; promoted -> reviewed candidate;
    rejected -> excluded. A candidate with no entry is unknown (None).
    """
    state: str | None = None
    for entry in ledger.get("entries", []):
        if entry.get("candidate_id") != candidate_id:
            continue
        kind = entry.get("kind")
        if kind == "distilled":
            state = state or "distilled"
        elif kind == "promoted":
            state = "promoted"
        elif kind == "rejected":
            state = "rejected"
    return state


def distilled_entry(ledger: dict[str, Any], candidate_id: str) -> dict[str, Any] | None:
    for entry in ledger.get("entries", []):
        if entry.get("kind") == "distilled" and entry.get("candidate_id") == candidate_id:
            return entry
    return None


def promotion_receipt_used(ledger: dict[str, Any], receipt_id: str) -> bool:
    return any(
        entry.get("refs", {}).get("promotion_receipt_ref") == receipt_id
        for entry in ledger.get("entries", [])
    )


def receipt_already_distilled(ledger: dict[str, Any], source_receipt_id: str) -> bool:
    return any(
        entry.get("kind") == "distilled" and entry.get("source_receipt_id") == source_receipt_id
        for entry in ledger.get("entries", [])
    )
