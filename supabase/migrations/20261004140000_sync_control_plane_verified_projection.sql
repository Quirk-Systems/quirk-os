-- ADR-0002/0003: PostgreSQL is a projection of an admitted Python verifier.
-- NOT independent GitHub attestation or Python JSON hash verification.
-- No credentials, membership grants, activation, or legacy consent are created.
-- The runner owns the transaction; this lock makes audit/cutover atomic.
lock table quirk_sync.manifest_registry in exclusive mode;

do $$
begin
  if exists (select 1 from quirk_sync.manifest_registry where status='active') then
    raise exception 'verified projection cutover blocked: legacy active manifests need human disposition; no historical attestation is inferred';
  end if;
  if not exists (select 1 from pg_roles where rolname='quirk_manifest_verifier') then
    create role quirk_manifest_verifier nologin noinherit nobypassrls;
  end if;
  if exists (select 1 from pg_roles where rolname='quirk_manifest_verifier'
             and (rolcanlogin or rolsuper or rolcreaterole or rolcreatedb or rolbypassrls or rolinherit)) then
    raise exception 'verifier role has unsupported privileges; cutover refused';
  end if;
  if pg_has_role('service_role','quirk_manifest_verifier','MEMBER')
     or pg_has_role('anon','quirk_manifest_verifier','MEMBER')
     or pg_has_role('authenticated','quirk_manifest_verifier','MEMBER') then
    raise exception 'runtime/browser role can assume the verifier role; cutover refused';
  end if;
  if exists (select 1 from pg_auth_members
             where roleid=(select oid from pg_roles where rolname='quirk_manifest_verifier')) then
    raise exception 'verifier membership must be separately admitted after cutover';
  end if;
end $$;

create table quirk_sync.manifest_projection_receipts (
  authority_grant_ref text primary key,
  runtime_payload jsonb not null check (jsonb_typeof(runtime_payload)='object'),
  verified_projection jsonb not null check (jsonb_typeof(verified_projection)='object'),
  expected_from_status text not null check (expected_from_status in ('candidate','paused','active')),
  expires_at timestamptz not null,
  verified_at timestamptz not null,
  recorded_at timestamptz not null default clock_timestamp(),
  check (expires_at > verified_at)
);
alter table quirk_sync.manifest_projection_receipts enable row level security;
revoke all on quirk_sync.manifest_projection_receipts from public,anon,authenticated,service_role;
grant usage on schema quirk_sync to quirk_manifest_verifier;
grant select,insert on quirk_sync.manifest_projection_receipts to quirk_manifest_verifier;
create policy manifest_projection_receipts_verifier on quirk_sync.manifest_projection_receipts
  for all to quirk_manifest_verifier using (true) with check (true);
create trigger manifest_projection_receipts_append_only before update or delete
  on quirk_sync.manifest_projection_receipts for each row
  execute function quirk_sync.prevent_append_only_mutation();

-- Broad service_role credentials must not activate, replace, pause or forge
-- active content. Do not rely on RLS for Supabase's BYPASSRLS service role.
revoke insert,update,delete on quirk_sync.manifest_registry from public,anon,authenticated,service_role;
grant select,insert,update on quirk_sync.manifest_registry to quirk_manifest_verifier;
create policy manifest_registry_verifier on quirk_sync.manifest_registry
  for all to quirk_manifest_verifier using (true) with check (true);

create or replace function quirk_sync.manifest_projection_snapshot(m quirk_sync.manifest_registry)
returns jsonb language sql immutable
set search_path=pg_catalog,quirk_sync,pg_temp as $$
  select to_jsonb(m) - 'id' - 'created_at' - 'updated_at'
$$;

-- A second guard preserves the original structural predicate and its audit.
-- It binds every persisted field to the trusted verifier's exact write payload.
create or replace function quirk_sync.guard_verified_manifest_projection() returns trigger
language plpgsql security definer set search_path=pg_catalog,quirk_sync,pg_temp as $$
declare r quirk_sync.manifest_projection_receipts%rowtype;
begin
  -- Stopping reduces authority. It stays available after an approval expires,
  -- cannot change content or consent, and records a distinct stop observation.
  -- Only the protected verifier lane (or a database administrator) can UPDATE.
  if tg_op='UPDATE' and old.status='active' and new.status in ('paused','revoked') then
    if new.requested_status is distinct from new.status
       or (quirk_sync.manifest_projection_snapshot(new) - 'status' - 'requested_status')
          is distinct from (quirk_sync.manifest_projection_snapshot(old) - 'status' - 'requested_status') then
      raise exception 'stopping may not alter manifest content or approval';
    end if;
    return new;
  end if;
  if new.status='active' or (tg_op='UPDATE' and old.status='active') then
    select * into r from quirk_sync.manifest_projection_receipts
      where authority_grant_ref=new.authority_grant_ref;
    if not found then raise exception 'active state requires a verifier projection receipt'; end if;
    if r.expires_at <= clock_timestamp() or r.verified_at > clock_timestamp()
       or r.verified_at < clock_timestamp() - interval '60 seconds' then
      raise exception 'verifier projection observation is expired or stale';
    end if;
    if r.runtime_payload is distinct from quirk_sync.manifest_projection_snapshot(new) then
      raise exception 'persisted manifest differs from verified projection payload';
    end if;
    if tg_op='UPDATE' and r.expected_from_status is distinct from old.status then
      raise exception 'manifest prior state changed since verification';
    end if;
    if tg_op='INSERT' and r.expected_from_status <> 'candidate' then
      raise exception 'new manifest requires candidate prior state';
    end if;
  end if;
  return new;
