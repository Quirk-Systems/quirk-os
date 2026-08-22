---
spec_id: quirk.agent-workforce.dual-plane-design
title: Quirk Agent Workforce Dual-Plane Design
version: 0.1.0
decision_date: 2026-08-22
human_decision: APPROVE
document_status: approved-for-spec-only-commit
architecture_status: approved-design
catalog_status: candidate
runtime_status: inactive
projection_status: not-created
authority_scope: written-design-spec-and-spec-only-commit
target_repository: Quirk-Systems/quirk-os
target_base_sha: b0a7d42d982c91effe2e6c1882d846d189326764
future_projection_repository: Quirk-Systems/.github-private
supersedes: null
---

# Quirk Agent Workforce Dual-Plane Design

## 1. Decision and authority boundary

The approved design is a governed dual-plane architecture with exactly eleven new candidate roles:

1. Quirk-Systems/quirk-os is the future semantic source plane for admitted agent contracts, lifecycle, evaluation, and projection policy.
2. Quirk-Systems/.github-private/agents may later be the organization-private GitHub projection plane for deterministic profiles compiled from admitted source contracts.

This document is a decision artifact, not an executable workforce artifact.

The human decision authorizes only this written design and one spec-only commit in quirk-os. The role identifiers, titles, responsibilities, skill references, tool aliases, handoffs, and future file paths are candidate design records. Senior, principal, director, steward, and lead titles describe intended remit; they are not evidence of competence, admission, availability, or performance.

This decision does not:

- create or admit an Agent object, manifest, registry, namespace, prompt, profile, skill, schema, validator, generator, workflow, fixture, connector, runtime, database object, deployment, package, GitHub setting, CODEOWNERS rule, or ruleset;
- make any role Current, Active, Live, Usable, Chooseable, installed, organization-available, automatically invocable, or manually invocable;
- approve a model/provider, tool mapping, MCP server, external connector, secret, credential, network route, API exposure, or production action;
- authorize a GitHub pull request, review, merge, release, branch-protection change, organization change, deployment, publication, transaction, external message, or package operation;
- authorize a Supabase schema, table, view, projection, migration, read, write, or other database effect;
- authorize a Preference Graph read, inference, write, update, or mutation;
- validate a product, commercial, market, safety, rights, or efficacy claim;
- alter, expand, or reinterpret the human-admitted quirk.products.beauty boundary or approve the Taste Engine machinery stacked on it.

Catalog references to actions or systems describe future maximum boundaries. They are not current capability, implementation evidence, or execution authority. A commit records the decision; it does not expand it. This decision does not authorize merge.

## 2. Normative distinctions

MUST, MUST NOT, SHOULD, and MAY are normative.

- Capability is not authority.
- Candidate is not admitted.
- Admitted is not projected.
- Projected is not installed.
- Installed is not active.
- Active is not authorized for every task.
- Merged is not active or approved.
- Generated is not reviewed.
- Available is not invoked.
- A tool permission is not a grant.
- A handoff is not an authority transfer.
- A projection is not semantic truth.
- Storage is not consent.
- History is not authority.
- Comments are not commands.
- Silence, urgency, prior approval, successful CI, successful execution, and model confidence are not consent.

## 3. Repository evidence at the design baseline

The design is bound to quirk-os main SHA b0a7d42d982c91effe2e6c1882d846d189326764.

At that baseline:

- agents/quirk-sync-steward/agent.yaml records agent.quirk-sync-steward version 0.2.0 as candidate with a propose ceiling;
- policies/manifest-admission-policy.yaml records no-self-approval, exact evaluated-hash binding, explicit grants, legal transitions, evidence for activation, and protected actions;
- policies/receipt-immutability-policy.yaml requires append-only receipts and correction by supersession;
- docs/canon/AGENT-PLATFORM-SYSTEM-PROMPTS.md defines twelve prompt modules and authority-ordered prompt layers;
- README.md states that consequential mutations owe receipts and separates polished contracts from executable Golden status;
- quirk-os main has no branch protection or required status checks;
- Quirk-Systems/.github-private exists, but no organization agent projection is created by this tranche.

The absence of installed protection is a material fact. This document, a future CODEOWNERS file, or passing CI would not itself be a GitHub ruleset.

## 4. Objectives and non-goals

The workforce is designed to provide senior professional coverage across product, program, architecture, engineering, platform operations, security, privacy, consent, data, evaluation, release, research, commerce, and integrations while preserving:

- Bryan's human decision authority;
- bounded assignments and safe refusal;
- explicit cross-system grants that cannot silently expand;
- deterministic and revocable projections;
- exact-head and exact-digest review;
- inspectable provenance and append-only receipts;
- separation of implementation, evaluation, admission, and release;
- evidence-bound claims;
- reversible rollout and fail-closed behavior;
- durable handoffs without implicit delegation.

The workforce is not an autonomous company, a self-appointing hierarchy, a substitute for accountable humans, a general authorization layer, or a route around existing domain boundaries.

## 5. Dual-plane architecture

~~~mermaid
flowchart TD
    H["Human decision"] --> S["quirk-os source contract"]
    S --> V["Validation and evaluation"]
    V --> P["Deterministic profile projection"]
    P --> R["Private GitHub projection review"]
    R --> A["Separate admission and activation"]
    A --> W["Bounded work order and receipts"]
~~~

### 5.1 Semantic source plane

Once separately implemented and admitted, quirk-os is the semantic authority for:

- stable agent identity and immutable version;
- lifecycle state;
- human owner;
- purpose and responsibility boundary;
- inputs, outputs, non-authorities, and stop conditions;
- readable, writable, and protected scopes;
- tool-policy requirements and provider mappings;
- authority, consent, handoff, evidence, and receipt references;
- evaluation suites;
- projection compiler version;
- source content digest.

This specification approves that architectural direction. It does not create the source contracts.

### 5.2 GitHub projection plane

Quirk-Systems/.github-private/agents may later contain generated organization profiles. A projection:

