from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_furniture_brief.py"


class FurnitureBriefFixtureCorpusTests(unittest.TestCase):
    """Drives the full eval corpus through the CLI validator, exactly as CI would."""

    def run_validator(self) -> dict:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), "--repo", str(ROOT), "--require-pass"],
            check=False,
            capture_output=True,
            text=True,
            env={"PYTHONPATH": str(ROOT / "scripts")},
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_corpus_passes(self) -> None:
        summary = self.run_validator()
        self.assertTrue(summary["passed"])
        self.assertEqual(summary["decision_mismatch_count"], 0)
        self.assertEqual(summary["refusal_code_mismatch_count"], 0)
        self.assertEqual(summary["schema_error_count"], 0)
        self.assertTrue(summary["receipt_chain_valid"])

    def test_corpus_covers_every_required_refusal_category(self) -> None:
        summary = self.run_validator()
        all_codes = {
            code
            for result in summary["results"]
            for code in result["actual_refusal_codes"]
        }
        self.assertEqual(
            all_codes,
            {
                "ADULT_CONSENT_MISSING_OR_AMBIGUOUS",
                "STORAGE_OR_CONTENT_PERMISSION_MISSING",
                "IDENTITY_RISK_UNACCEPTABLE",
                "FURNITURE_NOT_LOAD_BEARING",
                "GRIP_BELOW_THRESHOLD",
                "LINEAGE_INVALID",
            },
        )

    def test_exactly_one_case_finalizes(self) -> None:
        summary = self.run_validator()
        finalized = [r for r in summary["results"] if r["actual_decision"] == "FINALIZE"]
        self.assertEqual([r["case_id"] for r in finalized], ["case-001-success"])


class ReceiptChainIntegrityTests(unittest.TestCase):
    """The receipt chain must be append-only and hash-linked: any tamper is detected."""

    def setUp(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        from furniture_brief.compiler import compile_and_receipt
        from furniture_brief.receipt import verify_chain

        self.compile_and_receipt = compile_and_receipt
        self.verify_chain = verify_chain

        cases = json.loads((ROOT / "evals" / "furniture-brief" / "cases.json").read_text())["cases"]
        self.chain: list[dict] = []
        for case in cases:
            self.compile_and_receipt(case["request"], self.chain)

    def test_untampered_chain_verifies(self) -> None:
        verdict = self.verify_chain(self.chain)
        self.assertTrue(verdict["valid"])
        self.assertIsNone(verdict["broken_at"])

    def test_mutated_entry_is_detected(self) -> None:
        tampered = copy.deepcopy(self.chain)
        tampered[2]["decision"] = "FINALIZE"  # silently flip a refused case to approved
        verdict = self.verify_chain(tampered)
        self.assertFalse(verdict["valid"])
        self.assertEqual(verdict["broken_at"], 2)

    def test_reordered_chain_is_detected(self) -> None:
        reordered = copy.deepcopy(self.chain)
        reordered[0], reordered[1] = reordered[1], reordered[0]
        verdict = self.verify_chain(reordered)
        self.assertFalse(verdict["valid"])

    def test_dropped_entry_breaks_linkage(self) -> None:
        truncated = copy.deepcopy(self.chain)
        del truncated[3]
        verdict = self.verify_chain(truncated)
        self.assertFalse(verdict["valid"])


class ABryFurnitureSpecificityExperimentTests(unittest.TestCase):
    """One A/Bry-style local experiment: same synthetic root, Furniture specificity is
    the only variable changed. Records the observable contract/readiness delta and a
    verdict -- not a claim about musical quality.
    """

    def setUp(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        from furniture_brief.compiler import compile_batch

        self.compile_batch = compile_batch
        cases = {c["id"]: c for c in json.loads(
            (ROOT / "evals" / "furniture-brief" / "cases.json").read_text()
        )["cases"]}
        # Same synthetic root and every other asset; only `furniture` differs.
        self.variant_a = cases["case-005-furniture-decorative"]["request"]  # low specificity
        self.variant_b = cases["case-001-success"]["request"]  # high specificity

    def test_furniture_specificity_is_the_only_difference(self) -> None:
        a, b = self.variant_a, self.variant_b
        self.assertEqual(a["assets"], b["assets"])
        self.assertEqual(a["provenance"], b["provenance"])
        self.assertNotEqual(a["furniture"], b["furniture"])

    def test_specificity_flips_the_gate_and_raises_grounded(self) -> None:
        result_a = self.compile_batch(self.variant_a)
        result_b = self.compile_batch(self.variant_b)

        self.assertEqual(result_a["decision"], "FLOP")
        self.assertEqual(result_b["decision"], "FINALIZE")
        self.assertLess(result_a["grip"]["grounded"], result_b["grip"]["grounded"])
        self.assertFalse(result_a["furniture_assessment"]["load_bearing"])
        self.assertTrue(result_b["furniture_assessment"]["load_bearing"])

        # Recorded verdict for this run (see docs/furniture-brief/README.md):
        # ADVANCE -- Furniture specificity is a load-bearing, cheaply-iterable lever:
        # it is the only variable changed and it alone flipped FLOP -> FINALIZE and
        # raised Grounded 1 -> 2. Worth spending more synthetic fixtures on Furniture
        # wording before touching any other axis. This is a readiness/contract signal
        # only, not evidence about how the resulting song would sound.
        verdict = "ADVANCE"
        self.assertIn(verdict, {"ADVANCE", "KILL", "REGEN", "HOLD"})


if __name__ == "__main__":
    unittest.main()
