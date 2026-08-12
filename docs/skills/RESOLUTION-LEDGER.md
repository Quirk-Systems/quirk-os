# Quirk Skills Hardening — Resolution Ledger

## Resolved in this candidate branch

| Finding | Resolution |
| --- | --- |
| Skills CI failed before validation | Removed implicit cache discovery; pinned current Node 24 actions and bound pip cache to `requirements-evals.txt`. |
| Branch depended on obsolete PR #5 contracts | Reconciled through the current PR #5 stack, preserving the outbox lease and manifest-transition repairs. |
| Authority-only fixture coverage | Expanded to 44 executable positive, adversarial, regression, and authority cases. |
| Prose-only packages | Added 11 strict `manifest.json` contracts and a rebuildable registry. |
| Mutable or ambiguous identity | Added exact Git blob SHA and canonical manifest SHA-256 binding. |
| Runtime loading unspecified | Added fail-closed loader, scoped grant schema, and tests. |
| Over-ceiling or undeclared actions | Loader rejects both. |
| Self-approved admission/grants | Loader rejects requester/approver identity collisions. |
| Learning could imply silent mutation | Mutation mode is `propose_only`; history rewrite is forbidden. |
| Mapping drift | Added `mappings/skill-package.v1.yaml` with no silent loss and Proposed-Move-only reverse flow. |
| No receipt contract | Added strict immutable skill-run receipt schema and positive validation. |
| Unresolved PR #6 comments | None existed at inspection time; no review threads were open. |
| Placeholder debt | Validator rejects unresolved placeholder markers inside the bounded skill pack. |
| Skills workflow verification | Push and pull-request validation has passed on the hardened candidate. |
| Sync-control-plane dependency verification | Sync Control Plane Conformance passes on the reconciled stack. |
| Inherited Golden gate conflated merge with admission | PR #3 now separates candidate merge-readiness from Golden admission while preserving all tribunal holds. |

## Current inherited gate state

Golden Gates is an owned structural gate for the Golden Project Pack. It now allows a structurally valid `PROPOSED` candidate to be preserved and merged while continuing to emit explicit Golden-admission holds. The Ship It Without Bryan findings remain unresolved admission evidence; this child neither verifies nor waives them.

## Intentionally unresolved because code cannot manufacture the evidence

- accountable human admission decision;
- production or cross-platform live trials;
- organization branch-protection configuration;
- three independent consumers proving repository extraction;
- revocation and replay evidence beyond the bounded grant contract;
- inherited PR #3 Golden admission findings.

These remain visible admission blockers. They are not converted into green admission checks by wording or by candidate merge-readiness.