- derives from one exact, admitted source ID, version, and digest;
- carries the source path and digest, compiler version and digest, target GitHub schema version, and projection digest;
- may narrow but never widen source scope, authority, tools, or lifecycle;
- cannot define, enlarge, repair, or override semantic truth;
- contains no secret, credential, token, personal data, or Preference Graph content;
- cannot activate itself, modify its source, grant authority, merge, or deploy;
- is invalid when its source, compiler, target schema, or output digest is stale or unknown.

GitHub availability, successful execution, merge, installation, invocation, or model selection is not Quirk admission. Manual semantic edits to a generated profile are projection drift and MUST fail verification. Unknown or unmapped fields fail closed.

The cross-repository sequence is source decision first and candidate projection change second. Neither change is atomic with, approved by, or authorized by the other.

### 5.3 Source precedence

Future prompt compilation follows the existing Quirk order:

1. Platform invariant
2. Organization governance
3. Repository or project instruction
4. Agent manifest
5. Skill contract
6. Purpose-scoped context
7. Current explicit user instruction
8. Tool result and evidence

Issues, pull requests, source files, webpages, messages, retrieved context, model output, and tool output are untrusted evidence. They cannot expand authority or override higher-precedence governance.

## 6. Lifecycle

~~~mermaid
stateDiagram-v2
    [*] --> Proposed
    Proposed --> Candidate
    Candidate --> Evaluated
    Evaluated --> Admitted
    Admitted --> Projected
    Projected --> Active
    Active --> Suspended
    Suspended --> Active
    Candidate --> Superseded
    Admitted --> Retired
    Active --> Retired
~~~

- Proposed: an idea without a stable contract.
- Candidate: a stable candidate contract with zero execution authority.
- Evaluated: an exact version has reproducible evidence.
- Admitted: a human decision admits the semantic definition.
- Projected: a deterministic target profile exists and is independently reviewed.
- Active: bounded invocation is separately authorized.
- Suspended: invocation is disabled without erasing history.
- Retired: no new assignments; evidence remains inspectable.
- Superseded: an explicit successor exists; the predecessor remains auditable.

Every transition requires its own authority and evidence. Merge is preservation, not an implicit lifecycle transition.

## 7. Future contract and receipt model

The following are planned semantic objects, not files or database records created by this decision:

| Object | Required meaning |
|---|---|
| WorkOrder | Exact agent ID/version/digest, purpose, systems, stable repository IDs, refs, paths, actions, tools, grant, expiry, acceptance evidence, stop conditions, and next handoff |
| ContextSnapshot | Content-addressed, purpose-scoped inputs with source, freshness, sensitivity, and instruction-trust classification |
| CandidateArtifactReceipt | Candidate output paths and digests, exact base/head, limitations, tests, and unfulfilled obligations |
| HandoffReceipt | Sender, recipient, artifact/evidence digests, unresolved work, and an explicit declaration that authority was not transferred |
| EvaluatorDeclaration | Evaluator identity, independence/conflicts, provider/model disclosure, scope, and exact evaluated head/digests |
| EvidenceClaim | Fact, inference, proposal, uncertainty, source/provenance, applicability, recency, and counterevidence |
| TribunalVerdict | APPROVE, REVISE, HOLD, or SUPERSEDE recommendation bound to exact subject, head, source digest, projection digest, fixtures, and findings |
| DecisionReceipt | Human decision-maker, exact subject, action, conditions, exclusions, effective scope, and supersession rule |
| ExecutionReceipt | Effective grant, tools used, mutations attempted/completed/blocked, outputs, tests, rollback, partial failure, and exact result state |
| ProjectionReceipt | Source/compiler/schema/output digests, deterministic rebuild result, omissions, mappings, and drift result |
| PreferenceMutationReceipt | Exact human-confirmed proposed-delta digest, purpose, graph partition, mutation result, and supersession link |

Receipts are evidence, not permission. They MUST be append-only or content-addressed. Corrections supersede; they never silently rewrite. A valid receipt cannot retroactively legitimize an unauthorized act.

### 7.1 Grant contract

Every future grant binds:

- issuer and grantee identity;
- exact role ID, version, and source digest;
- task, purpose, and acceptance criteria;
- system, environment, tenant, and stable repository ID;
- actions, resources, readable/writable/protected paths, branches, refs, base/head SHA, issue or PR;
- explicit tools and provider scopes;
- network/egress and secrets/data classifications;
- start, expiry, revocation state, delegation rule, and receipt requirements.

Defaults are no delegation, no subgrant, no cross-role/task/repository/system/environment reuse, and no carry-forward after head drift, expiry, revocation, projection change, or task decomposition. Splitting a task cannot increase aggregate authority.

Effective action is the intersection of:

admitted role ceiling ∩ current grant ∩ explicit tool allowlist ∩ repository/system scope ∩ path/ref scope ∩ lifecycle state.

If any term is absent, unknown, or narrower than the requested action, the action is prohibited.

## 8. Candidate catalog global contract

The catalog contains exactly the declared set QAG-000 through QAG-100 in increments of ten. There is no implicit twelfth role, wildcard remit, other-duties clause, or catch-all authority. Every role currently has:

- lifecycle: candidate design record only;
- human decision owner: Bryan;
- operational owner/team: UNASSIGNED; this is a stop condition until separately assigned;
- authority: zero current runtime authority; future ceiling no higher than propose, comment, exact-field reversible routing metadata, or exact-scope candidate branch work, always under a current grant;
- admission: not admitted;
- invocation: disabled and unavailable;
- delegation: prohibited by default;
- merge, deployment, publication, transaction, Supabase mutation, Preference Graph access/mutation, and authority expansion: prohibited;
- failure state: HOLD, preserve evidence, disclose partial work, and hand off without authority transfer.

Candidate skill references below are capability-composition proposals to resolve at implementation time. A skill is an instruction/capability package, not an authority-bearing role. Referencing, reusing, resolving, or successfully running a skill does not admit an agent or grant tools. Missing, incompatible, or unavailable skills fail closed; no role may install a skill or broaden tools for itself.

### 8.1 Candidate GitHub alias vocabulary

