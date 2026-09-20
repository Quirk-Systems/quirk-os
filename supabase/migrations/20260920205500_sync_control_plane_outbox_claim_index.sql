-- Improve claim-path ordering support for pending/failed/leased ready rows.
create index if not exists projection_outbox_claim_ready_idx
  on quirk_sync.projection_outbox(available_at, id)
  where status in ('pending','failed','leased')
    and attempts < max_attempts;
