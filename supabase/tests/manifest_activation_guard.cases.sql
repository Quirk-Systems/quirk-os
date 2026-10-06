-- Manifest activation guard cases for Quirk Sync Control Plane v0.2.
--
-- Every case here exercises `quirk_sync.manifest_activation_violation` through
-- the trigger that raises it: one insert that must be admitted and eight that
-- must be refused by name. Each asserts the specific refusal substring, so a
-- rule that stops firing fails the case rather than passing on a different
-- rule's message.
--
-- The file carries NO transaction control on purpose, because both of its
-- callers supply one: `sync_control_plane_hardening.sql` includes it inside that
-- suite's begin/rollback, and `manifest_activation_guard.run.sql` — the driver
-- CI runs — includes it between its own `begin;` and `rollback;`. Adding
-- `begin;` here would break both. Nothing below commits.
--
-- To run these cases on their own, run the driver:
--
--   psql -v ON_ERROR_STOP=1 -f supabase/tests/manifest_activation_guard.run.sql
--
-- Do NOT run this file directly under `psql --single-transaction`. It looks
-- equivalent and is not: `--single-transaction` rolls back on an error but
-- COMMITS when nothing raises, and the first case below is supposed to raise
-- nothing, so it leaves an admitted active manifest in the database. That is
-- the reason the driver exists.
-- Synthetic approval; transaction rolls back. Never a real authorization.
insert into quirk_sync.github_approval_registry
(grant_id,subject_kind,subject_id,subject_version,subject_contract,subject_digest,authority_ceiling,allowed_actions,requested_by,approved_by,decision_ref,repository,request_commit,request_path,pr_number,review_id,reviewer_id,reviewer_login,issued_at,expires_at,verified_at)
values ('grant.sql.valid','manifest','agent.sql-valid','9.9.1',jsonb_build_object('manifest_key','agent.sql-valid','manifest_kind','agent','version','9.9.1','canonical_uri','https://github.com/Quirk-Systems/quirk-os/pull/5','authority_ceiling','propose','domains','["sync"]'::jsonb,'tools','[]'::jsonb,'inputs_schema_ref','schemas/source-binding.schema.json','outputs_schema_ref','schemas/sync-run-receipt.schema.json','trigger_contract',null,'skill_refs','[]'::jsonb,'rights_review',null,'eval_refs','["eval.sql.valid"]'::jsonb,'stop_conditions','["missing_authority"]'::jsonb,'metadata','{}'::jsonb),repeat('a',64),'propose','["activate_manifest"]','agent.sql-valid','human.bryan','decision.sql.valid','Quirk-Systems/quirk-os',repeat('0',40),'tests/synthetic-request.json',1,1,207279,'bryansayler',now()-interval '1 minute',now()+interval '1 hour',now());

-- Valid activation must pass with independent approval.
do $$
declare
  v_hash text := repeat('a', 64);
begin
  insert into quirk_sync.manifest_registry (
    manifest_key, manifest_kind, version, status, requested_status,
    canonical_uri, content_hash, authority_ceiling, tools,
    inputs_schema_ref, outputs_schema_ref, eval_refs, stop_conditions,
    requested_by, approved_by, admission_decision_ref, authority_grant_ref,
    evaluated_content_hash, transition_evidence_ref, admitted_at, domains
  ) values (
    'agent.sql-valid', 'agent', '9.9.1', 'active', 'active',
    'https://github.com/Quirk-Systems/quirk-os/pull/5', v_hash, 'propose', '[]'::jsonb,
    'schemas/source-binding.schema.json', 'schemas/sync-run-receipt.schema.json',
    '["eval.sql.valid"]'::jsonb, '["missing_authority"]'::jsonb,
    'agent.sql-valid', 'human.bryan', 'decision.sql.valid', 'grant.sql.valid',
    v_hash, 'evidence.sql.valid', now(), '["sync"]'::jsonb
  );
end $$;

