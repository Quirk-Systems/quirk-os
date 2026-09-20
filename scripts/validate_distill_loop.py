"""Fail-closed conformance for the Quirk distill loop.

Proves, from fixtures alone, that the post-run trigger writes candidates and
only candidates; that promotion requires a receipt with distinct actors and a
complete passing eval suite; that the runtime loader still rejects every
distilled candidate; and that anything distilled into the live tree keeps its
ledger provenance and digests intact. The report is evidence, not admission.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from distill_loop.common import LEDGER_PATH, CANDIDATE_PREFIX, load_schemas, schema_errors, sha256_json, sha256_json_without_keys, source_registration_errors
from distill_loop.context import next_run_context
from distill_loop.evaluator import evaluate_distilled_case
from distill_loop.ledger import append_entry, candidate_state, new_ledger, verify_ledger
from distill_loop.promotion import apply_promotion, validate_promotion_receipt
from distill_loop.trigger import post_run_distill
from sync_control_plane.skill_runtime import load_skill_for_execution, validate_manifest_integrity

EXAMPLE_DIR = Path("examples/distill-loop")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _json(path: Path) -> Any:
    return json.loads(_read(path))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)).replace("\\", "/"): _read(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _synthetic_grant(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "grant_id": f"grant.{manifest['id']}.probe.0001",
        "skill_id": manifest["id"],
        "skill_version": manifest["version"],
        "skill_manifest_sha256": manifest["integrity"]["manifest_sha256"],
        "decision": "approved",
        "admission_ref": "decision.probe.none",
        "requested_by": "operator.probe",
        "approved_by": "human.probe",
        "issued_at": "2026-09-19T00:00:00Z",
        "expires_at": "2026-09-19T02:00:00Z",
        "authority_ceiling": manifest["authority"]["ceiling"],
        "allowed_actions": [manifest["tools"][0]["actions"][0]],
        "purpose": "prove the runtime loader rejects distilled candidates",
    }


def run_example(repo: Path) -> dict[str, Any]:
    schemas = load_schemas(repo)
    registry = _json(repo / "skills" / "registry.json")
    receipt = _json(repo / EXAMPLE_DIR / "run-receipt.json")
    trace = _json(repo / EXAMPLE_DIR / "run-trace.json")
    source_dir = repo / "skills" / receipt["skill_id"]
    source_manifest = _json(source_dir / "manifest.json")
    source_text = _read(source_dir / "SKILL.md")

    distilled = post_run_distill(
        receipt=receipt,
        trace=trace,
        source_manifest=source_manifest,
        source_text=source_text,
        ledger=new_ledger(),
        schemas=schemas,
        registry=registry,
    )
    promotion_receipt = _json(repo / EXAMPLE_DIR / "promotion-receipt.json")
    reviewed_suite = _json(repo / EXAMPLE_DIR / "reviewed-eval-suite.json")
    promoted = None
    if distilled["outcome"] == "distilled":
        promoted = apply_promotion(
            promotion_receipt,
            candidate_manifest=distilled["manifest"],
            candidate_source=distilled["skill_text"],
            eval_suite=reviewed_suite,
            ledger=distilled["ledger"],
            schemas=schemas,
        )
    return {
        "schemas": schemas,
        "registry": registry,
        "receipt": receipt,
        "trace": trace,
        "source_manifest": source_manifest,
        "source_text": source_text,
        "distilled": distilled,
        "promotion_receipt": promotion_receipt,
        "reviewed_suite": reviewed_suite,
        "promoted": promoted,
    }


def validate(repo: Path) -> dict[str, Any]:
    findings: list[dict[str, str]] = []

    def fail(code: str, message: str) -> None:
        findings.append({"level": "error", "code": code, "message": message})

    try:
        schemas = load_schemas(repo)
    except Exception as exc:  # noqa: BLE001 - report and stop
        fail("SCHEMA_INVALID", str(exc))
        return _report(repo, findings, {})

    example = run_example(repo)
    distilled = example["distilled"]
    controls: dict[str, bool] = {}

    # 1. The fixture run distills, and the output is exactly what is committed.
    if distilled["outcome"] != "distilled":
        fail("EXAMPLE_DID_NOT_DISTILL", f"fixture abstained with {distilled['finding_codes']}")
    expected_after_distill = _tree(repo / EXAMPLE_DIR / "expected")
    if distilled["files"] != expected_after_distill:
        drift = sorted(set(distilled["files"]) ^ set(expected_after_distill)) or [
            path for path, text in distilled["files"].items() if expected_after_distill.get(path) != text
        ]
        fail("EXAMPLE_DRIFT", f"regenerated distill output differs from examples/distill-loop/expected: {drift}")

    manifest = distilled.get("manifest")
    skill_text = distilled.get("skill_text")
    if manifest is not None:
        for message in schema_errors(schemas["skill_package"], manifest):
            fail("CANDIDATE_MANIFEST_SCHEMA", message)
        for message in validate_manifest_integrity(manifest, skill_text):
            fail("CANDIDATE_INTEGRITY", message)
        if manifest["status"] != "candidate":
            fail("CANDIDATE_STATUS_BREACH", "distilled output must be candidate")
        if not manifest["id"].startswith(CANDIDATE_PREFIX):
            fail("CANDIDATE_NAMESPACE", "distilled output must live in the quirk-distilled- namespace")
        source_rank = {"observe": 0, "infer": 1, "propose": 2, "execute_bounded": 3}
        if source_rank[manifest["authority"]["ceiling"]] > source_rank[example["source_manifest"]["authority"]["ceiling"]]:
            fail("CANDIDATE_CEILING_BREACH", "distilled ceiling exceeds source ceiling")
        declared = {a for t in example["source_manifest"]["tools"] for a in t["actions"]}
        undeclared = sorted(set(manifest["method"]["moves"]) - declared)
        if undeclared:
            fail("UNDECLARED_MOVE_DISTILLED", f"{undeclared}")
        if "cache_sources" in manifest["method"]["moves"]:
            fail("UNDECLARED_MOVE_DISTILLED", "cache_sources must be excluded")
        for case in distilled["eval_suite"]:
            for message in schema_errors(schemas["skill_eval_case"], case):
                fail("STARTER_EVAL_SCHEMA", f"{case.get('id')}: {message}")
        kinds = {case["kind"] for case in distilled["eval_suite"]}
        controls["starter_suite_blocks_promotion"] = kinds != {"positive", "adversarial", "regression", "authority"}
        if not controls["starter_suite_blocks_promotion"]:
            fail("STARTER_SUITE_TOO_COMPLETE", "the loop must not author adversarial or regression cases itself")

        # 2. The runtime loader rejects the candidate even with a fully formed grant.
        loaded = load_skill_for_execution(manifest, skill_text, _synthetic_grant(manifest), now="2026-09-19T01:00:00Z")
        controls["runtime_loader_rejects_candidate"] = (
            not loaded["loaded"] and "runtime loader rejects unadmitted skill version" in loaded["errors"]
        )
        if not controls["runtime_loader_rejects_candidate"]:
            fail("RUNTIME_LOADER_FAIL_OPEN", f"{loaded}")

        # 3. Registry never carries a distilled candidate.
        registry = _json(repo / "skills" / "registry.json")
        leaked = [entry["id"] for entry in registry.get("skills", []) if entry.get("id", "").startswith(CANDIDATE_PREFIX)]
        if leaked:
            fail("REGISTRY_DISTILLED_LEAK", f"{leaked}")

        # 4. Promotion by receipt, and only by a sound receipt.
        promoted = example["promoted"]
        if promoted is None or promoted["outcome"] != "promoted":
            fail("EXAMPLE_PROMOTION_REFUSED", f"{promoted and promoted['errors']}")
        else:
            expected_after = _tree(repo / EXAMPLE_DIR / "expected-after-promotion")
            expected_context = json.loads(expected_after.pop("next-run-context.json", "{}"))
            if promoted["files"] != expected_after:
                fail("EXAMPLE_PROMOTION_DRIFT", "regenerated promotion output differs from expected-after-promotion")
            context = next_run_context(promoted["ledger"])
            if context != expected_context:
                fail("EXAMPLE_CONTEXT_DRIFT", "regenerated next-run context differs from expected")
            if [item["candidate_id"] for item in context["context_sources"]] != [manifest["id"]]:
                fail("CONTEXT_SELECTION", "promoted candidate must be the only context source")
            if any(item.get("runtime_loadable") for item in context["context_sources"]):
                fail("CONTEXT_RUNTIME_LEAK", "context sources must never claim runtime loadability")
            before = next_run_context(distilled["ledger"])
            controls["unpromoted_candidate_not_loaded"] = (
                before["context_sources"] == [] and before["pending_review"] == [manifest["id"]]
            )
            if not controls["unpromoted_candidate_not_loaded"]:
                fail("CONTEXT_FAIL_OPEN", f"{before}")
            for message in verify_ledger(promoted["ledger"]):
                fail("LEDGER_CHAIN", message)
            if candidate_state(promoted["ledger"], manifest["id"]) != "promoted":
                fail("LEDGER_STATE", "promotion did not fold to promoted")
            # promotion never edits the package or its status
            if promoted["files"].get(f"skills/{manifest['id']}/manifest.json"):
                fail("PROMOTION_MUTATES_PACKAGE", "promotion must not rewrite the candidate package")

        def refused(label: str, receipt_mutation, **overrides) -> None:
            receipt = copy.deepcopy(example["promotion_receipt"])
            receipt_mutation(receipt)
            kwargs = {
                "candidate_manifest": manifest,
                "candidate_source": skill_text,
                "eval_suite": example["reviewed_suite"],
                "ledger": distilled["ledger"],
                "schemas": schemas,
            }
            kwargs.update(overrides)
            errors = validate_promotion_receipt(receipt, **kwargs)
            controls[label] = bool(errors)
            if not errors:
                fail("PROMOTION_FAIL_OPEN", label)

        def _self_approve(receipt): receipt["approved_by"] = receipt["requested_by"]
        def _trigger_approves(receipt): receipt["approved_by"] = "agent.distill-loop"
        def _wrong_digest(receipt): receipt["candidate_manifest_sha256"] = "f" * 64
        def _tampered_body(receipt): receipt["rationale"] = receipt["rationale"] + " (edited after attestation)"
        def _noop(receipt): return None

        refused("self_approved_promotion_refused", _self_approve)
        refused("trigger_approval_refused", _trigger_approves)
        refused("digest_mismatch_refused", _wrong_digest)
        refused("tampered_receipt_refused", _tampered_body)
        starter = distilled["eval_suite"]

        def _starter_digest(receipt): receipt["eval_suite_sha256"] = sha256_json(starter)
        refused("incomplete_eval_suite_refused", _starter_digest, eval_suite=starter)
        refused("unknown_provenance_refused", _noop, ledger=new_ledger())
        tampered_source = skill_text + "\nquiet edit\n"
        refused("tampered_candidate_refused", _noop, candidate_source=tampered_source)
        if promoted and promoted["outcome"] == "promoted":
            refused("double_promotion_refused", _noop, ledger=promoted["ledger"])

        # 5. Blocked and escalated runs never distill.
        blocked_receipt = copy.deepcopy(example["receipt"])
        blocked_receipt["status"] = "blocked"
        blocked = post_run_distill(
            receipt=blocked_receipt, trace=example["trace"], source_manifest=example["source_manifest"],
            source_text=example["source_text"], ledger=new_ledger(), schemas=schemas, registry=example["registry"],
        )
        controls["blocked_run_abstains"] = blocked["outcome"] == "abstained" and "RUN_NOT_COMPLETED" in blocked["finding_codes"]
        if not controls["blocked_run_abstains"]:
            fail("TRIGGER_FAIL_OPEN", "blocked run distilled")
        escalated_receipt = copy.deepcopy(example["receipt"])
        escalated_receipt["authority_ceiling_observed"] = "execute_bounded"
        escalated = post_run_distill(
            receipt=escalated_receipt, trace=example["trace"], source_manifest=example["source_manifest"],
            source_text=example["source_text"], ledger=new_ledger(), schemas=schemas, registry=example["registry"],
        )
        controls["escalated_run_abstains"] = escalated["outcome"] == "abstained" and "CEILING_ESCALATION_OBSERVED" in escalated["finding_codes"]
        if not controls["escalated_run_abstains"]:
            fail("TRIGGER_FAIL_OPEN", "escalated run distilled")
        twice = post_run_distill(
            receipt=example["receipt"], trace=example["trace"], source_manifest=example["source_manifest"],
            source_text=example["source_text"], ledger=distilled["ledger"], schemas=schemas, registry=example["registry"],
        )
        controls["duplicate_receipt_abstains"] = twice["outcome"] == "abstained" and "ALREADY_DISTILLED" in twice["finding_codes"]
        if not controls["duplicate_receipt_abstains"]:
            fail("TRIGGER_FAIL_OPEN", "same receipt distilled twice")
        if blocked["ledger"]["entries"][-1]["kind"] != "abstained":
            fail("ABSTENTION_UNRECEIPTED", "abstentions must append a ledger entry")

        # 5b. Fight card: the bouts that landed before this hardening must all be refused now.
        def trigger_with(receipt_v=None, trace_v=None, manifest_v=None, text_v=None, ledger_v=None, registry_v=None):
            return post_run_distill(
                receipt=receipt_v or example["receipt"], trace=trace_v or example["trace"],
                source_manifest=manifest_v or example["source_manifest"], source_text=text_v or example["source_text"],
                ledger=ledger_v or new_ledger(), schemas=schemas, registry=registry_v or example["registry"],
            )

        collided, _ = append_entry(
            new_ledger(), kind="distilled", recorded_at="2026-09-01T00:00:00Z", actor="agent.distill-loop",
            candidate_id=manifest["id"], source_receipt_id="receipt.other.0001", source_skill_id=example["source_manifest"]["id"],
            source_skill_version=example["source_manifest"]["version"], finding_codes=["DISTILLED_CANDIDATE_WRITTEN"], refs={},
        )
        out = trigger_with(ledger_v=collided)
        controls["id_collision_abstains"] = out["outcome"] == "abstained" and "CANDIDATE_ID_COLLISION" in out["finding_codes"]

        forged_manifest = copy.deepcopy(example["source_manifest"])
        forged_manifest["purpose"] += " (forged)"
        forged_text = example["source_text"] + "\nforged\n"
        from sync_control_plane.skill_runtime import git_blob_sha, manifest_digest
        forged_manifest["integrity"]["source_blob_sha"] = git_blob_sha(forged_text)
        forged_manifest["integrity"]["manifest_sha256"] = "0" * 64
        forged_manifest["integrity"]["manifest_sha256"] = manifest_digest(forged_manifest)
        forged_receipt = copy.deepcopy(example["receipt"])
        forged_receipt["skill_manifest_sha256"] = forged_manifest["integrity"]["manifest_sha256"]
        out = trigger_with(receipt_v=forged_receipt, manifest_v=forged_manifest, text_v=forged_text)
        controls["forged_source_abstains"] = out["outcome"] == "abstained" and "SOURCE_NOT_REGISTERED" in out["finding_codes"]

        ghost_trace = copy.deepcopy(example["trace"])
        ghost_trace["moves"][0]["evidence_ref"] = "ledger.evidence.never-receipted"
        out = trigger_with(trace_v=ghost_trace)
        controls["unreceipted_evidence_excluded"] = (
            "EVIDENCE_UNRECEIPTED" in out["finding_codes"]
            and (out["outcome"] == "abstained" or ghost_trace["moves"][0]["move"] not in out["manifest"]["method"]["moves"])
        )

        inverted = copy.deepcopy(example["receipt"])
        inverted["started_at"] = "2026-09-18T15:00:00Z"
        out = trigger_with(receipt_v=inverted)
        controls["inverted_receipt_time_abstains"] = out["outcome"] == "abstained" and "RECEIPT_TIME_INVALID" in out["finding_codes"]

        if promoted and promoted["outcome"] == "promoted":
            def _same_receipt(receipt): return None
            refused("replayed_promotion_receipt_refused", _same_receipt, ledger=promoted["ledger"])
        def _time_travel(receipt): receipt["decided_at"] = "2026-01-01T00:00:00Z"
        refused("time_travel_promotion_refused", _time_travel)

        posturing = [dict(example["reviewed_suite"][0], id=f"QSK-{i:03d}", kind=kind)
                     for i, kind in enumerate(["positive", "adversarial", "regression", "authority"], start=1)]
        def _posturing(receipt): receipt["eval_suite_sha256"] = sha256_json(posturing)
        refused("posturing_suite_refused", _posturing, eval_suite=posturing)

        escalated_case = dict(example["reviewed_suite"][0])
        escalated_case["input"] = dict(escalated_case["input"], authority_ceiling_observed="execute_bounded")
        verdict = evaluate_distilled_case(escalated_case, manifest)
        controls["eval_ceiling_escalation_refused"] = verdict["result"] == "stop" and "CEILING_ESCALATION" in verdict["finding_codes"]

        if promoted and promoted["outcome"] == "promoted":
            import tempfile
            from distill_loop.common import write_files
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                write_files(root, distilled["files"])
                write_files(root, promoted["files"])
                (root / manifest["quality"]["eval_suite_ref"]).write_text("[]\n", encoding="utf-8")
                swapped = next_run_context(promoted["ledger"], root=root)
                controls["swapped_eval_suite_quarantined"] = swapped["context_sources"] == [] and bool(swapped["quarantined"])

        for label in ("id_collision_abstains", "forged_source_abstains", "unreceipted_evidence_excluded",
                      "inverted_receipt_time_abstains", "eval_ceiling_escalation_refused", "swapped_eval_suite_quarantined"):
            if not controls.get(label):
                fail("FIGHT_CARD_FAIL_OPEN", label)

    # 6. Live tree: ledger chain and every distilled candidate on disk.
    live_ledger_path = repo / LEDGER_PATH
    live_candidates: list[str] = []
    if not live_ledger_path.exists():
        fail("LIVE_LEDGER_MISSING", LEDGER_PATH)
    else:
        live_ledger = _json(live_ledger_path)
        for message in schema_errors(schemas["distill_ledger"], live_ledger):
            fail("LIVE_LEDGER_SCHEMA", message)
        for message in verify_ledger(live_ledger):
            fail("LIVE_LEDGER_CHAIN", message)
        registry = _json(repo / "skills" / "registry.json")
        for entry in live_ledger.get("entries", []):
            if entry.get("kind") != "distilled":
                continue
            probe = {"id": entry.get("source_skill_id"), "version": entry.get("source_skill_version"),
                     "integrity": {"manifest_sha256": entry.get("refs", {}).get("source_manifest_sha256")}}
            for message in source_registration_errors(registry, probe):
                fail("LIVE_LEDGER_SOURCE_UNREGISTERED", f"{entry.get('entry_id')}: {message}")
        for path in sorted((repo / "skills").glob(f"{CANDIDATE_PREFIX}*/manifest.json")):
            candidate_id = path.parent.name
            live_candidates.append(candidate_id)
            candidate_manifest = _json(path)
            candidate_text = _read(path.parent / "SKILL.md")
            for message in schema_errors(schemas["skill_package"], candidate_manifest):
                fail("LIVE_CANDIDATE_SCHEMA", f"{candidate_id}: {message}")
            for message in validate_manifest_integrity(candidate_manifest, candidate_text):
                fail("LIVE_CANDIDATE_INTEGRITY", f"{candidate_id}: {message}")
            if candidate_manifest.get("status") != "candidate":
                fail("LIVE_CANDIDATE_STATUS", f"{candidate_id}: must remain candidate")
            state = candidate_state(live_ledger, candidate_id)
            if state is None:
                fail("LIVE_CANDIDATE_UNLEDGERED", f"{candidate_id}: no distilled ledger entry")
            entry = next((e for e in live_ledger["entries"] if e.get("kind") == "distilled" and e.get("candidate_id") == candidate_id), None)
            if entry and entry["refs"].get("manifest_sha256") != candidate_manifest["integrity"]["manifest_sha256"]:
                fail("LIVE_CANDIDATE_DRIFT", f"{candidate_id}: on-disk digest differs from ledger provenance")
            suite_path = repo / candidate_manifest["quality"]["eval_suite_ref"]
            if not suite_path.exists():
                fail("LIVE_CANDIDATE_EVALS_MISSING", f"{candidate_id}: {candidate_manifest['quality']['eval_suite_ref']}")
        live_context = next_run_context(live_ledger, root=repo)
        if live_context["quarantined"]:
            fail("LIVE_CONTEXT_QUARANTINE", f"{live_context['quarantined']}")

    return _report(repo, findings, {"controls": controls, "live_candidates": live_candidates})


def _report(repo: Path, findings: list[dict[str, str]], extra: dict[str, Any]) -> dict[str, Any]:
    tracked = [
        "schemas/distill-run-trace.schema.json",
        "schemas/distill-ledger.schema.json",
        "schemas/distill-promotion-receipt.schema.json",
        "scripts/distill_loop/trigger.py",
        "scripts/distill_loop/promotion.py",
        "scripts/distill_loop/context.py",
        "scripts/distill_loop/package.py",
        "scripts/distill_loop/ledger.py",
        "scripts/distill_loop/evaluator.py",
        "scripts/validate_distill_loop.py",
        "examples/distill-loop/run-receipt.json",
        "examples/distill-loop/run-trace.json",
        "examples/distill-loop/promotion-receipt.json",
        "examples/distill-loop/reviewed-eval-suite.json",
    ]
    report = {
        "schema_version": "distill-loop-conformance.v1",
        "candidate_id": "distill-loop",
        "candidate_version": "0.1.0",
        "authority_effect": "none",
        "admission_effect": "none",
        "canon_effect": "none",
        "runtime_effect": "none",
        "findings": findings,
        "source_hashes": {path: _sha256_file(repo / path) for path in tracked if (repo / path).exists()},
        "verdict": "FAIL" if findings else "PASS",
        **extra,
    }
    report["receipt_hash"] = sha256_json_without_keys(report, {"receipt_hash"})
    return report


def regenerate_example(repo: Path) -> None:
    from distill_loop.common import write_files

    example = run_example(repo)
    distilled = example["distilled"]
    if distilled["outcome"] != "distilled":
        raise SystemExit(f"fixture abstained: {distilled['finding_codes']}")
    expected = repo / EXAMPLE_DIR / "expected"
    after = repo / EXAMPLE_DIR / "expected-after-promotion"
    for target in (expected, after):
        if target.exists():
            for path in sorted(target.rglob("*"), reverse=True):
                path.unlink() if path.is_file() else path.rmdir()
    write_files(expected, distilled["files"])
    promoted = example["promoted"]
    if promoted is None or promoted["outcome"] != "promoted":
        raise SystemExit(f"promotion refused: {promoted and promoted['errors']}")
    write_files(after, promoted["files"])
    context = next_run_context(promoted["ledger"])
    (after / "next-run-context.json").write_text(json.dumps(context, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--regenerate-example", action="store_true",
                        help="rewrite examples/distill-loop/expected* from the fixtures, then validate")
    args = parser.parse_args()
    repo = args.repo.resolve()

    if args.regenerate_example:
        regenerate_example(repo)

    report = validate(repo)
    if args.output:
        output = args.output if args.output.is_absolute() else repo / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    if report["verdict"] != "PASS":
        for finding in report["findings"]:
            print(f"{finding['level'].upper()} {finding['code']}: {finding['message']}", file=sys.stderr)
    if args.require_pass and report["verdict"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
