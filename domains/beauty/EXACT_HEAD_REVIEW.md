# Exact-head review policy

A candidate test is meaningful only for the exact SHA under review. The CI matrix binds checkout and evidence artifacts to `pull_request.head.sha`; each job emits its checked-out commit and tree. Any head change invalidates earlier test and review receipts.

Review classes:
- Canon-only commit: `CANON_ADMISSION_DECISION` — no runtime, database, provider, or graph authority.
- Candidate code commit: `EVIDENCE_ONLY`.
- CI/edge/provenance commit: `EVIDENCE_ONLY`.

`APPROVE_CANON_BOUNDARY` must be a distinct human decision from `APPROVE_EVIDENCE`. Neither automatically grants runtime authority. Old v0.1 proof verification is synthetic-only pending external trusted-key proof integration; it **must not be used as real admission**.

Cloudflare Worker test: receipt absent or malformed must deny without invoking an explanation service. Node tests are not Workers-runtime evidence.

Source HEAD: `bab7e54977a6db872d1fac718db8c2b935e8fe95` (orphan-based local source). This PR is a new repo-native descendant of main. Commit SHA preservation across rebasing is impossible; mapping is explicit in `SOURCE_LINEAGE_V0.1.1.md`.
