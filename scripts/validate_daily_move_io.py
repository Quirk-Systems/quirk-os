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

    return sorted(set(findings))
