# Brief: Approval attestation for manifest activation

Status: draft
Owner: @bryansayler
Repository: `Quirk-Systems/quirk-os`
Date: 2026-10-03
Authority effect: **none**

## Context

This brief exists because a review of pull request 113 was right about that
pull request. Two findings, raised against `scripts/sync_control_plane/policy.py`
and `supabase/migrations/20261003090000_sync_control_plane_independent_approval.sql`:

> This still trusts the manifest's own `approved_by` string as evidence of human
> approval. A manifest can set `approved_by` to any schema-valid value such as
> `human.fabricated` (and invent the free-form decision/grant refs), and
> `validate_manifest_admission` returns no errors; there is no trusted approval
> registry or attestation lookup anywhere in this path.

> The database guard has the same remaining bypass: `approved_by` is
> caller-controlled text, so an insert can use `human.fabricated` plus arbitrary
> non-null decision/grant references and pass this predicate.

Both are correct. Pull request 113 removed the structural bypass — the gate no
longer keys off a flag the judged document sets for itself, and an `agent.`
principal can no longer approve an activation. It narrowed which strings are
accepted. It did not make the string trustworthy, and a gate that reads a field
the judged document supplies is the exact defect class that pull request was
about. The fix went one layer down and stopped.

Repository state at `778b1628b8aa9b4bc6ab0b29ae126e5dd0cd8095`.
`validate_manifest_admission(manifest)` takes one argument, the manifest, so
there is nothing else in scope for it to consult. The Supabase trigger reads
`new.*` on `quirk_sync.manifest_registry`, so the same holds there.
`policies/manifest-admission-policy.yaml` at 0.3.0 states the rule as a
constraint on the principal's shape, which is all either surface enforces.

## Outcome

An activation is refused unless an approval record exists that the activating
party could not have authored, and both enforcement surfaces check that record
rather than a field of the manifest. Observed by taking the valid fixture,
changing `approved_by` to a human principal with no corresponding approval
record, and seeing both `validate_manifest_admission` and an insert into
`manifest_registry` refuse it.

## Constraints

- Standard library plus the two pinned eval dependencies; CI runs Python 3.13.
- Whatever the attestation is, the database must be able to check it without
  trusting the inserting caller, or the trigger goes back to being a projection
  of the Python gate rather than an independent surface.
- Authority effect stays `none`. The gate refuses; admission remains a human act.
- `schema_version` stays `runtime-manifest.v2` unless the field set changes.
  Adding a required attestation reference to `admission` would change it, and
  that is a decision, not a detail.
- Append-only ledgers are not rewritten to carry attestations for history
  already recorded.

## Semantic impact

- Change class: domain extension
- Concept IDs touched (from `.quirk/registry.json` in `Quirk-Systems/.github`):
  `concept.provenance` is consumed, not redefined. `control` (entity type,
  parent `system.quirk`) is the closest canonical fit for an approval record,
  which is worth checking before anything new is proposed.
- Proposed new concepts: none by this brief. "Attestation" is used in its
  ordinary sense and is not proposed for admission.
- Collision check: `authority_grant_ref` already exists in `admission` and is
  free-form. If an attestation reference is added, the two must not become two
  names for the same thing; either the grant reference becomes the resolvable
  record, or the difference is stated.

## Evidence

- VERIFIED — `validate_manifest_admission` receives only `manifest`. Every value
  it tests, `approved_by` included, comes from that one document.
- VERIFIED — the only constraint on `approved_by` is
  `^(human|agent|service|system)\.[a-z0-9._-]+$` in
  `schemas/runtime-manifest.schema.json`, narrowed by the gate to the `human`
  namespace. `human.fabricated` satisfies both.
- VERIFIED — `decision_ref`, `authority_grant_ref` and `transition_ref` are
  `{"type": "string", "minLength": 1}`. Nothing resolves them, so any non-empty
  string passes.
- VERIFIED — the trigger tests `new.approved_by`, a column the inserting
  statement supplies. Confirmed by execution on PostgreSQL 16.13: an insert
  naming a sibling agent was accepted before the migration and refused after,
  which shows the predicate works and equally shows what it reads.
- VERIFIED — no approval registry, attestation table, or signature verification
  exists anywhere in `scripts/` or `supabase/`. Searched for `attest`,
  `signature`, `pubkey`, and `verify`.
- INFERRED — the rule as it stands still has value against the realistic
  threat, which is an agent activating itself by following the schema. It does
  not survive an actor willing to write a false human name, and nothing
  currently distinguishes those two cases.
- UNKNOWN — what can hold the approval record. A GitHub review by a CODEOWNER,
  a signed commit, a row in a table the service role cannot write, or an
  external decision service are all candidates with different trust roots.
  Resolved by Bryan naming the root.
- UNKNOWN — whether the database can verify it independently. If the
  attestation is a signature, PostgreSQL needs the verification primitive and
  the public key; if it is a row, the insert path must not be able to write that
  row. Resolved by deciding the trust root above.
- UNKNOWN — what happens to manifests already `active` under the weaker rule.
  The migration in pull request 113 refuses to complete when it finds one, which
  surfaces them without deciding their fate.

## Action

Smallest coherent intervention, in wave order:

1. This brief at `docs/briefs/2026-10-03-approval-attestation.md`.
2. A decision record under `decisions/` naming the trust root and whether the
   database verifies independently or is declared a projection.
3. The record's shape: a schema for the approval attestation, plus whatever
   `admission` needs to reference it, with the schema-version question answered.
4. `validate_manifest_admission` takes the resolved attestation and fails closed
   when it is absent, with tests covering absent, mismatched, and forged.
5. The trigger checks the same record, or the decision from wave 2 is recorded
   explaining why it cannot and what that costs.

Waves 2 through 5 are the plan's scope, not this brief's. This brief commits
wave 1 only.

## Verification

For wave 1: nothing to run; the brief asserts no behavior. For waves 2 through
5, the observable condition in Outcome is met when the valid fixture with
`approved_by` pointed at a human principal that has no approval record is
refused by `python -m unittest discover -s tests -p 'test_*.py'` and by an
insert into `manifest_registry`, and the same fixture with a real record passes
both.

## Risk

- The load-bearing assumption is that a trust root exists outside the manifest.
  If every candidate ultimately reduces to a string some agent can write, this
  outcome is unreachable and the honest result is a documented limit rather
  than a weaker check that reads as strong.
- A required attestation reference with no resolver is worse than today,
  because it reads as verification while being another free-form string.
  Containment: wave 4 lands the resolver and the failing tests together, or not
  at all.
- Scope creep toward signing infrastructure. Containment: wave 2 is a decision
  record, and the default answer to "build a PKI" is not yet.

## Residue

Two decisions need Bryan and are not granted here.

1. What the trust root is. Until that is named, every later wave is guesswork,
   because the record's shape follows from who can write it.
2. Whether the database verifies the attestation itself or is declared a
   projection of the Python gate. The same question the content-hash brief asks,
   and the two should be answered together rather than drifting apart.

Deliberately excluded: any change to the rule shipped in pull request 113,
which is a strict improvement and should not be reverted while this is open;
and the `service.`/`system.` approver allow-list, which is a separate open
question about which principals may approve rather than how approval is proven.

Unknown: whether any manifest already `active` was admitted on a fabricated
human approver. The data check added in pull request 113 finds non-human
approvers; it cannot find a human name nobody stood behind, and no record
exists to check it against. That is the gap this brief is about, pointed
backwards.

This brief grants no canon, no admission, no authorization to build waves 2
through 5, and no publication. The plan and its tests still go through review.
