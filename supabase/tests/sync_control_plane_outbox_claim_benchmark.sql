-- Transactional benchmark fixture for quirk_sync.claim_projection_outbox.
-- Apply relevant sync-control-plane migrations first, then run this script.
begin;

-- Realistic state mixture: pending, failed, actively leased, expired leased,
-- succeeded, dead-lettered, and future-available rows.
do $$
declare
  v_object uuid;
  v_explain_line text;
  v_has_claim_index boolean := false;
  v_has_sort boolean := false;
  v_claimed integer;
  v_non_ready integer;
  v_total integer;
begin
  insert into quirk_sync.object_registry (object_key, kind, status)
  values ('test.outbox.benchmark', 'test', 'candidate')
  returning id into v_object;

  insert into quirk_sync.projection_outbox (
    object_id, destination_platform, operation, payload, payload_hash,
    idempotency_key, authority_ref, status, attempts, max_attempts,
    available_at, leased_until, created_at
  )
  select
    v_object,
    'notion',
    'rebuild',
    jsonb_build_object('fixture', 'pending-ready', 'n', g),
    repeat('a', 64),
    format('bench:pending-ready:%s', g),
    'grant.benchmark',
    'pending',
    0,
    5,
    now() - make_interval(secs => (g % 600)),
    null,
    now() - make_interval(days => 1)
  from generate_series(1, 3500) as g;

  insert into quirk_sync.projection_outbox (
    object_id, destination_platform, operation, payload, payload_hash,
    idempotency_key, authority_ref, status, attempts, max_attempts,
    available_at, leased_until, created_at
  )
  select
    v_object,
    'airtable',
    'update',
    jsonb_build_object('fixture', 'failed-ready', 'n', g),
    repeat('b', 64),
    format('bench:failed-ready:%s', g),
    'grant.benchmark',
    'failed',
    1,
    5,
    now() - make_interval(secs => (g % 900)),
    null,
    now() - make_interval(days => 1)
  from generate_series(1, 2200) as g;

  insert into quirk_sync.projection_outbox (
    object_id, destination_platform, operation, payload, payload_hash,
    idempotency_key, authority_ref, status, attempts, max_attempts,
    available_at, leased_until, created_at
  )
  select
    v_object,
    'vercel',
    'update',
    jsonb_build_object('fixture', 'leased-active', 'n', g),
    repeat('c', 64),
    format('bench:leased-active:%s', g),
    'grant.benchmark',
    'leased',
    2,
    5,
    now() - make_interval(secs => (g % 500)),
    now() + make_interval(secs => 120 + (g % 180)),
    now() - make_interval(hours => 6)
  from generate_series(1, 2000) as g;

  insert into quirk_sync.projection_outbox (
    object_id, destination_platform, operation, payload, payload_hash,
    idempotency_key, authority_ref, status, attempts, max_attempts,
    available_at, leased_until, created_at
  )
  select
    v_object,
    'google_drive',
    'update',
    jsonb_build_object('fixture', 'leased-expired', 'n', g),
    repeat('d', 64),
    format('bench:leased-expired:%s', g),
    'grant.benchmark',
    'leased',
    3,
    5,
    now() - make_interval(secs => (g % 700)),
    now() - make_interval(secs => (10 + (g % 120))),
    now() - make_interval(hours => 8)
  from generate_series(1, 1800) as g;

  insert into quirk_sync.projection_outbox (
    object_id, destination_platform, operation, payload, payload_hash,
    idempotency_key, authority_ref, status, attempts, max_attempts,
    available_at, leased_until, completed_at, created_at
  )
  select
    v_object,
    'notion',
    'update',
    jsonb_build_object('fixture', 'succeeded', 'n', g),
    repeat('e', 64),
    format('bench:succeeded:%s', g),
    'grant.benchmark',
    'succeeded',
    1,
    5,
    now() - make_interval(days => 1),
    null,
    now() - make_interval(hours => 2),
    now() - make_interval(days => 2)
  from generate_series(1, 1300) as g;

  insert into quirk_sync.projection_outbox (
    object_id, destination_platform, operation, payload, payload_hash,
    idempotency_key, authority_ref, status, attempts, max_attempts,
    available_at, leased_until, dead_lettered_at, created_at
  )
  select
    v_object,
    'airtable',
    'retire',
    jsonb_build_object('fixture', 'dead-lettered', 'n', g),
    repeat('f', 64),
    format('bench:dead-lettered:%s', g),
    'grant.benchmark',
    'dead_letter',
    5,
    5,
    now() - make_interval(days => 2),
    null,
    now() - make_interval(days => 1),
    now() - make_interval(days => 3)
  from generate_series(1, 900) as g;

  insert into quirk_sync.projection_outbox (
    object_id, destination_platform, operation, payload, payload_hash,
    idempotency_key, authority_ref, status, attempts, max_attempts,
    available_at, leased_until, created_at
  )
  select
    v_object,
    'notion',
    'create',
    jsonb_build_object('fixture', 'pending-future', 'n', g),
    repeat('0', 64),
    format('bench:pending-future:%s', g),
    'grant.benchmark',
    'pending',
    0,
    5,
    now() + make_interval(secs => 180 + (g % 3600)),
    null,
    now() - make_interval(hours => 1)
  from generate_series(1, 1800) as g;

  insert into quirk_sync.projection_outbox (
    object_id, destination_platform, operation, payload, payload_hash,
    idempotency_key, authority_ref, status, attempts, max_attempts,
    available_at, leased_until, created_at
  )
  select
    v_object,
    'vercel',
    'create',
    jsonb_build_object('fixture', 'failed-future', 'n', g),
    repeat('1', 64),
    format('bench:failed-future:%s', g),
    'grant.benchmark',
    'failed',
    4,
    5,
    now() + make_interval(secs => 120 + (g % 2400)),
    null,
    now() - make_interval(hours => 1)
  from generate_series(1, 700) as g;

  analyze quirk_sync.projection_outbox;

  for v_explain_line in execute $$
    explain (analyze, buffers)
    select id
    from quirk_sync.projection_outbox
    where status in ('pending','failed','leased')
      and available_at <= now()
      and attempts < max_attempts
      and (leased_until is null or leased_until < now())
    order by available_at, id
    for update skip locked
    limit 250
  $$
  loop
    raise notice '%', v_explain_line;
    if v_explain_line ilike '%projection_outbox_claim_ready_idx%' then
      v_has_claim_index := true;
    end if;
    if v_explain_line ~ '^\s*Sort\s' then
      v_has_sort := true;
    end if;
  end loop;

  if not v_has_claim_index then
    raise exception 'benchmark expected claim query to use projection_outbox_claim_ready_idx';
  end if;
  if v_has_sort then
    raise exception 'benchmark expected index-ordered claim path without explicit Sort node';
  end if;

  select count(*) into v_claimed
  from quirk_sync.claim_projection_outbox('worker.sql-benchmark', 250, 45);
  if v_claimed <> 250 then
    raise exception 'benchmark expected 250 claimed rows, got %', v_claimed;
  end if;

  select count(*) into v_non_ready
  from quirk_sync.projection_outbox
  where lease_owner = 'worker.sql-benchmark'
    and (
      status <> 'leased'
      or available_at > now()
      or attempts > max_attempts
    );
  if v_non_ready <> 0 then
    raise exception 'benchmark claimed rows outside readiness predicate';
  end if;

  select count(*) into v_total from quirk_sync.projection_outbox;
  if v_total < 14000 then
    raise exception 'benchmark fixture too small (% rows); expected >= 14000', v_total;
  end if;
end $$;

rollback;

-- Manual EXPLAIN invocation for local investigation:
-- EXPLAIN (ANALYZE, BUFFERS)
-- SELECT id
-- FROM quirk_sync.projection_outbox
-- WHERE status IN ('pending','failed','leased')
--   AND available_at <= now()
--   AND attempts < max_attempts
--   AND (leased_until IS NULL OR leased_until < now())
-- ORDER BY available_at, id
-- FOR UPDATE SKIP LOCKED
-- LIMIT 250;
