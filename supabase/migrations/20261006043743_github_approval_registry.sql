-- GitHub human review is evidence; the separately credentialed ingestor owns trust.
-- Run transactionally. No live grant is seeded and no existing row is changed.
lock table quirk_sync.manifest_registry in exclusive mode;
do $$ begin
  if exists (select 1 from pg_roles where rolname = 'quirk_approval_ingestor') then
    raise exception 'approval ingestor role already exists: inspect ownership and memberships before cutover';
  end if;
end $$;
create role quirk_approval_ingestor nologin noinherit nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
grant usage on schema quirk_sync to quirk_approval_ingestor;

-- Numeric account identity, login, and principal are all pinned. Only owner can
-- alter this allowlist; neither runtime nor ingestor can invent designated humans.
create table quirk_sync.github_approval_humans (
  reviewer_id bigint primary key check (reviewer_id = 207279),
  reviewer_login text not null check (reviewer_login = 'bryansayler'),
  principal text not null check (principal = 'human.bryan'),
  unique (reviewer_id, reviewer_login, principal)
);
insert into quirk_sync.github_approval_humans values (207279, 'bryansayler', 'human.bryan');
create table quirk_sync.github_approval_registry (
  grant_id text primary key check (length(grant_id) > 0),
  subject_kind text not null check (subject_kind in ('manifest','skill')),
  subject_id text not null check (length(subject_id) > 0),
  subject_version text not null check (length(subject_version) > 0),
  subject_contract jsonb not null check (jsonb_typeof(subject_contract) = 'object'),
  subject_digest text not null check (subject_digest ~ '^[a-f0-9]{64}$'),
  authority_ceiling text not null check (
    (subject_kind = 'skill' and authority_ceiling in ('observe','infer','propose','execute_bounded'))
    or (subject_kind = 'manifest' and authority_ceiling in ('observe','infer','propose','execute_reversible','enforce_invariant','execute_protected'))
  ),
  allowed_actions jsonb not null check (jsonb_typeof(allowed_actions) = 'array' and jsonb_array_length(allowed_actions) > 0 and not jsonb_path_exists(allowed_actions, '$[*] ? (@.type() != "string")')),
  requested_by text not null check (requested_by ~ '^(human|agent|service|system)\.[a-z0-9._-]+$'),
  approved_by text not null check (approved_by = 'human.bryan' and approved_by <> requested_by),
  decision_ref text not null check (length(decision_ref) > 0),
  repository text not null check (repository = 'Quirk-Systems/quirk-os'),
  request_commit text not null check (request_commit ~ '^[a-f0-9]{40}$'),
  request_path text not null check (length(request_path) > 0),
  pr_number bigint not null check (pr_number > 0),
  review_id bigint not null check (review_id > 0),
  reviewer_id bigint not null,
  reviewer_login text not null,
  issued_at timestamptz not null,
  expires_at timestamptz not null check (expires_at > issued_at),
  verified_at timestamptz not null,
  revoked_at timestamptz,
  foreign key (reviewer_id,reviewer_login,approved_by) references quirk_sync.github_approval_humans(reviewer_id,reviewer_login,principal)
);
revoke all on quirk_sync.github_approval_humans, quirk_sync.github_approval_registry from public, anon, authenticated, service_role;
grant select on quirk_sync.github_approval_humans to quirk_approval_ingestor;
grant select, insert on quirk_sync.github_approval_registry to quirk_approval_ingestor;
grant update (verified_at, revoked_at) on quirk_sync.github_approval_registry to quirk_approval_ingestor;
alter table quirk_sync.github_approval_humans enable row level security;
alter table quirk_sync.github_approval_registry enable row level security;
create policy github_humans_ingestor_read on quirk_sync.github_approval_humans for select to quirk_approval_ingestor using (true);
create policy github_registry_ingestor_read on quirk_sync.github_approval_registry for select to quirk_approval_ingestor using (true);
create policy github_registry_ingestor_insert on quirk_sync.github_approval_registry for insert to quirk_approval_ingestor with check (true);
create policy github_registry_ingestor_refresh on quirk_sync.github_approval_registry for update to quirk_approval_ingestor using (true) with check (true);

create function quirk_sync.guard_github_approval_binding() returns trigger
language plpgsql set search_path = pg_catalog, quirk_sync, pg_temp as $$
begin
  if (to_jsonb(new) - 'verified_at' - 'revoked_at') is distinct from (to_jsonb(old) - 'verified_at' - 'revoked_at') then
    raise exception 'GitHub approval binding is immutable';
  end if;
  if old.revoked_at is not null and new.revoked_at is distinct from old.revoked_at then
    raise exception 'GitHub approval revocation is sticky';
  end if;
  if new.verified_at < old.verified_at then raise exception 'GitHub approval verification may not regress'; end if;
  return new;
end $$;
create trigger github_approval_binding_guard before update on quirk_sync.github_approval_registry
for each row execute function quirk_sync.guard_github_approval_binding();

