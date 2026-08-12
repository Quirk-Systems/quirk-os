---
name: quirk-source-authority-resolver
description: Resolve which Quirk source is canonical, candidate, runtime, work-plane, projection, superseded, stale, duplicated, or conflicting before any cross-platform read or write.
---

# Quirk Source Authority Resolver

## Quirk contract

- Version: `0.1.0`
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
