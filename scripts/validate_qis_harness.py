#!/usr/bin/env python3
"""Validate the shared QIS candidate evidence envelope."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_receipt_payload(receipt: dict[str, Any]) -> bytes:
    value = copy.deepcopy(receipt)
    value.pop("receipt_hash", None)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def receipt_hash(receipt: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_receipt_payload(receipt)).hexdigest()


def schema_errors(schema: dict[str, Any], receipt: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(receipt), key=lambda item: list(item.absolute_path))
    ]


def semantic_errors(receipt: dict[str, Any], repo: Path | None = None) -> list[str]:
    errors: list[str] = []

    repository = receipt.get("repository", {})
    candidate_sha = repository.get("candidate_sha")
    merge_base_sha = repository.get("merge_base_sha")
    if candidate_sha and merge_base_sha and candidate_sha != merge_base_sha:
        errors.append("repository.merge_base_sha must exactly match repository.candidate_sha")
    if repository.get("is_traceable_descendant") is not True:
        errors.append("repository.is_traceable_descendant must be true")

    materials = receipt.get("materials", [])
    material_paths: set[str] = set()
    for index, material in enumerate(materials):
        path = material.get("path")
        if path in material_paths:
            errors.append(f"materials[{index}]: duplicate material path {path!r}")
        else:
            material_paths.add(path)
        if repo is not None and isinstance(path, str) and not (repo / path).is_file():
            errors.append(f"materials[{index}]: missing file {path}")

    evidence_refs = receipt.get("evidence_refs", [])
    evidence_paths: set[str] = set()
    for index, path in enumerate(evidence_refs):
        if path in evidence_paths:
            errors.append(f"evidence_refs[{index}]: duplicate evidence ref {path!r}")
        else:
            evidence_paths.add(path)
        if repo is not None and isinstance(path, str) and not (repo / path).is_file():
            errors.append(f"evidence_refs[{index}]: missing file {path}")

    verdict = receipt.get("verdict")
    critical_failures = receipt.get("critical_failures", [])
    if verdict == "PASS" and critical_failures:
        errors.append("critical failures cannot coexist with a PASS verdict")

    for index, command in enumerate(receipt.get("commands", [])):
        counts = command.get("counts", {})
        passed = counts.get("passed")
        failed = counts.get("failed")
        total = counts.get("total")
        if all(isinstance(value, int) for value in (passed, failed, total)) and passed + failed != total:
            errors.append(f"commands[{index}].counts total must equal passed + failed")

        status = command.get("status")
        exit_code = command.get("exit_code")
        if status == "passed":
            if exit_code != 0:
                errors.append(f"commands[{index}] passed commands must use exit_code 0")
            if failed != 0:
                errors.append(f"commands[{index}] passed commands must report failed = 0")
        if status == "failed" and exit_code == 0 and failed == 0:
            errors.append(f"commands[{index}] failed commands must record a failing exit code or failed count")
        if verdict == "PASS" and (status != "passed" or exit_code != 0 or failed != 0):
            errors.append(f"commands[{index}] PASS verdict requires all commands to pass exactly")

    expected_hash = receipt_hash(receipt)
    if receipt.get("receipt_hash") != expected_hash:
        errors.append(f"receipt_hash mismatch: expected {expected_hash}")

    return errors


def validate_receipt(receipt: dict[str, Any], schema: dict[str, Any], repo: Path | None = None) -> list[str]:
    return schema_errors(schema, receipt) + semantic_errors(receipt, repo=repo)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a QIS candidate evidence envelope.")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Repository root for path checks.")
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("schemas/qis-evidence-envelope.schema.json"),
        help="Schema path, absolute or relative to --repo.",
    )
    parser.add_argument("--receipt", type=Path, required=True, help="Receipt JSON path.")
    args = parser.parse_args()

    repo = args.repo.resolve()
    schema_path = args.schema if args.schema.is_absolute() else repo / args.schema
    receipt_path = args.receipt if args.receipt.is_absolute() else repo / args.receipt

    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    receipt = load_json(receipt_path)
    errors = validate_receipt(receipt, schema, repo=repo)

    summary = {
        "receipt": str(receipt_path.relative_to(repo)),
        "valid": not errors,
        "error_count": len(errors),
        "errors": errors,
        "receipt_hash": receipt.get("receipt_hash"),
    }
    print(json.dumps(summary, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
