from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sync_control_plane.mappers import (  # noqa: E402
    binding_canonical_to_runtime,
    binding_runtime_to_canonical,
    receipt_canonical_to_runtime,
    receipt_runtime_to_canonical,
)
from sync_control_plane.policy import evaluate_fixture, validate_manifest_admission  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
from validate_sync_control_plane import _privilege_lanes_hold, database_guard_job_checks  # noqa: E402


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class SyncControlPlaneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest_schema = load("schemas/runtime-manifest.schema.json")
        cls.binding_schema = load("schemas/source-binding.schema.json")
        cls.receipt_schema = load("schemas/sync-run-receipt.schema.json")
        cls.fixtures = load("evals/sync-control-plane/fixtures.json")

    def validate(self, schema, instance):
        return list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(instance))

    def test_all_eleven_fixtures(self):
        self.assertEqual(11, len(self.fixtures["fixtures"]))
        for fixture in self.fixtures["fixtures"]:
            with self.subTest(fixture=fixture["id"]):
                result = evaluate_fixture(fixture["name"], load(fixture["case_ref"]))
                self.assertEqual(fixture["expected"], result["action"])

    def test_valid_active_manifest(self):
        manifest = load("evals/sync-control-plane/valid-active-manifest.json")
        self.assertEqual([], self.validate(self.manifest_schema, manifest))
        self.assertEqual([], validate_manifest_admission(manifest))

    def test_self_promotion_rejected(self):
        manifest = load("evals/sync-control-plane/cases/SCP-011.json")["manifest"]
        # The manifest is schema-valid, so the rejection has to come from policy.
        self.assertEqual([], self.validate(self.manifest_schema, manifest))
        self.assertIn(
            "activation requires approval by an independent human principal",
            validate_manifest_admission(manifest),
        )

    def test_sibling_agent_approval_is_rejected(self):
        """A second agent approving an activation is still capability granting authority.

        The former gate only fired when the manifest set `metadata.self_requested`
        and named itself as requester, so omitting the flag and naming any other
        agent as approver walked straight through it.
        """
        manifest = load("evals/sync-control-plane/cases/SCP-011.json")["manifest"]
        manifest["metadata"] = {}
        manifest["admission"]["approved_by"] = "agent.quirk-sibling"
        self.assertEqual([], self.validate(self.manifest_schema, manifest))
        self.assertIn(
            "activation requires approval by an independent human principal",
            validate_manifest_admission(manifest),
        )

    def test_service_and_system_approval_are_refused(self):
        """No allow-list of authorized service approvers exists, so neither is assumed."""
        for principal in ("service.quirk-admitter", "system.quirk-runtime"):
            with self.subTest(approved_by=principal):
                manifest = load("evals/sync-control-plane/cases/SCP-011.json")["manifest"]
                manifest["metadata"] = {}
                manifest["admission"]["approved_by"] = principal
                self.assertEqual([], self.validate(self.manifest_schema, manifest))
                self.assertIn(
                    "activation requires approval by an independent human principal",
                    validate_manifest_admission(manifest),
                )

    def test_a_malformed_requester_is_refused_on_the_python_surface_too(self):
        """The SQL trigger had no requester check; `'NOT-A-PRINCIPAL'` activated a manifest.

        The schema constrains that field for manifests arriving as documents, but
        this function is called directly, so it checks the shape itself.
        """
        for requested_by in ("NOT-A-PRINCIPAL", "human.", "", "agent"):
            with self.subTest(requested_by=requested_by):
                manifest = load("evals/sync-control-plane/valid-active-manifest.json")
                manifest["admission"]["requested_by"] = requested_by
                self.assertIn(
                    "manifest requester must be a well-formed principal",
                    validate_manifest_admission(manifest),
                )

    def test_a_principal_naming_nobody_is_refused_without_help_from_the_schema(self):
        """The gate is called directly, so it may not lean on schema validation.

        `"human."` satisfies a prefix test while naming no one. The schema would
        also reject it, but `validate_manifest_admission` has callers of its own.
        """
        manifest = load("evals/sync-control-plane/cases/SCP-011.json")["manifest"]
        manifest["metadata"] = {}
        manifest["admission"]["approved_by"] = "human."
        self.assertTrue(self.validate(self.manifest_schema, manifest))
        self.assertIn(
            "activation requires approval by an independent human principal",
            validate_manifest_admission(manifest),
        )

    def test_declaring_self_request_honestly_is_not_itself_a_violation(self):
        """Self-request is permitted; self-approval is not.

        The valid fixture is already self-requested (`requested_by` equals
        `manifest_key`) and passes on a human approver. The former gate rejected
        a manifest that declared the same fact in `metadata`, which punished the
        honest declaration and rewarded omitting it.
        """
        manifest = load("evals/sync-control-plane/valid-active-manifest.json")
        self.assertEqual(manifest["admission"]["requested_by"], manifest["manifest_key"])
        manifest["metadata"] = {"self_requested": True}
        self.assertEqual([], self.validate(self.manifest_schema, manifest))
        self.assertEqual([], validate_manifest_admission(manifest))

    def test_cloudflare_deferred_binding_is_valid(self):
        binding = {
            "schema_version": "source-binding.v2",
            "binding_id": "binding.cloudflare.deferred",
            "object_key": "platform.cloudflare",
            "platform": "cloudflare",
            "external_id": "unverified",
            "authority_class": "projection",
            "sync_direction": "none",
            "state": "deferred",
            "freshness": {"status": "unknown"},
        }
        self.assertEqual([], self.validate(self.binding_schema, binding))

    def test_binding_mapper_roundtrip(self):
        runtime = {
            "schema_version": "source-binding.v2",
            "binding_key": "binding.github.repo",
            "platform": "github",
            "external_id": "Quirk-Systems/quirk-os",
            "authority_class": "canonical",
            "sync_direction": "pull",
            "state": "candidate",
            "freshness": {"status": "fresh"},
        }
        canonical = binding_runtime_to_canonical(runtime, object_key="repo.quirk-os")
        self.assertEqual([], self.validate(self.binding_schema, canonical))
        rebound = binding_canonical_to_runtime(canonical, object_id="uuid")
        self.assertEqual(runtime["binding_key"], rebound["binding_key"])

    def test_receipt_mapper_roundtrip(self):
        runtime = {
            "schema_version": "sync-run-receipt.v2",
            "receipt_key": "receipt.test",
            "idempotency_key": "receipt:test:1",
            "run_type": "validate",
            "status": "blocked",
            "started_at": "2026-08-12T00:00:00Z",
            "completed_at": "2026-08-12T00:00:01Z",
            "input_refs": [],
            "output_refs": [],
            "evidence_refs": ["test://receipt"],
            "receipt_hash": "f" * 64,
        }
        canonical = receipt_runtime_to_canonical(runtime)
        self.assertEqual([], self.validate(self.receipt_schema, canonical))
        rebound = receipt_canonical_to_runtime(canonical)
        self.assertEqual(runtime["receipt_key"], rebound["receipt_key"])