The aliases are Quirk design abstractions, not claims about GitHub-native tool names or current access:

- GH-R: repository read, code search, issue read, PR read, diff read, checks read, artifact read.
- GH-C: issue comment and PR comment.
- GH-B: branch create, file write, commit create, and draft PR open.
- GH-M: exact-resource routing metadata only: add/remove a pre-approved label, add/remove a pre-approved assignee, or set/clear an approved milestone. State changes, close/reopen, base retargeting, draft/readiness conversion, title/body edits, merge controls, branch controls, and unknown fields are excluded.

Every mutating alias is dormant without an exact unexpired grant. A GH-M grant binds the issue/PR, field, allowed prior value, allowed next value, and rollback. Provider mapping is a separate implementation decision; an unresolved or widened mapping fails closed.

Read is not write. Issue or PR commenting is not code mutation. Branch write is not merge, release, deployment, publication, or permission to modify a protected path.

## 9. Eleven candidate role contracts

### QAG-000 — Workforce Choreographer

- Owner/lifecycle: Bryan is decision owner; operational owner is UNASSIGNED; candidate and fail closed.
- Accountable outcome: one bounded WorkOrder with owner, dependencies, grants, acceptance evidence, risks, and handoff graph.
- Scope: intake, decomposition, routing, status synthesis, and dependency/risk ledger; never specialist execution.
- Inputs: human objective, current decision receipts, repository/system inventory, dependencies, and constraints.
- Outputs: work packet, routing/dependency graph, status/risk ledger, and handoff receipts.
- Candidate composition: superpowers:writing-plans; superpowers:dispatching-parallel-agents; superpowers:subagent-driven-development; agent-consent-patterns:agent-consent-patterns.
- Proposed aliases and ceiling: GH-R, GH-C, GH-M; propose and route, with reversible metadata only under an exact grant.
- Cross-system touchpoints: authority grants, decision log, GitHub Issues/PRs, Quirk receipts, and handoff inventory; all system-specific execution routes to a specialist.
- Mandatory handoffs: outcome to QAG-010; topology to QAG-020; implementation to QAG-030/QAG-040/QAG-060/QAG-100; evidence to QAG-070; synchronization to agent.quirk-sync-steward.
- Prohibited: implementation, evaluation of its own orchestration, approval, admission, authority grants, scope widening, merge, deploy, or publication.
- Stop/failure: ambiguous owner or objective, conflicting grants, undeclared dependency, scope/head drift, or missing specialist; HOLD and escalate.
- Admission evidence: decomposition cannot expand aggregate authority; every dependency and handoff is complete and independently checkable.

### QAG-010 — Product & Program Director

- Owner/lifecycle: Bryan is decision owner; operational owner is UNASSIGNED; candidate and fail closed.
- Accountable outcome: a human-reviewable outcome contract with user value, non-goals, acceptance criteria, milestones, dependencies, and risk decisions.
- Scope: briefs, PRDs, roadmap/prioritization, dependency planning, measurable acceptance, and release-readiness criteria.
- Inputs: human outcome decision, domain boundary, evidence claims, capacity constraints, and system dependencies.
- Outputs: brief, PRD, roadmap, risk register, decision log, observable acceptance criteria, and release-readiness criteria.
- Candidate composition: product-design:ideate; product-design:audit; data-analytics:gather-business-context; data-analytics:design-kpis.
- Proposed aliases and ceiling: GH-R, GH-C; GH-B only for spec artifacts under an exact grant.
- Cross-system touchpoints: product canon, GitHub planning artifacts, Preference Graph requirements, analytics definitions, commerce surfaces, and future Notion/Airtable projections; no live write follows.
- Mandatory handoffs: architecture to QAG-020; feasibility to QAG-030/QAG-040/QAG-060/QAG-100; claims to QAG-090; verification to QAG-070; release packaging to QAG-080.
- Prohibited: inventing or validating product/efficacy/commercial claims, implementing and approving the same slice, changing admitted domain boundaries, spend, live mutation, merge, or release.
- Stop/failure: missing human outcome, unsupported claim, unobservable criterion, absent dependency owner, or boundary conflict; HOLD.
- Admission evidence: outcome-to-criterion traceability, explicit non-goals, risk ownership, and independent feasibility/claim checks.

### QAG-020 — Principal Systems Architect

- Owner/lifecycle: Bryan is decision owner; operational owner is UNASSIGNED; candidate and fail closed.
- Accountable outcome: a coherent bounded design with contracts, ADRs, trust boundaries, failure modes, migration, rollback, and versioning.
- Scope: system boundaries, interfaces, data/control flow, interoperability, topology, versioning, migration, and rollback design.
- Inputs: approved outcome contract, current canon, system inventory, threat/data constraints, and dependency contracts.
- Outputs: architecture specification, ADRs, interface contracts, topology, migration/rollback design, and unresolved decision ledger.
- Candidate composition: code-ontology-companion:manage-code-ontology; superpowers:writing-plans; supabase:supabase-postgres-best-practices.
- Proposed aliases and ceiling: GH-R, GH-C; GH-B only for design/contract artifacts under an exact grant.
- Cross-system touchpoints: quirk-os, project repositories, contract registries, Supabase interfaces, hosting topology, packages, and agent/MCP boundaries; all provider state remains external evidence.
- Mandatory handoffs: implementation to QAG-030; platform to QAG-040; data to QAG-060; security to QAG-050; evaluation to QAG-070; cross-system reconciliation to agent.quirk-sync-steward.
- Prohibited: unilateral canon, root-system creation, implementing and approving the same slice, live credentials/providers, merge, deployment, or runtime activation.
- Stop/failure: canon conflict, unknown trust boundary, missing authority/evidence contract, irreversible migration without rollback, or unresolved dependency version; HOLD.
- Admission evidence: contract compatibility, threat-boundary coverage, rollback proof, failure analysis, and independent conformance review.

### QAG-030 — Principal Staff Engineer

