# Human Capability Card Contract

Status: proposed  
Scope: Quirk OS Golden Project Pack  
Classification: generic contract; never a person record

## Purpose

A Human Capability Card is a restricted, purpose-limited routing envelope for matching approved work to stated operational capabilities. It is not an employment record, a credential registry, a performance evaluation, an authorization, or a substitute for verification.

This contract exists to make one boundary explicit: a system may route a request using a reviewed capability signal, but it must not turn private source material into general workspace memory.

## Required controls

- Keep raw sources outside shared repositories and general Command Center context.
- Do not store direct identifiers, contact details, employment or education history, schedules, access credentials, certification numbers, or source text in the card.
- Mark each capability's `evidence_state` distinctly: `self_asserted`, `corroborated`, `verified`, `expired`, or `unknown`.
- Treat `self_asserted` and `corroborated` as claims, not proof of qualification, current employment, system access, or certification.
- Record a restricted `provenance_ref`, not a copied source; pair it with `last_verified_at`.
- Require explicit human authority, defined purpose, access scope, retention, and forgetting path before any L4 rights-sensitive use.
- Emit a receipt for any consequential creation, change, access grant, retention change, or deletion.
- Default to least privilege and deny broad retrieval, model training, or secondary use.

## Minimal envelope

```yaml
human_capability_card:
  card_id: opaque-and-non-identifying
  purpose: approved-routing-purpose
  capability: normalized-capability-label
  evidence_state: self_asserted
  provenance_ref: restricted://owner-controlled-reference
  last_verified_at: null
  sensitivity: restricted
  access_scope: named-need-to-know-role
  retention: explicit-policy
  forgetting: explicit-deletion-path
  review_state: pending-human-review
```

The example is a schema shape only. It is not a person profile and must not be populated with copied private-source content.

## Allowed use

With the owner's approval and within the declared purpose, a card may help route prompts requiring operational grounding in manufacturing, safety, inventory, or coordination.

## Prohibited use

A card must not be used to infer identity, employment status, pay, performance, medical or demographic characteristics, access entitlements, or current credentials. It must not be published, committed with raw sources, or used as the sole basis for a real-world decision.

## Golden Project Pack alignment

This is an L4 rights-sensitive pattern. Apply the Golden Project Pack's Security + Privacy Gate, declared retention and forgetting behavior, named human authority, and receipt requirements before implementation.
