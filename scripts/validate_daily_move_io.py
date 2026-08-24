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

from jsonschema import Draft202012Validator, FormatChecker

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


def _safe_string_set(value: Any) -> set[str]:
    if not isinstance(value, (list, tuple, set, frozenset)):
        return set()
    return {item for item in value if isinstance(item, str)}


def _looks_like_absolute_root(value: str) -> bool:
    return value.startswith("/") or (len(value) >= 3 and value[1:3] in {":\\", ":/"})


def _looks_like_invented_quirk_repository(value: str) -> bool:
    folded = value.casefold().rstrip("/")
    prefixes = (
        "quirk-systems/",
        "github.com/quirk-systems/",
        "https://github.com/quirk-systems/",
        "http://github.com/quirk-systems/",
    )
    for prefix in prefixes:
        if folded.startswith(prefix):
            repo = folded[len(prefix):].split("/", 1)[0]
            return repo != "quirk-os"
    return False


def _has_unsupported_architecture_hint(output_doc: Mapping[str, Any]) -> bool:
    raw_hints = output_doc.get("destination_hints", [])
    if not isinstance(raw_hints, (list, tuple)):
        return False
    for raw in raw_hints:
        value = str(raw)
        folded = value.casefold()
        if "quirkroot" in folded:
            return True
        if _looks_like_absolute_root(value):
            return True
        if _looks_like_invented_quirk_repository(value):
            return True
    return False


def validate_daily_move_pair(
    input_doc: Mapping[str, Any],
    output_doc: Mapping[str, Any],
    observed_spines: Mapping[str, str] | None = None,
    *,
    root: Path | None = None,
) -> list[str]:
    findings: list[str] = []
    schema_root = (root or ROOT_DEFAULT).resolve()

    input_schema = load_json(schema_root / INPUT_SCHEMA_PATH)
    output_schema = load_json(schema_root / OUTPUT_SCHEMA_PATH)
    format_checker = FormatChecker()
    if list(Draft202012Validator(input_schema, format_checker=format_checker).iter_errors(input_doc)):
        findings.append("INPUT_SCHEMA_INVALID")
    if list(Draft202012Validator(output_schema, format_checker=format_checker).iter_errors(output_doc)):
        findings.append("OUTPUT_SCHEMA_INVALID")

    if not isinstance(input_doc, Mapping):
        findings.extend(["INPUT_SCHEMA_INVALID", "NO_SPINE"])
        return sorted(set(findings))
    if not isinstance(output_doc, Mapping):
        findings.extend(["OUTPUT_SCHEMA_INVALID", "CONTENT_HASH_MISMATCH"])
        return sorted(set(findings))

    input_spine = input_doc.get("outcome_spine")
    output_spine = output_doc.get("outcome_spine")
    if not isinstance(input_spine, Mapping):
        findings.append("NO_SPINE")
    else:
        required_spine_codes = {
            "spine_id": "MISSING_SPINE_ID",
            "goal_id": "MISSING_GOAL_ID",
            "move_id": "MISSING_MOVE_ID",
            "decision_id": "MISSING_DECISION_ID",
            "receipt_id": "MISSING_RECEIPT_ID",
            "outcome_id": "MISSING_OUTCOME_ID",
        }
        for field, code in required_spine_codes.items():
            if not input_spine.get(field):
                findings.append(code)

        if observed_spines is not None:
            spine_id = input_spine.get("spine_id")
            if isinstance(spine_id, str) and spine_id in observed_spines:
                try:
                    fingerprint = input_fingerprint(input_doc)
                except (TypeError, ValueError):
                    findings.append("INPUT_SCHEMA_INVALID")
                else:
                    if observed_spines[spine_id] != fingerprint:
                        findings.append("DUPLICATE_SPINE_ID")

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

    input_sources = _safe_string_set(input_doc.get("source_refs", []))
    output_sources = _safe_string_set(output_doc.get("source_refs", []))
    if not output_sources.issubset(input_sources):
        findings.append("INVENTED_SOURCE_REF")

    available = input_doc.get("available_minutes")
    estimated = output_doc.get("estimated_minutes")
    if isinstance(available, int) and isinstance(estimated, int) and estimated > available:
        findings.append("TIMEBOX_EXCEEDED")

    canonical_destinations = input_doc.get("canonical_destination_refs", [])
    placement = output_doc.get("placement_disposition")
    if placement == "resolved" and not canonical_destinations:
        findings.append("PLACEMENT_UNRESOLVED")
    if _has_unsupported_architecture_hint(output_doc):
        findings.extend(["UNSUPPORTED_ARCHITECTURE", "PLACEMENT_UNRESOLVED"])

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

    try:
        expected_hash = expected_output_hash(output_doc)
    except (TypeError, ValueError):
        findings.append("CONTENT_HASH_MISMATCH")
    else:
        if output_doc.get("content_hash") != expected_hash:
            findings.append("CONTENT_HASH_MISMATCH")

    return sorted(set(findings))


def conformance_report(root: Path) -> dict[str, Any]:
    root = root.resolve()
    input_doc = load_json(root / VALID_INPUT_PATH)
    output_doc = load_json(root / VALID_OUTPUT_PATH)
    findings = validate_daily_move_pair(input_doc, output_doc, root=root)
    return {
        "schema_version": "daily-move.io-conformance.v1",
        "valid_pair": not findings,
        "finding_codes": findings,
        "input_fingerprint": input_fingerprint(input_doc),
        "output_content_hash": output_doc.get("content_hash"),
        "expected_output_hash": expected_output_hash(output_doc),
        "external_writes": 0,
        "authority_ceiling": "propose",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Quirk Daily Move input/output contracts.")
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    report = conformance_report(args.root)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(payload, end="")
    if args.report:
        target = args.report if args.report.is_absolute() else Path.cwd() / args.report
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(payload, encoding="utf-8")
    return 1 if args.require_pass and not report["valid_pair"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
