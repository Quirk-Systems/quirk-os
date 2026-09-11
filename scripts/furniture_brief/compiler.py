"""F3 -> F11 Grounded-to-Banger compiler.

Compiles one synthetic source record (a ``reality_shard`` plus its child
assets, a Furniture block, and a provenance/consent block) into either a
provider-neutral Song Brief (F11 stage: Finalize) or a refusal (F11 stage:
Flop) with explicit reason codes and a suggested Finagle.

This module never calls a model, a music provider, or a network of any
kind. It is pure data-in, data-out, so it is safe to run inside a test and
safe to hash into a receipt.
"""
from __future__ import annotations

from typing import Any

from furniture_brief import furniture as furniture_check
from furniture_brief import grip as grip_score
from furniture_brief import lineage as lineage_check
from furniture_brief.receipt import append, sha256_json

ADULT_CONSENT_MISSING_OR_AMBIGUOUS = "ADULT_CONSENT_MISSING_OR_AMBIGUOUS"
STORAGE_OR_CONTENT_PERMISSION_MISSING = "STORAGE_OR_CONTENT_PERMISSION_MISSING"
IDENTITY_RISK_UNACCEPTABLE = "IDENTITY_RISK_UNACCEPTABLE"
FURNITURE_NOT_LOAD_BEARING = "FURNITURE_NOT_LOAD_BEARING"
GRIP_BELOW_THRESHOLD = "GRIP_BELOW_THRESHOLD"
LINEAGE_INVALID = "LINEAGE_INVALID"

F_TIERS_REQUIRING_INTIMACY_CONSENT = {"F2", "F3"}
ACCEPTABLE_IDENTITY_RISK = {"none", "low"}

F11_STAGES = (
    "Find", "Fact", "Furniture", "Fiction", "Freak", "Flex", "Fit", "Freeze",
)


def _asset_by_type(assets: list[dict[str, Any]], asset_type: str) -> dict[str, Any] | None:
    for asset in assets:
        if asset.get("asset_type") == asset_type:
            return asset
    return None


def _check_consent(provenance: dict[str, Any]) -> list[str]:
    codes: list[str] = []

    adult_confirmed = provenance.get("adult_confirmed")
    f_tier = provenance.get("f_tier")
    consent_to_intimacy = provenance.get("consent_to_intimacy")

    adult_ambiguous = adult_confirmed is not True
    intimacy_ambiguous = (
        f_tier in F_TIERS_REQUIRING_INTIMACY_CONSENT and consent_to_intimacy is not True
    )
    if adult_ambiguous or intimacy_ambiguous:
        codes.append(ADULT_CONSENT_MISSING_OR_AMBIGUOUS)

    # Consent to intimacy must never imply permission to store or publish:
    # storage permission is checked independently, never derived.
    if provenance.get("consent_to_store") is not True:
        codes.append(STORAGE_OR_CONTENT_PERMISSION_MISSING)

    identity_risk = provenance.get("identity_risk")
    anonymized = provenance.get("anonymized")
    needs_anonymization = f_tier in F_TIERS_REQUIRING_INTIMACY_CONSENT
    identity_unacceptable = identity_risk not in ACCEPTABLE_IDENTITY_RISK
    anonymization_insufficient = needs_anonymization and anonymized is not True
    if identity_unacceptable or anonymization_insufficient:
        codes.append(IDENTITY_RISK_UNACCEPTABLE)

    return codes


