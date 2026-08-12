-- Quirk Sync Control Plane v0.2 bounded delivery and private runtime grants.
-- Atomic bounded outbox delivery.
alter table quirk_sync.projection_outbox
  add column if not exists max_attempts integer not null default 5,
  add column if not exists lease_token uuid,
  add column if not exists lease_owner text,
  add column if not exists compensation_payload jsonb,
  add column if not exists dead_lettered_at timestamptz;
alter table quirk_sync.projection_outbox drop constraint if exists projection_outbox_max_attempts_check;
alter table quirk_sync.projection_outbox add constraint projection_outbox_max_attempts_check check (max_attempts between 1 and 5);
alter table quirk_sync.projection_outbox drop constraint if exists projection_outbox_compensation_object_check;
alter table quirk_sync.projection_outbox add constraint projection_outbox_compensation_object_check
  check (compensation_payload is null or jsonb_typeof(compensation_payload)='object');
create or replace function quirk_sync.claim_projection_outbox(p_worker_id text,p_limit integer default 25,p_lease_seconds integer default 60)
returns setof quirk_sync.projection_outbox language plpgsql set search_path=pg_catalog,quirk_sync as $$
begin return query
  with c as (select id from quirk_sync.projection_outbox where status in ('pending','failed','leased') and available_at<=now()
    and attempts<max_attempts and (leased_until is null or leased_until<now()) order by available_at,id
    for update skip locked limit greatest(1,least(p_limit,100)))
  update quirk_sync.projection_outbox o set status='leased',attempts=o.attempts+1,lease_token=gen_random_uuid(),
    lease_owner=p_worker_id,leased_until=now()+make_interval(secs=>greatest(5,p_lease_seconds))
  from c where o.id=c.id returning o.*; end $$;
create or replace function quirk_sync.complete_projection_delivery(p_outbox_id bigint,p_lease_token uuid)
returns quirk_sync.projection_outbox language plpgsql set search_path=pg_catalog,quirk_sync as $$
declare r quirk_sync.projection_outbox%rowtype;
begin update quirk_sync.projection_outbox set status='succeeded',completed_at=now(),leased_until=null,lease_owner=null,lease_token=null
  where id=p_outbox_id and lease_token=p_lease_token and status='leased' returning * into r;
  if not found then raise exception 'outbox completion rejected'; end if; return r; end $$;
create or replace function quirk_sync.record_projection_failure(p_outbox_id bigint,p_lease_token uuid,p_error jsonb)
returns quirk_sync.projection_outbox language plpgsql set search_path=pg_catalog,quirk_sync as $$
declare r quirk_sync.projection_outbox%rowtype;
begin update quirk_sync.projection_outbox set
    status=case when attempts>=max_attempts then 'dead_letter' else 'failed' end,
    available_at=case when attempts>=max_attempts then available_at else now()+make_interval(secs=>least(3600,(30*power(2,greatest(attempts-1,0)))::integer)) end,
    dead_lettered_at=case when attempts>=max_attempts then now() end,last_error=p_error,
    leased_until=null,lease_owner=null,lease_token=null
  where id=p_outbox_id and lease_token=p_lease_token and status='leased' returning * into r;
  if not found then raise exception 'outbox failure rejected'; end if; return r; end $$;

-- Rebuildable projection envelope.
create or replace function quirk_sync.rebuild_projection_snapshot(p_object_key text) returns jsonb
language sql stable set search_path=pg_catalog,quirk_sync as $$
select jsonb_build_object('schema_version','projection-envelope.v1','object_key',o.object_key,'kind',o.kind,
  'canonical_uri',o.canonical_uri,'canonical_version',o.canonical_version,'content_hash',o.content_hash,
  'authority_class','projection','projection',jsonb_build_object('status',o.status,'metadata',o.metadata),
  'source_bindings',coalesce((select jsonb_agg(jsonb_build_object('binding_id',b.binding_key,'platform',b.platform,
    'external_id',b.external_id,'external_url',b.external_url,'authority_class',b.authority_class,
    'sync_direction',b.sync_direction,'state',b.state,'freshness',b.freshness) order by b.platform,b.binding_key)
    from quirk_sync.source_bindings b where b.object_id=o.id),'[]'::jsonb),
  'generated_at',now(),'generator_ref','function.quirk_sync.rebuild_projection_snapshot')
from quirk_sync.object_registry o where o.object_key=p_object_key $$;
-- Private browser boundary; explicit server-side service role.
alter table quirk_sync.manifest_transition_ledger enable row level security;
alter table quirk_sync.proposed_moves enable row level security;
revoke all on schema quirk_sync from public;
revoke all on schema quirk_sync from anon;
revoke all on schema quirk_sync from authenticated;
revoke all on all tables in schema quirk_sync from public,anon,authenticated;
revoke all on all sequences in schema quirk_sync from public,anon,authenticated;
grant usage on schema quirk_sync to service_role;
grant select,insert,update on quirk_sync.object_registry,quirk_sync.source_bindings,quirk_sync.manifest_registry,
  quirk_sync.sync_cursors,quirk_sync.projection_outbox,quirk_sync.proposed_moves to service_role;
grant select,insert on quirk_sync.run_receipts,quirk_sync.manifest_transition_ledger to service_role;
grant usage,select on all sequences in schema quirk_sync to service_role;
revoke execute on all functions in schema quirk_sync from public,anon,authenticated;
grant execute on function quirk_sync.observe_binding(text,text,text,text),
  quirk_sync.claim_projection_outbox(text,integer,integer),quirk_sync.complete_projection_delivery(bigint,uuid),
  quirk_sync.record_projection_failure(bigint,uuid,jsonb),quirk_sync.rebuild_projection_snapshot(text) to service_role;

comment on function quirk_sync.guard_manifest_activation() is 'Never #0001: capability and tool access cannot self-authorize activation.';
comment on table quirk_sync.manifest_transition_ledger is 'Append-only manifest transition evidence; human admission remains external.';
comment on table quirk_sync.proposed_moves is 'Typed runtime proposals for drift, conflict, review, rights, capacity, and provider boundaries.';
