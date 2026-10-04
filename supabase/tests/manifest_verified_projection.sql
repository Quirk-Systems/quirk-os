-- Synthetic database projection cases, never evidence of actual GitHub consent.
-- PostgreSQL trusts the protected verifier role; these cases prove that lane's
-- privileges, payload/state checks, refusal rollback, and append-only history.
\set ON_ERROR_STOP on
begin;
create temp table projection_probe(p jsonb);
insert into projection_probe values (jsonb_build_object(
  'schema_version','verified-manifest-projection.v1','database_verification','projection','authority_effect','none',
  'expected_from_status','candidate',
  'manifest',jsonb_build_object(
    'schema_version','runtime-manifest.v2','manifest_key','agent.projection-synthetic','manifest_kind','agent',
    'version','0.0.1','status','active','requested_status','active',
    'canonical_uri','https://example.invalid/synthetic','content_hash',repeat('a',64),
    'authority_ceiling','propose','tools','[]'::jsonb,'domains','["sync"]'::jsonb,
    'inputs_schema_ref','synthetic-input','outputs_schema_ref','synthetic-output',
    'eval_refs','["synthetic-eval"]'::jsonb,'stop_conditions','["missing_authority"]'::jsonb,
    'metadata','{"fixture_only":true}'::jsonb,
    'admission',jsonb_build_object('decision','approved','decision_ref','decision.sql.synthetic',
      'authority_grant_ref','grant.sql.synthetic','requested_by','agent.synthetic','approved_by','human.synthetic',
      'evaluated_content_hash',repeat('a',64),'transition_ref','transition.sql.synthetic',
      'decided_at',clock_timestamp(),'evidence_refs','["synthetic-eval"]'::jsonb)),
  'approval',jsonb_build_object('schema_version','verified-manifest-approval.v1',
    'database_verification','projection','authority_effect','none','approved_by','human.synthetic',
    'authority_grant_ref','grant.sql.synthetic','verified_at',clock_timestamp(),
    'subject',jsonb_build_object('hash_profile','runtime-manifest-content.v1','content_hash',repeat('a',64),
                               'from_status','candidate','expires_at',clock_timestamp()+interval '10 minutes'))));
grant select,update on projection_probe to quirk_manifest_verifier;
grant select on projection_probe to service_role,anon,authenticated;
create function pg_temp.expect_refusal(command text, expected text) returns void language plpgsql as $$
begin
  begin
    execute command;
  exception when others then
    if position(expected in sqlerrm)>0 then
      raise notice 'Refused as expected: %',expected;
      return;
    end if;
    raise exception 'Wrong refusal; expected %, observed %',expected,sqlerrm;
  end;
  raise exception 'Forbidden crossing succeeded: %',command;
end $$;

-- RLS bypass does not bypass object privileges. JSON cannot assume the role.
set role service_role;
select pg_temp.expect_refusal(
  'select quirk_sync.apply_verified_manifest_projection(p) from projection_probe', 'permission denied');
select pg_temp.expect_refusal(
  'insert into quirk_sync.manifest_registry(manifest_key) values (''agent.forged'')', 'permission denied');
select pg_temp.expect_refusal('update quirk_sync.manifest_registry set status=''active''', 'permission denied');
select pg_temp.expect_refusal('delete from quirk_sync.manifest_registry', 'permission denied');
select pg_temp.expect_refusal(
  'insert into quirk_sync.manifest_projection_receipts(authority_grant_ref) values (''grant.forged'')', 'permission denied');
select pg_temp.expect_refusal('set role quirk_manifest_verifier', 'permission denied');
reset role;
set role anon;
select pg_temp.expect_refusal('select quirk_sync.apply_verified_manifest_projection(p) from projection_probe', 'permission denied');
reset role;
set role authenticated;
select pg_temp.expect_refusal('select quirk_sync.apply_verified_manifest_projection(p) from projection_probe', 'permission denied');
reset role;

-- Legitimate projection at the supported edge, then exact retry with no effects.
set role quirk_manifest_verifier;
select quirk_sync.apply_verified_manifest_projection(p) from projection_probe;
select quirk_sync.apply_verified_manifest_projection(p) from projection_probe;
do $$
begin
  if (select count(*) from quirk_sync.manifest_registry)<>1
     or (select count(*) from quirk_sync.manifest_projection_receipts)<>1
     or (select count(*) from quirk_sync.manifest_transition_ledger)<>1 then
    raise exception 'exact retry produced additional effects';
  end if;
