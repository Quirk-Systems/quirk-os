---
spec_id: quirk.agent-workforce.cross-system-reconciliation
title: Quirk Agent Workforce Cross-System Reconciliation
version: 0.2.1
revision_date: 2026-08-22
revision_basis: exact-head-human-decision-revise
reviewed_head: db58a5b4d9952c765bebc4e4fd08dc115e5e5af6
reviewed_payload_digest: sha256:b83ff5be80b8d22c5bca7d1b4cc436d5ae0db64b9a1ba058ba2a19b1dfa51cf7
human_decision: REVISE_COMPOSED_DESIGN_ONLY
document_status: committed-awaiting-exact-head-review
architecture_status: candidate-awaiting-exact-head-review
catalog_status: candidate-unchanged
runtime_status: inactive
projection_status: not-created
authority_scope: one-spec-only-corrective-commit
target_repository: Quirk-Systems/quirk-os
target_parent_commit: db58a5b4d9952c765bebc4e4fd08dc115e5e5af6
target_branch: spec/quirk-agent-workforce-v0-2
incorporates_spec: quirk.agent-workforce.dual-plane-design@0.1.0
incorporates_commit: ab031a7e5c51704acaf15da0f4f705cc6f6a8531
incorporates_digest: sha256:9c572e32260efd271e38b152bd4fb93340a5fd4fd2c41d5206672bc098c99a6a
supersedes: null
proposes_superseding: quirk.agent-workforce.dual-plane-design@0.1.0
approval_decision_receipt: null
---

# Quirk Agent Workforce Cross-System Reconciliation

## 1. Decision and authority boundary

This specification is the corrected 0.2.1 candidate successor to the approved Quirk Agent Workforce Dual-Plane Design 0.1.0. It incorporates the exact 0.1.0 document identified above and proposes changing only the cross-system contract described here. Until an external exact-head human decision receipt approves this candidate, the 0.1.0 design remains the effective approved design. Unchanged role records, lifecycle rules, non-authorities, separation-of-duties laws, Preference Graph firewall, projection design, and rollout gates remain effective by exact reference.

The eleven-role candidate catalog remains exactly QAG-000 through QAG-100 in increments of ten. No role is added, removed, admitted, activated, projected, installed, invoked, or granted authority. The incumbent `agent.quirk-sync-steward` remains separate and unchanged.

The exact-head `REVISE` decision authorizes:

1. correction of this candidate specification on its existing branch;
2. one spec-only corrective commit in `Quirk-Systems/quirk-os`; and
3. deterministic readback needed to identify the corrected head, tree, scope, and digest.

It does not authorize:

- an agent manifest, GitHub profile, prompt, skill, plugin, submission pack, schema, validator, fixture, compiler, workflow, connector, model execution, runtime, database object, migration, package, container, deployment, API key, secret, or external projection;
- a Google Drive, Notion, Airtable, Supabase, Cloudflare, OpenAI, Vercel, commerce-provider, or other provider read or write except the exact GitHub readback required to verify this corrective commit;
- a GitHub pull request, review, merge, release, ruleset, CODEOWNERS change, organization setting, package publication, or agent activation;
- a product, market, commercial, safety, legal, license, rights, or efficacy claim;
- a Preference Graph read, inference, proposal promotion, write, update, or mutation.

Connector availability, repository permission, provider support, role title, successful read, successful tool call, durable state, generated artifact, trace, receipt, or human-in-the-loop feature is capability evidence only. None is execution authority or Quirk admission.

This specification does not authorize merge.

### 1.1 Approval and supersession are external decisions

This candidate MUST NOT mark itself approved, effective, admitted, or superseding. Approval and supersession require a separate human-issued `DecisionReceipt` bound to the exact candidate commit, tree, payload digest, reviewed scope, decision vocabulary, limitations, and invalidators. The receipt MUST distinguish the reviewed subject identity from the commit or system that stores the receipt.

An `APPROVE` receipt MAY approve the composed design without superseding 0.1.0. A `SUPERSEDE` receipt MUST explicitly identify the prior design being displaced. Silence, branch existence, a successful commit, provider access, passing checks, high confidence, or satisfaction of security prerequisites is not either decision.

