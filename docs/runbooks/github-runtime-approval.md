# GitHub approval ingestion and runtime use

This is a repository implementation, not evidence of a deployed grant service.
The designated reviewer is GitHub user ID 207279, login `bryansayler`, mapped to
`human.bryan`. Changing that allow-list is an authority-policy change.

A dedicated grant request JSON has exactly these keys: `grant_id`, `subject_kind`
(`manifest` or `skill`), `subject_id`, `subject_version`, `subject_digest`,
`subject_path`, `authority_ceiling`, `allowed_actions`, `requested_by`,
`approved_by`, `decision_ref`, `issued_at`, `expires_at`, `purpose`.
Use `.quirk/approval-requests/<grant_id>.json`, where the grant ID starts `grant.`.
The subject is JSON on the same reviewed commit. Skill digests are recomputed
with the existing canonical-manifest algorithm. Manifest grants permit only
`activate_manifest` and bind all inline execution fields in addition to the
existing content hash. No new preimage algorithm is asserted.

The latest submitted review by the designated human must be `APPROVED` on the
exact current request head, with user type `User`. Draft, closed-unmerged,
non-main-base, dismissed, newer commented/changes-requested, forged, old-head
and mid-fetch head changes deny ingestion. A fresh review uses a new grant ID
after revocation. Verification compares base repository ID/full name, base ref
and base SHA across reads; mutable repository metadata is excluded.
Transport, JSON decoding and incomplete/invalid API response failures propagate
without writing either `verified_at` or `revoked_at`. Retry the trusted worker;
a database check denies records older than five minutes. Only a verified policy
invalidation (or a changed original grant/head/review binding) marks sticky
revocation. Later successful verification can refresh an unrevoked row. Revocation propagation is bounded by this
freshness window, not instantaneous. GitHub API authentication is never supplied
by a judged runtime payload.

Before live rollout, audit current migration state and active manifests. The
migration refuses pre-existing active rows without matching protected records;
it never backfills synthetic grants or rewrites approval history. A database
owner provisions a separate trusted login using `quirk_approval_ingestor`, with
no membership granted to the runtime or service role. Keep its credentials
outside runtime environments. This trusted worker and the database owner are
part of the trust boundary; a compromised ingestor can forge records.

Install Psycopg 3 only in that worker. Set `QUIRK_APPROVAL_GITHUB_TOKEN` (read
access to pull requests and repository contents) and, for apply/refresh only,
`QUIRK_APPROVAL_DATABASE_URL` (current role `quirk_approval_ingestor`).

```sh
python scripts/ingest_github_approval.py --pr REQUEST_PR --request-path .quirk/approval-requests/grant.example.json
python scripts/ingest_github_approval.py --pr REQUEST_PR --request-path .quirk/approval-requests/grant.example.json --apply
python scripts/ingest_github_approval.py --refresh-grant grant.example --apply
```

Dry runs register nothing. The worker should refresh before the five-minute
freshness cap. Transactions commit only after verification. Ingestion records
cannot be edited to change their subject, scope, review or lifetime; correction
requires a new reviewed request and new grant ID.

Runtime Python uses `PostgresApprovalRegistry(runtime_connection)` supplied by
trusted application wiring, passing `approval_registry=` to admission/grant
validation and skill loading. Runtime data must not supply the resolver.
Database outages deny use; authorization results are never cached. Skill
loaders additionally check canonical-manifest and source-blob integrity and
the grant's local time contract. SQL execution callers must call
`quirk_sync.assert_manifest_runtime_authorized(manifest_key, version)` for every
invocation; an old `status='active'` alone is insufficient after expiry or
revocation. The trigger gates writes, while the helper gates subsequent use.
Existing executors have no established live wiring; verify adoption before any
runtime-authority claim. External reference identity, object-level scope and
operation-side effect enforcement remain executor responsibilities.

Tests use isolated synthetic records only. The candidate conformance positive
fixture uses an explicit mock resolver to test structure; it is not an actual
runtime authorization. No admission hold is disposed by this implementation.
