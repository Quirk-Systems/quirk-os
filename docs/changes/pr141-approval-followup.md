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
