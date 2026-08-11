# Ship It Without Bryan Tribunal — PR #3

**Tribunal ID:** `tribunal.ship_without_bryan.pr3`  
**Repository:** `Quirk-Systems/quirk-os`  
**Pull request:** `#3`  
**Evaluated head:** `5256370115d217c576dd403cc0770f34e906d675`  
**Generated:** `2026-08-11T11:30:09Z`  
**Verdict:** **BLOCK — REQUEST CHANGES**  
**Blocking Proposed Moves:** **15**

> The pack can explain the aspiration. It cannot yet let a competent outsider install, operate, verify, challenge, repair, or safely extend the system without Bryan.

## Tribunal standard

The tribunal had no oral access to Bryan. It attempted to:

1. orient to the system and repository topology;
2. identify target operators and authority;
3. install or bootstrap the release candidate;
4. execute examples and tests;
5. trace decisions, evidence, and receipts;
6. challenge or reverse state;
7. follow migrations and rebuild projections;
8. recover from a documented failure;
9. extend one bounded capability;
10. inspect security, privacy, provider, and Strange Intact boundaries.

The artifact was treated as the source of truth. Conversation history was used only to detect where the artifact silently depended on information it did not contain.

## Executive verdict

### EVIDENCE

- The pre-tribunal GitHub Actions run passed.
- That validator checks file presence, JSON parseability, six law sentences, eleven prompt IDs, and four placeholder strings.
- The repository contains no executable runtime, bootstrap, reference vertical slice, schema fixtures, authority manifest, ADRs, migrations, threat model, failure runbook, or capability extension.
- An active Supabase project named `quirk-os-alpha` exists outside the PR.
- No `quirk-os` project exists in either connected Vercel team.
- Cloudflare account/project state is not inspectable from the current connected tool surface, and the repository contains no Cloudflare manifest or Wrangler configuration.
- The Google Drive work plane exists but is not represented by a machine-readable, offline-reconstructable Git manifest.

### INFERENCE

The PR is structurally coherent but operationally dependent on Bryan's memory for system identity, vocabulary, authority, operator intent, provider roles, release judgment, and what counts as Strange Intact. That dependency violates the release claim the pack itself establishes.

## Round results

### Round 0 — Source census

Inspected the full PR file inventory, pack architecture, prompt library, schemas, validator, workflow, live Supabase project/migrations, connected Vercel teams/projects, and Drive work-plane identifiers.

**Result:** enough evidence to evaluate the release claim; not enough implementation evidence to pass it.

### Round 1 — Orientation

The repository explains Ledger, Logs, Evals, Gates, Capabilities, Agent Skills, and Proposed Moves well enough to understand the intended machinery.

It does not independently resolve:

- Quirk Core versus Quirk OS versus Quirk Systems versus Quirkverse;
- why Quirk Core infrastructure belongs in `quirk-os`;
- who the supported operators are;
- where Bryan's founder authority ends and a tenant/user's authority begins;
- what the distinctive Quirk vocabulary means operationally.

**Result:** **FAIL**

### Round 2 — Installation and execution

No deterministic bootstrap, package manifest, runtime implementation, executable example, fixture set, or local stack exists. The only runnable evidence is a structural Python validator exercised by GitHub Actions.

**Result:** **FAIL**

### Round 3 — Authority, evidence, and challenge

Authority modes are listed but no authority manifest or resolution algorithm exists. Research and Top Minds lack typed evidence packets. Comments, challenges, decisions, transitions, receipts, and outcomes are not all typed. No real state can be challenged, reversed, poisoned, forgotten, or reconstructed.

**Result:** **FAIL**

### Round 4 — Migration, failure recovery, and extension

The live Supabase project has migrations that are absent from this repository. There is no repository migration path, projection rebuild, drift check, failure runbook, rollback exercise, or implemented capability to extend.

**Result:** **FAIL**

### Round 5 — Golden tribunal

The distinctive language remains intact, but Strange Intact itself depends on Bryan's unrecorded judgment. Structural CI is green while the PR openly lists missing Golden requirements. No mechanism currently forces those requirements to remain blocking.

**Result:** **BLOCK**

## Gate matrix

