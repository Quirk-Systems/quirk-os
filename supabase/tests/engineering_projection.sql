-- Run after the engineering candidate migration in an isolated local database.
-- Requires Supabase auth.uid()/roles, or the explicit PGlite harness stubs.
-- Raises on every failed check. All fixtures and temporary grants roll back.
begin;
insert into engineering_candidate.tenant_readers values
 ('t1','00000000-0000-0000-0000-000000000001'),
 ('t1','00000000-0000-0000-0000-000000000002'),
 ('t2','00000000-0000-0000-0000-000000000003');
insert into engineering_candidate.resource_readers values
 ('t1','secret','00000000-0000-0000-0000-000000000002');

set local role engineering_candidate_writer;
insert into engineering_candidate.object_versions(tenant_id,object_id,digest,kind,visibility) values
 ('t1','candidate','c1','artifact','tenant'), ('t1','proof','p1','evidence','tenant'),
 ('t1','proof','p2','evidence','tenant'), ('t1','secret','s1','evidence','restricted'),
 ('t1','dependent','d1','claim','tenant'), ('t1','judgment','j1','judgment','tenant'),
 ('t2','foreign','f1','artifact','tenant');
insert into engineering_candidate.object_heads values
 ('t1','candidate','c1'),('t1','proof','p1'),('t1','secret','s1'),
 ('t1','dependent','d1'),('t1','judgment','j1'),('t2','foreign','f1');
insert into engineering_candidate.assertions
 (tenant_id,assertion_id,subject_id,subject_digest,predicate,object_id,object_digest,source_ref,source_digest,observer,observed_at,valid_from,valid_until,status)
values
 ('t1','support','candidate','c1','supported_by','proof','p1','proof','p1','host',now()-interval '1 hour',now()-interval '1 hour',null,'observed'),
 ('t1','contradiction','candidate','c1','contradicted_by','proof','p1','proof','p1','host',now()-interval '1 hour',now()-interval '1 hour',null,'observed'),
 ('t1','expired','candidate','c1','supported_by','proof','p1','proof','p1','host',now()-interval '2 hour',now()-interval '2 hour',now()-interval '1 hour','observed'),
 ('t1','declared','candidate','c1','supported_by','proof','p1','proof','p1','host',now()-interval '1 hour',now()-interval '1 hour',null,'declared'),
 ('t1','hidden','candidate','c1','supported_by','proof','p1','secret','s1','host',now()-interval '1 hour',now()-interval '1 hour',null,'observed'),
 ('t1','depends','dependent','d1','depends_on','candidate','c1','proof','p1','host',now()-interval '1 hour',now()-interval '1 hour',null,'observed'),
 ('t1','cycle','proof','p1','depends_on','dependent','d1','proof','p1','host',now()-interval '1 hour',now()-interval '1 hour',null,'observed'),
 ('t1','preference','judgment','j1','prefers','candidate','c1','proof','p1','human',now()-interval '1 hour',now()-interval '1 hour',null,'observed');

do $$ begin
  -- 1: Ingestor cannot change visibility memberships or acquire execution authority.
  begin insert into engineering_candidate.tenant_readers values ('t3','00000000-0000-0000-0000-000000000001'); raise exception 'writer granted membership'; exception when insufficient_privilege then null; end;
  begin update engineering_candidate.assertions set status='observed'; raise exception 'writer rewrote history'; exception when insufficient_privilege then null; end;
  begin delete from engineering_candidate.object_versions; raise exception 'writer deleted versions'; exception when insufficient_privilege then null; end;
  -- 2: Invalid content edges and type laundering are rejected at insertion.
  begin
    insert into engineering_candidate.assertions select tenant_id,'grant',subject_id,subject_digest,'may_perform',object_id,object_digest,source_ref,source_digest,observer,observed_at,valid_from,valid_until,status,null,recorded_at from engineering_candidate.assertions where assertion_id='preference';
    raise exception 'preference minted authority';
  exception when check_violation then null; end;
  begin
    insert into engineering_candidate.assertions select tenant_id,'wrong-type',subject_id,subject_digest,'produced',object_id,object_digest,source_ref,source_digest,observer,observed_at,valid_from,valid_until,status,null,recorded_at from engineering_candidate.assertions where assertion_id='support';
    raise exception 'untyped produced relationship';
  exception when check_violation then null; end;
  -- 3: Composite FKs reject a cross-tenant endpoint and a fabricated digest.
  begin
    insert into engineering_candidate.assertions select tenant_id,'cross-tenant',subject_id,subject_digest,predicate,'foreign','f1',source_ref,source_digest,observer,observed_at,valid_from,valid_until,status,null,recorded_at from engineering_candidate.assertions where assertion_id='support';
    raise exception 'cross tenant endpoint accepted';
  exception when foreign_key_violation then null; end;
  begin
    insert into engineering_candidate.assertions select tenant_id,'false-digest',subject_id,subject_digest,predicate,object_id,object_digest,source_ref,'fabricated',observer,observed_at,valid_from,valid_until,status,null,recorded_at from engineering_candidate.assertions where assertion_id='support';
    raise exception 'unregistered source digest accepted';
  exception when foreign_key_violation then null; end;
