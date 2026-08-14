---
name: quirk-deck-compiler
description: Compile purpose-scoped Quirk Objects and access rights into an Eligible Deck and proposed Active Hand without changing truth, ownership, settings, memory, or authority.
---

# Quirk Deck Compiler

## Contract

- Version: `0.1.0`
- Status: `candidate`
- Authority ceiling: `propose`
- Primary output: `EligibleDeck`, `ActiveHand`, and invariant proof
- Parent capability: `skill.quirk-intent-shaper`

## Use when

A task benefits from selecting and composing Persona, Aesthetic, Affordance, Asset, Goal, Intention, Area, or other Card projections.

Do not use when direct object access is simpler than card composition.

## Inputs

- current explicit instruction;
- purpose partition;
- Area;
- Goal;
- Intention;
- Card Definitions;
- owned Collection;
- temporary Entitlement Grants;
- Hand Preset;
- platform and task class;
- external authority grant;
- settings and exclusions.

## Procedure

1. Resolve the current Goal, facts, completion evidence, and Intention.
2. Build an Access Pool without calling temporary access ownership.
3. Filter the Eligible Deck by purpose, Area, platform, task, state, expiry, capability, and authority.
4. Apply a versioned Preset recipe.
5. Produce a proposed, ephemeral Hand.
6. Explain every included and excluded Card.
7. Snapshot truth, ownership, and external authority.
8. Compare candidate Hands when multiple Presets are evaluated.
9. Reject any attempt by premium access, rarity, Persona, Aesthetic, or successful execution to alter authority.
10. Emit evidence and a Proposed Move.

## Required invariants

```text
Object ≠ Card
Access ≠ Ownership
Rarity ≠ Quality
Premium ≠ Authority
Preset ≠ Identity
Hand ≠ Memory
Discard ≠ Delete
Artifact ≠ Asset
Aesthetic ≠ Permission
```

## Output

- typed `EligibleDeck`;
- typed proposed `ActiveHand`;
- included and excluded Card reasons;
- truth, ownership, and authority snapshots;
- approach summary;
- invariant comparison;
- conformance receipt.

## Stop conditions

Stop when:

- the Goal or external authority is ambiguous;
- a Preset requests permanent identity assignment;
- a Hand requests persistence without consent;
- rights or ownership are unclear;
- an entitlement claims authority effects;
- a Card requires unavailable capability or authority;
- a task does not benefit from card composition.
