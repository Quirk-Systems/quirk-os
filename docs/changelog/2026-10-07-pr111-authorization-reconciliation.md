# PR #111 — authorization reconciliation

Rebase versioned model-tool projection onto main `38ba6b9` and retain the original
merge-commit scoped-grant repair. Preserve the strict skill-runtime-grant schema,
principal/independent-approver checks, and protected approval registry. Require
current manifest content verification, trusted approval verifier and activation
context, and separate manifest/skill registry checks through both projection and
serialization. Defaults deny when trusted host dependencies are unavailable.

Retain the original adapter regressions and add denial coverage for registry
absence, mismatches, revocation after success, lookup failure, non-boolean approval,
missing verifier/context, malformed grants, and invalid admission principals.
Add adapter tests to the affected conformance workflow path filters and regenerate
Sync Control Plane evidence with its matching document digest. Migrate the synthetic
self-approval fixture to a versioned tool ref so its principal regressions remain
schema-valid under the projection contract.

This candidate remains draft. Human exact-head approval, merge authorization, and
live activation remain separate; no authority or activation is conferred by tests.
Exact published-head proof is recorded in the PR description after publication.
