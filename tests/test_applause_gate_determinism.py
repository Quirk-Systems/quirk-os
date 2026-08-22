from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = "scripts/validate_applause_gate.py"
FIXTURE_PATH = "evals/applause-gate/cases.json"
SCHEMA_PATH = "schemas/applause-review.schema.json"
PACKAGE_INIT_PATH = "scripts/applause_gate/__init__.py"
CLASSIFIER_PATH = "scripts/applause_gate/classifier.py"
RECEIPT_HELPER_PATH = "scripts/applause_gate/receipt.py"

SOURCE_PATHS = (
    FIXTURE_PATH,
    SCHEMA_PATH,
    PACKAGE_INIT_PATH,
    CLASSIFIER_PATH,
    RECEIPT_HELPER_PATH,
    VALIDATOR_PATH,
)

SOURCE_ALIASES = {
    FIXTURE_PATH: "fixture_digest",
    SCHEMA_PATH: "schema_digest",
    PACKAGE_INIT_PATH: "package_init_digest",
    CLASSIFIER_PATH: "classifier_digest",
    RECEIPT_HELPER_PATH: "receipt_helper_digest",
    VALIDATOR_PATH: "validator_digest",
}

CASE_IDS = [
    "ABG-P01", "ABG-P02", "ABG-P03", "ABG-P04", "ABG-P05",
    "ABG-N01", "ABG-N02", "ABG-N03",
    "ABG-A01", "ABG-A02", "ABG-A03", "ABG-A04", "ABG-A05",
    "ABG-A06", "ABG-A07", "ABG-A08", "ABG-A09", "ABG-A10", "ABG-A11",
]

RESULT_FIELDS = {
    "case_id", "kind", "request_digest", "expected_verdict", "actual_verdict",
    "actual_required_codes", "schema_errors", "fabricated_refs", "suppressed_refs",
    "missing_required_codes", "unexpected_codes", "authority_smuggling_reasons",
    "behavior_violations", "input_error", "review_evidence_refs",
    "review_withheld_claims", "review_missing_proof", "review_warnings", "passed",
}

FAILURE_COUNTERS = [
    "verdict_mismatch_count", "false_verified_success_count",
    "fabricated_evidence_count", "suppressed_evidence_count",
    "authority_smuggling_count", "schema_error_count", "behavior_violation_count",
    "input_error_count", "missing_required_code_count", "unexpected_code_count",
    "failed_case_count", "corpus_integrity_count", "summary_integrity_count",
]