The user's conditional direction that downstream actions require high confidence and necessary security measures is a gating policy, not a wildcard grant. A downstream action becomes executable only through the exact intersection of all required grant kinds, after its necessity, scoped confidence basis, security prerequisites, rollback, and receipt obligations are recorded. No conditional policy can supply a missing resource, operation, environment, audience, amount, expiry, or human decision.

Every future provider or runtime action MUST carry an `ActionReadinessRecord` with:

| Gate | Required proof |
|---|---|
| Exact action | Stable actor, provider/account/project/environment/resource, operation and state transition, data class, start/expiry, and prohibited outcomes |
| Necessity | Approved outcome, evidence the action is needed now, no-op consequence, and why a narrower or non-mutating alternative is insufficient |
| Confidence | `HIGH` only when source freshness, target identity, preconditions, expected result, counterevidence, uncertainty, and invalidators are recorded; labels without evidence fail closed |
| Security | Admitted components, least privilege, separation of duties, secret references rather than secret values, data minimization, network/egress bounds, tenant isolation, backup, rollback, idempotency, rate/cost limits, observability, and incident recovery as applicable |
| Authority intersection | Every required typed grant and human decision receipt independently valid for the exact action; no grant inferred from confidence or necessity |
| Evidence return | Pre-state, action/provider identifier, bounded logs, post-state readback, result, side effects, rollback state, and immutable `ExecutionReceipt` |

Every hard gate is conjunctive. A high aggregate score cannot average away a failed authority, identity, privacy, security, rollback, or receipt requirement. Pull-request creation, merge, public deployment, domain routing, database migration, network-policy change, telemetry control, and Preference Graph mutation remain separately decidable actions even when they support one approved outcome.

## 2. Successor composition and precedence

The candidate composed 0.2.1 design proposed for approval is:

1. the exact 0.1.0 document at commit `ab031a7e5c51704acaf15da0f4f705cc6f6a8531` and digest `sha256:9c572e32260efd271e38b152bd4fb93340a5fd4fd2c41d5206672bc098c99a6a`; and
2. this corrected reconciliation document at its eventual exact commit and digest.

If an external exact-head decision receipt approves this composition, this document controls where the two conflict. It proposes replacing the generic grant language in 0.1.0 with typed grant kinds, extending `WorkOrder` with component-admission binding, adding an external human legal/OSS-counsel gate, strengthening receipt identity, and requiring digest-bound evidence manifests.

No implementation may copy only the convenient half of the composition. Missing either exact document, any digest mismatch, or an unknown successor fails closed.

## 3. Evidence classification from the read-only census

The census was deliberately non-mutating. It establishes current evidence boundaries, not runtime truth.

| Surface | Observed evidence | Classification | Consequence |
|---|---|---|---|
| `Quirk-Systems/quirk-os` | 0.1.0 branch is one commit ahead of main with one 692-line design file | repository evidence | Valid design baseline only |
| GitHub code search | No indexed `ComponentAdmissionRef` or the then-proposed typed three-grant successor was found in the searched Quirk repositories | bounded historical negative search | Implementation machinery is not evidenced; search absence is not proof of global absence |
| Notion | `Quirk Sync Control Plane — Candidate` declares itself a projection and points to GitHub as source | noncanonical projection claim | May inform compatibility; cannot prove the runtime or authorize work |
| Airtable | `Quirk Work Control Plane — Candidate Registry v0.1.0` exposes candidate-only tables whose descriptions deny canon, execution, and receipt authority | noncanonical projection schema | May inform projection shape; cannot define source semantics |
| Google Drive | A bounded metadata search returned no exact workforce document title and several fuzzy unrelated results | access/search evidence | No Drive document is imported; no absence or preference claim is made |
| Cloudflare | Current primary documentation was reviewed; no authenticated Cloudflare inventory tool or installed local CLI was available in this session | documentation plus access limitation | No account/resource claim; no installation or fallback permitted |
| OpenAI | Current primary Agents SDK and Sandbox Agents documentation was reviewed | provider documentation | Runtime features are compatibility inputs only |
| GitHub custom agents | Current primary configuration and organization documentation was reviewed | provider documentation | Platform schema remains preview and must be reverified before implementation |

