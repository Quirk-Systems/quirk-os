import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from compiler import BREADTH, canonical, compile_pack, digest, load, write_pack

ROOT = Path(__file__).resolve().parents[2]
SOURCE = load(Path(__file__).with_name("source.json"))


class CrossingTests(unittest.TestCase):
    def test_three_domains_keep_words_attribution_and_breadth(self):
        pack = compile_pack(SOURCE)
        self.assertEqual(len(pack["projections"]), 3)
        for item in pack["projections"]:
            self.assertEqual(item["projection"]["words"], SOURCE["words"])
            self.assertEqual(item["projection"]["attribution"], SOURCE["attribution"])
            self.assertEqual(item["projection"]["breadth"], BREADTH)
            self.assertEqual(item["source_bindings"][0]["sha256"], digest(SOURCE))

    def test_replay_and_extension_round_trip(self):
        first = compile_pack(SOURCE)
        second = compile_pack(json.loads(canonical(SOURCE)))
        self.assertEqual(digest(first), digest(second))
        self.assertEqual(first["source"], SOURCE)
        self.assertEqual(first["projections"][0]["projection"]["extensions"], SOURCE["extensions"])

    def test_schema_conformance(self):
        from jsonschema import Draft202012Validator, FormatChecker
        schema = load(ROOT / "schemas/projection-envelope.schema.json")
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        for projection in compile_pack(SOURCE)["projections"]:
            validator.validate(projection)

    def test_fail_closed_matrix(self):
        for key, value in [
            ("visibility", "private"), ("rights", "unknown"), ("status", "canon"),
            ("freshness", "stale"), ("conflicts", ["unresolved"]),
            ("fixture_version", "future"), ("revision", ""), ("words", ""),
            ("attribution", ""), ("extensions", []),
        ]:
            with self.subTest(key=key):
                changed = copy.deepcopy(SOURCE)
                changed[key] = value
                with self.assertRaises(ValueError):
                    compile_pack(changed)

    def test_unsupported_domain_and_non_finite(self):
        changed = copy.deepcopy(SOURCE)
        changed["branches"]["unknown"] = "meaning"
        with self.assertRaises(ValueError):
            compile_pack(changed)
        changed = copy.deepcopy(SOURCE)
        changed["extensions"]["bad"] = float("nan")
        with self.assertRaises(ValueError):
            compile_pack(changed)

    def test_duplicate_keys_and_constants(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.json"
            for body in ['{"a":1,"a":2}', '{"a":NaN}']:
                path.write_text(body)
                with self.assertRaises(ValueError):
                    load(path)

    def test_write_hashes_and_preserve_existing(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "pack"
            write_pack(compile_pack(SOURCE), dest)
            receipt = load(dest / "receipt.json")
            import hashlib
            for name, expected in receipt["output_sha256"].items():
                self.assertEqual(hashlib.sha256((dest / name).read_bytes()).hexdigest(), expected)
            with self.assertRaises(ValueError):
                write_pack(compile_pack(SOURCE), dest)
            self.assertFalse(receipt["accepted"])

    def test_partial_failure_leaves_no_delivery(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "pack"
            with patch("compiler.os.rename", side_effect=OSError("simulated delivery failure")):
                with self.assertRaises(OSError):
                    write_pack(compile_pack(SOURCE), dest)
            self.assertFalse(dest.exists())
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_compiler_does_not_mutate_input(self):
        baseline = copy.deepcopy(SOURCE)
        compile_pack(SOURCE)
        self.assertEqual(SOURCE, baseline)

    def test_projection_edits_do_not_contaminate_other_domains(self):
        pack = compile_pack(SOURCE)
        pack["projections"][0]["projection"]["breadth"].append("local-only")
        self.assertEqual(pack["projections"][1]["projection"]["breadth"], BREADTH[:3])
        self.assertEqual(compile_pack(SOURCE)["projections"][0]["projection"]["breadth"], BREADTH[:3])


if __name__ == "__main__":
    unittest.main()