end $$;
reset role;

set local role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000001',true);
do $$ begin
  -- 4: Tenant isolation and hidden source prevent row and relationship leakage.
  if (select count(*) from engineering_candidate.object_versions) <> 5 then raise exception 'object visibility leaked'; end if;
  if exists(select 1 from engineering_candidate.assertions where assertion_id='hidden') then raise exception 'hidden provenance leaked'; end if;
  if (select count(*) from engineering_candidate.tenant_readers) <> 1 then raise exception 'tenant membership leaked'; end if;
  -- 5: Observed support and contradiction coexist; expiry/declaration are excluded.
  if (select count(*) from engineering_candidate.current_evidence) <> 2 then raise exception 'current support filtering failed'; end if;
  if not exists(select 1 from engineering_candidate.current_evidence where predicate='contradicted_by') then raise exception 'contradiction lost'; end if;
  -- 6: RLS applies through bounded traversal and cycles terminate.
  if (select count(*) from engineering_candidate.impact_of('t1','proof',1)) <> 2 then raise exception 'depth-one impact failed'; end if;
  if (select count(*) from engineering_candidate.impact_of('t1','proof',8)) <> 2 then raise exception 'cycle traversal failed'; end if;
  if exists(select 1 from engineering_candidate.impact_of('t1','secret',8)) then raise exception 'hidden source traversal leaked'; end if;
  if exists(select 1 from engineering_candidate.impact_of('t2','foreign',8)) then raise exception 'tenant traversal leaked'; end if;
  if exists(select 1 from engineering_candidate.impact_of('t1','proof',0)) then raise exception 'zero depth traversed'; end if;
  begin perform * from engineering_candidate.impact_of('t1','proof',33); raise exception 'depth bound bypassed'; exception when invalid_parameter_value then null; end;
  -- 7: Readers cannot alter state, append claimed observations, or grant access.
  begin insert into engineering_candidate.tenant_readers values ('t2','00000000-0000-0000-0000-000000000001'); raise exception 'reader self granted'; exception when insufficient_privilege then null; end;
  begin insert into engineering_candidate.assertions select * from engineering_candidate.assertions limit 1; raise exception 'reader forged observation'; exception when insufficient_privilege then null; end;
  begin update engineering_candidate.object_heads set digest='p2' where object_id='proof'; raise exception 'reader advanced head'; exception when insufficient_privilege then null; end;
  if pg_has_role('authenticated','engineering_candidate_writer','MEMBER') then raise exception 'reader is writer member'; end if;
end $$;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000002',true);
do $$ begin
  -- 8: Explicit resource reader can see source-backed assertion.
  if (select count(*) from engineering_candidate.current_evidence) <> 3 then raise exception 'resource reader cannot see own evidence'; end if;
end $$;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000003',true);
do $$ begin
  -- 9: Other tenant sees own object only and no first-tenant assertions.
  if (select count(*) from engineering_candidate.object_versions) <> 1 then raise exception 'other tenant isolation failed'; end if;
  if exists(select 1 from engineering_candidate.assertions) then raise exception 'other tenant saw assertion'; end if;
end $$;
reset role;

set local role engineering_candidate_writer;
update engineering_candidate.object_heads set digest='p2' where tenant_id='t1' and object_id='proof';
reset role;
set local role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000001',true);
do $$ begin
  -- 10: Changing the current source/endpoint digest invalidates evidence, retains history.
  if exists(select 1 from engineering_candidate.current_evidence) then raise exception 'stale evidence stayed current'; end if;
  if (select count(*) from engineering_candidate.assertions) <> 7 then raise exception 'history lost after digest change'; end if;
