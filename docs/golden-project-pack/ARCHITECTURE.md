# Quirk Core Architecture

## 1. Architectural thesis

Quirk Core separates four concerns that systems routinely collapse:

1. **What is defined** — canonical objects, laws, contracts, and versions.
2. **What is allowed to matter** — authority, purpose, policy, and consent.
3. **What happened** — operations, telemetry, logs, and transitions.
4. **What was learned** — evaluations, outcomes, poison, promotion, and revision.

A record can be historically valid while being operationally inactive. A source can be authentic while its claim is wrong. A comment can be useful while carrying zero authority. A model can be confident while lacking permission.

## 2. Planes

### Canonical plane

Git-backed, reviewable, versioned:

- canonical definitions;
- object grammar;
- schemas;
- policies and contracts;
- capability and skill manifests;
- eval definitions;
- Golden Prompts;
- ADRs and migrations.

### Runtime plane

Code and services that:

- classify mutation risk;
- resolve authority;
- enforce policy and purpose;
- invoke capabilities and tools;
- apply domain mutations;
- verify outcomes;
- emit receipts;
- fail closed on stale, missing, expired, or poisoned inputs.

### Projection plane

Queryable representations:

- relational read models;
- graph projections;
- search and vector indexes;
- Quirk Control views;
- dashboards and digests;
- materialized current-state views.

Projections are disposable and rebuildable. They do not outrank canon or receipts.

### Work plane

Google Drive and other collaborative surfaces:

- drafts;
- comments;
- research;
- design;
- review;
- multimedia production;
- human handoff.

Work-plane state is never silently promoted.

## 3. Core object grammar

### `QuirkTransition`

A consequential proposed or accepted state change.

Required concepts:

- subject object and expected version;
- operation;
- before/after state or patch;
- actor and proposer;
- provenance;
- purpose;
- authority requirement;
- evidence references;
- risk class;
- reversibility;
- status;
- timestamps and schema version.

### `QuirkReceipt`

Portable proof that a transition was authorized, applied, and verified.

A receipt reports evidence. It does not replace domain state.

### `QuirkLogRecord`

Operational or diagnostic record correlated to traces, transitions, receipts, tools, models, builds, and users where permitted.

### `QuirkEval`

A versioned test object containing task, environment, graders, expected evidence, sampling policy, thresholds, and anti-cheat controls.

### `QuirkGate`

A policy-controlled decision that consumes evidence and returns `pass`, `fail`, `waived`, or `not_applicable`.

A waiver is itself consequential and owes a receipt.

### `QuirkCapability`

A versioned promise:

```yaml
capability:
  id: capability.repo_ready_project_pack
  version: 1.0.0
  promise: Produce a coherent implementation-ready project pack.
  inputs: [...]
  outputs: [...]
  preconditions: [...]
  permissions: [...]
  evals: [...]
  failure_modes: [...]
  implements: [...]
```

### `QuirkAgentSkill`

An executable procedure with bounded tools, inputs, outputs, stop conditions, evals, permission requirements, and evidence emission.

### `QuirkProposedMove`

A bounded candidate mutation. It contains enough evidence and impact analysis to approve, revise, reject, defer, or test without reconstructing an entire conversation.

### `QuirkResearchClaim`

A source-bounded claim with temporal scope, confidence, contradictions, adoption decision, and affected objects.

### `QuirkMediaDerivative`

A medium-native transformation tied to canonical source, claims, rights, accessibility, provenance, and release evidence.

## 4. Lifecycle grammar

```text
draft
→ proposed
→ evaluating
→ approved | rejected | deferred
→ applying
→ applied
→ verified
→ operative
→ challenged | superseded | revoked | expired | poisoned | forgotten
```

Maintain separate fields:

```yaml
historical_status: retained
operative_status: superseded
```

This is the No Zombie Truth control.

## 5. Proposed Move Queue

### Queue lanes

- `canon`
- `policy`
- `schema`
- `capability`
- `skill`
- `prompt`
- `eval`
- `gate`
- `research-adoption`
- `media-release`
- `migration`
- `forgetting`
- `poison`

### Queue item contract

A move includes:

- desired change;
- reason and expected outcome;
- source/provenance;
- affected objects and versions;
- evidence and contradictions;
- authority required;
- risk and reversibility;
- implementation patch or plan;
- pre-evals and regression suite;
- communication plan;
- outcome-eval date;
- disposition and receipt.

### Ordering

Use explicit priority dimensions, not one magical score:

- rights/safety urgency;
- dependency unblock;
- value;
- evidence strength;
- reversibility;
- effort;
- freshness decay;
- strategic fit;
- Strange Intact risk.

## 6. Ledger vs logs vs telemetry

