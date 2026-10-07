# GitHub runtime approval — candidate build brief

Version: v0.1 · State: candidate · Date: 2026-10-06

A runtime manifest can currently claim a human approved it by supplying a human
name and invented references. Bryan selected **GitHub human approvals with
independent database verification** in this session. A merged code repair is
separate from an approval to operate a particular subject.

The first slice authenticates the designated human's latest submitted GitHub
review of the exact grant-request commit, then writes an immutable binding via
an isolated PostgreSQL ingestor role. Every invocation uses a fresh database
lookup. Missing, stale, mismatched, expired, revoked or unavailable records deny
use. Existing runtime manifest and skill grant schemas retain their fields.

1. An agent proposes a JSON request in `.quirk/approval-requests/<grant_id>.json`
   and a subject JSON file on an exact commit targeting repository `main`.
2. The designated human reviews that request commit. Code PR approvals and
   generic review comments do not issue grants.
3. An isolated worker reads GitHub API state and the reviewed source. Only its
   database role may ingest, refresh or revoke records.
4. Runtime callers query the protected registry with exact subject, digest,
   principal pair, decision, ceiling and operations. Manifest execution fields
   also match the reviewed JSON contract, preventing hash reuse with new tools.

Observable checks: adversarial Python tests deny fabricated/old/bot/dismissed
reviews, changed heads, scope drift and database failures. SQL tests deny
unregistered, mismatched, expired, stale and revoked grants; the service role
cannot manufacture or refresh approval. Positive records are synthetic and
transactionally rolled back. Hosted validation and migration read-back are
required before merge. No real grant or admission is created by these checks.

Upkeep: the dedicated worker must refresh valid records more often than five
minutes, using a dedicated credential unavailable to the runtime. Failure stops
authority after the freshness window. Measure worker availability and refresh
cost before enabling real grants; no operational baseline is established.

Open rollout dependencies: reconcile live migration drift; provision the
separate worker identity; wire SQL execution callers to the active-use helper;
then obtain a real, scoped human review. Runtime content-hash preimage semantics
remain separate debt, although the protected inline contract blocks execution
field changes. Referenced resources and external systems still need their own
version checks. The 16 historical admission holds remain unverified.

Next action: the engineering lane validates the candidate repair locally and
in hosted CI, publishes an evidence-bound draft PR and stops any merge if a
required check fails. A proposed first operational trial is one existing-tool,
30-minute dry run; stop before issuing a grant without its real human review.

Resume: v0.1; retain the selected GitHub/database trust root. Need hosted checks,
live migration reconciliation and isolated-worker deployment evidence. Continue
at the candidate PR; do not claim deployed runtime authority.
