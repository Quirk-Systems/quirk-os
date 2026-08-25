# Versioning and Migration Rules

## Stable identity

- canonical domain ID: `quirk.products.beauty`;
- pack package: `@quirk/domain-beauty`;
- current pack version: `0.1.0`;
- schema IDs include semantic version;
- event names remain stable; envelopes carry their own version.

## Canonical boundary changes

Any change to purpose, ownership, delegation, exclusions, invariants, or proof requirements requires:

1. a dedicated canon diff;
2. explicit human admission;
3. content-hash update;
4. decision record;
5. compatibility analysis;
6. no implicit promotion of candidate runtime artifacts.

## Candidate schema changes

- additive optional fields: candidate minor version;
- changed meaning, required field, or enum removal: candidate major version;
- typo or documentation-only correction: patch version;
- database change: numbered forward migration plus rollback/restore strategy;
- proof schema change: prior proof bundles remain readable or receive an explicit migration tool.

## Projection rule

Supabase is rebuildable from domain events and core references. A projection migration cannot mutate canonical definitions.

## Upgrade evidence

Every migration PR needs:

- before/after schema digest;
- fixture migration result;
- denied and allowed RLS cases;
- replay/idempotency check;
- proof-verifier compatibility result;
- rollback or forward-fix decision.
