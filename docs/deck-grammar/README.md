# Quirk Deck Grammar Candidate Pack

**Status:** Candidate  
**Move:** `move.deck-grammar.create-candidate-pack`  
**Parent:** Quirk Intent Shaper PR #15  
**Authority ceiling:** `propose`

## Canon candidate

> Quirk Objects are the underlying things. Cards are selectable projections of those things. Decks define what is eligible. Hands define what is active. Presets define how a Hand is assembled. Unlocks define access—not authority.

## Package contents

- fifteen Draft 2020-12 JSON Schemas;
- `skill.quirk-deck-compiler`;
- a deterministic Hand compiler;
- Canon Architect and BryMinn Studio Presets;
- one same-Goal/two-Preset live proof;
- eleven adversarial fixtures;
- four Mermaid diagrams;
- a reusable Quirk Object Pack scaffolder;
- canonical guidance for repository management, system prompts, custom instructions, settings, project instructions, and reference documents.

## Grammar

```text
Area
→ Goal
→ Intention
→ Access Pool
→ Eligible Deck
→ Hand Preset
→ Proposed Hand
→ Human Adjustment
→ Task Affordances
→ Moves
→ Artifacts
→ Assets / Art
→ Feedback Receipt
→ Adaptation Proposal
```

## Separation invariants

```text
Object ≠ Card
Collection ≠ Access Pool
Access ≠ Ownership
Rarity ≠ Quality
Quality ≠ Authority
Premium ≠ Authority
Preset ≠ Identity
Hand ≠ Memory
Discard ≠ Delete
Artifact ≠ Asset
Aesthetic ≠ Permission
```

## Commands

```bash
python -m pip install -r requirements-evals.txt

python -m unittest discover -s tests -p 'test_deck_grammar.py' -v

python scripts/validate_deck_grammar.py \
  --repo . \
  --output evals/deck-grammar/conformance-results.json \
  --metrics-output evals/deck-grammar/conformance-metrics.json \
  --require-pass

python scripts/deck_grammar/perf_benchmarks.py \
  --scenario build_access_pool \
  --output evals/deck-grammar/perf-build-access-pool.json

python scripts/deck_grammar/perf_benchmarks.py \
  --scenario compile_hand \
  --output evals/deck-grammar/perf-compile-hand.json
```

`perf-build-access-pool.json` compares the legacy linear duplicate-search behavior with the set-backed implementation and reports a relative speedup ratio instead of an absolute timing gate.  
`perf-compile-hand.json` records workload shape plus `cProfile` cumulative hot paths for `compile_hand` without introducing flaky pass/fail thresholds.
`conformance-metrics.json` records validator wall-clock and workload dimensions for CI trend monitoring.

## Admission posture

Passing the candidate suite permits human review. It does not activate the compiler, persist a Hand, change ownership, expand authority, promote Canon, or deploy a product.

Issue #26 evaluation artifacts:

- [`ADMISSION-EVALUATION.md`](ADMISSION-EVALUATION.md) — checklist, recommendation **revise**, Bryan decision open
- [`LIVE-TRIAL.md`](LIVE-TRIAL.md) — same-Goal two-Preset human trial answers
- [`OBJECT-PACK-REVIEW.md`](OBJECT-PACK-REVIEW.md) — non-agent scaffold review

Revised evaluation conformance content hash, regenerated with
`python scripts/validate_deck_grammar.py --repo . --output evals/deck-grammar/conformance-results.json --require-pass`:

`f36aa708fdd414924981c20778ee8ea98b158b436553c9a455fb2441737c917f`

It supersedes `ffdfd6d9b0ebc828621966394a2bd733141fef158b8474b9e7a754a7031fbfa7`, whose `content-hash-binds` entry recorded only a
verdict and not the digest it verified, so it would have read identically
whichever proof had been bound. That in turn superseded
`efc7b28456076c06caac8fcc31d82662a521e5fc2d874274e9c6e17e067fa20a`, which covered the suite before the
`content-hash-binds` check existed. Omitting `--output` prints the evidence
and leaves the tracked artifact where it was, which is how that hash came to
be quoted here while the suite it described had moved on.
