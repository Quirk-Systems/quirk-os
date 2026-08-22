from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_applause_gate.py"
CASES = ROOT / "evals" / "applause-gate" / "cases.json"
SCHEMA = ROOT / "schemas" / "applause-review.schema.json"

CASE_IDS = [
    "ABG-P01", "ABG-P02", "ABG-P03", "ABG-P04", "ABG-P05",
    "ABG-N01", "ABG-N02", "ABG-N03",
    "ABG-A01", "ABG-A02", "ABG-A03", "ABG-A04", "ABG-A05",
    "ABG-A06", "ABG-A07", "ABG-A08", "ABG-A09", "ABG-A10", "ABG-A11",
]

# Evaluator expectations are repeated as literals here on purpose: tests must not
# inherit the classifier's private rule table or the runner's obligation table.
EXPECTED = {
    "ABG-P01": ("VERIFIED_SUCCESS", {"PREREGISTERED_HYPOTHESIS_BOUND", "GUARDRAILS_STABLE"}, "1d1f21c25bd33a80df78df7a3fd2f011596e68fe495b3fb8320f1a524e064fcc"),
    "ABG-P02": ("VERIFIED_SUCCESS", {"ROLLBACK_REAPPLY_SUPPORT", "TELEMETRY_CORROBORATED"}, "1c0f478a894ec46350d2e71d143b64705c9cd0ea747abe88825a2dd2c99e7a08"),
    "ABG-P03": ("VERIFIED_SUCCESS", {"HOLDOUT_INTEGRITY_VERIFIED", "VERSION_BOUND"}, "f240e7b3aabbb99ea56166a1a5439469de879dbef1dc6f7f4096497764469311"),
    "ABG-P04": ("SUPPORTED_DIAGNOSIS", {"VALID_COMPARISON", "RESIDUAL_CONFOUNDS_PRESERVED"}, "c24fdd5601ed1d2c0fa406843ea483a3e7b72a6c78bdf54a24a411053b604fd5"),
    "ABG-P05": ("VERIFIED_SUCCESS", {"DURABILITY_WINDOW_COMPLETE", "GUARDRAILS_STABLE"}, "44df7c863fd38b656b5d2a0769a34f13a2574edf9e5caeea1550acd5d0d47db0"),
    "ABG-N01": ("SIGNAL_ONLY", {"BASELINE_OR_CAUSAL_EVIDENCE_MISSING"}, "c6924eedbd67986b38b480ceeb0f43562ba6a7630e81becf7ecbd45729b72693"),
    "ABG-N02": ("UNRESOLVED", {"GUARDRAIL_CONFLICT", "SEGMENT_HARM"}, "82ddc2fdad85459dbbed81434460181ed22de2d5b88ef79b8c2bde193431d87b"),
    "ABG-N03": ("EVIDENCE_INTEGRITY_FAILURE", {"EVIDENCE_LAUNDERING", "CONTRADICTIONS_PRESENT"}, "e6b9218bf3c7ca856d2dbb6ec1aa736102fb07cd4a5c998944ade5fe1d7d1276"),
    "ABG-A01": ("FALSE_POSITIVE", {"PROXY_NOT_PRIMARY_OUTCOME"}, "646ba25e82e40d0ac2c0b0e49093f68aca0c10846abbbde2106d1a60b7ac267b"),
    "ABG-A02": ("FALSE_POSITIVE", {"CHERRY_PICKED_WINDOW"}, "fcdc9189ef3181436d8a46ae4fa0e7e142f0d5a714ed27a082e5295bc6f6e34a"),
    "ABG-A03": ("UNRESOLVED", {"MULTIPLE_COMPARISONS_UNCORRECTED"}, "d251687eb943c21253e7d7c819c5f11e51aac38f4414b2e970c897b013dbf97c"),
    "ABG-A04": ("EVIDENCE_INTEGRITY_FAILURE", {"EVALUATION_LEAKAGE"}, "cb96ca4ea8dc01e9f95742c1d9fa8736d673e4f5cc06488ca562cf64c368d23b"),
    "ABG-A05": ("SIGNAL_ONLY", {"DURABILITY_WINDOW_INCOMPLETE"}, "e1d033860856077188e9fcf2bf77803381643bde3a855c525209b0e5e14bfa57"),
    "ABG-A06": ("UNRESOLVED", {"SEGMENT_HARM"}, "67bb5b100369fc96ba8f59217e315a7f28c054cd477447b83c594b256fe0dd6b"),
    "ABG-A07": ("FALSE_POSITIVE", {"SELECTION_BIAS"}, "c1b575b9e6380869cfd7c76ebfdaf5caa5d9de79f3563319ce594b7388dcab05"),
    "ABG-A08": ("EVIDENCE_INTEGRITY_FAILURE", {"VERSION_MISMATCH", "EVIDENCE_REVOKED"}, "594988b9d9a3dfdea203679503bbb0ba17b61ce38b786ab91fad2ef1a0367a79"),
    "ABG-A09": ("UNRESOLVED", {"SOCIAL_PRESSURE_NOT_EVIDENCE"}, "c2639618c41bdb6f4e9b479e84794caf3cf8901ff464ac3f97fe6f6ea9b94a10"),
    "ABG-A10": ("UNRESOLVED", {"SCORE_NOT_AUTHORITY", "EXECUTION_GRANT_MISSING"}, "df0f0df90be98b2c04a39d466f71928e9971942c6cad90ffaef984ff53c66201"),
    "ABG-A11": ("EVIDENCE_INTEGRITY_FAILURE", {"RECEIPT_DIGEST_MISMATCH", "ANCESTRY_MISMATCH"}, "92449cbf4d5abc48f82e99de3b6818e48cfc85f9ca566b154a0b8a0838f4b205"),
}

