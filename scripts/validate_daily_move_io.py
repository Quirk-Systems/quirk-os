#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from jsonschema import Draft202012Validator

ROOT_DEFAULT = Path(__file__).resolve().parents[1]
INPUT_SCHEMA_PATH = Path("schemas/daily-move-input.schema.json")
OUTPUT_SCHEMA_PATH = Path("schemas/daily-move-output.schema.json")
VALID_INPUT_PATH = Path("evals/daily-move/io-cases/valid-input.json")
VALID_OUTPUT_PATH = Path("evals/daily-move/io-cases/valid-output.json")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def input_fingerprint(input_doc: Mapping[str, Any]) -> str:
    return sha256_json(input_doc)


def expected_output_hash(output_doc: Mapping[str, Any]) -> str:
    payload = copy.deepcopy(dict(output_doc))
    payload.pop("content_hash", None)
    return sha256_json(payload)


def validate_daily_move_pair(
    input_doc: Mapping[str, Any],
    output_doc: Mapping[str, Any],
    observed_spines: Mapping[str, str] | None = None,
) -> list[str]:
    del observed_spines  # Task 5 adds contextual duplicate-spine semantics.
    findings: list[str] = []

    input_schema = load_json(ROOT_DEFAULT / INPUT_SCHEMA_PATH)
    output_schema = load_json(ROOT_DEFAULT / OUTPUT_SCHEMA_PATH)
    if list(Draft202012Validator(input_schema).iter_errors(input_doc)):
        findings.append("INPUT_SCHEMA_INVALID")
    if list(Draft202012Validator(output_schema).iter_errors(output_doc)):
        findings.append("OUTPUT_SCHEMA_INVALID")

    input_spine = input_doc.get("outcome_spine")
    output_spine = output_doc.get("outcome_spine")
    if not isinstance(input_spine, Mapping):
        findings.append("NO_SPINE")
    else:
        required_spine_codes = {
            "goal_id": "MISSING_GOAL_ID",
            "move_id": "MISSING_MOVE_ID",
            "decision_id": "MISSING_DECISION_ID",
            "receipt_id": "MISSING_RECEIPT_ID",
            "outcome_id": "MISSING_OUTCOME_ID",
        }
        for field, code in required_spine_codes.items():
            if not input_spine.get(field):
                findings.append(code)

    if isinstance(input_spine, Mapping) and isinstance(output_spine, Mapping):
        mutation_codes = {
            "spine_id": "SPINE_ID_MUTATED",
            "move_id": "MOVE_ID_MUTATED",
            "decision_id": "DECISION_ID_MUTATED",
            "receipt_id": "RECEIPT_ID_MUTATED",
            "outcome_id": "OUTCOME_ID_MUTATED",
        }
        for field, code in mutation_codes.items():
            if input_spine.get(field) != output_spine.get(field):
                findings.append(code)
        if dict(input_spine) != dict(output_spine):
            findings.append("OUTCOME_SPINE_MUTATED")

    if isinstance(output_spine, Mapping):
        for field in ("decision_state", "receipt_state", "outcome_state"):
            if output_spine.get(field) != "reserved":
                findings.append("REALIZED_EVENT_FABRICATION")

    if output_doc.get("authority_ceiling") != "propose":
        findings.append("AUTHORITY_ABOVE_PROPOSE")

    input_sources = set(input_doc.get("source_refs", []))
    output_sources = set(output_doc.get("source_refs", []))
    if not output_sources.issubset(input_sources):
        findings.append("INVENTED_SOURCE_REF")

    available = input_doc.get("available_minutes")
    estimated = output_doc.get("estimated_minutes")
    if isinstance(available, int) and isinstance(estimated, int) and estimated > available:
        findings.append("TIMEBOX_EXCEEDED")

    timezone_name = input_doc.get("timezone")
    try:
        ZoneInfo(str(timezone_name))
    except (ZoneInfoNotFoundError, ValueError):
        findings.append("INVALID_TIMEZONE")

    try:
        expected_weekday = date.fromisoformat(str(input_doc.get("local_date"))).strftime("%A")
    except ValueError:
        expected_weekday = None
    if expected_weekday is not None and output_doc.get("weekday") != expected_weekday:
        findings.append("WEEKDAY_MISMATCH")

    if output_doc.get("content_hash") != expected_output_hash(output_doc):
        findings.append("CONTENT_HASH_MISMATCH")

    return sorted(set(findings))
