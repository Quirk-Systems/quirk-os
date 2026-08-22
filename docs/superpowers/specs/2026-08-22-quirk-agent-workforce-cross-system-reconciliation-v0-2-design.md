---
spec_id: quirk.agent-workforce.cross-system-reconciliation
title: Quirk Agent Workforce Cross-System Reconciliation
version: 0.2.0
decision_date: 2026-08-22
human_decision: APPROVE_SPEC_ONLY_RECONCILIATION
document_status: approved-for-spec-only-commit
architecture_status: approved-successor-design
catalog_status: candidate-unchanged
runtime_status: inactive
projection_status: not-created
authority_scope: local-draft-read-only-census-and-one-spec-only-commit
target_repository: Quirk-Systems/quirk-os
target_parent_commit: ab031a7e5c51704acaf15da0f4f705cc6f6a8531
target_branch: spec/quirk-agent-workforce-v0-2
incorporates_spec: quirk.agent-workforce.dual-plane-design@0.1.0
incorporates_commit: ab031a7e5c51704acaf15da0f4f705cc6f6a8531
incorporates_digest: sha256:9c572e32260efd271e38b152bd4fb93340a5fd4fd2c41d5206672bc098c99a6a
supersedes: quirk.agent-workforce.dual-plane-design@0.1.0
---

# Quirk Agent Workforce Cross-System Reconciliation

## 1. Decision and authority boundary

This specification is the 0.2.0 successor to the approved Quirk Agent Workforce Dual-Plane Design 0.1.0. It incorporates the exact 0.1.0 document identified above and changes only the cross-system contract described here. Unchanged role records, lifecycle rules, non-authorities, separation-of-duties laws, Preference Graph firewall, projection design, and rollout gates remain effective by exact reference.

The eleven-role candidate catalog remains exactly QAG-000 through QAG-100 in increments of ten. No role is added, removed, admitted, activated, projected, installed, invoked, or granted authority. The incumbent `agent.quirk-sync-steward` remains separate and unchanged.

The human decision authorizes:

1. a local successor draft;
2. a narrowly scoped read-only census across named systems;
3. one successor-spec commit in `Quirk-Systems/quirk-os`.

It does not authorize:

- an agent manifest, GitHub profile, prompt, skill, plugin, submission pack, schema, validator, fixture, compiler, workflow, connector, model execution, runtime, database object, migration, package, container, deployment, API key, secret, or external projection;
- a Google Drive, Notion, Airtable, Supabase, Cloudflare, OpenAI, Vercel, commerce-provider, or other provider write;
- a GitHub pull request, review, merge, release, ruleset, CODEOWNERS change, organization setting, package publication, or agent activation;
- a product, market, commercial, safety, legal, license, rights, or efficacy claim;
- a Preference Graph read, inference, proposal promotion, write, update, or mutation.

Connector availability, repository permission, provider support, role title, successful read, successful tool call, durable state, generated artifact, trace, receipt, or human-in-the-loop feature is capability evidence only. None is execution authority or Quirk admission.

This specification does not authorize merge.

## 2. Successor composition and precedence

The effective 0.2.0 design is the immutable composition of:

1. the exact 0.1.0 document at commit `ab031a7e5c51704acaf15da0f4f705cc6f6a8531` and digest `sha256:9c572e32260efd271e38b152bd4fb93340a5fd4fd2c41d5206672bc098c99a6a`; and
2. this reconciliation document at its eventual exact commit and digest.

This document controls where the two conflict. It replaces the generic grant language in 0.1.0 with typed grant kinds, extends `WorkOrder` with component-admission binding, adds an external human legal/OSS-counsel gate, strengthens receipt identity, and requires digest-bound evidence manifests.

No implementation may copy only the convenient half of the composition. Missing either exact document, any digest mismatch, or an unknown successor fails closed.

## 3. Evidence classification from the read-only census

The census was deliberately non-mutating. It establishes current evidence boundaries, not runtime truth.

