-- Candidate-only private projection. Do not add this schema to Data API exposure.
-- No role memberships are assigned here; activation/ingestor credentials are a
-- separately governed deployment decision. No canonical or action grants exist.
begin;

create schema engineering_candidate;
revoke all on schema engineering_candidate from public, anon, authenticated, service_role;
create role engineering_candidate_writer nologin noinherit nobypassrls;
grant usage on schema engineering_candidate to authenticated, engineering_candidate_writer;
alter default privileges in schema engineering_candidate revoke all on tables from public, anon, authenticated, service_role;
alter default privileges in schema engineering_candidate revoke execute on functions from public;

-- Administratively maintained visibility, not writable by the ingestion role.
create table engineering_candidate.tenant_readers (
  tenant_id text not null,
  user_id uuid not null,
  primary key (tenant_id, user_id)
);
create table engineering_candidate.resource_readers (
  tenant_id text not null,
  object_id text not null,
  user_id uuid not null,
  primary key (tenant_id, object_id, user_id),
  foreign key (tenant_id, user_id) references engineering_candidate.tenant_readers
);
create table engineering_candidate.object_versions (
  tenant_id text not null,
  object_id text not null check (length(object_id) > 0),
  digest text not null check (length(digest) > 0),
  kind text not null check (kind in ('artifact','claim','evidence','run','action','judgment','principal','policy')),
  visibility text not null default 'restricted' check (visibility in ('tenant','restricted')),
  recorded_at timestamptz not null default statement_timestamp(),
  primary key (tenant_id, object_id, digest)
);
-- A disposable current-version index; observations and object versions stay intact.
create table engineering_candidate.object_heads (
  tenant_id text not null,
  object_id text not null,
  digest text not null,
  primary key (tenant_id, object_id),
  foreign key (tenant_id, object_id, digest) references engineering_candidate.object_versions
);
create table engineering_candidate.assertions (
  tenant_id text not null,
  assertion_id text not null check (length(assertion_id) > 0),
  subject_id text not null,
  subject_digest text not null,
  predicate text not null check (predicate in ('supported_by','contradicted_by','depends_on','blocked_by','produced','prefers')),
  object_id text not null,
  object_digest text not null,
  source_ref text not null,
  source_digest text not null,
  observer text not null check (length(observer) > 0),
  observed_at timestamptz not null,
  valid_from timestamptz not null,
  valid_until timestamptz,
  status text not null check (status in ('observed','declared','retracted')),
  supersedes text,
  recorded_at timestamptz not null default statement_timestamp(),
  primary key (tenant_id, assertion_id),
  foreign key (tenant_id, subject_id, subject_digest) references engineering_candidate.object_versions,
  foreign key (tenant_id, object_id, object_digest) references engineering_candidate.object_versions,
  foreign key (tenant_id, source_ref, source_digest) references engineering_candidate.object_versions,
  foreign key (tenant_id, supersedes) references engineering_candidate.assertions,
  check (valid_until is null or valid_until > valid_from),
  check (recorded_at >= observed_at),
  check (supersedes is null or supersedes <> assertion_id)
);
create index assertions_subject on engineering_candidate.assertions(tenant_id, subject_id, subject_digest, predicate);
create index assertions_dependency on engineering_candidate.assertions(tenant_id, object_id, predicate);
create index assertions_source on engineering_candidate.assertions(tenant_id, source_ref);
create index assertions_supersedes on engineering_candidate.assertions(tenant_id, supersedes);

alter table engineering_candidate.tenant_readers enable row level security;
alter table engineering_candidate.tenant_readers force row level security;
alter table engineering_candidate.resource_readers enable row level security;
alter table engineering_candidate.resource_readers force row level security;
alter table engineering_candidate.object_versions enable row level security;
alter table engineering_candidate.object_versions force row level security;
alter table engineering_candidate.object_heads enable row level security;
alter table engineering_candidate.object_heads force row level security;
alter table engineering_candidate.assertions enable row level security;
alter table engineering_candidate.assertions force row level security;

