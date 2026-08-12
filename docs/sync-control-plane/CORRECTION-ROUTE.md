# Authorized Correction Route for Append-Only Evidence

## Invariant

All run receipts and manifest transition records are **append-only**.  No
agent, service, administrator, or privileged database role may `UPDATE` or
`DELETE` a row in `quirk_sync.run_receipts` or
`quirk_sync.manifest_transition_ledger`.  Any attempt to do so is rejected by
the `prevent_append_only_mutation` trigger.

## The only authorized correction: a superseding record

When a receipt or transition was written incorrectly, the sole authorized
repair is to insert a **new** record that supersedes the original.

### Superseding a run receipt

```sql
INSERT INTO quirk_sync.run_receipts (
    receipt_key,
    idempotency_key,
    run_type,
    status,
    input_refs,
    output_refs,
    evidence_refs,
    completed_at,
    receipt_hash,
    supersedes_receipt_key,   -- key of the record being corrected
    correction_reason         -- mandatory; must be non-empty
) VALUES ( ... );
```

`correction_reason` is enforced non-null and non-empty by
`quirk_sync.guard_receipt_insert()`.  A superseding receipt without a reason
is rejected at the database layer.

### Superseding a manifest transition

A corrected admission decision is expressed by submitting a new admission
request that results in a new row in `quirk_sync.manifest_transition_ledger`
with the updated evidence and decision references.  The original transition
row remains permanently visible for audit.

## Why no administrative override is permitted

- Silent rewriting hides errors and creates plausible-deniability gaps.
- The `service_role` Postgres role holds only `SELECT` and `INSERT` on
  receipt and ledger tables; `UPDATE`/`DELETE` are never granted (see
  `20260812030002_sync_control_plane_delivery.sql`).
- Row-level security on both tables is enabled; no browser-facing role
  can reach the schema at all.
- These controls are tested in `supabase/tests/sync_control_plane_hardening.sql`
  and regressed in `tests/test_sync_control_plane.py`.

## Reference

- `policies/receipt-immutability-policy.yaml`
- `schemas/sync-run-receipt.schema.json` (`supersedes_receipt_key`,
  `correction_reason` fields)
- `supabase/migrations/20260812030001_sync_control_plane_evidence.sql`
  (`prevent_append_only_mutation`, `guard_receipt_insert`)
