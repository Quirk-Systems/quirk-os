-- Quirk Core Ship It Without Bryan tribunal projection.
-- Git remains canonical. This schema stores a private runtime projection only.

create schema if not exists quirk_control;

revoke all on schema quirk_control from public;
revoke all on schema quirk_control from anon;
revoke all on schema quirk_control from authenticated;
grant usage on schema quirk_control to service_role;

alter default privileges in schema quirk_control revoke all on tables from public;
alter default privileges in schema quirk_control revoke all on tables from anon;
alter default privileges in schema quirk_control revoke all on tables from authenticated;

create table if not exists quirk_control.tribunal_runs (
  id text primary key,
  schema_version text not null,
  source_repository text not null,
  source_pull_request integer not null check (source_pull_request > 0),
  source_commit text not null check (source_commit ~ '^[a-f0-9]{40}$'),
  verdict text not null check (verdict in ('block', 'hold', 'pass')),
  status text not null check (status in ('proposed', 'running', 'completed', 'superseded')),
  report_path text not null,
  evidence_path text not null,
  blocking_move_count integer not null check (blocking_move_count >= 0),
  canonical_state text not null default 'proposed'
    check (canonical_state in ('proposed', 'canonical', 'superseded')),
  payload jsonb not null,
  created_at timestamptz not null,
  completed_at timestamptz
);

create table if not exists quirk_control.proposed_moves (
  id text primary key check (id ~ '^qpm_[A-Za-z0-9_-]+$'),
  schema_version text not null,
  tribunal_id text not null references quirk_control.tribunal_runs(id) on delete restrict,
  source_repository text not null,
  source_pull_request integer not null check (source_pull_request > 0),
  source_commit text not null check (source_commit ~ '^[a-f0-9]{40}$'),
  source_path text not null,
  content_hash text not null check (content_hash ~ '^[a-f0-9]{64}$'),
  lane text not null,
  title text not null,
  dependency_class text not null,
  disposition text not null,
  blocks_merge boolean not null,
  canonical_state text not null default 'proposed'
    check (canonical_state in ('proposed', 'canonical', 'superseded')),
  payload jsonb not null,
  created_at timestamptz not null,
  updated_at timestamptz not null,
  check (payload ->> 'id' = id),
  check (payload ->> 'schema_version' = schema_version),
  check ((payload ->> 'blocks_merge')::boolean = blocks_merge)
);

create index if not exists proposed_moves_pr_blocking_idx
  on quirk_control.proposed_moves
  (source_repository, source_pull_request, blocks_merge, disposition);

create index if not exists proposed_moves_tribunal_idx
  on quirk_control.proposed_moves
  (tribunal_id, lane, dependency_class);

alter table quirk_control.tribunal_runs enable row level security;
alter table quirk_control.proposed_moves enable row level security;

revoke all on quirk_control.tribunal_runs from public, anon, authenticated;
revoke all on quirk_control.proposed_moves from public, anon, authenticated;
grant select, insert, update, delete on quirk_control.tribunal_runs to service_role;
grant select, insert, update, delete on quirk_control.proposed_moves to service_role;

comment on schema quirk_control is
  'Private runtime projection of Git-backed Quirk governance artifacts. Never canonical by itself.';

comment on table quirk_control.tribunal_runs is
  'Ship It Without Bryan tribunal projections with source commit and evidence paths.';

comment on table quirk_control.proposed_moves is
  'Typed Proposed Move projections. Unresolved blocks_merge rows prohibit Golden promotion.';