-- Self-promotion must be rejected.
do $$
declare
  v_rejected boolean := false;
  v_hash text := repeat('b', 64);
begin
  begin
    insert into quirk_sync.manifest_registry (
      manifest_key, manifest_kind, version, status, requested_status,
      canonical_uri, content_hash, authority_ceiling, tools,
      inputs_schema_ref, outputs_schema_ref, eval_refs, stop_conditions,
      requested_by, approved_by, admission_decision_ref, authority_grant_ref,
      evaluated_content_hash, transition_evidence_ref, admitted_at, domains
    ) values (
      'agent.sql-self', 'agent', '9.9.2', 'active', 'active',
      'https://github.com/Quirk-Systems/quirk-os/pull/5', v_hash, 'execute_protected', '[]'::jsonb,
      'schemas/source-binding.schema.json', 'schemas/sync-run-receipt.schema.json',
      '["eval.self"]'::jsonb, '["none"]'::jsonb,
      'agent.sql-self', 'agent.sql-self', 'decision.self', 'grant.self',
      v_hash, 'evidence.self', now(), '["sync","governance"]'::jsonb
    );
  exception when others then
    v_rejected := position('may not approve' in sqlerrm) > 0;
  end;
  if not v_rejected then
    raise exception 'SCP-011 failed: self-promotion was not rejected';
  end if;
end $$;

-- A sibling agent's approval is still capability granting authority.
-- The self-approval test above passes on string inequality alone, so it never
-- caught this: naming any second agent cleared the guard.
do $$
declare
  v_rejected boolean := false;
  v_hash text := repeat('e', 64);
begin
  begin
    insert into quirk_sync.manifest_registry (
      manifest_key, manifest_kind, version, status, requested_status,
      canonical_uri, content_hash, authority_ceiling, tools,
      inputs_schema_ref, outputs_schema_ref, eval_refs, stop_conditions,
      requested_by, approved_by, admission_decision_ref, authority_grant_ref,
      evaluated_content_hash, transition_evidence_ref, admitted_at, domains
    ) values (
      'agent.sql-escalate', 'agent', '9.9.5', 'active', 'active',
      'https://github.com/Quirk-Systems/quirk-os/pull/113', v_hash, 'execute_protected', '[]'::jsonb,
      'schemas/source-binding.schema.json', 'schemas/sync-run-receipt.schema.json',
      '["eval.sibling"]'::jsonb, '["none"]'::jsonb,
      'agent.sql-escalate', 'agent.sql-sibling', 'decision.sibling', 'grant.sibling',
      v_hash, 'evidence.sibling', now(), '["sync","governance"]'::jsonb
    );
  exception when others then
    v_rejected := position('independent human principal' in sqlerrm) > 0;
  end;
  if not v_rejected then
    raise exception 'sibling-agent approval was not rejected';
  end if;
end $$;

-- An omitted JSON key must not pass a guard that exists to require it.
-- `->>` on a missing key is NULL and `NULL <> 'approved'` is NULL, so the old
-- `<>` form let omission through while refusing a wrong value.
do $$
declare
  v_rejected boolean := false;
  v_hash text := repeat('1', 64);
begin
  begin
    insert into quirk_sync.manifest_registry (
      manifest_key, manifest_kind, version, status, requested_status,
      canonical_uri, content_hash, authority_ceiling, tools,
      inputs_schema_ref, outputs_schema_ref, eval_refs, stop_conditions,
      requested_by, approved_by, admission_decision_ref, authority_grant_ref,
      evaluated_content_hash, transition_evidence_ref, admitted_at, domains,
      rights_review
    ) values (
      'agent.sql-rights-omitted', 'agent', '9.9.7', 'active', 'active',
      'https://github.com/Quirk-Systems/quirk-os/pull/113', v_hash, 'propose', '[]'::jsonb,
      'schemas/source-binding.schema.json', 'schemas/sync-run-receipt.schema.json',
      '["eval.omitted"]'::jsonb, '["none"]'::jsonb,
      'agent.sql-rights-omitted', 'human.bryan', 'decision.omitted', 'grant.omitted',
      v_hash, 'evidence.omitted', now(), '["data_productization"]'::jsonb,
      '{"license_verified":true,"provenance_complete":true}'::jsonb
    );
  exception when others then
    v_rejected := position('data productization requires' in sqlerrm) > 0;
  end;
  if not v_rejected then
    raise exception 'rights review with outcome and privacy_review omitted was accepted';
  end if;
