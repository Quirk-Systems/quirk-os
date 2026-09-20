---
status: CANDIDATE
authority_effect: none
runtime_state: INACTIVE
admission_state: NOT_AUTHORIZED
publication_state: NOT_AUTHORIZED
---

# Furniture Brief: F3 -> F11 Grounded-to-Banger contract

**Status: candidate, local-only.** This is a new module, not a promoted or
Canon-admitted one. It grants itself no execution, admission, or publication
authority. It was written and validated locally in one autonomous session
and has not been staged, committed, or reviewed. Before it is trusted for
anything beyond local experimentation it needs the same human plan review
this repo already requires for other consequential additions (see
`docs/applause-gate/` for the pattern: an exact-head review naming the
reviewed commit, before any promotion).

## What this is

A deterministic, offline compiler that turns one synthetic source record
(a `reality_shard` plus derived assets, a Furniture block, and an explicit
privacy/consent block) into either:

- a provider-neutral **Song Brief** (`decision: FINALIZE`), or
- a **refusal** (`decision: FLOP`) with machine-checkable reason codes and
  a suggested next step (`Finagle`).

It never calls a model, a music provider, or a network. It does not
generate audio, upload anything, publish anything, or send a message. See
`non_actions` on every receipt entry.

## Files

| Path | Purpose |
| --- | --- |
| `schemas/furniture-brief-contract.schema.json` | JSON Schema (2020-12) for the compile request, the twelve asset types, the Song Brief, and the receipt entry. |
| `scripts/furniture_brief/furniture.py` | Load-bearing Furniture check (7 dimensions, deterministic keyword gate). |
| `scripts/furniture_brief/grip.py` | GRIP scoring (Grounded/Reciprocal/Irreplaceable/Performable, 0-8, gate at 7). |
| `scripts/furniture_brief/lineage.py` | Parent/child asset lineage validation (acyclic, fully resolved, one root). |
| `scripts/furniture_brief/receipt.py` | Append-only, hash-linked receipts. Reuses `applause_gate.receipt.canonical_json`/`sha256_json` rather than a second hashing scheme. |
| `scripts/furniture_brief/compiler.py` | The F11 trace itself: `compile_batch()` / `compile_and_receipt()`. |
| `scripts/validate_furniture_brief.py` | CLI: runs the fixture corpus through the compiler + schema + receipt-chain verification, prints a JSON summary, exits non-zero on any mismatch. |
| `evals/furniture-brief/cases.json` | 7 synthetic fixtures: 1 success, 6 refusals (one per required category). |
| `tests/test_furniture_brief.py` | unittest suite: fixture corpus, receipt-tamper detection, the A/Bry Furniture-specificity experiment. |

## Run it

```
pip install jsonschema==4.26.0 pytest==9.1.1   # already declared in requirements-evals.txt
PYTHONPATH=scripts python3 scripts/validate_furniture_brief.py --require-pass
PYTHONPATH=scripts python3 -m pytest tests/test_furniture_brief.py -v
```

## The contract, briefly

- **F-cubed provenance** (`provenance.f_tier`): `F0` fantasy, `F1`
  observation, `F2` lived/anonymized, `F3` co-owned intimacy.
- **Consent fields are independent, never inferred from each other.**
  `consent_to_intimacy` gates nothing about storage or publication.
  `consent_to_store` and `consent_to_publish` are checked separately.
  Only `consent_to_store` gates whether a Song Brief may be built at all;
  `consent_to_publish` is carried through as `publication_permitted` and
  is never assumed true.
- **Furniture** is load-bearing only if all seven dimensions
  (bodies/position, objects/obstruction, distance/movement, temperature,
  acoustics, geography, privacy pressure) answer the literal question:
  *could we block this scene physically and mix it spatially?* Decorative
  filler (`"n/a"`, `"a room"`, `"tbd"`) fails deterministically.
- **GRIP** is four axes, 0-2 each, 0-8 total, computed only from concrete
  signals already present in the batch (never a vibe call). The
  generation gate requires `total >= 7`.
- **The F11 trace** (`Find -> Fact -> Furniture -> Fiction -> Freak -> Flex
  -> Fit -> Freeze`, then `Finalize` or `Flop -> Finagle`) is the literal
  stage list returned in `f11_trace`, each stage recording its own
  pass/refuse status and the concrete reason.
- **Lineage**: every batch is exactly one `reality_shard` root plus
  children whose `parent_ids` resolve inside the batch, acyclic.
- **Receipts** are append-only and hash-linked: each entry seals a
  `sha256` of its own content as `entry_hash`, and chains to the previous
  entry's `entry_hash` via `prev_hash`. `verify_chain()` recomputes both
  and reports the first broken index. Every entry records
  `input_hash`, `output_hash`, `revision`, `decision`, a `proof_state`
  (concrete measured facts, not prose claims), and explicit
  `non_actions`.

## Refusal categories proven (see `evals/furniture-brief/cases.json`)

1. `ADULT_CONSENT_MISSING_OR_AMBIGUOUS` -- missing or ambiguous adult/consent confirmation.
2. `STORAGE_OR_CONTENT_PERMISSION_MISSING` -- consent to intimacy present, storage permission not.
3. `IDENTITY_RISK_UNACCEPTABLE` -- identity risk above `low`, or insufficient anonymization for F2/F3.
4. `FURNITURE_NOT_LOAD_BEARING` -- Furniture present but decorative.
5. `GRIP_BELOW_THRESHOLD` -- Furniture and consent pass, but the total is 6/8.
6. `LINEAGE_INVALID` -- a child asset references a parent that does not exist in the batch.

Plus, independently: a tampered or reordered or truncated receipt chain is
detected by `verify_chain()` (`tests/test_furniture_brief.py::ReceiptChainIntegrityTests`).

Exactly one fixture (`case-001-success`) reaches `FINALIZE` and produces a
Song Brief + receipt.

## The A/Bry experiment

`ABryFurnitureSpecificityExperimentTests` takes the same synthetic root and
every other asset from `case-001-success`, changes *only* the Furniture
block to the decorative version from `case-005-furniture-decorative`, and
observes:

| | Furniture decorative | Furniture load-bearing |
| --- | --- | --- |
| `decision` | `FLOP` | `FINALIZE` |
| GRIP `grounded` | 1/2 | 2/2 |
| GRIP `total` | 7/8 | 8/8 |
| `furniture_assessment.load_bearing` | `false` | `true` |

**Verdict: ADVANCE.** Furniture specificity was the only variable changed
and it alone flipped the gate and raised Grounded. It is a cheap,
deterministic, iterable lever worth spending more synthetic fixtures on
before touching any other axis. This is an observation about the
*contract's readiness signal*, not a claim about how any resulting song
would actually sound -- no audio was generated.

## Explicit non-claims

This module does not claim, and its receipts do not record: legal
clearance, platform reliability, audio quality, commercial viability, or
that anything ran outside this local validation. It has made zero
provider calls, generated zero audio, and published nothing.