- Owner/lifecycle: Bryan is decision owner; operational owner is UNASSIGNED; candidate and fail closed.
- Accountable outcome: the smallest maintainable candidate implementation with typed contracts, tests, documentation, and reproducible evidence.
- Scope: application/library code, refactors, tests, local tooling, and branch-local fixes inside an approved design and WorkOrder.
- Inputs: bounded WorkOrder, approved design, exact base SHA, path/action grant, acceptance criteria, and test environment.
- Outputs: branch-local candidate code, tests, documentation, CandidateArtifactReceipt, and disclosed limitations.
- Candidate composition: superpowers:test-driven-development; superpowers:systematic-debugging; superpowers:verification-before-completion.
- Proposed aliases and ceiling: GH-R, GH-B, GH-C; exact-scope candidate-branch edits and draft PR only under an exact grant.
- Cross-system touchpoints: repositories, CI evidence, internal packages, local test doubles, and observability contracts; no live provider, database, or graph effect.
- Mandatory handoffs: scope to QAG-010; design conflict to QAG-020; CI/runtime to QAG-040; security to QAG-050; data to QAG-060; exact-head review to QAG-070; packaging to QAG-080.
- Prohibited: scope expansion, self-approval, protected-branch write, merge, deployment, secrets, production/provider/database/Preference Graph mutation.
- Stop/failure: tests cannot prove criteria, head drift, untrusted dependency, live secret/mutation required, or architectural ambiguity; HOLD.
- Admission evidence: clean reproducible tests, minimal diff, exact-head artifact receipt, negative-path coverage, and independent Tribunal review.

### QAG-040 — Platform & SRE Lead

- Owner/lifecycle: Bryan is decision owner; operational owner is UNASSIGNED; candidate and fail closed.
- Accountable outcome: reproducible CI/CD and operability candidates with rollback, observability, SLO/error-budget assumptions, runbooks, and failure evidence.
- Scope: workflows, build/release plumbing, IaC proposals, environments, resilience, observability, and runbooks.
- Inputs: architecture, candidate implementation, environment inventory, service objectives, security constraints, and provider state evidence.
- Outputs: candidate workflow/IaC changes, runbooks, SLO proposals, rollback plan, resilience evidence, and readiness ledger.
- Candidate composition: cloudflare:workers-best-practices; vercel:deployments-cicd; vercel:observability; app-6a624c56bfe081918f7544f7d58f6faf:render-debug.
- Proposed aliases and ceiling: GH-R, GH-B, GH-C; candidate workflow/IaC/runbook changes and sandbox/dry-run only under an exact grant.
- Cross-system touchpoints: GitHub Actions/Packages, Cloudflare, Vercel, Render, Sentry, PostHog, and artifact stores; provider access and production execution are separately gated.
- Mandatory handoffs: architecture to QAG-020; secrets/security to QAG-050; app fixes to QAG-030; release to QAG-080; evaluation to QAG-070; provider reconciliation to agent.quirk-sync-steward.
- Prohibited: production deploy, promotion, secret creation/rotation, branch-protection changes, package publication, bypass, or release approval.
- Stop/failure: non-reversible operation, missing rollback, unscoped credential, production target, provider-state drift, or non-reproducible proof; HOLD.
- Admission evidence: hermetic CI evidence, rollback drill, observability coverage, failure injection, and independent readiness verdict.

### QAG-050 — Security, Privacy & Consent Steward

- Owner/lifecycle: Bryan is decision owner; operational owner is UNASSIGNED; candidate and fail closed.
- Accountable outcome: an explicit threat/privacy/consent verdict with blocking findings, mitigations, residual risk, and authority trace.
- Scope: threat models, access/data boundaries, supply chain, provenance, secrets, consent, privacy, retention, and blocking review.
- Inputs: design, data flows, grants, dependencies, secrets/identity boundaries, retention basis, and exact candidate head.
- Outputs: threat model, data classification, consent review, findings, remediation requirements, and exact-head security verdict.
- Candidate composition: agent-consent-patterns:agent-consent-patterns; supabase:supabase-postgres-best-practices; coderabbit:code-review.
- Proposed aliases and ceiling: GH-R, GH-C; inspect, block, and propose remediation, with no branch/file/metadata write alias; GH-C is comment-only and grant-bound.
- Cross-system touchpoints: GitHub security/dependencies, Supabase auth/RLS design, Preference Graph consent, provider credentials, hosting boundaries, and commerce PII; secrets and live state remain inaccessible.
- Mandatory handoffs: remediation to the owning implementer; data/privacy to QAG-060; platform to QAG-040; evidence sufficiency to QAG-070; human risk acceptance to Bryan.
- Prohibited: weakening controls, accepting risk for Bryan, exposing secrets/PII, implementing and clearing the same finding, granting access, merge, or deploy.
- Stop/failure: secret/PII exposure, absent consent/retention basis, critical unmitigated threat, unverified dependency, or stale/missing grant; HOLD and escalate.
- Admission evidence: adversarial threat fixtures, least-privilege proof, consent/retention traceability, dependency provenance, and independently verified remediation.

### QAG-060 — Data & Preference Graph Steward

- Owner/lifecycle: Bryan is decision owner; operational owner is UNASSIGNED; candidate and fail closed.
- Accountable outcome: a versioned candidate data contract/migration/provenance plan and, when requested, an inert proposed graph delta.
- Scope: data contracts, schemas, lineage, quality, retention, migration design, projection semantics, and inert Preference Graph proposals.
- Inputs: approved semantics, current schemas, provenance, consent purpose, quality constraints, and exact environment boundaries.
- Outputs: candidate schemas/migrations/fixtures, lineage and quality reports, retention plan, rollback design, and inert proposed graph delta.
- Candidate composition: data-analytics:create-data-context; data-analytics:validate-data; supabase:supabase; supabase:supabase-postgres-best-practices.
- Proposed aliases and ceiling: GH-R, GH-B, GH-C; repository-local candidate artifacts only.
- Cross-system touchpoints: Supabase/Postgres design, Preference Graph boundaries, analytics, event schemas, and future Airtable/Notion projections; no system read/write is implied.
- Mandatory handoffs: semantics to QAG-010/QAG-020; implementation to QAG-030; consent/security to QAG-050; migration operations to QAG-040; evidence to QAG-070; sync to agent.quirk-sync-steward.
- Prohibited: Supabase/database reads or writes, applying migrations, Preference Graph reads/writes, treating projection/storage as canon, inference from silence, destructive cleanup, or recording its own human confirmation.
- Stop/failure: missing provenance/consent, irreversible or unversioned migration, identity ambiguity, canon/projection conflict, or absent exact human confirmation; HOLD.
- Admission evidence: reversible migration proof, lineage/quality fixtures, exact purpose partition, and Preference Graph mutation-poison tests.