| Surface | Observed evidence | Classification | Consequence |
|---|---|---|---|
| `Quirk-Systems/quirk-os` | 0.1.0 branch is one commit ahead of main with one 692-line design file | repository evidence | Valid design baseline only |
| GitHub code search | No indexed `ComponentAdmissionRef` or typed three-grant successor was found in the searched Quirk repositories | bounded negative search | Successor machinery is not evidenced; search absence is not proof of global absence |
| Notion | `Quirk Sync Control Plane — Candidate` declares itself a projection and points to GitHub as source | noncanonical projection claim | May inform compatibility; cannot prove the runtime or authorize work |
| Airtable | `Quirk Work Control Plane — Candidate Registry v0.1.0` exposes candidate-only tables whose descriptions deny canon, execution, and receipt authority | noncanonical projection schema | May inform projection shape; cannot define source semantics |
| Google Drive | A bounded metadata search returned no exact workforce document title and several fuzzy unrelated results | access/search evidence | No Drive document is imported; no absence or preference claim is made |
| Cloudflare | Current primary documentation was reviewed; no authenticated Cloudflare inventory tool or installed local CLI was available in this session | documentation plus access limitation | No account/resource claim; no installation or fallback permitted |
| OpenAI | Current primary Agents SDK and Sandbox Agents documentation was reviewed | provider documentation | Runtime features are compatibility inputs only |
| GitHub custom agents | Current primary configuration and organization documentation was reviewed | provider documentation | Platform schema remains preview and must be reverified before implementation |

Claims inside an external projection remain `UNVERIFIED_PROJECTION_CLAIM` until rebound to exact source, environment, evidence, and receipt. A projection saying that tables, runtime, RLS, bindings, or deployments exist is not proof that they exist now or existed as claimed.

## 4. Three planes, not one vague agent blob

~~~mermaid
flowchart TD
    H["Human decision plane"] --> S["Semantic source plane"]
    S --> P["Provider projection plane"]
    P --> R["Provider runtime plane"]
    R --> E["Evidence and receipts"]
    E --> H
~~~

- **Human decision plane:** grants, admissions, risk acceptance, legal/rights decisions, activation, release, and revocation.
- **Semantic source plane:** exact reviewed Quirk contracts in `quirk-os`.
- **Provider projection plane:** generated GitHub profiles, Notion pages, Airtable records, Drive documents, spreadsheets, dashboards, or package metadata.
- **Provider runtime plane:** GitHub Copilot execution, OpenAI Agents SDK runs, Cloudflare Agents, Supabase/Postgres, commerce adapters, CI, containers, models, MCP, and SaaS connectors.
- **Evidence plane:** source-bound manifests, evaluator declarations, traces, test outputs, receipts, and reconciliations.

Provider projection is not provider runtime. Provider runtime is not semantic source. Evidence is not authority. A human approval UI is not a Quirk grant unless the exact decision is captured in a valid `DecisionReceipt` and the runtime action remains within the effective grant intersection.

## 5. Canonical authority envelope and non-interchangeable grant kinds

Future grants share one canonical envelope named `AuthorityGrantEnvelope`. The envelope supplies common identity, scope, time, revocation, and receipt fields. It MUST contain exactly one `grant_kind` and one matching payload.

The allowed grant kinds for this design are:

| Grant kind | Permits when separately issued | Cannot permit |
|---|---|---|
| `AgentWorkGrant` | One bounded agent task, approved read/comment/routing action, or candidate branch/spec action | Component installation/runtime, commerce/customer/financial action, admission, activation, merge, or release |
| `CommerceCapabilityGrant` | One exact provider, tenant, environment, mode, resource, and commercial action with amount/state/idempotency bounds | General agent work, component installation, semantic admission, graph mutation, or reuse at another provider |
| `ComponentRuntimeGrant` | One admitted component/version/digest in one runtime/environment with exact execution, storage, network, tool, and secret-reference scope | Agent task expansion, commerce authority, semantic admission, or provider-wide permission |

The common envelope binds:

- grant ID, version, issuer, grantee, decision receipt, and issue time;
- purpose, task, acceptance criteria, and prohibited outcomes;
- system, provider, stable repository/project/account/tenant/environment identifiers;
- exact resources, paths, refs, base/head/tree, actions, tools, and field transitions;
- data classes, secret references, network/egress, retention, and deletion duties;
- start, expiry, revocation, non-delegation, non-reuse, and supersession;
- required evidence, rollback, reconciliation, and execution receipts.

Grant kinds MUST NOT be cast, inherited, unioned, widened, treated as aliases, or inferred from overlapping fields. One action requiring two kinds requires two valid grants and satisfies both independently. Decomposing work cannot increase their aggregate authority.

