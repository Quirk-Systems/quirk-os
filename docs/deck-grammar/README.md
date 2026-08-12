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
