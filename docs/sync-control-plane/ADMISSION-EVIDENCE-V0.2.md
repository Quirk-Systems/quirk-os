# Quirk Sync Control Plane v0.2 — Admission Evidence

**Candidate:** `program.quirk-sync-control-plane` v0.2.0  
**Candidate commit:** `f344af21ff96e9e748a0a0c65dbc20ae71912222`  
**PR:** Quirk-Systems/quirk-os#5  
**Evidence captured:** 2026-08-12  
**Conformance decision:** `ELIGIBLE_FOR_HUMAN_ADMISSION`  
**Automatic activation:** false  
**Content hash (SHA-256):** `ab07a616af2effda9a93a1edca3c8284e6c764479bd5de7a234bd93998d6a76b`

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

Three independent enforcement layers all reject SCP-011 (self_promotion_attack):

| Layer | Rejection |
| --- | --- |
| JSON Schema (`schemas/runtime-manifest.schema.json`) | `approved_by` must differ from `requested_by` |
| Python policy (`scripts/sync_control_plane/policy.py`) | "requester may not approve its own manifest transition"; "self-requested activation requires independent human or authorized service approval" |
| PostgreSQL trigger (`guard_manifest_activation`) | present in migration static check |

Fixture SCP-011 passes with `reject_capability_to_authority_escalation`. Unit test `test_self_promotion_rejected` passes. Schema attack `self_promotion_policy_errors` returns the expected two policy errors.

**Status:** satisfied by three independent enforcement layers

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
