# Quirk Sync Control Plane v0.2 — Admission Evidence

**Candidate:** `program.quirk-sync-control-plane` v0.2.0  
**Candidate commit (the subject evaluated):** `f344af21ff96e9e748a0a0c65dbc20ae71912222`  
**PR:** Quirk-Systems/quirk-os#5  
**Evidence captured:** 2026-08-12  
**Conformance decision:** `ELIGIBLE_FOR_HUMAN_ADMISSION`  
**Automatic activation:** false  
**Content hash (SHA-256):** `c5feeaeaf7340d3435818c56261f838747aa62568f8fa0bf2cb1a95ec06f2068`  
**Evidence revision (the tree that reproduces that hash):** `731d4996feda357a1db87e9b31b458c98b9aa090`

> **Why two revisions.** The candidate commit names the subject that was
> evaluated. The evidence revision names the tree whose validator and inputs
> produce the hash above, and they are not the same commit:
> `evals/sync-control-plane/conformance-results.json` does not exist at
> `f344af21`, so that revision cannot reproduce this digest and never could.
> Pairing a candidate commit with a regenerated hash and nothing else invited
> the reading that the hash was the digest of the evidence at that commit,
> which was not true.
>
> Reproduce with:
>
> ```sh
> git checkout 731d4996feda357a1db87e9b31b458c98b9aa090
> python scripts/validate_sync_control_plane.py --repo . \
>   --output evals/sync-control-plane/conformance-results.json --require-admit
> ```
>
> Observed at that revision in a detached worktree:
> `c5feeaeaf7340d3435818c56261f838747aa62568f8fa0bf2cb1a95ec06f2068`, matching
> both the tracked artifact and the line above.

> **Digest history**, recorded because a hash replaced without a note is
> indistinguishable from one that was always that value. The decision above is
> unchanged throughout and still is not admission.
>
> - `ab07a616…` — covered a payload recording the retired error
>   `self-requested activation requires independent human or authorized service approval`.
>   Superseded when that rule became an independent-human-approver check. Its
>   producing revision is not recorded anywhere in this repository and is not
>   guessed here; the artifact reached `main` through a merge rather than a
>   generation step.
> - `e63fd964…` — covered the replacement error and the first two migration
>   static checks. Produced at `be80180e2d2548346809c83b96842aac92c826c1`.
>   Superseded when those checks were scoped to the rule function, because a
>   whole-file search for a predicate stayed satisfied even when the enforcing
>   definition had lost it.
> - `0ac9f28d…` — covered the seventeen static checks as they stood before CI
>   executed any SQL. Produced at `b2b95cd`. Superseded by the three
>   `ci_*` checks, which assert the `database-guard` job still exists and
>   still runs the cases through the driver that discards its rows.
> - `f7392196…` — covered the first three `ci_*` checks, added when the
>   database guard began executing in CI. Produced at `38d53cc`. Superseded
>   when the Codex review of that commit found that the rule function was
>   never granted to `service_role` and that the migration's own
>   `begin`/`commit` closes `supabase db push`'s transaction.
> - `744412cd…` — covered the `service_role` grant and the removal of the
>   migration's own transaction. Produced at `d969a9f`. Superseded when the
>   Codex review of `3417a8d` found that this decision was computed in
>   parallel with the proof it cites, so a failing database guard still
>   left an `ELIGIBLE_FOR_HUMAN_ADMISSION` artifact to be uploaded.
> - `a18c5aa2…` — covered the first form of the eligibility gate, a bare
>   `needs: database-guard`. Produced at `893cd30`. Superseded when the
>   Codex review of `7d91ecc` pointed out that a job whose dependency
>   failed reports as *skipped*, and GitHub counts a skipped required check
>   as a successful one, so that form could have turned a red guard into a
>   green required check.
> - `c5feeaea…` — current, produced at `731d499` as above.

> **What produces this decision.** `candidate-conformance` declares
> `needs: database-guard` and runs with `if: always()`, failing explicitly when
> that guard's result is not `success`. Both halves are load-bearing. Computed
> in parallel, as it was before `893cd30`, a database guard that enforced
> nothing did not stop this decision being produced and uploaded —
> `migration_hardening_complete` cannot catch that, because it checks the job
> is spelled in the workflow, not that it passed. Gated by a bare `needs:`, as
> it was in `893cd30`, a failed guard would have left this job *skipped*, which
> GitHub counts as a successful required status check.
>
> The uploaded artifact is also no longer able to be a stale pass: the tracked
> `conformance-results.json` is removed before any check runs, so the upload
> carries a decision this run computed or fails.

This document consolidates the technical evidence for each admission criterion. It does not constitute admission. Bryan's explicit approve, revise, reject, or supersede decision is required before any activation, Canon promotion, merge, authority expansion, or production deployment.

