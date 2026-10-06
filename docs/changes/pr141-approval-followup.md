# PR #141 approval verification follow-up — 2026-10-06

Both unresolved, non-outdated findings remain valid on main
`9dfb4ffa95ce954b689233e3fdc989936f789242`.

- [Metadata finding](https://github.com/Quirk-Systems/quirk-os/pull/141#discussion_r4191692504): repaired. Compare only base repository ID/full name, ref and SHA across verification reads. Mutable counts, timestamps, labels and descriptions do not change approval.
- [Revocation finding](https://github.com/Quirk-Systems/quirk-os/pull/141#discussion_r4191692531): repaired. `PolicyInvalidation` identifies established authorization failures. `refresh()` catches only that exception; transport, JSON parsing, incomplete PR/document/review payloads and pagination failures propagate with no timestamp write. Validate required response fields before interpreting missing data as a withdrawal.

Adversarial regressions cover metadata drift, each base binding field, first and
final incomplete PR responses, malformed review entries/pages, truncated HTTP
200 JSON, document failures, recovery, true policy invalidation, changed review
identity and pre-existing sticky revocation. Three new regression methods fail
against the original implementation and pass with this repair.

Local validation: 261 repository tests pass, including 20 approval tests;
Sync Control Plane conformance and Golden candidate structural checks pass.
The generated Sync result remains byte-identical to the tracked result. Hosted
checks and PostgreSQL behavioral verification are reported separately by CI.

No migrations, database privileges, runtime-grant scope, designated reviewer,
freshness cap or immutable registry bindings change. Tests use synthetic grants
and mocked connections only. All 16 admission holds remain unresolved. This PR
creates no real grant, admission, deployment or established runtime authority.

## PR #143 malformed-request correction — 2026-10-06

Validate every required request value, principal, digest, path, action list and
timezone-aware timestamp before interpreting request authorization policy. Null
or wrong-typed values, malformed fields and invalid action-list shapes propagate
as ordinary ValueError, without updating verified_at or revoked_at. Well-formed
wrong approvers, insufficient purposes, excess scope, unknown subject kinds and
subject-binding mismatches still produce sticky policy invalidation.

Validation: 264 repository tests pass in a clean standalone checkout, including
23 approval methods. Both malformed-request regression methods fail against the
original #143 implementation. The 79 affected approval/runtime/control-plane
tests pass. Sync conformance output is byte-identical; Golden candidate
structural gates pass with all 16 holds. Tests use synthetic fixtures and mocked
connections; hosted checks are reported separately. Freshness, immutable binding
and no-runtime-authority boundaries remain unchanged.