Claims inside an external projection remain `UNVERIFIED_PROJECTION_CLAIM` until rebound to exact source, environment, evidence, and receipt. A projection saying that tables, runtime, RLS, bindings, or deployments exist is not proof that they exist now or existed as claimed.

## 4. Five planes, not one vague agent blob

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
| `AgentWorkGrant` | One bounded agent task, approved read/comment/routing action, or candidate branch/spec action | Component installation/runtime, provider-resource control, commerce/customer/financial action, publication, admission, activation, merge, or release |
| `ProviderResourceGrant` | One exact provider, account/organization, tenant, project, environment, resource, access mode, operation class, field/state transition, and data class | Component execution, provider-wide administration, commerce authority, publication, semantic admission, graph mutation, or reuse across a resource, tenant, environment, or provider |
| `CommerceCapabilityGrant` | One exact provider, tenant, environment, mode, resource, and commercial action with amount/state/idempotency bounds | General agent work, component installation, unrelated provider-resource control, publication, semantic admission, graph mutation, or reuse at another provider |
| `ComponentRuntimeGrant` | One admitted component/version/digest in one runtime/environment with exact execution, storage, network, tool, and secret-reference scope | Agent task expansion, provider administration, commerce authority, publication, semantic admission, or provider-wide permission |
| `PublicationGrant` | One exact payload/version/digest, audience, channel, destination, exposure mode, release window, withdrawal path, and public identity | General agent work, component execution, provider administration, commerce authority, semantic admission, graph mutation, or reuse for another payload, audience, channel, or destination |

The common envelope binds:

- grant ID, version, issuer, grantee, decision receipt, and issue time;
- purpose, task, acceptance criteria, and prohibited outcomes;
- system, provider, stable repository/project/account/tenant/environment identifiers;
- exact resources, paths, refs, base/head/tree, actions, tools, and field transitions;
- data classes, secret references, network/egress, retention, and deletion duties;
- start, expiry, revocation, non-delegation, non-reuse, and supersession;
- required evidence, rollback, reconciliation, and execution receipts.

Grant kinds MUST NOT be cast, inherited, unioned, widened, treated as aliases, or inferred from overlapping fields. One action requiring multiple kinds requires every applicable grant and satisfies each independently. Decomposing work cannot increase their aggregate authority.

Unknown, omitted, wildcard, stale, revoked, digest-mismatched, environment-mismatched, or cross-kind grants fail closed.

For the eleven-role workforce, every future `WorkOrder` uses `AgentWorkGrant` and intersects it with each additional grant required by the intended effects. A role cannot issue, approve, or convert its own grant.

`ProviderResourceGrant.operation_class` MUST be one exact allowed value such as `inspect`, `query`, `export`, `create`, `update`, `delete`, `control`, `identity`, `network`, or `observability`; `*`, `admin`, `manage`, implied defaults, and undocumented provider bundles fail closed. A provider read that exposes secrets, personal data, customer data, privileged incidents, or Preference Graph material is still a governed provider-resource operation.

