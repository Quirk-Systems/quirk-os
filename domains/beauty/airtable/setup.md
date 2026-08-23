# Airtable Operational Projection — Candidate

Airtable is a pilot-operations surface, not storage authority, canon, Human Gate, or backup.

## Table

`Beauty Taste Proofs`, keyed by `recordKey`.

Only `operatorNote` is human-editable in Airtable. All other fields are regenerated from the proof bundle or core receipt. A webhook arriving later cannot override a field owned by Git, explicit human evidence, or Quirk core.

## Required setup evidence

1. Record the connected base and table IDs outside Git secrets.
2. Create fields exactly from `field-authority.json`.
3. Deny automations that write `decision`, `coreReceiptRef`, `outcome`, or `state` directly.
4. Upsert one synthetic projection.
5. Attempt edits to every protected field and confirm rejection or overwrite by the projection writer.
6. Delete the projection and prove the Git artifact and core receipt remain intact.

No connected Airtable mutation is authorized by this document alone.
