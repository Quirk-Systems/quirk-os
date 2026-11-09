import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from compiler import load
from synchronize import sync

SOURCE = load(Path(__file__).with_name("source.json"))


class LocalSyncTests(unittest.TestCase):
    def test_refresh_replay_and_revision_history(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = sync(SOURCE, root)
            self.assertEqual(first["status"], "updated")
            self.assertEqual(sync(SOURCE, root, first["snapshot"])["status"], "unchanged")
            self.assertEqual(len(list((root / "receipts").glob("*.json"))), 1)
            updated = copy.deepcopy(SOURCE)
            updated["revision"] = "0.2.0"
            updated["branches"]["town"] = "A different fictional consequence."
            with self.assertRaises(ValueError):
                sync(updated, root, None)
            second = sync(updated, root, first["snapshot"])
            self.assertEqual(load(root / "current.json")["previous"], first["snapshot"])
            self.assertNotEqual(second["snapshot"], first["snapshot"])
            self.assertEqual(load(root / "snapshots" / first["snapshot"] / "pack.json")["source"], SOURCE)
            restored = sync(SOURCE, root, second["snapshot"])
            self.assertEqual(restored["snapshot"], first["snapshot"])
            self.assertEqual(load(root / "current.json")["snapshot"], first["snapshot"])

    def test_lock_and_tamper_block_delivery(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = sync(SOURCE, root)
            lock = root / ".sync-lock"
            lock.mkdir()
            with self.assertRaises(FileExistsError):
                sync(SOURCE, root, first["snapshot"])
            lock.rmdir()
            (root / "snapshots" / first["snapshot"] / "town.json").write_text("{}")
            with self.assertRaises(ValueError):
                sync(SOURCE, root, first["snapshot"])

    def test_pointer_failure_keeps_prior_and_marks_receipt_failed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch("synchronize.os.replace", side_effect=OSError("simulated pointer failure")):
                with self.assertRaises(OSError):
                    sync(SOURCE, root)
            self.assertFalse((root / "current.json").exists())
            self.assertFalse((root / ".sync-lock").exists())
            receipt = load(next((root / "receipts").glob("*.json")))
            self.assertEqual(receipt["result"], "failed")
            self.assertEqual(receipt["changes"], [])

    def test_source_version_cannot_hide_meaning_change(self):
        with tempfile.TemporaryDirectory() as temp:
            first = sync(SOURCE, temp)
            changed = copy.deepcopy(SOURCE)
            changed["words"] = "Different meaning under the same revision."
            with self.assertRaisesRegex(ValueError, "revision reused"):
                sync(changed, temp, first["snapshot"])

    def test_style_release_is_part_of_snapshot_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            first = sync(SOURCE, temp)
            original_load = load
            def revised_style(path):
                value = original_load(path)
                if Path(path).name == "style-lock.json" and "styles" in Path(path).parts:
                    value["token_sha256"] = "0" * 64
                return value
            with patch("synchronize.load", side_effect=revised_style):
                second = sync(SOURCE, temp, first["snapshot"])
            self.assertNotEqual(first["snapshot"], second["snapshot"])

    def test_receipt_does_not_claim_success_before_pointer_delivery(self):
        import os
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original_replace = os.replace
            def inspect_provisional(before, after):
                receipt = load(next((root / "receipts").glob("*.json")))
                self.assertEqual(receipt["result"], "cancelled")
                self.assertEqual(receipt["changes"], [])
                return original_replace(before, after)
            with patch("synchronize.os.replace", side_effect=inspect_provisional):
                sync(SOURCE, root)
            self.assertEqual(load(next((root / "receipts").glob("*.json")))["result"], "success")


if __name__ == "__main__":
    unittest.main()
