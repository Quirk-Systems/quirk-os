# ADR-0002 — Cloudflare capability inventory and bounded edge role

**Status:** Accepted — `INVENTORY_COMPLETE_DEFER_SELECTIVE`
**Date:** 2026-08-12
**Owner:** Bryan
**Supersedes:** ADR-0001 (status clause only; boundary rules remain in force)
**Closes:** quirk-os#11
**Parent:** quirk-os#7

---

## Context

ADR-0001 encoded `DEFER_UNBOUND` and required a live account inventory before any Cloudflare resource could be admitted.  This ADR records that inventory, makes a per-capability adoption decision, and proves the provider-boundary rules from ADR-0001 are satisfied.

---

## Account inventory

| Field | Value |
|---|---|
| Account name | quirk-systems (personal/org, free tier) |
| Account ID | unverified — no API token issued; no resource created |
| Zones | none registered |
| Projects (Pages) | none |
| Workers | none |
| R2 buckets | none |
| Queues | none |
| Turnstile widgets | none |
| AI Gateway endpoints | none |
| Secrets / KV namespaces | none |
| Billing posture | free; no paid add-ons activated |

**Inventory method:** manual console inspection, 2026-08-12.  No programmatic API call was made and no credential was created or stored.

---

## Per-capability decision

| Capability | Decision | Justification | Reversibility |
|---|---|---|---|
| DNS and routing | **Defer** | No zone registered; Vercel handles apex and subdomain routing for v0.2. Re-evaluate if multi-region or custom TLS requirements emerge. | Adopt by registering a zone and routing traffic; reject by not registering. |
| WAF / DDoS / API Shield | **Defer** | No origin server exposed; Vercel's built-in edge protection is sufficient at current traffic volume. Re-evaluate at first DDoS incident or when a public API is exposed. | Adopt by proxying traffic through Cloudflare; reject by maintaining direct Vercel delivery. |
| Turnstile | **Defer** | No user-facing form exists that requires bot protection in v0.2. Re-evaluate when a public registration or payment flow is introduced. | Adopt by embedding the Turnstile widget and adding a server-side verification step; reject by using an alternative CAPTCHA or no challenge. |
| Workers or Pages | **Defer** | Vercel is the admitted application delivery projection. A Workers or Pages deployment would duplicate delivery authority without justification. Re-evaluate only if a specific edge-compute capability unavailable in Vercel is required. | Adopt by creating a named project bound to a Git branch; reject by preserving Vercel-only delivery. |
| R2 | **Defer** | Supabase Storage is the admitted binary-object store. R2 would duplicate persistence authority. Re-evaluate only if cost or egress requirements make Supabase Storage unsuitable. | Adopt by creating a named bucket with a scoped API token; reject by preserving Supabase Storage only. |
| Queues / Workflows | **Defer** | Supabase outbox and the sync control plane own async work dispatch. Cloudflare Queues would duplicate work-queue authority. Re-evaluate only if a durable, globally distributed queue with sub-second delivery latency is required. | Adopt by creating a named queue bound to a scoped Worker; reject by preserving the Supabase outbox. |
| AI Gateway / Workers AI | **Defer** | No AI inference route is exposed publicly in v0.2. Re-evaluate when an LLM proxy, cost-cap gateway, or observability requirement exists for AI calls. | Adopt by routing inference traffic through an AI Gateway endpoint; reject by calling model providers directly. |
| Observability and log export | **Defer** | Supabase and Vercel each emit their own structured logs. No unified log-sink requirement exists in v0.2. Re-evaluate when a cross-provider log aggregation requirement is accepted. | Adopt by configuring a Logpush job to an S3-compatible sink; reject by relying on per-provider dashboards. |

**Summary:** all eight capabilities are deferred.  No Cloudflare resource has been created, changed, routed, or deployed as a result of this inventory.

---

## Provider-boundary proofs

### Cloudflare cannot mutate Canon

- No API token for the `quirk-systems` Cloudflare account has been created.
- No GitHub Actions workflow grants Cloudflare credentials `contents:write` or `id-token:write`.
- Canon lives entirely in GitHub; Cloudflare has no read or write access to any repository resource.

### No overlap with Supabase persistence

- No R2 bucket exists.  R2 is explicitly deferred above with justification.
- No Queue or Workflow exists.  Queues are explicitly deferred above with justification.
- The constraint `source_bindings_cloudflare_boundary_check` in `quirk_sync.source_bindings` enforces `sync_direction in ('none','projection_only')` for any Cloudflare binding row.

### No overlap with Vercel application delivery

- No Pages project or Worker exists.
- Workers and Pages are explicitly deferred above with justification.
- No DNS route proxied through Cloudflare exists.

### Secrets, outbound access, rollback, and incident ownership

- No secret is stored in Cloudflare Workers secrets, KV, or environment variables.
- No outbound request originates from a Cloudflare resource.
- Rollback is not applicable — no deployment exists.
- Incident ownership is not assigned — no runtime exists.

---

## Preview and production paths

Not yet applicable.  No project exists.  When a capability is adopted, preview and production environments must be bound to separate Git branches or tags and recorded in the relevant platform manifest before the first deployment.

---

## Binding state transition

The Supabase `source_bindings` row `binding.cloudflare.deferred` transitions from `state = 'deferred'` to `state = 'deferred'` (unchanged) but the `freshness` object is updated to record inventory completion.  A new migration records the inventory timestamp and this ADR as the evidence reference.

---

## Decision record

| Field | Value |
|---|---|
| Status | `INVENTORY_COMPLETE_DEFER_SELECTIVE` |
| Evidence | This document |
| Reversibility | Per-capability table above |
| Next trigger | Acceptance of a specific capability requirement by a human product decision |
| Canon mutation risk | None — no Cloudflare resource or credential exists |
