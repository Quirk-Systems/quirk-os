#!/usr/bin/env python3
"""Bind a passing One-to-Infinity candidate report to a clean exact Git head.

Creates a review artifact only. No runtime, merge, or canon authority is granted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


class ReceiptError(ValueError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(repo: Path, *args: str) -> str:
    run = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if run.returncode:
        raise ReceiptError(f"git {' '.join(args)} failed: {run.stderr.strip()}")
    return run.stdout.strip()


def fail_if(condition: bool, reason: str) -> None:
    if condition:
        raise ReceiptError(reason)


def checked_head(repo: Path, expected_head: str | None = None) -> str:
    head = git(repo, "rev-parse", "HEAD")
    if expected_head is not None:
        fail_if(not re.fullmatch(r"[0-9a-f]{40}", expected_head),
                "expected_head must be an exact lowercase 40-hex commit SHA")
        fail_if(head != expected_head, "checked-out HEAD differs from expected PR head")
    fail_if(bool(git(repo, "status", "--porcelain", "--untracked-files=no")),
            "tracked source files are dirty")
    fail_if(bool(git(repo, "ls-files", "--others", "--exclude-standard", "--",
                     "programs/one-to-infinity/tests",
                     "programs/one-to-infinity/contracts",
                     "programs/one-to-infinity/fixtures")),
            "untracked candidate source files are present")
    return head


def make_receipt(repo: Path, expected_head: str) -> dict:
    repo = repo.resolve()
    head = checked_head(repo, expected_head)

    root = repo / "programs" / "one-to-infinity"
    report_path = root / "evidence" / "validation-report.generated.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    fail_if(report.get("git_head") != head, "validation report head differs from checked-out HEAD")
    fail_if(report.get("candidate_only") is not True, "report is not candidate-only")
    fail_if(report.get("status") != "pass", "validator status is not pass")
    fail_if(
        report.get("admission") != "NOT_ADMITTED",
        "candidate report unexpectedly claims admission",
    )
    fail_if(report.get("positive_passing") != 4, "positive fixture count is not 4")
    fail_if(
        report.get("adversarial_rejecting_for_intended_rule") != 11,
        "adversarial intended-rule count is not 11",
    )
    fail_if(len(report.get("results", [])) != 15, "expected exactly 15 fixture results")
    fail_if(
        any(r.get("passed") is not True for r in report["results"]),
        "at least one fixture failed",
    )

    validator_path = root / "tests" / "validate_contracts.py"
    fail_if(
        sha256(validator_path) != report.get("validator_sha256"),
        "validator digest differs from passing report",
    )

    schema_hashes = report.get("schema_sha256", {})
    fail_if(
        set(schema_hashes) != {"transformation", "run", "evidence", "promotion"},
        "schema digest set incomplete",
    )
    for name, digest in sorted(schema_hashes.items()):
        fail_if(
            sha256(root / "contracts" / f"{name}.schema.json") != digest,
            f"schema {name} differs from passing report",
        )

    observed_fixtures = set()
    for result in report["results"]:
        if result["expected"] == "accept":
            path = root / "fixtures" / "positive" / result["fixture"]
        elif result["expected"] == "reject":
            path = root / "fixtures" / "adversarial" / f"{result['fixture']}.json"
        else:
            raise ReceiptError("unexpected fixture expectation")
        fail_if(not path.is_file(), f"fixture is missing: {path}")
        fail_if(path in observed_fixtures, "duplicate fixture identity in validation report")
        observed_fixtures.add(path)
        fail_if(
            sha256(path) != result.get("sha256"),
            f"fixture changed after validation: {path.name}",
        )

    actual_fixture_paths = (
        set((root / "fixtures" / "positive").glob("*.json"))
        | set((root / "fixtures" / "adversarial").glob("*.json"))
    )
    fail_if(
        actual_fixture_paths != observed_fixtures,
        "fixture inventory changed after validation",
    )

    checked_head(repo, expected_head)
    manifest = root / "MANIFEST.json"
    return {
        "receipt_type": "one-to-infinity-candidate-ci-binding",
        "version": "0.2.0-candidate",
        "git_head": head,
        "git_tree": git(repo, "rev-parse", "HEAD^{tree}"),
        "validated_report_sha256": sha256(report_path),
        "manifest_sha256": sha256(manifest),
        "validator_sha256": sha256(validator_path),
        "schema_sha256": dict(sorted(schema_hashes.items())),
        "fixture_results": {"positive": 4, "adversarial_intended_rule": 11},
        "candidate_only": True,
        "human_approval": False,
        "runtime_grant": False,
        "provider_access_grant": False,
        "publication_grant": False,
        "canon_promotion": False,
        "not_proven": [
            "production beneficiary value",
            "long-run retention",
            "compounding",
            "human approval",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
    )
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    dest = args.out or args.repo_root / "programs" / "one-to-infinity" / "evidence" / "ci-receipt.json"
    try:
        fail_if(dest.is_symlink(), "receipt output must not be a symlink")
        # Never overwrite a tracked source file, even when --out is explicit.
        try:
            relative = dest.resolve().relative_to(args.repo_root.resolve()).as_posix()
        except ValueError:
            relative = None
        if relative:
            fail_if(bool(git(args.repo_root, "ls-files", "--", ":(literal)" + relative)),
                    "receipt output is tracked source")
        # Artifact upload runs even after failure; remove an earlier success first.
        dest.unlink(missing_ok=True)
        result = make_receipt(args.repo_root, args.expected_head)
    except (ReceiptError, OSError, KeyError, TypeError, ValueError) as e:
        print(f"RECEIPT_BLOCKED: {e}", file=sys.stderr)
        return 1
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"CI_RECEIPT_PASS head={result['git_head']} "
        f"report_sha256={result['validated_report_sha256']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
