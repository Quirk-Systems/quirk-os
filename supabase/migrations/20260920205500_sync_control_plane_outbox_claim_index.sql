-- Match the complete claim predicate while preserving queue order.
create index if not exists projection_outbox_claim_ready_idx
  on quirk_sync.projection_outbox(available_at, id)
  where status in ('pending','failed','leased')
    and attempts < max_attempts;
