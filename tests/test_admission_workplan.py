from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from admission_workplan import AUDIT, QUEUE, build_plan, local_path


class AdmissionWorkplanTests(unittest.TestCase):
    def test_plan_accounts_for_every_hold_without_granting_authority(self):
        plan = build_plan(ROOT)
        queue = json.loads((ROOT / QUEUE).read_text())
        self.assertEqual(set(queue["blocking_move_ids"]), {task["move_id"] for task in plan["tasks"]})
        self.assertEqual("inspect_only", plan["execution_mode"])
        self.assertEqual("none", plan["authority_effect"])
        self.assertEqual(0, plan["verified_moves"])
        for task in plan["tasks"]:
            self.assertTrue(task["acceptance"])
            self.assertTrue(all(item["status"] == "unassessed" for item in task["acceptance"]))
        seen = set()
        for wave in plan["dependency_waves"]:
            for move_id in wave:
                task = next(task for task in plan["tasks"] if task["move_id"] == move_id)
                self.assertLessEqual(set(task["dependencies"]), seen)
            seen.update(wave)

    def test_outside_and_directory_symlink_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            root = parent / "repo"
            root.mkdir()
            (parent / "outside").mkdir()
            (root / "linked").symlink_to(parent / "outside", target_is_directory=True)
            for path in ("../outside", str(parent / "outside"), "linked/receipt.json"):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    local_path(root, path)

    def test_stale_criteria_and_audit_self_verification_are_refused(self):
        # Copy only audit inputs and share Git history; no remote or operative mutation.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").write_text("gitdir: " + str(ROOT / ".git") + "\n")
            for relative in (QUEUE, AUDIT):
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)
            queue = json.loads((ROOT / QUEUE).read_text())
            for ref in queue["move_refs"]:
                target = root / ref["path"]
                shutil.copyfile(ROOT / ref["path"], target)
            original = json.loads((root / AUDIT).read_text())
            for attack in ("criteria", "verified", "coverage"):
                audit = copy.deepcopy(original)
                if attack == "criteria":
                    audit["moves"][0]["acceptance_checks"] = ["pretend it passed"]
                elif attack == "verified":
                    audit["moves"][0]["verified"] = True
                else:
                    audit["moves"].pop()
                (root / AUDIT).write_text(json.dumps(audit))
                with self.subTest(attack=attack), self.assertRaises(ValueError):
                    build_plan(root)


if __name__ == "__main__":
    unittest.main()
