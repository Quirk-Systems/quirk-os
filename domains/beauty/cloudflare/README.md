# Cloudflare Request Boundary — Candidate, Undeployed

The Worker is a fail-closed edge adapter for exactly one candidate action: `beauty.render_recommendation_explanation`.

It is disabled by default, has no public route, contains no provider secret, and cannot rank, decide, publish, purchase, transact, deploy itself, or mutate the Preference Graph.

A request may reach the explanation service only when all of these are true:

1. `QUIRK_RUNTIME_STATE` is explicitly `bounded_test` in an authorized test deployment;
2. the request supplies a scoped grant;
3. the independent Quirk authority verifier returns `allowed: true` for the exact action;
4. the verifier returns a non-empty `receiptRef` for that authorization decision;
5. the request body carries the required recommendation/evidence envelope.

`allowed: true` without a receipt is denied. The committed `wrangler.jsonc` is configuration evidence, not deployment authority. Service names are candidate placeholders and must be rebound through a separate deployment grant.
