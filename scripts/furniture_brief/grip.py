"""GRIP scoring: Grounded, Reciprocal, Irreplaceable, Performable.

Each axis is worth 0-2 points from concrete, checkable signals only (never
a vibe call), for a 0-8 total. Only 7-8 may cross the generation gate.
"""
from __future__ import annotations

from typing import Any

GATE_THRESHOLD = 7
MAX_TOTAL = 8

# A small banlist of stock phrases. Not exhaustive -- it exists only to make
# "irreplaceable" fail deterministically on the laziest possible input, the
# same way the furniture keyword gate does.
_CLICHES = (
    "broken heart", "tears fall", "love hurts", "dance all night",
    "never let you go", "burning desire", "moth to a flame", "heart on fire",
)


def _asset_by_type(assets: list[dict[str, Any]], asset_type: str) -> dict[str, Any] | None:
    for asset in assets:
        if asset.get("asset_type") == asset_type:
            return asset
    return None


def score(assets: list[dict[str, Any]], furniture_assessment: dict[str, Any]) -> dict[str, Any]:
    reality_shard = _asset_by_type(assets, "reality_shard")
    want_resistance = _asset_by_type(assets, "want_resistance_pair")
    power_vector = _asset_by_type(assets, "power_vector")
    contradiction_pair = _asset_by_type(assets, "contradiction_pair")
    phrase_atom = _asset_by_type(assets, "phrase_atom")
    hook_thesis = _asset_by_type(assets, "hook_thesis")
    sonic_cell = _asset_by_type(assets, "sonic_cell")

    grounded = 0
    if reality_shard and len(str(reality_shard.get("text", "")).split()) >= 5:
        grounded += 1
    if furniture_assessment.get("load_bearing"):
        grounded += 1

    reciprocal = 0
    if want_resistance:
        want = str(want_resistance.get("want", "")).strip()
        resistance = str(want_resistance.get("resistance", "")).strip()
        if want and resistance and want.lower() != resistance.lower():
            reciprocal += 1
    if power_vector:
        holder = str(power_vector.get("holder", "")).strip()
        target = str(power_vector.get("target", "")).strip()
        if holder and target and holder.lower() != target.lower():
            reciprocal += 1

    irreplaceable = 0
    if contradiction_pair:
        a = str(contradiction_pair.get("a", "")).strip()
        b = str(contradiction_pair.get("b", "")).strip()
        if a and b and a.lower() != b.lower():
            irreplaceable += 1
    if phrase_atom:
        text = str(phrase_atom.get("text", "")).strip()
        if text and not any(cliche in text.lower() for cliche in _CLICHES):
            irreplaceable += 1

    performable = 0
    if hook_thesis and len(str(hook_thesis.get("text", "")).split()) >= 3:
        performable += 1
    if sonic_cell:
        tempo_feel = str(sonic_cell.get("tempo_feel", "")).strip()
        texture = str(sonic_cell.get("texture", "")).strip()
        space = str(sonic_cell.get("space", "")).strip()
        if tempo_feel and texture and space:
            performable += 1

    total = grounded + reciprocal + irreplaceable + performable
    return {
        "grounded": grounded,
        "reciprocal": reciprocal,
        "irreplaceable": irreplaceable,
        "performable": performable,
        "total": total,
        "gate_threshold": GATE_THRESHOLD,
        "passes_gate": total >= GATE_THRESHOLD,
    }
