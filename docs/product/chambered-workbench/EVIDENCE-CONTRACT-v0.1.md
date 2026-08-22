# Evidence Contract v0.1

**Status:** Candidate design contract  
**Contract id:** `contract.evidence.operator.v0.1`  
**Authority ceiling:** `propose`  
**Executable schema:** none  
**Runtime effect:** none

## Purpose

Keep source, observation, extraction, interpretation, inference, evaluation, contradiction, and outcome distinguishable as a `HookCandidate` changes. Evidence informs a named decision. It does not authorize the decision, certify value, transfer rights, or create truth through repetition.

## Evidence atom

An evidence atom is the smallest inspectable, source-bound observation used by the workbench.

```yaml
contract_version: evidence.atom.v0.1
atom_id: evidence.atom.<stable-id>
atom_version: <version>
atom_digest: sha256:<digest>

evidence_class: source | observation | extraction | interpretation | inference | test_result | evaluation | contradiction | outcome

source:
  source_ref: <source-ref>
  source_binding_ref: <source-binding.v2-ref-or-null>
  authority_class: canonical | runtime | work | projection
  locator: <reproducible-locator>
  content_hash: sha256:<digest-or-null>
  author_or_custodian_ref: <actor-ref-or-null>

claim:
  statement: <bounded-statement>
  exact_span_or_selector: <selector-or-null>
  affected_object_versions: [<object-version-ref>]
  decision_use: <named-decision>

provenance:
  capture_actor_ref: <actor-ref>
  extraction_actor_ref: <actor-ref-or-null>
  method: <method>
  observed_at: <date-time>
  captured_at: <date-time>
  as_of: <date-or-date-time>

quality:
  source_quality: normative_standard | peer_reviewed_primary | official_primary | direct_practitioner | strong_secondary | community_signal | unknown
  evidence_strength: direct | reproduced | corroborated | derived | expert_judgment | model_inference | anecdotal | unknown
  confidence: <0..1-or-null>
  confidence_basis: <basis-or-null>

freshness:
  status: unknown | fresh | aging | stale | expired
  last_verified_at: <date-time-or-null>
  max_age_days: <integer-or-null>
  evaluated_at: <date-time>
  reason: <reason>

rights_and_use:
  consent_ref: <ref-or-null>
  allowed_purposes: [<purpose>]
  prohibited_purposes: [<purpose>]
  reuse_status: allowed | restricted | prohibited | unknown
  retention_class: <retention-class>

integrity:
  contradiction_refs: [<evidence-ref>]
  supersedes_refs: [<evidence-ref>]
  poison_status: clear | suspected | confirmed
  limitations: [<limitation>]
```

An atom proves only its bounded observation. Authenticity does not prove correctness; storage does not grant consent or reuse; a model summary is not an independent source.

## Evidence bundle

```yaml
contract_version: evidence.bundle.v0.1
bundle_id: evidence.bundle.<stable-id>
bundle_version: <version>
bundle_digest: sha256:<digest>
purpose: <named-decision-purpose>
subject_versions: [<exact-object-version-ref>]
assembler_ref: <actor-ref>
assembled_at: <date-time>

included_atom_refs: [<atom-ref>]
excluded_atom_refs:
  - ref: <atom-ref>
    reason: <reason>

claim_refs: [<claim-ref>]
contradiction_refs: [<atom-or-claim-ref>]
unresolved_gaps: [<gap>]
coverage_statement: <what-is-and-is-not-covered>
freshness_policy_ref: <policy-ref>
freshness_evaluated_at: <date-time>
derivation_edges: [<typed-edge-ref>]
rights_purpose_intersection: [<allowed-purpose>]
```

Bundling cannot upgrade source quality, evidence strength, freshness, rights, confidence, or authority. Repeated citations and derived summaries collapse to their original source for independence analysis.

## Claim obligations

Each claim used in the workbench records:

- stable id, version, statement, `as_of`, and temporal scope;
- classification as `observation`, `interpretation`, `inference`, `evaluation`, or `outcome`;
- atom and bundle refs;
- source quality and evidence strength using current repository vocabulary;
- confidence and its basis, kept separate from permission;
- contradictions and unresolved gaps;
- affected exact object versions;
- the named decision it may inform;
- review date and supersession refs;
- research disposition such as `adopt`, `adapt`, `reject`, `monitor`, `experiment`, or `boneyard` where relevant.

Research disposition is not Canon admission, selection, execution, release, publication, or preference.

## HookCandidate evidence obligations

| Decision | Required evidence | Evidence that is insufficient alone |
| --- | --- | --- |
| scope the fixture | origin, human purpose confirmation, source binding, rights declaration | agent inference of intent |
| mark variant review-ready | exact parent, derivation operation, constraint checks, rights inheritance, known failures | generator confidence or aesthetic score |
| mark decision-ready | versioned rubric, evaluator declarations, criterion evidence, counterevidence, dissent, freshness | consensus, winner bracket, average score |
| preserve a decision | exact human decision, authority grant, evidence snapshot digest, retention basis | Gallery location or reviewer reaction |
| record outcome | observed use, date, audience/context, comparison or baseline, limitations | repeated generation, self-rated quality, model memory |
| propose preference update | real outcome plus explicit human confirmation for the bounded preference claim | selection, reuse, praise, silence, or inferred satisfaction |

## Contradiction and freshness rules

1. Known contradictions remain attached even when rebutted, outweighed, or superseded.
2. Every contradiction has a disposition and rationale; omission is not resolution.
3. A bundle with unresolved material contradictions cannot be described as settled.
4. Stale or expired evidence remains inspectable but cannot satisfy a freshness requirement or serve as sole qualifying evidence for a consequential transition.
5. Refreshing evidence creates a new atom or version; it never rewrites the old observation.
6. A freshness waiver requires separate waiver authority and a receipt and cannot waive non-waivable rights, consent, safety, or provenance gates.
7. Confidence is recalculated or explicitly reaffirmed when material evidence expires, is poisoned, is revoked, or gains a contradiction.
8. Evidence produced by a candidate, its creator, or its evaluator may be included but cannot self-certify value, safety, release readiness, admission, or Canon.
9. A projection records what another source said. It does not become a new source merely because it appears in another tool.
10. Outcome evidence must identify the real-world event and cannot be manufactured from the design's own expected outcome.

## UI obligations

- Every claim can expand to its source locator, extraction, actor, date, freshness, confidence basis, limitations, and contradictions.
- Derived evidence visibly points to its parents.
- The drawer separates supporting evidence, counterevidence, excluded evidence, and gaps.
- Confidence never shares the same visual control or label as authority.
- Stale and disputed evidence remain readable but are marked unusable for named decisions that require freshness.
- No score, chart, trend, status light, or count appears as telemetry without an event contract, timestamp, population, denominator, and drill-down.

## Compatibility posture

This design references `research-claim.v1` and `source-binding.v2` concepts. It adds no new executable evidence type, authority class, platform binding, or adoption state. Future implementation work must reconcile exact schema versions and preserve existing source-authority boundaries.

