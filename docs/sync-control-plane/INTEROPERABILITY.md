# Quirk-Shaped Architectural Interoperability

Quirk interoperability is not “everything edits everything.” It is stable identity, explicit authority, typed translation, receipt-backed movement, and rebuildable projections.

## One object, several truthful representations

```text
GitHub candidate/canon
  -> validated canonical envelope
  -> Supabase runtime projection
  -> receipt-backed outbox
  -> Drive / Airtable / Notion / Vercel views
  -> observations and human feedback
  -> typed Proposed Move
  -> GitHub candidate change
```

## The five non-negotiable seams

1. **Identity seam:** stable `object_key`, `binding_id`, and `receipt_id` survive vendor IDs.
2. **Authority seam:** capability, credentials, tool access, and successful execution never imply permission.
3. **Translation seam:** canonical and runtime field mappings are named, versioned, and tested both directions.
4. **Evidence seam:** every state-changing run produces an immutable receipt; corrections supersede rather than rewrite.
5. **Projection seam:** Drive, Airtable, Notion, Vercel, and deferred Cloudflare representations can be rebuilt and never outrank Canon.

## Quirk object movement

Every adapter resolves:

```text
actor + purpose + authority grant + manifest version + tool scope + object scope
```

Then it may observe, normalize, validate, persist private runtime state, rebuild projections, and propose. Protected actions remain human-gated.

## Failure posture

- Canon conflict -> block projection and emit Proposed Move.
- Vendor identity collision -> reject binding.
- Consequential uncertain label -> human review.
- Taxonomy gap -> propose a distinction; do not abuse `other`.
- Stale guidance -> mark freshness without rewriting history.
- Trigger collision -> fail closed or route through an admitted policy.
- Capacity overload -> stop pulling work and propose rebalance.
- Rights uncertainty -> block productization.
- Self-promotion -> reject transition and preserve evidence.