`PublicationGrant` is required for public deployment, external release, public URL or network exposure, domain or DNS routing to a public surface, marketplace/package publication, outbound campaign delivery, or externally visible agent communication. Creating a deployable artifact is not publication; exposing it is.

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
| GitHub custom agent | Deterministic organization profile projection | Explicit tools because omission enables all; automatic invocation disabled; candidate user invocation disabled; no MCP; exact source/compiler/profile digests; separate `.github-private` protection; `AgentWorkGrant`; `ProviderResourceGrant` for GitHub state; `PublicationGrant` for externally visible release | Not created |
| OpenAI Agents SDK | Optional execution adapter for bounded application workflows | Separate admitted app/runtime; exact model/provider/tools; harness/compute separation; approvals, state, traces, network, data, and secret policy; `ComponentRuntimeGrant`; `ProviderResourceGrant` for provider state | Not created or executed |
| OpenAI Sandbox Agent | Optional isolated compute adapter | Exact manifest, mounts, files, commands, packages, ports, snapshots, credentials, egress, session lifecycle, destruction/export policy; `ComponentRuntimeGrant`; `ProviderResourceGrant` for provider state | Not created or executed |
| Cloudflare Agents | Optional durable runtime adapter | Exact Worker/account/environment; Durable Object/state schema; storage, WebSocket/RPC, schedules, Workflows, MCP, browser, email, payments, observability, migration, deletion, and human-approval policy; runtime and provider-resource grants; publication grant for exposure | Not created, inventoried, or deployed |
| PostHog / Sentry | Product analytics, feature-control, experiment, incident, trace, and observability surfaces | Exact organization/project/environment; read versus export versus configuration mutation; sensitivity/retention/redaction; `ProviderResourceGrant`; separate runtime or publication grants for behavioral or external effects | Documentation compatibility only; no account read or change |
| Temporal | Durable workflow execution and message-driven state transition | Exact namespace/task queue/workflow type/ID/run and operation; admitted workflow code; replay/versioning/retention policy; `ProviderResourceGrant` plus `ComponentRuntimeGrant` for execution | Documentation compatibility only; no workflow started or signaled |
| Supabase | Database, Auth, Storage, Realtime, Edge Function, and policy surface | Exact organization/project/environment/schema/table/bucket/function/policy; row/data class; RLS/service-role boundary; migration/rollback; `ProviderResourceGrant` plus runtime, commerce, or publication grants where effects intersect | Documentation compatibility only; no project read or change |
| Tailscale | Identity, device, grant, route, service, and public-network surface | Exact tailnet/identity/device/tag/service/route and policy delta; lockout and rollback proof; `ProviderResourceGrant`; `PublicationGrant` for Funnel or equivalent public exposure | Documentation compatibility only; no tailnet read or change |
| Spaceship / Hostinger | Domain, DNS, hosting, VPS, account, and billing surfaces | Exact account/domain/zone/record/service/environment; TTL/propagation/rollback; ownership and spend bounds; `ProviderResourceGrant`; `PublicationGrant` for routing/exposure; `CommerceCapabilityGrant` for purchase or billing effect | Documentation compatibility only; no account, domain, DNS, hosting, or billing action |
| FastAPI Cloud | Build, deploy, hosted runtime, and publication surface | Exact source/head/artifact digest/project/environment/build/deploy target; secrets/network/rollback/observability; `ComponentRuntimeGrant`; `ProviderResourceGrant`; `PublicationGrant` for external exposure | Documentation compatibility only; no build, deployment, hosting, or publication |
| Game Studio toolchain | Candidate component set for building an interactive artifact | Exact skill/tool/version/digest, generated asset provenance, test evidence, local runtime boundary, and `ComponentAdmissionRef`; runtime grant for execution; provider-resource grant only for an exact external provider; publication grant for exposure | Named candidate coordinate only; no component admitted, build run, or artifact published |
| Notion | Human-readable orientation projection | Exact page/database, source digest, projection receipt, no command/authority semantics; `ProviderResourceGrant` for any provider read or write | Read-only candidate page observed |
| Airtable | Operational projection | Exact base/table/record mapping, source digest, no receipt/admission/command semantics; `ProviderResourceGrant` for any provider read or write | Read-only candidate schema observed |
| Google Drive/Docs/Sheets | Work products and review packs | Exact file, source provenance, content digest/revision, audience, sensitivity, retention, and no-canon notice; `ProviderResourceGrant`; `PublicationGrant` when shared beyond the approved audience | Metadata search only; no workforce artifact imported |
| Data Analytics artifacts | Derived evidence views | Bound source query/snapshot, transformation, grain, completeness, digest, and non-authority notice | None created |
| Skill/plugin submission | Candidate packaging and review evidence | Exact source/version/digest, manifest, evaluation, dependency/rights/security evidence, separate `ProviderResourceGrant` for submission-state mutation and `PublicationGrant` for publication | Not created or submitted |

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
| `grant_kind_confusion` | Reject agent, provider-resource, commerce, runtime, and publication grants used outside their exact kind |
| `grant_union_escalation` | Reject combining partial grants into wider authority |
| `provider_admin_as_component_runtime` | Reject provider account, project, tenant, configuration, identity, network, data, or control-plane action offered under only `ComponentRuntimeGrant` |
| `provider_resource_cross_scope_reuse` | Reject resource grant reused across provider, account, tenant, project, environment, resource, operation class, or data class |
| `public_exposure_without_publication_grant` | Reject deployment, DNS routing, Funnel, public URL, marketplace/package release, campaign delivery, or external communication without exact `PublicationGrant` |
| `publication_payload_or_audience_drift` | Reject publication when payload digest, audience, channel, destination, exposure window, or withdrawal path differs from the grant |
| `confidence_or_necessity_as_authority` | Reject high confidence, operational necessity, security readiness, urgency, or successful dry run offered in place of an exact grant and decision receipt |
| `security_score_averages_hard_failure` | Reject aggregate readiness score when any authority, identity, privacy, security, rollback, or receipt hard gate fails |
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

