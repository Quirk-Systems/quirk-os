from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.validate_submission_pack import validate

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "docs" / "applause-gate" / "submission-pack.json"
REPORT = ROOT / "evals" / "applause-gate" / "submission-pack-validation.json"
SCHEMA = ROOT / "schemas" / "submission-pack.schema.json"
VALIDATOR = ROOT / "scripts" / "validate_submission_pack.py"


class SubmissionPackTests(unittest.TestCase):
    def test_blocked_pack_is_contract_valid_but_not_submission_ready(self):
        report = validate(ROOT)
        self.assertTrue(report["contract_valid"], report["errors"])
        self.assertFalse(report["submission_ready"])
        self.assertEqual(report["pack_status"], "BLOCKED_INPUT_CONFLICT")
        self.assertEqual(report["checks"]["positive_case_count"], 0)
        self.assertEqual(report["checks"]["negative_case_count"], 0)
        self.assertFalse(report["checks"]["exact_case_counts"])
        self.assertFalse(report["checks"]["field_lengths_evaluated"])

    def test_vocabularies_are_exactly_the_issue_defined_values(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(
            schema["properties"]["status"]["enum"],
            [
                "PARTIAL_MISSING_INPUT",
                "BLOCKED_INPUT_CONFLICT",
                "BLOCKED_UNVERIFIED_EVIDENCE",
            ],
        )
        self.assertEqual(
            schema["$defs"]["ledgerEntry"]["properties"]["classification"]["enum"],
            [
                "CONFIRMED_PRODUCT_FACT",
                "PASSED_TEST_EVIDENCE",
                "PROPOSED_OR_UNVERIFIED",
                "MISSING",
                "CONTRADICTION",
            ],
        )

    def test_partial_pack_with_public_copy_does_not_become_submission_ready(self):
        pack = json.loads(PACK.read_text(encoding="utf-8"))
        pack["public_copy"]["listing"] = {
            "name": "Unverified listing",
            "short_description": "Unverified",
            "description": "Unverified",
        }
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            pack_path = Path(directory) / "submission-pack.json"
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            report = validate(ROOT, pack_path.relative_to(ROOT))
        self.assertFalse(report["submission_ready"])
        self.assertTrue(report["contract_valid"], report["errors"])

    def test_cases_must_bind_to_package_and_passed_evidence(self):
        pack = json.loads(PACK.read_text(encoding="utf-8"))
        pack["package"]["submitted_package"]["sha256"] = "1" * 64
        pack["review_cases"]["positive"].append(
            {
                "id": "P1",
                "prompt": "Unbound case",
                "expected_behavior": "Do not accept",
                "package_sha256": "0" * 64,
                "evidence_refs": ["ABG11-E003"],
            }
        )
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            pack_path = Path(directory) / "submission-pack.json"
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            report = validate(ROOT, pack_path.relative_to(ROOT))
        self.assertFalse(report["contract_valid"])
        self.assertTrue(any("submitted package digest mismatch" in error for error in report["errors"]))
        self.assertTrue(
            any("non-passed current-package evidence" in error for error in report["errors"])
        )

    def test_mcp_package_never_satisfies_skills_only_boundary(self):
        pack = json.loads(PACK.read_text(encoding="utf-8"))
        submitted = pack["package"]["submitted_package"]
        submitted.update(
            {
                "public_name": "Applause Gate",
                "version": "0.1.0",
                "sha256": "0" * 64,
                "classification": "skills-only",
                "contains_mcp": True,
                "requires_authentication": False,
                "uses_live_data": False,
                "performs_external_actions": False,
                "capability_allowlist": ["Evaluate supplied evidence"],
            }
        )
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            pack_path = Path(directory) / "submission-pack.json"
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            report = validate(ROOT, pack_path.relative_to(ROOT))
        self.assertFalse(report["checks"]["package_boundary_complete"])

    def test_two_processes_produce_identical_output(self):
        command = [
            sys.executable,
            str(VALIDATOR),
            "--repo",
            str(ROOT),
            "--require-contract-valid",
        ]
        first = subprocess.run(command, check=False, capture_output=True, text=True)
        second = subprocess.run(command, check=False, capture_output=True, text=True)
        self.assertEqual(first.returncode, 0, first.stderr or first.stdout)
        self.assertEqual(second.returncode, 0, second.stderr or second.stdout)
        self.assertEqual(json.loads(first.stdout), json.loads(second.stdout))

    def test_committed_validation_report_matches_current_inputs(self):
        self.assertEqual(json.loads(REPORT.read_text(encoding="utf-8")), validate(ROOT))


if __name__ == "__main__":
    unittest.main()
