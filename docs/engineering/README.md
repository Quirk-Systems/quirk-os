# Loop, Graph, and Action Engineering — candidate implementation

This package implements the approved adoption design as executable candidate machinery. Run it on a source pointer to produce an evidenced next-proof card, retain the action history, and identify what must be rechecked when its source changes. It does not admit skills or expand an existing grant.

The implementation status below supersedes the research-time observations in [ADOPTION-SPEC.md](ADOPTION-SPEC.md). The original spec remains a dated design record. [VERIFICATION.md](VERIFICATION.md) records execution evidence and unresolved live gates.

## Run the pilot

From the repository root, with Python 3.12+ and Node 24:

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements-evals.txt
.venv/bin/python scripts/run_engineering_pilot.py --input examples/engineering/runtime-pr2.json --state-dir /tmp/quirk-engineering-pilot --output /tmp/quirk-engineering-pilot-result.json
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
.venv/bin/python scripts/validate_engineering.py --repo .
npm ci --prefix supabase/tests --ignore-scripts
npm run --prefix supabase/tests test:engineering
```

The input is a captured GitHub PR pointer at an exact head, not a live fetch. Refresh it through an authenticated source reader before using it for a new decision. The example preserves the PR body's reported build status separately from observed local behavior. Upstream code and human usefulness are not evaluated by this pilot.

Use a dedicated state directory per host fixture environment. It contains SQLite event ledgers, the current source pointer, and a host-created fixture grant. The grant is limited to the built-in local adapter and expires after one hour. `--now` provides a deterministic simulation clock; it must not be used as live authorization time. The CLI is intended for one local operator; concurrent filesystem pointer updates are not a distributed ingestion service.

Read the top-level `status` and `current_applicability` for present reuse. `loop` and `action_receipt` preserve historical results. Reusing a successful historical run with an expired or changed grant returns `PAUSED_AUTHORITY_CHANGE` without rewriting its original receipt. A new source revision creates a new run; stale support remains visible as excluded evidence.

## Implemented responsibilities

| Responsibility | Implementation | Boundary |
|---|---|---|
| Loop Engineering | `LoopStore` and `LoopRunner`: frozen objective, acceptance and evaluator; durable checkpoints/events; step, repair, attempt and time budgets; interruption recovery; unchanged-failure stop | Trusted bounded callbacks; cooperative time checks cannot preempt arbitrary blocking code |
| Graph Engineering | Typed objects/assertions, source and version digests, time validity, contradictions, supersession, tenant visibility, bounded support/impact/context queries | Evidence and preference edges cannot authorize an action |
| Action Engineering | Strict action and grant schemas, target/argument binding, fresh dispatch check, durable intent/outcome ledger, observed local postconditions | Built-in bounded read/prepare adapter only; uncertain effects require reconciliation |
| Context and harness engineering | Exact source pointers, independently stored state, frozen run spec, bounded graph context and explicit stale references | A source reader still has to establish the truth and freshness of submitted metadata |
| Evaluation engineering | Adversarial regression cases, fixed evaluator digests, paired comparison under equal budgets, separate observed human measurements | A passing synthetic test is not a human usefulness result or rare-failure guarantee |
| Tool and interoperability engineering | Typed operations plus strict local MCP/A2A-shaped envelope normalizers using the same executor | Local compatibility only; no live protocol server or protocol conformance claim |
| Observability and recovery | Run/action/step identities, append-only events, observed hashes, attempts, elapsed time, stop reasons, idempotent replay | SQLite owner can alter storage; hashes do not authenticate observers |
| Judgment engineering | Scoped pairwise judgment candidates with source/observer references; accepted preference remains unknown | Collector provenance must be checked independently; a candidate cannot accept itself |
| Complexity discipline | One controller per run, bounded independent work, paired trials, explicit coordination and rescue accounting in the trial protocol | Broader orchestration requires measured benefit before expansion |

## Contracts and compatibility

`action-contract/v1` carries the existing skill ID, version, manifest digest and runtime grant ID, plus exact target, target digest, canonical argument digest, postcondition, effect bounds and recovery policy. The trusted host installs grants separately. Neither source content, graph edges nor transport envelopes can install a grant.

`action-receipt/v2` reports observed local postconditions and the exact grant snapshot checked at dispatch. Subsequent revocation prevents replay while leaving a truthful historical observation intact. Intent without a recorded outcome is uncertain; it is never blindly repeated. No claim of exactly-once external effects is made.

`build_run_receipt` now emits `skill-run-receipt/v2`. Its scope and storage assertions remain unknown. The historical v1 schema remains available to read old records; consumers must distinguish both historical v1 and `skill-run-receipt/v2` declarations from observed `action-receipt/v2` evidence. No existing receipt is upgraded by changing a version label.

The evidence graph accepts `supported_by`, `contradicted_by`, `depends_on`, `blocked_by`, `produced` and `prefers`. Authorization stays in the separate trusted grant registry. `impact_of` produces a bounded revalidation plan; it does not dispatch repair or grant permission. Revalidation is triggered by submitting changed source metadata in this version; no unattended scheduler is installed.

Local transport adapters accept versioned `quirk-mcp-action/v1` or `quirk-a2a-action/v1` envelopes. They are normalizers around the same exact action contract. See `tests/test_engineering_interoperability.py` for complete executable envelopes. Switching transport retains the idempotency identity and cannot widen the resource/argument scope. A production MCP/A2A connection additionally needs authenticated principals, negotiated capabilities, transport tests and the same Quirk authorization boundary.

## Providers and operating ownership

| Provider | Candidate adoption | Next live proof |
|---|---|---|
| GitHub | Contracts, implementation, regression cases, CI and reviewable PRs; exact tree binding for runtime proof | Required repository checks and maintainer review at the final head |
| Supabase | Private PostgreSQL evidence projection, RLS, separately governed ingestion and append-only observations; local behavioral SQL tests | Restore or select an active target, then test real Auth/PostgREST/JWT integration and advisors before migration rollout |
| Cloudflare | Existing runtime proven in actual local workerd; malformed input, ceiling, identity and receipt-binding repairs in [quirk-run PR #3](https://github.com/Quirk-Systems/quirk-run/pull/3) | Scoped live account binding, staged deployment, production identity/recovery tests |
| Airtable | Additive candidate records with stable identities, source/evidence references, content hashes and forced non-admission semantics | Verified readback is recorded separately; future sync must reconcile by stable Record ID |
| Hugging Face | Portable JSONL regression descriptions and dataset card; explicit synthetic/public export boundary | Repository-write scope and an identified dataset destination before upload; paid jobs are not needed |
| Agent Ready | Site scan attempted; TLS handshake failed before any page was scanned | Establish reachability, rerun, then fix confirmed discovery/accessibility defects |
| Superpowers and Quirk routing | Isolated implementation, failing regression cases before fixes, independent scoped review and verified completion | Human usefulness and release/admission decisions remain their own evidence lanes |

Runtime owners maintain dispatch and reconciliation. Evidence owners maintain object/version identity and visibility. Workflow owners own acceptance and budgets. Human reviewers own actual usefulness judgments. Provider projections remain rebuildable views of those records.

## Expansion decisions

Use the trial protocol in `evals/engineering/README.md` to compare a direct baseline with the candidate on 12 representative cases. Counterbalance order, retain correctness and manual-rescue evidence, and measure reconstruction time. A proposed directional goal is at least 25% less median reconstruction time with no correctness loss or authority expansion. No such improvement has yet been observed.

Add model routing, graph retrieval depth, additional agents or automated repair only to address a measured failure. Freeze the evaluator and comparison budget before each trial. After two meaningful repair cycles without useful lift, retain provenance/receipt improvements and remove the extra orchestration. Published regression examples cannot also serve as an untouched held-out set.

Production rollout requires observed live identity, tenancy, retention, concurrency and recovery behavior on the chosen adapters. These are explicit implementation gates, not silently satisfied by local test counts. The candidate SQL and SQLite ledgers store bounded records; establish payload retention and redaction policy before ingesting sensitive production content.
