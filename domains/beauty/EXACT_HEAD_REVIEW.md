# Exact-head review policy

A candidate test is meaningful only for the exact SHA under review. The CI matrix binds checkout and evidence artifacts to `pull_request.head.sha`; each job emits its checked-out commit and tree. Any head change invalidates earlier test and review receipts.

Review classes:
- Canon-only commit: `CANON_ADMISSION_DECISION` — no runtime, database, provider, or graph authority.
- Candidate code commit: `EVIDENCE_ONLY`.
- CI/edge/provenance commit: `EVIDENCE_ONLY`.

`APPROVE_CANON_BOUNDARY` must be a distinct human decision from `APPROVE_EVIDENCE`. Neither automatically grants runtime authority. The real-proof CLI fails closed until detached Ed25519 verification against an independently administered Quirk-core trust registry is integrated.

Cloudflare Worker contract tests require a valid Quirk-core issuer and receipt reference; missing or malformed receipts, malformed requests, oversized bodies, and verifier failures must not invoke the explanation service. Node tests are not Workers-runtime evidence.

Source HEAD: `bab7e54977a6db872d1fac718db8c2b935e8fe95` (orphan-based local source). Source provenance is recorded in `SOURCE_LINEAGE.md`. This PR is a new repo-native descendant of main. Commit SHA preservation across a parent change is impossible; the source mapping is explicit.

**Exact-head rule:** this review policy and every check receipt are bound to the PR's current head SHA. A new commit invalidates all prior reviews and checks.
