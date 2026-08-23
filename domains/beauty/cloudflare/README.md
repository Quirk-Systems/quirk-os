# Cloudflare Request Boundary — Candidate, Undeployed

The Worker is a fail-closed edge adapter for one action: `beauty.render_recommendation_explanation`.

It is disabled by default, has no public route, contains no provider secret, and cannot rank, decide, publish, purchase, or mutate the Preference Graph. A request reaches the explanation service only when:

1. `QUIRK_RUNTIME_STATE` is explicitly changed to `bounded_test` in an authorized deployment;
2. a scoped grant is supplied;
3. the separate Quirk authority verifier returns `allowed: true` for the exact action;
4. the body carries a recommendation and evidence envelope.

The committed `wrangler.jsonc` is configuration evidence, not deployment authority. Service names are candidate placeholders and must be rebound through an exact deployment grant.
