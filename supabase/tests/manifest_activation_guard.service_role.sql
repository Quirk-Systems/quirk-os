-- Manifest activation guard cases for the role that actually writes.
--
-- These must run in a psql session of their own, and must be the first thing
-- in it that fires the trigger on `quirk_sync.manifest_registry`. That is not
-- tidiness, it is the only arrangement in which they can fail.
--
-- `guard_manifest_activation` calls `quirk_sync.manifest_activation_violation`,
-- and PL/pgSQL caches the plan for that call per session while the function's
-- EXECUTE privilege is checked when the plan is built. So the check is
-- session-order dependent. Observed on PostgreSQL 16.13 with the grant
-- revoked:
--
--   fresh session, service_role writes first   -> ERROR: permission denied for
--                                                 function manifest_activation_violation
--   fresh session, postgres writes first, then
--   `set role service_role` and write again    -> INSERT 0 1, INSERT 0 1
--
-- Folding these cases into `manifest_activation_guard.cases.sql` puts nine
-- superuser writes in front of them, which primes the cached plan and makes
-- them pass with no grant at all. That is how they were written first, and it
-- is why they are here instead.
--
-- Production connects as `service_role`, so production is the first arrangement.
--
-- `service_role` needs BYPASSRLS, which Supabase gives it; without that these
-- inserts fail on row-level security before reaching the trigger and pass for
-- the wrong reason.

begin;

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
    'service_role cannot write a valid manifest: %. The guard calls manifest_activation_violation and the invoking role needs EXECUTE on it.',
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

rollback;