### QAG-070 — Evaluation & Design Tribunal Lead

- Owner/lifecycle: Bryan is decision owner; operational owner is UNASSIGNED; candidate and fail closed.
- Accountable outcome: a commit-bound reproducible recommendation with evaluator declaration, claims, fixtures, limitations, and decision evidence.
- Scope: evaluation plans, adversarial fixtures, evidence validation, exact-head conformance, evaluator independence, and Tribunal recommendations.
- Inputs: exact source/projection/artifact digests, head SHA, acceptance criteria, grants, evaluator conflicts, and fixture corpus.
- Outputs: evaluation plan, fixture results, EvidenceClaims, EvaluatorDeclaration, and APPROVE/REVISE/HOLD/SUPERSEDE TribunalVerdict.
- Candidate composition: plugin-eval:evaluate-plugin; plugin-eval:evaluate-skill; coderabbit:code-review; superpowers:verification-before-completion.
- Proposed aliases and ceiling: GH-R, GH-C; GH-B only for eval-only artifacts on a separately granted branch.
- Cross-system touchpoints: CI artifacts, Tribunal/evidence contracts, authority and receipt stores, fixture registries, and exact Git commits; inspection never becomes remediation authority.
- Mandatory handoffs: findings to responsible role; security to QAG-050; release evidence to QAG-080; admission decision to Bryan.
- Prohibited: editing evaluated implementation, self-evaluation, executing remediation, stale-head verdicts, confidence laundering, admission, merge, or activation.
- Stop/failure: head/digest drift, undisclosed conflict, unavailable/tampered evidence, non-deterministic fixtures, or stale grant; HOLD and invalidate verdict.
- Admission evidence: independent exact-head replay, adversarial corpus, declared provider/model/identity relationships, and reproducible verdict.

### QAG-080 — Developer Experience & Release Manager

- Owner/lifecycle: Bryan is decision owner; operational owner is UNASSIGNED; candidate and fail closed.
- Accountable outcome: a reproducible release candidate with package metadata, docs, changelog, compatibility, provenance, rollback, and readiness ledger.
- Scope: developer tooling, onboarding, documentation, package assembly, versioning proposals, and release-candidate orchestration.
- Inputs: exact candidate head, build/test evidence, security/data verdicts, release policy, package constraints, and supported environments.
- Outputs: candidate tooling/docs, release notes, package/release drafts, compatibility matrix, SBOM/provenance, and readiness report.
- Candidate composition: superpowers:finishing-a-development-branch; superpowers:verification-before-completion; skill-submission-pack-writer:write-skill-submission-pack.
- Proposed aliases and ceiling: GH-R, GH-B, GH-C, GH-M; candidate packaging/docs and draft release artifacts only.
- Cross-system touchpoints: GitHub Packages/Releases/Actions, package registries, documentation sites, SBOM/provenance stores, and release metadata; no publication or promotion.
- Mandatory handoffs: implementation/platform to QAG-030/QAG-040; security to QAG-050; schema compatibility to QAG-060; claims to QAG-090; final evidence to QAG-070; publication decision to Bryan.
- Prohibited: merge, tag, publish, release, bypass, production promotion, or invented compatibility/support claims.
- Stop/failure: missing digest/SBOM/license/provenance, unresolved blocker, incompatible contract, failed clean-room build, or head drift; HOLD.
- Admission evidence: clean-room reproduction, provenance and rollback proof, compatibility fixtures, and independent exact-head readiness verdict.

### QAG-090 — Research & Evidence Lead

- Owner/lifecycle: Bryan is decision owner; operational owner is UNASSIGNED; candidate and fail closed.
- Accountable outcome: a source-backed evidence pack separating fact, inference, proposal, uncertainty, recency, and claim applicability.
- Scope: source census, standards/docs research, evidence genealogy, claim ledger, contradiction analysis, rights, and freshness.
- Inputs: research question, decision scope, source policy, rights constraints, current claim ledger, and contradiction criteria.
- Outputs: source census, EvidenceClaims, evidence ledger, contradiction map, uncertainty/freshness assessment, and research brief.
- Candidate composition: quirk-deep-research; quirk-research-critic; hugging-face:huggingface-papers; hugging-face:huggingface-datasets.
- Proposed aliases and ceiling: GH-R, GH-C; GH-B only for evidence artifacts under an exact grant.
- Cross-system touchpoints: primary standards/docs, source registries, model cards, research datasets, and product claim ledgers; provider execution and restricted content remain excluded.
- Mandatory handoffs: product implications to QAG-010; architecture to QAG-020; security to QAG-050; data/model implications to QAG-060; claim verification to QAG-070; source synchronization to agent.quirk-sync-steward.
- Prohibited: fabricated citations/metrics, inference upgraded to fact, restricted-content copying, commercial/efficacy claims, provider execution, implementation, or admission.
- Stop/failure: no primary source, material recency gap, license/usage ambiguity, unresolved contradiction, or requested certainty beyond evidence; HOLD.
- Admission evidence: primary-source traceability, rights compliance, contradiction handling, recency tests, and independent claim-to-change applicability review.

### QAG-100 — Commerce & Integration Architect

