# Security and Authority Boundary

## Non-negotiable controls

- No medical or dermatological diagnosis.
- No sensitive-attribute inference.
- No silent Preference Graph mutation.
- No outcome inferred from click, purchase, dwell, return visit, silence, or engagement.
- No provider secret in Git, Airtable, browser code, Cloudflare `vars`, logs, fixtures, or proof bundles.
- No OpenAI output may rank candidates, grant authority, issue a receipt, or mutate state.
- No Supabase or Airtable projection may become semantic authority.
- Every consequential transition carries actor, purpose, lineage, time, expiry, and digest evidence.

## Reporting

Report suspected secret exposure, authority bypass, cross-tenant access, receipt tampering, or sensitive inference as a release blocker. Preserve evidence; do not “fix forward” by deleting the only record of what happened.

## Core receipt trust

`receiptWriter`, issuer names, URLs, database rows, and Airtable fields are not proof of core issuance. Real proof requires a detached Ed25519 signature that validates against a trusted Quirk-core public key supplied outside the proof bundle.
