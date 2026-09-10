#!/usr/bin/env python3
"""Run the bounded protocol tests and emit one content-bound evidence receipt."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


class EvidenceResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.executed_ids = []

    def startTest(self, test):
        self.executed_ids.append(test.id())
        super().startTest(test)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    started = datetime.now(timezone.utc).isoformat()
    before = time.perf_counter()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_unsigned_rationale*.py")
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=EvidenceResult).run(suite)
    elapsed = time.perf_counter() - before
    paths = [ROOT / "scripts/unsigned_rationale.py", Path(__file__).resolve(),
             ROOT / "schemas/unsigned-rationale.schema.json",
             ROOT / ".github/workflows/unsigned-rationale-conformance.yml"]
    for directory, pattern in (("tests", "test_unsigned_rationale*.py"), ("examples/unsigned-rationale", "*"),
                               ("docs/unsigned-rationale", "*")):
        paths.extend(path for path in (ROOT / directory).glob(pattern)
                     if path.is_file() and path.resolve() != Path(args.output).resolve())
    hashes = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(set(paths))}
    passed = result.wasSuccessful() and result.testsRun > 0 and not result.skipped and not result.expectedFailures
    receipt = {
        "receipt_version": "0.1.0", "status": "CANDIDATE", "authority_maximum_right": "none",
        "capability_ref": "capability.unsigned-rationale-custody", "implementation_version": "0.1.0",
        "source_base_commit": "499f94b8d12e29dd7804cc9b537fd70f6a8048d8",
        "tested_commit": os.environ.get("GITHUB_SHA"), "pr_head_sha": os.environ.get("QUIRK_PR_HEAD_SHA"),
        "python_version": platform.python_version(), "started_at": started,
        "completed_at": datetime.now(timezone.utc).isoformat(), "duration_seconds": elapsed,
        "command": "python scripts/check_unsigned_rationale.py --output <receipt-path>",
        "verdict": "PASS" if passed else "FAIL", "tests_run": result.testsRun,
        "failures": len(result.failures), "errors": len(result.errors), "skips": len(result.skipped),
        "executed_tests": result.executed_ids, "test_output": stream.getvalue(), "file_sha256": hashes,
        "observed_local_effects": "Temporary fixture exports and explicitly requested evidence-file write",
        "network_effects_executed": False, "graph_applied": False, "training_permission": False,
        "source_observation_trust": "CALLER_SUPPLIED_UNVERIFIED", "human_benefit": None,
        "compute_cost": None, "human_review_minutes": None,
        "not_proven": ["Full JSON Schema standards conformance", "Source authenticity or authority enforcement",
                       "Native Preference intake compatibility", "Quirk Now UI integration", "Human-use benefit",
                       "Power-loss atomicity", "Production or canon admission"],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"{receipt['verdict']}: {result.testsRun} protocol/file tests; {len(hashes)} file digests; declaration and local file behavior only")
    if not passed:
        print(stream.getvalue(), file=sys.stderr)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