class DatabaseGuardJobTests(unittest.TestCase):
    """The checks that assert CI still executes the database guard.

    The admission evidence now cites a CI job as the behavioural proof for the
    PostgreSQL layer. If that job can be deleted without anything failing, the
    document goes back to overstating enforcement — the same defect the
    candidate's own guards were written to close. These tests confirm the
    checks fail when the job is gone, which is the only property that makes
    them worth recording.
    """

    WORKFLOW = "ci.yml"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.live = yaml.safe_load(
            (ROOT / ".github/workflows/sync-control-plane-conformance.yml").read_text(
                encoding="utf-8"
            )
        )

    def run_checks(self, workflow) -> dict[str, bool]:
        path = self.tmp / self.WORKFLOW
        path.write_text(yaml.safe_dump(workflow, sort_keys=False), encoding="utf-8")
        return database_guard_job_checks(path)

    def test_the_live_workflow_satisfies_every_check(self):
        self.assertEqual(
            {
                "ci_declares_database_guard_job": True,
                "ci_runs_guard_cases": True,
                "ci_reads_installed_guard_back": True,
                "ci_runs_guard_cases_as_service_role": True,
                "ci_evidence_depends_on_database_guard": True,
                "ci_decision_fails_when_guard_fails": True,
                "ci_discards_tracked_decision": True,
                "ci_rejects_stale_committed_decision": True,
                "ci_path_filter_covers_job_inputs": True,
            },
            self.run_checks(self.live),
        )

    def test_removing_the_job_fails_every_check_about_the_job(self):
        # Not every check here is about the guard job any more:
        # `ci_decision_fails_when_guard_fails` and
        # `ci_discards_tracked_decision` are properties of the decision job and
        # survive the guard's deletion by design. What must not survive is any
        # claim that the guard exists, runs, or is read back.
        gutted = copy.deepcopy(self.live)
        del gutted["jobs"]["database-guard"]
        checks = self.run_checks(gutted)
        about_the_job = {
            "ci_declares_database_guard_job",
            "ci_runs_guard_cases",
            "ci_reads_installed_guard_back",
            "ci_runs_guard_cases_as_service_role",
            "ci_evidence_depends_on_database_guard",
        }
        # Properties of the decision job, or of the workflow's trigger, that
        # hold whether or not the guard job exists.
        about_something_else = {
            "ci_decision_fails_when_guard_fails",
            "ci_discards_tracked_decision",
            "ci_rejects_stale_committed_decision",
            "ci_path_filter_covers_job_inputs",
        }
        self.assertEqual(
            about_the_job,
            set(checks) - about_something_else,
            "a new check was added without deciding which job it is about",
        )
        self.assertEqual({False}, {checks[name] for name in about_the_job})

    def test_dropping_the_postgres_service_fails_the_job_check(self):
        gutted = copy.deepcopy(self.live)
        del gutted["jobs"]["database-guard"]["services"]
        self.assertFalse(self.run_checks(gutted)["ci_declares_database_guard_job"])

    def test_running_the_cases_file_without_its_driver_is_not_enough(self):
        # `psql --single-transaction` on the cases file commits when nothing
        # raises, leaving the one admitted manifest in the database. Only the
        # driver discards it, so naming the cases file alone must not pass.
        gutted = copy.deepcopy(self.live)
        for step in gutted["jobs"]["database-guard"]["steps"]:
            if "run" in step:
                step["run"] = step["run"].replace(
                    "manifest_activation_guard.run.sql",
                    "manifest_activation_guard.cases.sql",
                )
        checks = self.run_checks(gutted)
        self.assertFalse(checks["ci_runs_guard_cases"])
        self.assertTrue(checks["ci_declares_database_guard_job"])

    def test_the_service_role_step_must_be_its_own_psql_invocation(self):
        # EXECUTE on the rule function is checked when PL/pgSQL builds the
        # trigger's cached plan, so the privilege check is session-order
        # dependent. Merging the two steps puts nine superuser writes in front
        # of the service_role cases, priming the plan and making them pass with
        # no grant at all — observed on PostgreSQL 16.13.
        merged = copy.deepcopy(self.live)
        steps = merged["jobs"]["database-guard"]["steps"]
        service = next(
            s for s in steps if "service_role.sql" in str(s.get("run", ""))
        )
        plain = next(
            s
            for s in steps
            if "guard.run.sql" in str(s.get("run", ""))
            and "service_role.sql" not in str(s.get("run", ""))
        )
        plain["run"] = plain["run"] + "\n" + service["run"]
        steps.remove(service)
        checks = self.run_checks(merged)
        self.assertFalse(checks["ci_runs_guard_cases_as_service_role"])
        self.assertTrue(checks["ci_runs_guard_cases"])

    def test_eligibility_must_depend_on_the_database_job(self):
        # Run in parallel, candidate-conformance computes and uploads an
        # `ELIGIBLE_FOR_HUMAN_ADMISSION` decision even when the guard failed,
        # and the artifact cannot contradict it: `migration_hardening_complete`
        # only checks that the job is spelled in the workflow.
        detached = copy.deepcopy(self.live)
        del detached["jobs"]["candidate-conformance"]["needs"]
        checks = self.run_checks(detached)
        self.assertFalse(checks["ci_evidence_depends_on_database_guard"])
        self.assertTrue(checks["ci_declares_database_guard_job"])

    def test_a_bare_needs_is_not_enough_to_gate_the_decision(self):
        # A job whose dependency failed reports as *skipped*, and GitHub counts
        # a skipped required status check as a successful one. Dropping the
        # `if: always()` and the explicit assertion would turn a red guard into
        # a green required check — weakening merge protection in the name of
        # strengthening it.
        bare = copy.deepcopy(self.live)
        job = bare["jobs"]["candidate-conformance"]
        del job["if"]
        job["steps"] = [
            s
            for s in job["steps"]
            if "needs.database-guard.result" not in str(s.get("env", ""))
        ]
        checks = self.run_checks(bare)
        self.assertFalse(checks["ci_decision_fails_when_guard_fails"])
        self.assertTrue(checks["ci_evidence_depends_on_database_guard"])

    def test_the_path_filter_covers_what_the_jobs_read(self):
        # A path-filtered workflow runs only when a changed path matches, so a
        # file a job or test consumes but the filter omits is a guard that the
        # change it guards against cannot reach. Each of these was missing at
        # some point in this branch's history.
        paths = self.live.get(True, self.live.get("on", {}))["pull_request"]["paths"]
        for required, why in (
            (".claude/skills/verify/SKILL.md", "the drift test reads the recipe"),
            ("supabase/migrations/**", "the guard job applies every migration, not only the matching ones"),
            ("docs/sync-control-plane/**", "the digest test reads the admission evidence"),
        ):
            with self.subTest(required=required):
                self.assertIn(required, paths, why)

    def test_dropping_any_covered_path_fails_the_check(self):
        for required in (
            ".claude/skills/verify/SKILL.md",
            "supabase/migrations/**",
            "docs/sync-control-plane/**",
        ):
            with self.subTest(required=required):
                gutted = copy.deepcopy(self.live)
                key = True if True in gutted else "on"
                gutted[key]["pull_request"]["paths"] = [
                    p for p in gutted[key]["pull_request"]["paths"] if p != required
                ]
                self.assertFalse(
                    self.run_checks(gutted)["ci_path_filter_covers_job_inputs"]
                )

    def test_the_migration_filter_is_not_narrower_than_the_loop(self):
        # `20260811113009_ship_without_bryan_projection.sql` does not contain
        # `sync_control_plane`, and the guard job applies it. A filter of
        # `supabase/migrations/*sync_control_plane*` would skip the only job
        # that proves the sequence still applies to a clean database.
        globbed = sorted(p.name for p in (ROOT / "supabase/migrations").glob("*.sql"))
        self.assertTrue(
            any("sync_control_plane" not in name for name in globbed),
            "this test is pointless if every migration matches the old filter",
        )
        paths = self.live.get(True, self.live.get("on", {}))["pull_request"]["paths"]
        self.assertNotIn("supabase/migrations/*sync_control_plane*", paths)

    def test_dropping_the_staleness_gate_fails_that_check(self):
        # Without it, a change that alters the payload while leaving the
        # committed artifact and the document untouched passes everything: the
        # doc-digest test compares stale to stale, and the validator rewrites
        # the file without comparing it to what is committed. Confirmed by
        # altering the payload and touching neither — that test still passed.
        gutted = copy.deepcopy(self.live)
        job = gutted["jobs"]["candidate-conformance"]
        job["steps"] = [
            s for s in job["steps"] if "git diff --exit-code" not in str(s.get("run", ""))
        ]
        self.assertFalse(
            self.run_checks(gutted)["ci_rejects_stale_committed_decision"]
        )

    def test_keeping_the_tracked_decision_fails_that_check(self):
        # Checkout restores a committed decision recording a pass. With the
        # upload on `always()`, a failure before the validator runs would ship
        # that file as this run's evidence.
        kept = copy.deepcopy(self.live)
        job = kept["jobs"]["candidate-conformance"]
        job["steps"] = [
            s for s in job["steps"] if "rm -f evals" not in str(s.get("run", ""))
        ]
        self.assertFalse(self.run_checks(kept)["ci_discards_tracked_decision"])

    def test_dropping_the_service_role_step_fails_that_check(self):
        gutted = copy.deepcopy(self.live)
        steps = gutted["jobs"]["database-guard"]["steps"]
        gutted["jobs"]["database-guard"]["steps"] = [
            s for s in steps if "service_role.sql" not in str(s.get("run", ""))
        ]
        self.assertFalse(
            self.run_checks(gutted)["ci_runs_guard_cases_as_service_role"]
        )

    def test_dropping_the_installed_guard_read_back_fails_that_check(self):
        gutted = copy.deepcopy(self.live)
        for step in gutted["jobs"]["database-guard"]["steps"]:
            if "run" in step:
                step["run"] = step["run"].replace("pg_get_functiondef", "current_database")
        self.assertFalse(self.run_checks(gutted)["ci_reads_installed_guard_back"])

    def test_an_unreadable_workflow_fails_closed(self):
        self.assertEqual(
            {False}, set(database_guard_job_checks(self.tmp / "absent.yml").values())
        )


