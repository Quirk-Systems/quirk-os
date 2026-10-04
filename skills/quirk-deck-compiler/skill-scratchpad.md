# Quirk Deck Compiler — Skill Scratchpad

**Status:** Candidate exploration surface. Ideas here do not become Canon, ownership, access, or authority without admission.

## Why cards

Cards are useful when a person must:

- select;
- compare;
- draft;
- combine;
- sequence;
- inspect;
- collect;
- unlock;
- swap;
- discard from current context.

Cardification is harmful when it hides object semantics, turns identity into cosmetics, or makes ordinary work feel like a store.

## Candidate mechanics

### Hand Size Budget

Limit cognitive and contextual load by slot class rather than one arbitrary card count.

```yaml
persona: 1..3
aesthetic: 1..3
affordance: 1..5
asset: 0..3
constraint: 0..5
wildcard: 0..1
```

### Mulligan

Replace a Card in the proposed Hand before activation. A Mulligan records why the first choice was wrong without lowering the underlying preference automatically.

### Sideboard

Cards likely to become useful if conditions change. Sideboard Cards are visible but inactive.

### Exhaustion

A temporary cooldown for Cards that have been overused, produced repetitive output, or exceeded a task budget. Exhaustion is not revocation.

### Synergy

A typed relation showing that two Cards work unusually well together for a named purpose. Synergy requires observed evidence.

### Counter

A Card that prevents or corrects a known failure pattern.

Examples:

- Groundtruth counters speculative architecture.
- Plain Fallback counters inaccessible generated UI.
- Receipt Required counters invisible adaptation.
- Boneyard Review counters sunk-cost resurrection.

### Pack

A curated group of Card Definitions or Entitlements. A Pack is not a Deck and not a Hand.

### Edition

A versioned presentation or configuration of the same underlying object projection. Edition does not create a new Quirk identity unless semantics change.

## Premium doctrine

Premium may unlock:

- saved Presets;
- additional Cards;
- private purpose partitions;
- model-routing controls;
- larger batch review;
- advanced analytics;
- local or private processing;
- generated interface tooling.

Premium may not lock:

- preference inspection or correction;
- data export or deletion;
- accessibility;
- safety;
- receipts;
- authority visibility;
- the ability to disable personalization.

## Analytics

Useful metrics:

- Cards proposed versus kept;
- Mulligan rate;
- Hand size versus acceptance;
- Card over-selection;
- Preset diversity;
- task outcome by Hand;
- same-Goal cross-Preset variance;
- preference leakage incidents;
- ownership and entitlement errors;
- time from Artifact to Asset promotion.

Do not optimize for card play volume. Optimize for accepted outcomes and reduced human burden.

## Open object candidates

- `CardSynergy`
- `CardCounter`
- `Sideboard`
- `HandBudget`
- `MulliganReceipt`
- `PackDefinition`
- `Edition`
- `ExhaustionState`
- `HandOutcome`
- `PresetVariant`
- `DeckPolicy`

Each remains a candidate until its operational difference matters.