end $$;
select pg_temp.expect_refusal(
  'select quirk_sync.apply_verified_manifest_projection(jsonb_set(p,''{manifest,metadata}'',''{"fixture_only":true,"unreviewed":true}'')) from projection_probe',
  'cannot be replayed');
select pg_temp.expect_refusal(
  'update quirk_sync.manifest_registry set metadata=''{}''', 'differs from verified projection');
select pg_temp.expect_refusal(
  'insert into quirk_sync.manifest_registry select (jsonb_populate_record(null::quirk_sync.manifest_registry, to_jsonb(m)||jsonb_build_object(''id'',gen_random_uuid(),''manifest_key'',''agent.fake'',''authority_grant_ref'',''grant.missing''))).* from quirk_sync.manifest_registry m',
  'requires a verifier projection receipt');

-- Freshness and optimistic state failure occur before persistent side effects.
select pg_temp.expect_refusal(
  'select quirk_sync.apply_verified_manifest_projection(jsonb_set(p,''{approval,verified_at}'',to_jsonb(clock_timestamp()-interval ''61 seconds''))) from projection_probe',
  'expired or stale');
select pg_temp.expect_refusal(
  'select quirk_sync.apply_verified_manifest_projection(jsonb_set(p,''{approval,subject,expires_at}'',to_jsonb(clock_timestamp()-interval ''1 second''))) from projection_probe',
  'expired or stale');
select pg_temp.expect_refusal(
  'select quirk_sync.apply_verified_manifest_projection(p #- ''{approval,verified_at}'') from projection_probe',
  'unsupported verified projection');
select pg_temp.expect_refusal(
  'update quirk_sync.manifest_projection_receipts set runtime_payload=''{}''', 'permission denied');
reset role;
select pg_temp.expect_refusal('update quirk_sync.manifest_projection_receipts set runtime_payload=''{}''', 'append-only');
select pg_temp.expect_refusal('delete from quirk_sync.manifest_projection_receipts', 'append-only');

-- A stop cannot change content or launder a new grant; it records no approver.
set role quirk_manifest_verifier;
select pg_temp.expect_refusal(
  'update quirk_sync.manifest_registry set status=''paused'',requested_status=''paused'',metadata=''{}''',
  'stopping may not alter');
update quirk_sync.manifest_registry set status='paused',requested_status='paused';
do $$
begin
  if (select count(*) from quirk_sync.manifest_transition_ledger where to_status='paused' and approved_by is null)<>1 then
    raise exception 'stop did not preserve a distinct history observation';
  end if;
end $$;
select pg_temp.expect_refusal(
  'select quirk_sync.apply_verified_manifest_projection(p) from projection_probe', 'cannot be replayed');

-- A new grant for the exact paused state may resume. Wrong prior state refuses.
update projection_probe set p=jsonb_set(jsonb_set(jsonb_set(jsonb_set(p,
  '{manifest,admission,authority_grant_ref}','"grant.sql.resume"'),
  '{approval,authority_grant_ref}','"grant.sql.resume"'),
  '{manifest,admission,transition_ref}','"transition.sql.resume"'),
  '{approval,verified_at}',to_jsonb(clock_timestamp()));
select pg_temp.expect_refusal(
  'select quirk_sync.apply_verified_manifest_projection(p) from projection_probe', 'prior state changed');
update projection_probe set p=jsonb_set(jsonb_set(p,'{expected_from_status}','"paused"'),
                                                  '{approval,subject,from_status}','"paused"');
select quirk_sync.apply_verified_manifest_projection(p) from projection_probe;
do $$
begin
  if (select count(*) from quirk_sync.manifest_registry where status='active')<>1
     or (select count(*) from quirk_sync.manifest_projection_receipts)<>2
     or (select count(*) from quirk_sync.manifest_transition_ledger)<>3 then
    raise exception 'resume or refusal rollback produced wrong effects';
  end if;
end $$;
update quirk_sync.manifest_registry set status='revoked',requested_status='revoked';
reset role;

-- The SQL guard is a projection and must not claim independent verification.
do $$
begin
  if (select prosecdef from pg_proc where oid='quirk_sync.apply_verified_manifest_projection(jsonb)'::regprocedure) then
    raise exception 'projection application became a privilege-escalating DEFINER';
  end if;
  if has_table_privilege('service_role','quirk_sync.manifest_registry','INSERT,UPDATE,DELETE') then
    raise exception 'broad service role retained registry writes';
  end if;
end $$;
rollback;
