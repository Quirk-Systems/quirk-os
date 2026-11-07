"""ADR-0003: runtime-manifest-content.v1 (Python JSON, not JCS).

This digest binds content, never approval or lifecycle authority.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

HASH_PROFILE = "runtime-manifest-content.v1"
COVERED_FIELDS = frozenset({
    "schema_version", "manifest_key", "manifest_kind", "version", "canonical_uri",
    "authority_ceiling", "domains", "tools", "inputs_schema_ref", "outputs_schema_ref",
    "eval_refs", "skill_refs", "stop_conditions", "rights_review", "trigger_contract", "metadata",
})
EXCLUDED_FIELDS = frozenset({"content_hash", "admission", "status", "requested_status"})
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas/runtime-manifest.schema.json"


class ContentError(ValueError):
    pass


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ContentError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _nonfinite(value):
    raise ContentError(f"nonfinite JSON number: {value}")


def _json_value(value: Any) -> None:
    if value is None or type(value) in (bool, int):
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ContentError("nonfinite JSON number")
        return
    if type(value) is str:
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise ContentError("invalid Unicode scalar") from exc
        return
    if type(value) is list:
        for item in value:
            _json_value(item)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ContentError("JSON object keys must be strings")
            _json_value(key)
            _json_value(item)
        return
    raise ContentError("non-JSON value")


def strict_json_loads(raw: str | bytes) -> Any:
    try:
        result = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_nonfinite)
        _json_value(result)
        return result
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ContentError(str(exc)) from exc


def validate_manifest_shape(manifest: dict[str, Any]) -> None:
    _json_value(manifest)
    schema = strict_json_loads(SCHEMA_PATH.read_bytes())
    if set(schema["properties"]) != COVERED_FIELDS | EXCLUDED_FIELDS:
        raise ContentError("manifest schema field set changed: a new hash profile is required")
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(manifest))
    if errors:
        raise ContentError("manifest schema: " + errors[0].message)


def manifest_preimage(manifest: dict[str, Any]) -> bytes:
    validate_manifest_shape(manifest)
    content = {key: value for key, value in manifest.items() if key in COVERED_FIELDS}
    return json.dumps(content, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def manifest_content_hash(manifest: dict[str, Any]) -> str:
    return hashlib.sha256(manifest_preimage(manifest)).hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    result = strict_json_loads(path.read_bytes())
    validate_manifest_shape(result)
    return result
