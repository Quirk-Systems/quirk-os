# Brief: Manifest content-hash preimage

Status: draft
Owner: @bryansayler
Repository: `Quirk-Systems/quirk-os`
Date: 2026-10-03
Authority effect: **none**

## Context

The ask was an audit instruction: fix the reported bug and identify what else
across Quirk Systems needs fixing, setting, preventing, or denying. This brief
is one of the findings. The other four were repaired in code on the same
branch; this one is not a bug with a patch, it is a missing specification, so
it gets a brief instead.

Repository state at `3e67c819dc009bbf634747ada9091c60a218fe51` plus the three
fixes ahead of it on `claude/linkedin-content-critique-caghmx`. The admission
gate lives in `scripts/sync_control_plane/policy.py`, its stated policy in
`policies/manifest-admission-policy.yaml`, its shape in
`schemas/runtime-manifest.schema.json`, and a second enforcement copy in
`supabase/migrations/20260812030000_sync_control_plane_contracts.sql`.

The admission rule `evaluated_hash_matches` requires
`admission.evaluated_content_hash == content_hash`. Both fields live inside the
manifest being judged, and nothing anywhere computes either one from the
manifest's body. The rule therefore reads as a binding between an evaluation
and the bytes it evaluated, while being a comparison of two numbers the author
typed. An author who types the same string twice satisfies it; an author who
changes the manifest after evaluation and updates both fields also satisfies
it.

## Outcome

`content_hash` is derived from manifest bytes rather than declared: a single
documented preimage exists, one function computes it, both enforcement surfaces
(the Python gate and the Supabase trigger) reject a manifest whose declared
`content_hash` does not equal the computed value, and every fixture in
`evals/sync-control-plane/` carries a real digest. Observed by editing one
field of `valid-active-manifest.json` without touching its hashes and seeing
both surfaces reject it.

## Constraints

- Standard library plus the two pinned eval dependencies (`jsonschema`,
  `PyYAML`); CI runs Python 3.13.
- The preimage must be computable identically in Python and in PostgreSQL, or
  the SQL side has to verify a hash it cannot recompute. This is the binding
  constraint and it may force the choice of canonicalization.
- Authority effect stays `none`. The gate reports; admission remains a human
  act.
- `schema_version` stays `runtime-manifest.v2` unless the field set changes.
  Defining a preimage does not by itself change the shape.
- Append-only receipt and transition ledgers must not be rewritten to carry
  recomputed hashes for history already recorded.

## Semantic impact

- Change class: domain extension
- Concept IDs touched (from `.quirk/registry.json` in
  `Quirk-Systems/.github`): `concept.provenance` is consumed, not redefined.
  quirk-os carries no `.quirk/` of its own, so no local registry is affected.
- Proposed new concepts: none. "Preimage" is used in its ordinary
  cryptographic sense and is not proposed for admission.
- Collision check: `content_hash` already means at least three different things
  in this repository — the manifest field (bare 64 hex),
  `docs/product/chambered-workbench/EVIDENCE-CONTRACT-v0.1.md` and
  `docs/canon/AGENT-PLATFORM-SYSTEM-PROMPTS.md` (`sha256:<digest>`, prefixed),
  and `scripts/deck_grammar/common.py` (sha256 over canonical JSON, computed).
  A preimage spec must say which of these it is defining and leave the others
  alone or converge them deliberately.

## Evidence

- VERIFIED — `scripts/sync_control_plane/policy.py` compares
  `admission.get("evaluated_content_hash")` with `manifest.get("content_hash")`.
  Both are fields of the single `manifest` argument.
- VERIFIED — nothing computes a manifest content hash. Searched `scripts/`,
  `docs/`, `policies/`, `schemas/`, and `supabase/` for `content_hash`. The only
  computation found is `scripts/validate_sync_control_plane.py:203`, which
  hashes the validator's own output payload, and
  `scripts/deck_grammar/common.py:19`, which belongs to the Deck Grammar and is
  not applied to manifests.
- VERIFIED — the Supabase trigger repeats the same comparison in SQL:
  `if new.evaluated_content_hash<>new.content_hash then raise exception ...`.
  Two surfaces, one tautology.
- VERIFIED — the fixtures carry placeholders, not digests.
  `evals/sync-control-plane/cases/SCP-011.json` uses 64 `c` characters and
  `evals/sync-control-plane/valid-active-manifest.json` uses 64 `d`
  characters. Both satisfy the schema's `^[a-f0-9]{64}$`.
