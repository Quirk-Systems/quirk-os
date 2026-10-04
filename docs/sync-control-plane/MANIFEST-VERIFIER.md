# Candidate manifest verifier

ADR-0002 and ADR-0003 are approved design decisions. This implementation remains
candidate. It preserves the portable v2 schema and introduces external
`manifest-approval-attestation.v1`, `manifest-evaluation.v1`,
`verified-manifest-approval.v1`, `verified-manifest-projection.v1`, and
`runtime-manifest-content.v1`. Admission policy is candidate 0.4.0.

| Decision | Operational meaning |
| --- | --- |
| Approval root | Resolve one submitted APPROVED human review at the PR's current head. Require explicit activation JSON and trusted base CODEOWNERS/account mapping. A normal PR approval is insufficient. |
| Database | Trust the admitted Python host's exact projection; preserve structural checks. Broad service/browser write privileges are revoked. No independent attestation/hash claim. |
| Hash preimage | Cover all 16 declared content fields when present, including every metadata value. Exclude content_hash, admission, status and requested_status. Status changes still require scoped transition consent. |
| Versions | Keep the v2 field shape. Hash/profile semantics changed, so old arbitrary hashes/grants are not grandfathered. Add a new manifest version only when its shape changes. |

Run under CPython 3.13 with `requirements-evals.txt` installed:

```sh
python scripts/manifest_admission.py path/to/candidate.json
python -m unittest discover -s tests -p 'test_*.py' -v
```

The first command computes a digest and explicitly reports no admission. For
preparation, the admitted host supplies its installed policy and request
context with `--policy` and `--context`; an authenticated GitHub reader uses
`GITHUB_TOKEN`. Only GET requests to the fixed API origin are used. The CLI
never writes SQL or installs authority. Do not expose verifier credentials to
candidate code, let a submitter choose policy/transport, or install the branch's
code merely because it passed its own tests.

The candidate policy sets both `enabled` and `protection_verified` false. Its
proposed single owner is `@bryansayler`, account ID 207279 (resolved from the
GitHub profile during this session). A protected host must verify/admit the
identity, protections and base CODEOWNERS digest; changing booleans in candidate
JSON cannot confer authority. The resolver initially accepts only universal
single-owner coverage plus ownership of CODEOWNERS itself. Team/multiple-owner
patterns need a tested policy revision.

The review body contains exactly one fenced `quirk-manifest-approval` JSON
block matching `schemas/manifest-approval-attestation.schema.json`. It binds the
repository/PR/head/base, candidate path/key/version, profile/computed digest,
requester, expected prior state, active target, environment, capability/action
scope, evaluation evidence and validity interval. Allowed actions/object scope
are the sorted unions of the candidate's tool fields. The reviewer must be a
mapped human who is neither the PR author nor the requester. Reviews are
re-fetched, enumerated for conflicts/revocation, and re-read before the result
is yielded. API failure, wrong scope, later contrary review, duplicate approval,
expiry, changed head/base or missing evidence refuses.

Authority starts at the later of the requested valid_from and GitHub's actual
review submission, and ends at expires_at. The body may be composed earlier;
it cannot backdate consent. The runtime decided_at always comes from GitHub's
submission timestamp, rather than a timestamp supplied in the subject.

The candidate source at the reviewed SHA has admission null/absent. Its hash
must agree with the submitted object. Evaluation and raw materials are read
at that SHA, with recorded material digests verified. The evaluation record's
pass is a report bound to inspected materials; resolving it does not independently
rerun or certify its evaluator. The admitted runner and human must establish
that evaluation's provenance before relying on it. Referenced URIs beyond
these bound materials remain mutable; the hash covers strings, not all transitively
referenced bytes.

Preparation generates active status/admission in memory while leaving the
content digest unchanged. Freshly resolve again immediately before the SQL
transaction. Apply the returned envelope through
`quirk_sync.apply_verified_manifest_projection(jsonb)` as the separately
provisioned `quirk_manifest_verifier` role. The function is INVOKER, compares
prior state, serializes identity writes, writes the exact payload and immutable
receipt/transition together, and makes an identical repeat produce no additional
effects. SQL observations older than 60 seconds or expired approvals refuse.
GitHub and SQL do not share an atomic transaction; revocation in that final
interval is a disclosed limitation. Consumers must revalidate continuing
protected use; this slice does not implement that consumer contract.

SQL payload binding uses column and JSONB value equality. It does not preserve
the CPython canonical byte stream: PostgreSQL can normalize numeric notation
and consider differently spelled numeric values equal. The reviewed Git source
and its hash profile remain the content authority. A reconstructed database
row is not an independently verified portable manifest or digest. See the
[PostgreSQL JSON types contract](https://www.postgresql.org/docs/16/datatype-json.html#JSON-INPUT-OUTPUT).

The candidate migration creates a NOLOGIN role with no memberships, audits
legacy active rows under a lock and refuses cutover until a human disposes of
them. It grants no production credential. Apply the migration only through a
transactional runner after deployment authorization. Historical rows and
receipts are never backfilled as consent.

A protected verifier can stop an active row by setting both status fields to
paused or revoked without changing content or approval. This remains possible
after expiry, logs a separate stop observation with no human approver, and
never confers fresh authority. Resume requires a new scoped grant for the
actual paused state. Direct SQL by administrators and a compromised verifier
remain explicit trusted bypasses under the projection design.

The conformance workflow tests the historical structural guard before the
cutover, observes legacy-row cutover refusal, then applies the successor and
runs `manifest_verified_projection.sql` against actual PostgreSQL. All synthetic
rows are rolled back. Running the old service_role positive tests after the
cutover is intentionally invalid because broad registry writes have been revoked.

The deliberate trust-gap findings remain open pending protected bootstrap,
authentic positive/negative live-review evidence and consumer enforcement.
Local or hosted synthetic proof is candidate evidence, never final admission.