end $$;

-- Same NULL-logic class on the orchestrator routing guard.
do $$
declare
  v_rejected boolean := false;
  v_hash text := repeat('2', 64);
begin
  begin
    insert into quirk_sync.manifest_registry (
      manifest_key, manifest_kind, version, status, requested_status,
      canonical_uri, content_hash, authority_ceiling, tools,
      inputs_schema_ref, outputs_schema_ref, eval_refs, stop_conditions,
      requested_by, approved_by, admission_decision_ref, authority_grant_ref,
      evaluated_content_hash, transition_evidence_ref, admitted_at, domains,
      skill_refs, trigger_contract
    ) values (
      'orchestrator.sql-collision-omitted', 'orchestrator', '9.9.8', 'active', 'active',
      'https://github.com/Quirk-Systems/quirk-os/pull/113', v_hash, 'propose', '[]'::jsonb,
      'schemas/source-binding.schema.json', 'schemas/sync-run-receipt.schema.json',
      '["eval.collision"]'::jsonb, '["none"]'::jsonb,
      'agent.sql-collision-requester', 'human.bryan', 'decision.collision', 'grant.collision',
      v_hash, 'evidence.collision', now(), '["sync"]'::jsonb,
      '["skill.a","skill.b"]'::jsonb, '{"routing_policy":"explicit_priority"}'::jsonb
    );
  exception when others then
    v_rejected := position('fail-closed trigger contract' in sqlerrm) > 0;
  end;
  if not v_rejected then
    raise exception 'orchestrator with collision_behavior omitted was accepted';
  end if;
end $$;

-- The requester had no shape check at all. The JSON schema constrains that
-- field for manifests arriving as documents; nothing constrained the column.
do $$
declare
  v_rejected boolean := false;
  v_hash text := repeat('3', 64);
begin
  begin
    insert into quirk_sync.manifest_registry (
      manifest_key, manifest_kind, version, status, requested_status,
      canonical_uri, content_hash, authority_ceiling, tools,
      inputs_schema_ref, outputs_schema_ref, eval_refs, stop_conditions,
      requested_by, approved_by, admission_decision_ref, authority_grant_ref,
      evaluated_content_hash, transition_evidence_ref, admitted_at, domains
    ) values (
      'agent.sql-bad-requester', 'agent', '9.9.9', 'active', 'active',
      'https://github.com/Quirk-Systems/quirk-os/pull/113', v_hash, 'propose', '[]'::jsonb,
      'schemas/source-binding.schema.json', 'schemas/sync-run-receipt.schema.json',
      '["eval.requester"]'::jsonb, '["none"]'::jsonb,
      'NOT-A-PRINCIPAL', 'human.bryan', 'decision.requester', 'grant.requester',
      v_hash, 'evidence.requester', now(), '["sync"]'::jsonb
    );
  exception when others then
    v_rejected := position('well-formed principal' in sqlerrm) > 0;
  end;
  if not v_rejected then
    raise exception 'a malformed requester principal was accepted';
  end if;
end $$;

-- A principal naming nobody is refused. There is no schema layer in front of
-- the database, so the guard matches the whole principal, not its prefix.
do $$
declare
  v_rejected boolean := false;
  v_hash text := repeat('f', 64);
