from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from distill_loop import (  # noqa: E402
    apply_promotion,
    attest_promotion,
    candidate_state,
    load_schemas,
    new_ledger,
    next_run_context,
    post_run_distill,
    run_eval_suite,
    schema_errors,
    validate_promotion_receipt,
    verify_ledger,
)
from distill_loop.ledger import append_entry  # noqa: E402
from sync_control_plane.skill_runtime import load_skill_for_execution, validate_manifest_integrity  # noqa: E402

EXAMPLE = ROOT / "examples" / "distill-loop"


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class DistillFixture:
    def __init__(self) -> None:
        self.schemas = load_schemas(ROOT)
        self.receipt = _json(EXAMPLE / "run-receipt.json")
        self.trace = _json(EXAMPLE / "run-trace.json")
        source_dir = ROOT / "skills" / self.receipt["skill_id"]
        self.source_manifest = _json(source_dir / "manifest.json")
        self.source_text = (source_dir / "SKILL.md").read_text(encoding="utf-8")
        self.promotion_receipt = _json(EXAMPLE / "promotion-receipt.json")
        self.reviewed_suite = _json(EXAMPLE / "reviewed-eval-suite.json")

    def distill(self, *, receipt=None, trace=None, ledger=None):
        return post_run_distill(
            receipt=receipt or self.receipt,
            trace=trace or self.trace,
            source_manifest=self.source_manifest,
            source_text=self.source_text,
            ledger=ledger or new_ledger(),
            schemas=self.schemas,
        )


class TriggerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fx = DistillFixture()
        cls.result = cls.fx.distill()

    def test_completed_run_distills_a_candidate_package(self) -> None:
        self.assertEqual(self.result["outcome"], "distilled")
        manifest = self.result["manifest"]
        self.assertEqual(manifest["status"], "candidate")
        self.assertTrue(manifest["id"].startswith("quirk-distilled-"))
        self.assertEqual(schema_errors(self.fx.schemas["skill_package"], manifest), [])
        self.assertEqual(validate_manifest_integrity(manifest, self.result["skill_text"]), [])

    def test_frontmatter_matches_manifest_like_every_other_package(self) -> None:
        text = self.result["skill_text"]
        self.assertTrue(text.startswith("---\n") and text.endswith("\n"))
        frontmatter = yaml.safe_load(text.split("---", 2)[1])
        manifest = self.result["manifest"]
        self.assertEqual(frontmatter["name"], manifest["id"])
        self.assertEqual(frontmatter["version"], manifest["version"])
        self.assertEqual(frontmatter["status"], "candidate")
        self.assertEqual(frontmatter["family"], manifest["family"])
        self.assertEqual(frontmatter["authority_ceiling"], manifest["authority"]["ceiling"])
        self.assertEqual(frontmatter["manifest"], "manifest.json")
        self.assertEqual(frontmatter["eval_suite"], "../../" + manifest["quality"]["eval_suite_ref"])

    def test_only_declared_successful_moves_are_distilled(self) -> None:
        moves = self.result["manifest"]["method"]["moves"]
        self.assertEqual(moves, ["read_sources", "normalize_claims", "map_contradictions", "emit_synthesis_pack"])
        self.assertNotIn("cache_sources", moves)
        self.assertNotIn("emit_proposed_move", moves)
        self.assertIn("UNDECLARED_MOVE_EXCLUDED", self.result["finding_codes"])
        self.assertEqual(self.result["ledger_entry"]["refs"]["excluded_moves"], ["cache_sources", "emit_proposed_move"])

    def test_distilled_ceiling_never_exceeds_source(self) -> None:
        self.assertEqual(self.result["manifest"]["authority"]["ceiling"], "infer")
        escalated = copy.deepcopy(self.fx.receipt)
        escalated["authority_ceiling_observed"] = "propose"
        outcome = self.fx.distill(receipt=escalated)
        self.assertEqual(outcome["outcome"], "abstained")
        self.assertIn("CEILING_ESCALATION_OBSERVED", outcome["finding_codes"])

    def test_non_completed_runs_abstain_with_a_ledger_entry(self) -> None:
        for status in ("blocked", "abstained", "failed"):
            receipt = copy.deepcopy(self.fx.receipt)
            receipt["status"] = status
            outcome = self.fx.distill(receipt=receipt)
            with self.subTest(status=status):
                self.assertEqual(outcome["outcome"], "abstained")
                self.assertIn("RUN_NOT_COMPLETED", outcome["finding_codes"])
                self.assertEqual(outcome["ledger"]["entries"][-1]["kind"], "abstained")
                self.assertEqual(set(outcome["files"]), {"skills/distill-ledger.json"})

    def test_receipt_bound_to_other_digest_abstains(self) -> None:
        receipt = copy.deepcopy(self.fx.receipt)
        receipt["skill_manifest_sha256"] = "a" * 64
        outcome = self.fx.distill(receipt=receipt)
        self.assertIn("RECEIPT_SOURCE_MISMATCH", outcome["finding_codes"])

    def test_fewer_than_three_moves_is_not_a_skill(self) -> None:
        trace = copy.deepcopy(self.fx.trace)
        trace["moves"] = trace["moves"][:3]
        outcome = self.fx.distill(trace=trace)
        self.assertEqual(outcome["outcome"], "abstained")
        self.assertIn("INSUFFICIENT_SUCCESSFUL_MOVES", outcome["finding_codes"])

    def test_stop_condition_in_trace_abstains(self) -> None:
        trace = copy.deepcopy(self.fx.trace)
        trace["stop_conditions_hit"] = ["missing_provenance"]
        outcome = self.fx.distill(trace=trace)
        self.assertIn("STOP_CONDITION_HIT", outcome["finding_codes"])

    def test_same_receipt_distills_once(self) -> None:
        again = self.fx.distill(ledger=self.result["ledger"])
        self.assertEqual(again["outcome"], "abstained")
        self.assertIn("ALREADY_DISTILLED", again["finding_codes"])
        self.assertEqual(len(again["ledger"]["entries"]), 2)

    def test_trigger_is_deterministic(self) -> None:
        second = self.fx.distill()
        self.assertEqual(second["files"], self.result["files"])

    def test_runtime_loader_rejects_distilled_candidate_with_full_grant(self) -> None:
        manifest = self.result["manifest"]
        grant = {
            "grant_id": "grant.probe.0001",
            "skill_id": manifest["id"],
            "skill_version": manifest["version"],
            "skill_manifest_sha256": manifest["integrity"]["manifest_sha256"],
            "decision": "approved",
            "admission_ref": "decision.probe.0001",
            "requested_by": "operator.probe",
            "approved_by": "human.probe",
            "issued_at": "2026-09-19T00:00:00Z",
            "expires_at": "2026-09-19T02:00:00Z",
            "authority_ceiling": manifest["authority"]["ceiling"],
            "allowed_actions": [manifest["method"]["moves"][0]],
            "purpose": "prove distilled candidates never execute",
        }
        loaded = load_skill_for_execution(manifest, self.result["skill_text"], grant, now="2026-09-19T01:00:00Z")
        self.assertFalse(loaded["loaded"])
        self.assertIn("runtime loader rejects unadmitted skill version", loaded["errors"])

    def test_starter_suite_is_honest_and_incomplete(self) -> None:
        report = run_eval_suite(self.result["eval_suite"], self.result["manifest"], case_schema=self.fx.schemas["skill_eval_case"])
        self.assertEqual(report["failures"], [])
        self.assertEqual(report["passed"], 2)
        self.assertEqual(report["missing_kinds"], ["adversarial", "regression"])
        self.assertFalse(report["complete"])

    def test_distilled_skill_cannot_be_distilled_again(self) -> None:
        manifest = self.result["manifest"]
        receipt = copy.deepcopy(self.fx.receipt)
        receipt.update({
            "receipt_id": "receipt.second-order.0001",
            "skill_id": manifest["id"],
            "skill_version": manifest["version"],
            "skill_manifest_sha256": manifest["integrity"]["manifest_sha256"],
        })
        trace = copy.deepcopy(self.fx.trace)
        trace.update({"receipt_id": receipt["receipt_id"], "skill_id": manifest["id"], "skill_version": manifest["version"]})
        outcome = post_run_distill(
            receipt=receipt, trace=trace, source_manifest=manifest, source_text=self.result["skill_text"],
            ledger=new_ledger(), schemas=self.fx.schemas,
        )
        self.assertIn("RECURSIVE_DISTILLATION_DENIED", outcome["finding_codes"])


