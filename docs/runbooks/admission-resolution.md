# Golden admission repair workstream

Status: candidate repair; admission and runtime authority remain unestablished.

## Completed code management

PR #139 merged as `017d7f700982b63b31d3a24f3886d89898277c49` after QIS Agent Harness, Golden Gates, Evidence Binding and CodeQL passed. PR #138 closed without merge as superseded.

## Executable inspection

Run `python scripts/admission_workplan.py --output /tmp/quirk-admission-workplan.json`. This reads the live queue and the versioned audit, checks exact source ancestry and unchanged move definitions, and emits dependency waves, every acceptance criterion, current artifact hashes, authority IDs, evidence gaps, and stop conditions. It executes no tasks or external writes. Every criterion remains unassessed: artifact existence is not acceptance proof. CI rejects stale criteria, incomplete audit coverage, self-awarded verification, dependency cycles, and symlink/traversal evidence paths.

The audit is a version-bound observation, not a new queue or canonical decision. Refresh it after changing any move; preserve the historical tribunal. The original merge-blocking acceptance language conflicts with the current candidate-preservation contract in ADMISSION.md. A later decision must reconcile that wording before claiming the original acceptance check passed.

## Current hold work

| Move | Next implementation | Evidence boundary |
|---|---|---|
| qpm_pr3_authority_approval_manifest | Add policy-bound principal registry, risk/scope resolution and waiver contracts; keep actual grants separate from synthetic fixtures. | human observation/decision |
| qpm_pr3_canonical_vocabulary_strange_intact | Implement term registry with required fields and neutral-versus-styled fixtures; preserve candidate status pending language-owner adoption. | human observation/decision |
| qpm_pr3_cloudflare_edge_decision | Reuse defer ADR/manifest and add explicit acceptance mapping plus no-active-binding tests; do not provision provider to close a defer-compatible hold. | human observation/decision |
| qpm_pr3_complete_contracts_queue_semantics | Inventory normative objects and implement missing schemas/fixtures plus versioned queue state machine and transactional concurrency tests. |  |
| qpm_pr3_eval_threat_model_tribunal_harness | Expand actual validators into named threat-model cases and reference recovery/forgetting tests; explicitly distinguish deterministic evidence from human/model reliability trials. | human observation/decision |
| qpm_pr3_executable_vertical_slice_bootstrap | Extend current Python conformance bootstrap into one local end-to-end mutation and recovery demo, then run outsider extension trial. | human observation/decision |
| qpm_pr3_google_drive_workplane_manifest | Create versioned inventory and offline fallback contract, then test denied-access behavior; obtain actual authorized resource metadata. | current external evidence |
| qpm_pr3_merge_blocking_receipt_outcome_gate | Disposition superseded candidate-merge wording through approved policy; add content-bound per-check receipts and live admission ruleset/review verification without conflating merges with canon. | human observation/decision, current external evidence |
| qpm_pr3_multimedia_rights_accessibility_provenance | Use repository-owned neutral source to build one licensed accessible derivative and executable withdrawal/provenance tests, then verify outsider usability. | human observation/decision |
| qpm_pr3_operator_personalization_boundaries | Reuse Intent Shaper policy and add operator/namespace/context-provenance contracts plus three executable Golden Paths. | human observation/decision |
| qpm_pr3_release_migrations_supply_chain | Create candidate release/security/compatibility policy and tested manifest; explicit license selection requires actual rights-owner decision. | human observation/decision |
| qpm_pr3_research_top_minds_evidence | Create typed source and MindCard packets using exact retrieved primary artifacts; implement freshness/reversal and proposed-adoption tests. | human observation/decision, current external evidence |
| qpm_pr3_supabase_projection_contract | Reconcile migration history with intended project, add missing provenance fields safely, test role access/rebuild/forgetting and bind live advisor evidence. | current external evidence |
| qpm_pr3_supabase_security_reconciliation | Read live grants/functions/extensions/advisors; create narrowly scoped reconciliation migration and tests from actual findings, then capture post-change evidence. | human observation/decision, current external evidence |
| qpm_pr3_system_identity_topology | Write candidate identity/topology contracts and automated reference checks; run an independent contributor placement exercise. | human observation/decision |
| qpm_pr3_vercel_deployment_decision | Record candidate defer decision or verify existing admitted delivery project with bounded secrets/rollback/commit receipt; operator chooses substantive adoption. | human observation/decision, current external evidence |

## Runtime repair and remaining trust decision

The skill loader now enforces the existing grant schema before semantic use and requires well-formed requesters and independent human approver identities. Missing, malformed, schema-invalid, expired, excessive-scope and nonhuman-approved grants fail. Unknown `revoked` fields are rejected rather than ignored. This is structural hardening, not authenticated approval or a revocation registry. Existing admitted test fixtures are synthetic; no actual skill admission or grant was produced.

The real authority gap is described in `docs/briefs/2026-10-03-approval-attestation.md`: caller-supplied `human.*` strings and invented decision references still do not prove a human acted.

Recommended candidate: GitHub-authenticated designated human approval tied to the exact subject digest and operations, ingested into a protected approval registry that the runtime principal cannot write. Python resolves the registry; PostgreSQL independently verifies the protected row, subject, scope, expiry and revocation. This recommendation is not a selected trust root, a fabricated approval, or an applied database migration. A signed-approval service is an alternative with different key custody and deployment burdens.

Before activation, choose the trust root and confirm whether PostgreSQL must enforce it independently. Then implement resolver, registry isolation, tamper/scope/expiry/revocation tests, migration refusal for unproved existing active records, and a real approval-and-resume trial. Do not reclassify all sixteen moves as verified based on this patch.

## Stop, resume, and rollback

Stop before real grants, provider mutations, license adoption, production deployment, or Golden promotion without their scoped evidence and authority. Resume by reading current main, regenerating the workplan, refreshing acceptance evidence, and checking hosted results at the proposed head. Roll back code using a reviewed revert; preserve receipts and audit history. This workstream earns a reusable admission-debt inspection command and structural grant hardening. It does not earn a Golden release.
