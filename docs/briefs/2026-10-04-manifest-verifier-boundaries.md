# Manifest verification — candidate build brief

Version: v0.1 · State: candidate · Date: 2026-10-04 · Authority effect: none

Bryan approved ADR-0002/0003's design pair and continued implementation in this
conversation. PR #113 has since merged; this successor starts at main commit
`31a3fc56c71f55351f0c2be2bc18ad80a3007d08`. The two October 3 draft briefs and
historical evidence remain intact. Their deliberate trust-gap findings are not
marked fixed by this brief or by passing synthetic tests.

## Problem and useful result

Matching submitted hashes and a `human.*` string cannot establish evaluated
content or human consent. A reviewer needs an inspectable candidate verifier,
explicit hash semantics, a protected projection lane, and evidence showing
both permitted flow and refusal.

## Keep the distinctive part

Prove the crossing, including useful flow at the edge. An agent may request
admission; only independently resolved, scoped human consent can authorize
activation. A proof never admits itself.

## First slice

- Build: strict content hashing, live GET-only review resolution, external
  schemas, in-memory projection preparation, and a candidate SQL cutover with
  transactional privilege, drift, replay, history, stop, and resume cases.
- Leave for later: protection changes, credential provisioning, installing the
  verifier, deploying migrations, consumer revalidation, and live admission.
- Bound: one successor branch and draft PR; CPython 3.13 and PostgreSQL 16 CI;
  single universal CODEOWNER. No general CODEOWNERS parser or second approval
  plane. Production policy remains disabled pending a separately admitted host.

## User journey

1. Submit a schema-valid candidate with a computed digest and no admission.
2. Inspect the hash and evaluation materials without authority effects.
3. After trusted bootstrap, an independent human submits one exact-head
   activation review with explicit subject, transition, scope and expiry.
4. The admitted host resolves it, prepares the runtime envelope, immediately
   resolves again before applying the protected database transaction, and
   records append-only projection/transition evidence. Missing or contrary
   evidence blocks the crossing. Hash-only output remains useful on failure.

## Implementation handoff

Use `scripts/manifest_admission.py` for hashing or preparation. Its policy and
transport are host-controlled dependencies, never fields supplied by a
manifest. The CLI never writes a database. The SQL application function is an
INVOKER entry point for `quirk_manifest_verifier`; broad runtime/browser roles
cannot assume that role or write registry/receipt rows. A separately provisioned
login and admitted Python runner are still prerequisites.

Preserve `runtime-manifest.v2`. Version the approval subject, evaluation record,
normalized verifier result and hash profile externally. SQL does not recompute
Python JSON or resolve GitHub. A compromised verifier or privileged database
administrator can forge the projection; this is the explicit design tradeoff.

## Evidence and upkeep

| Question | Observable check | Decision rule | Current evidence |
| --- | --- | --- | --- |
| Does scoped consent discriminate? | Valid exact review vs one-axis stale review; forged identities/scope/refs | Exact case succeeds in memory; every altered case refuses | Executed synthetic Python tests; no authentic live activation tested |
| Is content bound? | Golden vectors, metadata drift, lifecycle-only changes, strict ingestion | Covered content changes digest; statuses need separate consent | Executed on CPython 3.13 |
| Is the projection protected? | Real PostgreSQL roles, RPC/direct write attacks, replay and stop/resume | Refusal rolls back all effects; authorized lane succeeds | CI cases written; result recorded in successor evidence |
| Does it earn upkeep? | Host trust/protection audit, API availability, consumer revalidation | Proposed: quarterly audit and after every trust/profile/role change | Burden not measured; stop live bootstrap if ownership cannot be maintained |

## Decisions and authority

Known: GitHub review root, metadata-inclusive hash, PostgreSQL projection,
separate profile versions. Architectural consent does not approve any manifest,
merge or deployment. Current branch lacks installed protected-base ownership;
adding CODEOWNERS in this candidate does not bootstrap itself. The installed
host must pin its approved digest, verify Bryan's account-ID mapping and
repository protections, and maintain independent-requester rules. If Bryan is
the PR author, admit another human or use an independently submitted request;
never turn off independence to make an approval work.

Assumed/open: positive live review, protected runner deployment, provisioned
login isolation, final write interval, consumer expiry/revocation enforcement,
and human disposition of legacy active rows. Cutover refuses legacy active
rows rather than inferring consent. Stops only reduce authority, preserve
content/approval, and append a distinct stop observation with no human approver.

## Skill routing and claim checks

`demonstrate-quirk-boundaries`, `draft-quirk-brief`, and `quirk-deep-research`
were read and applied. `quirk-claim-check`, `quirk-greathering`, and
`route-quirk-skills` were not available in the complete executor/cloud catalogs
or installed skill paths. This brief and the research ledger perform the needed
claim/routing checks without asserting that missing skills ran. No skill was
invented or installed, and no agent was delegated work.

A green structural conformance report means candidate eligibility only. The
synthetic human fixture now carries `fixture_only` metadata, a computed hash,
and an explicit gate refusal when no external verifier is installed. No
receipt or historical approval is rewritten.

## One next action

Complete exact-version review and database CI evidence for the successor.
Keep runtime policy disabled. Stop before host installation, cutover deployment
or admission. On failure, retain the refusal, repair the candidate and rerun
only checks affected by the repair.

## Resume record

Current: v0.1. Retain: approved ADR pair and projection tradeoff. Open: trusted
bootstrap and live evidence. Resume: review the successor's exact tree, then
separately admit host policy and credentials if all deployment prerequisites
are established. Passing candidate checks does not close the deliberate trust
gaps or resolve their review findings.
