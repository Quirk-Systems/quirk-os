from __future__ import annotations

import json
from typing import Any


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _reject_nonfinite(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _reject_duplicate_evidence_refs(value: Any) -> None:
    if isinstance(value, dict):
        assessments = value.get("evidence_assessments")
        if isinstance(assessments, list):
            seen: set[str] = set()
            for assessment in assessments:
                if not isinstance(assessment, dict):
                    continue
                evidence_ref = assessment.get("evidence_ref")
                if isinstance(evidence_ref, str):
                    if evidence_ref in seen:
                        raise ValueError(f"duplicate evidence_ref: {evidence_ref}")
                    seen.add(evidence_ref)
        for item in value.values():
            _reject_duplicate_evidence_refs(item)
    elif isinstance(value, list):
        for item in value:
            _reject_duplicate_evidence_refs(item)


def load_json_strict(text: str) -> Any:
    value = json.loads(
        text,
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_nonfinite,
    )
    _reject_duplicate_evidence_refs(value)
    return value
