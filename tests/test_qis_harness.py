from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_qis_harness import (  # noqa: E402
    canonical_receipt_payload,
    receipt_hash,
    validate_receipt,
)


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class QISHarnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load("schemas/qis-evidence-envelope.schema.json")
        cls.fixture_dir = ROOT / "evals/qis-agent-harness"
        cls.valid = load("evals/qis-agent-harness/receipt.valid.json")

    def errors_for(self, relative_path: str) -> list[str]:
        return validate_receipt(load(relative_path), self.schema, repo=ROOT)

    def test_schema_is_valid_draft_2020_12(self) -> None:
        Draft202012Validator.check_schema(self.schema)

    def test_valid_receipt_fixture_passes_and_hash_is_stable(self) -> None:
        self.assertEqual([], self.errors_for("evals/qis-agent-harness/receipt.valid.json"))
        expected_hash = hashlib.sha256(canonical_receipt_payload(self.valid)).hexdigest()
        self.assertEqual(expected_hash, receipt_hash(self.valid))
        self.assertEqual(expected_hash, self.valid["receipt_hash"])

    def test_unknown_verdict_fixture_fails(self) -> None:
        errors = self.errors_for("evals/qis-agent-harness/receipt.unknown-verdict.json")
        self.assertTrue(any("verdict" in error for error in errors))

    def test_missing_evidence_fixture_fails(self) -> None:
        errors = self.errors_for("evals/qis-agent-harness/receipt.missing-evidence.json")
        self.assertTrue(any("missing file" in error for error in errors))

    def test_unexpected_field_fixture_fails(self) -> None:
        errors = self.errors_for("evals/qis-agent-harness/receipt.unexpected-field.json")
        self.assertTrue(any("Additional properties are not allowed" in error for error in errors))

    def test_hash_mismatch_fixture_fails(self) -> None:
        errors = self.errors_for("evals/qis-agent-harness/receipt.hash-mismatch.json")
        self.assertTrue(any("receipt_hash mismatch" in error for error in errors))

    def test_critical_failure_cannot_hide_behind_pass(self) -> None:
        errors = self.errors_for("evals/qis-agent-harness/receipt.critical-failure-pass.json")
        self.assertIn("critical failures cannot coexist with a PASS verdict", errors)

    def test_ancestry_mismatch_fails_closed(self) -> None:
        errors = self.errors_for("evals/qis-agent-harness/receipt.ancestry-mismatch.json")
        self.assertTrue(any("traceable descendant" in error or "merge_base_sha" in error for error in errors))

    def test_instruction_files_stay_short_and_match_repo_commands(self) -> None:
        repo_text = (ROOT / ".github/copilot-instructions.md").read_text(encoding="utf-8")
        path_text = (ROOT / ".github/instructions/intent-shaper.instructions.md").read_text(
            encoding="utf-8"
        )
        skill_text = (ROOT / ".github/skills/intent-shaper-admission/SKILL.md").read_text(
            encoding="utf-8"
        )

        command = "python -m unittest tests.test_intent_shaper tests.test_qis_harness -v"
        validator = "python scripts/validate_qis_harness.py --repo . --receipt <receipt-path>"
        self.assertIn(command, repo_text)
        self.assertIn(command, path_text)
        self.assertIn(command, skill_text)
        self.assertIn(validator, repo_text)
        self.assertIn(validator, path_text)
        self.assertIn(validator, skill_text)
        self.assertLessEqual(len(repo_text.splitlines()), 10)
        self.assertLessEqual(len(path_text.splitlines()), 11)
        self.assertLessEqual(len(skill_text.splitlines()), 28)

    def test_skill_distinguishes_canonical_runtime_projection_and_evidence(self) -> None:
        text = (ROOT / ".github/skills/intent-shaper-admission/SKILL.md").read_text(encoding="utf-8")
        for heading in ("## Canonical objects", "## Runtime objects", "## Projections", "## Evidence"):
            self.assertIn(heading, text)

    def test_workflow_is_pull_request_only_and_uploads_expected_artifact(self) -> None:
        workflow_path = ROOT / ".github/workflows/qis-agent-harness.yml"
        workflow_text = workflow_path.read_text(encoding="utf-8")
        workflow = yaml.load(workflow_text, Loader=yaml.BaseLoader)

        self.assertEqual({"pull_request"}, set(workflow["on"].keys()))
        self.assertEqual("read", workflow["permissions"]["contents"])
        self.assertIn("schemas/qis-evidence-envelope.schema.json", workflow_text)
        self.assertIn("tests/test_qis_harness.py", workflow_text)
        self.assertIn("name: qis-agent-harness-${{ github.sha }}", workflow_text)
        self.assertIn("if-no-files-found: error", workflow_text)
        self.assertIn("retention-days: 30", workflow_text)
        self.assertIn("if: always()", workflow_text)
        self.assertIn('run: test -f "$RECEIPT_PATH"', workflow_text)
        self.assertNotIn("pull_request_target", workflow_text)
        self.assertNotIn("workflow_dispatch", workflow_text)
        self.assertNotIn("schedule:", workflow_text)


if __name__ == "__main__":
    unittest.main()