---

## Admission criteria evidence

### 1. Candidate and runtime contracts remain semantically aligned

**Evidence**

- Canonical schemas (`schemas/runtime-manifest.schema.json`, `schemas/source-binding.schema.json`, `schemas/sync-run-receipt.schema.json`) drive both the Python policy runner and the Supabase migration guards.
- Versioned mapping YAML (`mappings/sync-control-plane.v1.yaml`) names every `receipt_id↔receipt_key`, `binding_id↔binding_key`, and `object_key↔object_id` translation.
- Mapper round-trip test passes: canonical→runtime→canonical with zero schema errors on both legs (`mapping_proof.binding_schema_errors: []`, `mapping_proof.receipt_schema_errors: []`, `mapping_proof.binding_roundtrip_stable: true`, `mapping_proof.receipt_roundtrip_stable: true`).

**Status:** satisfied by executable proof

---

### 2. No agent can approve or activate its own manifest

**Evidence**

Two enforcement layers reject SCP-011 (self_promotion_attack), and both are now
executed in CI. An earlier version of this section claimed three and counted
JSON Schema among them; that was never true and the artifact says so.

| Layer | Rejects SCP-011? | On what evidence |
| --- | --- | --- |
| JSON Schema (`schemas/runtime-manifest.schema.json`) | **No** | `self_promotion_schema_errors: []` in the conformance artifact. The `admission` object carries no constraint relating `requested_by` to `approved_by` — JSON Schema is not expressing this rule, which is why `validate_manifest_admission` exists at all: its docstring reads "Return policy violations that JSON Schema cannot express alone." `test_self_promotion_rejected` now asserts the fixture is schema-valid, precisely so the rejection has to come from policy. |
| Python policy (`scripts/sync_control_plane/policy.py`) | Yes | `self_promotion_policy_errors` records two: `requester may not approve its own manifest transition` and `activation requires approval by an independent human principal`. Executed on every CI run of the conformance validator. |
| PostgreSQL trigger (`quirk_sync.manifest_activation_violation`, raised by `guard_manifest_activation`) | Yes | Executed by the `database-guard` job in `.github/workflows/sync-control-plane-conformance.yml`: the job applies every migration to a PostgreSQL 16 service, reads `pg_get_functiondef` back to assert the installed guard delegates to the rule function, then runs `supabase/tests/manifest_activation_guard.run.sql` — nine cases where a sibling-agent approval, a bare `human.` principal, a malformed requester, an omitted rights-review key and an omitted `collision_behavior` are each refused by their own message, and one well-formed activation is admitted. A separate step then runs `manifest_activation_guard.service_role.sql` in its own psql session as `service_role`, which is what writes in production; it has to be a separate session because EXECUTE on the rule function is checked when PL/pgSQL builds the trigger's cached plan, so a superuser write ahead of it would prime the plan and hide a missing grant. The static checks `rule_*`, `guard_delegates_to_rules` and `audit_uses_rule_function` remain, but they are now a spelling test in front of a behavioural one rather than the whole of it. |

Fixture SCP-011 passes with `reject_capability_to_authority_escalation`, and
`test_self_promotion_rejected` passes.

**Status:** satisfied by two layers, both executed in CI, and the database
layer is now exercised under the role that writes in production rather than
only under a superuser. What neither layer establishes is that a named human
actually approved anything: both check the *shape* of `approved_by`, and a
string shaped like `human.bryan` is not an attestation — see
`docs/briefs/2026-10-03-approval-attestation.md`.

---

### 3. Receipts and transition evidence remain append-only

**Evidence**

- Migration static check `append_only_receipts: true` confirms the `prevent_append_only_mutation` trigger is present in the candidate migrations.
- Migration static check `transition_ledger: true` confirms `manifest_transition_ledger` is present.
- Supabase transactional proof exercises both tables and rolls back cleanly; no UPDATE or DELETE path exists on receipt or ledger rows.

**Status:** satisfied by database trigger and transactional proof

---

### 4. Drift produces a typed Proposed Move rather than silent repair

**Evidence**

- Fixture SCP-007 (`stale_guidance`) returns `mark_stale_without_rewriting_history` — content history preserved, freshness metadata updated, no repair.
- Fixture SCP-001 (`conflicting_canon`) returns `block_projection_and_propose_reconciliation` — projection blocked, Proposed Move emitted.
- Migration static check `drift_controller: true` confirms `observe_binding` function is present.
- `proposed-moves/sync-control-plane/qpm_sync_control_plane_hardening.json` is a live example of a typed Proposed Move produced by the candidate.

**Status:** satisfied by fixtures and migration proof

---

