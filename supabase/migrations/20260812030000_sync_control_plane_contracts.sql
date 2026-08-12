-- Quirk Sync Control Plane v0.2 candidate hardening.
-- Canon remains in Git. Human admission remains external.

create schema if not exists quirk_sync;

-- Stable canonical/runtime mapping fields.
alter table quirk_sync.source_bindings
  add column if not exists schema_version text not null default 'source-binding.v2',
  add column if not exists binding_key text,
  add column if not exists freshness jsonb not null default '{"status":"unknown"}'::jsonb;
update quirk_sync.source_bindings
set binding_key = 'binding.' || platform || '.' || md5(external_id)
where binding_key is null;
alter table quirk_sync.source_bindings alter column binding_key set not null;
create unique index if not exists source_bindings_binding_key_uq on quirk_sync.source_bindings(binding_key);
alter table quirk_sync.source_bindings drop constraint if exists source_bindings_platform_check;
alter table quirk_sync.source_bindings add constraint source_bindings_platform_check
  check (platform in ('github','supabase','google_drive','airtable','notion','vercel','cloudflare'));
alter table quirk_sync.source_bindings drop constraint if exists source_bindings_state_check;
alter table quirk_sync.source_bindings add constraint source_bindings_state_check
  check (state in ('discovered','candidate','active','deferred','drifted','paused','error','retired'));
alter table quirk_sync.source_bindings drop constraint if exists source_bindings_freshness_object_check;
alter table quirk_sync.source_bindings add constraint source_bindings_freshness_object_check
  check (jsonb_typeof(freshness) = 'object');
alter table quirk_sync.source_bindings drop constraint if exists source_bindings_cloudflare_boundary_check;
alter table quirk_sync.source_bindings add constraint source_bindings_cloudflare_boundary_check
  check (platform <> 'cloudflare' or (state in ('discovered','deferred','paused','retired') and sync_direction in ('none','projection_only')));

alter table quirk_sync.run_receipts
  add column if not exists schema_version text not null default 'sync-run-receipt.v2',
  add column if not exists receipt_hash text,
  add column if not exists supersedes_receipt_key text,
  add column if not exists correction_reason text,
  add column if not exists content_hashes jsonb not null default '{}'::jsonb,
  add column if not exists outcome jsonb not null default '{}'::jsonb;
alter table quirk_sync.run_receipts drop constraint if exists run_receipts_run_type_check;
alter table quirk_sync.run_receipts add constraint run_receipts_run_type_check
  check (run_type in ('discover','pull','push','reconcile','project','validate','backfill','rebuild','compensate'));
alter table quirk_sync.run_receipts drop constraint if exists run_receipts_status_check;
alter table quirk_sync.run_receipts add constraint run_receipts_status_check
  check (status in ('planned','running','succeeded','failed','blocked','cancelled','superseded'));
alter table quirk_sync.run_receipts drop constraint if exists run_receipts_receipt_hash_check;
alter table quirk_sync.run_receipts add constraint run_receipts_receipt_hash_check
  check (receipt_hash is null or receipt_hash ~ '^[a-f0-9]{64}$');
alter table quirk_sync.run_receipts drop constraint if exists run_receipts_v2_json_check;
alter table quirk_sync.run_receipts add constraint run_receipts_v2_json_check
  check (jsonb_typeof(content_hashes)='object' and jsonb_typeof(outcome)='object');
alter table quirk_sync.run_receipts drop constraint if exists run_receipts_correction_check;
alter table quirk_sync.run_receipts add constraint run_receipts_correction_check
  check (supersedes_receipt_key is null or nullif(correction_reason,'') is not null);

-- Admission fields remain separate from capability and tools.
alter table quirk_sync.manifest_registry
  add column if not exists requested_status text not null default 'candidate',
  add column if not exists admission_decision_ref text,
  add column if not exists authority_grant_ref text,
  add column if not exists requested_by text,
  add column if not exists approved_by text,
  add column if not exists evaluated_content_hash text,
  add column if not exists transition_evidence_ref text,
  add column if not exists admitted_at timestamptz,
  add column if not exists domains jsonb not null default '[]'::jsonb,
  add column if not exists skill_refs jsonb not null default '[]'::jsonb,
  add column if not exists rights_review jsonb,
  add column if not exists trigger_contract jsonb;
alter table quirk_sync.manifest_registry drop constraint if exists manifest_registry_requested_status_check;
alter table quirk_sync.manifest_registry add constraint manifest_registry_requested_status_check
  check (requested_status in ('candidate','active','paused','superseded','revoked'));
alter table quirk_sync.manifest_registry drop constraint if exists manifest_registry_v2_json_check;
alter table quirk_sync.manifest_registry add constraint manifest_registry_v2_json_check
  check (jsonb_typeof(domains)='array' and jsonb_typeof(skill_refs)='array'
    and (rights_review is null or jsonb_typeof(rights_review)='object')
    and (trigger_contract is null or jsonb_typeof(trigger_contract)='object'));
