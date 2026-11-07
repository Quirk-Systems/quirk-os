#!/usr/bin/env python3
"""Validate the shared QIS candidate evidence envelope."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


CANDIDATE_BRANCH = "agent/quirk-intent-shaper"
CANDIDATE_SHA = "f5effa3d6da3e5879e10007492aeff39a1c643be"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_receipt_payload(receipt: dict[str, Any]) -> bytes:
    value = copy.deepcopy(receipt)
    value.pop("receipt_hash", None)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def receipt_hash(receipt: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_receipt_payload(receipt)).hexdigest()


def repository_file(repo: Path, path: str) -> Path:
    root = repo.resolve()
    if Path(path).is_absolute():
        raise ValueError("path must be relative to the repository")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("path must resolve within the repository")
    if not resolved.is_file():
        raise ValueError(f"missing file {path}")
    return resolved


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
    if repository.get("candidate_branch") != CANDIDATE_BRANCH or candidate_sha != CANDIDATE_SHA:
        errors.append("repository candidate identity must match the evaluated branch and SHA")
    if candidate_sha and merge_base_sha and candidate_sha != merge_base_sha:
        errors.append("repository.merge_base_sha must exactly match repository.candidate_sha")
    if repository.get("is_traceable_descendant") is not True:
        errors.append("repository.is_traceable_descendant must be true")
    if repo is None:
        errors.append("repository checkout is required for ancestry and file verification")
    else:
        try:
            actual_merge_base = subprocess.check_output(
                ["git", "-C", str(repo), "merge-base", CANDIDATE_SHA, repository["head_sha"]],
                text=True,
                stderr=subprocess.PIPE,
            ).strip()
            if actual_merge_base != CANDIDATE_SHA:
                errors.append("repository.head_sha is not a traceable descendant of the evaluated candidate")
            if merge_base_sha != actual_merge_base:
                errors.append("repository.merge_base_sha does not match Git history")
        except (OSError, subprocess.CalledProcessError) as exc:
            errors.append(f"repository ancestry could not be verified against Git history: {exc}")

    materials = receipt.get("materials", [])
    material_paths: set[str] = set()
    for index, material in enumerate(materials):
        path = material.get("path")
        if path in material_paths:
            errors.append(f"materials[{index}]: duplicate material path {path!r}")
        else:
            material_paths.add(path)
        if repo is not None:
            try:
                material_file = repository_file(repo, path)
                digest = hashlib.sha256(material_file.read_bytes()).hexdigest()
                if digest != material["sha256"]:
                    errors.append(f"materials[{index}]: sha256 mismatch for {path}")
            except (OSError, ValueError, RuntimeError) as exc:
                errors.append(f"materials[{index}]: {exc}")

    evidence_refs = receipt.get("evidence_refs", [])
    evidence_paths: set[str] = set()
    for index, path in enumerate(evidence_refs):
        if path in evidence_paths:
            errors.append(f"evidence_refs[{index}]: duplicate evidence ref {path!r}")
        else:
            evidence_paths.add(path)
        if repo is not None:
            try:
                repository_file(repo, path)
            except (OSError, ValueError, RuntimeError) as exc:
                errors.append(f"evidence_refs[{index}]: {exc}")

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
    errors = schema_errors(schema, receipt)
    return errors if errors else semantic_errors(receipt, repo=repo)


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
