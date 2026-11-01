from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parent / "emit_ci_receipt.py"


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2) + "\n")


def git(repo, *args):
    r = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        text=True,
        capture_output=True,
    )
    return r.stdout.strip()


class ReceiptTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.root = self.repo / "programs" / "one-to-infinity"
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "tests@example.invalid")
        git(self.repo, "config", "user.name", "Fixture")
        self.validator = self.root / "tests" / "validate_contracts.py"
        self.validator.parent.mkdir(parents=True)
        self.validator.write_text("# fixture validator\n")
        report = {
            "status": "pass",
            "admission": "NOT_ADMITTED",
            "positive_passing": 4,
            "adversarial_rejecting_for_intended_rule": 11,
            "results": [],
            "schema_sha256": {},
        }
        for n in ("transformation", "run", "evidence", "promotion"):
            path = self.root / "contracts" / f"{n}.schema.json"
            write(path, {"type": "object", "title": n})
            report["schema_sha256"][n] = digest(path)
        for n in ("transformation", "run", "evidence", "promotion"):
            path = self.root / "fixtures" / "positive" / f"{n}.valid.json"
            write(path, {"contract": n})
            report["results"].append(
                {
                    "fixture": path.name,
                    "expected": "accept",
                    "passed": True,
                    "sha256": digest(path),
                }
            )
        for i in range(11):
            path = self.root / "fixtures" / "adversarial" / f"fixture-{i:02d}.json"
            write(path, {"fixture_id": i, "expected_rule": "RULE"})
            report["results"].append(
                {
                    "fixture": path.stem,
                    "expected": "reject",
                    "passed": True,
                    "sha256": digest(path),
                }
            )
        report["validator_sha256"] = digest(self.validator)
        write(self.root / "MANIFEST.json", {"pack": "candidate"})
        write(self.root / "evidence" / "validation-report.generated.json", report)
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "sample commit")
        self.head = git(self.repo, "rev-parse", "HEAD")

    def run_cli(self, head=None):
        return subprocess.run(
            [
                "python3",
                str(SCRIPT),
                "--repo-root",
                str(self.repo),
                "--expected-head",
                head or self.head,
            ],
            capture_output=True,
            text=True,
        )

    def test_pass_exact_head_with_all_digests(self):
        r = self.run_cli()
        self.assertEqual(r.returncode, 0, r.stderr)
        receipt = json.loads(
            (self.root / "evidence" / "ci-receipt.json").read_text()
        )
        self.assertEqual(receipt["git_head"], self.head)
        self.assertFalse(receipt["human_approval"])
        self.assertFalse(receipt["canon_promotion"])

    def test_reject_wrong_head(self):
        r = self.run_cli("0" * 40)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("HEAD differs", r.stderr)

    def test_reject_tampered_validator(self):
        self.validator.write_text("# tampered validator\n")
        r = self.run_cli()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("dirty", r.stderr)

    def test_reject_tampered_fixture_even_with_new_commit(self):
        f = self.root / "fixtures" / "adversarial" / "fixture-00.json"
        f.write_text(f.read_text().replace("RULE", "EVADED"))
        git(self.repo, "add", str(f))
        git(self.repo, "commit", "-qm", "tamper fixture")
        new_head = git(self.repo, "rev-parse", "HEAD")
        r = self.run_cli(new_head)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("fixture changed", r.stderr)

    def test_reject_report_inventing_approval(self):
        rpath = self.root / "evidence" / "validation-report.generated.json"
        data = json.loads(rpath.read_text())
        data["admission"] = "CANON"
        write(rpath, data)
        git(self.repo, "add", str(rpath))
        git(self.repo, "commit", "-qm", "forge report")
        r = self.run_cli(git(self.repo, "rev-parse", "HEAD"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("admission", r.stderr)


if __name__ == "__main__":
    unittest.main()
