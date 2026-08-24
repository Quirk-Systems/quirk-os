# Quirk Daily Move Fixture Contract

**Status:** candidate / fixture-only
**Authority ceiling:** `propose`
**Runtime implementation:** absent by design in Task 1

This directory fixes the first executable boundary for Quirk Daily Move:

- seven positive fixtures, one for each weekday rotation;
- eleven adversarial fixtures covering architectural invention, authority leakage, stale approval, candidate chaining, repetition, file theater, timezone mistakes, missing evidence, and premature product claims;
- `QDM-A01 noncanonical_root` as a Poison Marker for the long-running thread that repeatedly invented `Quirkroot` and treated it as established architecture.

## Permanent rule

A plausible path, root, repository, platform plane, table, base, or projection does not become Quirk architecture because a model emitted it repeatedly. Placement must resolve to canonical Git-backed evidence or remain explicitly `UNRESOLVED`.

`QDM-A01` includes both the literal historical mistake and equivalent invented architectures. Its pass control resolves an immutable Git object for the existing Sync Control Plane Program without transferring that Program's authority to Daily Move. Mutable, dangling, irrelevant, wrong-scope, and cross-Program references remain distinct failures.

The corpus contains 65 embedded trials and 77 comparator units in total. Embedded trials are independent comparator units. Their scenario is assembled only from `input.trial_context` plus the selected trial's `scenario`; parent attacks, fixture identity, other trials, comparator hints, and all expected results stay oracle-side. Each trial has an exact oracle in the top-level `trial_expectations` map. Repetition coverage includes compound disguises, a duplicate at the end of a longer complete history, an open candidate represented by a schema-valid Proposed Move with `disposition: awaiting_authority`, the inclusive recency edge expressed through a different RFC 3339 offset, and isolated malformed timestamp, history-signature, and candidate-signature failures.

A future implementation must own its evaluator declaration at `Program.acceptance.fixture_evaluator`, while remaining `candidate` with `authority.maximum_right: propose`. The fixture manifest cannot select the implementation entrypoint.

Skill invocation adversarials reuse the existing `schemas/skill-runtime-grant.schema.json` contract and the Sync Control Plane grant validator. They bind the candidate Value Foundry ID, version, manifest digest, admission reference, ceiling, and declared actions, and still reject loading because the Skill is not admitted. Connector-write and publication inputs do not borrow that Skill-only contract or create another grant grammar: their non-null references are explicitly untrusted claims or fixture-local approval observations. Live external-write and publication authority remain unresolved adapter contracts for the implementation PR.

The declaration is checked without import: `module_ref` must resolve through regular, non-symlink path components beneath `scripts/daily_move`, and the declared callable must be one undecorated top-level Python function or async function with the exact `(scenario, adapters)` interface. This verifies declaration shape, never callable behavior. Daily Move implementation markers are detected by path and content across the repository tree, including submodule declarations, `qdm`, `DailyMove`, evaluator/generator aliases, and recognizable focus rotations even when renamed or numerically indexed.

## Boundaries

Task 1 does not:

- add the Candidate Program or SkillPackage;
- activate a skill or grant runtime authority;
- add a Supabase migration or table;
- mutate Airtable, Notion, or Google Drive;
- use an OpenAI API key or live model evaluator;
- publish, merge, deploy, or promote Canon.

Passing this fixture-only suite proves that the candidate corpus, immutable references, schema boundaries, and CI connectivity conform. The in-source semantic digests are candidate-local until a protected base and human review anchor them. Branch protection and CODEOWNERS enforcement are unobserved. Bryan retains admission and execution authority.

The pure corpus comparator accepts exactly the declared output-label set. Each positive output must contain one clean, case-specific Proposed Move whose full required semantics match the selected scenario; unrelated optional residue, noncanonical architecture values, generic or reused IDs/titles, and duplicate cross-output signatures fail. Adversarial outputs cannot carry Proposed Move/card/evidence payloads.

This fixture-only validator never imports or executes repository implementation code. If a Daily Move Program, Skill, registry entry, or executable namespace marker appears, it validates the candidate/propose bindings and fails closed with `RUNTIME_CONTAINMENT_REQUIRED`; all attempted/executed counters remain zero. The implementation PR must supply a separately reviewed OS-contained runner. Total external writes, projections, admission, activation, publication, deployment, and merge effects remain explicitly unobserved here.

Marker detection is a static guard, not proof against deliberately obfuscated code hidden inside an allowlisted gate file or expressed without recognizable Daily Move semantics. Diff review, protected-branch review, and the future contained runner remain required; a fixture-only pass cannot admit or activate an implementation.

The CI gate is an exact six-step contract on `ubuntu-24.04`: universal pull-request coverage, `main`-only push coverage, read-only permissions, credential-free full-history checkout, pinned actions, exact dependency/test/conformance commands, and an `always()` evidence upload. Proposed Moves are checked with the target repository's canonical JSON Schema and strict RFC 3339 date-time validation. A future Daily Move Skill must use the canonical `evals/skills/daily-move.json` contract and bind that regular in-tree alias exactly to `evals/daily-move/fixtures.json`.

## Task 2 — I/O and Outcome Spine

Task 2 adds generator input/output contract evidence under `io-cases/`.
It does not replace or weaken `QDM-P01..P07` or `QDM-A01..A11`.
Decision, receipt, and outcome IDs are reserved addresses, not realized events.
Task 2 conformance is Candidate evidence only and creates no external writes.
