"""Append-only, hash-linked receipts for the furniture-brief compiler.

Reuses the canonical-JSON hashing convention already established by
``applause_gate.receipt`` (candidate: policies/receipt-immutability-policy.yaml)
instead of inventing a second hashing scheme.
"""
from __future__ import annotations

from typing import Any

from applause_gate.receipt import canonical_json, sha256_json  # noqa: F401  (re-exported)

GENESIS_HASH = "0" * 64

NON_ACTIONS = (
    "no_audio_generation",
    "no_provider_call",
    "no_upload",
    "no_publication",
    "no_payment",
    "no_deployment",
)


def build_entry(
    *,
    batch_id: str,
    seq: int,
    prev_hash: str,
    input_hash: str,
    output_hash: str | None,
    decision: str,
    refusal_codes: list[str],
    proof_state: dict[str, Any],
    revision: int = 1,
    supersedes_receipt_id: str | None = None,
) -> dict[str, Any]:
    """Build one receipt entry and seal it with its own content hash.

    The entry is a plain dict (JSON-serializable). Its ``entry_hash`` is the
    sha256 of the canonical JSON of every *other* field, so any later
    mutation of a sealed entry is detectable by recomputing the hash.
    """
    entry_id = f"receipt.furniture-brief.{batch_id}.{seq:04d}"
    body: dict[str, Any] = {
        "receipt_id": entry_id,
        "seq": seq,
        "prev_hash": prev_hash,
        "batch_id": batch_id,
        "revision": revision,
        "input_hash": input_hash,
        "output_hash": output_hash,
        "decision": decision,
        "refusal_codes": sorted(refusal_codes),
        "proof_state": proof_state,
        "non_actions": list(NON_ACTIONS),
        "authority_ceiling_observed": "propose",
        "no_authority_escalation": True,
        "immutable": True,
    }
    if supersedes_receipt_id is not None:
        body["supersedes_receipt_id"] = supersedes_receipt_id

    entry = dict(body)
    entry["entry_hash"] = sha256_json(body)
    return entry


def append(chain: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
    """Append one new sealed entry to ``chain`` (mutates and returns it)."""
    prev_hash = chain[-1]["entry_hash"] if chain else GENESIS_HASH
    seq = len(chain) + 1
    entry = build_entry(prev_hash=prev_hash, seq=seq, **kwargs)
    chain.append(entry)
    return entry


def verify_chain(chain: list[dict[str, Any]]) -> dict[str, Any]:
    """Verify append-only hash-linkage and per-entry content integrity.

    Returns ``{"valid": bool, "broken_at": int | None, "reason": str | None}``.
    ``broken_at`` is the 0-based index of the first entry that fails to
    reproduce its stored hash or chain correctly to its predecessor.
    """
    expected_prev = GENESIS_HASH
    for index, entry in enumerate(chain):
        stored_hash = entry.get("entry_hash")
        body = {key: value for key, value in entry.items() if key != "entry_hash"}
        recomputed_hash = sha256_json(body)
        if recomputed_hash != stored_hash:
            return {
                "valid": False,
                "broken_at": index,
                "reason": "entry_hash does not match recomputed content hash "
                "(entry was mutated after sealing)",
            }
        if entry.get("prev_hash") != expected_prev:
            return {
                "valid": False,
                "broken_at": index,
                "reason": "prev_hash does not match the previous entry's sealed hash "
                "(chain linkage broken)",
            }
        expected_prev = stored_hash
    return {"valid": True, "broken_at": None, "reason": None}
