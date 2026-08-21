# Quirk Beauty Domain Pack v0.1 Integration Plan

> **Execution contract:** use an isolated `agent/*` branch, TDD for behavior and
> migration contracts, draft stacked PRs, and fresh verification before claims.

**Goal:** Land the human-admitted Quirk Beauty domain boundary separately from a
candidate Taste Engine vertical slice, while preserving the proof chain and
blocking runtime/database promotion without evidence.

**Architecture:** `docs/canon/` owns the one admitted boundary. `domains/beauty/`
holds candidate semantics, schemas, deterministic code, proof tooling, product
and sales assets. Root `supabase/` holds a candidate projection migration and a
transactional RLS proof. Generic authority and Preference Graph mutation remain
external dependencies.

**Stack:** YAML/JSON Schema, Node.js 22/24, `node:test`, PostgreSQL 17/Supabase,
GitHub Actions.

## Task 1 — Boundary-only review

- Add `docs/canon/QUIRK-BEAUTY-DOMAIN-BOUNDARY.yaml` and its hash-basis payload as one semantic boundary.
- Record ADR-0002.
- Add the human-admitted boundary to the canon index without promoting candidate implementation.
- Open a draft PR from `agent/beauty-domain-boundary-v0-1` to `main`.

Pass condition: changed files contain no runtime, migration, provider, product,
or sales implementation.

## Task 2 — Candidate pack integration

- Place candidate source under `domains/beauty/`.
- Point pack validation at the authoritative boundary rather than duplicating it.
- Add a path-scoped Node 22/24 workflow.
- Add ownership rules limited to Quirk Beauty paths.
- Open a stacked draft PR from `agent/beauty-taste-engine-v0-1` to the boundary branch.

Pass condition: candidate status and activation denial remain machine-checkable.

## Task 3 — Supabase contract hardening by TDD

1. Add a migration-contract test that fails against the portable draft.
2. Remove client authority to rewrite session lifecycle state.
3. Bind session, actor, purpose, recommendation, outcome, proposal, and decision
   references with composite constraints.
4. Validate presented option keys before accepting a choice.
5. Grant only explicit server-writer privileges; retain no anonymous access.
6. Replace the comment-only RLS checklist with a transactional two-user proof.

Pass condition: Node contract test passes and the SQL proof is ready for an
isolated Supabase branch. Live execution remains blocked until branch cost is
explicitly confirmed.

## Task 4 — Verification

Run from `domains/beauty/`:

```bash
npm test
npm run validate
npm run proof:synthetic
npm run proof:verify -- proof/synthetic-example.json  # expected non-zero
```

Then inspect both PR diffs and GitHub check state. No merge or Supabase apply is
authorized by this plan.
