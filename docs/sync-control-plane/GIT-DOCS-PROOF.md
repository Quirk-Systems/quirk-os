# PR148 disposable Git-to-Docs guarded integration proof

Observed on 2026-10-08 against original PR head `260263d77efce731dbdb240619d71985b843f72b`.
Owner: human.bryan. Authorization: the user's explicit disposable-path test request;
this is not a runtime grant, production admission or a creative decision.

## Exact source and target

Disposable branch: `agent/disposable-pr148-lease-proof-20261008`.
Source path: `.quirk/disposable/pr148-template.txt`.
Alpha commit `cfd649dec5ce8b872116f19f9e28d16485a481d0`, blob
`cde5bc610198c6c100bdfba7c8c687544f2e8090`.
Beta commit `520c38281be334c0312c6a2cfbba969dbf391b4a`, blob
`c97e6182d43866e61c52d802b30730b5ea3cbe6d`.

Immutable source: https://github.com/Quirk-Systems/quirk-os/blob/520c38281be334c0312c6a2cfbba969dbf391b4a/.quirk/disposable/pr148-template.txt

Disposable target: https://docs.google.com/document/d/1ev7b7j73AZjHyeXjWLi-I0qwvHBoUbwES3PDetTRTg0/edit
Tab `t.0`; native Docs revision IDs, requests, final text and provider error responses
are recorded in `.quirk/evidence/pr148-git-docs-run.json` under outcome.
These opaque Docs revisions are caller-bound, short-lived write leases, not permanent
historical retrieval IDs. Drive file revision IDs are not substituted for Docs revision IDs.

## Actual capabilities and outcomes

| Operation | Observation |
| --- | --- |
| GitHub fetch_file with immutable commit | Exact content and blob SHA returned; adapter verifies Git blob identity from UTF-8 bytes |
| GitHub update_file with current blob SHA | Alpha -> beta succeeded on disposable branch |
| GitHub update_file with obsolete alpha blob SHA | HTTP 409 CONFLICT; subsequent read returned beta, no stale overwrite |
| GitHub update_ref expected_sha probe | GraphQL UNKNOWN error; branch read still beta; branch lease atomicity remains unproved |
| Google Docs get_document | Returned document identity, tab indexes, text and revisionId together |
| Google Docs batchUpdate requiredRevisionId | Owner edit succeeded; obsolete revision then failed HTTP 400 INVALID_ARGUMENT, explicitly mismatching latest revision |
| Adapter-generated range delete + insert with fresh requiredRevisionId | Beta marker update succeeded; exact readback preserved concurrent owner edit, prefix, suffix and final newline |
| Replay identical adapter batch after successful update | Rejected stale revision; final revision remained unchanged |
| Generic Drive update_file | Exposed metadata/raw upload operation has no expected-version or If-Match parameter; do not use it as a conditional native-document writer |

One conflict was followed by one fresh snapshot and proposal reconstruction;
no blind retry, unguarded fallback or recurring process was installed.

## Smallest implementation

`git_docs_proposal.py` reuses `plan_changes` and `prepare_marked_update`.
It binds exact commit, path, blob and content digest to the source version;
revision and text digest to the consumer version; computes template -> document
impact; and prepares UTF-16-indexed marked-range operations with requiredRevisionId.
No-op emits no requests. Missing bindings, unpinned refs, forged blobs,
stale digests and missing/ambiguous markers fail closed.
All outputs remain inert and executable=false. There is no connector writer,
grant evaluator, provider credential, new outbox or deduplication store.

Supported proposal scope is one normalized plain-text marked tab. The caller
must reject rich elements, suggestions, headers and extra tabs before using it.
No formatting, tables, media, Unicode normalization or arbitrary document fidelity
claim is made. The actual test document contained only plain text.

## Limits and next gate

The Docs provider-side target lease is established. Git file-level SHA guarding
is established. Atomic Git branch-ref lease is not established by the failed probe.
There is no transaction joining GitHub source freshness, Docs target freshness
and grant revocation. A final source read narrows but does not eliminate the
cross-provider source race. The test consumes an immutable Git version;
if latest-source policy is required, concurrent source movement must defer or
produce another reconciliation proposal through existing coordinator policy.

Connector responses were authenticated observations in this session. The pure
adapter does not independently authenticate supplied snapshots. Durable dedup,
independent review, effect-boundary authority/revocation checks and cold handoff
remain pending. Keep runtime proposal-only until these gates are met. The next
proof is coordinator admission and source/grant-race handling, not another planner.
No production document, deployment, recurring automation, canonical authority,
provider ownership or creative choice changed. Disposable objects are retained
for inspection; removal is optional after evidence review.

## Validation

21 focused tests passed (16 existing plus five adapter tests).
Full local discovery: 454 tests run, one skip, OK. Expected failure-path diagnostics
are emitted by fixtures; they are not suite failures. New hosted validation is pending.
Exact implementation subject and blob hashes are bound by the evidence receipt.
