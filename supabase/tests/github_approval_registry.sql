-- Synthetic transaction only. Every assertion and record is discarded.
begin;
insert into quirk_sync.github_approval_registry
(grant_id,subject_kind,subject_id,subject_version,subject_contract,subject_digest,authority_ceiling,allowed_actions,requested_by,approved_by,decision_ref,repository,request_commit,request_path,pr_number,review_id,reviewer_id,reviewer_login,issued_at,expires_at,verified_at)
values ('grant.test','skill','skill.test','1.0.0','{}'::jsonb,repeat('a',64),'propose','["propose"]','agent.test','human.bryan','decision.test','Quirk-Systems/quirk-os',repeat('0',40),'tests/synthetic-request.json',1,1,207279,'bryansayler',now()-interval '1 minute',now()+interval '1 hour',now());
do $$ declare mutation text; ok boolean; invalid_actions jsonb; begin
 foreach invalid_actions in array array[null::jsonb,'{}'::jsonb,'[]'::jsonb,'[123]'::jsonb,'[null]'::jsonb] loop
  if quirk_sync.github_approval_allows('grant.test','skill','skill.test','1.0.0',repeat('a',64),'propose',invalid_actions,'agent.test','human.bryan','decision.test') then raise exception 'invalid actions admitted'; end if;
 end loop;
 if not quirk_sync.github_approval_allows('grant.test','skill','skill.test','1.0.0',repeat('a',64),'propose','["propose"]','agent.test','human.bryan','decision.test') then raise exception 'valid registry denied'; end if;
 if quirk_sync.github_approval_allows('absent','skill','skill.test','1.0.0',repeat('a',64),'propose','["propose"]','agent.test','human.fabricated','decision.test') then raise exception 'fabricated human admitted'; end if;
 if quirk_sync.github_approval_allows('grant.test','skill','skill.test','1.0.0',repeat('b',64),'propose','["propose"]','agent.test','human.bryan','decision.test') then raise exception 'wrong digest admitted'; end if;
 if quirk_sync.github_approval_allows('grant.test','manifest','skill.test','1.0.0',repeat('a',64),'propose','["propose"]','agent.test','human.bryan','decision.test') then raise exception 'wrong subject scope admitted'; end if;
 if quirk_sync.github_approval_allows('grant.test','skill','skill.test','1.0.0',repeat('a',64),'execute_protected','["propose"]','agent.test','human.bryan','decision.test') then raise exception 'wrong authority admitted'; end if;
 if quirk_sync.github_approval_allows('grant.test','skill','skill.test','1.0.0',repeat('a',64),'propose','["execute"]','agent.test','human.bryan','decision.test') then raise exception 'extra action admitted'; end if;
 -- Each subtransaction rolls back its deliberately invalid condition.
 foreach mutation in array array[
  'expires_at = now() - interval ''1 second'', issued_at = now() - interval ''2 minutes''',
  'revoked_at = now()',
  'verified_at = now() - interval ''6 minutes''',
  'verified_at = now() + interval ''1 minute'''
 ] loop
  begin
   -- Owner temporarily disables immutability to inspect each invalid stored state.
   alter table quirk_sync.github_approval_registry disable trigger github_approval_binding_guard;
   execute 'update quirk_sync.github_approval_registry set ' || mutation || ' where grant_id=''grant.test''';
   ok := quirk_sync.github_approval_allows('grant.test','skill','skill.test','1.0.0',repeat('a',64),'propose','["propose"]','agent.test','human.bryan','decision.test');
   if ok then raise exception 'invalid registry admitted: %',mutation; end if;
   raise exception sqlstate 'ZX001' using message='rollback test mutation';
  exception when sqlstate 'ZX001' then null;
  end;
 end loop;
 begin
  update quirk_sync.github_approval_registry set subject_digest=repeat('b',64) where grant_id='grant.test';
  raise exception 'immutable binding changed';
 exception when raise_exception then if sqlerrm <> 'GitHub approval binding is immutable' then raise; end if; end;
 update quirk_sync.github_approval_registry set revoked_at=now() where grant_id='grant.test';
 begin
  update quirk_sync.github_approval_registry set revoked_at=null where grant_id='grant.test';
  raise exception 'revocation removed';
 exception when raise_exception then if sqlerrm <> 'GitHub approval revocation is sticky' then raise; end if; end;
end $$;

-- Read back the role boundary including indirect membership and schema writes.
do $$ declare runtime_role text; begin
 foreach runtime_role in array array['service_role','anon','authenticated'] loop
  if pg_has_role(runtime_role, 'quirk_approval_ingestor','MEMBER')
   or has_table_privilege(runtime_role,'quirk_sync.github_approval_registry','INSERT')
   or has_table_privilege(runtime_role,'quirk_sync.github_approval_registry','UPDATE')
   or has_schema_privilege(runtime_role,'quirk_sync','CREATE') then
   raise exception 'runtime role crosses approval boundary: %',runtime_role;
  end if;
 end loop;
 if exists(select 1 from pg_roles where rolname='quirk_approval_ingestor' and (rolcanlogin or rolsuper or rolcreaterole or rolbypassrls)) then raise exception 'ingestor role has unsafe attributes'; end if;