create policy read_own_tenants on engineering_candidate.tenant_readers for select to authenticated
using (user_id = (select auth.uid()));
create policy read_own_resources on engineering_candidate.resource_readers for select to authenticated
using (user_id = (select auth.uid()));
create policy read_visible_versions on engineering_candidate.object_versions for select to authenticated
using (
  exists (select 1 from engineering_candidate.tenant_readers r where r.tenant_id = object_versions.tenant_id)
  and (visibility = 'tenant' or exists (
    select 1 from engineering_candidate.resource_readers r
    where r.tenant_id = object_versions.tenant_id and r.object_id = object_versions.object_id
  ))
);
create policy read_visible_heads on engineering_candidate.object_heads for select to authenticated
using (exists (
  select 1 from engineering_candidate.object_versions v where v.tenant_id = object_heads.tenant_id
  and v.object_id = object_heads.object_id and v.digest = object_heads.digest
));
create policy read_visible_assertions on engineering_candidate.assertions for select to authenticated
using (
  exists (select 1 from engineering_candidate.object_versions v where v.tenant_id = assertions.tenant_id and v.object_id = assertions.subject_id and v.digest = assertions.subject_digest)
  and exists (select 1 from engineering_candidate.object_versions v where v.tenant_id = assertions.tenant_id and v.object_id = assertions.object_id and v.digest = assertions.object_digest)
  and exists (select 1 from engineering_candidate.object_versions v where v.tenant_id = assertions.tenant_id and v.object_id = assertions.source_ref and v.digest = assertions.source_digest)
);
create policy writer_read_versions on engineering_candidate.object_versions for select to engineering_candidate_writer using (true);
create policy writer_insert_versions on engineering_candidate.object_versions for insert to engineering_candidate_writer with check (true);
create policy writer_read_heads on engineering_candidate.object_heads for select to engineering_candidate_writer using (true);
create policy writer_insert_heads on engineering_candidate.object_heads for insert to engineering_candidate_writer with check (true);
create policy writer_update_heads on engineering_candidate.object_heads for update to engineering_candidate_writer using (true) with check (true);
create policy writer_read_assertions on engineering_candidate.assertions for select to engineering_candidate_writer using (true);
create policy writer_insert_assertions on engineering_candidate.assertions for insert to engineering_candidate_writer with check (true);

create function engineering_candidate.reject_history_mutation() returns trigger
language plpgsql security invoker set search_path = '' as $$
begin
  raise exception 'engineering history is append-only' using errcode = '55000';
end;
$$;
create trigger immutable_assertions before update or delete or truncate on engineering_candidate.assertions
for each statement execute function engineering_candidate.reject_history_mutation();
create trigger immutable_versions before update or delete or truncate on engineering_candidate.object_versions
for each statement execute function engineering_candidate.reject_history_mutation();

create function engineering_candidate.validate_assertion() returns trigger
language plpgsql security invoker set search_path = '' as $$
declare subject_kind text; prior engineering_candidate.assertions%rowtype;
begin
  -- Ingestion time is observed by this database; client-provided backdating is ignored.
  new.recorded_at := statement_timestamp();
  select kind into subject_kind from engineering_candidate.object_versions
  where tenant_id = new.tenant_id and object_id = new.subject_id and digest = new.subject_digest;
  if new.predicate = 'produced' and subject_kind not in ('run','action') then
    raise exception 'produced requires run or action subject' using errcode = '23514';
  end if;
  if new.predicate = 'prefers' and subject_kind not in ('judgment','principal') then
    raise exception 'prefers requires judgment or principal subject' using errcode = '23514';
  end if;
  if new.supersedes is not null then
    select * into prior from engineering_candidate.assertions where tenant_id = new.tenant_id and assertion_id = new.supersedes;
    if not found or prior.assertion_id = new.assertion_id or
       (prior.subject_id, prior.predicate, prior.object_id, prior.observer) is distinct from
       (new.subject_id, new.predicate, new.object_id, new.observer) or prior.observed_at > new.observed_at then
      raise exception 'invalid supersession identity or chronology' using errcode = '23514';
    end if;
  end if;
  return new;
end;
$$;
create trigger validate_assertion before insert on engineering_candidate.assertions
for each row execute function engineering_candidate.validate_assertion();

