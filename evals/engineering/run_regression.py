#!/usr/bin/env python3
"""Verify and run the frozen engineering regression fixture set."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "evals/engineering/evaluator-manifest.json"
CASES_PATH = ROOT / "evals/engineering/regression-cases.jsonl"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def verify() -> tuple[dict[str, Any], list[str]]:
    manifest = _load_object(MANIFEST_PATH)
    expected_sources = manifest.get("source_sha256")
    if not isinstance(expected_sources, dict) or not expected_sources:
        raise ValueError("manifest source_sha256 must be a nonempty object")
    for relative, expected in sorted(expected_sources.items()):
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise ValueError("manifest source_sha256 entries must be strings")
        path = ROOT / relative
        if not path.resolve().is_relative_to(ROOT.resolve()) or not path.is_file():
            raise ValueError(f"pinned source is missing: {relative}")
        actual = _sha256(path)
        if actual != expected:
            raise ValueError(f"pinned source changed: {relative}")

    evaluator_digest = _sha256(MANIFEST_PATH)
    cases = []
    with CASES_PATH.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                raise ValueError(f"blank JSONL row at line {line_number}")
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"JSONL row {line_number} must be an object")
            cases.append(row)

    manifest_cases = manifest.get("case_selectors")
    if not isinstance(manifest_cases, list) or len(manifest_cases) != 11:
        raise ValueError("manifest must map exactly 11 cases")
    if len(cases) != 11:
        raise ValueError("JSONL must contain exactly 11 cases")
    mapped = {case["case_id"]: case["selectors"] for case in manifest_cases}
    if len(mapped) != 11:
        raise ValueError("manifest case IDs must be unique")
    seen = set()
    for row in cases:
        case_id = row.get("case_id")
        if case_id in seen or case_id not in mapped:
            raise ValueError(f"unexpected or duplicate JSONL case ID: {case_id}")
        seen.add(case_id)
        metadata = row.get("evaluation_metadata", {})
        if metadata.get("evaluator_digest") != evaluator_digest:
            raise ValueError(f"evaluator digest drift for {case_id}")
        if row.get("split") != "regression" or metadata.get("evidence_class") != "synthetic":
            raise ValueError(f"published case is not synthetic regression metadata: {case_id}")
        if row.get("input", {}).get("unittest_selectors") != mapped[case_id]:
            raise ValueError(f"selector mapping drift for {case_id}")

    selectors = [selector for case in manifest_cases for selector in case["selectors"]]
    if not selectors or any(not isinstance(selector, str) for selector in selectors):
        raise ValueError("manifest selectors must be nonempty strings")
    return manifest, selectors


def main() -> int:
    try:
        _manifest, selectors = verify()
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"engineering regression integrity failed: {exc}", file=sys.stderr)
        return 2
    return subprocess.call(
        [sys.executable, "-m", "unittest", "-v", *selectors], cwd=ROOT
    )


if __name__ == "__main__":
    raise SystemExit(main())
