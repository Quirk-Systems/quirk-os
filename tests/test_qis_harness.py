from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
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
        cls.valid = load("evals/qis-agent-harness/receipt.valid-provenance.json")

    def errors_for(self, relative_path: str) -> list[str]:
        return validate_receipt(load(relative_path), self.schema, repo=ROOT)

    def test_schema_is_valid_draft_2020_12(self) -> None:
        Draft202012Validator.check_schema(self.schema)

    def test_valid_receipt_fixture_passes_and_hash_is_stable(self) -> None:
        self.assertEqual([], self.errors_for("evals/qis-agent-harness/receipt.valid-provenance.json"))
        expected_hash = hashlib.sha256(canonical_receipt_payload(self.valid)).hexdigest()
        self.assertEqual(expected_hash, receipt_hash(self.valid))
        self.assertEqual(expected_hash, self.valid["receipt_hash"])

    NEGATIVE_FIXTURES = {
        "receipt.ancestry-mismatch.json": (
            {("repository", "is_traceable_descendant")},
            ["repository/is_traceable_descendant: True was expected"],
        ),
        "receipt.critical-failure-pass.json": (
            {("critical_failures",)},
            ["critical failures cannot coexist with a PASS verdict"],
        ),
        "receipt.hash-mismatch.json": (
            set(),
            None,
        ),
        "receipt.material-mismatch.json": (
            {("materials", 0, "sha256")},
            ["materials[0]: sha256 mismatch for .github/copilot-instructions.md"],
        ),
        "receipt.missing-evidence.json": (
            {("evidence_refs",)},
            ["evidence_refs[3]: missing file evals/qis-agent-harness/does-not-exist.json"],
        ),
        "receipt.unexpected-field.json": (
            {("cute_dashboard",)},
            ["<root>: Additional properties are not allowed ('cute_dashboard' was unexpected)"],
        ),
        "receipt.unknown-verdict.json": (
            {("verdict",)},
            ["verdict: 'MAYBE' is not one of ['PASS', 'REVISE', 'FAIL']"],
        ),
    }
    IDENTITY_PATHS = {("receipt_id",), ("receipt_hash",)}

    def changed_paths(self, left, right, path=()) -> set[tuple]:
        if isinstance(left, dict) and isinstance(right, dict):
            changed = set()
            for key in left.keys() | right.keys():
                if key not in left or key not in right:
                    changed.add(path + (key,))
                else:
                    changed |= self.changed_paths(left[key], right[key], path + (key,))
            return changed
        if isinstance(left, list) and isinstance(right, list) and len(left) == len(right):
            changed = set()
            for index, (a, b) in enumerate(zip(left, right)):
                changed |= self.changed_paths(a, b, path + (index,))
            return changed
        return set() if left == right else {path}

    def test_fixture_directory_is_exactly_valid_plus_known_negatives(self) -> None:
        self.assertEqual(
            {"receipt.valid-provenance.json", "receipt.valid-pr132-provenance.json", *self.NEGATIVE_FIXTURES},
            {path.name for path in self.fixture_dir.glob("*.json")},
        )

    def test_each_negative_fixture_is_valid_plus_exactly_one_defect(self) -> None:
        for name, (defect_paths, _) in self.NEGATIVE_FIXTURES.items():
            with self.subTest(fixture=name):
                fixture = load(f"evals/qis-agent-harness/{name}")
                self.assertEqual(
                    f"receipt.qis-agent-harness.fixture-{name.removeprefix('receipt.').removesuffix('.json')}",
                    fixture["receipt_id"],
                )
                self.assertEqual(
                    defect_paths,
                    self.changed_paths(self.valid, fixture) - self.IDENTITY_PATHS,
                )
                if name == "receipt.hash-mismatch.json":
                    self.assertNotEqual(receipt_hash(fixture), fixture["receipt_hash"])
                else:
                    self.assertEqual(receipt_hash(fixture), fixture["receipt_hash"])

    def test_negative_fixtures_fail_with_exact_errors(self) -> None:
        for name, (_, expected) in self.NEGATIVE_FIXTURES.items():
            with self.subTest(fixture=name):
                path = f"evals/qis-agent-harness/{name}"
                if expected is None:
                    expected = [f"receipt_hash mismatch: expected {receipt_hash(load(path))}"]
                self.assertEqual(expected, self.errors_for(path))

    def validate_resealed(self, receipt: dict, repo: Path = ROOT) -> list[str]:
        receipt["receipt_hash"] = receipt_hash(receipt)
        return validate_receipt(receipt, self.schema, repo=repo)

    def test_candidate_identity_is_pinned(self) -> None:
        for field, value in (("candidate_branch", "agent/other"), ("candidate_sha", "a" * 40)):
            with self.subTest(field=field):
                receipt = copy.deepcopy(self.valid)
                receipt["repository"][field] = value
                self.assertTrue(any(field in error for error in self.validate_resealed(receipt)))

    def test_self_reported_ancestry_cannot_hide_unrelated_head(self) -> None:
        receipt = copy.deepcopy(self.valid)
        receipt["repository"]["head_sha"] = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", f"{receipt['repository']['candidate_sha']}^"],
            text=True,
        ).strip()
        self.assertTrue(any("traceable descendant" in error for error in self.validate_resealed(receipt)))

    def test_unknown_head_fails_closed(self) -> None:
        receipt = copy.deepcopy(self.valid)
        receipt["repository"]["head_sha"] = "0" * 40
        self.assertTrue(any("ancestry could not be verified" in error for error in self.validate_resealed(receipt)))

    def test_checkout_history_is_required(self) -> None:
        self.assertTrue(validate_receipt(self.valid, self.schema))
        with tempfile.TemporaryDirectory() as directory:
            errors = validate_receipt(self.valid, self.schema, repo=Path(directory))
            self.assertTrue(any("ancestry could not be verified" in error for error in errors))

    def test_material_mutation_invalidates_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            material = self.valid["materials"][0]
            target = repo / material["path"]
            target.parent.mkdir(parents=True)
            target.write_text("changed material", encoding="utf-8")
            errors = validate_receipt(self.valid, self.schema, repo=repo)
            self.assertTrue(any("materials[0]: sha256 mismatch" in error for error in errors))

    def test_absolute_traversal_and_symlink_paths_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            repo = parent / "repo"
            repo.mkdir()
            outside = parent / "outside.json"
            outside.write_text("{}", encoding="utf-8")
            (repo / "escape.json").symlink_to(outside)
            for path in (str(outside), "../outside.json", "escape.json"):
                for field in ("materials", "evidence_refs"):
                    with self.subTest(path=path, field=field):
                        receipt = copy.deepcopy(self.valid)
                        if field == "materials":
                            receipt[field][0]["path"] = path
                            receipt[field][0]["sha256"] = hashlib.sha256(outside.read_bytes()).hexdigest()
                        else:
                            receipt[field][0] = path
                        errors = self.validate_resealed(receipt, repo=repo)
                        self.assertTrue(any(
                            f"{field}[0]: path must" in error for error in errors
                        ))

    def test_repository_relative_paths_pass(self) -> None:
        receipt = copy.deepcopy(self.valid)
        for material in receipt["materials"]:
            material["path"] = "./" + material["path"]
        receipt["evidence_refs"] = ["./" + path for path in receipt["evidence_refs"]]
        self.assertEqual([], self.validate_resealed(receipt))

    def test_malformed_paths_are_schema_errors(self) -> None:
        for field in ("materials", "evidence_refs"):
            receipt = copy.deepcopy(self.valid)
            if field == "materials":
                receipt[field][0]["path"] = []
            else:
                receipt[field][0] = []
            self.assertTrue(self.validate_resealed(receipt))

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

    def test_workflows_running_repository_tests_fetch_ancestry(self) -> None:
        tested_jobs = 0
        for path in (ROOT / ".github/workflows").glob("*.yml"):
            workflow = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
            for name, job in workflow.get("jobs", {}).items():
                steps = job.get("steps", [])
                if not any(
                    "unittest discover" in step.get("run", "")
                    and "'test_*.py'" in step.get("run", "")
                    for step in steps
                ):
                    continue
                with self.subTest(workflow=path.name, job=name):
                    checkout = next(
                        step for step in steps
                        if step.get("uses", "").startswith("actions/checkout@")
                    )
                    self.assertEqual("0", checkout.get("with", {}).get("fetch-depth"))
                    tested_jobs += 1
        self.assertGreaterEqual(tested_jobs, 3)

    def test_workflow_receipt_records_exact_test_counts(self) -> None:
        workflow = yaml.load(
            (ROOT / ".github/workflows/qis-agent-harness.yml").read_text(encoding="utf-8"),
            Loader=yaml.BaseLoader,
        )
        build = next(
            step for step in workflow["jobs"]["harness"]["steps"]
            if step["name"] == "Build harness receipt"
        )
        git_dir = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "--absolute-git-dir"], text=True,
        ).strip()
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            for path in set(re.findall(r'"path": "([^"]+)"', build["run"])):
                target = repo / path
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / path, target)
            (repo / "evals/intent-shaper/conformance-results.json").write_text(
                json.dumps({"status": "passed", "fixtures_total": 25, "fixtures_passed": 25}),
                encoding="utf-8",
            )
            log = repo / "tests.log"
            receipt_path = repo / "receipt.json"
            env = dict(
                os.environ,
                GIT_DIR=git_dir,
                CANDIDATE_BRANCH=self.valid["repository"]["candidate_branch"],
                CANDIDATE_SHA=self.valid["repository"]["candidate_sha"],
                BASE_SHA=self.valid["repository"]["base_sha"],
                HEAD_SHA=self.valid["repository"]["head_sha"],
                TEST_LOG=str(log),
                RECEIPT_PATH=str(receipt_path),
                RUNNER_OS="Linux",
            )
            for summary, failed in (("OK", 0), ("FAILED (failures=2, errors=1)", 3)):
                with self.subTest(summary=summary):
                    log.write_text(f"Ran 45 tests in 0.2s\n\n{summary}\n", encoding="utf-8")
                    subprocess.run(
                        ["bash", "-e"], input=build["run"], text=True,
                        cwd=repo, env=env, check=True, capture_output=True,
                    )
                    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                    self.assertEqual(
                        {"passed": 45 - failed, "failed": failed, "total": 45},
                        receipt["commands"][0]["counts"],
                    )
                    self.assertEqual("PASS" if failed == 0 else "REVISE", receipt["verdict"])
                    self.assertEqual(receipt_hash(receipt), receipt["receipt_hash"])
                    subprocess.run(
                        ["python", str(ROOT / "scripts/validate_qis_harness.py"),
                         "--repo", str(repo), "--receipt", str(receipt_path)],
                        env=env, check=True, capture_output=True,
                    )

    def test_workflow_is_pull_request_only_and_uploads_expected_artifact(self) -> None:
        workflow_path = ROOT / ".github/workflows/qis-agent-harness.yml"
        workflow_text = workflow_path.read_text(encoding="utf-8")
        workflow = yaml.load(workflow_text, Loader=yaml.BaseLoader)

        self.assertEqual({"pull_request"}, set(workflow["on"].keys()))
        self.assertEqual("read", workflow["permissions"]["contents"])
        self.assertIn("schemas/qis-evidence-envelope.schema.json", workflow_text)
        self.assertIn("tests/test_qis_harness.py", workflow_text)
        head_ref = "${{ github.event.pull_request.head.sha }}"
        steps = workflow["jobs"]["harness"]["steps"]
        checkout = next(step for step in steps if step["name"] == "Checkout")
        build = next(step for step in steps if step["name"] == "Build harness receipt")
        self.assertEqual(head_ref, checkout["with"]["ref"])
        self.assertEqual("0", checkout["with"]["fetch-depth"])
        self.assertEqual(head_ref, build["env"]["HEAD_SHA"])
        self.assertIn(f"name: qis-agent-harness-{head_ref}", workflow_text)
        self.assertIn(f"RECEIPT_PATH: evals/qis-agent-harness/qis-agent-harness-{head_ref}.json", workflow_text)
        self.assertNotIn("github.sha", workflow_text)
        self.assertIn("if-no-files-found: error", workflow_text)
        self.assertIn("retention-days: 30", workflow_text)
        self.assertIn("if: always()", workflow_text)
        self.assertIn('run: test -f "$RECEIPT_PATH"', workflow_text)
        self.assertNotIn("pull_request_target", workflow_text)
        self.assertNotIn("workflow_dispatch", workflow_text)
        self.assertNotIn("schedule:", workflow_text)


if __name__ == "__main__":
    unittest.main()