class LedgerTests(unittest.TestCase):
    def test_ledger_is_hash_chained_and_tamper_evident(self) -> None:
        ledger = new_ledger()
        self.assertEqual(verify_ledger(ledger), [])
        ledger, _ = append_entry(
            ledger, kind="abstained", recorded_at="2026-09-19T00:00:00Z", actor="agent.distill-loop",
            candidate_id=None, source_receipt_id="receipt.x.1", source_skill_id="quirk-x",
            source_skill_version="0.1.0", finding_codes=["RUN_NOT_COMPLETED"], refs={},
        )
        self.assertEqual(verify_ledger(ledger), [])
        tampered = copy.deepcopy(ledger)
        tampered["entries"][0]["finding_codes"] = []
        self.assertTrue(any("entry sha256" in error for error in verify_ledger(tampered)))
        with self.assertRaises(ValueError):
            append_entry(
                tampered, kind="abstained", recorded_at="2026-09-19T00:00:00Z", actor="agent.distill-loop",
                candidate_id=None, source_receipt_id="receipt.x.2", source_skill_id="quirk-x",
                source_skill_version="0.1.0", finding_codes=[], refs={},
            )

    def test_live_ledger_is_valid_genesis_or_valid_chain(self) -> None:
        schemas = load_schemas(ROOT)
        ledger = _json(ROOT / "skills" / "distill-ledger.json")
        self.assertEqual(schema_errors(schemas["distill_ledger"], ledger), [])
        self.assertEqual(verify_ledger(ledger), [])


class PromotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fx = DistillFixture()
        cls.distilled = cls.fx.distill()

    def _validate(self, receipt=None, **overrides):
        kwargs = {
            "candidate_manifest": self.distilled["manifest"],
            "candidate_source": self.distilled["skill_text"],
            "eval_suite": self.fx.reviewed_suite,
            "ledger": self.distilled["ledger"],
            "schemas": self.fx.schemas,
        }
        kwargs.update(overrides)
        return validate_promotion_receipt(receipt or self.fx.promotion_receipt, **kwargs)

    def test_sound_receipt_promotes_to_reviewed_candidate_only(self) -> None:
        self.assertEqual(self._validate(), [])
        promoted = apply_promotion(
            self.fx.promotion_receipt,
            candidate_manifest=self.distilled["manifest"], candidate_source=self.distilled["skill_text"],
            eval_suite=self.fx.reviewed_suite, ledger=self.distilled["ledger"], schemas=self.fx.schemas,
        )
        self.assertEqual(promoted["outcome"], "promoted")
        self.assertEqual(candidate_state(promoted["ledger"], self.distilled["manifest"]["id"]), "promoted")
        self.assertNotIn(f"skills/{self.distilled['manifest']['id']}/manifest.json", promoted["files"])
        codes = promoted["ledger_entry"]["finding_codes"]
        for code in ("ADMISSION_EFFECT_NONE", "CANON_EFFECT_NONE", "RUNTIME_EFFECT_NONE"):
            self.assertIn(code, codes)

    def test_self_approval_is_refused(self) -> None:
        receipt = attest_promotion({**self.fx.promotion_receipt, "approved_by": self.fx.promotion_receipt["requested_by"]})
        self.assertTrue(any("distinct" in error for error in self._validate(receipt)))

    def test_trigger_cannot_approve_or_request_its_own_output(self) -> None:
        for field in ("approved_by", "requested_by"):
            receipt = attest_promotion({**self.fx.promotion_receipt, field: "agent.distill-loop"})
            with self.subTest(field=field):
                self.assertTrue(any("distill trigger" in error for error in self._validate(receipt)))

    def test_attestation_tamper_is_refused(self) -> None:
        receipt = copy.deepcopy(self.fx.promotion_receipt)
        receipt["decided_at"] = "2026-09-20T09:15:00Z"
        self.assertTrue(any("attestation" in error for error in self._validate(receipt)))

    def test_digest_mismatch_is_refused(self) -> None:
        receipt = attest_promotion({**self.fx.promotion_receipt, "candidate_manifest_sha256": "f" * 64})
        errors = self._validate(receipt)
        self.assertTrue(any("manifest digest" in error for error in errors))

    def test_incomplete_eval_suite_blocks_promotion(self) -> None:
        from distill_loop.common import sha256_json

        starter = self.distilled["eval_suite"]
        receipt = attest_promotion({**self.fx.promotion_receipt, "eval_suite_sha256": sha256_json(starter)})
        errors = self._validate(receipt, eval_suite=starter)
        self.assertTrue(any("all four eval kinds" in error for error in errors))

    def test_failing_eval_case_blocks_promotion(self) -> None:
        from distill_loop.common import sha256_json

        suite = copy.deepcopy(self.fx.reviewed_suite)
        suite[0]["expected"]["required_codes"].append("PROMOTION_IMPLIED")
        receipt = attest_promotion({**self.fx.promotion_receipt, "eval_suite_sha256": sha256_json(suite)})
        errors = self._validate(receipt, eval_suite=suite)
        self.assertTrue(any("eval failure" in error for error in errors))

    def test_unknown_provenance_is_refused(self) -> None:
        errors = self._validate(ledger=new_ledger())
        self.assertTrue(any("no distilled ledger entry" in error for error in errors))

    def test_promotion_receipt_may_not_claim_admission(self) -> None:
        receipt = attest_promotion({**self.fx.promotion_receipt, "promoted_to": "admitted"})
        self.assertTrue(any("receipt schema" in error for error in self._validate(receipt)))
        receipt = attest_promotion({**self.fx.promotion_receipt, "admission_effect": "admitted"})
        self.assertTrue(any("receipt schema" in error for error in self._validate(receipt)))

    def test_rejection_receipt_excludes_candidate(self) -> None:
        receipt = attest_promotion({**self.fx.promotion_receipt, "decision": "reject",
                                    "receipt_id": "receipt.distill-promotion.reject.0001"})
        rejected = apply_promotion(
            receipt, candidate_manifest=self.distilled["manifest"], candidate_source=self.distilled["skill_text"],
            eval_suite=self.fx.reviewed_suite, ledger=self.distilled["ledger"], schemas=self.fx.schemas,
        )
        self.assertEqual(rejected["outcome"], "rejected")
        context = next_run_context(rejected["ledger"])
        self.assertEqual(context["context_sources"], [])
        self.assertEqual(context["rejected"], [self.distilled["manifest"]["id"]])
        self.assertTrue(self._validate(ledger=rejected["ledger"]))


