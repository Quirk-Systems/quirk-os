# Supabase Candidate Projection

## Boundary

The root migration is a **candidate runtime projection**, not canon and not the authoritative Preference Graph:

```text
supabase/migrations/20260821090000_quirk_beauty_taste_engine_candidate.sql
supabase/tests/quirk_beauty_taste_engine_rls.sql
```

It stores beauty-scoped events and mirrors references to core decisions and receipts. Quirk core remains responsible for identity, grants, revocation, graph versioning, effect execution, receipt signing, and forgetting.

The migration creates a custom `beauty` schema but does not add that schema to Supabase Data API exposure. Exposure is a separate operator decision.

## Security posture

- no anonymous schema or table grants;
- RLS enabled on every table;
- exact actor, purpose, and session scope enforced by composite foreign keys;
- authenticated users receive column-level insert grants only for explicit human events;
- authenticated users cannot write lifecycle state, derived evidence, recommendations, proposals, decision mirrors, or receipt mirrors;
- option keys are validated against owned rows by a database trigger;
- recommendation evidence uses a relational link table instead of an unenforced UUID array;
- service-writer grants are explicit and server-only;
- a receipt trigger requires a live, human-confirmed `approve` decision;
- `auto_apply=true` is structurally rejected;
- service-role credentials never belong in browser or mobile code.

## Required isolated-branch verification

1. Create a temporary Supabase development branch after cost approval.
2. Apply the migration to that branch only.
3. Run `supabase/tests/quirk_beauty_taste_engine_rls.sql` as one transaction.
4. Prove anonymous access is absent.
5. Prove participant A cannot read or cross-bind participant B's rows.
6. Prove clients cannot manufacture lifecycle state or derived artifacts.
7. Prove nonexistent option keys fail.
8. Prove cross-actor recommendation reuse fails.
9. Prove `auto_apply=true`, expired decisions, and reject-to-receipt transitions fail.
10. Record schema digest, migration output, SQL proof output, and branch deletion receipt in the pull request.

## Current evidence ceiling

The migration has not been applied to the connected Supabase project. Static contract tests and SQL review are useful evidence, but they do not substitute for live PostgreSQL and RLS execution.