This corrective tranche passes only when:

- only this Markdown candidate specification is changed in one corrective commit whose parent is exact reviewed head `db58a5b4d9952c765bebc4e4fd08dc115e5e5af6`;
- the original 0.1.0 file remains byte-identical at its recorded digest;
- the successor explicitly preserves exactly eleven candidate roles and the separate incumbent Sync Steward;
- the five typed grant kinds cannot impersonate, substitute for, or widen one another;
- provider-resource control cannot be laundered through component runtime authority;
- public exposure cannot occur without an exact publication grant;
- every future WorkOrder requires exact component-admission references;
- external human legal/OSS counsel is a gate, not a role or agent capability;
- receipt subject identity, receipt content identity, and receipt storage identity are distinct;
- evidence manifests distinguish full-tree proof, diffs, projections, provider reads, derived analytics, and unverified claims;
- GitHub, OpenAI, Cloudflare, PostHog, Sentry, Temporal, Supabase, Tailscale, Spaceship, Hostinger, FastAPI Cloud, Game Studio, Drive, Notion, Airtable, analytics, documents, spreadsheets, skills, and plugins remain provider-specific candidate surfaces;
- no manifest, profile, skill, submission pack, schema, validator, fixture, code, dependency, connector, API key, runtime, database object, deployment, projection, or provider configuration is created or changed;
- no pull request, review, merge, admission, activation, publication, external provider write, or Preference Graph effect occurs;
- the candidate metadata records no approval or supersession before an external exact-head human decision receipt;
- exact reviewed parent, corrected commit, corrected tree, changed-file scope, original digest, corrected payload digest, and no-write census are verified and reported.

The next gate after this corrective commit is fresh human review of the exact corrected head and digest. Implementation planning remains blocked until that review separately approves the composed 0.2.1 candidate design. Approval does not itself authorize implementation, provider access, activation, publication, pull request creation, or merge.

## 14. Required primary references for later implementation

Current behavior must be reverified at implementation time because these provider surfaces change:

- GitHub custom-agent configuration: https://docs.github.com/en/copilot/reference/custom-agents-configuration
- GitHub organization custom-agent repository: https://docs.github.com/en/copilot/how-tos/administer-copilot/manage-for-organization/prepare-for-custom-agents
- GitHub custom-agent creation: https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/create-custom-agents
- OpenAI Agents SDK: https://developers.openai.com/api/docs/guides/agents
- OpenAI Sandbox Agents: https://developers.openai.com/api/docs/guides/agents/sandboxes
- Cloudflare Agents: https://developers.cloudflare.com/agents/
- Cloudflare human-in-the-loop patterns: https://github.com/cloudflare/agents/blob/main/docs/agents/human-in-the-loop.md
- PostHog feature flags: https://posthog.com/docs/feature-flags/start-here
- Temporal workflow messages: https://docs.temporal.io/sending-messages
- Supabase Row Level Security: https://supabase.com/docs/guides/database/postgres/row-level-security
- Supabase Edge Functions: https://supabase.com/docs/guides/functions
- Tailscale grants: https://tailscale.com/docs/reference/syntax/grants
- Spaceship Knowledgebase: https://www.spaceship.com/knowledgebase/
- Hostinger DNS management: https://www.hostinger.com/support/1583249-how-to-manage-dns-records-at-hostinger/
- FastAPI Cloud deployment: https://fastapicloud.com/docs/fastapi-cloud-cli/deploy/
- Sentry documentation: https://docs.sentry.io/

This document is a decision artifact. It is not an agent, runtime, connector, projection, deployment, admission, or execution grant.
