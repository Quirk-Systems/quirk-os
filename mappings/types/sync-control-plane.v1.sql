-- Quirk Sync Control Plane — runtime projection type annotations
-- Mapping version: sync-control-plane.v1.1.0
-- Source: mappings/sync-control-plane.v1.yaml
--
-- These composite types mirror the runtime Supabase columns and document the
-- canonical ↔ runtime mapping contract.  They are not applied as live
-- database types; they serve as the single authoritative reference for
-- generating or auditing runtime projections in downstream adapters.
--
-- Vendor IDs are bindings.  They are never Quirk identity.

-- ---------------------------------------------------------------------------
-- source_bindings runtime projection
-- canonical field       runtime column
-- binding_id        →   binding_key        (stable Quirk id, not a UUID)
-- object_key        ←   object_registry.object_key via object_id join
-- source_bindings.id   omitted_runtime_identity  (private UUID, never Canon)
-- source_bindings.object_id  resolved via object_registry to object_key
-- ---------------------------------------------------------------------------

create type quirk_source_binding_canonical as (
  schema_version    text,       -- "source-binding.v2"
  binding_id        text,       -- pattern: binding.<platform>.<slug>
  object_key        text,       -- stable Quirk key, never a UUID
  platform          text,
  external_id       text,       -- vendor id stored as binding, not Quirk identity
  external_url      text,
  authority_class   text,
  sync_direction    text,
  state             text,
  canonical_uri     text,
  content_hash      text,       -- sha-256 hex
  last_seen_at      timestamptz,
  last_synced_at    timestamptz,
  freshness         jsonb,
  cursor            jsonb,
  metadata          jsonb
);

-- ---------------------------------------------------------------------------
-- run_receipts runtime projection
-- canonical field           runtime column
-- receipt_id            →   receipt_key        (stable Quirk id, not a UUID)
-- supersedes_receipt_id →   supersedes_receipt_key
-- run_receipts.id           omitted_runtime_identity  (private UUID, never Canon)
-- ---------------------------------------------------------------------------

create type quirk_run_receipt_canonical as (
  schema_version          text,       -- "sync-run-receipt.v2"
  receipt_id              text,       -- pattern: receipt.<slug>
  idempotency_key         text,
  run_type                text,
  status                  text,
  immutable               boolean,    -- always true
  actor_ref               text,
  authority_ref           text,
  agent_ref               text,
  skill_ref               text,
  manifest_version        text,
  trace_id                text,
  started_at              timestamptz,
  completed_at            timestamptz,
  input_refs              text[],
  output_refs             text[],
  evidence_refs           text[],
  metrics                 jsonb,
  error                   jsonb,
  proposed_move_ref       text,
  content_hashes          jsonb,
  receipt_hash            text,       -- sha-256 hex
  supersedes_receipt_id   text,       -- pattern: receipt.<slug>
  correction_reason       text,
  outcome                 jsonb
);

-- ---------------------------------------------------------------------------
-- projection_envelopes runtime projection
-- The envelope carries only canonical-side fields; no runtime UUIDs allowed.
-- ---------------------------------------------------------------------------

create type quirk_projection_envelope_canonical as (
  schema_version      text,       -- "projection-envelope.v1"
  object_key          text,       -- stable Quirk key, never a UUID
  kind                text,
  canonical_uri       text,
  canonical_version   text,
  content_hash        text,       -- sha-256 hex
  authority_class     text,       -- always "projection"
  projection          jsonb,
  source_bindings     jsonb,      -- array of quirk_source_binding_canonical
  generated_at        timestamptz,
  generator_ref       text
);
