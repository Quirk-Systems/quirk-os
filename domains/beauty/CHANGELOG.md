# Changelog

## 0.1.1 — 2026-08-22

### Corrected

- Reclassified the boundary as human-approved pending Git admission instead of falsely claiming repository canonization.
- Replaced an unverifiable eight-file bundle with a reproducible package.
- Added missing source modules, tests, schemas, proof verifier, synthetic runner, CI, provider projection contracts, and integrity manifest.
- Hardened the Supabase projection against cross-session ownership inconsistencies and default privilege exposure.
- Hardened real-proof admission with detached Ed25519 Quirk-core receipt attestations and an external trusted-key registry; core-looking metadata can no longer impersonate issuance.

### Preserved

- Stable domain ID `quirk.products.beauty`.
- Domain boundary semantics.
- Required proof chain.
- Human Gate, candidate-before-canon, and capability-does-not-imply-authority invariants.
