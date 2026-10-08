# Change maintenance — candidate v0.1.0

Change receipts extend PR changelogs to plans, goals, code, agents, configs,
defaults, templates, vocabulary, documents, design and media. This module belongs
to the existing Sync Control Plane; it creates no new authority plane.

## Implemented scope

`scripts/sync_control_plane/change_maintenance.py` provides a deterministic,
side-effect-free dependency planner and marked-text preparation guard. It
accepts an asserted current snapshot, orders affected objects, and proposes
receipt preparation or dependency-impact review. No connector, scheduler,
database migration, live grant verifier, transaction executor or device agent is
installed. Existing PR automation remains separately scoped.

Owner: Quirk OS. Human authority and creative taste remain with Bryan and the
actual object owners. Bryan, Brayn, BryMinn and Brayk are contexts/personas, not
four inferred permission grants. Department, device and provider boundaries
must have named bindings and accountable owners.

## Apply at the correct time

| Trigger | Required response | Timing |
| --- | --- | --- |
| New artifact or meaningful revision | Prepare concise version-bound change receipt | After current source read and validation |
| Goal, contract, default or vocabulary changes | Traverse consumers; propose impacted revisions | Before dependent work resumes |
| Policy, permission, ownership or binding changes | Reconcile authority and invalidate affected evidence | Before any effect |
| Provider, model, schema or device environment changes | Recheck compatibility and affected obligations | Before reuse of previous proof |
| Review or actual human decision | Record exact source/version and disposition | After independently retrieving decision |
| Merge, publication or closure | Record actual observed disposition | After source confirmation; never infer shipment |
| Cosmetic change | Skip consequence escalation if reviewed diff preserves meaning | Receipt only if materially useful |
| Missing evidence, offline provider, ambiguous markers | Defer with owner and resume proof | Immediately; preserve source/history |

Cosmetic/material classification is an adapter/reviewer responsibility, not a
confidence threshold or a feature implemented by this planner. Avoid producing
notifications for identical state. No recurring monitor is created.

## Hierarchy and operations

Resolve source identity and object owner, then authority/policy, contracts,
dependency versions, obligations/evidence, proposed transformation, projection,
and observed outcome. Dependency order always overrides heuristic priority.
For independent ready objects, order authority, contract, goal, plan,
config/agent, template/vocabulary, code, document/design/media, then projection.
Priority never manufactures permission or changes a legal state transition.

The planner rejects cycles across the entire supplied graph, missing edges,
duplicate identities, provider binding collisions, unknown fields/enums and
excessive graphs (256 objects, 1,024 edges). It propagates offline/unknown
prerequisites into deferral. Inputs and completed-key ledger are asserted,
not authenticated. A resolved ledger entry means the coordinator has verified
the operation and receipt; agents must not manufacture completed keys.

Deduplication binds planner version, source object/current version/disposition,
consumer and its entire prerequisite lineage (versions, bindings, platforms,
owners and kinds). A version must change whenever the referenced content,
policy, dependencies, environment or settings change; provider revisions must
be paired with content hashes when revisions omit those changes. Old events
are refreshed against the supplied current snapshot and flagged as stale.

## Input and output contract

`plan_changes(objects, event, completed_keys=())` accepts objects containing
exactly `object_key`, `version`, `kind`, `platform`, `owner`, `binding_id`,
`dependencies` (object keys), and `availability` (`online`, `offline`, `unknown`).
Kinds and platforms are explicit allowlists in the module; a new provider
requires a contract change. Event fields are exactly `object_key`, `version`,
and `disposition` (`proposed`, `accepted`, `closed`, `superseded`). Disposition is
an observation used for planning; `accepted` does not prove admission.

Output includes the resolved source version, stale-event flag, ordered actions,
prerequisites, owner, idempotency key, state and next gate. Every action is
`executable=false`; every result has `effects_executed=0` and
`authority_effect=false`. States are proposed, deferred or unchanged.

## Adapter obligations before live integration

