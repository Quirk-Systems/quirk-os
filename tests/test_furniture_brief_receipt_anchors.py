import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from furniture_brief.receipt import append, verify_chain, sha256_json


class ReceiptAnchorTests(unittest.TestCase):
    def setUp(self):
        self.chain = []
        for index in range(3):
            append(self.chain, batch_id=f"synthetic-{index}", input_hash="a" * 64,
                   output_hash=None, decision="FLOP", refusal_codes=["FIXTURE"],
                   proof_state={"synthetic": True})
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
        chain[0]["entry_hash"] = sha256_json({k:v for k,v in chain[0].items() if k != "entry_hash"})
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


if __name__ == "__main__":
    unittest.main()
