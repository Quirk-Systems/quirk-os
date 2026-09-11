"""Load-bearing Furniture check.

Furniture is load-bearing only if every dimension answers a concrete
question: bodies/position, objects/obstruction, distance/movement,
temperature, acoustics, geography, privacy pressure. The test named in the
mission brief is literal: "Could we block this scene physically and mix it
spatially?" Decorative filler ("a room", "n/a", "some stuff") must fail.

The check is deliberately a dumb, deterministic keyword gate rather than a
model call: it has to be reproducible inside a receipt and inside a test,
not a judgment call that drifts between runs.
"""
from __future__ import annotations

from typing import Any

FIELDS = (
    "bodies_position",
    "objects_obstruction",
    "distance_movement",
    "temperature",
    "acoustics",
    "geography",
    "privacy_pressure",
)

_DECORATIVE = {"", "n/a", "na", "none", "tbd", "unknown", "unspecified", "some stuff", "a room"}

# Small, closed vocabularies per dimension. A field only counts as
# load-bearing if it names something concrete enough to block and mix, not
# just genre-flavor language.
_CONCRETE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "bodies_position": (
        "stand", "sit", "lean", "kneel", "facing", "behind", "beside", "between",
        "shoulder", "hand", "back", "knee", "hip", "across from", "over",
    ),
    "objects_obstruction": (
        "table", "door", "wall", "counter", "curtain", "window", "box", "chair",
        "shelf", "blanket", "couch", "desk", "fence", "railing", "sink",
    ),
    "distance_movement": (
        "step", "reach", "cross", "approach", "retreat", "inch", "pace",
        "lean in", "pull back", "distance", "feet", "meter", "arm's length", "across the room",
    ),
    "temperature": (
        "warm", "cold", "hot", "cool", "chill", "heat", "humid", "frost", "sweat", "draft",
    ),
    "acoustics": (
        "echo", "muffle", "quiet", "loud", "hum", "creak", "thin wall", "reverb",
        "silence", "whisper carries", "thud", "carries through",
    ),
    "geography": (
        "kitchen", "apartment", "street", "stairwell", "parking lot", "rooftop",
        "hallway", "bedroom", "car", "porch", "alley", "room", "yard",
    ),
    "privacy_pressure": (
        "door lock", "curtain", "neighbor", "thin wall", "roommate", "overheard",
        "shared", "private", "exposed", "closed door", "blinds", "landlord",
    ),
}


def assess(furniture: dict[str, Any]) -> dict[str, Any]:
    """Assess one Furniture block. Returns a per-field breakdown plus the
    overall load_bearing verdict and the literal block-and-mix question.
    """
    per_field: dict[str, bool] = {}
    for field in FIELDS:
        raw = str(furniture.get(field, "") or "").strip()
        normalized = raw.lower()
        present = normalized not in _DECORATIVE and len(raw.split()) >= 3
        concrete = present and any(keyword in normalized for keyword in _CONCRETE_KEYWORDS[field])
        per_field[field] = bool(concrete)

    load_bearing = all(per_field.values())
    missing_or_decorative = [field for field, ok in per_field.items() if not ok]

    return {
        "per_field": per_field,
        "load_bearing": load_bearing,
        "missing_or_decorative_fields": missing_or_decorative,
        "answers_block_and_mix_question": load_bearing,
    }
