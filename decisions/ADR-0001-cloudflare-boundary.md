# ADR-0001 — Cloudflare boundary

**Status:** Candidate decision — `DEFER_UNBOUND`  
**Date:** 2026-08-11  
**Owner:** Bryan  
**Scope:** Quirk Sync Control Plane

## Decision

Cloudflare is represented as a known but deferred edge/security platform. It is not an active runtime, canonical source, projection delivery target, or deployment authority in v0.2.

No Worker, Pages project, DNS route, WAF rule, Turnstile widget, R2 bucket, Queue, secret, or production deployment may be created from the sync control plane until a live account inventory and a separate human admission decision exist.

## Responsibility boundary

- **GitHub:** versioned Canon and candidate source.
- **Supabase:** private runtime state and receipts.
- **Vercel:** approved application delivery projection.
- **Cloudflare:** deferred candidate for edge security, DNS, routing, or specialized edge compute only.

Cloudflare may not duplicate Supabase persistence, silently replace Vercel delivery, mutate Canon, or infer authority from connected credentials.

## Admission evidence later required

1. Account, zone, project, and environment inventory.
2. Adopt/adapt/reject decision by product capability.
3. Preview and production separation bound to commits.
4. Secrets, outbound access, observability, rollback, and incident ownership.
5. Provider-overlap tests against Vercel and Supabase.
6. Proof that Cloudflare cannot write Canon.