class ManifestActivationCasesFileTests(unittest.TestCase):
    """The split that lets CI run the activation cases on a clean database.

    The cases live in their own file because the rest of the hardening suite
    depends on seed rows no migration creates. Two properties keep both callers
    working, and neither is obvious from reading either file alone.
    """

    CASES = ROOT / "supabase/tests/manifest_activation_guard.cases.sql"
    DRIVER = ROOT / "supabase/tests/manifest_activation_guard.run.sql"
    SUITE = ROOT / "supabase/tests/sync_control_plane_hardening.sql"

    def test_the_cases_file_declares_no_transaction_of_its_own(self):
        # It is included inside the hardening suite's transaction. A `begin;`
        # here would nest, and a `commit;` would end the suite's rollback early
        # and persist every test row.
        body = self.CASES.read_text(encoding="utf-8").lower()
        for statement in ("\nbegin;", "\ncommit;", "\nrollback;"):
            self.assertNotIn(statement, body)

    def test_both_callers_include_the_one_cases_file(self):
        self.assertIn("\\ir manifest_activation_guard.cases.sql", self.DRIVER.read_text(encoding="utf-8"))
        self.assertIn("\\ir manifest_activation_guard.cases.sql", self.SUITE.read_text(encoding="utf-8"))

    def test_the_driver_supplies_the_boundary_the_cases_file_omits(self):
        driver = self.DRIVER.read_text(encoding="utf-8").lower()
        self.assertIn("begin;", driver)
        self.assertIn("rollback;", driver)
        self.assertNotIn("commit;", driver)

    SERVICE_ROLE = ROOT / "supabase/tests/manifest_activation_guard.service_role.sql"
    MIGRATION = ROOT / (
        "supabase/migrations/20261003090000_sync_control_plane_independent_approval.sql"
    )

    def test_the_service_role_cases_are_not_in_the_shared_cases_file(self):
        # They have to be the first trigger fire in their session to be able to
        # fail. A `set role` in the shared file would run after nine superuser
        # writes have already cached the trigger's plan.
        self.assertNotIn("set role", self.CASES.read_text(encoding="utf-8").lower())

    def test_the_service_role_file_owns_its_whole_session(self):
        body = self.SERVICE_ROLE.read_text(encoding="utf-8").lower()
        self.assertIn("begin;", body)
        self.assertIn("set role service_role;", body)
        self.assertIn("reset role;", body)
        self.assertIn("rollback;", body)
        self.assertNotIn("commit;", body)
        self.assertNotIn("\\ir", body)
        # The grant must be revoked BEFORE the first write in the session.
        # Otherwise the first write builds the guard's cached plan while the
        # grant is still present, and the cases after the revoke would pass on
        # a guard that had lost SECURITY DEFINER — the plan-cache trap that
        # made the first version of these cases pass with no grant at all.
        self.assertLess(
            body.index("revoke execute on function"),
            body.index("insert into quirk_sync.manifest_registry"),
        )

    def test_the_service_role_file_distinguishes_privilege_from_rule_failures(self):
        # A case that caught `others` would report a permission error as a
        # guard refusal, which is the same class of mistake as a guard that
        # cannot return false.
        body = self.SERVICE_ROLE.read_text(encoding="utf-8")
        # Two write cases and the pre-flight direct call.
        self.assertEqual(3, body.count("insufficient_privilege"))

    def test_the_migration_opens_no_transaction_of_its_own(self):
        # `supabase db push` applies each file inside a transaction, so an
        # in-file `commit` closes the runner's and the push can report success
        # while leaving the migration unrecorded.
        lines = {
            line.strip().lower()
            for line in self.MIGRATION.read_text(encoding="utf-8").splitlines()
        }
        self.assertNotIn("begin;", lines)
        self.assertNotIn("commit;", lines)

    def test_the_migration_still_takes_the_write_lock(self):
        # This is what keeps the requirement above from being documentation
        # only: PostgreSQL rejects `LOCK TABLE` outside a transaction block, so
        # a runner that does not wrap the file fails there instead of splitting
        # the audit from the cutover.
        self.assertIn(
            "lock table quirk_sync.manifest_registry in exclusive mode",
            self.MIGRATION.read_text(encoding="utf-8").lower(),
        )

    def test_the_privilege_lanes_check_can_fail(self):
        # The guard is SECURITY DEFINER so it can judge a row whatever role is
        # writing; pg_temp must be LAST in its search_path, since present-but-
        # first is no protection against definer hijacking; and the rule
        # function stays invoker. Each breakage must flip the check on its own.
        sql = "\n".join(
            p.read_text(encoding="utf-8")
            for p in sorted((ROOT / "supabase/migrations").glob("*_sync_control_plane_*.sql"))
        )
        self.assertTrue(_privilege_lanes_hold(sql))
        guard_header = "language plpgsql\nsecurity definer\nset search_path = pg_catalog, quirk_sync, pg_temp"
        path = "set search_path = pg_catalog, quirk_sync, pg_temp as $$"
        self.assertIn(guard_header, sql)
        for label, broken in (
            ("guard reverted to invoker", sql.replace(guard_header, guard_header.replace("security definer\n", ""))),
            ("pg_temp dropped", sql.replace(path, "set search_path = pg_catalog, quirk_sync as $$")),
            ("pg_temp moved first", sql.replace(path, "set search_path = pg_temp, pg_catalog, quirk_sync as $$")),
            (
                "rule function made definer",
                sql.replace("returns text\nlanguage plpgsql\nimmutable\n", "returns text\nlanguage plpgsql\nimmutable\nsecurity definer\n"),
            ),
        ):
            with self.subTest(label=label):
                self.assertNotEqual(sql, broken, "the mutation did not apply")
                self.assertFalse(_privilege_lanes_hold(broken))

    def test_the_migration_grants_the_rule_function_to_service_role(self):
        body = self.MIGRATION.read_text(encoding="utf-8").lower()
        self.assertIn("revoke execute on function", body)
        self.assertIn("to service_role;", body)

    SKILL = ROOT / ".claude/skills/verify/SKILL.md"

    def test_the_admission_evidence_quotes_the_tracked_digest(self):
        # Two Deck Grammar documents quoted a conformance hash that nothing
        # compared to the artifact, and a stale one survived two commits. This
        # document is the same shape, so it gets the same check. Superseded
        # hashes still appear in its digest history by design, so this asserts
        # the current one is present rather than that no other is.
        # Read the commit, not the working tree: the conformance workflow
        # deletes this artifact before running anything so that an `always()`
        # upload cannot ship a committed passing result as a failed run's
        # evidence. Reading the working tree made this test fail in CI on
        # `33769ba` for a reason unrelated to what it asserts. The commit is
        # also the more faithful reading of the claim.
        tracked = json.loads(
            subprocess.run(
                ["git", "show", "HEAD:evals/sync-control-plane/conformance-results.json"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            ).stdout
        )["content_hash_sha256"]
        doc = (ROOT / "docs/sync-control-plane/ADMISSION-EVIDENCE-V0.2.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(tracked, doc)

    def test_the_verify_recipe_does_not_drift_from_the_workflow(self):
        """A recipe that cannot go red is the same defect as a guard that cannot refuse.

        The skill was written one commit before the migration stopped opening
        its own transaction and before the production-role cases existed, and
        both of its instructions became wrong without anything failing. These
        assertions are what make the next such drift fail here instead of in
        somebody's terminal.
        """
        recipe = self.SKILL.read_text(encoding="utf-8")
        # The migration's `lock table` is rejected outside a transaction block,
        # so a loop without this flag aborts.
        self.assertIn("--single-transaction -f \"$m\"", recipe)
        self.assertNotIn("Do **not** add `--single-transaction`", recipe)
        # Supabase creates service_role with BYPASSRLS; without it the
        # production-role cases fail on RLS before reaching the trigger.
        self.assertIn("bypassrls", recipe.lower())
        # The recipe must drive the file that can detect a missing grant.
        self.assertIn("manifest_activation_guard.service_role.sql", recipe)
        self.assertIn("session-order dependent", recipe)
        # Neither validator writes anything without `--output`, and
        # `validate_deck_grammar.py` only writes inside its `if args.output`
        # branch. A recipe that omits it prints the new evidence and leaves the
        # tracked artifact — the committed evidence of record, whose digest the
        # admission docs quote — exactly as it was. That happened.
        self.assertIn(
            "--output evals/deck-grammar/conformance-results.json", recipe
        )
        self.assertIn(
            "--output evals/sync-control-plane/conformance-results.json", recipe
        )

    def test_every_refusal_case_asserts_its_own_message(self):
        # A case that asserted rejection without naming the reason would stay
        # green when a different rule fired, which is how a tightened guard
        # hides a rule that stopped working.
        body = self.CASES.read_text(encoding="utf-8")
        expected = {
            "may not approve",
            "independent human principal",
            "data productization requires",
            "fail-closed trigger contract",
            "well-formed principal",
            "trigger contract",
        }
        for phrase in expected:
            self.assertIn(f"position('{phrase}' in sqlerrm)", body)


if __name__ == "__main__":
    unittest.main()