| Gate | Verdict | Primary evidence | Blocking moves |
|---|---|---|---|
| `gate.canon` | **FAIL** | Quirk Core is named as owner inside a quirk-os repository without a canonical identity-stack or repository-topology decision. | `qpm_pr3_system_identity_topology`, `qpm_pr3_canonical_vocabulary_strange_intact` |
| `gate.schema` | **FAIL** | Only LedgerTransition, ProposedMove, ResearchClaim, and MediaDerivative schemas exist. | `qpm_pr3_complete_contracts_queue_semantics`, `qpm_pr3_merge_blocking_receipt_outcome_gate` |
| `gate.authority` | **FAIL** | Authority modes are named, but no authority manifest, owner IDs, resolution algorithm, CODEOWNERS, waiver policy, or risk-scoped delegation exists. | `qpm_pr3_authority_approval_manifest`, `qpm_pr3_operator_personalization_boundaries` |
| `gate.evidence` | **FAIL** | Research and Top Minds are prose inventories without typed source records, preserved primary artifacts, claim-level citations, contradiction packets, or adoption receipts. | `qpm_pr3_research_top_minds_evidence`, `qpm_pr3_supabase_projection_contract`, `qpm_pr3_vercel_deployment_decision`, `qpm_pr3_cloudflare_edge_decision` |
| `gate.integrity` | **FAIL** | The validator checks file existence, JSON parsing, six sentences, eleven prompt IDs, and placeholder strings. | `qpm_pr3_eval_threat_model_tribunal_harness`, `qpm_pr3_merge_blocking_receipt_outcome_gate`, `qpm_pr3_complete_contracts_queue_semantics` |
| `gate.security_privacy` | **FAIL** | No threat model, hostile-document tests, secret contract, rights-sensitive forgetting implementation, non-resurrection test, or provider access policy exists. | `qpm_pr3_eval_threat_model_tribunal_harness`, `qpm_pr3_google_drive_workplane_manifest`, `qpm_pr3_supabase_projection_contract` |
| `gate.interop` | **FAIL** | No executable receipt envelope, provider manifest, projection rebuild, or cross-system fixture exists. | `qpm_pr3_supabase_projection_contract`, `qpm_pr3_vercel_deployment_decision`, `qpm_pr3_cloudflare_edge_decision`, `qpm_pr3_google_drive_workplane_manifest` |
| `gate.eval` | **FAIL** | No executable eval definitions, task bank, reference solutions, repeated-trial policy, grader calibration, adversarial cases, or outcome comparison exists. | `qpm_pr3_eval_threat_model_tribunal_harness`, `qpm_pr3_executable_vertical_slice_bootstrap` |
| `gate.documentation` | **FAIL** | Architecture prose is strong, but there is no quickstart, install contract, operator guide, runbook, ADR, migration guide, changelog, license, contributing guide, security policy, or failure-recovery procedure. | `qpm_pr3_executable_vertical_slice_bootstrap`, `qpm_pr3_release_migrations_supply_chain`, `qpm_pr3_google_drive_workplane_manifest` |
| `gate.strange_intact` | **FAIL** | Distinctive language survives, but no calibrated rubric separates useful Quirk specificity from Bryan-only taste, inaccessible jargon, or ornamental profanity. | `qpm_pr3_canonical_vocabulary_strange_intact`, `qpm_pr3_multimedia_rights_accessibility_provenance` |
| `gate.ship_without_bryan` | **FAIL** | The tribunal could orient conceptually but could not install a runtime, execute an example, trace a real authority decision, challenge state, follow a migration, recover a failure, or extend a capability. | `qpm_pr3_system_identity_topology`, `qpm_pr3_canonical_vocabulary_strange_intact`, `qpm_pr3_operator_personalization_boundaries`, `qpm_pr3_authority_approval_manifest`, `qpm_pr3_executable_vertical_slice_bootstrap`, `qpm_pr3_complete_contracts_queue_semantics`, `qpm_pr3_eval_threat_model_tribunal_harness`, `qpm_pr3_google_drive_workplane_manifest`, `qpm_pr3_supabase_projection_contract`, `qpm_pr3_vercel_deployment_decision`, `qpm_pr3_cloudflare_edge_decision`, `qpm_pr3_research_top_minds_evidence`, `qpm_pr3_multimedia_rights_accessibility_provenance`, `qpm_pr3_release_migrations_supply_chain`, `qpm_pr3_merge_blocking_receipt_outcome_gate` |

## Typed blocking queue

