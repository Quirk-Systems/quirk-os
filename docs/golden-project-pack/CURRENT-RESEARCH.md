# Current Research Operating Model

**As of:** 2026-08-11  
**Purpose:** Turn external research into inspectable Quirk decisions without confusing citation, truth, authority, or implementation.

## 1. Research objects

### `ResearchSource`

Records publication, authorship, date, source type, primary/secondary status, access date, conflicts, stable URL, and preservation state.

### `ResearchClaim`

A bounded proposition that can be evaluated independently.

### `ResearchDistillation`

Explains what a cluster of sources collectively supports, disputes, or leaves open.

### `ResearchAdoptionDecision`

One of:

- `adopt`
- `adapt`
- `reject`
- `monitor`
- `experiment`
- `boneyard`

### `FreshnessCheck`

Re-runs time-sensitive claims and records whether they remain valid, changed, disappeared, or became contested.

## 2. Research pipeline

```text
question
→ source census
→ primary-source priority
→ oldest relevant strata
→ current state
→ claim extraction
→ contradiction map
→ applicability analysis
→ adopt/adapt/reject
→ bounded experiment
→ evidence + receipt
→ freshness review
```

Research does not directly mutate canon. It produces Proposed Moves.

## 3. Source quality

Prefer:

1. normative standards and official specifications;
2. peer-reviewed research and primary technical reports;
3. official engineering write-ups with reproducible detail;
4. direct practitioner essays with disclosed context;
5. strong secondary synthesis;
6. community reports and anecdotes as leads, not proof.

Record missing evidence instead of laundering confidence through prose.

## 4. 2026 standards adoption matrix

| Source | Quirk decision | Use |
|---|---|---|
| **W3C PROV-O** | **ADAPT** | Map `Entity`, `Activity`, `Agent`, derivation, attribution, bundles, and primary sources into Quirk provenance. Do not require RDF/OWL for every runtime object. |
| **CloudEvents 1.0.2** | **ADAPT** | Use the common event envelope for transport metadata; keep Quirk transition and receipt semantics in typed payloads. |
| **OpenTelemetry semantic conventions 1.43.0** | **ADOPT discipline / ADAPT namespace** | Standardize trace, log, metric, event, resource, GenAI, tool, build, and transition correlation. Avoid duplicate low-value attributes. |
| **NIST AI RMF** | **ADAPT selectively** | Use Govern/Map/Measure/Manage as a cross-check; implement Quirk-native `Authority / Context / Proof / Disposition`. Do not cargo-cult the entire playbook. |
| **MCP 2026-07-28** | **ADOPT interoperability principles** | Capability negotiation, explicit protocol versions, stateless core, extensions, lifecycle/deprecation discipline, and conformance testing. |
| **C2PA 2.4** | **ADOPT where media supports it** | Content Credentials, edit provenance, signed claims, repository receipts, and compatibility rules for public media assets. |
| **SLSA + Sigstore/Rekor** | **ADAPT** | Supply-chain provenance, attestations, artifact verification, and tamper-evident transparency patterns for releases and receipts. |
| **OpenAI Presence patterns** | **ADAPT** | Specific jobs, policies, guardrails, escalation, simulations, production signals, proposed updates, controlled rollout. |
| **Anthropic agent-eval guidance** | **ADOPT core practice** | Eval-driven development, balanced tasks, deterministic graders where possible, calibrated model graders, reference solutions, transcript review, pass@k and pass^k. |

## 5. Current research signals

### Harnesses are first-class systems

Lilian Weng's July 2026 synthesis treats the harness around a model—workflow, tools, persistent files, permissions, subagents, context management, and evaluation—as an optimization target. Quirk should therefore version and evaluate harness components separately rather than hiding them inside one prompt.

**Quirk adoption:** explicit editable surfaces, file-backed state, bounded self-improvement proposals, held-out regression tests, and policy/evaluator components outside the self-editing surface.

### Production agents need controlled change

Current production-agent practice emphasizes defined jobs, policies, guardrails, escalation, simulations, production signals, proposed updates, and controlled rollout.

**Quirk adoption:** Proposed Move Queue as the change-control backbone, with outcome debt and progressive releases.

### Agent evals must measure reliability, not one lucky run

Agent behavior is non-deterministic. Use `pass@k` where one success is sufficient and `pass^k` where consistency matters. Balance positive and negative cases. Keep reference solutions. Calibrate model graders against humans and inspect trajectories.

**Quirk adoption:** each capability declares its reliability metric, trial count, grader mix, and acceptable variance.

### Context-rich telemetry matters for agentic validation

Agentic systems need preserved relationships across user intent, build, model, tool, feature flags, traces, transitions, and outcomes. Splitting context into disconnected signal silos weakens debugging and automated validation.

**Quirk adoption:** wide structured events with disciplined semantic conventions and correlation IDs; do not put everything in one ledger.

### Local-first principles strengthen human authority

Local-first work continues to emphasize data ownership, resilience, collaboration, provider portability, and access control without assuming one permanent cloud authority.

**Quirk adoption:** Git-exportable canon, portable receipts, reconstructable projections, provider abstraction, offline-readable packs, and no Drive-only critical truth.

### Media provenance is becoming operational infrastructure

C2PA 2.4 expands format support and adds repository receipts and a JSON-LD derived view while retaining signed, tamper-evident manifests as the source of verification.

**Quirk adoption:** C2PA for public assets where supported; Quirk receipt linkage for canonical source, transformation, rights, accessibility, and release.

## 6. Research record example

```yaml
research_claim:
  id: research.claim.agent_eval_reliability
  statement: >
    Reliability-sensitive agent capabilities should be evaluated across
    repeated trials rather than by one successful trajectory.
  temporal_scope:
    as_of: 2026-08-11
    review_after: 2026-11-11
  sources:
    - source.anthropic.demystifying_agent_evals.2026
  evidence_strength: primary_practitioner_guidance
  contradictions: []
  confidence: 0.92
  adoption:
    disposition: adopt
    affected_objects:
      - quirk.eval
      - quirk.capability
      - quirk.gate
    proposed_move_ref: move.eval_reliability_metrics
```

## 7. Research integrity gates

- no current claim without `as_of`;
- no adoption without primary-source review when available;
- no quote without exact provenance;
- no consensus claim without contradiction search;
- no benchmark claim without task/grader audit;
- no expert name used as authority by itself;
- no vendor guidance adopted without incentive/context note;
- no research-driven canonical mutation without a Proposed Move;
- no stale source silently retained as current;
- no discarded finding lost without boneyard rationale.

## 8. Initial primary resource index

- W3C PROV-O — https://www.w3.org/TR/prov-o/
- CloudEvents specification — https://github.com/cloudevents/spec
- OpenTelemetry semantic conventions — https://opentelemetry.io/docs/specs/semconv/
- NIST AI RMF Playbook — https://airc.nist.gov/airmf-resources/playbook/
- MCP specification — https://modelcontextprotocol.io/specification/
- C2PA 2.4 — https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html
- Anthropic, Demystifying evals for AI agents — https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- Lilian Weng, Harness Engineering for Self-Improvement — https://lilianweng.github.io/posts/2026-07-04-harness/
- Martin Kleppmann, local-first research and talks — https://martin.kleppmann.com/
- Simon Willison, prompt-injection field notes — https://simonwillison.net/tags/prompt-injection/
- Charity Majors, context-rich observability — https://charity.wtf/
- OpenAI Presence — https://openai.com/index/introducing-openai-presence/