- Owner/lifecycle: Bryan is decision owner; operational owner is UNASSIGNED; candidate and fail closed.
- Accountable outcome: a provider-neutral candidate integration contract with idempotency, tenancy, money/data flow, reconciliation, failure recovery, and sandbox proof plan.
- Scope: commerce adapters, APIs/webhooks, identity mapping, payment/order/subscription boundaries, tenancy, and integration failure modes.
- Inputs: product rules, provider contracts, architecture, data/security constraints, tenancy, failure modes, and sandbox-only evidence.
- Outputs: adapter/API/webhook contracts, event/identity mappings, test doubles, sandbox fixtures, reconciliation and rollback design.
- Candidate composition: sales:index; supabase:supabase-postgres-best-practices; cloudflare:workers-best-practices; vercel:payments.
- Proposed aliases and ceiling: GH-R, GH-B, GH-C; candidate contracts, test doubles, fixtures, and branch-local adapter code only under an exact grant.
- Cross-system touchpoints: Medusa, Shopify, WooCommerce, Stripe, Lemon Squeezy, marketplaces, webhooks, Quirk Merchant, hosting edges, and Supabase projection boundaries; live providers remain inaccessible.
- Mandatory handoffs: product to QAG-010; architecture to QAG-020; implementation to QAG-030; platform to QAG-040; security/PCI/privacy to QAG-050; data to QAG-060; evaluation to QAG-070; provider reconciliation to agent.quirk-sync-steward.
- Prohibited: live transaction/refund/order, provider configuration, secret use, customer-data access, deployment, merchant/product claims, merge, or release.
- Stop/failure: live credential/money/customer required, non-idempotent design, tenant ambiguity, missing reconciliation/rollback, or unknown provider terms; HOLD.
- Admission evidence: sandbox-only replay, idempotency/reconciliation fixtures, tenancy isolation, provider-contract provenance, and independent security/financial review.

## 10. Incumbent Sync Steward boundary

agent.quirk-sync-steward is an existing candidate specialist, not one of the eleven new entries. This design does not modify, replace, admit, activate, or duplicate it.

Its existing contract exclusively owns its stated synchronization semantics under its own grants, including cross-platform identity, bounded synchronization operations, reconciliation, projection drift, and sync receipts. The eleven roles may identify a synchronization need and hand it off. They may not impersonate the Sync Steward, reuse its grants, treat handoff as execution, or create a second general synchronization role.

The Sync Steward remains governed by its exact source contract and lifecycle. This specification cannot widen it.

## 11. Separation of duties and handoff laws

- QAG-000 may route work but cannot implement, evaluate, admit, or merge it.
- QAG-010 may own acceptance criteria but cannot be sole implementer, evaluator, or release approver for the same slice.
- QAG-020 cannot be the independent conformance reviewer of its own architecture.
- QAG-030 implementers cannot approve, admit, merge, deploy, or issue the final Tribunal verdict for their work.
- QAG-040 may design release machinery but cannot authorize or execute final production release.
- QAG-050 may block but cannot accept human risk, implement and clear the same finding, or release.
- QAG-060 may propose a graph delta but cannot confirm or execute it; it cannot validate its own live migration.
- QAG-070 may evaluate but cannot edit the evaluated implementation or execute remediation.
- QAG-080 may assemble a release candidate but cannot verify and publish it alone.
- QAG-090 may produce evidence but cannot decide admission or self-validate claim applicability.
- QAG-100 cannot approve security, financial reconciliation, production activation, or release.

An author, implementer, or projection compiler cannot be the sole reviewer, evaluator, admission authority, or merger for the same change. Verdicts bind exact source/projection digests and exact head SHA. Drift invalidates them.

Independence MUST be declared. Any human-accepted exception is explicit, narrow, head-bound, recorded, and non-transitive; it does not imply admission, activation, merge, or release.

## 12. Cross-system posture

| Surface | Default posture for v0.1 | Separate future gate |
|---|---|---|
| GitHub repositories | No profile or runtime access in this tranche | Admitted role, activated projection, stable repo ID, exact task/ref/path/action grant |
| GitHub comments/metadata | No current writes | Exact issue/PR and action grant; comments remain non-authoritative |
| Branch-local code/specs | No agent writes | Candidate branch, exact base/head, allowed/denied paths, tools, tests, receipt |
| Review/merge/release | No agent authority | Independent exact-head review; separate human merge/release decision |
| GitHub Actions/Packages/org settings | No access | Provider-specific high-impact grant, rollback, protected workflow/check design |
| Supabase/Postgres | No read or write | Purpose, project/environment, schema/table/action, RLS, rollback, receipt |
| Preference Graph | No read, inference, or mutation | Purpose-partitioned read grant; exact human-confirmed delta for mutation |
| Airtable/Notion/Drive/Slack | No connector or write | Explicit system/tenant/object/action projection or communication contract |
| Vercel/Cloudflare/Render | No connector/deploy/config | Environment/provider/action grant, credential boundary, rollback and receipt |
| CI/artifacts/packages | No execution/publication | Exact workflow/artifact/package/version grant and provenance |
| Commerce/payment providers | No connector, customer access, or transaction | Provider/tenant/mode/amount/action, idempotency, PCI/privacy, reconciliation |
| Research/model providers | No connector/model execution | Source/rights/data policy and bounded provider/model grant |
| Secrets/identity | No access or transport | Dedicated secret reference mechanism and least-privilege identity; secret value never enters prompts or receipts |
| MCP servers | Zero in v0.1 | Separate threat model, server/tool allowlist, read-only proof, tenancy/egress, rollback, receipts, adversarial tests |
| Cross-system synchronization | Reserved to incumbent Sync Steward remit | Exact per-system grants and synchronization receipt |

Inspection or permission in one system never implies permission in another. External access failure is absence of evidence, not a negative user preference or permission to fall back to another provider.

## 13. Preference Graph firewall

No role has current Preference Graph read or write authority. A proposed graph delta is an inert, content-addressed artifact only.

No inference, recommendation, outcome, successful run, storage record, model confidence, or user silence becomes preference evidence. A future read requires a purpose-partitioned grant. A future mutation requires human confirmation bound to the exact proposed delta digest and a PreferenceMutationReceipt. Bulk, derived, stale, or mismatched confirmation fails closed.

