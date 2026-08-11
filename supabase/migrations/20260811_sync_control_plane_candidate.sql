-- Quirk Sync Control Plane candidate runtime registry.
-- Canon remains in Git. This schema stores private runtime state and receipts only.

create schema if not exists quirk_sync;

revoke all on schema quirk_sync from public;
revoke all on schema quirk_sync from anon;
revoke all on schema quirk_sync from authenticated;

alter default privileges in schema quirk_sync revoke all on tables from public;
alter default privileges in schema quirk_sync revoke all on tables from anon;
alter default privileges in schema quirk_sync revoke all on tables from authenticated;
alter default privileges in schema quirk_sync revoke all on sequences from public;
alter default privileges in schema quirk_sync revoke all on sequences from anon;
alter default privileges in schema quirk_sync revoke all on sequences from authenticated;
alter default privileges in schema quirk_sync revoke execute on functions from public;
alter default privileges in schema quirk_sync revoke execute on functions from anon;
alter default privileges in schema quirk_sync revoke execute on functions from authenticated;

create table if not exists quirk_sync.object_registry (
  id uuid primary key default gen_random_uuid(),
  object_key text not null unique,
  kind text not null,
  canonical_uri text,
  canonical_version text,
  status text not null default 'candidate'
    check (status in ('discovered','candidate','active','paused','superseded','retired')),
  content_hash text
    check (content_hash is null or content_hash ~ '^[a-f0-9]{64}$'),
  metadata jsonb not null default '{}'::jsonb
    check (jsonb_typeof(metadata) = 'object'),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists quirk_sync.source_bindings (
  id uuid primary key default gen_random_uuid(),
  object_id uuid not null references quirk_sync.object_registry(id) on delete restrict,
  platform text not null
    check (platform in ('github','supabase','google_drive','airtable','notion','vercel')),
  external_id text not null,
  external_url text,
  authority_class text not null
    check (authority_class in ('canonical','runtime','work','projection')),
  sync_direction text not null
    check (sync_direction in ('pull','push','bidirectional_proposal','projection_only','none')),
  state text not null default 'discovered'
    check (state in ('discovered','candidate','active','drifted','paused','error','retired')),
  last_seen_hash text
    check (last_seen_hash is null or last_seen_hash ~ '^[a-f0-9]{64}$'),
  last_synced_hash text
    check (last_synced_hash is null or last_synced_hash ~ '^[a-f0-9]{64}$'),
  cursor jsonb not null default '{}'::jsonb
    check (jsonb_typeof(cursor) = 'object'),
  metadata jsonb not null default '{}'::jsonb
    check (jsonb_typeof(metadata) = 'object'),
  last_seen_at timestamptz,
  last_synced_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (platform, external_id),
  unique (object_id, platform, external_id)
);

create table if not exists quirk_sync.manifest_registry (
  id uuid primary key default gen_random_uuid(),
  manifest_key text not null,
  manifest_kind text not null
    check (manifest_kind in ('agent','skill','capability','orchestrator')),
  version text not null,
  status text not null default 'candidate'
    check (status in ('candidate','active','paused','superseded','revoked')),
  canonical_uri text not null,
  content_hash text not null
    check (content_hash ~ '^[a-f0-9]{64}$'),
  authority_ceiling text not null
    check (authority_ceiling in ('observe','infer','propose','execute_reversible','enforce_invariant','execute_protected')),
  tools jsonb not null default '[]'::jsonb
    check (jsonb_typeof(tools) = 'array'),
  inputs_schema_ref text not null,
  outputs_schema_ref text not null,
  eval_refs jsonb not null default '[]'::jsonb
    check (jsonb_typeof(eval_refs) = 'array'),
  stop_conditions jsonb not null default '[]'::jsonb
    check (jsonb_typeof(stop_conditions) = 'array'),
  metadata jsonb not null default '{}'::jsonb
    check (jsonb_typeof(metadata) = 'object'),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (manifest_key, version)
);

create table if not exists quirk_sync.sync_cursors (
  id uuid primary key default gen_random_uuid(),
  binding_id uuid not null references quirk_sync.source_bindings(id) on delete cascade,
  cursor_key text not null,
  cursor_value jsonb not null,
  observed_at timestamptz not null default now(),
  unique (binding_id, cursor_key)
);

create table if not exists quirk_sync.run_receipts (
  id uuid primary key default gen_random_uuid(),
  receipt_key text not null unique,
  idempotency_key text not null unique,
  run_type text not null
    check (run_type in ('discover','pull','push','reconcile','project','validate','backfill','rebuild')),
  status text not null
    check (status in ('planned','running','succeeded','failed','blocked','cancelled')),
  actor_ref text,
  authority_ref text,
  agent_ref text,
  skill_ref text,
  manifest_version text,
  trace_id text,
  proposed_move_ref text,
  input_refs jsonb not null default '[]'::jsonb
    check (jsonb_typeof(input_refs) = 'array'),
  output_refs jsonb not null default '[]'::jsonb
    check (jsonb_typeof(output_refs) = 'array'),
  evidence_refs jsonb not null default '[]'::jsonb
    check (jsonb_typeof(evidence_refs) = 'array'),
  metrics jsonb not null default '{}'::jsonb
    check (jsonb_typeof(metrics) = 'object'),
  error jsonb,
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  check ((status not in ('succeeded','failed','blocked','cancelled')) or completed_at is not null),
  check ((status <> 'failed') or error is not null)
);

create table if not exists quirk_sync.projection_outbox (
  id bigint generated by default as identity primary key,
  object_id uuid not null references quirk_sync.object_registry(id) on delete restrict,
  destination_platform text not null
    check (destination_platform in ('google_drive','airtable','notion','vercel')),
  operation text not null
    check (operation in ('create','update','retire','rebuild')),
  payload jsonb not null
    check (jsonb_typeof(payload) = 'object'),
  payload_hash text not null
    check (payload_hash ~ '^[a-f0-9]{64}$'),
  idempotency_key text not null unique,
  authority_ref text not null,
  status text not null default 'pending'
    check (status in ('pending','leased','succeeded','failed','dead_letter','cancelled')),
  attempts integer not null default 0
    check (attempts >= 0 and attempts <= 5),
  available_at timestamptz not null default now(),
  leased_until timestamptz,
  completed_at timestamptz,
  last_error jsonb,
  created_at timestamptz not null default now()
);

create index if not exists source_bindings_object_id_idx
  on quirk_sync.source_bindings(object_id);

create index if not exists source_bindings_drift_idx
  on quirk_sync.source_bindings(state)
  where state = 'drifted';

create index if not exists manifest_registry_active_idx
  on quirk_sync.manifest_registry(manifest_key, version)
  where status = 'active';

create index if not exists run_receipts_trace_idx
  on quirk_sync.run_receipts(trace_id)
  where trace_id is not null;

create index if not exists projection_outbox_ready_idx
  on quirk_sync.projection_outbox(status, available_at)
  where status in ('pending','failed');

alter table quirk_sync.object_registry enable row level security;
alter table quirk_sync.source_bindings enable row level security;
alter table quirk_sync.manifest_registry enable row level security;
alter table quirk_sync.sync_cursors enable row level security;
alter table quirk_sync.run_receipts enable row level security;
alter table quirk_sync.projection_outbox enable row level security;

revoke all on all tables in schema quirk_sync from public;
revoke all on all tables in schema quirk_sync from anon;
revoke all on all tables in schema quirk_sync from authenticated;
revoke all on all sequences in schema quirk_sync from public;
revoke all on all sequences in schema quirk_sync from anon;
revoke all on all sequences in schema quirk_sync from authenticated;

comment on schema quirk_sync is
  'Private runtime state for receipt-backed cross-platform Quirk synchronization. Not canonical and not exposed to browser roles.';

comment on table quirk_sync.manifest_registry is
  'Versioned runtime projection of admitted or candidate agent, skill, capability, and orchestrator manifests. Capability does not imply authority.';

comment on table quirk_sync.projection_outbox is
  'Bounded delivery queue for rebuildable human-facing projections. Canon writes are prohibited.';
