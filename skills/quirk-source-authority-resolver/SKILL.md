---
name: quirk-source-authority-resolver
description: Resolve which Quirk source is canonical, candidate, runtime, work-plane, projection, superseded, stale, duplicated, or conflicting before any cross-platform read or write.
version: 0.2.0
status: candidate
family: research
authority_ceiling: infer
manifest: manifest.json
eval_suite: ../../evals/skills/conformance.json
---

# Quirk Source Authority Resolver

## Quirk contract

- Version: `0.2.0`
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
