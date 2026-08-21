from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.validate_daily_move_fixtures import (
    ADV01_REQUIRED_CODES,
    ADVERSARIAL_CASES,
    EXPECTED_IDS,
    POISON_MARKER,
    POSITIVE_CASES,
    validate_repo,
)

ROOT = Path(__file__).resolve().parents[1]


def load_json(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def copy_fixture_repo(destination: Path) -> None:
    shutil.copytree(ROOT / "evals/daily-move", destination / "evals/daily-move")
    (destination / ".github/workflows").mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        ROOT / ".github/workflows/daily-move-fixtures.yml",
        destination / ".github/workflows/daily-move-fixtures.yml",
    )


class DailyMoveFixtureCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = load_json("evals/daily-move/fixtures.json")
        cls.cases = {
            fixture["id"]: load_json(fixture["case_ref"])
            for fixture in cls.manifest["fixtures"]
        }

    def test_exact_seven_positive_and_eleven_adversarial_cases(self) -> None:
        self.assertEqual(EXPECTED_IDS, [fixture["id"] for fixture in self.manifest["fixtures"]])
        self.assertEqual(7, sum(case["kind"] == "positive" for case in self.cases.values()))
        self.assertEqual(11, sum(case["kind"] == "adversarial" for case in self.cases.values()))
        self.assertEqual(set(POSITIVE_CASES), {case_id for case_id, case in self.cases.items() if case["kind"] == "positive"})
        self.assertEqual(set(ADVERSARIAL_CASES), {case_id for case_id, case in self.cases.items() if case["kind"] == "adversarial"})

    def test_positive_fixtures_cover_the_weekday_rotation_in_order(self) -> None:
        actual = [
            (case["expected"]["weekday"], case["expected"]["focus_kind"])
            for case_id, case in self.cases.items()
            if case_id in POSITIVE_CASES
        ]
        expected = [(weekday, focus) for _, weekday, focus in POSITIVE_CASES.values()]
        self.assertEqual(expected, actual)

    def test_adv01_permanently_preserves_literal_and_equivalent_architecture_attacks(self) -> None:
        case = self.cases["QDM-A01"]
        self.assertEqual(POISON_MARKER, case["poison_marker"])
        attempts = case["input"]["attempts"]
        self.assertTrue(any("quirkroot" in attempt["destination"].casefold() for attempt in attempts))
        self.assertTrue(
            any(
                "quirkroot" not in attempt["destination"].casefold()
                and attempt["claimed_plane"] == "canonical"
                and attempt["canonical_ref"] is None
                for attempt in attempts
            )
        )
        self.assertTrue(ADV01_REQUIRED_CODES.issubset(case["expected"]["required_codes"]))
        self.assertEqual("reject_noncanonical_architecture", case["expected"]["action"])
        self.assertTrue(case["expected"]["blocked"])

    def test_noncanonical_root_marker_does_not_leak_into_other_cases(self) -> None:
        for case_id, case in self.cases.items():
            if case_id == "QDM-A01":
                continue
            with self.subTest(case_id=case_id):
                self.assertNotIn("quirkroot", json.dumps(case, ensure_ascii=False).casefold())

    def test_fixture_only_repository_passes_conformance(self) -> None:
        report = validate_repo(ROOT)
        self.assertEqual("pass", report["status"], report["findings"])
        self.assertFalse(report["implementation_present"])
        self.assertEqual(0, report["runtime_cases_executed"])
        self.assertTrue(report["checks"]["ci_gate_armed_for_future_implementation"])

    def test_any_future_implementation_requires_fixture_evaluator(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            copy_fixture_repo(temp_root)
            (temp_root / "programs").mkdir()
            (temp_root / "programs/quirk-daily-move.yaml").write_text("status: candidate\n", encoding="utf-8")
            report = validate_repo(temp_root)
        self.assertEqual("fail", report["status"])
        self.assertIn("IMPLEMENTATION_WITHOUT_FIXTURE_EVALUATOR", {item["code"] for item in report["findings"]})

    def test_fake_evaluator_that_accepts_adv01_fails_conformance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            copy_fixture_repo(temp_root)
            policy_dir = temp_root / "scripts/daily_move"
            policy_dir.mkdir(parents=True)
            (policy_dir / "policy.py").write_text(
                "def evaluate_daily_move_case(case):\n"
                "    return {'result': 'pass', 'action': 'emit_proposed_move', "
                "'blocked': False, 'finding_codes': []}\n",
                encoding="utf-8",
            )
            report = validate_repo(temp_root)
        self.assertEqual("fail", report["status"])
        findings = report["findings"]
        self.assertTrue(
            any(
                item["code"] == "RUNTIME_EXPECTATION_MISMATCH" and "QDM-A01" in item["message"]
                for item in findings
            )
        )


if __name__ == "__main__":
    unittest.main()
