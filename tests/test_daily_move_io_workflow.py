from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github/workflows/daily-move-io-conformance.yml"


class DailyMoveIOWorkflowTests(unittest.TestCase):
    def test_workflow_runs_both_gates_and_uploads_fail_closed_receipt(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        required_tokens = (
            "schemas/daily-move-*.schema.json",
            "evals/daily-move/**",
            "scripts/validate_daily_move_io.py",
            "scripts/validate_daily_move_fixtures.py",
            "tests/test_daily_move_io.py",
            "tests/test_daily_move_io_workflow.py",
            "tests/test_daily_move_fixtures.py",
            "python scripts/validate_daily_move_fixtures.py --require-pass",
            "python scripts/validate_daily_move_io.py --require-pass --report daily-move-io-conformance.json",
            "python -m unittest tests.test_daily_move_fixtures -v",
            "python -m unittest tests.test_daily_move_io -v",
            "python -m unittest tests.test_daily_move_io_workflow -v",
            "Initialize Daily Move IO evidence",
            "VALIDATION_NOT_RUN",
            "daily-move-io-conformance.json",
            "contents: read",
        )
        for token in required_tokens:
            self.assertIn(token, workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertGreaterEqual(workflow.count("if: always()"), 4)

    def test_workflow_actions_are_pinned_and_contains_no_mutation_command(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        action_refs = re.findall(r"uses:\s+[^@]+@([^\s]+)", workflow)
        self.assertTrue(action_refs)
        for ref in action_refs:
            self.assertRegex(ref, r"^[0-9a-f]{40}$")
        for forbidden in (
            "contents: write",
            "git push",
            "gh pr merge",
            "merge_pull_request",
            "supabase",
            "airtable",
            "google drive",
        ):
            self.assertNotIn(forbidden, workflow.casefold())


if __name__ == "__main__":
    unittest.main()