end $$;
-- SESSION AUTHORIZATION is essential: SET ROLE alone keeps superuser
-- session_user and would permit assuming any role, invalidating this test.
set session authorization service_role;
do $$ begin
 begin
  insert into quirk_sync.github_approval_registry(grant_id) values ('fabricated');
  raise exception 'service role can manufacture approval';
 exception when insufficient_privilege then null; end;
 begin
  update quirk_sync.github_approval_registry set verified_at=now();
  raise exception 'service role can refresh approval';
 exception when insufficient_privilege then null; end;
 begin
  execute 'set local role quirk_approval_ingestor';
  raise exception 'service role can assume ingestor';
 exception when insufficient_privilege then null; end;
end $$;
reset session authorization;
-- Skill runtime ceilings differ from manifest admission ceilings.
insert into quirk_sync.github_approval_registry
(grant_id,subject_kind,subject_id,subject_version,subject_contract,subject_digest,authority_ceiling,allowed_actions,requested_by,approved_by,decision_ref,repository,request_commit,request_path,pr_number,review_id,reviewer_id,reviewer_login,issued_at,expires_at,verified_at)
select 'grant.bounded',subject_kind,subject_id,subject_version,subject_contract,subject_digest,'execute_bounded','["propose"]'::jsonb,requested_by,approved_by,decision_ref,repository,request_commit,request_path,pr_number,review_id,reviewer_id,reviewer_login,issued_at,expires_at,verified_at from quirk_sync.github_approval_registry where grant_id='grant.test';
do $$ begin
 if not quirk_sync.github_approval_allows('grant.bounded','skill','skill.test','1.0.0',repeat('a',64),'execute_bounded','["propose"]','agent.test','human.bryan','decision.test') then raise exception 'valid bounded skill denied'; end if;
 begin
  insert into quirk_sync.github_approval_registry
  (grant_id,subject_kind,subject_id,subject_version,subject_contract,subject_digest,authority_ceiling,allowed_actions,requested_by,approved_by,decision_ref,repository,request_commit,request_path,pr_number,review_id,reviewer_id,reviewer_login,issued_at,expires_at,verified_at)
  select 'grant.invalid-bounded','manifest',subject_id,subject_version,subject_contract,subject_digest,'execute_bounded',allowed_actions,requested_by,approved_by,decision_ref,repository,request_commit,request_path,pr_number,review_id,reviewer_id,reviewer_login,issued_at,expires_at,verified_at from quirk_sync.github_approval_registry where grant_id='grant.test';
  raise exception 'manifest accepted skill-only bounded ceiling';
 exception when check_violation then null; end;
end $$;

-- The isolated role can ingest/refresh/revoke but cannot alter immutable bindings.
set role quirk_approval_ingestor;
insert into quirk_sync.github_approval_registry
(grant_id,subject_kind,subject_id,subject_version,subject_contract,subject_digest,authority_ceiling,allowed_actions,requested_by,approved_by,decision_ref,repository,request_commit,request_path,pr_number,review_id,reviewer_id,reviewer_login,issued_at,expires_at,verified_at)
select 'grant.ingestor',subject_kind,subject_id,subject_version,subject_contract,subject_digest,authority_ceiling,allowed_actions,requested_by,approved_by,decision_ref,repository,request_commit,request_path,pr_number,review_id,reviewer_id,reviewer_login,issued_at,expires_at,verified_at from quirk_sync.github_approval_registry where grant_id='grant.test';
update quirk_sync.github_approval_registry set verified_at=statement_timestamp(),revoked_at=statement_timestamp() where grant_id='grant.ingestor';
do $$ begin
 begin
  update quirk_sync.github_approval_registry set subject_digest=repeat('c',64) where grant_id='grant.ingestor';
  raise exception 'ingestor can rewrite binding';
 exception when insufficient_privilege then null; end;
 begin
  update quirk_sync.github_approval_humans set principal='human.fabricated';
  raise exception 'ingestor can manufacture human allowlist';
 exception when insufficient_privilege then null; end;
end $$;
reset role;
-- Existing positive structural case gets its own test-only approval seed.
\ir manifest_activation_guard.cases.sql
select quirk_sync.assert_manifest_runtime_authorized('agent.sql-valid','9.9.1');
do $$ declare mutation text; begin
 foreach mutation in array array[
  'approved_by = ''human.fabricated''',
  'authority_grant_ref = ''grant.absent''',
  'content_hash = repeat(''b'',64), evaluated_content_hash = repeat(''b'',64)',
  'version = ''9.9.99''',
  'authority_ceiling = ''execute_protected''',
  'tools = ''["powerful_tool"]''::jsonb'
 ] loop
  begin
   execute 'update quirk_sync.manifest_registry set ' || mutation || ' where manifest_key=''agent.sql-valid''';
   raise exception 'unbound active manifest accepted: %',mutation;
  exception when raise_exception then
   if sqlerrm <> 'active manifest requires a matching fresh verified GitHub human approval' then raise; end if;
  end;
 end loop;
end $$;
update quirk_sync.github_approval_registry set revoked_at=now() where grant_id='grant.sql.valid';
do $$ begin
 begin
  perform quirk_sync.assert_manifest_runtime_authorized('agent.sql-valid','9.9.1');
  raise exception 'revoked active manifest remained usable';
 exception when raise_exception then if sqlerrm <> 'manifest runtime use requires current GitHub approval' then raise; end if; end;
end $$;
rollback;
