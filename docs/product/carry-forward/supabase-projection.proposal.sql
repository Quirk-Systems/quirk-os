-- PROPOSAL ONLY. This file is not a migration and has not been executed.
-- Optional private snapshot storage for quirk-career-workspace/0.2.
-- Google Drive remains authoritative. Database presence grants no career authority.
-- Review SUPABASE_CONTRACT.md and prove grants/RLS on an isolated database first.
-- No project identifier, credential, source document identifier, or personal seed data.
-- Deliberately fail if these objects already exist; do not silently reuse old policies.

begin;

create schema career_projection_private;
revoke all on schema career_projection_private from public, anon, authenticated, service_role;
grant usage on schema career_projection_private to authenticated;

-- Pure, bounded structural admission check; not a full career graph validator.
-- The adapter MUST run the pinned engine.restore on upload and on every download.
-- This schema must stay outside Supabase's exposed API schemas.
create function career_projection_private.is_candidate_workspace_02(payload jsonb)
returns boolean
language plpgsql
immutable
security invoker
set search_path = pg_catalog
as $function$
declare
  item jsonb;
begin
  -- IS DISTINCT FROM turns absent values and JSON null into explicit rejection.
  if payload is null or jsonb_typeof(payload) is distinct from 'object' then
    return false;
  end if;
  if (payload ->> 'format') is distinct from 'quirk-career-workspace/0.2'
     or not (payload ?& array['format', 'objects', 'receipts', 'quarantine'])
     or (payload - array['format', 'objects', 'receipts', 'quarantine']) <> '{}'::jsonb
     or jsonb_typeof(payload -> 'objects') is distinct from 'array'
     or jsonb_typeof(payload -> 'receipts') is distinct from 'array'
     or jsonb_typeof(payload -> 'quarantine') is distinct from 'array' then
    return false;
  end if;
  if octet_length(convert_to(payload::text, 'UTF8')) > 10485760
     or jsonb_array_length(payload -> 'objects')
        + jsonb_array_length(payload -> 'receipts')
        + jsonb_array_length(payload -> 'quarantine') > 1000 then
    return false;
  end if;

  for item in select value from jsonb_array_elements(payload -> 'objects') loop
    if jsonb_typeof(item) is distinct from 'object'
       or not (item ?& array['api_version','kind','metadata','authority','provenance','spec','evidence','lifecycle'])
       or (item - array['api_version','kind','metadata','authority','provenance','spec','evidence','lifecycle']) <> '{}'::jsonb
       or (item ->> 'api_version') is distinct from 'quirk.dev/v1alpha1'
       or not coalesce((item ->> 'kind') = any(array['Source','Claim','Asset','Opportunity','Feedback','Learning','UsefulnessTrial']), false)
       or jsonb_typeof(item -> 'metadata') is distinct from 'object'
       or (item #>> '{metadata,status}') is distinct from 'candidate'
       or jsonb_typeof(item -> 'authority') is distinct from 'object'
       or (item -> 'authority') is distinct from
          '{"source_of_truth":"google_drive","current_authority_ref":"authority.local_candidate","maximum_runtime_right":"propose"}'::jsonb
       or jsonb_typeof(item -> 'provenance') is distinct from 'object'
       or jsonb_typeof(item -> 'spec') is distinct from 'object'
       or jsonb_typeof(item -> 'evidence') is distinct from 'object'
       or jsonb_typeof(item -> 'lifecycle') is distinct from 'object' then
      return false;
    end if;
    if (item ->> 'kind') = 'Opportunity'
       and not coalesce((item #>> '{spec,stage}') = any(array['DISCOVERED','QUALIFIED']), false) then
      return false;
    end if;
  end loop;

  for item in select value from jsonb_array_elements(payload -> 'receipts') loop
    if jsonb_typeof(item) is distinct from 'object'
       or (item ->> 'kind') is distinct from 'prepared_bundle'
       or jsonb_typeof(item -> 'packet') is distinct from 'object'
       or (item #>> '{packet,state}') is distinct from 'proposed'
       or (item #> '{packet,permissions}') is distinct from '["propose"]'::jsonb
       or not (item ? 'observed_effect')
       or (item -> 'observed_effect') is distinct from 'null'::jsonb then
      return false;
    end if;
  end loop;

  -- Quarantine intentionally preserves rejected raw data. Its embedded instructions,
  -- status strings, and authority claims remain inert and are never admitted objects.
  -- engine.restore must verify quarantine integrity and deterministic receipts.
  return true;
end;
$function$;

revoke all on function career_projection_private.is_candidate_workspace_02(jsonb)
  from public, anon, authenticated, service_role;
grant execute on function career_projection_private.is_candidate_workspace_02(jsonb)
  to authenticated;

create table public.career_workspace_snapshots (
  owner_id uuid not null default auth.uid()
    references auth.users(id) on delete restrict,
  workspace_id uuid not null,
  version bigint not null,
  parent_version bigint,
  payload jsonb not null,
  payload_sha256 text not null,
  created_at timestamptz not null default now(),

  primary key (owner_id, workspace_id, version),
  constraint career_snapshot_version_chain check (
    (
      (version = 1 and parent_version is null)
      or (version > 1 and parent_version is not null and parent_version = version - 1)
    ) is true
  ),
  constraint career_snapshot_parent foreign key (owner_id, workspace_id, parent_version)
    references public.career_workspace_snapshots(owner_id, workspace_id, version),
  constraint career_snapshot_hash_shape check (
    (payload_sha256 ~ '^[a-f0-9]{64}$') is true
  ),
  constraint career_snapshot_candidate_payload check (
    career_projection_private.is_candidate_workspace_02(payload) is true
  )
);

comment on table public.career_workspace_snapshots is
  'Optional private candidate projections. Append-only for browser clients; Google Drive remains authoritative. Snapshot storage neither verifies facts nor grants application authority.';
comment on column public.career_workspace_snapshots.payload_sha256 is
  'Adapter-supplied canonical SHA-256. SQL checks shape only; adapter must recompute it with the pinned runtime. This is not a signature or encryption.';
comment on column public.career_workspace_snapshots.parent_version is
  'Expected version read by the client. Insert version = parent_version + 1. First snapshot uses version 1 and NULL parent. Concurrent writes conflict on the primary key.';

alter table public.career_workspace_snapshots enable row level security;
alter table public.career_workspace_snapshots force row level security;

-- Explicit privileges matter on projects with either old or new default grants.
-- This changes only the new objects, not global default privileges or existing tables.
revoke all on table public.career_workspace_snapshots
  from public, anon, authenticated, service_role;
grant usage on schema public to authenticated;
grant select on table public.career_workspace_snapshots to authenticated;
grant insert (workspace_id, version, parent_version, payload, payload_sha256)
  on table public.career_workspace_snapshots to authenticated;

-- owner_id and created_at cannot be supplied through authenticated INSERT grants.
-- No UPDATE, DELETE, TRUNCATE, write view, upsert, or privileged RPC is exposed.
create policy career_snapshot_owner_read
  on public.career_workspace_snapshots
  for select to authenticated
  using ((select auth.uid()) = owner_id);

create policy career_snapshot_owner_append
  on public.career_workspace_snapshots
  for insert to authenticated
  with check ((select auth.uid()) = owner_id);

commit;
