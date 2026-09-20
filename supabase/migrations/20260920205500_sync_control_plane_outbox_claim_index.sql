-- Improve claim-path ordering support with separate index paths:
-- pending/failed rows by queue order and expired leased rows by lease expiry.
create index if not exists projection_outbox_claim_pending_failed_idx
  on quirk_sync.projection_outbox(available_at, id)
  where status in ('pending','failed')
    and attempts < max_attempts;

create index if not exists projection_outbox_claim_expired_leased_idx
  on quirk_sync.projection_outbox(leased_until, available_at, id)
  where status = 'leased'
    and attempts < max_attempts;
