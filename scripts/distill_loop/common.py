"""Shared helpers for the Quirk distill loop.

Everything here is deterministic and side-effect free. Nothing in this package
admits a skill, grants runtime authority, or promotes Canon.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

TRIGGER_ACTOR = "agent.distill-loop"
CANDIDATE_PREFIX = "quirk-distilled-"
CANDIDATE_VERSION = "0.1.0"
LEDGER_PATH = "skills/distill-ledger.json"
DISTILLED_EVAL_DIR = "evals/skills/distilled"
GENESIS_SHA256 = "0" * 64
MIN_SUCCESSFUL_MOVES = 3
REQUIRED_EVAL_KINDS = frozenset({"positive", "adversarial", "regression", "authority"})

AUTHORITY_RANK = {
    "observe": 0,
    "infer": 1,
    "propose": 2,
    "execute_bounded": 3,
}

SCHEMA_FILES = {
    "skill_package": "schemas/skill-package.schema.json",
    "skill_eval_case": "schemas/skill-eval-case.schema.json",
    "skill_run_receipt": "schemas/skill-run-receipt.schema.json",
    "skill_runtime_grant": "schemas/skill-runtime-grant.schema.json",
    "distill_run_trace": "schemas/distill-run-trace.schema.json",
    "distill_ledger": "schemas/distill-ledger.schema.json",
    "distill_promotion_receipt": "schemas/distill-promotion-receipt.schema.json",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_text(canonical_json(value))


def sha256_json_without_keys(value: dict[str, Any], omitted_keys: set[str]) -> str:
    return sha256_json({key: item for key, item in value.items() if key not in omitted_keys})


def pretty_json(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def load_schemas(root: Path) -> dict[str, dict[str, Any]]:
    schemas: dict[str, dict[str, Any]] = {}
    for key, relative in SCHEMA_FILES.items():
        schema = json.loads((root / relative).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        schemas[key] = schema
    return schemas


def schema_errors(schema: dict[str, Any], instance: Any) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path))
    ]


def registry_digest(registry: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in registry.items() if key != "registry_sha256"})


def source_registration_errors(registry: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    """A source skill may only be distilled if the manifested registry carries this exact digest."""
    if registry.get("registry_sha256") != registry_digest(registry):
        return ["registry digest mismatch; refusing to trust its entries"]
    digest = manifest.get("integrity", {}).get("manifest_sha256")
    for entry in registry.get("skills", []):
        if (
            entry.get("id") == manifest.get("id")
            and entry.get("version") == manifest.get("version")
            and entry.get("manifest_sha256") == digest
        ):
            return []
    return ["source skill is not in the manifested registry at this exact digest"]


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return parsed.astimezone(timezone.utc)


def unique_in_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def write_files(root: Path, files: dict[str, str]) -> list[Path]:
    """Write each file through a temp sibling and an atomic replace, ledger last."""
    written: list[Path] = []
    ordered = sorted(files.items(), key=lambda item: (item[0] == LEDGER_PATH, item[0]))
    for relative, text in ordered:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_name(path.name + ".tmp")
        temp.write_text(text, encoding="utf-8")
        os.replace(temp, path)
        written.append(path)
    return written
