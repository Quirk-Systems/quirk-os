# Quirk Daily Move Input/Output + Outcome Spine Design

**Status:** Candidate design for Task 2. This document defines durable interfaces only. It does not admit the Daily Move Program, activate a SkillPackage, grant runtime authority, mutate Supabase, project to Airtable/Drive, or merge PR #47.

**Parent evidence:** PR #47 (`agent/quirk-daily-move-fixture-corpus`) provides the seven positive weekday fixtures, eleven adversarial fixtures, and the `QDM-A01 noncanonical_root` Poison Marker. Task 2 is stacked on that branch and must preserve its fail-closed semantics.

## 1. Goal

Define versioned Daily Move input and output schemas that make every generated move traceable from its originating goal through a reserved decision, run receipt, and eventual outcome. A generated move must never exist as an orphaned assignment that cannot be joined to the later human decision, execution evidence, or real-world result.

## 2. Non-goals

Task 2 does not implement the Daily Move generator, Program manifest, SkillPackage, runtime evaluator, Supabase writes, projection delivery, outcome scoring, preference updates, publishing, autonomous execution, or admission. It does not add a new repository, root, database table, Airtable table, or projection plane.

## 3. Architectural decision: Inline Reserved Outcome Spine

Each generation request carries a complete `outcome_spine` envelope. The generator must echo that envelope exactly in its output. The identifiers are allocated before generation and are immutable across the generation boundary.

The required identifiers are:

- `spine_id`: stable identity for the whole lifecycle chain;
- `goal_id`: the declared goal or intention the move serves;
- `move_id`: stable identity of the proposed Daily Move;
- `decision_id`: reserved identity for the human decision about that move;
- `receipt_id`: reserved identity for the execution/verification receipt if the move is acted on;
- `outcome_id`: reserved identity for the eventual observed outcome.

Reservation is not realization. The schema must prevent the generator from claiming that a decision, receipt, or outcome has already happened merely because an identifier exists.

The lifecycle is:

```text
goal_id
  ↓
spine_id allocated
  ├── move_id       → generated proposed move
  ├── decision_id   → reserved decision address
  ├── receipt_id    → reserved execution/verification address
  └── outcome_id    → reserved observed-outcome address
```

## 4. Identity grammar

Task 2 introduces only Daily Move-specific identifier patterns. It reuses the existing receipt identifier grammar.

| Field | Pattern | Example |
|---|---|---|
| `spine_id` | `^qos_[A-Za-z0-9_-]+$` | `qos_20260821_01` |
| `goal_id` | `^qgoal_[A-Za-z0-9_-]+$` | `qgoal_daily_move_task2` |
| `move_id` | `^qdm_[A-Za-z0-9_-]+$` | `qdm_20260821_friday_01` |
| `decision_id` | `^qdecision_[A-Za-z0-9_-]+$` | `qdecision_20260821_friday_01` |
| `receipt_id` | `^receipt\.[a-z0-9._-]+$` | `receipt.daily-move.20260821.01` |
| `outcome_id` | `^qoutcome_[A-Za-z0-9_-]+$` | `qoutcome_20260821_friday_01` |

These names are candidate contract syntax, not new architectural planes.

## 5. Outcome Spine envelope

Both input and output require exactly this logical shape:

```json
{
  "spine_id": "qos_20260821_01",
  "goal_id": "qgoal_daily_move_task2",
  "move_id": "qdm_20260821_friday_01",
  "decision_id": "qdecision_20260821_friday_01",
  "receipt_id": "receipt.daily-move.20260821.01",
  "outcome_id": "qoutcome_20260821_friday_01",
  "decision_state": "reserved",
  "receipt_state": "reserved",
  "outcome_state": "reserved"
}
```

For Task 2, all three lifecycle state fields are constant `reserved`. Later lifecycle contracts may realize those addresses, but the Daily Move generator itself may not do so.

## 6. Input contract

Create `schemas/daily-move-input.schema.json` using JSON Schema draft 2020-12 and `additionalProperties: false`.

Required top-level fields:

