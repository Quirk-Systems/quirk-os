# ADR-0002 — Admit the Quirk Beauty domain boundary only

- **Status:** accepted by explicit human instruction; repository merge pending
- **Decision date:** 2026-08-21
- **Decision owner:** Bryan
- **Canonical object:** `quirk.products.beauty`

## Decision

Admit only the Quirk Beauty domain boundary recorded in
`docs/canon/QUIRK-BEAUTY-DOMAIN-BOUNDARY.yaml` and its bound sorted-JSON hash payload. They are two encodings of one admitted semantic boundary.

The boundary owns beauty-specific taste semantics and experiences. It delegates
identity, authority, Human Gate enforcement, receipts, generic Preference Graph
infrastructure, model execution, publishing, transactions, and cross-domain
orchestration to Quirk core systems.

## Explicit non-decision

This decision does not admit the Taste Engine runtime, object registry, scoring
method, product design, Supabase schema, provider adapter, sales offer, or any
broader Quirk Beauty platform proposal.

## Required proof

```text
choice
→ preference evidence
→ recommendation
→ real-world outcome
→ human-confirmed graph update
```

Synthetic execution may validate machinery but cannot satisfy this proof.

## Authority ceiling

Merging the boundary branch records the human decision. It does not activate a
runtime, apply a migration, publish externally, transact, or mutate a Preference
Graph. Bryan retains the keys.