| Surface | Owns | Required effect boundary |
| --- | --- | --- |
| GitHub | Repository-owned definitions and proposed source changes | Exact SHA + expected branch lease; candidate PR |
| Drive | Authored work/drafts and review projections | Fresh revision; provider-native conditional update or exclusive lock |
| Supabase | Admitted private runtime ledger/outbox | Transactional grant, policy, object version and dedup checks |
| Airtable / Notion | Rebuildable views and work queues | Stable binding, observed version, conditional write or serialized adapter |
| Vercel | Admitted interface delivery | Existing deployment gate; receipt does not authorize deployment |
| Devices | Local intake/cache and user surfaces | Explicit device binding, encryption/retention policy, offline reconciliation |

An adapter without conditional-write capability must remain proposal-only until
it has a tested serialization strategy. Reading immediately before writing
alone does not eliminate a race. Revalidate grants, revocation, policy and object
versions inside the effect boundary. A rejected lease stops the write; fresh
reads may retry at most twice before deferral. Existing outbox retry/dead-letter
rules continue to govern delivery; this module does not replace them.

`prepare_marked_update(current_text, expected_digest, entry)` preserves all
outside bytes, rejects partial/multiple/reversed markers, blocks a mismatched
SHA-256 text digest, and returns an identical-entry no-op. It uses
`<!-- quirk-change:start -->` / `<!-- quirk-change:end -->`, distinct from the
PR-specific changelog markers. This is preparation, not a provider compare-and-swap.

## Receipt and maintenance rules

Record date, object/current version, disposition, concrete consequence, source
links, tested versions/commands, evidence gaps, owner and next gate. Keep local
results separate from independently retrieved hosted evidence. Use existing
`sync-run-receipt.v2` for actual state-changing runs and `sync-decision.v1`
freshness/trigger-route envelopes for proposals; do not introduce another
append-only evidence store. Corrections supersede receipts rather than edit them.

Pause the affected dependency chain, not unrelated departments. Escalation must
include object/version, observed failure, accountable owner, attempted bounded
recovery, and the proof needed to resume. Preserve disagreements and creative
variants. Taste decisions require actual human judgment. Rights, privacy and
retention remain required before media distribution or productization.

## Reproduce and evaluate

From repository root:

```sh
python -m unittest discover -s tests -p 'test_change_maintenance.py' -v
```

Fixtures test GitHub goal -> Drive plan -> Supabase agent -> device projection,
transitive impact, deterministic ordering, ownership/version invalidation,
offline deferral, unknown inputs, collisions, cycles, duplicate suppression,
concurrent edits and surrounding-text preservation. These are synthetic tests;
they do not establish multi-provider interoperability or independent usability.

Baseline: PR-only receipts with no cross-object impact traversal. The deposit is
an inspectable deterministic planner and reusable text guard. No model is needed
for ordering or write safety; prose generation and materiality judgment remain
separate, version-bound review tasks.

Admission decision: **Constrain** to candidate planning and text preparation.
Independent cold-handoff, real provider race tests, authenticated provenance,
durable ledger, revocation and three downstream usefulness trials are pending.
No Golden, complete, production-ready or system-wide enforcement claim is made.

Decision: reuse the Sync Control Plane instead of building a parallel receipt
system or letting every provider edit every object. Rollback: remove this
additive module, tests and document; no runtime data or existing defaults change.
The disposable Git-to-Docs path now has an observed provider-native target lease,
Git file-SHA conflict rejection, safe owner-text preservation and replay rejection.
See [GIT-DOCS-PROOF.md](GIT-DOCS-PROOF.md) for exact versions and limits.
`git_docs_proposal.py` remains an inert request preparer; runtime admission is unchanged.
Next move: independently review coordinator authority/revocation and cross-provider
source-race handling; durable deduplication and atomic branch-ref lease remain unproved.

Sources: current Sync Control Plane INTEROPERABILITY.md, README.md,
sync-decision.schema.json and sync-run-receipt.schema.json at base
`03f70e1a790bac09294fe0f31a3c5f0d0fb4418e`; user direction on 2026-10-08.