- VERIFIED — `schemas/runtime-manifest.schema.json` requires `content_hash` on
  every manifest and gives it no description, so the schema does not say what
  it covers either.
- VERIFIED — `scripts/deck_grammar/common.py` already implements a usable
  idiom: sha256 over `json.dumps(value, sort_keys=True,
  separators=(',', ':'), ensure_ascii=False)`. A preimage spec can adopt it
  rather than invent one.
- UNKNOWN — whether PostgreSQL can reproduce that canonicalization. `jsonb`
  does not preserve key order or duplicate keys and normalizes numbers, so
  `jsonb` round-tripping may not agree with Python's `json.dumps`. Resolved by
  computing both over the existing fixtures and comparing.
- UNKNOWN — which fields the preimage covers. `admission` plainly cannot be
  inside it, since the hash is what admission evaluates. Whether `status`,
  `requested_status`, and `metadata` are content or envelope is undecided.
  Resolved by Bryan, or by a decision record.
- UNKNOWN — whether any manifest outside this repository already publishes a
  `content_hash` that a new preimage would invalidate. Resolved by a search of
  the other Quirk repositories, which this brief has not done.

## Action

Smallest coherent intervention, in wave order:

1. This brief, at `docs/briefs/2026-10-03-manifest-content-hash-preimage.md`.
2. A decision record under `decisions/` naming the preimage: the field set,
   the canonicalization, the digest format, and whether the `sha256:` prefix
   conventions elsewhere converge or stay separate.
3. `scripts/sync_control_plane/content.py` with one `manifest_content_hash()`
   function, plus `tests/` coverage including a case that mutates one covered
   field and one uncovered field and asserts the hash moves only for the
   former.
4. The gate: `validate_manifest_admission` compares
   `evaluated_content_hash` against the computed value, not against a declared
   twin. Regenerate every fixture digest.
5. The SQL surface: either a trigger that recomputes the same preimage, or, if
   wave 1's UNKNOWN resolves against that being possible, a recorded decision
   that PostgreSQL verifies a hash supplied by a verified caller and what that
   costs.

Waves 2 through 5 are the plan's scope, not this brief's. This brief commits
wave 1 only.

## Verification

For wave 1: nothing to run; the brief asserts no behavior. For waves 2 through
5, the observable condition in Outcome is met when editing a single covered
field of `valid-active-manifest.json`, without touching either hash, makes
`python -m unittest discover -s tests -p 'test_*.py'` fail and
`python scripts/validate_sync_control_plane.py --repo . --require-admit` exit
non-zero, and when the same edit to an uncovered field does not.

## Risk

- The load-bearing assumption is that one preimage can serve both Python and
  PostgreSQL. If it cannot, the SQL trigger either stops checking the hash or
  starts trusting its caller, and either is a weakening that needs its own
  decision rather than a quiet implementation choice.
- Regenerating fixture digests makes every fixture diff unreviewable by eye. A
  reviewer cannot tell a correct digest from a wrong one. Containment: the
  generator is a committed script, and the test that mutates one field is what
  proves the digests mean something.
- A computed hash that still only ever compares against itself would be the
  same defect wearing a function call. Containment: the acceptance condition
  above is an external edit, not a self-consistency check.

## Residue

Two decisions need Bryan and are not granted here.

1. What the preimage covers. Specifically whether `status`,
   `requested_status`, and `metadata` are part of a manifest's content or part
   of its envelope. Everything downstream depends on this and it is not
   derivable from the files.
2. Whether the Supabase trigger is expected to recompute the hash or to trust
   a verified caller. This decides whether the database is an independent
   enforcement surface or a projection of the Python gate.

Deliberately excluded: the `sha256:`-prefixed `content_hash` conventions in
`docs/product/chambered-workbench/` and `docs/canon/`, which may or may not be
the same concept; and the approver rule repaired separately on this branch,
which closed a different hole in the same gate.

Unknown: whether the append-only transition ledger holds rows whose
`evaluated_content_hash` was accepted under the tautology. If it does, they
cannot be corrected by rewriting, and a correction record is the only honest
remedy.

This brief grants no canon, no admission, no authorization to build waves 2
through 5, and no publication. The plan and its tests still go through review.