- `schema_version` = `daily-move.input.v1`;
- `local_date` as ISO calendar date;
- `timezone` as a non-empty IANA timezone identifier string;
- `rotation_ref` as a non-empty policy/source reference;
- `outcome_spine` as the required envelope above;
- `authority_ceiling` = `propose`;
- `source_refs` as a non-empty unique array;
- `goal_context` with a non-empty `statement` and optional evidence references;
- `available_minutes` constrained to 10–15 inclusive for v1.

Optional top-level fields:

- `recent_move_refs`;
- `priority_refs`;
- `blocked_refs`;
- `proven_capability_refs`;
- `human_constraints`;
- `recent_outcome_refs`;
- `allowed_destination_types`.

Missing optional context must remain missing. The generator may not manufacture it.

## 7. Output contract

Create `schemas/daily-move-output.schema.json` using JSON Schema draft 2020-12 and `additionalProperties: false`.

Required top-level fields:

- `schema_version` = `daily-move.output.v1`;
- `outcome_spine` exactly matching the input envelope;
- `status` = `proposed`;
- `authority_ceiling` = `propose`;
- `weekday` in Monday–Sunday;
- `focus`;
- `why_it_matters`;
- `steps`, containing 3–5 non-empty strings;
- `deliverable`;
- `stretch_goal`;
- `capability_family`;
- `proof_required`;
- `completion_criterion`;
- `estimated_minutes`, constrained to 10–15 inclusive;
- `source_refs`;
- `risk_class`, using `L0`–`L5`;
- `reversibility`, using `trivial`, `reversible`, `compensatable`, or `irreversible`;
- `placement_disposition`, using `resolved`, `unresolved`, or `not_applicable`;
- `unknowns`, an array that may be empty but may not be omitted;
- `content_hash`, a lowercase SHA-256 hex string.

Optional output fields:

- `destination_hints`, permitted only as typed hints and never as claims of canonical placement;
- `recent_similarity`;
- `evidence_refs`.

The schema itself validates shape. Cross-document equality and semantic invariants are enforced by the Task 2 validator/tests.

## 8. Cross-document invariants

The validator must enforce all of the following after validating both JSON documents against their schemas:

1. `input.outcome_spine == output.outcome_spine` as deep structural equality.
2. The output `authority_ceiling` remains exactly `propose`.
3. `output.source_refs` must be a subset of or equal to references supplied in the input; the generator cannot invent source references.
4. `estimated_minutes` must remain within the input's available time.
5. `placement_disposition == unresolved` whenever no canonical destination evidence is supplied.
6. `destination_hints`, if present, must not be absolute filesystem roots, invented canonical repositories, or platform-plane declarations.
7. `decision_state`, `receipt_state`, and `outcome_state` remain `reserved`.
8. No output field may claim that the move was accepted, executed, verified, published, admitted, canonical, or outcome-confirmed.
9. A `content_hash` must cover the canonicalized move payload while excluding the `content_hash` field itself. The precise canonicalization procedure must be deterministic and documented in the implementation plan before code is written.
10. The Task 1 `QDM-A01` Poison Marker remains authoritative negative evidence: literal `Quirkroot` and equivalent unsupported architectural inventions must fail closed.

## 9. Fail-closed finding codes

Task 2 tests must cover at least these findings:

- `NO_SPINE`
- `MISSING_GOAL_ID`
- `MISSING_MOVE_ID`
- `MISSING_DECISION_ID`
- `MISSING_RECEIPT_ID`
- `MISSING_OUTCOME_ID`
- `SPINE_ID_MUTATED`
- `MOVE_ID_MUTATED`
- `DECISION_ID_MUTATED`
- `RECEIPT_ID_MUTATED`
- `OUTCOME_ID_MUTATED`
- `DUPLICATE_SPINE_ID`
- `REALIZED_EVENT_FABRICATION`
- `AUTHORITY_ABOVE_PROPOSE`
- `INVENTED_SOURCE_REF`
- `UNSUPPORTED_ARCHITECTURE`
- `PLACEMENT_UNRESOLVED`
- `TIMEBOX_EXCEEDED`
- `CONTENT_HASH_MISMATCH`

A failing case may emit more than one finding code when appropriate, but must include the code that identifies the primary violated invariant.

## 10. Duplicate identity handling