### 5. Outbox delivery remains bounded, leased, retryable, and dead-lettered

**Evidence**

Migration static checks confirm:

| Property | Check | Result |
| --- | --- | --- |
| Atomic outbox claim | `claim_projection_outbox` | true |
| Bounded retries | `dead_lettered_at` | true |
| Dead letter | `bounded_dead_letter` | true |

Fixture SCP-009 (`roadmap_capacity_overload`) returns `stop_pull_and_propose_rebalance`, proving the outbox does not spiral on overload. Supabase transactional proof exercises `SKIP LOCKED`, retry exhaustion at five attempts, and dead-letter promotion.

**Status:** satisfied by migration static analysis and transactional proof

---

### 6. Drive, Airtable, and Notion projections can be rebuilt from Git + Supabase

**Evidence**

- Migration static check `projection_rebuild: true` confirms `rebuild_projection_snapshot` function is present.
- `workflows/quirk-sync-control-plane.workflow.yaml` defines the rebuild flow from canonical identity plus runtime state to projection envelope.
- `schemas/projection-envelope.schema.json` defines the typed envelope that every adapter produces.
- Mapping round-trip (`mapping_proof`) proves canonical identity survives translation.
- VERIFICATION-2026-08-11.md records that Drive, Airtable, and Notion were populated and read back from candidate state.

**Status:** mechanically satisfied; projection reconstruction from live adapter fixtures is tracked separately in issue #14

---

### 7. Vercel remains delivery-only until admitted

**Evidence**

- `programs/quirk-sync-control-plane.yaml` lists Vercel under `planes.projections` and the comment "active_only_after_human_admission: true" applies to all delivery projections.
- VERIFICATION-2026-08-11.md records "No project or deployment created" in Vercel.
- No Vercel deployment or project creation appears in any migration, script, or workflow file.

**Status:** satisfied by program declaration and verified runtime state

---

### 8. Cloudflare remains DEFER_UNBOUND until a separate provider decision

**Evidence**

- `programs/quirk-sync-control-plane.yaml` lists Cloudflare under `planes.deferred_edges` with `state: deferred_unbound` and `decision_ref: decisions/ADR-0001-cloudflare-boundary.md`.
- `decisions/ADR-0001-cloudflare-boundary.md` records the explicit deferral decision.
- `platform/cloudflare.manifest.yaml` (if present) is candidate-only.
- Migration static check `cloudflare_binding: true` confirms the deferred Cloudflare binding is represented in the migration.
- Fixture SCP-008 (`skill_trigger_collision`) blocks ambiguous invocation — Cloudflare edge invocation would be blocked by the same trigger-routing guard.

**Status:** satisfied by program declaration, ADR, and migration proof

---

### 9. Inherited PR #3 blockers are reconciled separately

**Evidence**

- Issue #12 created to track Golden Gates reconciliation for PR #3.
- `tribunals/ship-without-bryan/pr-3/` contains the tribunal evidence and report for PR #3.
- `proposed-moves/pr-3/` contains three typed Proposed Moves addressing the PR #3 findings.
- The conformance suite runs independently of the Golden Project Pack workflow per `sync-control-plane-conformance.yml`.

**Status:** reconciliation tracked in issue #12; this candidate's conformance is independent

---

### 10. Bryan records the admission decision and rationale

**Status:** awaiting human action — this is the only criterion an agent cannot satisfy

---

## Full conformance evidence

| Check | Result |
| --- | --- |
| fixture_count_11 | true |
| all_fixtures_pass | true |
| valid_active_manifest_passes_schema | true |
| valid_active_manifest_passes_policy | true |
| self_promotion_rejected_by_schema_or_policy | true |
| rights_unclear_rejected | true |
| trigger_collision_rejected | true |
| migration_hardening_complete | true |
| mapping_roundtrip_passes | true |

**All nine automated checks pass.**

See `evals/sync-control-plane/conformance-results.json` for the full machine-readable evidence record.

---

## Open work items before admission decision

| Issue | Title | Blocking admission? |
| --- | --- | --- |
| #9 | Bounded live adapter fixture | No — mechanical evidence; candidate eligible without it |
| #12 | PR #3 Golden Gates reconciliation | Separate track; does not block SCP conformance |
| #13 | Native Discussion publication | Blocked by GitHub Discussions being disabled |
| #14 | Notion writeback and full projection regeneration proof | Connector unavailable; tracked separately |

---

## Authority state at evidence capture

- No merge.
- No Canon promotion.
- No manifest activation.
- No authority expansion.
- No production deployment.
- Zero active manifests; zero production deployments.
- Cloudflare: `DEFER_UNBOUND`.
- Vercel: inventory only.

**The candidate is eligible for a human admission decision. It is not admitted.**