alter table quirk_sync.manifest_registry drop constraint if exists manifest_registry_evaluated_hash_check;
alter table quirk_sync.manifest_registry add constraint manifest_registry_evaluated_hash_check
  check (evaluated_content_hash is null or evaluated_content_hash ~ '^[a-f0-9]{64}$');

create table if not exists quirk_sync.manifest_transition_ledger (
  id bigint generated by default as identity primary key,
  transition_key text not null unique,
  manifest_id uuid not null references quirk_sync.manifest_registry(id) on delete restrict,
  manifest_key text not null,
  manifest_version text not null,
  from_status text,
  to_status text not null,
  requested_by text,
  approved_by text,
  decision_ref text,
  authority_grant_ref text,
  evaluated_content_hash text,
  evidence_refs jsonb not null default '[]'::jsonb check (jsonb_typeof(evidence_refs)='array'),
  occurred_at timestamptz not null default now()
);

create or replace function quirk_sync.guard_manifest_activation() returns trigger
language plpgsql set search_path=pg_catalog,quirk_sync as $$
begin
  if new.status='active' then
    if new.requested_status<>'active' then raise exception 'active manifest requires requested_status=active'; end if;
    if new.admission_decision_ref is null or new.authority_grant_ref is null or new.requested_by is null
      or new.approved_by is null or new.evaluated_content_hash is null or new.transition_evidence_ref is null or new.admitted_at is null
      then raise exception 'active manifest requires independent admission evidence'; end if;
    if new.requested_by=new.approved_by then raise exception 'manifest requester may not approve its own activation'; end if;
    if new.evaluated_content_hash<>new.content_hash then raise exception 'evaluated content hash does not match manifest content hash'; end if;
    if jsonb_array_length(new.eval_refs)=0 or jsonb_array_length(new.stop_conditions)=0
      then raise exception 'active manifest requires eval evidence and stop conditions'; end if;
    if new.manifest_kind='orchestrator' and jsonb_array_length(new.skill_refs)>1 and
      (new.trigger_contract is null or new.trigger_contract->>'collision_behavior'<>'block'
       or nullif(new.trigger_contract->>'routing_policy','') is null)
      then raise exception 'multi-skill orchestrator requires fail-closed trigger contract'; end if;
    if new.domains ? 'data_productization' and
      (new.rights_review is null or new.rights_review->>'outcome'<>'approved'
       or coalesce(new.rights_review->>'license_verified','false')::boolean is not true
       or new.rights_review->>'privacy_review'<>'approved'
       or coalesce(new.rights_review->>'provenance_complete','false')::boolean is not true)
      then raise exception 'data productization requires approved rights, licensing, privacy, and provenance review'; end if;
  end if;
  return new;
end $$;

create or replace function quirk_sync.record_manifest_transition() returns trigger
language plpgsql set search_path=pg_catalog,quirk_sync as $$
begin
  insert into quirk_sync.manifest_transition_ledger(
    transition_key,manifest_id,manifest_key,manifest_version,from_status,to_status,requested_by,approved_by,
    decision_ref,authority_grant_ref,evaluated_content_hash,evidence_refs,occurred_at)
  values('transition.'||replace(new.manifest_key,'.','_')||'.'||new.version||'.'||replace(gen_random_uuid()::text,'-',''),
    new.id,new.manifest_key,new.version,case when tg_op='UPDATE' then old.status end,new.status,new.requested_by,new.approved_by,
    new.admission_decision_ref,new.authority_grant_ref,new.evaluated_content_hash,
    case when new.transition_evidence_ref is null then '[]'::jsonb else jsonb_build_array(new.transition_evidence_ref) end,
    coalesce(new.admitted_at,now()));
  return new;
end $$;

drop trigger if exists manifest_activation_guard on quirk_sync.manifest_registry;
create trigger manifest_activation_guard before insert or update on quirk_sync.manifest_registry
for each row execute function quirk_sync.guard_manifest_activation();
drop trigger if exists manifest_transition_insert on quirk_sync.manifest_registry;
create trigger manifest_transition_insert after insert on quirk_sync.manifest_registry
for each row execute function quirk_sync.record_manifest_transition();
drop trigger if exists manifest_transition_update on quirk_sync.manifest_registry;
create trigger manifest_transition_update after update of status on quirk_sync.manifest_registry
for each row when (old.status is distinct from new.status) execute function quirk_sync.record_manifest_transition();

insert into quirk_sync.manifest_transition_ledger(
  transition_key,manifest_id,manifest_key,manifest_version,to_status,evidence_refs,occurred_at)
select 'transition.seed.'||md5(manifest_key||':'||version),id,manifest_key,version,status,
  jsonb_build_array('migration://sync-control-plane-v0.2/baseline'),created_at
from quirk_sync.manifest_registry
on conflict (transition_key) do nothing;
