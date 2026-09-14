# ADR-0001 — Taste Engine as the v0.1 Wedge

**Status:** candidate decision  
**Date:** 2026-08-21

## Decision

Use a deterministic, model-optional Taste Engine to prove one complete preference-learning sequence before expanding Quirk Beauty.

## Why

A deterministic kernel makes the evidence chain inspectable. It prevents a language model from quietly becoming the ranking authority, hides less implementation behavior, and gives adversarial tests a stable target.

## Consequences

- Pairwise or forced choice is the first input surface.
- Preference evidence remains candidate and purpose-scoped.
- Recommendations cite exact evidence IDs.
- Real-world outcomes require explicit human reports.
- Graph updates are proposals until a fresh Human Gate decision.
- OpenAI may render explanations later but cannot replace the ranking kernel or authority gate.
- Hugging Face may package evaluation datasets later but is not a runtime dependency.
- Commerce remains outside the wedge.

## Rejected alternatives

### Start with a beauty chatbot

Rejected because conversation quality does not prove preference learning, authority safety, or recommendation improvement.

### Start with image analysis

Rejected because it introduces sensitive inference, retention, confidence, and visual-truth problems before the basic evidence spine exists.

### Start with storefront conversion

Rejected because clicks and purchases can reward aggressive merchandising while teaching the wrong preference model.