end $$;
create trigger manifest_verified_projection_guard before insert or update
  on quirk_sync.manifest_registry for each row
  execute function quirk_sync.guard_verified_manifest_projection();

-- Preserve the existing history triggers, with one record for each crossing.
-- An activation consumes the protected projection receipt. Non-active states
-- are observations, never new human approval. Historical rows are untouched.
create or replace function quirk_sync.record_manifest_transition() returns trigger
language plpgsql set search_path=pg_catalog,quirk_sync,pg_temp as $$
declare r quirk_sync.manifest_projection_receipts%rowtype;
begin
  if new.status='active' then
    select * into strict r from quirk_sync.manifest_projection_receipts
      where authority_grant_ref=new.authority_grant_ref;
    insert into quirk_sync.manifest_transition_ledger
      (transition_key,manifest_id,manifest_key,manifest_version,from_status,to_status,
       requested_by,approved_by,decision_ref,authority_grant_ref,evaluated_content_hash,evidence_refs,occurred_at)
      values (new.transition_evidence_ref,new.id,new.manifest_key,new.version,
              case when tg_op='UPDATE' then old.status else r.expected_from_status end,'active',
              new.requested_by,new.approved_by,new.admission_decision_ref,new.authority_grant_ref,
              new.evaluated_content_hash,r.verified_projection->'manifest'->'admission'->'evidence_refs',
              new.admitted_at);
  else
    insert into quirk_sync.manifest_transition_ledger
      (transition_key,manifest_id,manifest_key,manifest_version,from_status,to_status,
       requested_by,approved_by,decision_ref,authority_grant_ref,evaluated_content_hash,evidence_refs)
      values ('transition.projection.observation.'||gen_random_uuid()::text,new.id,new.manifest_key,new.version,
              case when tg_op='UPDATE' then old.status end,new.status,
              'service.quirk-manifest-verifier',null,'projection-state-observation',new.authority_grant_ref,
              new.content_hash,jsonb_build_array('session:'||session_user));
  end if;
  return new;
end $$;
drop trigger manifest_transition_update on quirk_sync.manifest_registry;
create trigger manifest_transition_update after update on quirk_sync.manifest_registry
  for each row when (old.status is distinct from new.status
                    or old.authority_grant_ref is distinct from new.authority_grant_ref)
  execute function quirk_sync.record_manifest_transition();
revoke all on function quirk_sync.record_manifest_transition() from public,anon,authenticated,service_role;
grant execute on function quirk_sync.record_manifest_transition() to quirk_manifest_verifier;

-- The authenticated host must re-resolve GitHub immediately before invoking
-- this function. Only its separately provisioned login may SET ROLE to this
-- lane. JSON arguments cannot confer that role; this function is NOT DEFINER.
create or replace function quirk_sync.apply_verified_manifest_projection(p jsonb) returns uuid
language plpgsql set search_path=pg_catalog,quirk_sync,pg_temp as $$
declare
  m jsonb := p->'manifest';
  a jsonb := p->'approval';
  candidate quirk_sync.manifest_registry%rowtype;
  existing quirk_sync.manifest_registry%rowtype;
  prior quirk_sync.manifest_projection_receipts%rowtype;
  grant_ref text := a->>'authority_grant_ref';