end $$;
reset role;

-- 11: Append-only triggers still enforce history if ordinary write privileges are accidentally added.
grant update, delete, truncate on engineering_candidate.assertions to engineering_candidate_writer;
create policy test_writer_update on engineering_candidate.assertions for update to engineering_candidate_writer using(true) with check(true);
create policy test_writer_delete on engineering_candidate.assertions for delete to engineering_candidate_writer using(true);
set local role engineering_candidate_writer;
do $$ begin
  begin update engineering_candidate.assertions set status='retracted'; raise exception 'append-only update bypassed'; exception when object_not_in_prerequisite_state then null; end;
  begin delete from engineering_candidate.assertions; raise exception 'append-only delete bypassed'; exception when object_not_in_prerequisite_state then null; end;
  begin truncate engineering_candidate.assertions; raise exception 'append-only truncate bypassed'; exception when object_not_in_prerequisite_state then null; end;
end $$;
reset role;

-- 12: All candidate tables force RLS; no definer function/default public execution or authority table.
do $$ begin
  if exists(select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='engineering_candidate' and c.relkind='r' and (not c.relrowsecurity or not c.relforcerowsecurity)) then raise exception 'RLS missing'; end if;
  if exists(select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='engineering_candidate' and p.prosecdef) then raise exception 'definer bypass'; end if;
  if has_schema_privilege('anon','engineering_candidate','USAGE') then raise exception 'anonymous schema access'; end if;
  if has_schema_privilege('service_role','engineering_candidate','USAGE') then raise exception 'implicit service role access'; end if;
  if has_function_privilege('anon','engineering_candidate.impact_of(text,text,integer)','EXECUTE') then raise exception 'public function execution'; end if;
end $$;
-- 13: Supersession preserves history and respects when replacement becomes effective.
set local role engineering_candidate_writer;
update engineering_candidate.object_heads set digest='p1' where tenant_id='t1' and object_id='proof';
insert into engineering_candidate.assertions
select tenant_id,'future-replacement',subject_id,subject_digest,predicate,object_id,object_digest,source_ref,source_digest,observer,observed_at,now()+interval '1 day',null,status,'support',recorded_at
from engineering_candidate.assertions where assertion_id='support';
reset role;
set local role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000001',true);
do $$ begin
  if not exists(select 1 from engineering_candidate.current_evidence where assertion_id='support') then raise exception 'future replacement erased current evidence'; end if;
end $$;
reset role;
set local role engineering_candidate_writer;
insert into engineering_candidate.assertions
select tenant_id,'current-replacement',subject_id,subject_digest,predicate,object_id,object_digest,source_ref,source_digest,observer,observed_at,valid_from,null,status,'support',recorded_at
from engineering_candidate.assertions where assertion_id='support';
do $$ begin
  begin
    insert into engineering_candidate.assertions select tenant_id,'bad-replacement',subject_id,subject_digest,'contradicted_by',object_id,object_digest,source_ref,source_digest,observer,observed_at,valid_from,null,status,'support',recorded_at from engineering_candidate.assertions where assertion_id='support';
    raise exception 'supersession crossed predicates';
  exception when check_violation then null; end;
end $$;
reset role;
set local role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000001',true);
do $$ begin
  if exists(select 1 from engineering_candidate.current_evidence where assertion_id='support') then raise exception 'superseded evidence current'; end if;
  if not exists(select 1 from engineering_candidate.current_evidence where assertion_id='current-replacement') then raise exception 'replacement missing'; end if;
  if not exists(select 1 from engineering_candidate.assertions where assertion_id='support') then raise exception 'supersession erased history'; end if;
end $$;
reset role;

-- 14: Changing provenance source alone invalidates its support, independently of edge endpoints.
set local role engineering_candidate_writer;
insert into engineering_candidate.object_versions(tenant_id,object_id,digest,kind,visibility) values ('t1','secret','s2','evidence','restricted');
update engineering_candidate.object_heads set digest='s2' where tenant_id='t1' and object_id='secret';
reset role;
set local role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000002',true);
do $$ begin
  if exists(select 1 from engineering_candidate.current_evidence where assertion_id='hidden') then raise exception 'stale separate provenance remained current'; end if;
  if not exists(select 1 from engineering_candidate.assertions where assertion_id='hidden') then raise exception 'stale separate provenance history lost'; end if;
end $$;
reset role;
select '14 SQL behavior groups passed' as result;
rollback;
