import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from furniture_brief.receipt import append, sha256_json, verify_chain


class ReceiptAnchorTests(unittest.TestCase):
    """expected_count/expected_tip let a caller detect tail-truncation, which an
    unanchored hash chain cannot: a valid prefix is itself structurally valid.
    """

    def setUp(self):
        self.chain = []
        for index in range(3):
            append(
                self.chain,
                batch_id=f"synthetic-{index}",
                input_hash="a" * 64,
                output_hash=None,
                decision="FLOP",
                refusal_codes=["FIXTURE"],
                proof_state={"synthetic": True},
            )
        self.tip = self.chain[-1]["entry_hash"]

    def test_full_chain_matches_trusted_anchors(self):
        self.assertTrue(verify_chain(self.chain, expected_count=3, expected_tip=self.tip)["valid"])

    def test_unanchored_prefix_has_only_structural_validity(self):
        self.assertTrue(verify_chain(self.chain[:-1])["valid"])

    def test_trusted_count_detects_tail_loss(self):
        self.assertFalse(verify_chain(self.chain[:-1], expected_count=3)["valid"])

    def test_trusted_tip_detects_tail_loss(self):
        self.assertFalse(verify_chain(self.chain[:-1], expected_tip=self.tip)["valid"])

    def test_empty_chain_cannot_match_nonempty_anchor(self):
        self.assertFalse(verify_chain([], expected_count=3, expected_tip=self.tip)["valid"])

    def test_wrong_tip_rejects_an_otherwise_valid_chain(self):
        self.assertFalse(verify_chain(self.chain, expected_tip="f" * 64)["valid"])

    def test_invalid_anchor_types_fail_closed(self):
        for value in [-1, True, "3"]:
            with self.subTest(count=value):
                self.assertFalse(verify_chain(self.chain, expected_count=value)["valid"])
        for value in [0, "bad", "Z" * 64]:
            with self.subTest(tip=value):
                self.assertFalse(verify_chain(self.chain, expected_tip=value)["valid"])

    def test_malformed_chain_or_entry_is_reported(self):
        for value in [None, {}, [None], [42]]:
            with self.subTest(value=value):
                self.assertFalse(verify_chain(value)["valid"])

    def test_resealed_sequence_gap_is_rejected(self):
        chain = copy.deepcopy(self.chain)
        chain[0]["seq"] = 2
        chain[0]["entry_hash"] = sha256_json({k: v for k, v in chain[0].items() if k != "entry_hash"})
        self.assertFalse(verify_chain(chain)["valid"])

    def test_mutation_and_reordering_remain_rejected(self):
        chain = copy.deepcopy(self.chain)
        chain[1]["decision"] = "FINALIZE"
        self.assertFalse(verify_chain(chain)["valid"])
        self.assertFalse(verify_chain(list(reversed(self.chain)))["valid"])

    def test_non_json_content_is_reported(self):
        chain = copy.deepcopy(self.chain)
        chain[0]["proof_state"] = {"non_json": {1, 2}}
        self.assertFalse(verify_chain(chain)["valid"])

    def test_deeply_nested_entry_returns_invalid_with_trusted_anchors(self):
        chain = copy.deepcopy(self.chain)
        nested = chain[0]["proof_state"]
        for _ in range(10000):
            nested["child"] = {}
            nested = nested["child"]
        verdict = verify_chain(chain, expected_count=3, expected_tip=self.tip)
        self.assertEqual(verdict, {
            "valid": False,
            "broken_at": 0,
            "reason": "entry exceeds JSON serialization recursion limit",
        })

    def test_anchor_mismatch_positions_are_boundaries(self):
        for chain, anchors, position in [
            (self.chain[:-1], {"expected_count": 3}, 2),
            (self.chain, {"expected_count": 2}, 2),
            (self.chain, {"expected_tip": "f" * 64}, 3),
            ([], {"expected_tip": self.tip}, 0),
        ]:
            with self.subTest(anchors=anchors, length=len(chain)):
                verdict = verify_chain(chain, **anchors)
                self.assertFalse(verdict["valid"])
                self.assertEqual(verdict["broken_at"], position)

    def test_both_anchors_must_match(self):
        self.assertFalse(verify_chain(
            self.chain, expected_count=3, expected_tip="f" * 64,
        )["valid"])
        self.assertFalse(verify_chain(
            self.chain, expected_count=2, expected_tip=self.tip,
        )["valid"])

    def test_count_does_not_authenticate_resealed_replacement(self):
        chain = copy.deepcopy(self.chain)
        previous = "0" * 64
        for entry in chain:
            entry["decision"] = "FINALIZE"
            entry["prev_hash"] = previous
            entry["entry_hash"] = sha256_json({
                k: v for k, v in entry.items() if k != "entry_hash"
            })
            previous = entry["entry_hash"]
        self.assertTrue(verify_chain(chain, expected_count=3)["valid"])
        self.assertFalse(verify_chain(chain, expected_tip=self.tip)["valid"])


if __name__ == "__main__":
    unittest.main()