begin
  if current_user <> 'quirk_manifest_verifier' then
    raise exception 'verifier role required' using errcode='42501';
  end if;
  if p->>'schema_version' is distinct from 'verified-manifest-projection.v1'
     or p->>'database_verification' is distinct from 'projection'
     or p->>'authority_effect' is distinct from 'none'
     or a->>'schema_version' is distinct from 'verified-manifest-approval.v1'
     or a->>'database_verification' is distinct from 'projection'
     or a->>'authority_effect' is distinct from 'none'
     or a->'subject'->>'hash_profile' is distinct from 'runtime-manifest-content.v1'
     or m->>'schema_version' is distinct from 'runtime-manifest.v2'
     or m->>'status' is distinct from 'active'
     or nullif(grant_ref,'') is null
     or a->>'verified_at' is null or a->'subject'->>'expires_at' is null then
    raise exception 'unsupported verified projection envelope';
  end if;
  if (a->>'verified_at')::timestamptz > clock_timestamp()
     or (a->>'verified_at')::timestamptz < clock_timestamp() - interval '60 seconds'
     or (a->'subject'->>'expires_at')::timestamptz <= clock_timestamp() then
    raise exception 'verifier projection observation is expired or stale';
  end if;
  -- Serializes admissions for this identity including the first insertion,
  -- where SELECT FOR UPDATE alone has no row to lock.
  perform pg_advisory_xact_lock(hashtextextended((m->>'manifest_key')||'@'||(m->>'version'),0));
  select * into existing from quirk_sync.manifest_registry
    where manifest_key=m->>'manifest_key' and version=m->>'version' for update;

  candidate := jsonb_populate_record(null::quirk_sync.manifest_registry,
    m - 'schema_version' - 'admission' || jsonb_build_object(
      'requested_by',m->'admission'->>'requested_by',
      'approved_by',m->'admission'->>'approved_by',
      'admission_decision_ref',m->'admission'->>'decision_ref',
      'authority_grant_ref',m->'admission'->>'authority_grant_ref',
      'evaluated_content_hash',m->'admission'->>'evaluated_content_hash',
      'transition_evidence_ref',m->'admission'->>'transition_ref',
      'admitted_at',m->'admission'->>'decided_at',
      'tools',coalesce(m->'tools','[]'::jsonb),
      'eval_refs',coalesce(m->'eval_refs','[]'::jsonb),
      'skill_refs',coalesce(m->'skill_refs','[]'::jsonb),
      'stop_conditions',coalesce(m->'stop_conditions','[]'::jsonb)));
  candidate.id := coalesce(existing.id,gen_random_uuid());
  candidate.created_at := coalesce(existing.created_at,clock_timestamp());
  candidate.updated_at := clock_timestamp();
  if candidate.authority_grant_ref is distinct from grant_ref
     or candidate.content_hash is distinct from a->'subject'->>'content_hash'
     or candidate.approved_by is distinct from a->>'approved_by' then
    raise exception 'projection subject mismatch';
  end if;
  select * into prior from quirk_sync.manifest_projection_receipts where authority_grant_ref=grant_ref;
  if found then
    if prior.runtime_payload is not distinct from quirk_sync.manifest_projection_snapshot(candidate)
       and prior.runtime_payload is not distinct from quirk_sync.manifest_projection_snapshot(existing) then
      return existing.id; -- exact repeat: zero additional writes or ledger effects
    end if;
    raise exception 'projection grant cannot be replayed for changed content';
  end if;
  if coalesce(existing.status,'candidate') is distinct from p->>'expected_from_status'
     or p->>'expected_from_status' is distinct from a->'subject'->>'from_status' then
    raise exception 'manifest prior state changed since verification';
  end if;
  insert into quirk_sync.manifest_projection_receipts
    (authority_grant_ref,runtime_payload,verified_projection,expected_from_status,expires_at,verified_at)
    values (grant_ref,quirk_sync.manifest_projection_snapshot(candidate),p,p->>'expected_from_status',
            (a->'subject'->>'expires_at')::timestamptz,(a->>'verified_at')::timestamptz);
  if existing.id is null then
    insert into quirk_sync.manifest_registry select (candidate).*;
  else
    update quirk_sync.manifest_registry set
      (manifest_kind,status,requested_status,canonical_uri,content_hash,authority_ceiling,
       tools,inputs_schema_ref,outputs_schema_ref,eval_refs,stop_conditions,metadata,
       admission_decision_ref,authority_grant_ref,requested_by,approved_by,evaluated_content_hash,
       transition_evidence_ref,admitted_at,domains,skill_refs,rights_review,trigger_contract,updated_at)
      = (candidate.manifest_kind,candidate.status,candidate.requested_status,candidate.canonical_uri,
         candidate.content_hash,candidate.authority_ceiling,candidate.tools,candidate.inputs_schema_ref,
         candidate.outputs_schema_ref,candidate.eval_refs,candidate.stop_conditions,candidate.metadata,
         candidate.admission_decision_ref,candidate.authority_grant_ref,candidate.requested_by,
         candidate.approved_by,candidate.evaluated_content_hash,candidate.transition_evidence_ref,
         candidate.admitted_at,candidate.domains,candidate.skill_refs,candidate.rights_review,
         candidate.trigger_contract,candidate.updated_at) where id=existing.id;
  end if;
  return candidate.id;
end $$;

revoke all on function quirk_sync.apply_verified_manifest_projection(jsonb),
  quirk_sync.manifest_projection_snapshot(quirk_sync.manifest_registry),
  quirk_sync.guard_verified_manifest_projection() from public,anon,authenticated,service_role;
grant execute on function quirk_sync.apply_verified_manifest_projection(jsonb),
  quirk_sync.manifest_projection_snapshot(quirk_sync.manifest_registry) to quirk_manifest_verifier;
grant select,insert on quirk_sync.manifest_transition_ledger to quirk_manifest_verifier;
grant usage,select on all sequences in schema quirk_sync to quirk_manifest_verifier;
create policy manifest_transition_ledger_verifier on quirk_sync.manifest_transition_ledger
  for all to quirk_manifest_verifier using (true) with check (true);
comment on table quirk_sync.manifest_projection_receipts is
  'Append-only projection of an external GitHub approval verified by admitted Python. Not independent attestation or hash verification.';