begin
  begin
    insert into quirk_sync.manifest_registry (
      manifest_key, manifest_kind, version, status, requested_status,
      canonical_uri, content_hash, authority_ceiling, tools,
      inputs_schema_ref, outputs_schema_ref, eval_refs, stop_conditions,
      requested_by, approved_by, admission_decision_ref, authority_grant_ref,
      evaluated_content_hash, transition_evidence_ref, admitted_at, domains
    ) values (
      'agent.sql-empty-principal', 'agent', '9.9.6', 'active', 'active',
      'https://github.com/Quirk-Systems/quirk-os/pull/113', v_hash, 'propose', '[]'::jsonb,
      'schemas/source-binding.schema.json', 'schemas/sync-run-receipt.schema.json',
      '["eval.empty"]'::jsonb, '["none"]'::jsonb,
      'agent.sql-empty-principal', 'human.', 'decision.empty', 'grant.empty',
      v_hash, 'evidence.empty', now(), '["sync"]'::jsonb
    );
  exception when others then
    v_rejected := position('independent human principal' in sqlerrm) > 0;
  end;
  if not v_rejected then
    raise exception 'a principal naming nobody was accepted as an approver';
  end if;
end $$;

-- Data productization without approved rights must be rejected.
do $$
declare
  v_rejected boolean := false;
  v_hash text := repeat('c', 64);
begin
  begin
    insert into quirk_sync.manifest_registry (
      manifest_key, manifest_kind, version, status, requested_status,
      canonical_uri, content_hash, authority_ceiling, tools,
      inputs_schema_ref, outputs_schema_ref, eval_refs, stop_conditions,
      requested_by, approved_by, admission_decision_ref, authority_grant_ref,
      evaluated_content_hash, transition_evidence_ref, admitted_at, domains, rights_review
    ) values (
      'capability.sql-rights', 'capability', '9.9.3', 'active', 'active',
      'https://github.com/Quirk-Systems/quirk-os/pull/5', v_hash, 'execute_reversible', '[]'::jsonb,
      'rights/unknown', 'products/data-product', '["eval.rights"]'::jsonb, '["rights_unclear"]'::jsonb,
      'agent.quirk-value-foundry', 'human.bryan', 'decision.rights', 'grant.rights',
      v_hash, 'evidence.rights', now(), '["data_productization"]'::jsonb,
      '{"outcome":"deferred","license_verified":false,"privacy_review":"blocked","provenance_complete":false}'::jsonb
    );
  exception when others then
    v_rejected := position('data productization requires' in sqlerrm) > 0;
  end;
  if not v_rejected then
    raise exception 'SCP-010 failed: rights-unclear productization was not rejected';
  end if;
end $$;

-- Multi-skill trigger collision without routing contract must be rejected.
do $$
declare
  v_rejected boolean := false;
  v_hash text := repeat('d', 64);
begin
  begin
    insert into quirk_sync.manifest_registry (
      manifest_key, manifest_kind, version, status, requested_status,
      canonical_uri, content_hash, authority_ceiling, tools,
      inputs_schema_ref, outputs_schema_ref, eval_refs, stop_conditions,
      requested_by, approved_by, admission_decision_ref, authority_grant_ref,
      evaluated_content_hash, transition_evidence_ref, admitted_at, domains, skill_refs
    ) values (
      'orchestrator.sql-collision', 'orchestrator', '9.9.4', 'active', 'active',
      'https://github.com/Quirk-Systems/quirk-os/pull/5', v_hash, 'propose', '[]'::jsonb,
      'triggers/ambiguous', 'routing/unknown', '["eval.collision"]'::jsonb, '["collision"]'::jsonb,
      'agent.sql-orchestrator', 'human.bryan', 'decision.collision', 'grant.collision',
      v_hash, 'evidence.collision', now(), '["sync"]'::jsonb,
      '["skill.alpha","skill.beta"]'::jsonb
    );
  exception when others then
    v_rejected := position('trigger contract' in sqlerrm) > 0;
  end;
  if not v_rejected then
    raise exception 'SCP-008 failed: trigger collision was not rejected';
  end if;
end $$;
