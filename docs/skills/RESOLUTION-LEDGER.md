# Quirk Skills Hardening — Resolution Ledger

## Resolved in this candidate branch

| Finding | Resolution |
| --- | --- |
| Skills CI failed before validation | Removed implicit cache discovery; pinned current Node 24 actions and bound pip cache to `requirements-evals.txt`. |
| Branch depended on obsolete PR #5 contracts | Reconciled and rebased the skill branch onto PR #5 head `bf09bb90bcb365db55fdd47239fe7a48d48aa1f0`, including the outbox lease and manifest-transition repairs. |
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
| Placeholder debt | Validator rejects TODO-style markers inside the bounded skill pack. |
| Skills workflow verification | Push and pull-request runs passed on the hardened commit. |
| Sync-control-plane dependency verification | Sync Control Plane Conformance passed on the hardened commit. |

## Inherited dependency blocker

Golden Gates still fails at `structural-integrity → Validate Golden Project Pack`. The same step failed on PR #5 commit `f344af21ff96e9e748a0a0c65dbc20ae71912222` before this skill commit existed. The Node 20 annotation is a warning; the validator exits 1. This PR does not modify the Golden Project Pack, its tribunal queue, or `scripts/validate_golden_pack.py`, so the failure remains owned by stacked PR #3 / its inherited evidence contract rather than being silently patched through this child PR.

## Intentionally unresolved because code cannot manufacture the evidence

- accountable human admission decision;
- production or cross-platform live trials;
- organization branch-protection configuration;
- three independent consumers proving repository extraction;
- revocation and replay evidence beyond the bounded grant contract;
- inherited PR #3 Golden Gates findings.

These remain visible blockers. They are not converted into green checks by wording.