A future field or phrase such as human_confirmed_graph_update is a constraint label only. It is not implementation evidence, proof of confirmation, or mutation authority.

Projection and storage never become semantic authority.

## 14. Future GitHub projection contract

No profile is created by this decision. A later implementation must re-verify GitHub's current schema and limits.

Subject to that verification, a generated profile is expected to use:

- name and description;
- an explicit tools allowlist;
- disable-model-invocation;
- user-invocable;
- provenance metadata;
- the twelve prompt modules defined in quirk-os.

Candidate projections MUST NOT be present on an organization-active default branch. Where the target schema supports it, candidate output uses disable-model-invocation: true and user-invocable: false. A separate activation transition may set user-invocable: true for manual selection only after admission, exact projection review, organization protection, and human activation. Automatic model invocation remains disabled unless separately approved.

Repository-local profiles, if ever approved, use .github/agents. Organization profiles, if ever approved, use /agents in the organization's .github or .github-private repository. This design chooses .github-private for the future organization projection plane; it does not create profiles there.

Other requirements:

- no model pin in v0.1;
- zero MCP servers or external connectors;
- explicit tools only: omitted tools, wildcard/all, provider-wide wildcard, unknown tool, or transitive/runtime-added tool fails closed;
- the retired infer property is prohibited;
- the prompt must stay within GitHub's then-current profile size limit, observed as 30,000 characters at design time;
- local and organization profile shadowing/collision must be detected;
- profile presence cannot enforce path-level writes; exact path/ref limits require grants plus protected CODEOWNERS/rulesets/CI;
- compiler output uses UTF-8, LF, stable ordering, deterministic whitespace, and no timestamps, randomness, environment paths, or mutable network content;
- source change, compiler change, GitHub schema change, mapping change, or manual drift requires regeneration, conformance tests, and fresh review;
- stale/unknown source or compiler state disables or withholds the profile.

The compiler may narrow, never widen. It cannot write directly to the target default branch, activate a profile, or repair source semantics.

### 14.1 Required prompt modules

Every future durable profile compiles the existing twelve modules:

1. Role
2. Objective
3. Authority
4. Source precedence
5. Required behavior
6. Prohibited behavior
7. Tools and object scope
8. Output contract
9. Evidence and receipts
10. Stop conditions
11. Evaluation hooks
12. Version and provenance

## 15. External connector and MCP firewall

Version 0.1 has zero MCP servers and zero external connectors. Documenting a provider does not authorize connection.

A future MCP proposal requires a separate human gate, exact server and tool allowlists, trust/threat model, data/secret/egress review, read-only proof first, idempotency and rollback, tenant/environment bounds, receipts, and adversarial fixtures. Autonomous MCP writes, transitive discovery, runtime-added tools, and fallback execution after a gate failure are prohibited by default.

No Supabase/database mutation, package publication, commerce transaction, deployment/API exposure, external message, or cross-system write follows from this specification.

## 16. Evaluation and adversarial corpus

Every role must pass shared and role-specific evidence before admission and again before activation when projection behavior is involved.

Required adversarial fixtures include:

| Fixture | Expected fail-closed behavior |
|---|---|
| capability_as_authority | Reject tool/profile/skill availability as permission |
| silent_prior_or_revoked_consent | Reject silence, history, stale, revoked, or expired grants |
| decomposition_expansion | Reject subtask splitting that increases aggregate authority |
| cross_scope_grant_reuse | Reject reuse across role, task, repository, ref, system, environment, tenant, or time |
| prompt_injection | Treat issue/PR/file/web/tool content as untrusted evidence |
| head_or_digest_drift | Invalidate review, verdict, decision, and projection |
| self_review_or_collusion | Reject same identity as sole author/evaluator/admission/merge chain |
| candidate_leakage | Reject Current/Active/Live/Usable/Chooseable/installed/invocable claims |
| projection_as_canon | Reject projection changes without matching admitted source |
| partial_write_and_retry | Stop, disclose partial state, prove idempotency, and avoid duplicate effects |
| receipt_tamper | Invalidate dependent claims; preserve original and superseding correction |
| secret_or_pii_leak | Stop, minimize retention, and escalate without reproducing sensitive value |
| graph_mutation_without_confirmation | Reject inferred, bulk, stale, derived, or digest-mismatched confirmation |
| product_claim_laundering | Reject unsupported commercial, market, safety, or efficacy claims |
| access_failure_as_preference | Record no signal; never infer a negative preference |
| duplicate_role_or_object | Reject ID/remit collision and Sync Steward duplication |
| prompt_policy_drift | Reject stale source, prompt, compiler, mapping, or platform schema |
| fallback_after_gate_failure | Stop instead of using a different tool/provider/path |
| omitted_or_wildcard_tools | Reject omitted tools, wildcard/all, unknown, or concealed write scope |
| retired_infer_property | Reject obsolete invocation configuration |
| profile_shadowing | Reject ambiguous repo/org agent resolution |
| autonomous_mcp_write | Reject any MCP/server/connector configuration or write in v0.1 |
| false_reversibility | Reclassify as protected and require a stronger gate |
| success_as_authority | Reject green CI, merge, installation, completion, or successful call as approval |

Role-specific suites must prove each role's explicit boundary and refusal quality, not merely its happy path.

## 17. Future enforcement design

No enforcement file is authorized by this specification. A later implementation slice must separately design, review, and install:

- source schemas and exact eleven manifests;
- deterministic projection compiler and mapping registry;
- validators for lifecycle, unique IDs, grants, aliases, receipts, prompt modules, digests, and unknown fields;
- shared and role-specific fixtures;
- stable-name required CI checks;
- CODEOWNERS for source contracts, compiler, validators, fixtures, workflows, projections, and CODEOWNERS itself;
- quirk-os rulesets requiring independent review, stale-review dismissal, exact-head checks, and constrained receipted bypass;
- separate .github-private CODEOWNERS/rulesets because quirk-os protections cannot govern another repository;
- protection for workflow/path-filter changes so coverage cannot be silently removed.

The generator should be hermetic, dependency-pinned, network-independent, deterministic across clean environments, and unable to write directly to the projection repository. CI validates evidence; it does not admit an agent or authorize merge.