| Record | Question |
|---|---|
| **Telemetry** | What did the software do and how did it perform? |
| **Log** | What operational fact or diagnostic observation was recorded? |
| **Ledger** | What consequential state became authoritative, by what right, and why? |
| **Eval** | Did behavior meet a defined standard? |
| **Outcome** | Did the decision create the intended effect? |

Correlate them:

```text
trace_id
↔ log_record_id
↔ transition_id
↔ receipt_id
↔ eval_run_id
↔ outcome_record_id
```

Do not store private chain-of-thought. Store decisions, tool actions, observable evidence, concise rationales, and policy outcomes.

## 7. Authority model

Authority is scoped by:

- actor;
- object type;
- operation;
- purpose;
- environment;
- risk class;
- time window;
- delegation chain;
- required co-approval.

Modes:

- `human_explicit`
- `policy_delegated`
- `mutual`
- `system_deterministic`
- `emergency`
- `waiver`

Agents may propose. They may only approve where policy explicitly grants that operation and risk class.

## 8. Evidence model

Use references, not giant duplicated payloads.

Evidence strengths:

- `direct`
- `reproduced`
- `corroborated`
- `derived`
- `expert_judgment`
- `model_inference`
- `anecdotal`
- `unknown`

Contradictions remain attached. Confidence does not erase dissent.

## 9. Evaluation model

Three moments:

1. **Pre-eval:** should this move happen?
2. **Post-eval:** did it happen correctly?
3. **Outcome-eval:** was it worth doing?

Evaluator types:

- deterministic assertions;
- schema and contract tests;
- reference solutions;
- simulation;
- adversarial cases;
- model graders with structured rubrics;
- calibrated human review;
- production outcome comparison.

Prefer outcome grading over rigid path matching unless the path itself is the safety property.

## 10. Gate behavior

A gate is executable policy, not documentation theater.

```yaml
gate_result:
  gate_id: gate.no_silent_mutation
  version: 1.0.0
  result: fail
  evidence_refs: [...]
  evaluated_at: ...
  evaluator: ...
  waiver_allowed: false
```

Required integrity gates:

- no silent mutation;
- no zombie truth;
- no machine self-promotion;
- receipt reconstructability;
- stale proposal rejection;
- idempotent commit;
- projection convergence;
- poison recurrence;
- forgetting completeness;
- forgetting non-resurrection;
- Ship It Without Bryan.

## 11. Failure grammar

- `LEDGER_SCHEMA_INVALID`
- `LEDGER_AUTHORITY_MISSING`
- `LEDGER_AUTHORITY_EXPIRED`
- `LEDGER_EVIDENCE_INSUFFICIENT`
- `LEDGER_POLICY_DENIED`
- `LEDGER_STALE_PROPOSAL`
- `LEDGER_IDEMPOTENCY_CONFLICT`
- `LEDGER_RECEIPT_INVALID`
- `LEDGER_PROJECTION_DRIFT`
- `LEDGER_ZOMBIE_STATE`
- `LEDGER_POISONED_SOURCE`
- `LEDGER_FORGETTING_INCOMPLETE`
- `LEDGER_HUMAN_APPROVAL_REQUIRED`
- `GATE_WAIVER_UNAUTHORIZED`
- `RESEARCH_SOURCE_STALE`
- `MEDIA_SOURCE_RECEIPT_MISSING`
- `MEDIA_NO_NATIVE_AFFORDANCE`

## 12. Security and privacy boundaries

- least privilege by capability and tool;
- untrusted-content partitioning;
- outbound network controls;
- approval for higher-risk writes;
- secret and credential exclusion;
- PII minimization;
- purpose-bound retention;
- tamper evidence;
- replay and idempotency protection;
- stale-write rejection;
- safe forgetting across indexes, caches, vectors, exports, and receipts;
- deterministic sandboxes outside agent discretion;
- read-only evaluators and policy controls when testing self-improvement.

## 13. Product-design surfaces

Quirk Control should answer human questions:

- Why is this true?
- What changed?
- Who or what authorized it?
- What evidence supports it?
- What does it affect?
- Has it been challenged?
- What replaced it?
- Can I reverse, revoke, forget, or poison it?
- What proposed moves need me?
- Which decisions still owe an outcome?

Reusable primitives:

```text
<Receipt />
<TransitionDiff />
<AuthorityBadge />
<EvidenceStack />
<ChallengeButton />
<HistoryTimeline />
<WhyThisIsTrue />
<WhatThisAffects />
<UndoMutation />
<ForgetThis />
<PoisonWarning />
<PendingApproval />
<OutcomeDebt />
```

## 14. Promotion ladder

```text
Observation
→ Proposed Move
→ Tested Move
→ Repeated Pattern
→ Quirk Way
→ Capability
→ Canonball candidate
→ Canon
```

Ledger evidence supports promotion. Popularity alone does not.
