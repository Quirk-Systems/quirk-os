# Loop, Graph, and Action Adoption Implementation Plan

> For agentic workers: use Superpowers subagent-driven development, test-first behavior changes, task review, and whole-branch review.

**Goal:** implement the approved adoption design as executable candidate machinery and tested provider projections.

**Architecture:** `quirk-os` owns canonical contracts, a local reference implementation, and projection SQL. `quirk-run` retains its existing Cloudflare activation boundary and receives behavioral proof coverage. Durable logs record observations; graph relationships and provider projections cannot mint authority.

**Tech stack:** Python standard library plus existing JSON Schema dependencies; PostgreSQL projection SQL; existing TypeScript/Cloudflare adapter. No paid compute or production deployment is necessary for the candidate proof.

**Spec:** `docs/engineering/ADOPTION-SPEC.md` (approved by Bryan's comprehensive adoption request).

## Global constraints

- Candidate implementation/testing is authorized. Existing production, admission, public-access, and irreversible-action gates remain applicable.
- `quirk-os` base: `499f94b8d12e29dd7804cc9b537fd70f6a8048d8`.
- `quirk-run` inspected PR #2 head: `850e5718377751d40cff68cde2db7c943b4b7e6b`; its PR #71 contract binding remains unchanged.
- No inference of human usefulness, preference acceptance, immutability, or effect verification from self-reported flags.
- Existing test fixtures are not rewritten to fabricate stronger authority.
- Version changed receipt semantics explicitly; old receipts are declarations and cannot be admitted as observed evidence.
- Changes are implemented in isolated paths; agents own disjoint files. Root integrates, reviews, and publishes candidate PRs.
- Live Supabase project is inactive; prepare/test migrations locally without restoring or deploying it implicitly.
- HF connection lacks repository-write scope; support portable dataset artifacts without claiming upload.

## Task 1: Cloudflare runtime proof

**Owner/files:** separate `quirk-run` snapshot; `tests/**`, `src/**` only where a demonstrated defect requires repair, package/test configuration, existing candidate CI, verification documentation.

**Consumes:** exact existing PR #2 source and fixtures, obtained through the authorized GitHub connector if clone authentication is unavailable.
**Produces:** executed fixture evidence and regression coverage while preserving the source contract, `PREPARE` ceiling, authentication, and no external mutation bindings.

- [x] Materialize exact source and inspect instructions and test entrypoints.
- [x] Exercise both existing fixtures through production functions and, when available, the local Cloudflare runtime.
- [x] Add adversarial cases for changed source binding, overscope, malformed input, unauthenticated calls, repeated activation identity, and pause behavior. Example assertion: `assert.equal(receipt.status, 'PAUSED_AUTHORITY_CHANGE')` using the actual emitted shape after inspection.
- [x] Repair reproduced defects, run type/bundle checks and actual behavior tests, and record the distinction between host logic and workerd integration.
- [x] Review the diff; return exact commands, results, and any unproved runtime surface.

## Task 2: Action contracts and truthful receipts

**Files:** `scripts/engineering/actions.py`, `scripts/engineering/ledger.py`, new versioned action/receipt schemas, `scripts/sync_control_plane/skill_runtime.py`, affected skill receipt tests, `tests/test_engineering_actions.py`.

**Consumes:** existing manifest, runtime-grant, and receipt identities. Trusted host-provided grant registry and adapters are distinct from model-proposed action data.
**Produces:** `validate_action(action, grant, *, now, current_target_digest, revoked_grant_ids=()) -> list[str]`; a durable local action ledger; execution result containing observed status and evidence. Publish exact adapter/ledger interfaces to root before implementing dependents.

- [x] Write regression showing a new receipt cannot assert observed scope or enforced immutability with no observation: `self.assertNotEqual(receipt.get('no_authority_escalation'), True)`.
- [x] Add and fail resource/arguments/digest/expiry/revocation/idempotency tests.
- [x] Implement strict target/argument binding, pre-dispatch revalidation, durable intent/outcome records, and fail-closed reconciliation of uncertain effects.
- [x] Use local bounded read/prepare adapter effects for executable examples; arbitrary external dispatch is not enabled.
- [x] Introduce explicit observed-receipt version and migration documentation; preserve historical schema as historical evidence format.
- [x] Run affected existing tests and new adversarial cases, then review.

## Task 3: Evidence graph and database projection

**Files:** `scripts/engineering/graph.py`, `tests/test_engineering_graph.py`, versioned graph schemas, `supabase/migrations/*engineering*`, `supabase/tests/engineering_projection.sql`.

**Consumes:** immutable object/version identities; observations/assertions with source/digest/time/status; no authorization inference.
**Produces:** `EvidenceGraph(objects, assertions)` with `support_for(object_id, digest, *, now)`, `impact_of(object_id, *, max_depth=8)`, and `context_for(object_id, digest, *, now, max_items=20)` returning bounded JSON-serializable records. Expose exact record shape before dependent code.

- [x] Fail tests for stale digest support, contradictory assertions, bounded cycle traversal, expired evidence, and preference-as-authorization rejection.
- [x] Implement typed relationship validation, source/version freshness, impact traversal, and bounded context extraction.
- [x] Add separately governed PostgreSQL candidate projection with RLS, least-privilege access, append-only observations, and no grant tables writable by clients.
- [x] Execute SQL verification locally if PostgreSQL-compatible runtime can be installed; otherwise preserve an explicit unexecuted gate.
- [x] Review Python and SQL behavior independently.

## Task 4: Bounded loop, evaluation, and interoperability

**Files:** root owns `scripts/engineering/loop.py`, `scripts/engineering/projections.py`, `scripts/engineering/__init__.py`, `scripts/run_engineering_pilot.py`, `tests/test_engineering_loop.py`, `tests/test_engineering_projections.py`, `examples/engineering/**`, `evals/engineering/**`, `.github/workflows/engineering-candidate.yml`, documentation.

**Consumes:** Task 2 action/ledger and Task 3 graph interfaces. Root resolves integration changes before consumer implementation.
**Produces:** a deterministic local pilot CLI, frozen evaluation metadata, resumable bounded control loop, redacted provider projection payloads, and actual integration inventory.

- [x] Write and fail loop tests: unchanged-state stop, fixed acceptance/evaluator digest, repair budget, interruption/resume, missing evidence, duplicate work, and authority-change pause.
- [x] Implement immutable run spec, durable checkpoint/events, time/step/repair budgets, stop reasons, and evidence-triggered invalidation/repair scheduling.
- [x] Add explicit evaluation records for capability/regression/held-out comparisons, judgment provenance, and manual-rescue accounting. Unknown human usefulness remains unknown.
- [x] Exercise real PR #2 metadata as a sourced candidate input; classify reported build proof separately from executed behavior proof.
- [x] Export bounded Airtable records, HF-compatible JSONL, and MCP/A2A interoperability descriptors. Only execute a remote projection when the actual target and allowed semantics are established.
- [x] Add a CLI demonstration and eleven adversarial fixture coverage mapping; enforce them in CI.
- [x] Run full existing Python suite, new suites, actual SQL/runtime checks available, and independent final review. Fix concrete findings before candidate PR publication.

## Preflight interface review

| Pair/task | Check | Resolution |
|---|---|---|
| Actions ↔ loop | Durable result and uncertain outcome shape needed | Action owner publishes API before root writes consumer. |
| Graph ↔ loop | Context has exact source and version references | Graph owner publishes shape; root pins it in integration tests. |
| Actions ↔ graph | Graph cannot grant action authority | Pass trusted grant separately at dispatch; graph only explains dependencies. |
| SQL ↔ provider exports | Database projection and Airtable/HF exports cannot self-admit | Candidate-only data, no accepted-grant writes. |
| Each task | Outputs match stated candidate scope | Tests distinguish declaration, observed behavior, and human judgment. |

## Completion record

Actual commits, commands, results, provider limits, review findings, and PR URLs are recorded in `docs/engineering/VERIFICATION.md`. Passing synthetic fixtures never substitutes for Bryan's usefulness judgment or production approval.

Implementation/review checkboxes record candidate work only. Human usefulness measurement, skill admission, merges and production rollout are not completed by these checks. Provider observations and the eight verified Airtable projection writes are recorded in the verification document and example receipt.
