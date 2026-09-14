# Candidate Object Grammar

These object names are implementation candidates, not admitted ontology.

## `TasteContext`

Declares **why** the choice is being made. Context is not decoration; it partitions preference evidence.

Required ideas:

- actor-independent context ID;
- realm `beauty`;
- purpose partition;
- explicit attributes such as occasion, budget, lighting, effort, or use case.

## `TasteOption`

A comparable candidate with visible attributes. Options must expose the contrasts used to derive evidence. Hidden embeddings may support retrieval later but cannot be the only explanation surface.

## `TasteChoice`

An append-only record of explicit selection or abstention. It says what happened, not why the system imagines it happened.

## `PreferenceEvidence`

A candidate claim derived from a specific contrast:

```text
actor preferred finish=satin over finish=matte
within purpose=personal_beauty_recommendation
because of choice=choice:001
confidence=0.70
```

It is evidence for a possible preference edge. It is not the edge itself.

## `Recommendation`

An expiring proposal containing:

- recommended option;
- deterministic score;
- confidence;
- cited evidence IDs;
- feature contributions;
- insufficient-evidence state;
- expiry.

## `OutcomeObservation`

An explicit report after a real-world test. `purchase_event`, `link_click`, `dwell_time`, and `no_complaint` are forbidden source types for preference outcomes.

## `GraphUpdateProposal`

A purpose-scoped, revision-bound candidate mutation. It must contain `autoApply: false`.

## `GraphUpdateDecision`

A fresh human decision owned by Quirk core. `revise` replaces the relevant candidate deltas with explicit corrections.

## `PreferenceGraphUpdateReceipt`

Proof of the actual admitted effect. The local receipt in this pack is only a test adapter; the authoritative writer belongs to Quirk core.
