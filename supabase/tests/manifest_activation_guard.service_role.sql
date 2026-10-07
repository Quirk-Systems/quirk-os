-- Manifest activation guard cases for the role that actually writes.
--
-- What these prove: the guard judges `service_role` writes correctly WITHOUT
-- `service_role` holding EXECUTE on the rule function. The guard is SECURITY
-- DEFINER, so its inner call is checked against the guard's owner, and the
-- grant is revoked below before the first write precisely so that enforcement
-- has to be carried by that property and nothing else. If a later
-- `CREATE OR REPLACE` drops `security definer`, the first case here fails with
-- a privilege error rather than passing on the grant.
--
-- These must run in a psql session of their own, and the first trigger fire in
-- that session must come AFTER the revoke. That is not tidiness: PL/pgSQL
-- caches the plan for the guard's inner call per session, and EXECUTE on a
-- function is checked when that plan is built, so under an invoker guard the
-- check is session-order dependent. Observed on PostgreSQL 16.13:
--
--   fresh session, service_role writes first   -> ERROR: permission denied for
--                                                 function manifest_activation_violation
--   fresh session, postgres writes first, then
--   `set role service_role` and write again    -> INSERT 0 1, INSERT 0 1
--
-- Any write ahead of the revoke would prime that plan and let these pass on a
-- guard that had lost SECURITY DEFINER. Folding them into
-- `manifest_activation_guard.cases.sql`, behind nine superuser writes, is the
-- same mistake; it is how they were first written.
--
-- The last case re-grants EXECUTE and calls the rule function directly as
-- `service_role`: the pre-flight lane, where a writer reads the refusal reason
-- before attempting a write.
--
-- `service_role` needs BYPASSRLS, which Supabase gives it; without that these
-- inserts fail on row-level security before reaching the trigger and pass for
-- the wrong reason. The revoke and re-grant need a superuser, which is what CI
-- runs this file as; everything rolls back.

begin;

-- Before any write in this session. See the header for why the position matters.
revoke execute on function
  quirk_sync.manifest_activation_violation(quirk_sync.manifest_registry)
  from service_role;

-- Seed the later protected registry only when that migration is installed.
do $$ begin
  if to_regclass('quirk_sync.github_approval_registry') is not null then
-- Synthetic approval; transaction rolls back. Never a real authorization.
insert into quirk_sync.github_approval_registry
(grant_id,subject_kind,subject_id,subject_version,subject_contract,subject_digest,authority_ceiling,allowed_actions,requested_by,approved_by,decision_ref,repository,request_commit,request_path,pr_number,review_id,reviewer_id,reviewer_login,issued_at,expires_at,verified_at)
values ('grant.service','manifest','agent.service-role-valid','9.9.10',jsonb_build_object('manifest_key','agent.service-role-valid','manifest_kind','agent','version','9.9.10','canonical_uri','https://github.com/Quirk-Systems/quirk-os/pull/113','authority_ceiling','propose','domains','["sync"]'::jsonb,'tools','[]'::jsonb,'inputs_schema_ref','schemas/source-binding.schema.json','outputs_schema_ref','schemas/sync-run-receipt.schema.json','trigger_contract',null,'skill_refs','[]'::jsonb,'rights_review',null,'eval_refs','["eval.service"]'::jsonb,'stop_conditions','["missing_authority"]'::jsonb,'metadata','{}'::jsonb),repeat('7',64),'propose','["activate_manifest"]','agent.service-role-valid','human.bryan','decision.service','Quirk-Systems/quirk-os',repeat('0',40),'tests/synthetic-request.json',1,1,207279,'bryansayler',now()-interval '1 minute',now()+interval '1 hour',now());
  end if;
end $$;

set role service_role;

do $$
declare
  v_hash text := repeat('7', 64);
begin
  insert into quirk_sync.manifest_registry (
    manifest_key, manifest_kind, version, status, requested_status,
    canonical_uri, content_hash, authority_ceiling, tools,
    inputs_schema_ref, outputs_schema_ref, eval_refs, stop_conditions,
    requested_by, approved_by, admission_decision_ref, authority_grant_ref,
    evaluated_content_hash, transition_evidence_ref, admitted_at, domains
  ) values (
    'agent.service-role-valid', 'agent', '9.9.10', 'active', 'active',
    'https://github.com/Quirk-Systems/quirk-os/pull/113', v_hash, 'propose', '[]'::jsonb,
    'schemas/source-binding.schema.json', 'schemas/sync-run-receipt.schema.json',
    '["eval.service"]'::jsonb, '["missing_authority"]'::jsonb,
    'agent.service-role-valid', 'human.bryan', 'decision.service', 'grant.service',
    v_hash, 'evidence.service', now(), '["sync"]'::jsonb
  );
exception when insufficient_privilege then
  raise exception
    'service_role cannot write a valid manifest: %. EXECUTE on the rule function was revoked above, so this means the guard is no longer SECURITY DEFINER and its inner call is being checked against the writer.',
    sqlerrm;
end $$;

do $$
declare
  v_rejected boolean := false;
  v_hash text := repeat('8', 64);
begin
  begin
    insert into quirk_sync.manifest_registry (
      manifest_key, manifest_kind, version, status, requested_status,
      canonical_uri, content_hash, authority_ceiling, tools,
      inputs_schema_ref, outputs_schema_ref, eval_refs, stop_conditions,
      requested_by, approved_by, admission_decision_ref, authority_grant_ref,
      evaluated_content_hash, transition_evidence_ref, admitted_at, domains
    ) values (
      'agent.service-role-escalate', 'agent', '9.9.11', 'active', 'active',
      'https://github.com/Quirk-Systems/quirk-os/pull/113', v_hash, 'execute_protected', '[]'::jsonb,
      'schemas/source-binding.schema.json', 'schemas/sync-run-receipt.schema.json',
      '["eval.service"]'::jsonb, '["none"]'::jsonb,
      'agent.service-role-escalate', 'agent.service-role-escalate', 'decision.service', 'grant.service',
      v_hash, 'evidence.service', now(), '["sync"]'::jsonb
    );
  exception
    when insufficient_privilege then
      raise exception 'the guard failed on privileges rather than on the rule: %', sqlerrm;
    when others then
      v_rejected := position('may not approve' in sqlerrm) > 0;
  end;
  if not v_rejected then
    raise exception 'service_role self-approved an activation';
  end if;
end $$;

reset role;

-- The pre-flight lane: restore the grant and call the rule directly as
-- service_role. An invalid active row must come back with a reason, and the
-- call itself must not be refused on privileges.
grant execute on function
  quirk_sync.manifest_activation_violation(quirk_sync.manifest_registry)
  to service_role;

set role service_role;

do $$
declare
  v_reason text;
begin
  begin
    v_reason := quirk_sync.manifest_activation_violation(
      jsonb_populate_record(
        null::quirk_sync.manifest_registry,
        '{"status":"active","requested_status":"active","requested_by":"agent.preflight","approved_by":"agent.preflight"}'::jsonb
      )
    );
  exception when insufficient_privilege then
    raise exception 'service_role cannot call the rule function for pre-flight: %', sqlerrm;
  end;
  if v_reason is null then
    raise exception 'pre-flight returned no reason for an active row with no admission evidence';
  end if;
end $$;

reset role;

rollback;
