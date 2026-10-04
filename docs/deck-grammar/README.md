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
  --require-pass
```

## Admission posture

Passing the candidate suite permits human review. It does not activate the compiler, persist a Hand, change ownership, expand authority, promote Canon, or deploy a product.

Issue #26 evaluation artifacts:

- [`ADMISSION-EVALUATION.md`](ADMISSION-EVALUATION.md) — checklist, recommendation **revise**, Bryan decision open
- [`LIVE-TRIAL.md`](LIVE-TRIAL.md) — same-Goal two-Preset human trial answers
- [`OBJECT-PACK-REVIEW.md`](OBJECT-PACK-REVIEW.md) — non-agent scaffold review

Revised evaluation conformance content hash:

`efc7b28456076c06caac8fcc31d82662a521e5fc2d874274e9c6e17e067fa20a`
