---
name: quirk-source-authority-resolver
description: Resolve which Quirk source is canonical, candidate, runtime, work-plane, projection, superseded, stale, duplicated, or conflicting before any cross-platform read or write.
version: 0.2.1
status: candidate
family: research
authority_ceiling: infer
manifest: manifest.json
eval_suite: ../../evals/skills/conformance.json
---

# Quirk Source Authority Resolver

## Quirk contract

- Version: `0.2.1`
- Status: `candidate`
- Authority ceiling: `infer`
- Canonical output: authority census plus unresolved conflicts

## Use when

Multiple repositories, documents, database rows, conversations, or platform records appear to describe the same object or decision.

## Procedure

1. Assign every source a stable reference and fingerprint.
2. Record author, date, version, purpose, scope, and declared authority.
3. Separate Canon, candidate, runtime state, work material, and projection.
4. Trace supersession and derivation rather than choosing by recency alone.
5. Compare normalized claims and identify material divergence.
6. Return one authoritative source only when policy and evidence permit it.
7. Otherwise mark the conflict unresolved and emit a Proposed Move.

## Current-state reconciliation

For a status refresh, identify the owning repository and exact head before changing prose.
Read the applicable decision record and its successor/revocation chain, including issue
comments; an old PR description is not a reliable inventory of outstanding permissions.
A closed issue alone does not prove its acceptance criteria passed.

Track permission and delivery separately. A scoped approval with no implementation is
**approved / implementation unverified**, not **awaiting permission**. An implemented
candidate with no promotion decision remains **candidate**, even when merged or CI-green.
Keep administrator access, policy enforcement, human judgment, and runtime activation
separate. A successful failing/clean CI pair does not prove required-check enforcement.

Bind evidence to its actual reviewed or tested revision, including a synthetic merge SHA
when that is what the job checked. When a branch advances, preserve the older receipt as
historical and assess the new head separately. Do not copy an old test count onto a new SHA.
A freshness edit changes the projection; it cannot create an approval or successful outcome.

Read-only discovery may report missing authority as unknown. It does not need the mutation
grant it is trying to locate. User authorization for a bounded repair persists; ask only
when the next action genuinely exceeds that authorization or a material conflict remains.

Examples for review: an approved but uninstalled Core rule is an implementation blocker;
a superseding plan grant overrides an older plan's permission warning only for its bound
version and scope; an old-head pass stays historical after a head change; merge plus green
CI with no promotion record remains candidate. These examples are guidance, not runtime proof.

## Output

```yaml
authority_census:
  canonical: []
  candidates: []
  runtime: []
  work: []
  projections: []
  superseded: []
  conflicts: []
  proposed_moves: []
```

## Stop conditions

Stop before mutation when authority is missing, contradictory, expired, inferred only from convenience, or would require invisible Bryan-context.

## Machine binding

- Manifest: [`manifest.json`](manifest.json)
- Eval suite: [`../../evals/skills/conformance.json`](../../evals/skills/conformance.json)
- Mapping contract: [`../../mappings/skill-package.v1.yaml`](../../mappings/skill-package.v1.yaml)
- Runtime status: candidate source only; the runtime loader must reject this version until a separate admission record and scoped grant exist.

## Invocation contract

Use this skill only when its trigger contract matches, required sources and authority are available, and no trigger collision remains unresolved. The caller owns purpose and authority. The skill owns procedure and evidence. A successful run may emit `authority_census` and Proposed Moves; it may not convert either into Canon, active runtime state, or an irreversible write.

## Evaluation and learning

Positive, adversarial, regression, and authority cases are mandatory. Feedback appends evidence and may produce a mutation candidate. It never rewrites this running version. Any successor must receive a new version, digest, evaluation record, and external admission decision.

## Universal stop rule

Capability, credentials, connected tools, successful validation, model confidence, or repeated use never create authority. Stop before self-activation, self-escalation, Canon promotion, history mutation, or action beyond the external grant.
