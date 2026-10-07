#!/usr/bin/env python3
"""Executable admission conformance for Quirk Sync Control Plane v0.2.

The runner proves candidate eligibility. It never performs human admission,
activates a manifest, promotes Canon, or deploys production.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

HERE = Path(__file__).resolve()
ROOT_DEFAULT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))

from sync_control_plane.mappers import (  # noqa: E402
    binding_canonical_to_runtime,
    binding_runtime_to_canonical,
    receipt_canonical_to_runtime,
    receipt_runtime_to_canonical,
)
from sync_control_plane.policy import evaluate_fixture, validate_manifest_admission, validate_manifest_structure  # noqa: E402
from sync_control_plane.skill_runtime import (  # noqa: E402
    build_model_tool_request_receipt,
    map_skill_tools_to_runtime_bindings,
    resolve_model_visible_tools,
    serialize_model_request,
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(schema: dict[str, Any], instance: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [error.message for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.path))]


def _function_body(sql: str, name: str) -> str:
    """The text of one `create or replace function <name>` definition, or ''.

    Needed because a token can appear in a migration without appearing in the
    function that has to enforce it. The approver predicate is written twice in
    `20261003090000`: once in the rule function and once, previously, in the
    pre-install audit, so a whole-file search for it stayed satisfied even if
    the enforcing definition had lost it.
    """
    lower = sql.lower()
    # The LAST definition, because applying the migrations in order leaves that
    # one installed. `guard_manifest_activation` is defined twice across these
    # files, and reading the earlier one would report the older body's contents.
    start = lower.rfind(f"create or replace function quirk_sync.{name}")
    if start < 0:
        return ""
    end = lower.find("end $$;", start)
    return lower[start : end + len("end $$;")] if end > start else lower[start:]



def _privilege_lanes_hold(sql: str) -> bool:
    """The guard is SECURITY DEFINER with pg_temp last; the rule function is not."""
    guard = _function_body(sql, "guard_manifest_activation")
    rule = _function_body(sql, "manifest_activation_violation")
    header = guard.split("as $$", 1)[0]
    path = next(
        (line for line in header.splitlines() if "search_path" in line), ""
    )
    return (
        "security definer" in header
        and path.rstrip().rstrip(",").split(",")[-1].strip().startswith("pg_temp")
        and "security definer" not in rule.split("as $$", 1)[0]
    )

def static_migration_checks(sql: str) -> dict[str, bool]:
    """Presence checks over the concatenated migration text.

    These prove a token appears in the migrations — and, where the name says
    `rule_`, inside the definition that has to enforce it. None of them proves
    what a database currently has installed. A static read cannot, so these
    checks are a spelling test; the behavioural evidence comes from the
    `database-guard` job in `.github/workflows/sync-control-plane-conformance.yml`,
    which applies the migrations to PostgreSQL, reads the installed guard back,
    and runs `supabase/tests/manifest_activation_guard.run.sql`.
    """
    lower = sql.lower()
    rules = _function_body(sql, "manifest_activation_violation")
    scoped = {
        # Scoped to the rule function, so the audit query cannot satisfy them.
        "rule_independent_human_approver": "approved_by !~ '^human\\.[a-z0-9._-]+$'" in rules,
        "rule_well_formed_requester": "requested_by !~ '^(human|agent|service|system)\\.[a-z0-9._-]+$'" in rules,
        "rule_null_safe_rights_review": "->>'outcome' is distinct from 'approved'" in rules,
        "rule_null_safe_trigger_contract": "->>'collision_behavior' is distinct from 'block'" in rules,
        # The guard must delegate to the rule function rather than restate it.
        "guard_delegates_to_rules": "manifest_activation_violation(new)"
        in _function_body(sql, "guard_manifest_activation"),
        # Privilege lanes, in the LAST definition of each function. The guard
        # runs as its owner so that whether it can judge a row does not depend
        # on which role writes, with pg_temp pinned last against definer
        # hijacking. The rule function stays invoker: it reads only its
        # argument and has no use for owner reach. Checked here and again on
        # the installed functions in CI, because the service_role grant on the
        # rule function masks the guard losing SECURITY DEFINER, and a
        # `CREATE OR REPLACE` that omits it resets it silently.
        "rule_privilege_lanes": _privilege_lanes_hold(sql),
        # The audit must be driven by the same function, not its own copy.
        "audit_uses_rule_function": "where quirk_sync.manifest_activation_violation(m) is not null" in lower,
        "audit_holds_write_lock": "lock table quirk_sync.manifest_registry in exclusive mode" in lower,
        # No migration may open its own transaction. `supabase db push` applies
        # each file inside one, so an in-file `commit` closes the runner's
        # transaction and the push can report success while leaving the
        # migration unrecorded. The write lock above is what keeps the
        # requirement honest: PostgreSQL rejects `LOCK TABLE` outside a
        # transaction block, so a runner that does not wrap the file fails
        # there rather than splitting the audit from the cutover.
        "no_migration_opens_a_transaction": not any(
            line.strip() in {"begin;", "commit;", "begin transaction;", "end transaction;"}
            for line in lower.splitlines()
        ),
        # The guard's inner call is checked against the invoking role, and
        # every other function in this schema is revoked from the browser roles
        # and granted to `service_role` explicitly. Without the grant, a
        # `service_role` write raises `permission denied for function
        # manifest_activation_violation` from inside the trigger and no row can
        # be written, valid or not.
        "rule_function_granted_to_service_role": "grant execute on function\n  quirk_sync.manifest_activation_violation(quirk_sync.manifest_registry)\n  to service_role;"
        in lower,
    }
    tokens = {
        "manifest_guard": "guard_manifest_activation",
        "append_only_receipts": "prevent_append_only_mutation",
        "transition_ledger": "manifest_transition_ledger",
        "proposed_move_store": "create table if not exists quirk_sync.proposed_moves",
        "atomic_outbox_claim": "claim_projection_outbox",
        "bounded_dead_letter": "dead_lettered_at",
        "drift_controller": "observe_binding",
        "projection_rebuild": "rebuild_projection_snapshot",
        "cloudflare_binding": "'cloudflare'",
        "browser_roles_revoked": "revoke all on schema quirk_sync from authenticated",
    }
    return {**{name: token in lower for name, token in tokens.items()}, **scoped}


def database_guard_job_checks(workflow_path: Path) -> dict[str, bool]:
    """Assert the workflow still contains the job that executes the DB guard.

    The migration static checks above are a spelling test, and the admission
    evidence now says the behavioural proof comes from a CI job. Deleting that
    job would make the document false again with nothing failing, which is the
    defect class this whole candidate is about. These read the workflow and
    check that the job is there and still runs the cases through the driver
    that discards its rows. They prove the workflow is spelled that way; only a
    run of the job proves PostgreSQL refused anything.
    """
    try:
        workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {
            "ci_declares_database_guard_job": False,
            "ci_runs_guard_cases": False,
            "ci_reads_installed_guard_back": False,
            "ci_runs_guard_cases_as_service_role": False,
            "ci_evidence_depends_on_database_guard": False,
            "ci_decision_fails_when_guard_fails": False,
            "ci_discards_tracked_decision": False,
            "ci_rejects_stale_committed_decision": False,
            "ci_path_filter_covers_job_inputs": False,
        }
    jobs = (workflow or {}).get("jobs", {})
    trigger = (workflow or {}).get(True) or (workflow or {}).get("on") or {}
    trigger_paths = ((trigger.get("pull_request") or {}).get("paths")) or []
    job = jobs.get("database-guard") or {}
    decision = jobs.get("candidate-conformance") or {}
    needs = decision.get("needs")
    needs = [needs] if isinstance(needs, str) else list(needs or [])
    decision_runs = "\n".join(
        str(step.get("run", "")) for step in decision.get("steps", []) if isinstance(step, dict)
    )
    decision_envs = "\n".join(
        str(step.get("env", "")) for step in decision.get("steps", []) if isinstance(step, dict)
    )
    runs = "\n".join(
        str(step.get("run", "")) for step in job.get("steps", []) if isinstance(step, dict)
    )
    return {
        "ci_declares_database_guard_job": bool(job) and "postgres" in job.get("services", {}),
        # The driver, not the cases file: `--single-transaction` on the cases
        # file commits the one admitted manifest instead of discarding it.
        "ci_runs_guard_cases": "manifest_activation_guard.run.sql" in runs,
        "ci_reads_installed_guard_back": "pg_get_functiondef" in runs
        and "manifest_activation_violation(new)" in runs,
        # In its own step, so its own psql session. EXECUTE on the rule
        # function is checked when PL/pgSQL builds the trigger's cached plan,
        # which makes the privilege check session-order dependent: run after
        # the superuser cases and these pass with no grant at all.
        # Eligibility must be downstream of the behavioural proof. Run in
        # parallel, the Python job computes and uploads an
        # `ELIGIBLE_FOR_HUMAN_ADMISSION` decision even when the database guard
        # failed, and nothing in the artifact can contradict it: its
        # `migration_hardening_complete` only checks that this job is spelled
        # in the workflow.
        # `bool(job)` as well, because a `needs:` naming a job that no longer
        # exists is not a dependency on anything. Without that conjunct,
        # deleting the job left this check green.
        "ci_evidence_depends_on_database_guard": bool(job) and "database-guard" in needs,
        # A bare `needs:` is not enough. A job whose dependency failed reports
        # as *skipped*, and GitHub counts a skipped required status check as a
        # successful one, so `needs:` alone would turn a red guard into a green
        # required check. The job must always run and fail explicitly instead.
        "ci_decision_fails_when_guard_fails": str(decision.get("if", "")).strip() == "always()"
        and "needs.database-guard.result" in decision_envs
        and "exit 1" in decision_runs,
        # Checkout restores the committed decision, which records a pass. With
        # the upload on `always()`, any failure before the validator runs would
        # ship that committed file as this run's evidence.
        "ci_discards_tracked_decision": "rm -f evals/sync-control-plane/conformance-results.json"
        in decision_runs,
        # The doc-digest test compares the committed document to the committed
        # artifact, so a change altering the payload while leaving both
        # untouched compares stale to stale and passes. This job must therefore
        # diff the regenerated artifact against the committed blob: without it,
        # green CI can merge an evidence of record that the tree no longer
        # produces.
        "ci_rejects_stale_committed_decision": "git diff --exit-code -- evals/sync-control-plane/conformance-results.json"
        in decision_runs,
        # A path-filtered workflow runs only when a changed path matches, so a
        # test or step that consumes a file is dead weight unless that file is
        # one of those paths. Three such dependencies are not obviously related
        # to this workflow's name and were each missing at some point: the
        # verification recipe the drift test reads, every migration the guard
        # job applies (not just the `*sync_control_plane*` ones — the loop
        # globs them all), and the admission evidence the digest test reads.
        #
        # This is an enumerated list, not a derived one. It cannot know about a
        # dependency nobody added to it, which is the limit of the check rather
        # than a property of the workflow.
        "ci_path_filter_covers_job_inputs": all(
            required in trigger_paths
            for required in (
                ".claude/skills/verify/SKILL.md",
                "supabase/migrations/**",
                "docs/sync-control-plane/**",
            )
        ),
        "ci_runs_guard_cases_as_service_role": any(
            "manifest_activation_guard.service_role.sql" in str(step.get("run", ""))
            and "manifest_activation_guard.run.sql" not in str(step.get("run", ""))
            for step in job.get("steps", [])
            if isinstance(step, dict)
        ),
    }


def projection_job_checks(workflow_path: Path) -> dict[str, bool]:
    """Workflow presence only; executed PostgreSQL evidence is separate."""
    try:
        workflow = yaml.safe_load(workflow_path.read_text()) or {}
    except (OSError, yaml.YAMLError):
        workflow = {}
    trigger = workflow.get(True) or workflow.get("on") or {}
    paths = ((trigger.get("pull_request") or {}).get("paths")) or []
    steps = ((workflow.get("jobs") or {}).get("database-guard") or {}).get("steps", [])
    runs = "\n".join(str(step.get("run", "")) for step in steps)
    return {
        "ci_runs_verified_projection_cases": "-f supabase/tests/manifest_verified_projection.sql" in runs,
        "ci_proves_legacy_projection_cutover_refusal": "manifest_verified_projection.cutover.sql" in runs
        and 'test "$result" -eq 3' in runs and "legacy active manifests need human disposition" in runs,
        "ci_stages_projection_cutover": ' > "20261004140000"' in runs
        and ' < "20261004140000"' in runs
        and 0 <= runs.find("manifest_activation_guard.service_role.sql") < runs.find(' < "20261004140000"'),
        "ci_paths_cover_projection_inputs": all(path in paths for path in (
            "scripts/manifest_admission.py", "scripts/prove_manifest_boundaries.py", "tests/test_manifest_admission.py",
            "decisions/**", "supabase/tests/manifest_verified_projection.sql",
            "supabase/tests/manifest_verified_projection.cutover.sql")),
    }


def mapping_roundtrip(binding_schema: dict[str, Any], receipt_schema: dict[str, Any]) -> dict[str, Any]:
    runtime_binding = {
        "binding_key": "binding.github.example",
        "schema_version": "source-binding.v2",
        "platform": "github",
        "external_id": "Quirk-Systems/quirk-os#5",
        "external_url": "https://github.com/Quirk-Systems/quirk-os/pull/5",
        "authority_class": "canonical",
        "sync_direction": "bidirectional_proposal",
        "state": "candidate",
        "last_seen_hash": "a" * 64,
        "freshness": {"status": "fresh"},
        "cursor": {},
        "metadata": {},
    }
    canonical_binding = binding_runtime_to_canonical(runtime_binding, object_key="program.quirk-sync-control-plane")
    binding_errors = validate(binding_schema, canonical_binding)
    rebound = binding_canonical_to_runtime(canonical_binding, object_id="00000000-0000-0000-0000-000000000001")

    runtime_receipt = {
        "schema_version": "sync-run-receipt.v2",
        "receipt_key": "receipt.mapping.test",
        "idempotency_key": "mapping:test:0001",
        "run_type": "validate",
        "status": "succeeded",
        "actor_ref": "human.bryan",
        "authority_ref": "grant.mapping.test",
        "started_at": "2026-08-12T00:00:00Z",
        "completed_at": "2026-08-12T00:00:01Z",
        "input_refs": [],
        "output_refs": [],
        "evidence_refs": ["test://mapping"],
        "metrics": {},
        "receipt_hash": "b" * 64,
        "outcome": {},
    }
    canonical_receipt = receipt_runtime_to_canonical(runtime_receipt)
    receipt_errors = validate(receipt_schema, canonical_receipt)
    rereceipt = receipt_canonical_to_runtime(canonical_receipt)
    return {
        "binding_schema_errors": binding_errors,
        "receipt_schema_errors": receipt_errors,
        "binding_roundtrip_stable": rebound["binding_key"] == runtime_binding["binding_key"] and rebound["platform"] == runtime_binding["platform"],
        "receipt_roundtrip_stable": rereceipt["receipt_key"] == runtime_receipt["receipt_key"] and rereceipt["idempotency_key"] == runtime_receipt["idempotency_key"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--output", type=Path, default=Path("evals/sync-control-plane/conformance-results.json"))
    parser.add_argument("--metrics-output", type=Path, help="Optional JSON output path for performance/workload metrics.")
    parser.add_argument("--write-step-summary", action="store_true", help="Append metrics to GitHub step summary when available.")
    parser.add_argument("--require-admit", action="store_true", help="Exit nonzero unless candidate is eligible for a human admission decision.")
    args = parser.parse_args()
    repo = args.repo.resolve()
    started = time.perf_counter()

    schemas = {
        "manifest": load_json(repo / "schemas/runtime-manifest.schema.json"),
        "binding": load_json(repo / "schemas/source-binding.schema.json"),
        "receipt": load_json(repo / "schemas/sync-run-receipt.schema.json"),
        "transition": load_json(repo / "schemas/manifest-transition.schema.json"),
        "decision": load_json(repo / "schemas/sync-decision.schema.json"),
        "projection": load_json(repo / "schemas/projection-envelope.schema.json"),
    }
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)

    fixtures = load_json(repo / "evals/sync-control-plane/fixtures.json")
    results = []
    for fixture in fixtures["fixtures"]:
        case = load_json(repo / fixture["case_ref"])
        actual = evaluate_fixture(fixture["name"], case)
        passed = actual.get("action") == fixture["expected"]
        results.append({**fixture, "passed": passed, "actual": actual})

    valid_active = load_json(repo / "evals/sync-control-plane/valid-active-manifest.json")
    valid_schema_errors = validate(schemas["manifest"], valid_active)
    valid_structure_errors = validate_manifest_structure(valid_active)
    valid_policy_errors = validate_manifest_admission(valid_active)

    self_promotion = load_json(repo / "evals/sync-control-plane/cases/SCP-011.json")["manifest"]
    self_schema_errors = validate(schemas["manifest"], self_promotion)
    self_policy_errors = validate_manifest_admission(self_promotion)

    rights_unclear = {
        **valid_active,
        "manifest_key": "capability.data-productization",
        "manifest_kind": "capability",
        "version": "1.0.1",
        "domains": ["data_productization"],
        "rights_review": {
            "outcome": "deferred",
            "license_verified": False,
            "privacy_review": "blocked",
            "provenance_complete": False,
            "reviewed_by": "human.bryan",
            "reviewed_at": "2026-08-12T00:00:00Z",
            "evidence_refs": ["rights://blocked"],
        },
    }
    rights_schema_errors = validate(schemas["manifest"], rights_unclear)

    collision = {
        **valid_active,
        "manifest_key": "orchestrator.collision",
        "manifest_kind": "orchestrator",
        "version": "1.0.1",
        "skill_refs": ["skill.alpha", "skill.beta"],
    }
    collision.pop("trigger_contract", None)
    collision_schema_errors = validate(schemas["manifest"], collision)

    # Every sync-control-plane migration, not a hardcoded timestamp prefix. The
    # previous glob pinned `2026081203000*`, so a migration added later was not
    # read at all: `manifest_guard` still matched `guard_manifest_activation` in
    # the August file and `migration_hardening_complete` stayed true however the
    # newer migration was written. Broadening is safe because every static check
    # tests for a token's presence, so more SQL can only satisfy more of them.
    migration_paths = sorted((repo / "supabase/migrations").glob("*_sync_control_plane_*.sql"))
    migration_sql = "\n".join(path.read_text(encoding="utf-8") for path in migration_paths)
    static = static_migration_checks(migration_sql)
    static.update(
        database_guard_job_checks(repo / ".github/workflows/sync-control-plane-conformance.yml")
    )
    static.update(projection_job_checks(repo / ".github/workflows/sync-control-plane-conformance.yml"))
    mappings = mapping_roundtrip(schemas["binding"], schemas["receipt"])

    tool_registry_schema = load_json(repo / "schemas/tool-registry.schema.json")
    model_tool_receipt_schema = load_json(repo / "schemas/model-tool-request-receipt.schema.json")
    Draft202012Validator.check_schema(tool_registry_schema)
    Draft202012Validator.check_schema(model_tool_receipt_schema)
    tool_registry = load_json(repo / "evals/sync-control-plane/tool-registry.v1.json")
    model_tool_fixture = load_json(repo / "evals/sync-control-plane/model-tool-request.fixture.json")
    tool_registry_errors = validate(tool_registry_schema, tool_registry)
    model_tool_manifest_errors = validate(schemas["manifest"], model_tool_fixture["manifest"])
    canonical_tool_mapping = map_skill_tools_to_runtime_bindings(
        {"tools": [{"name": "quirk_runtime", "actions": ["read_sources"], "required": True}]},
        tool_registry,
    )
    tool_resolution = resolve_model_visible_tools(model_tool_fixture["manifest"], tool_registry)
    request = serialize_model_request(
        model_tool_fixture["manifest"],
        tool_registry,
        model="conformance-proof-model",
        messages=model_tool_fixture["messages"],
    ) if tool_resolution["resolved"] else None
    tool_receipt = build_model_tool_request_receipt(
        request,
        receipt_id="receipt.sync-control-plane.model-tool-proof.0001",
        serialized_at="2026-09-25T00:00:00Z",
    ) if request else None
    tool_receipt_errors = validate(model_tool_receipt_schema, tool_receipt) if tool_receipt else ["request was not serialized"]
    emitted_tool_names = [tool["function"]["name"] for tool in request["tools"]] if request else []
    allowed_schema_present = request is not None and "source_refs" in request["tools"][0]["function"]["parameters"]["properties"]
    forbidden_schema_absent = request is not None and "quirk_runtime__promote_canon" not in emitted_tool_names and "object_ref" not in request["tools"][0]["function"]["parameters"]["properties"]

    checks = {
        "fixture_count_11": len(results) == 11,
        "all_fixtures_pass": all(item["passed"] for item in results),
        "valid_active_manifest_passes_schema": not valid_schema_errors,
        "synthetic_active_fixture_passes_structure": not valid_structure_errors,
        "synthetic_approval_is_not_live_authority": "trusted approval verifier and activation context required" in valid_policy_errors,
        "self_promotion_rejected_by_schema_or_policy": bool(self_schema_errors or self_policy_errors),
        "rights_unclear_rejected": bool(rights_schema_errors),
        "trigger_collision_rejected": bool(collision_schema_errors),
        "migration_hardening_complete": all(static.values()),
        "mapping_roundtrip_passes": not mappings["binding_schema_errors"] and not mappings["receipt_schema_errors"] and mappings["binding_roundtrip_stable"] and mappings["receipt_roundtrip_stable"],
        "tool_registry_passes_schema": not tool_registry_errors,
        "model_tool_manifest_passes_schema": not model_tool_manifest_errors,
        "canonical_tool_mapping_resolves": canonical_tool_mapping["mapped"] and canonical_tool_mapping["bindings"] == model_tool_fixture["manifest"]["tools"],
        "model_tool_projection_resolves": tool_resolution["resolved"],
        "allowed_tool_schema_present": allowed_schema_present,
        "forbidden_tool_schema_absent": forbidden_schema_absent,
        "model_tool_receipt_logs_unknown_metrics": not tool_receipt_errors and tool_receipt["measurement_state"] == "not_observed",
    }
    eligible = all(checks.values())
    payload = {
        "suite_id": "eval.sync-control-plane.conformance.v0.2",
        "decision": "ELIGIBLE_FOR_HUMAN_ADMISSION" if eligible else "REVISE",
        "automatic_activation": False,
        "approval_verification": "synthetic fixture only; live admission is separately verified",
        "database_verification": "projection of the admitted Python gate",
        "checks": checks,
        "fixtures": results,
        "schema_attacks": {
            "valid_active_schema_errors": valid_schema_errors,
            "valid_active_structure_errors": valid_structure_errors,
            "valid_active_policy_errors": valid_policy_errors,
            "self_promotion_schema_errors": self_schema_errors,
            "self_promotion_policy_errors": self_policy_errors,
            "rights_unclear_schema_errors": rights_schema_errors,
            "trigger_collision_schema_errors": collision_schema_errors,
        },
        "migration_static": static,
        "mapping_proof": mappings,
        "model_tool_schema_proof": {
            "tool_registry_errors": tool_registry_errors,
            "manifest_schema_errors": model_tool_manifest_errors,
            "canonical_mapping": canonical_tool_mapping,
            "resolution": tool_resolution,
            "serialized_request": request,
            "receipt": tool_receipt,
            "receipt_schema_errors": tool_receipt_errors,
        },
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["content_hash_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    output = args.output if args.output.is_absolute() else repo / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    elapsed = time.perf_counter() - started
    metrics = {
        "validator": "validate_sync_control_plane.py",
        "elapsed_seconds": elapsed,
        "fixture_count": len(results),
        "schema_count": len(schemas),
        "migration_file_count": len(migration_paths),
        "eligible": eligible,
    }
    if args.metrics_output:
        metrics_output = args.metrics_output if args.metrics_output.is_absolute() else repo / args.metrics_output
        metrics_output.parent.mkdir(parents=True, exist_ok=True)
        metrics_output.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    if args.write_step_summary and os.environ.get("GITHUB_STEP_SUMMARY"):
        summary_lines = [
            "## validate_sync_control_plane performance",
            "",
            "| metric | value |",
            "| --- | ---: |",
            f"| elapsed_seconds | {metrics['elapsed_seconds']:.6f} |",
            f"| fixture_count | {metrics['fixture_count']} |",
            f"| schema_count | {metrics['schema_count']} |",
            f"| migration_file_count | {metrics['migration_file_count']} |",
            f"| eligible | {str(metrics['eligible']).lower()} |",
            "",
        ]
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as handle:
            handle.write("\n".join(summary_lines))
    print(json.dumps(payload, indent=2))
    return 1 if args.require_admit and not eligible else 0


if __name__ == "__main__":
    raise SystemExit(main())