create function quirk_sync.github_approval_allows(
 p_grant_id text,p_subject_kind text,p_subject_id text,p_subject_version text,p_subject_digest text,
 p_authority_ceiling text,p_actions jsonb,p_requested_by text,p_approved_by text,p_decision_ref text,p_subject_contract jsonb default '{}'::jsonb
) returns boolean language sql stable security definer
set search_path = pg_catalog, quirk_sync, pg_temp as $$
 select case when jsonb_typeof(p_actions) is distinct from 'array' then false else coalesce(jsonb_array_length(p_actions) > 0
   and not jsonb_path_exists(p_actions, '$[*] ? (@.type() != "string")') and exists (
   select 1 from quirk_sync.github_approval_registry a
   join quirk_sync.github_approval_humans h on (h.reviewer_id,h.reviewer_login,h.principal) = (a.reviewer_id,a.reviewer_login,a.approved_by)
   where a.grant_id=p_grant_id and a.subject_kind=p_subject_kind and a.subject_id=p_subject_id
     and a.subject_version=p_subject_version and a.subject_digest=p_subject_digest
     and a.subject_contract = p_subject_contract
     and a.authority_ceiling=p_authority_ceiling and a.allowed_actions @> p_actions
     and a.requested_by=p_requested_by and a.approved_by=p_approved_by and a.decision_ref=p_decision_ref
     and a.issued_at <= statement_timestamp() and a.expires_at > statement_timestamp() and a.revoked_at is null
     and a.verified_at <= statement_timestamp() and a.verified_at >= statement_timestamp() - interval '5 minutes'
 ), false) end
$$;
revoke all on function quirk_sync.github_approval_allows(text,text,text,text,text,text,jsonb,text,text,text,jsonb) from public,anon,authenticated;
grant execute on function quirk_sync.github_approval_allows(text,text,text,text,text,text,jsonb,text,text,text,jsonb) to service_role;

-- All inline execution-bearing fields are bound, independent of caller hash.
create function quirk_sync.manifest_github_contract(m quirk_sync.manifest_registry)
returns jsonb language sql immutable set search_path = pg_catalog, quirk_sync, pg_temp as $$
 select jsonb_build_object('manifest_key',m.manifest_key,'manifest_kind',m.manifest_kind,
  'version',m.version,'canonical_uri',m.canonical_uri,'authority_ceiling',m.authority_ceiling,
  'domains',m.domains,'tools',m.tools,'inputs_schema_ref',m.inputs_schema_ref,
  'outputs_schema_ref',m.outputs_schema_ref,'trigger_contract',m.trigger_contract,
  'skill_refs',m.skill_refs,'rights_review',m.rights_review,'eval_refs',m.eval_refs,
  'stop_conditions',m.stop_conditions,'metadata',m.metadata)
$$;
revoke all on function quirk_sync.manifest_github_contract(quirk_sync.manifest_registry) from public, anon, authenticated;
grant execute on function quirk_sync.manifest_github_contract(quirk_sync.manifest_registry) to service_role;

create function quirk_sync.guard_manifest_github_approval() returns trigger
language plpgsql security definer set search_path = pg_catalog, quirk_sync, pg_temp as $$
begin
 if new.status = 'active' and not quirk_sync.github_approval_allows(new.authority_grant_ref,'manifest',new.manifest_key,new.version,new.content_hash,new.authority_ceiling,'["activate_manifest"]'::jsonb,new.requested_by,new.approved_by,new.admission_decision_ref,quirk_sync.manifest_github_contract(new)) then
   raise exception 'active manifest requires a matching fresh verified GitHub human approval';
 end if;
 return new;
end $$;
-- Alphabetical trigger order preserves the older structural refusal diagnostics.
create trigger manifest_github_approval_guard before insert or update on quirk_sync.manifest_registry
for each row execute function quirk_sync.guard_manifest_github_approval();
revoke all on function quirk_sync.guard_manifest_github_approval(), quirk_sync.guard_github_approval_binding() from public,anon,authenticated,service_role;

do $$ declare bad text; begin
 select string_agg(manifest_key || '@' || version, ', ') into bad from quirk_sync.manifest_registry m
 where m.status='active' and not quirk_sync.github_approval_allows(m.authority_grant_ref,'manifest',m.manifest_key,m.version,m.content_hash,m.authority_ceiling,'["activate_manifest"]'::jsonb,m.requested_by,m.approved_by,m.admission_decision_ref,quirk_sync.manifest_github_contract(m));
 if bad is not null then raise exception 'refusing GitHub approval cutover: active manifests lack matching approvals: %', bad; end if;
end $$;

-- A persisted active status does not survive expiry/revocation. Every executor
-- must call this lookup immediately before use; raw status SELECT is insufficient.
create function quirk_sync.assert_manifest_runtime_authorized(p_manifest_key text,p_version text)
returns boolean language plpgsql stable security definer set search_path = pg_catalog, quirk_sync, pg_temp as $$
declare m quirk_sync.manifest_registry; begin
 select * into m from quirk_sync.manifest_registry where manifest_key=p_manifest_key and version=p_version and status='active';
 if not found or not quirk_sync.github_approval_allows(m.authority_grant_ref,'manifest',m.manifest_key,m.version,m.content_hash,m.authority_ceiling,'["activate_manifest"]'::jsonb,m.requested_by,m.approved_by,m.admission_decision_ref,quirk_sync.manifest_github_contract(m)) then
  raise exception 'manifest runtime use requires current GitHub approval';
 end if;
 return true;
end $$;
revoke all on function quirk_sync.assert_manifest_runtime_authorized(text,text) from public,anon,authenticated;
grant execute on function quirk_sync.assert_manifest_runtime_authorized(text,text) to service_role;