All discovered hidden-context dependencies are encoded as Proposed Moves in:

`proposed-moves/pr-3/queue.json`

| # | Move | Lane | Dependency removed | Risk | Merge |
|---:|---|---|---|---|---|
| 1 | `qpm_pr3_system_identity_topology` | `canon` | Make the Quirk identity stack and repository topology independently reconstructable | `L3` | **BLOCK** |
| 2 | `qpm_pr3_canonical_vocabulary_strange_intact` | `canon` | Replace founder-recognition vocabulary with canonical definitions and executable rubrics | `L3` | **BLOCK** |
| 3 | `qpm_pr3_operator_personalization_boundaries` | `policy` | Define target operators, namespace partitions, and the boundary between Bryan authority and user authority | `L4` | **BLOCK** |
| 4 | `qpm_pr3_authority_approval_manifest` | `policy` | Make authority, delegation, review ownership, and waivers machine-inspectable | `L4` | **BLOCK** |
| 5 | `qpm_pr3_executable_vertical_slice_bootstrap` | `capability` | Ship a deterministic bootstrap and one complete accountable mutation vertical slice | `L3` | **BLOCK** |
| 6 | `qpm_pr3_complete_contracts_queue_semantics` | `schema` | Type every referenced core object and specify Proposed Move Queue runtime semantics | `L3` | **BLOCK** |
| 7 | `qpm_pr3_eval_threat_model_tribunal_harness` | `eval` | Replace structural greenness with executable integrity, security, privacy, and outsider-operation evidence | `L4` | **BLOCK** |
| 8 | `qpm_pr3_google_drive_workplane_manifest` | `policy` | Make the Google Drive work plane portable, permissioned, and reconstructable | `L4` | **BLOCK** |
| 9 | `qpm_pr3_supabase_projection_contract` | `migration` | Canonicalize the Supabase projection contract for quirk-os-alpha | `L4` | **BLOCK** |
| 10 | `qpm_pr3_vercel_deployment_decision` | `policy` | Decide and document Vercel's role before creating a quirk-os deployment | `L3` | **BLOCK** |
| 11 | `qpm_pr3_cloudflare_edge_decision` | `policy` | Decide and document Cloudflare's edge, security, storage, and deployment boundary | `L3` | **BLOCK** |
| 12 | `qpm_pr3_research_top_minds_evidence` | `research-adoption` | Turn Current Research and Top Minds prose into preserved, typed, contestable evidence packets | `L3` | **BLOCK** |
| 13 | `qpm_pr3_multimedia_rights_accessibility_provenance` | `media-release` | Prove Multimedia Multipliziert with a rights-cleared, accessible, provenance-linked specimen | `L4` | **BLOCK** |
| 14 | `qpm_pr3_release_migrations_supply_chain` | `gate` | Make release, migration, contribution, and supply-chain expectations explicit | `L3` | **BLOCK** |
| 15 | `qpm_pr3_merge_blocking_receipt_outcome_gate` | `gate` | Make unresolved tribunal findings mechanically block merge and require verified closure | `L3` | **BLOCK** |

## Release conditions

PR #3 may not pass the Ship It Without Bryan gate until:

1. every `blocks_merge: true` move is `verified`;
2. every verified move has non-empty evidence and a `receipt_ref`;
3. CI validates the queue and fails on unresolved blockers;
4. the authority manifest identifies who may accept each move;
5. an outsider reruns the tribunal from a clean environment;
6. the rerun can execute a vertical slice, follow a migration, recover a failure, and extend one capability;
7. the final release receipt records the verified source commit and zero unresolved blockers.

## What the tribunal did not claim

- It did not claim any external link is broken; the repository simply has no automated link gate.
- It did not claim Cloudflare is unused or absent; live account state was not available through the connected tool surface.
- It did not treat the existing Supabase project as canon.
- It did not invent defects beyond observed missing contracts, artifacts, or executable evidence.

## Final decision

```yaml
tribunal:
  id: tribunal.ship_without_bryan.pr3
  verdict: block
  request_changes: true
  release_receipt: null
  blocking_moves: 15
  merge_allowed: false
  reason: >
    The release candidate still requires hidden Bryan context to explain
    topology, vocabulary, authority, operators, provider roles, execution,
    migration, evaluation, and Golden judgment.
```

**No receipt. No release. No polite little merge because the documents have excellent posture.**