Unknown, omitted, wildcard, stale, revoked, digest-mismatched, environment-mismatched, or cross-kind grants fail closed.

For the eleven-role workforce, every future `WorkOrder` uses `AgentWorkGrant`. A role cannot issue, approve, or convert its own grant.

## 6. Component admission is a prerequisite, not a footnote

Every future `WorkOrder` MUST carry a complete list of `ComponentAdmissionRef` objects for every skill, plugin, package, model, provider, tool mapping, MCP server, SaaS connector, container, template/starter, runtime, and executable dependency the work may use.

`ComponentAdmissionRef` binds at minimum:

| Field group | Required binding |
|---|---|
| Identity | stable component ID, kind, owner/source, exact version or immutable revision |
| Integrity | content/artifact digest, provenance/attestation, dependency lock, and SBOM reference where applicable |
| Rights | license, source terms, redistribution/productization limits, provenance completeness, and human counsel decision when required |
| Security | vulnerability review, threat model, secrets/data classes, tenant isolation, sandbox/containment, network/egress, and update policy |
| Runtime | provider, environment, executable surfaces, storage/state, ports, schedules, tools, MCP, side effects, and observability |
| Exit | uninstall/disable path, data export/deletion, rollback, provider substitution seam, and reconciliation duties |
| Governance | lifecycle, exact admission decision receipt, allowed uses, expiry/review date, and supersession |

A role catalog reference such as `superpowers:*`, `product-design:*`, `data-analytics:*`, a GitHub alias, OpenAI SDK, Cloudflare Agents SDK, or Skill Submission Pack Writer is a candidate composition coordinate only. It is not a resolved component, installation request, admission record, runtime grant, or permission to package or submit a skill.

Transitive components are explicit. Mutable tags, floating branches, unpinned templates, latest-version selectors, provider defaults, dynamically discovered MCP tools, and runtime-installed dependencies are prohibited until separately admitted and digest-bound.

## 7. External human legal and OSS-counsel gate

The candidate catalog remains exactly eleven roles. Legal and OSS-counsel judgment is an external accountable human gate, not a twelfth agent.

The separation is:

1. QAG-090 Research & Evidence Lead gathers sources, license text, provenance, rights constraints, and unresolved questions.
2. QAG-050 Security, Privacy & Consent Steward identifies privacy, data, security, and consent blockers.
3. QAG-020 and QAG-080 bind architecture, package, SBOM, provenance, and exit evidence.
4. An identified human legal/OSS reviewer issues a narrow `LegalRightsReviewReceipt` or records `NOT_REVIEWED`/`COUNSEL_REQUIRED`.
5. Bryan alone makes the Quirk admission decision.

No agent may claim legal sufficiency, legal advice, license compatibility, rights clearance, privilege, regulatory compliance, or productization permission. A missing counsel identity, scope, jurisdiction, source set, exact component digest, or decision is a HOLD where the use requires counsel.

## 8. Receipt identity and storage integrity

Every receipt MUST distinguish:

- `receipt_id`: content-derived immutable identity;
- `receipt_content_digest`: digest of the canonical receipt payload;
- `subject_id`, `subject_version`, and `subject_content_digest`;
- `subject_repository_id`, `subject_commit_sha`, and `subject_tree_sha` where relevant;
- `receipt_commit_sha`: the commit that stores the receipt, when known externally;
- `supersedes_receipt_id` and correction reason;
- issuer/actor identity, effective grant reference, timestamps, outcome, and limitations.

`subject_commit_sha` is not `receipt_commit_sha`. The commit storing a receipt is not automatically the commit the receipt evaluates. A receipt payload cannot require its own future containing commit SHA as part of the content from which its identity is derived; the containing commit is recorded by a separate index/attestation or later superseding receipt.

One mutable bootstrap path MUST NOT be the sole evidence history. Durable storage uses content-addressed or versioned receipts. A mutable `latest` pointer MAY exist only when it records the prior and next receipt IDs/digests, preserves both objects, has an authorized transition, and leaves its own receipt.

Storage success, trace presence, UI history, database row existence, or a provider action ID does not prove authorization. Corrections supersede; they never rewrite.

## 9. Digest-bound evidence manifest

