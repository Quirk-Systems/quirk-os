# Verification Report — Quirk Beauty Domain Pack v0.1.1

**Latest local rerun:** 2026-08-23  
**Local runtime:** Node `v22.16.0`, npm `10.9.2`  
**Target CI:** Node 22 and Node 24

## Repaired evidence surface

The predecessor `v0.1` mounted artifact contained eight files and referenced absent modules, scripts, tests, schemas, workflows, and provider packages. Its reported 13-test and 87-file verification was not reproducible from those bytes.

`v0.1.1` is a successor patch, not a retroactive rewrite.

## Local result

```text
npm run ci
PACK VALID
41 tests passed
0 tests failed
SYNTHETIC MACHINERY VALID
REAL ADMISSION DENIED:
  proof.synthetic
  proof.consent
  proof.core_attestation_missing
MANIFEST VALID: controlled Beauty paths only
```

## Boundary

```text
sha256:6457fcfddde804791729d82837d3ed9d71aa1e30b15e1055a487c0db6907b8d8
```

The boundary is human-approved for canonical admission but does not claim Git merge admission.

## Outstanding evidence

- Node 24 execution in target-repository CI;
- exact GitHub branch, commit, tree, PR, and check receipts;
- Supabase isolated migration/RLS/advisor output;
- Airtable protected-field mutation attempts;
- Cloudflare local Wrangler validation and any separately authorized deployment receipt;
- OpenAI live structured-output eval;
- real-world proof with consent, a Quirk-core-applied graph update, and an Ed25519 receipt attestation verified against the external Git-canonical trust registry.

## Repository integration correction

The manifest generator and validator are scoped to `domains/beauty/`, the single Beauty boundary, and the three Beauty-specific GitHub files. Unrelated `quirk-os` files neither enter the manifest nor satisfy the Beauty proof.
