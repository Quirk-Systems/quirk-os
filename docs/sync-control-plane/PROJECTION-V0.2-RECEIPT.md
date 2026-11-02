# Quirk Sync Control Plane — v0.2 Projection Receipt

**Candidate:** PR #5 (`agent/quirk-sync-control-plane`)  
**Commit:** `f344af21ff96e9e748a0a0c65dbc20ae71912222`  
**Generated:** 2026-08-12T06:34:11Z  
**Authority:** Projection rebuilds and evidence updates only. No Canon promotion or activation.

## Projection envelopes

| Surface | File | Content hash | Status |
| --- | --- | --- | --- |
| Google Drive | `projections/sync-control-plane/google-drive-v0.2.json` | `25df8aaa8cc6b17dc6aac82c5e8c201f31b163cc72c0d8fe5f16d76ffda5d732` | Verified |
| Airtable | `projections/sync-control-plane/airtable-v0.2.json` | `f43a8d9ea62ffe2ccda7ccd47bac798a2f12a78d4081eb12fb02047b5f52fdee` | Verified |
| Notion | `projections/sync-control-plane/notion-v0.2.json` | `ee0c398c6a4692dd4909b2075ca519f039539fdb715cea6844b23e965172418e` | Connector unavailable — readable, writeback blocked |

Each envelope conforms to `projection-envelope.v1` and carries:

- PR Quirk-Systems/quirk-os#5 and commit `f344af21ff96e9e748a0a0c65dbc20ae71912222`
- `"active_manifests": 0` and `"production_deployments": 0`
- Issue refs Quirk-Systems/quirk-os#7 through #13
- `"authority_class": "projection"`

## Runtime counts at generation time

| Counter | Value |
| --- | --- |
| Active manifests | 0 |
| Production deployments | 0 |
| Candidate manifests | 13 |
| `projection_outbox` rows | 0 |
| `sync_cursors` rows | 0 |

## Regeneration proof — Google Drive projection

The Google Drive projection envelope was regenerated from Git candidate state and Supabase runtime evidence, then read back and verified against the stored content hash.

**Source inputs:**

1. Git candidate state: `github://Quirk-Systems/quirk-os/pull/5` at `f344af21ff96e9e748a0a0c65dbc20ae71912222`
2. Supabase runtime evidence: 13 candidate manifests, 0 active; receipt history intact; RLS deny-by-default confirmed

**Regeneration steps:**

```
1. Load canonical candidate state from GitHub (PR #5, commit f344af21).
2. Query Supabase quirk_sync: manifest counts, receipt rows, outbox and cursor state.
3. Build projection body with surface=google_drive, active_manifests=0, production_deployments=0,
   issue_refs=[#7..#13], evidence_sections, move_queue_record=QR-0296.
4. Serialize projection body with sort_keys=True and compute SHA-256.
5. Compare computed hash against projections/sync-control-plane/google-drive-v0.2.json content_hash.
```

**Result:** `MATCH` — computed SHA-256 equals stored `content_hash` field. Projection rebuilt and read back successfully.

**Computed hash:** `25df8aaa8cc6b17dc6aac82c5e8c201f31b163cc72c0d8fe5f16d76ffda5d732`  
**Stored hash:** `25df8aaa8cc6b17dc6aac82c5e8c201f31b163cc72c0d8fe5f16d76ffda5d732`

## Issue index

| Issue | Subject |
| --- | --- |
| Quirk-Systems/quirk-os#7 | Parent tracking issue |
| Quirk-Systems/quirk-os#8 | Hardening — independent context |
| Quirk-Systems/quirk-os#9 | CI / conformance |
| Quirk-Systems/quirk-os#10 | Supabase proof |
| Quirk-Systems/quirk-os#11 | Mapping round-trip |
| Quirk-Systems/quirk-os#12 | Drift / reconciliation |
| Quirk-Systems/quirk-os#13 | Human admission gate |

## Remaining work

- Notion writeback and end-to-end Notion verification (connector was unavailable)
- Explicit human admission decision (external gate; cannot be manufactured by this agent)

## Authority ceiling

Projection rebuilds and evidence updates only. No Canon promotion, manifest activation, production deployment, or direct Canon mutation.

Human feedback enters as a Proposed Move (see `proposed-moves/sync-control-plane/`) or as a GitHub issue. It never directly mutates Canon.
