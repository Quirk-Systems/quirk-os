# Cloudflare Request Boundary — Candidate, Undeployed

The Worker is a fail-closed edge adapter for exactly one candidate action: `beauty.render_recommendation_explanation`.

It is disabled by default, has no public route, contains no provider secret, and cannot rank, decide, publish, purchase, transact, deploy itself, or mutate the Preference Graph.

## Candidate verifier response contract

An explanation request may reach the explanation service only when all of these are true:

1. `QUIRK_RUNTIME_STATE` is explicitly `bounded_test` in an authorized test environment.
2. The request supplies a scoped grant.
3. The independent Quirk authority verifier returns `allowed: true` for the exact action.
4. The verifier returns `receiptIssuer: "quirk.core.evidence"`.
5. The verifier returns a trimmed `receiptRef` matching `urn:quirk:core:evidence:<opaque-id>`.
6. The request has valid JSON, the required recommendation/evidence envelope, and a body no larger than 16 KiB.

Malformed JSON, non-JSON media types, missing or malformed receipts, verifier failures, and oversized requests fail closed. Body parsing and the size limit happen before the verifier call. The validated receipt reference and issuer are forwarded to the explanation service.

The receipt URI shape is a **candidate integration contract**. Compatibility with the actual Quirk-core verifier must be confirmed before any binding is connected.

## Verification ceiling

The checked-in Node tests exercise handler contracts with simulated service bindings. They are not Workers-runtime evidence. Before deployment consideration, add and pass Cloudflare's Workers Vitest integration against the installed Wrangler schema and test harness. The current configuration enables structured Worker logs and traces, but does not grant deployment authority.

The committed `wrangler.jsonc` is configuration evidence, not deployment authority. Service names are candidate placeholders and must be rebound through a separate deployment grant.
