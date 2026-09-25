# Quirk Deck Grammar Architecture

## 1. Cardification boundary

A Quirk Object becomes a Card only when the interface benefits from selection, comparison, composition, drafting, play, collection, or inspection.

```text
Quirk Object
  ├── canonical definition
  ├── runtime state
  ├── evidence and authority
  └── Card projection
        ├── display
        ├── compatibility
        ├── access
        └── selectable behavior
```

Card projection must never replace the underlying object identity or authority.

## 2. Access topology

```text
Owned Collection
      │
      ├──────────────┐
      │              │
Temporary Entitlements
      │              │
      └──────┬───────┘
             ▼
         Access Pool
             │
     purpose / area / platform
     task / authority / settings
             │
             ▼
        Eligible Deck
```

Ownership survives subscription cancellation. Temporary access expires without deleting the Card Definition or historical receipts.

## 3. Hand compiler

The compiler receives one Goal and Intention plus current context. It may change the active lenses, aesthetics, and affordances. It may not alter:

- Goal facts;
- completion evidence;
- owned-card ledger;
- external authority grant;
- user settings;
- persistent memory;
- Canon.

## 4. Presets

A Preset is a versioned recipe containing:

- applicability;
- required and optional slots;
- preferred Card IDs and tags;
- exclusions;
- maximum authority;
- non-persistence rules;
- an approach profile.

It is not a frozen Hand and not a personality assignment.

## 5. Premium Unlocks

Premium is represented as an `EntitlementGrant`.

```text
EntitlementGrant
  → expands Access Pool
  → may increase capacity or available Cards
  → has authority_effect: none
```

Premium must never paywall inspection, correction, deletion, accessibility, safety, receipts, or the ability to disable personalization.

## 6. Output promotion

```text
Artifact
→ reviewed
→ accepted
→ rights and provenance clear
→ Asset candidate
→ reusable Asset
→ optional Golden evaluation
```

Art remains a distinct expressive object. It may also become an Asset, but expressiveness and reusability are separate judgments.

## 7. Live-proof invariant

The same Goal is compiled through:

- `preset.canon-architect`
- `preset.bryminn-studio`

The active Cards and approach differ. The following hashes must remain equal:

- Goal truth snapshot;
- facts snapshot;
- owned Collection snapshot;
- external authority snapshot.
