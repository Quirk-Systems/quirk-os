# Ship It Without Bryan Tribunal — PR #3

**Tribunal ID:** `tribunal.ship_without_bryan.pr3`  
**Repository:** `Quirk-Systems/quirk-os`  
**Pull request:** `#3`  
**Evaluated head:** `e66db5cb95a8cb40e5c4d5718a3418e9a3ec6b88`  
**Refreshed:** `2026-08-11T13:36:00Z`  
**Verdict:** **BLOCK — REQUEST CHANGES**  
**Blocking Proposed Moves:** **16**

> The pack can explain the aspiration. It still cannot let a competent outsider install, operate, verify, challenge, repair, secure, or safely extend the system without Bryan.

## Tribunal standard

The tribunal had no oral access to Bryan. It attempted to orient to the system and repository topology; identify target operators and authority; install or bootstrap the release candidate; execute examples and tests; trace decisions, evidence, and receipts; challenge or reverse state; follow migrations and rebuild projections; recover from a documented failure; extend one bounded capability; and inspect security, privacy, provider, and Strange Intact boundaries.

Conversation history is not accepted as implementation evidence. It is used only to identify where the artifact silently depends on context it does not contain.

## Current evidence

- PR #3 remains draft and mergeable, but no Golden release receipt exists.
- The branch now contains typed Proposed Moves, queue schema, tribunal evidence/report, a Supabase projection migration, and fail-closed queue validation machinery.
- The queue still contains unresolved merge-blocking moves, so structural CI must fail until they are verified with evidence and receipts.
- Google Drive work-plane identifiers exist, but the offline-reconstructable manifest is still unresolved.
- Supabase project `quirk-os-alpha` is live. Current migration history includes `20260521204930_quirk_os_schema`, `20260729101853_add_created_at_to_quirk_pipeline_runs`, and `20260811133653_establish_preference_edge_validation`.
- Supabase security advisors currently report RLS-enabled tables without policies, `vector` installed in `public`, and `public.rls_auto_enable()` exposed as a `SECURITY DEFINER` function callable by anon and authenticated roles. These findings are now captured by `qpm_pr3_supabase_security_reconciliation`.
- Neither connected Vercel team contains a `quirk-os` project, so Vercel remains a decision rather than an assumed deployment target.
- Cloudflare live account state remains unavailable from the connected surface; no repository manifest currently establishes its role.

## Gate verdicts

| Gate | Verdict | Why it still fails |
|---|---|---|
| `gate.canon` | FAIL | Identity stack, repository topology, and normative Quirk vocabulary still require canonical definitions and placement rules. |
| `gate.schema` | FAIL | Multiple core contracts remain prose-only and there is no complete executable vertical slice. |
| `gate.authority` | FAIL | No verified authority manifest, risk-scoped delegation, waiver semantics, or operator/persona boundary. |
| `gate.evidence` | FAIL | Research, Top Minds, provider decisions, and release claims lack complete typed evidence and adoption receipts. |
| `gate.integrity` | FAIL | Ledger Fuckery, receipt reconstruction, concurrency, idempotency, poison, drift, and outcome evals remain incomplete. |
| `gate.security_privacy` | FAIL | Supabase live-state findings plus missing threat model, forgetting/non-resurrection tests, and provider security contracts. |
| `gate.interop` | FAIL | Provider manifests, receipt transport fixtures, Drive reconstruction, and projection rebuild remain incomplete. |
| `gate.eval` | FAIL | No complete outsider-operation task bank or calibrated repeated-trial eval suite exists. |
| `gate.documentation` | FAIL | Quickstart, install, runbook, ADR, migration, recovery, and extension paths remain incomplete. |
| `gate.strange_intact` | FAIL | The rubric still cannot distinguish reusable Quirk specificity from founder-only taste without Bryan. |
| `gate.ship_without_bryan` | FAIL | A clean outsider still cannot execute, migrate, recover, secure, and extend the stack from repo artifacts alone. |

## Typed blocking queue

The authoritative queue is `proposed-moves/pr-3/queue.json`.

1. `qpm_pr3_system_identity_topology`
2. `qpm_pr3_canonical_vocabulary_strange_intact`
3. `qpm_pr3_operator_personalization_boundaries`
4. `qpm_pr3_authority_approval_manifest`
5. `qpm_pr3_executable_vertical_slice_bootstrap`
6. `qpm_pr3_complete_contracts_queue_semantics`
7. `qpm_pr3_eval_threat_model_tribunal_harness`
8. `qpm_pr3_google_drive_workplane_manifest`
9. `qpm_pr3_supabase_projection_contract`
10. `qpm_pr3_supabase_security_reconciliation`
11. `qpm_pr3_vercel_deployment_decision`
12. `qpm_pr3_cloudflare_edge_decision`
13. `qpm_pr3_research_top_minds_evidence`
14. `qpm_pr3_multimedia_rights_accessibility_provenance`
15. `qpm_pr3_release_migrations_supply_chain`
16. `qpm_pr3_merge_blocking_receipt_outcome_gate`

## New Supabase security blocker

`qpm_pr3_supabase_security_reconciliation` exists because an outsider cannot currently tell whether RLS-without-policy tables are deliberately private or accidentally unusable, why a publicly callable `SECURITY DEFINER` helper exists, whether the `vector` public-schema warning is accepted, or what the Data API exposure policy is. Hidden infrastructure decisions are hidden Bryan-context even when they predate this PR.

No destructive Supabase remediation is performed by the tribunal itself. The Proposed Move requires explicit security/data/privacy authority, version-controlled migration, advisor verification, access tests, and a receipt.

## Provider boundary findings

### Google Drive
Drive is a valid work plane but cannot be required for orientation or canonical review. Critical IDs, ownership, access expectations, source versions, Git fallbacks, comment routing, retention, and forgetting must be machine-readable in Git.

### Supabase
Supabase should remain a projection/runtime data concern, not canon. Repository migrations, source-commit hashes, rebuild/drift procedures, explicit exposure decisions, and security reconciliation are blocking.

### Vercel
No `quirk-os` project currently exists. That is good evidence against accidental assumption. An ADR must decide whether Vercel owns preview/control UI/docs/runtime API responsibilities or nothing at all.

### Cloudflare
No live account state was asserted. The missing decision itself is the finding: Workers/Pages/DNS/WAF/Turnstile/R2/Queues responsibilities and overlap with Vercel/Supabase require an explicit adopt/adapt/reject/defer decision.

## Release conditions

PR #3 may not pass until every `blocks_merge: true` move is `verified`; every verified move carries evidence and `receipt_ref`; CI derives zero unresolved blockers; authority is machine-inspectable; provider state is reconciled to documented contracts; and an outsider reruns the tribunal from a clean environment and can execute a vertical slice, follow a migration, recover a failure, inspect authority and evidence, and extend one bounded capability.

```yaml
tribunal:
  id: tribunal.ship_without_bryan.pr3
  verdict: block
  request_changes: true
  release_receipt: null
  blocking_moves: 16
  merge_allowed: false
  reason: >
    The candidate still depends on hidden Bryan context for topology,
    vocabulary, authority, operator boundaries, provider roles, live security
    assumptions, execution, migration, evaluation, recovery, and Golden judgment.
```

**No receipt. No release. The repo has to know the shit Bryan currently knows.**