REPORT_FIELDS = {
    "report_schema_version", "candidate_id", "candidate_version",
    "authority_effect", "candidate_evidence_only", "corpus_seal", "total_cases",
    "case_counts", "passed_count", "results", "corpus_errors", "summary_errors",
    "failure_reasons", "count_semantics", "failure_counters", *FAILURE_COUNTERS,
    "verdict", "source_hashes", "fixture_payload_sha256", "fixture_digest",
    "schema_digest", "package_init_digest", "classifier_digest",
    "receipt_helper_digest", "validator_digest", "source_origin_errors",
    "receipt_hash",
}


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@contextmanager
def copied_repo() -> Iterator[Path]:
    """Yield a minimal isolated repo copy; mutations never touch the worktree."""

    with tempfile.TemporaryDirectory() as temporary:
        repo = Path(temporary) / "repo"
        repo.mkdir()
        for directory in ("evals", "schemas", "scripts"):
            shutil.copytree(
                ROOT / directory,
                repo / directory,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
        yield repo


class ApplauseGateDeterminismTests(unittest.TestCase):
    def run_validator(
        self, repo: Path = ROOT, *, require_pass: bool = True
    ) -> subprocess.CompletedProcess[bytes]:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo / "scripts")
        command = [
            sys.executable,
            str(repo / VALIDATOR_PATH),
            "--repo",
            str(repo),
        ]
        if require_pass:
            command.append("--require-pass")
        return subprocess.run(
            command,
            cwd=repo,
            check=False,
            capture_output=True,
            env=env,
        )

    def passing_report(self, repo: Path = ROOT) -> tuple[bytes, dict]:
        result = self.run_validator(repo)
        self.assertEqual(
            result.returncode,
            0,
            (result.stderr or result.stdout).decode("utf-8", errors="replace"),
        )
        return result.stdout, json.loads(result.stdout)

    def test_canonical_hash_helpers_are_sorted_compact_utf8(self):
        from applause_gate.receipt import (
            canonical_json,
            sha256_json,
            sha256_json_without_keys,
        )

        value = {"z": "café", "a": [2, 1]}
        expected = '{"a":[2,1],"z":"café"}'
        self.assertEqual(canonical_json(value), expected)
        self.assertEqual(
            sha256_json(value), hashlib.sha256(expected.encode("utf-8")).hexdigest()
        )
        self.assertEqual(
            sha256_json_without_keys(
                {"keep": value, "receipt_hash": "ignored"},
                omitted_keys={"receipt_hash"},
            ),
            sha256_json({"keep": value}),
        )

    def test_two_untouched_cold_processes_are_byte_identical(self):
        first_bytes, first = self.passing_report()
        second_bytes, second = self.passing_report()

        self.assertEqual(first_bytes, second_bytes)
        self.assertEqual(first["receipt_hash"], second["receipt_hash"])
        self.assertTrue(first_bytes.endswith(b"\n"))

    def test_receipt_hash_omits_exactly_itself(self):
        from applause_gate.receipt import sha256_json_without_keys

        _, report = self.passing_report()
        self.assertEqual(
            report["receipt_hash"],
            sha256_json_without_keys(report, omitted_keys={"receipt_hash"}),
        )

        changed = dict(report)
        changed["candidate_evidence_only"] = False
        self.assertNotEqual(
            report["receipt_hash"],
            sha256_json_without_keys(changed, omitted_keys={"receipt_hash"}),
        )
        self.assertNotEqual(
            report["receipt_hash"],
            sha256_json_without_keys(
                report,
                omitted_keys={"receipt_hash", "validator_digest"},
            ),
        )

    def test_report_binds_complete_results_counters_and_sources(self):
        rendered, report = self.passing_report()

        self.assertEqual(set(report), REPORT_FIELDS)
        self.assertEqual(report["verdict"], "PASS")
        self.assertEqual(report["authority_effect"], "none")
        self.assertTrue(report["candidate_evidence_only"])
        self.assertEqual(report["source_origin_errors"], [])
        self.assertEqual(report["total_cases"], 19)
        self.assertEqual(report["passed_count"], 19)
        self.assertEqual(
            report["case_counts"],
            {"positive": 5, "negative": 3, "adversarial": 11},
        )
        self.assertEqual([result["case_id"] for result in report["results"]], CASE_IDS)
        self.assertEqual(len(report["results"]), 19)
        for result in report["results"]:
            with self.subTest(case_id=result["case_id"]):
                self.assertEqual(set(result), RESULT_FIELDS)
                self.assertTrue(result["passed"])

        self.assertEqual(report["failure_counters"], FAILURE_COUNTERS)
        for counter in FAILURE_COUNTERS:
            self.assertEqual(report[counter], 0, counter)

        expected_source_hashes = {
            relative: raw_sha256(ROOT / relative) for relative in SOURCE_PATHS
        }
        self.assertEqual(report["source_hashes"], expected_source_hashes)
        for relative, alias in SOURCE_ALIASES.items():
            self.assertEqual(report[alias], expected_source_hashes[relative])

        fixture = json.loads((ROOT / FIXTURE_PATH).read_bytes())
        self.assertEqual(
            report["fixture_payload_sha256"],
            hashlib.sha256(canonical_json_bytes(fixture)).hexdigest(),
        )
        self.assertEqual(
            report["fixture_payload_sha256"],
            report["corpus_seal"]["actual_canonical_sha256"],
        )
        self.assertEqual(
            report["fixture_digest"], report["corpus_seal"]["actual_raw_sha256"]
        )
        self.assertEqual(len(report["receipt_hash"]), 64)
        self.assertNotIn(str(ROOT).encode("utf-8"), rendered)

    def test_semantic_fixture_mutation_changes_payload_and_fails_closed(self):
        _, baseline = self.passing_report()

        with copied_repo() as repo:
            fixture_path = repo / FIXTURE_PATH
            fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
            fixture["cases"][0]["claim"] += " Semantic mutation."
            fixture_path.write_text(
                json.dumps(fixture, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )

            result = self.run_validator(repo)
            self.assertEqual(result.returncode, 1, result.stderr.decode("utf-8"))
            report = json.loads(result.stdout)

        self.assertEqual(report["verdict"], "FAIL")
        self.assertNotEqual(report["fixture_digest"], baseline["fixture_digest"])
        self.assertNotEqual(
            report["fixture_payload_sha256"], baseline["fixture_payload_sha256"]
        )
        self.assertEqual(
            report["fixture_digest"], report["source_hashes"][FIXTURE_PATH]
        )
        self.assertNotEqual(report["receipt_hash"], baseline["receipt_hash"])
        self.assertGreater(report["corpus_integrity_count"], 0)

    def test_benign_schema_comment_changes_only_its_source_binding_and_passes(self):
        _, baseline = self.passing_report()

        with copied_repo() as repo:
            schema_path = repo / SCHEMA_PATH
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            schema["$comment"] = "Receipt mutation test; validation semantics unchanged."
            schema_path.write_text(
                json.dumps(schema, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            _, report = self.passing_report(repo)

        self.assertEqual(report["verdict"], "PASS")
        self.assertNotEqual(report["schema_digest"], baseline["schema_digest"])
        self.assertEqual(report["schema_digest"], report["source_hashes"][SCHEMA_PATH])
        self.assertNotEqual(report["receipt_hash"], baseline["receipt_hash"])
        for relative in SOURCE_PATHS:
            if relative != SCHEMA_PATH:
                self.assertEqual(
                    report["source_hashes"][relative],
                    baseline["source_hashes"][relative],
                    relative,
                )

    def test_comment_only_source_mutations_each_change_their_binding(self):
        _, baseline = self.passing_report()
        mutation_targets = (
            PACKAGE_INIT_PATH,
            CLASSIFIER_PATH,
            RECEIPT_HELPER_PATH,
            VALIDATOR_PATH,
        )

        for relative in mutation_targets:
            with self.subTest(source=relative), copied_repo() as repo:
                source = repo / relative
                source.write_text(
                    source.read_text(encoding="utf-8")
                    + "\n# Receipt-binding comment mutation.\n",
                    encoding="utf-8",
                )
                _, report = self.passing_report(repo)

                alias = SOURCE_ALIASES[relative]
                self.assertEqual(report["verdict"], "PASS")
                self.assertNotEqual(report[alias], baseline[alias])
                self.assertEqual(report[alias], report["source_hashes"][relative])
                self.assertNotEqual(report["receipt_hash"], baseline["receipt_hash"])
                for other in SOURCE_PATHS:
                    if other != relative:
                        self.assertEqual(
                            report["source_hashes"][other],
                            baseline["source_hashes"][other],
                            other,
                        )

    def test_foreign_executor_cannot_attest_poisoned_copied_sources(self):
        _, baseline = self.passing_report()

        with copied_repo() as repo:
            poisoned_sources = (
                CLASSIFIER_PATH,
                RECEIPT_HELPER_PATH,
                VALIDATOR_PATH,
            )
            for relative in poisoned_sources:
                source = repo / relative
                source.write_text(
                    source.read_text(encoding="utf-8")
                    + "\n# Poisoned copy must never be attested by a foreign executor.\n",
                    encoding="utf-8",
                )

            env = os.environ.copy()
            env["PYTHONPATH"] = str(ROOT / "scripts")
            command = [
                sys.executable,
                str(ROOT / VALIDATOR_PATH),
                "--repo",
                str(repo),
                "--require-pass",
            ]
            first = subprocess.run(
                command,
                cwd=ROOT,
                check=False,
                capture_output=True,
                env=env,
            )
            second = subprocess.run(
                command,
                cwd=ROOT,
                check=False,
                capture_output=True,
                env=env,
            )

        self.assertEqual(first.returncode, 1, first.stderr.decode("utf-8"))
        self.assertEqual(second.returncode, 1, second.stderr.decode("utf-8"))
        self.assertEqual(first.stdout, second.stdout)
        report = json.loads(first.stdout)
        self.assertEqual(report["verdict"], "FAIL")
        self.assertEqual(
            report["source_origin_errors"],
            [
                f"{VALIDATOR_PATH}: executing source origin does not match requested repo",
                f"{PACKAGE_INIT_PATH}: executing source origin does not match requested repo",
                f"{CLASSIFIER_PATH}: executing source origin does not match requested repo",
                f"{RECEIPT_HELPER_PATH}: executing source origin does not match requested repo",
            ],
        )
        self.assertGreater(report["corpus_integrity_count"], 0)
        self.assertNotEqual(report["receipt_hash"], baseline["receipt_hash"])
        for relative in poisoned_sources:
            self.assertNotEqual(
                report["source_hashes"][relative],
                baseline["source_hashes"][relative],
                relative,
            )
        self.assertNotIn(str(ROOT).encode("utf-8"), first.stdout)
        self.assertNotIn(str(repo).encode("utf-8"), first.stdout)


if __name__ == "__main__":
    unittest.main()
