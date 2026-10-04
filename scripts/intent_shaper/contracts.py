"""Shared full-object validation for candidate plans and canonical Proposed Moves."""

from __future__ import annotations

from typing import Any, Mapping

from jsonschema import Draft202012Validator, FormatChecker
# jsonschema silently omits date-time checking when this existing dependency is
# absent. Import it explicitly so both command-line gates fail closed instead.
import rfc3339_validator  # noqa: F401

from .policy import _persona_rejection_reasons, persona_weight_total_valid


def schema_errors(value: Any, schema: Mapping[str, Any]) -> list[str]:
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return sorted(
        f"{'/'.join(map(str, error.path))}:{error.message}"
        for error in validator.iter_errors(value)
    )


def validate_personalization_plan(value: Any, schema: Mapping[str, Any]) -> list[str]:
    """Validate the entire plan, not merely isolated evaluator operations."""
    errors = schema_errors(value, schema)
    if errors:
        return errors
    if value["settings"]["personalization_enabled"]:
        hand = value["persona_hand"]
        selections = [hand["primary"], *hand["supporting"]]
        if not persona_weight_total_valid(selections):
            errors.append("persona_hand:invalid_weight_total")
        for index, selection in enumerate(selections):
            errors.extend(
                f"persona_hand/{index}:{reason}"
                for reason in _persona_rejection_reasons(selection)
            )
    return errors


def validate_proposed_move(value: Any, schema: Mapping[str, Any]) -> list[str]:
    errors = schema_errors(value, schema)
    if not isinstance(value, dict):
        return errors
    # Schema minLength doesn't exclude whitespace; do not treat it as evidence
    # or a receipt. Resolution artifacts are obligations, not proof of execution.
    for field in ("evidence_refs", "resolution_artifacts"):
        refs = value.get(field)
        if isinstance(refs, list):
            errors.extend(
                f"{field}/{index}:nonempty_ref_required"
                for index, ref in enumerate(refs)
                if isinstance(ref, str) and not ref.strip()
            )
    for field in ("receipt_ref", "resolution_note"):
        if field in value and isinstance(value[field], str) and not value[field].strip():
            errors.append(f"{field}:nonempty_ref_required")
    if value.get("disposition") in {"verified", "rejected", "poisoned", "boneyard"}:
        if not value.get("evidence_refs"):
            errors.append("evidence_refs:resolved_move_requires_evidence")
    return errors