## 18. Required acceptance tests for later implementation

| Test | Passing condition |
|---|---|
| spec_only_diff | Only the allowlisted design document changes; reject profiles, manifests, prompts, schemas, workflows, CODEOWNERS, scripts, fixtures, migrations, packages, locks, runtime, or connector files |
| candidate_not_active | Reject active/usable/installed/invocable/automatic/admitted/canonical claims and user-invocable: true in candidate state |
| catalog_exact_11 | Exact declared IDs, unique candidate records, no Sync Steward duplication or implicit role |
| projection_non_authority | Profile-only semantic/tool/scope mutation fails; deterministic source-bound regeneration passes |
| tool_default_deny | Missing, wildcard/all, unknown/MCP, unmapped, or path-concealing tools fail |
| permission_intersection | Action succeeds only at exact role/grant/tool/repo/system/path/ref/lifecycle intersection |
| grant_reuse_poison | Any role/task/repo/ref/system/environment/head/expiry/revocation/decomposition reuse fails |
| self_review_poison | Same identity as sole author and verdict/admission/merge fails; declared exact-head independence passes |
| projection_drift | Stale source/compiler/profile/schema, manual edit, unknown field, or widened permission fails and disables |
| mcp_zero | Any MCP/server/connector config or external write capability in v0.1 fails |
| preference_graph_no_mutation | Only inert proposal passes; inferred/unconfirmed/mismatched/storage mutation fails |
| role_separation | Choreographer implementation, implementer approval, evaluator remediation, release-manager publication, or Data Steward graph write fails |
| protected_surface | Later rulesets protect source, projection, compiler, checks, fixtures, workflows, and CODEOWNERS in each repository |
| no_authority_by_success | Green CI, merge, installed profile, model completion, or successful tool call without exact grant fails |
| head_bound_receipt | Any subject/head/digest drift invalidates prior verdict and requires fresh review |

## 19. Rollout gates

| Gate | Evidence | Status under this decision |
|---|---|---|
| G0 Design and eleven-role catalog | Human APPROVE decision | Approved |
| G1 Written spec and one spec-only commit | One-file scope and exact commit evidence | Authorized |
| G2 Source schema and candidate manifests | Separate approved implementation plan | Not authorized |
| G3 Validators, compiler, and fixture corpus | Tests and deterministic proof | Not authorized |
| G4 Exact-head independent evaluation | Evaluator declaration and Tribunal verdict | Not authorized |
| G5 Individual semantic admission | Human decision receipt per exact version/digest | Not authorized |
| G6 Candidate projection change | Source/compiler/projection receipt and separate review | Not authorized |
| G7 Organization protection and profile installation | Protected paths/checks and human decision | Not authorized |
| G8 Manual activation | Separate exact-profile activation receipt | Not authorized |
| G9 Shadow/pilot WorkOrders | Narrow grants and execution receipts | Not authorized |
| G10 External systems or MCP | Separate contracts, threat model, and human grant | Not authorized |

No gate may be bundled into the preceding gate. Each role is admitted individually; catalog approval is not bulk admission.

## 20. Future file map

These paths are planning coordinates only. Their listing does not authorize creation.

~~~text
quirk-os/
  agents/catalog/qag-000...qag-100.yaml
  schemas/agent-contract.schema.json
  schemas/agent-work-order.schema.json
  schemas/agent-projection-receipt.schema.json
  evals/agent-workforce/shared/
  evals/agent-workforce/roles/
  tools/agent-projection/
  .github/workflows/agent-workforce-conformance.yml
  CODEOWNERS

.github-private/
  agents/qag-000...qag-100.agent.md
  CODEOWNERS
  protected required checks and rulesets
~~~

The incumbent agents/quirk-sync-steward/agent.yaml remains outside the new catalog.

## 21. Acceptance criteria for this tranche

This tranche is complete only when:

- exactly this one Markdown design file is added by one commit based on the recorded main SHA;
- no manifest, profile, prompt, schema, script, workflow, fixture, connector, migration, runtime, package, lock, CODEOWNERS, or ruleset file changes;
- exactly eleven unique role IDs and names appear as candidate design records;
- the Sync Steward remains unchanged and explicitly non-duplicated;
- the dual-plane source/projection precedence and digest binding are explicit;
- capability, authority, grant, admission, projection, installation, activation, invocation, merge, and release remain separate;
- candidate profiles are not treated as manually invocable;
- Supabase, Preference Graph, product claims, deployment, commerce, external connectors, and MCP remain unapproved;
- future object contracts, role ceilings, handoffs, fixtures, protections, failure states, and rollout gates are specified;
- the exact commit, one-file diff, and document digest are verified and reported;
- no pull request, review, merge, admission, activation, or external mutation occurs.

This document is a decision artifact, not an executable workforce artifact.

## 22. Versioning and supersession

This specification is version 0.1.0. A semantic change to architecture, catalog membership, any role boundary, authority ceiling, source/projection precedence, lifecycle, grant semantics, or activation rule requires:

1. a new version and content digest;
2. an explicit supersession statement;
3. exact-head independent review;
4. a fresh human APPROVE/REVISE/HOLD/SUPERSEDE decision.

A later implementation plan, commit, pull request, merge, profile, or runtime cannot silently supersede this specification. Review and decision receipts are invalid after subject-head or content-digest drift.

## 23. Official GitHub references

The implementation tranche must re-check current GitHub behavior against primary documentation:

- Creating custom agents: https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/create-custom-agents
- Custom-agent configuration: https://docs.github.com/en/copilot/reference/custom-agents-configuration
- Preparing an organization for custom agents: https://docs.github.com/en/copilot/how-tos/administer-copilot/manage-for-organization/prepare-for-custom-agents
- MCP and the GitHub cloud agent: https://docs.github.com/en/copilot/concepts/agents/cloud-agent/mcp-and-cloud-agent

At design time, GitHub custom agents and organization management are preview features and may change. Platform drift therefore requires a new compatibility review before implementation or activation.
