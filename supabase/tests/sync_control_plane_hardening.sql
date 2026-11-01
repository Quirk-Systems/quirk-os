-- Transactional proof suite for Quirk Sync Control Plane v0.2.
-- A successful run returns no error and rolls back every test row.

begin;

-- Manifest activation guard cases. Kept in their own file so CI can run them
-- alone against a freshly migrated database: the cases below this include
-- depend on seed rows no migration creates, and the projection-rebuild case at
-- the end of this file fails on a clean schema for that reason. `\ir` resolves
-- relative to this file, and the included file carries no transaction control,
-- so these cases roll back with the rest of this suite.
\ir manifest_activation_guard.cases.sql

-- Duplicate vendor identity must be rejected.
do $$
declare
  v_object_one uuid;
  v_object_two uuid;
  v_rejected boolean := false;
begin
  insert into quirk_sync.object_registry (object_key, kind, status)
  values ('test.object.one', 'test', 'candidate') returning id into v_object_one;
  insert into quirk_sync.object_registry (object_key, kind, status)
  values ('test.object.two', 'test', 'candidate') returning id into v_object_two;

  insert into quirk_sync.source_bindings (
    object_id, platform, external_id, authority_class, sync_direction, state, binding_key
  ) values (
    v_object_one, 'github', 'duplicate/sql-id', 'canonical', 'pull', 'candidate', 'binding.github.sql-one'
  );

  begin
    insert into quirk_sync.source_bindings (
      object_id, platform, external_id, authority_class, sync_direction, state, binding_key
    ) values (
      v_object_two, 'github', 'duplicate/sql-id', 'canonical', 'pull', 'candidate', 'binding.github.sql-two'
    );
  exception when unique_violation then
    v_rejected := true;
  end;
  if not v_rejected then
    raise exception 'SCP-003 failed: duplicate external identity was not rejected';
  end if;
end $$;

-- Receipts must be idempotent and append-only.
do $$
declare
  v_receipt_id uuid;
  v_mutation_rejected boolean := false;
begin
  insert into quirk_sync.run_receipts (
    receipt_key, idempotency_key, run_type, status,
    input_refs, output_refs, evidence_refs, completed_at, receipt_hash
  ) values (
    'receipt.sql-proof', 'receipt:sql-proof:1', 'validate', 'succeeded',
    '[]'::jsonb, '[]'::jsonb, '["sql://proof"]'::jsonb, now(), repeat('e', 64)
  ) returning id into v_receipt_id;

  insert into quirk_sync.run_receipts (
    receipt_key, idempotency_key, run_type, status,
    input_refs, output_refs, evidence_refs, completed_at, receipt_hash
  ) values (
    'receipt.sql-proof-duplicate', 'receipt:sql-proof:1', 'validate', 'succeeded',
    '[]'::jsonb, '[]'::jsonb, '["sql://proof"]'::jsonb, now(), repeat('f', 64)
  ) on conflict (idempotency_key) do nothing;

  if (select count(*) from quirk_sync.run_receipts where idempotency_key = 'receipt:sql-proof:1') <> 1 then
    raise exception 'idempotent replay failed';
  end if;

  begin
    update quirk_sync.run_receipts set status = 'failed' where id = v_receipt_id;
  exception when others then
    v_mutation_rejected := position('append-only' in sqlerrm) > 0;
  end;
  if not v_mutation_rejected then
    raise exception 'append-only receipt mutation was not rejected';
  end if;
end $$;

-- Cloudflare may be represented only as deferred/unbound.
do $$
declare
  v_object uuid;
begin
  insert into quirk_sync.object_registry (object_key, kind, status)
  values ('platform.cloudflare.sql-proof', 'platform', 'candidate') returning id into v_object;
  insert into quirk_sync.source_bindings (
    object_id, platform, external_id, authority_class, sync_direction, state, binding_key, freshness
  ) values (
    v_object, 'cloudflare', 'unverified', 'projection', 'none', 'deferred',
    'binding.cloudflare.sql-proof', '{"status":"unknown"}'::jsonb
  );
end $$;

-- Bounded retries must reach dead letter exactly at max_attempts.
do $$
declare
  v_object uuid;
  v_outbox_id bigint;
  v_claim quirk_sync.projection_outbox%rowtype;
  v_i integer;
begin
  insert into quirk_sync.object_registry (object_key, kind, status)
  values ('test.outbox.object', 'test', 'candidate') returning id into v_object;

  insert into quirk_sync.projection_outbox (
    object_id, destination_platform, operation, payload, payload_hash,
    idempotency_key, authority_ref, max_attempts
  ) values (
    v_object, 'notion', 'rebuild', '{"test":true}'::jsonb, repeat('1',64),
    'outbox:sql-proof:1', 'grant.sql-proof', 5
  ) returning id into v_outbox_id;

  for v_i in 1..5 loop
    select * into v_claim
    from quirk_sync.claim_projection_outbox('worker.sql-proof', 1, 30)
    where id = v_outbox_id;
    if not found then
      raise exception 'outbox claim failed at attempt %', v_i;
    end if;
    perform quirk_sync.record_projection_failure(v_outbox_id, v_claim.lease_token, jsonb_build_object('attempt', v_i));
    if v_i < 5 then
      -- Simulate elapsed exponential backoff inside this rolled-back proof transaction.
      update quirk_sync.projection_outbox set available_at = now() where id = v_outbox_id;
    end if;
  end loop;

  if not exists (
    select 1 from quirk_sync.projection_outbox
    where id = v_outbox_id and status = 'dead_letter' and attempts = 5 and dead_lettered_at is not null
  ) then
    raise exception 'bounded retry/dead-letter proof failed';
  end if;
end $$;

-- Drift must block and propose, never silently repair.
do $$
declare
  v_object uuid;
  v_result jsonb;
begin
  insert into quirk_sync.object_registry (object_key, kind, status, content_hash)
  values ('test.drift.object', 'test', 'candidate', repeat('2',64)) returning id into v_object;
  insert into quirk_sync.source_bindings (
    object_id, platform, external_id, authority_class, sync_direction, state,
    binding_key, last_synced_hash, freshness
  ) values (
    v_object, 'notion', 'page/sql-proof', 'projection', 'projection_only', 'candidate',
    'binding.notion.sql-drift', repeat('3',64), '{"status":"fresh"}'::jsonb
  );

  v_result := quirk_sync.observe_binding(
    'binding.notion.sql-drift', repeat('4',64), 'notion://page/sql-proof', 'agent.quirk-sync-steward'
  );

  if coalesce((v_result ->> 'drifted')::boolean, false) is not true
    or v_result ->> 'action' <> 'block_and_propose'
    or not exists (select 1 from quirk_sync.proposed_moves where object_key = 'test.drift.object' and move_kind = 'projection_drift') then
    raise exception 'drift controller failed';
  end if;
end $$;

-- A projection must rebuild from canonical identity plus runtime state.
do $$
declare
  v_snapshot jsonb;
begin
  v_snapshot := quirk_sync.rebuild_projection_snapshot('program.quirk-sync-control-plane');
  if v_snapshot is null
    or v_snapshot ->> 'schema_version' <> 'projection-envelope.v1'
    or v_snapshot ->> 'object_key' <> 'program.quirk-sync-control-plane' then
    raise exception 'projection rebuild proof failed';
  end if;
end $$;

rollback;