-- Exact current-version support/contradiction candidates, never an authority view.
-- SECURITY INVOKER preserves tenant and endpoint/source visibility through joins.
create view engineering_candidate.current_evidence with (security_invoker = true) as
select a.* from engineering_candidate.assertions a
join engineering_candidate.object_heads s on (s.tenant_id,s.object_id,s.digest) = (a.tenant_id,a.subject_id,a.subject_digest)
join engineering_candidate.object_heads o on (o.tenant_id,o.object_id,o.digest) = (a.tenant_id,a.object_id,a.object_digest)
join engineering_candidate.object_heads r on (r.tenant_id,r.object_id,r.digest) = (a.tenant_id,a.source_ref,a.source_digest)
where a.predicate in ('supported_by','contradicted_by') and a.status = 'observed'
  and a.observed_at <= statement_timestamp() and a.recorded_at <= statement_timestamp()
  and a.valid_from <= statement_timestamp() and (a.valid_until is null or a.valid_until > statement_timestamp())
  and not exists (
    select 1 from engineering_candidate.assertions replacement
    where replacement.tenant_id = a.tenant_id and replacement.supersedes = a.assertion_id
    and replacement.status in ('observed','retracted')
    and replacement.observed_at <= statement_timestamp() and replacement.recorded_at <= statement_timestamp()
    and replacement.valid_from <= statement_timestamp()
  );

-- RLS applies at every expansion. Conservatively visits historical dependencies;
-- affected means recheck, not that the dependent conclusion is currently false.
create function engineering_candidate.impact_of(p_tenant text, p_object text, p_max_depth integer default 8)
returns table(object_id text, depth integer)
language plpgsql stable security invoker set search_path = '' as $$
declare frontier text[] := array[p_object]; visited text[] := array[p_object]; next_frontier text[];
        level integer; candidate record; count_seen integer := 0;
begin
  if p_max_depth is null or p_max_depth < 0 or p_max_depth > 32 then
    raise exception 'max_depth must be between 0 and 32' using errcode = '22023';
  end if;
  if not exists (select 1 from engineering_candidate.object_versions v where v.tenant_id = p_tenant and v.object_id = p_object) then return; end if;
  for level in 1..p_max_depth loop
    next_frontier := array[]::text[];
    for candidate in
      select distinct a.subject_id from engineering_candidate.assertions a
      where a.tenant_id = p_tenant and a.predicate in ('supported_by','contradicted_by','depends_on','blocked_by')
      and (a.object_id = any(frontier) or a.source_ref = any(frontier))
      and not (a.subject_id = any(visited)) order by a.subject_id limit 1000
    loop
      visited := array_append(visited, candidate.subject_id);
      next_frontier := array_append(next_frontier, candidate.subject_id);
      object_id := candidate.subject_id; depth := level; return next;
      count_seen := count_seen + 1;
      if count_seen >= 1000 then return; end if;
    end loop;
    frontier := next_frontier;
    exit when cardinality(frontier) = 0;
  end loop;
end;
$$;

revoke all on all tables in schema engineering_candidate from public, anon, authenticated, service_role;
revoke all on all functions in schema engineering_candidate from public, anon, authenticated, service_role;
grant select on engineering_candidate.tenant_readers, engineering_candidate.resource_readers,
  engineering_candidate.object_versions, engineering_candidate.object_heads,
  engineering_candidate.assertions, engineering_candidate.current_evidence to authenticated;
grant select, insert on engineering_candidate.object_versions, engineering_candidate.assertions to engineering_candidate_writer;
grant select, insert, update on engineering_candidate.object_heads to engineering_candidate_writer;
grant select on engineering_candidate.current_evidence to engineering_candidate_writer;
grant execute on function engineering_candidate.impact_of(text,text,integer) to authenticated, engineering_candidate_writer;
-- Trigger functions run under the caller; trigger invocation does not require a
-- public EXECUTE grant. The schema/table owner can still alter or drop triggers.
comment on schema engineering_candidate is 'Private candidate observation projection; no action grants, admission, or production activation. Owner/DBA can alter storage; append-only enforcement applies to ordinary roles.';
commit;