`DUPLICATE_SPINE_ID` cannot be proven by JSON Schema alone because uniqueness is contextual. The Task 2 validator therefore accepts an optional set of previously observed spine identifiers during evaluation. If the incoming `spine_id` already exists in that evaluation set for a different generation request, validation fails.

This is evaluation/runtime semantics only. Task 2 does not create a database uniqueness constraint or new persistence table.

## 11. Outcome Spine realization boundary

The Daily Move output does not create a Decision, Run Receipt, or Outcome object. It reserves identifiers for those future objects.

Later contracts must join back using the reserved identifiers and must carry their own evidence and authority semantics. A future decision object cannot be inferred from `decision_state: reserved`; a future receipt cannot be inferred from `receipt_state: reserved`; and an observed outcome cannot be inferred from `outcome_state: reserved`.

The following implications are prohibited:

```text
reserved decision_id ≠ approved decision
reserved receipt_id  ≠ execution happened
reserved outcome_id  ≠ outcome observed
generated move       ≠ accepted move
accepted move        ≠ executed move
executed move        ≠ useful outcome
```

## 12. Relationship to existing contracts

Task 2 does not replace `schemas/proposed-move.schema.json`, `schemas/skill-run-receipt.schema.json`, or `schemas/ledger-transition.schema.json`.

- `daily-move-output.v1` is the generator-specific contract and may later map into a `proposed-move.v1` projection.
- The reserved `receipt_id` uses the same identifier grammar as the existing Skill Run Receipt contract.
- Later execution evidence may use or extend existing receipt semantics, but Task 2 does not modify that contract.
- Existing ledger identity, authority, provenance, evidence, and reversibility conventions remain normative patterns for this design.

No schema changes outside the two new Daily Move contracts and their validator/test surfaces are justified in Task 2.

## 13. Task 1 compatibility

Task 2 is stacked from `agent/quirk-daily-move-fixture-corpus` and must not alter PR #47's fixture meanings.

The Task 2 validator/tests must continue to satisfy:

- seven positive weekday fixtures remain intact;
- eleven adversarial fixtures remain intact;
- `QDM-A01` remains a permanent Poison Marker;
- the Daily Move implementation gate remains fail closed;
- passing schema tests do not imply Program admission or Skill activation.

Task 2 may add schema-focused fixtures/tests, but it must not weaken or rename existing Task 1 adversarial semantics merely to simplify implementation.

## 14. Repository and branch strategy

Task 2 branch:

```text
main
  └── agent/quirk-daily-move-fixture-corpus
       └── agent/quirk-daily-move-io-schemas
```

The Task 2 PR should target `agent/quirk-daily-move-fixture-corpus` while PR #47 remains draft. It should remain independently reviewable and must not merge Task 1 implicitly.

Expected Task 2 implementation surfaces after this design is reviewed and an implementation plan is approved:

```text
schemas/daily-move-input.schema.json
schemas/daily-move-output.schema.json
scripts/validate_daily_move_io.py
tests/test_daily_move_io.py
evals/daily-move/io-cases/
```

Exact fixture filenames and any small manifest extension are to be specified in the implementation plan, following the existing repository pattern. No other architectural surface is assumed.

## 15. Verification and acceptance

Task 2 is complete only when fresh verification proves:

1. both schemas validate their positive examples;
2. every required Outcome Spine identifier is mandatory;
3. input/output spine mutation is rejected field-by-field;
4. reserved states cannot be promoted by generator output;
5. unsupported architecture is rejected using the Task 1 semantics;
6. invented source references are rejected;
7. timebox overflow is rejected;
8. deterministic content hashing is verified;
9. duplicate `spine_id` detection is tested contextually;
10. all existing Daily Move fixture tests still pass;
11. no Supabase, Airtable, Drive, publication, merge, admission, or runtime-grant mutation occurs.

Passing these checks is candidate evidence only.

## 16. Design rationale

Preallocating the full Outcome Spine costs a few identifiers but prevents the more expensive failure mode: recommendations that cannot later be reconciled with human decisions or observed outcomes. Keeping the envelope inline makes validation local and deterministic. Keeping later lifecycle states explicitly `reserved` prevents the IDs from becoming evidence laundering. Keeping Task 2 separate from the general Proposed Move and receipt schemas avoids prematurely widening shared contracts before Daily Move proves its semantics.