Every implementation, evaluation, projection, release, and cross-system claim requires an `EvidenceManifest` that binds evidence to the exact subject.

The manifest includes:

- manifest ID/version/digest, author, creation time, and evidence class;
- stable repository/project/provider identifiers;
- exact base, head, merge base, tree, and ancestry result;
- complete required-path inventory with modes, blob IDs, and content digests;
- changed-file record separately labeled as a diff, never a full-tree inventory;
- source records with locator, immutable revision where available, retrieval time, digest, rights status, and trust classification;
- commands/checks with versions, environment/container identity, exit status, bounded output digest, and limitations;
- provider reads with tenant/environment, query scope, timestamp, pagination/completeness, and access failures;
- claims explicitly labeled `FACT`, `INFERENCE`, `PROPOSAL`, `UNVERIFIED_PROJECTION_CLAIM`, or `OPEN`;
- missing evidence, contradictions, counterevidence, partial failure, and stale/drift status;
- exact evaluator declaration, verdict, decision, and supersession references.

A changed-file list cannot prove the full tree. An absent path in a diff is `UNPROVEN_BY_THIS_RECORD`, not `MISSING_FROM_TREE`. A successful helper script cannot prove remote state without readback. A projection cannot cite itself as the source that proves its own claims.

Analytics, spreadsheet, document, dashboard, or chart outputs are derived projections. They become evidence only when their source query/data snapshot, transformations, row grain, exclusions, freshness, and artifact digest are bound in the manifest.

## 10. Provider-specific containment

| Plane | Candidate use | Required future containment | Status now |
|---|---|---|---|
| GitHub custom agent | Deterministic organization profile projection | Explicit tools because omission enables all; automatic invocation disabled; candidate user invocation disabled; no MCP; exact source/compiler/profile digests; separate `.github-private` protection | Not created |
| OpenAI Agents SDK | Optional execution adapter for bounded application workflows | Separate admitted app/runtime; exact model/provider/tools; harness/compute separation; approvals, state, traces, network, data, and secret policy; `ComponentRuntimeGrant` | Not created or executed |
| OpenAI Sandbox Agent | Optional isolated compute adapter | Exact manifest, mounts, files, commands, packages, ports, snapshots, credentials, egress, session lifecycle, and destruction/export policy | Not created or executed |
| Cloudflare Agents | Optional durable runtime adapter | Exact Worker/account/environment; Durable Object/state schema; storage, WebSocket/RPC, schedules, Workflows, MCP, browser, email, payments, observability, migration, deletion, and human-approval policy | Not created, inventoried, or deployed |
| Notion | Human-readable orientation projection | Exact page/database, source digest, projection receipt, no command/authority semantics | Read-only candidate page observed |
| Airtable | Operational projection | Exact base/table/record mapping, source digest, no receipt/admission/command semantics | Read-only candidate schema observed |
| Google Drive/Docs/Sheets | Work products and review packs | Exact file, source provenance, content digest/revision, audience, sensitivity, retention, and no-canon notice | Metadata search only; no workforce artifact imported |
| Data Analytics artifacts | Derived evidence views | Bound source query/snapshot, transformation, grain, completeness, digest, and non-authority notice | None created |
| Skill/plugin submission | Candidate packaging and review evidence | Exact source/version/digest, manifest, evaluation, dependency/rights/security evidence, separate submission and publication grants | Not created or submitted |

The same semantic role MAY eventually have multiple provider adapters. Each adapter is a separately admitted component and separately activated projection/runtime. Provider-native state, memory, sessions, traces, schedules, approvals, or identities MUST NOT be silently synchronized or treated as Quirk Memory or Preference Graph content.

## 11. Sync Steward boundary under the successor

The eleven roles may produce an exact `ProjectionRequest` or `ReconciliationRequest`. Only the incumbent Sync Steward, under its own exact contract, component admissions, typed grants, and system-specific receipts, may perform approved cross-platform projection or reconciliation within its admitted remit.

The existing candidate Sync Steward manifest contains provider capability declarations. Those declarations are dormant candidate ceilings. They do not prove current credentials, runtime, connector installation, provider state, migration authority, or execution permission. This successor does not modify or admit that manifest.

