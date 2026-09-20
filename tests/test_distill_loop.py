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
    evaluate_distilled_case,
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
        self.registry = _json(ROOT / "skills" / "registry.json")

    def distill(self, *, receipt=None, trace=None, ledger=None, source_manifest=None, source_text=None, registry=None):
        return post_run_distill(
            receipt=receipt or self.receipt,
            trace=trace or self.trace,
            source_manifest=source_manifest or self.source_manifest,
            source_text=source_text or self.source_text,
            ledger=ledger or new_ledger(),
            schemas=self.schemas,
            registry=registry or self.registry,
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
            ledger=new_ledger(), schemas=self.fx.schemas, registry=self.fx.registry,
        )
        # a distilled candidate is never in the registry, so the registry gate fires first
        self.assertTrue({"SOURCE_NOT_REGISTERED", "RECURSIVE_DISTILLATION_DENIED"} & set(outcome["finding_codes"]))
        self.assertEqual(outcome["outcome"], "abstained")


class FightCardTests(unittest.TestCase):
    """Each test is one bout that landed on main before hardening and must be refused now."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.fx = DistillFixture()
        cls.distilled = cls.fx.distill()
        cls.promoted = apply_promotion(
            cls.fx.promotion_receipt, candidate_manifest=cls.distilled["manifest"], candidate_source=cls.distilled["skill_text"],
            eval_suite=cls.fx.reviewed_suite, ledger=cls.distilled["ledger"], schemas=cls.fx.schemas,
        )
        assert cls.promoted["outcome"] == "promoted", cls.promoted["errors"]

    def _validate(self, receipt=None, **overrides):
        kwargs = {
            "candidate_manifest": self.distilled["manifest"], "candidate_source": self.distilled["skill_text"],
            "eval_suite": self.fx.reviewed_suite, "ledger": self.distilled["ledger"], "schemas": self.fx.schemas,
        }
        kwargs.update(overrides)
        return validate_promotion_receipt(receipt or self.fx.promotion_receipt, **kwargs)

    def test_k1_candidate_id_collision_abstains(self) -> None:
        ledger, _ = append_entry(
            new_ledger(), kind="distilled", recorded_at="2026-09-01T00:00:00Z", actor="agent.distill-loop",
            candidate_id=self.distilled["manifest"]["id"], source_receipt_id="receipt.other.0001",
            source_skill_id=self.fx.source_manifest["id"], source_skill_version=self.fx.source_manifest["version"],
            finding_codes=["DISTILLED_CANDIDATE_WRITTEN"], refs={},
        )
        out = self.fx.distill(ledger=ledger)
        self.assertEqual(out["outcome"], "abstained")
        self.assertIn("CANDIDATE_ID_COLLISION", out["finding_codes"])

    def test_k2_cli_refuses_to_write_over_a_forked_ledger(self) -> None:
        import subprocess
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            from distill_loop import write_files

            write_files(root, self.distilled["files"])
            # fork: the on-disk ledger moves after the operation read it
            forked, _ = append_entry(
                self.distilled["ledger"], kind="abstained", recorded_at="2026-09-19T00:00:00Z", actor="agent.distill-loop",
                candidate_id=None, source_receipt_id="receipt.elsewhere.0001", source_skill_id="quirk-x",
                source_skill_version="0.1.0", finding_codes=["RUN_NOT_COMPLETED"], refs={},
            )
            # promote computes against the ledger it reads; simulate the race by racing the file after read
            # via a stale copy: write the fork *before* promote reads means no fork, so instead exercise the guard directly.
            from distill_loop.__main__ import _write_guarded

            stale_result = {"files": {"skills/distill-ledger.json": "{}"}, "ledger_input_sha256": self.distilled["ledger"]["ledger_sha256"]}
            (root / "skills" / "distill-ledger.json").write_text(json.dumps(forked), encoding="utf-8")
            self.assertEqual(_write_guarded(root, stale_result), 1)
            self.assertEqual(json.loads((root / "skills" / "distill-ledger.json").read_text())["ledger_sha256"], forked["ledger_sha256"])
            fresh_result = {"files": {"skills/distill-ledger.json": json.dumps(forked)}, "ledger_input_sha256": forked["ledger_sha256"]}
            self.assertEqual(_write_guarded(root, fresh_result), 0)

    def test_k3_promotion_receipt_is_single_use(self) -> None:
        errors = self._validate(ledger=self.promoted["ledger"])
        self.assertTrue(any("single use" in error for error in errors), errors)

    def test_k4_unreceipted_evidence_is_excluded(self) -> None:
        trace = copy.deepcopy(self.fx.trace)
        trace["moves"][0]["evidence_ref"] = "ledger.evidence.never-receipted"
        out = self.fx.distill(trace=trace)
        self.assertIn("EVIDENCE_UNRECEIPTED", out["finding_codes"])
        self.assertEqual(out["outcome"], "distilled")
        self.assertNotIn(trace["moves"][0]["move"], out["manifest"]["method"]["moves"])
        self.assertIn(trace["moves"][0]["move"], out["ledger_entry"]["refs"]["excluded_moves"])

    def test_k5_source_outside_registry_abstains(self) -> None:
        from sync_control_plane.skill_runtime import git_blob_sha, manifest_digest

        forged = copy.deepcopy(self.fx.source_manifest)
        forged["purpose"] += " (forged)"
        text = self.fx.source_text + "\nforged\n"
        forged["integrity"]["source_blob_sha"] = git_blob_sha(text)
        forged["integrity"]["manifest_sha256"] = "0" * 64
        forged["integrity"]["manifest_sha256"] = manifest_digest(forged)
        receipt = copy.deepcopy(self.fx.receipt)
        receipt["skill_manifest_sha256"] = forged["integrity"]["manifest_sha256"]
        out = self.fx.distill(receipt=receipt, source_manifest=forged, source_text=text)
        self.assertEqual(out["outcome"], "abstained")
        self.assertIn("SOURCE_NOT_REGISTERED", out["finding_codes"])

    def test_k5b_tampered_registry_is_not_trusted(self) -> None:
        registry = copy.deepcopy(self.fx.registry)
        registry["skills"][0]["manifest_sha256"] = "f" * 64
        out = self.fx.distill(registry=registry)
        self.assertIn("SOURCE_NOT_REGISTERED", out["finding_codes"])

    def test_k6_time_travel_promotion_refused(self) -> None:
        receipt = attest_promotion({**self.fx.promotion_receipt, "decided_at": "2026-01-01T00:00:00Z"})
        errors = self._validate(receipt)
        self.assertTrue(any("before the candidate was distilled" in error for error in errors), errors)

    def test_k7_receipt_finished_before_started_abstains(self) -> None:
        receipt = copy.deepcopy(self.fx.receipt)
        receipt["started_at"] = "2026-09-18T15:00:00Z"
        out = self.fx.distill(receipt=receipt)
        self.assertEqual(out["outcome"], "abstained")
        self.assertIn("RECEIPT_TIME_INVALID", out["finding_codes"])

    def test_s1_posturing_suite_refused(self) -> None:
        from distill_loop.common import sha256_json

        positive = self.fx.reviewed_suite[0]
        posturing = [dict(positive, id=f"QSK-{i:03d}", kind=kind)
                     for i, kind in enumerate(["positive", "adversarial", "regression", "authority"], start=1)]
        receipt = attest_promotion({**self.fx.promotion_receipt, "eval_suite_sha256": sha256_json(posturing)})
        errors = self._validate(receipt, eval_suite=posturing)
        self.assertTrue(any("does not match its kind" in error for error in errors), errors)
        self.assertTrue(any("distinct scenarios" in error for error in errors), errors)

    def test_s2_eval_refuses_ceiling_escalation(self) -> None:
        case = dict(self.fx.reviewed_suite[0])
        case["input"] = dict(case["input"], authority_ceiling_observed="execute_bounded")
        verdict = evaluate_distilled_case(case, self.distilled["manifest"])
        self.assertEqual(verdict["result"], "stop")
        self.assertIn("CEILING_ESCALATION", verdict["finding_codes"])
        missing = dict(self.fx.reviewed_suite[0])
        missing["input"] = {k: v for k, v in missing["input"].items() if k != "authority_ceiling_observed"}
        self.assertNotEqual(evaluate_distilled_case(missing, self.distilled["manifest"])["result"], "pass")

    def test_s3_swapped_eval_suite_is_quarantined(self) -> None:
        import tempfile

        from distill_loop import write_files

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_files(root, self.distilled["files"])
            write_files(root, self.promoted["files"])
            self.assertTrue(next_run_context(self.promoted["ledger"], root=root)["context_sources"])
            (root / self.distilled["manifest"]["quality"]["eval_suite_ref"]).write_text("[]\n", encoding="utf-8")
            context = next_run_context(self.promoted["ledger"], root=root)
            self.assertEqual(context["context_sources"], [])
            self.assertTrue(any("eval suite" in problem for problem in context["quarantined"][0]["problems"]))



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