class ContextTests(unittest.TestCase):
    def test_only_promoted_candidates_reach_the_next_run(self) -> None:
        fx = DistillFixture()
        distilled = fx.distill()
        before = next_run_context(distilled["ledger"])
        self.assertEqual(before["context_sources"], [])
        self.assertEqual(before["pending_review"], [distilled["manifest"]["id"]])
        promoted = apply_promotion(
            fx.promotion_receipt, candidate_manifest=distilled["manifest"], candidate_source=distilled["skill_text"],
            eval_suite=fx.reviewed_suite, ledger=distilled["ledger"], schemas=fx.schemas,
        )
        after = next_run_context(promoted["ledger"])
        self.assertEqual([item["candidate_id"] for item in after["context_sources"]], [distilled["manifest"]["id"]])
        self.assertFalse(after["context_sources"][0]["runtime_loadable"])
        self.assertEqual(after["context_sources"][0]["tier"], "reviewed_candidate")

    def test_promoted_candidate_with_drifted_bytes_is_quarantined(self) -> None:
        import tempfile

        fx = DistillFixture()
        distilled = fx.distill()
        promoted = apply_promotion(
            fx.promotion_receipt, candidate_manifest=distilled["manifest"], candidate_source=distilled["skill_text"],
            eval_suite=fx.reviewed_suite, ledger=distilled["ledger"], schemas=fx.schemas,
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            from distill_loop import write_files

            write_files(root, distilled["files"])
            skill_path = root / distilled["candidate"]["source_path"]
            skill_path.write_text(skill_path.read_text(encoding="utf-8") + "\nedited after promotion\n", encoding="utf-8")
            context = next_run_context(promoted["ledger"], root=root)
            self.assertEqual(context["context_sources"], [])
            self.assertEqual(context["quarantined"][0]["candidate_id"], distilled["manifest"]["id"])


class CliLockTests(unittest.TestCase):
    def test_windows_lock_failures_do_not_spin_forever(self) -> None:
        import errno
        import tempfile
        from types import SimpleNamespace
        from unittest import mock

        import distill_loop.__main__ as cli

        contention = getattr(errno, "EDEADLOCK", getattr(errno, "EDEADLK", 36))

        def fake_msvcrt(sequence):
            calls = []

            def locking(fd, mode, nbytes):
                if mode == 2:  # LK_UNLCK
                    return None
                calls.append(mode)
                outcome = sequence[min(len(calls), len(sequence)) - 1]
                if outcome is not None:
                    raise outcome

            return SimpleNamespace(locking=locking, LK_LOCK=1, LK_UNLCK=2, calls=calls)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "skills" / "distill-ledger.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("before\n", encoding="utf-8")
            files = {"skills/distill-ledger.json": "after\n"}

            denied = fake_msvcrt([OSError(errno.EINVAL, "denied")])
            with mock.patch.object(cli, "fcntl", None), mock.patch.object(cli, "msvcrt", denied):
                self.assertEqual(cli._write_guarded(root, files), 1)
            self.assertEqual(len(denied.calls), 1)
            self.assertEqual(target.read_text(encoding="utf-8"), "before\n")

            busy = fake_msvcrt([OSError(contention, "busy")])
            with mock.patch.object(cli, "fcntl", None), mock.patch.object(cli, "msvcrt", busy):
                self.assertEqual(cli._write_guarded(root, files), 1)
            self.assertEqual(len(busy.calls), cli.WINDOWS_LOCK_ATTEMPTS)
            self.assertEqual(target.read_text(encoding="utf-8"), "before\n")

            eventually = fake_msvcrt([OSError(contention, "busy"), None])
            with mock.patch.object(cli, "fcntl", None), mock.patch.object(cli, "msvcrt", eventually):
                self.assertEqual(cli._write_guarded(root, files), 0)
            self.assertEqual(target.read_text(encoding="utf-8"), "after\n")


class ConformanceTests(unittest.TestCase):
    def test_validator_passes_and_reports_no_authority(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_distill_loop.py"), "--repo", str(ROOT), "--require-pass"],
            check=False, capture_output=True, text=True, env={"PYTHONPATH": str(ROOT / "scripts")},
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        report = json.loads(result.stdout.splitlines()[-1])
        self.assertEqual(report["verdict"], "PASS")
        self.assertEqual(report["authority_effect"], "none")
        self.assertEqual(report["admission_effect"], "none")
        self.assertTrue(all(report["controls"].values()), report["controls"])


if __name__ == "__main__":
    unittest.main()