No generic multi-system connector, Choreographer handoff, analytics export, Airtable automation, Notion button, Drive script, GitHub Action, OpenAI handoff, or Cloudflare workflow may impersonate the Sync Steward or route around it.

## 12. Required adversarial additions

The 0.1.0 fixture catalog remains required. A future implementation adds at least:

| Fixture | Required fail-closed result |
|---|---|
| `component_reference_as_admission` | Reject named/available/imported component without exact admitted `ComponentAdmissionRef` |
| `mutable_dependency_or_template` | Reject floating version, tag, branch, starter, provider default, or transitive dependency |
| `grant_kind_confusion` | Reject agent, commerce, and runtime grants used outside their exact kind |
| `grant_union_escalation` | Reject combining partial grants into wider authority |
| `provider_runtime_equivalence` | Reject GitHub/OpenAI/Cloudflare projection or runtime as interchangeable |
| `connector_access_as_authority` | Reject authenticated access or successful read/write as permission |
| `legal_counsel_impersonation` | Reject agent-issued rights or legal clearance |
| `receipt_subject_storage_conflation` | Reject subject SHA/tree and receipt-storage commit treated as the same identity |
| `mutable_pointer_as_history` | Reject overwritten latest pointer without preserved versioned receipts and transition receipt |
| `diff_as_tree_proof` | Reject changed-file record offered as complete topology evidence |
| `projection_claim_as_runtime_fact` | Reject Notion/Airtable/Drive/dashboard claim without source-bound proof |
| `analytics_projection_as_evidence` | Reject chart/table/report without exact source snapshot/query/transformation/digest |
| `provider_hitl_as_quirk_grant` | Reject native approval UI without matching Quirk decision and typed grant |
| `state_as_memory_or_preference` | Reject provider session/state/storage as Quirk Memory or Preference Graph evidence |
| `skill_pack_as_activation` | Reject packaged, validated, submitted, installed, or published skill as agent admission/activation |
| `sync_steward_impersonation` | Reject any other role or workflow performing cross-system reconciliation |

## 13. Acceptance criteria for this reconciliation tranche

This tranche passes only when:

- one new Markdown successor spec is committed from exact parent `ab031a7e5c51704acaf15da0f4f705cc6f6a8531`;
- the original 0.1.0 file remains byte-identical at its recorded digest;
- the successor explicitly preserves exactly eleven candidate roles and the separate incumbent Sync Steward;
- the three typed grant kinds cannot impersonate or widen one another;
- every future WorkOrder requires exact component-admission references;
- external human legal/OSS counsel is a gate, not a role or agent capability;
- receipt subject identity, receipt content identity, and receipt storage identity are distinct;
- evidence manifests distinguish full-tree proof, diffs, projections, provider reads, derived analytics, and unverified claims;
- GitHub, OpenAI, Cloudflare, Drive, Notion, Airtable, analytics, documents, spreadsheets, skills, and plugins remain provider-specific candidate surfaces;
- no manifest, profile, skill, submission pack, schema, validator, fixture, code, dependency, connector, API key, runtime, database object, deployment, projection, or provider configuration is created or changed;
- no pull request, review, merge, admission, activation, publication, external provider write, or Preference Graph effect occurs;
- exact parent, new commit, two-file compare, original digest, successor digest, and no-write census are verified and reported.

The next gate after this commit is fresh human review of the exact successor head and digest. Implementation planning remains blocked until that review separately approves the composed 0.2.0 design.

## 14. Required primary references for later implementation

Current behavior must be reverified at implementation time because these provider surfaces change:

- GitHub custom-agent configuration: https://docs.github.com/en/copilot/reference/custom-agents-configuration
- GitHub organization custom-agent repository: https://docs.github.com/en/copilot/how-tos/administer-copilot/manage-for-organization/prepare-for-custom-agents
- GitHub custom-agent creation: https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/create-custom-agents
- OpenAI Agents SDK: https://developers.openai.com/api/docs/guides/agents
- OpenAI Sandbox Agents: https://developers.openai.com/api/docs/guides/agents/sandboxes
- Cloudflare Agents: https://developers.cloudflare.com/agents/
- Cloudflare human-in-the-loop patterns: https://github.com/cloudflare/agents/blob/main/docs/agents/human-in-the-loop.md

This document is a decision artifact. It is not an agent, runtime, connector, projection, deployment, admission, or execution grant.