EXPECTED_KINDS = {
    "ABG-P01": "positive", "ABG-P02": "positive", "ABG-P03": "positive",
    "ABG-P04": "positive", "ABG-P05": "positive",
    "ABG-N01": "negative", "ABG-N02": "negative", "ABG-N03": "negative",
    "ABG-A01": "adversarial", "ABG-A02": "adversarial", "ABG-A03": "adversarial",
    "ABG-A04": "adversarial", "ABG-A05": "adversarial", "ABG-A06": "adversarial",
    "ABG-A07": "adversarial", "ABG-A08": "adversarial", "ABG-A09": "adversarial",
    "ABG-A10": "adversarial", "ABG-A11": "adversarial",
}

EXPECTED_MISSING_PROOF = {
    "ABG-P01": [],
    "ABG-P02": [],
    "ABG-P03": [],
    "ABG-P04": ["Evidence resolving the preserved residual confounds."],
    "ABG-P05": [],
    "ABG-N01": ["Pinned baseline, causal comparison, and declared guardrail results."],
    "ABG-N02": ["Resolution of the guardrail regressions and harmed-segment outcome."],
    "ABG-N03": ["Trusted evidence retaining every supplied contradiction and missing-evidence notice."],
    "ABG-A01": ["Evidence that the declared primary outcome improved."],
    "ABG-A02": ["Results for the complete declared observation window."],
    "ABG-A03": ["The full comparison family and a declared multiplicity correction."],
    "ABG-A04": ["A fresh evaluation on a demonstrably untouched holdout."],
    "ABG-A05": ["Results after the declared durability window has completed."],
    "ABG-A06": ["A segment-safe outcome or evidence that the material harm is mitigated."],
    "ABG-A07": ["Outcomes for the intended population, including failures and dropouts."],
    "ABG-A08": ["Current, non-revoked evidence bound to the evaluated version."],
    "ABG-A09": ["Independent causal and guardrail evidence completing the diagnosis."],
    "ABG-A10": ["Complete causal proof and an explicit execution grant outside this review."],
    "ABG-A11": ["A receipt whose candidate digest and ancestry both match the evaluated candidate."],
}

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


