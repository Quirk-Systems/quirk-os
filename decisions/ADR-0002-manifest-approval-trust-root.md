# ADR-0002 — approval trust root and database boundary

**Repository path:** `decisions/ADR-0002-manifest-approval-trust-root.md`  
**Status:** Approved design; implementation remains candidate  
**Owner:** Bryan Sayler  
**Date:** 2026-10-04  
**Authority effect:** design decision only; no runtime admission  
**Scope:** Manifest activation only; pair with ADR-0003  
**Basis:** PR #113 at `d9443d713bb532e00d0d16e692509c2519457d3e`

## Decision

The trust root is a GitHub-hosted, submitted `APPROVED` review by a specifically authorized human, on the exact candidate commit, containing explicit approval of a bounded manifest activation. An ordinary code-review approval, merge, bot verdict, green check, or declared `human.*` principal is insufficient.

Reviewer eligibility comes from a separately admitted base-branch CODEOWNERS policy plus a protected mapping from GitHub account ID to Quirk human principal. The candidate branch cannot appoint its own reviewer, replace the mapping, or change the verifier used to judge itself. Proposed initial eligible person: Bryan (`@bryansayler`), subject to verified account-ID mapping and independent-requester rules. The candidate implementation proposes account ID 207279, resolved from the authenticated GitHub profile in this session; the protected host must independently verify and admit the mapping. If GitHub or Quirk independence rules prevent a person from approving the request, obtain another explicitly admitted human; do not bypass them.

The review must explicitly bind repository, PR and head SHA; manifest path, key and version; ADR-0003 profile and computed content digest; requester; action `activate_manifest`; expected prior state and intended `active` state; requested status; target environment; authority ceiling, permitted actions and object scope; transition/evaluation evidence; and approval validity interval. Consent to this ADR pair is architectural consent only, not one of these activation reviews.

Python resolves the approval from authenticated GitHub data and trusted configuration. It verifies reviewer identity and eligibility, exact commit and content, explicit action/scope, independence, current review state, expiry and any recorded revocation. Missing data, API failure, ambiguous reviews, later contrary review, dismissal, changed head/base approval context, wrong scope, expired/revoked consent, or an untrusted resolver input fails closed. Recheck immediately before applying a transition; do not reuse a generic cached approval forever. This does not claim an atomic transaction spanning GitHub and PostgreSQL: revocation during the final verification/write interval remains a documented limitation. A later consumer must revalidate any continuing authority before protected use; this design grants no permanent execution capability.

Preserve the existing references:

- `decision_ref` identifies the authentic GitHub review decision.
- `authority_grant_ref` resolves to the normalized, scoped attestation of that decision, not a second approval plane. It is deterministically bound to the review identity and approved subject/scope. Resolution re-fetches the source decision or uses a protected verifier-controlled cache with explicit freshness; a caller-authored file/dictionary is not a trusted record.
- `transition_ref` resolves the legal transition evidence. A nonempty string is insufficient; check actual prior state and subject.

The normalized external record uses proposed `manifest-approval-attestation.v1`. Its contract contains the source review identifiers, reviewer account/principal mapping, subject commit and manifest identity, hash profile/digest, transition and scope, validity and observed revocation state, evidence, and verifier provenance. The manifest cannot author it. Any fixture identifying Bryan remains explicitly synthetic and conveys no consent.

Avoid a commit/approval-reference cycle: review the candidate content at its exact commit with admission absent/null as permitted for candidates. Resolve the review out of band, then generate the runtime admission/status envelope without changing the approved content. The projected manifest retains the reviewed source commit as provenance. Committing that generated envelope creates a new source head and does not inherit the old exact-head approval automatically.

## Database-independence decision — shared by both ADRs

**PostgreSQL is a projection of the verified Python gate for approval authenticity and content-hash verification. It is not an independent verifier of either.** Its existing local structural guard remains defense in depth; do not remove it or reverse PR #113's repairs.

Before relying on this model, an implementation must establish and prove a protected verifier-only write path for the manifest registry, including changes to rows already active. Candidate submitters and ordinary runtime workers must be unable to use the verifier credential, become its role, write active rows directly, insert alleged verifier receipts, or change verification policy. The current broad `service_role` grant does not meet that condition by itself. Audit every direct/RPC path and role inheritance; keep administrative owners/migration credentials as explicit trusted bypasses, outside candidate-agent reach. Do not assume an invokable function is safe merely because it has a gate-like name.

The verifier must run admitted code/configuration, not arbitrary candidate-branch code with protected credentials. It verifies the exact payload it subsequently writes, binds the write to the expected current database state, and records revision-bound evidence in the same database transaction. Candidate-only changes cannot substitute an active payload. A boolean `verified=true`, caller-supplied receipt ID, or caller-supplied hash never replaces this boundary.

**Accepted consequence:** compromised verifier credentials, admitted verifier code, or trusted database administration can forge the projection. PostgreSQL does not independently catch false GitHub consent or a false computed digest. If this tradeoff is unacceptable, reject this ADR; select the protected-record or signed-root design and solve database body/hash verification explicitly. Do not quietly call a mirrored record independent verification.

## Schema and migration consequences

Keep `runtime-manifest.v2` and its field set. Reuse `authority_grant_ref`; add no `attestation_ref` alias. Introduce the external attestation schema and a new admission-policy revision (proposed `0.4.0`) describing resolution and the projection boundary. Shape compatibility is not semantic compatibility: legacy arbitrary grant strings do not acquire authority through this change. Trusted configuration must select the new verifier contract; metadata cannot opt into an old weaker gate.

A later choice to add a required manifest field, serialize the profile in the manifest, or change required field shapes needs a new manifest schema version (proposed `runtime-manifest.v3`) and coordinated consumer migration. Database privilege/receipt migrations are separate from portable manifest schema versioning.

Audit legacy active rows during a coordinated cutover. Missing authentic approval must block completion and be reported for human disposition; do not invent historical consent or silently revoke/re-admit rows. Keep receipt and transition history append-only; corrections are new records. Expiry/revocation and ongoing runtime consumers require explicit enforcement before claiming currently usable authority.

## Acceptance evidence and admission limits

Candidate Python refusals and PostgreSQL projection cases have been executed. See `evals/sync-control-plane/manifest-verifier-ci-d30ab0c54d7e.json` for the exact tested source, 252 Python tests, and PostgreSQL 16.15 results. This evidence uses synthetic review subjects; an authentic positive review, protected host installation, and continuing consumer enforcement remain unproved. Passing candidate tests does not resolve the deliberate trust-gap findings.

Refuse fabricated human names, invented references, bot/unauthorized/self approval, wrong head/digest/environment/action/scope, withdrawn/expired consent, unavailable resolver, and missing legal transition. Demonstrate that untrusted callers cannot bypass verification through direct SQL or RPC, even using their real runtime privileges. Demonstrate exact-payload write binding, active-row mutation refusal, concurrent prior-state changes, and fresh refusal receipts. Test a valid authentic approval separately from synthetic fixture conformance.

These tests prove the selected projection contract. They must not be reported as independent SQL attestation verification.

## Approval record

**Design approval:** Bryan explicitly approved the recommended pair in this conversation on 2026-10-04: “Approved and Continue Additional Improvements Implemented via Iteratively Integrated and Enhanced Loop Engineering”. The approval also authorizes continued candidate implementation. The transcript supplies no GitHub review ID; this record is not a runtime activation attestation. No merge, deployment, credential provisioning, or live admission is recorded.

