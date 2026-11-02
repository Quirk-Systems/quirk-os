-- Migration: Cloudflare binding inventory completion
-- ADR: decisions/ADR-0002-cloudflare-capability-inventory.md
-- Date: 2026-08-12
--
-- Records the outcome of the live account inventory required by ADR-0001.
-- All eight capabilities remain deferred; no resource has been created.
-- The binding state stays 'deferred'; freshness is updated with inventory evidence.

update quirk_sync.source_bindings
set
  freshness = jsonb_build_object(
    'status',          'inventory_complete',
    'inventory_at',    '2026-08-12',
    'method',          'manual_console_inspection',
    'zones',           0,
    'pages_projects',  0,
    'workers',         0,
    'r2_buckets',      0,
    'queues',          0,
    'ai_gateway',      0,
    'secrets',         0,
    'api_token_issued', false,
    'decision_ref',    'decisions/ADR-0002-cloudflare-capability-inventory.md'
  ),
  updated_at = now()
where binding_key = 'binding.cloudflare.deferred'
  and platform    = 'cloudflare'
  and state       = 'deferred';