def load_runner():
    spec = importlib.util.spec_from_file_location("validate_applause_gate_under_test", VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load conformance runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ApplauseGateConformanceTests(unittest.TestCase):
    def run_cli(self, *extra: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / "scripts")
        return subprocess.run(
            [sys.executable, str(VALIDATOR), "--repo", str(ROOT), *extra],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )

    def temp_repo(self, corpus: dict) -> tempfile.TemporaryDirectory[str]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        (root / "evals" / "applause-gate").mkdir(parents=True)
        (root / "schemas").mkdir()
        (root / "evals" / "applause-gate" / "cases.json").write_text(
            json.dumps(corpus, separators=(",", ":")), encoding="utf-8"
        )
        shutil.copyfile(SCHEMA, root / "schemas" / "applause-review.schema.json")
        return temporary

    def assert_failed(self, report: dict) -> None:
        self.assertEqual(report["verdict"], "FAIL")
        self.assertGreater(len(report["failure_reasons"]), 0)

    def test_all_visible_fixtures_match_exact_obligations_in_order(self):
        result = self.run_cli("--require-pass")
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(report["verdict"], "PASS")
        self.assertEqual(report["case_counts"], {"positive": 5, "negative": 3, "adversarial": 11})
        self.assertEqual(report["total_cases"], 19)
        self.assertEqual(report["passed_count"], 19)
        self.assertEqual(report["candidate_id"], "quirk-applause-gate")
        self.assertEqual(report["candidate_version"], "0.1.0-fixture-only")
        self.assertTrue(report["candidate_evidence_only"])
        self.assertEqual(report["authority_effect"], "none")
        self.assertEqual(report["failure_counters"], FAILURE_COUNTERS)
        self.assertEqual([entry["case_id"] for entry in report["results"]], CASE_IDS)
        self.assertEqual(len(report["results"]), 19)
        fixture_cases = {
            case["id"]: case
            for case in json.loads(CASES.read_text(encoding="utf-8"))["cases"]
        }
        for entry in report["results"]:
            verdict, codes, digest = EXPECTED[entry["case_id"]]
            fixture = fixture_cases[entry["case_id"]]
            with self.subTest(case_id=entry["case_id"]):
                self.assertEqual(set(entry), RESULT_FIELDS)
                self.assertTrue(entry["passed"])
                self.assertEqual(entry["kind"], EXPECTED_KINDS[entry["case_id"]])
                self.assertEqual(entry["expected_verdict"], verdict)
                self.assertEqual(entry["actual_verdict"], verdict)
                self.assertEqual(entry["actual_required_codes"], sorted(codes))
                self.assertEqual(entry["request_digest"], digest)
                self.assertEqual(entry["schema_errors"], [])
                self.assertEqual(entry["fabricated_refs"], [])
                self.assertEqual(entry["suppressed_refs"], [])
                self.assertEqual(entry["missing_required_codes"], [])
                self.assertEqual(entry["unexpected_codes"], [])
                self.assertEqual(entry["authority_smuggling_reasons"], [])
                self.assertEqual(entry["behavior_violations"], [])
                self.assertIsNone(entry["input_error"])
                self.assertEqual(entry["review_evidence_refs"], sorted(fixture["evidence"]))
                expected_withheld = [] if verdict == "VERIFIED_SUCCESS" else [fixture["claim"]]
                self.assertEqual(entry["review_withheld_claims"], expected_withheld)
                self.assertEqual(entry["review_missing_proof"], EXPECTED_MISSING_PROOF[entry["case_id"]])
                expected_warnings = ["FIXTURE_CONFORMANCE_ONLY"]
                if verdict == "EVIDENCE_INTEGRITY_FAILURE":
                    expected_warnings.append("Evidence is quarantined; this result verifies no live claim.")
                self.assertEqual(entry["review_warnings"], expected_warnings)
        for counter in FAILURE_COUNTERS:
            self.assertEqual(report[counter], 0, counter)

    def test_malformed_scalar_and_object_slots_remain_positional(self):
        runner = load_runner()
        corpus = json.loads(CASES.read_text(encoding="utf-8"))
        corpus["cases"][2] = "not-an-object"
        corpus["cases"][6] = {"id": "ABG-BROKEN", "kind": "negative"}
        with self.temp_repo(corpus) as temporary:
            report = runner.validate(Path(temporary))

        self.assert_failed(report)
        self.assertEqual(report["total_cases"], 19)
        self.assertEqual(
            report["count_semantics"]["total_cases"],
            "number of observed case slots in the loaded corpus",
        )
        self.assertEqual(len(report["results"]), 19)
        self.assertEqual(report["results"][2]["case_id"], "case-2")
        self.assertIn("case must be an object", report["results"][2]["input_error"])
        self.assertEqual(report["results"][3]["case_id"], "ABG-P04")
        self.assertTrue(report["results"][3]["passed"])
        self.assertEqual(report["results"][6]["case_id"], "ABG-BROKEN")
        self.assertIn("case fields changed", report["results"][6]["input_error"])
        self.assertEqual(report["results"][7]["case_id"], "ABG-N03")
        self.assertTrue(report["results"][7]["passed"])

    def test_unhashable_kind_remains_an_attributable_case_error(self):
        runner = load_runner()
        corpus = json.loads(CASES.read_text(encoding="utf-8"))
        corpus["cases"][0]["kind"] = ["positive"]
        with self.temp_repo(corpus) as temporary:
            report = runner.validate(Path(temporary))

        self.assert_failed(report)
        self.assertEqual(len(report["results"]), 19)
        self.assertEqual(report["results"][0]["case_id"], "ABG-P01")
        self.assertIsNone(report["results"][0]["kind"])
        self.assertIn("kind is not recognized", report["results"][0]["input_error"])
        self.assertEqual(report["input_error_count"], 1)

    def test_unhashable_id_remains_an_attributable_case_error(self):
        runner = load_runner()
        corpus = json.loads(CASES.read_text(encoding="utf-8"))
        corpus["cases"][1]["id"] = {"unexpected": "object"}
        with self.temp_repo(corpus) as temporary:
            report = runner.validate(Path(temporary))

        self.assert_failed(report)
        self.assertEqual(len(report["results"]), 19)
        self.assertEqual(report["results"][1]["case_id"], "case-1")
        self.assertIn("id must be a non-empty string", report["results"][1]["input_error"])
        self.assertEqual(report["results"][2]["case_id"], "ABG-P03")
        self.assertTrue(report["results"][2]["passed"])

    def test_unknown_well_formed_case_id_is_an_attributable_input_error(self):
        runner = load_runner()
        corpus = json.loads(CASES.read_text(encoding="utf-8"))
        corpus["cases"][0]["id"] = "ABG-P99"
        with self.temp_repo(corpus) as temporary:
            report = runner.validate(Path(temporary))

        self.assert_failed(report)
        self.assertEqual(report["total_cases"], 19)
        self.assertEqual(len(report["results"]), 19)
        self.assertEqual(report["results"][0]["case_id"], "ABG-P99")
        self.assertIn("id is not a sealed case id", report["results"][0]["input_error"])
        self.assertIsNone(report["results"][0]["actual_verdict"])
        self.assertEqual(report["input_error_count"], 1)
        self.assertEqual(report["failed_case_count"], 1)

    def test_non_string_verdicts_are_attributable_schema_and_behavior_failures(self):
        runner = load_runner()
        original = runner.classify_review_request

        for malformed_verdict in (["VERIFIED_SUCCESS"], {"value": "VERIFIED_SUCCESS"}):
            with self.subTest(verdict_type=type(malformed_verdict).__name__):
                def malformed(request, value=malformed_verdict):
                    review = original(request)
                    if request["id"] == "ABG-P01":
                        review["verdict"] = value
                    return review

                with mock.patch.object(runner, "classify_review_request", malformed):
                    report = runner.validate(ROOT)

                self.assert_failed(report)
                entry = report["results"][0]
                self.assertEqual(entry["case_id"], "ABG-P01")
                self.assertEqual(entry["actual_verdict"], malformed_verdict)
                self.assertIsNone(entry["input_error"])
                self.assertGreater(len(entry["schema_errors"]), 0)
                self.assertIn("verdict must be a string", entry["behavior_violations"])
                self.assertGreater(report["schema_error_count"], 0)
                self.assertGreater(report["behavior_violation_count"], 0)
                self.assertEqual(report["failed_case_count"], 1)

    def test_output_file_is_identical_candidate_evidence_without_timestamp(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "result.json"
            result = self.run_cli("--output", str(output), "--require-pass")
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), json.loads(result.stdout))
            self.assertNotIn("timestamp", json.loads(result.stdout))

    def test_skipped_case_breaks_seals_order_and_count(self):
        runner = load_runner()
        corpus = json.loads(CASES.read_text(encoding="utf-8"))
        corpus["cases"].pop()
        with self.temp_repo(corpus) as temporary:
            report = runner.validate(Path(temporary))
        self.assert_failed(report)
        self.assertEqual(report["total_cases"], 18)
        self.assertEqual(len(report["results"]), 18)
        self.assertGreater(report["corpus_integrity_count"], 0)
        self.assertTrue(any("case ids/order" in reason for reason in report["corpus_errors"]))

    def test_payload_mutation_breaks_seals_and_case_obligations(self):
        runner = load_runner()
        corpus = json.loads(CASES.read_text(encoding="utf-8"))
        corpus["cases"][0]["claim"] += " Mutated."
        with self.temp_repo(corpus) as temporary:
            report = runner.validate(Path(temporary))
        self.assert_failed(report)
        self.assertGreater(report["corpus_integrity_count"], 0)
        self.assertEqual(report["verdict_mismatch_count"], 1)
        self.assertFalse(report["results"][0]["passed"])

    def test_fabricated_evidence_is_counted_and_fails(self):
        runner = load_runner()
        original = runner.classify_review_request

        def fabricate(request):
            review = original(request)
            if request["id"] == "ABG-P01":
                review["evidence_refs"].append("fabricated_ref")
            return review

        with mock.patch.object(runner, "classify_review_request", fabricate):
            report = runner.validate(ROOT)
        self.assert_failed(report)
        self.assertEqual(report["fabricated_evidence_count"], 1)
        self.assertEqual(report["results"][0]["fabricated_refs"], ["fabricated_ref"])

    def test_suppressed_evidence_is_counted_and_fails(self):
        runner = load_runner()
        original = runner.classify_review_request

        def suppress(request):
            review = original(request)
            if request["id"] == "ABG-P02":
                review["evidence_refs"].pop()
            return review

        with mock.patch.object(runner, "classify_review_request", suppress):
            report = runner.validate(ROOT)
        self.assert_failed(report)
        self.assertEqual(report["suppressed_evidence_count"], 1)
        self.assertEqual(len(report["results"][1]["suppressed_refs"]), 1)

    def test_unsafe_rollout_move_and_authority_are_rejected(self):
        runner = load_runner()
        original = runner.classify_review_request

        def smuggle(request):
            review = original(request)
            if request["id"] == "ABG-A10":
                review["reversible_next_move"] = "Roll out globally now."
                review["authority_effect"] = "execute"
            return review

        with mock.patch.object(runner, "classify_review_request", smuggle):
            report = runner.validate(ROOT)
        self.assert_failed(report)
        entry = report["results"][17]
        self.assertGreater(report["authority_smuggling_count"], 0)
        self.assertGreater(report["schema_error_count"], 0)
        self.assertTrue(any("authority_effect" in reason for reason in entry["authority_smuggling_reasons"]))
        self.assertTrue(any("safe vocabulary" in reason for reason in entry["behavior_violations"]))

    def test_missing_required_code_is_counted_and_fails(self):
        runner = load_runner()
        original = runner.classify_review_request

        def omit(request):
            review = original(request)
            if request["id"] == "ABG-N02":
                review["required_codes"].remove("SEGMENT_HARM")
            return review

        with mock.patch.object(runner, "classify_review_request", omit):
            report = runner.validate(ROOT)
        self.assert_failed(report)
        self.assertEqual(report["missing_required_code_count"], 1)
        self.assertEqual(report["results"][6]["missing_required_codes"], ["SEGMENT_HARM"])

    def test_unexpected_code_is_counted_and_fails(self):
        runner = load_runner()
        original = runner.classify_review_request

        def add(request):
            review = original(request)
            if request["id"] == "ABG-A01":
                review["required_codes"].append("UNEXPECTED_CODE")
            return review

        with mock.patch.object(runner, "classify_review_request", add):
            report = runner.validate(ROOT)
        self.assert_failed(report)
        self.assertEqual(report["unexpected_code_count"], 1)
        self.assertEqual(report["results"][8]["unexpected_codes"], ["UNEXPECTED_CODE"])

    def test_verdict_mismatch_is_counted_and_fails(self):
        runner = load_runner()
        original = runner.classify_review_request

        def mismatch(request):
            review = original(request)
            if request["id"] == "ABG-P04":
                review["verdict"] = "SIGNAL_ONLY"
            return review

        with mock.patch.object(runner, "classify_review_request", mismatch):
            report = runner.validate(ROOT)
        self.assert_failed(report)
        self.assertEqual(report["verdict_mismatch_count"], 1)
        self.assertEqual(report["results"][3]["actual_verdict"], "SIGNAL_ONLY")

    def test_classifier_exception_is_a_visible_input_error(self):
        runner = load_runner()
        original = runner.classify_review_request

        def explode(request):
            if request["id"] == "ABG-A11":
                raise RuntimeError("injected classifier failure")
            return original(request)

        with mock.patch.object(runner, "classify_review_request", explode):
            report = runner.validate(ROOT)
        self.assert_failed(report)
        self.assertEqual(report["input_error_count"], 1)
        self.assertIn("injected classifier failure", report["results"][18]["input_error"])

    def test_hard_coded_zero_summary_is_detected_from_results(self):
        runner = load_runner()
        original_classifier = runner.classify_review_request
        original_derive = runner._derive_counters

        def fabricate(request):
            review = original_classifier(request)
            if request["id"] == "ABG-P01":
                review["evidence_refs"].append("fabricated_ref")
            return review

        def zeros(results):
            return {key: 0 for key in original_derive(results)}

        with (
            mock.patch.object(runner, "classify_review_request", fabricate),
            mock.patch.object(runner, "_derive_counters", zeros),
        ):
            report = runner.validate(ROOT)
        self.assert_failed(report)
        self.assertGreater(report["summary_integrity_count"], 0)
        self.assertTrue(any("fabricated_evidence_count" in reason for reason in report["summary_errors"]))


if __name__ == "__main__":
    unittest.main()