def compile_batch(request: dict[str, Any]) -> dict[str, Any]:
    """Run one compile request through the full F11 trace.

    ``request`` shape: {batch_id, provenance, assets[], furniture,
    next_bounded_experiment, compiled_at}. See
    schemas/furniture-brief-contract.schema.json for the contract.
    """
    batch_id = request["batch_id"]
    provenance = request["provenance"]
    assets = request["assets"]
    furniture_block = request["furniture"]

    trace: list[dict[str, Any]] = []

    def stage(name: str, status: str, detail: str) -> None:
        trace.append({"stage": name, "status": status, "detail": detail})

    reality_shard = _asset_by_type(assets, "reality_shard")
    stage(
        "Find",
        "ok" if reality_shard else "refused",
        "reality_shard located" if reality_shard else "no reality_shard in batch",
    )

    lineage_result = lineage_check.validate(assets)
    stage(
        "Fact",
        "ok" if lineage_result["valid"] else "refused",
        "lineage acyclic and fully resolved" if lineage_result["valid"]
        else "; ".join(lineage_result["problems"]),
    )

    furniture_assessment = furniture_check.assess(furniture_block)
    stage(
        "Furniture",
        "ok" if furniture_assessment["load_bearing"] else "refused",
        "all seven dimensions are load-bearing" if furniture_assessment["load_bearing"]
        else f"decorative or absent: {furniture_assessment['missing_or_decorative_fields']}",
    )

    fiction_types = {
        "want_resistance_pair", "power_vector", "consent_beat",
        "sensory_triad", "contradiction_pair",
    }
    fiction_present = [a["asset_type"] for a in assets if a.get("asset_type") in fiction_types]
    stage("Fiction", "ok", f"derived asset types present: {sorted(fiction_present)}")

    freak_types = {"phrase_atom", "hook_thesis"}
    freak_present = [a["asset_type"] for a in assets if a.get("asset_type") in freak_types]
    stage("Freak", "ok", f"specific/irreplaceable units present: {sorted(freak_present)}")

    grip = grip_score.score(assets, furniture_assessment)
    stage(
        "Flex",
        "ok" if grip["passes_gate"] else "refused",
        f"GRIP {grip['total']}/{grip_score.MAX_TOTAL} "
        f"(gate requires >= {grip_score.GATE_THRESHOLD})",
    )

    refusal_codes = list(_check_consent(provenance))
    if not furniture_assessment["load_bearing"]:
        refusal_codes.append(FURNITURE_NOT_LOAD_BEARING)
    if not grip["passes_gate"]:
        refusal_codes.append(GRIP_BELOW_THRESHOLD)
    if not lineage_result["valid"]:
        refusal_codes.append(LINEAGE_INVALID)
    refusal_codes = sorted(set(refusal_codes))

    stage(
        "Fit",
        "ok" if not refusal_codes else "refused",
        "privacy/consent/grip/lineage gate passed" if not refusal_codes
        else f"refusal codes: {refusal_codes}",
    )

    input_hash = sha256_json(request)
    stage("Freeze", "ok", f"inputs locked, input_hash={input_hash}")

    decision = "FLOP" if refusal_codes else "FINALIZE"

    song_brief: dict[str, Any] | None = None
    if decision == "FINALIZE":
        song_brief = _build_song_brief(request, assets, furniture_assessment, grip, lineage_result)

    decode_autopsy = {
        "asset_type": "decode_autopsy",
        "batch_id": batch_id,
        "decision": decision,
        "grip": grip,
        "furniture_assessment": furniture_assessment,
        "refusal_codes": refusal_codes,
        "f11_trace": trace,
    }

    return {
        "batch_id": batch_id,
        "f11_trace": trace,
        "furniture_assessment": furniture_assessment,
        "grip": grip,
        "lineage": lineage_result,
        "refusal_codes": refusal_codes,
        "decision": decision,
        "next_step": "Finagle" if decision == "FLOP" else "none",
        "song_brief": song_brief,
        "decode_autopsy": decode_autopsy,
        "input_hash": input_hash,
        "output_hash": sha256_json(song_brief) if song_brief is not None else None,
    }


def _build_song_brief(
    request: dict[str, Any],
    assets: list[dict[str, Any]],
    furniture_assessment: dict[str, Any],
    grip: dict[str, Any],
    lineage_result: dict[str, Any],
) -> dict[str, Any]:
    provenance = request["provenance"]
    lineage_map = {a["asset_id"]: a.get("parent_ids", []) for a in assets}

    def field(asset_type: str) -> dict[str, Any] | None:
        return _asset_by_type(assets, asset_type)

    brief = {
        "asset_type": "song_brief",
        "batch_id": request["batch_id"],
        "f_tier": provenance["f_tier"],
        "source_provenance": provenance["source_provenance"],
        "storage_permitted": provenance["consent_to_store"] is True,
        "publication_permitted": provenance.get("consent_to_publish") is True,
        "grip": grip,
        "furniture": {**request["furniture"], "load_bearing": furniture_assessment["load_bearing"]},
        "want_resistance_pair": field("want_resistance_pair"),
        "power_vector": field("power_vector"),
        "consent_beat": field("consent_beat"),
        "sensory_triad": field("sensory_triad"),
        "contradiction_pair": field("contradiction_pair"),
        "phrase_atom": field("phrase_atom"),
        "hook_thesis": field("hook_thesis"),
        "sonic_cell": field("sonic_cell"),
        "lineage": lineage_map,
        "next_bounded_experiment": request.get("next_bounded_experiment"),
        "compiled_at": request.get("compiled_at"),
        "provider": None,
    }
    brief["song_brief_id"] = f"brief.{sha256_json(brief)[:16]}"
    return brief


def compile_and_receipt(request: dict[str, Any], chain: list[dict[str, Any]]) -> dict[str, Any]:
    """Compile a batch and append its sealed receipt entry to ``chain``."""
    result = compile_batch(request)
    grip = result["grip"]
    proof_state = {
        "grip_total": grip["total"],
        "grip_passes_gate": grip["passes_gate"],
        "furniture_load_bearing": result["furniture_assessment"]["load_bearing"],
        "lineage_valid": result["lineage"]["valid"],
        "privacy_gate_passes": not result["refusal_codes"],
    }
    entry = append(
        chain,
        batch_id=result["batch_id"],
        input_hash=result["input_hash"],
        output_hash=result["output_hash"],
        decision=result["decision"],
        refusal_codes=result["refusal_codes"],
        proof_state=proof_state,
    )
    result["receipt_entry"] = entry
    return result
