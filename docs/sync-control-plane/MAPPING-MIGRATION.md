# Mapping Migration Guide

**Mapping package:** `mappings/sync-control-plane.v1.yaml`  
**Current version:** 1.1.0  
**Applies to:** Quirk Sync Control Plane and all downstream Quirk repositories

---

## Background

Quirk v0.1 exposed identifier drift between canonical JSON and Supabase
runtime projections.  Three field-name assumptions caused silent data loss:

| v0.1 runtime column | v0.2+ runtime column | Canonical field |
| --- | --- | --- |
| `binding_id` (plain UUID) | `binding_key` | `binding_id` |
| `receipt_id` (plain UUID) | `receipt_key` | `receipt_id` |
| `source_bindings.object_id` (UUID FK) | resolved via `object_registry` join | `object_key` |

The v1.1.0 mapping names every lossy field and prohibits silent loss.

---

## Migration steps

### 1 — `binding_id` → `binding_key`

Rows created before v0.2 may carry a plain Supabase serial/UUID in the
`binding_id` column instead of a stable Quirk binding identifier.

```sql
-- Identify un-migrated rows (binding_id looks like a UUID, not binding.<slug>)
SELECT id, binding_id, binding_key
FROM source_bindings
WHERE binding_id ~ '^[0-9a-f-]{36}$'   -- UUID pattern
  AND binding_key IS NULL;

-- Derive binding_key from platform + external_id where possible, then set:
UPDATE source_bindings
SET binding_key = 'binding.' || platform || '.' || external_id
WHERE binding_id ~ '^[0-9a-f-]{36}$'
  AND binding_key IS NULL;
```

After migration, all canonical documents must reference `binding_id` using the
`binding.<platform>.<slug>` pattern.  The legacy UUID column is retired.

### 2 — `receipt_id` → `receipt_key`

Same pattern as bindings.  Receipt rows created before v0.2 may carry a plain
UUID in `receipt_id`.

```sql
-- Identify un-migrated rows
SELECT id, receipt_id, receipt_key
FROM run_receipts
WHERE receipt_id ~ '^[0-9a-f-]{36}$'
  AND receipt_key IS NULL;

-- Derive a stable receipt_key from idempotency_key
UPDATE run_receipts
SET receipt_key = 'receipt.' || replace(idempotency_key, ':', '.')
WHERE receipt_id ~ '^[0-9a-f-]{36}$'
  AND receipt_key IS NULL;
```

After migration, all canonical documents must reference `receipt_id` using the
`receipt.<slug>` pattern.  The legacy UUID column is retired.

### 3 — `object_id` UUID assumptions

The `source_bindings.object_id` column is a foreign-key UUID into
`object_registry`.  It must never appear in a canonical document.  Always
resolve through the join:

```sql
SELECT sb.*, obj.object_key
FROM source_bindings sb
JOIN object_registry obj ON obj.id = sb.object_id;
```

No adapter or projection generator may write a raw `object_id` UUID into a
canonical envelope or a `source-binding.v2` document.

---

## Downstream repository pinning

Every downstream Quirk repository that consumes this mapping must pin to a
specific tagged version.  Add a `mapping_pin` entry to the repository's
runtime manifest or a top-level `MAPPINGS.lock` file:

```yaml
# MAPPINGS.lock
quirk-os/mappings/sync-control-plane:
  version: "1.1.0"
  ref: "<git tag or commit SHA>"
```

Bumping the mapping version requires a separate commit from any vendor adapter
change.  See `mappings/sync-control-plane.v1.yaml` → `versioning`.

---

## Reverse sync: Proposed Moves, not Canon mutation

When the runtime observation layer (drift detection, vendor webhook, feedback
loop) identifies a change that would affect a canonical document, the sync
plane must:

1. Emit a typed **Proposed Move** (`schemas/proposed-move.schema.json`).
2. Record an immutable receipt for the observation run.
3. Route the Proposed Move to human review.
4. Block any direct write to Canon until the Proposed Move is admitted.

The mapping YAML key `reverse_sync.direct_canon_mutation: prohibited` encodes
this rule.  No adapter may bypass it.

---

## Quirk standard reminder

> **Vendor IDs are bindings.  They are never Quirk identity.**

A GitHub repository ID, Supabase row UUID, Drive file ID, or Airtable record
ID is always stored in `source_bindings.external_id`.  It becomes a binding
(`binding_id`), not an `object_key`.
