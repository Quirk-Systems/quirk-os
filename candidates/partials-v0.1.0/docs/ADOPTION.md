# Adoption and recovery

## Decision

Own one candidate contract in Quirk OS, with adapters at the same version. Keep native inputs authoritative for their original purpose; the common record is a derived projection. This avoids incompatible meanings of PARTIAL across consumers while allowing useful uncertainty to survive transport.

The shared record is intentionally richer than a boolean and intentionally narrower than an orchestration runtime. A partial execution can be recorded in `work`, but existing Transition/Move rules still require reconciliation and idempotency decisions before retry. The evaluator cannot authorize or perform retry.

## Expansion order and finish conditions

| Stage | Candidate owner / consumer | Concrete finish condition | Current state |
| --- | --- | --- | --- |
| Shared foundation | quirk-os | Full closed record, evaluator, provenance, correction receipts, static projection; adversarial and independent schema checks | Implemented in this package |
| OS adapter | PR #74 Attention Program | Validate real Program inputs, carry partial inventory as bound sidecar, preserve native unknown/start/protected-time holds | Implemented and locally tested; native panel migration pending |
| Preference adapter | quirk-preference intake PR #2 | Run pinned producer/inspector, preserve page scope, replay limits, missing lineage, bytes and unsigned source | Implemented and locally tested; consumer wiring pending |
| Skills adapter | quirk-skills RED-stage candidate | Preserve historical result vs unexecuted vs missing result, artifact absence, candidate holds | Implemented and locally tested; readiness view wiring pending |
| Shared local review consumer | quirk-os CLI/mobile file | Compare explicit source expectations and age policy; account for stale, conflicting, duplicate and malformed inputs; reproduce receipt | Implemented in `src/review.mjs`; external app wiring and human use pending |
| Move / Transition | quirk-os chambered workbench | Bind partial effects to exact invocation, receipts and reconciliation before retry; retain per-effect authority | Future adapter; never infer from this record alone |
| Core / graph / memory | owning repositories | Versioned projection persistence, identity mapping, stale invalidation, lossless readback, no count aggregation across scopes | Future design and conformance proof |
| Feed / Operator Shell / API surfaces | owning applications | Render shared validated records, preserve unknown fields and holds, fail closed on unsupported schema, observe mobile review and recovery | Future integration and human use |

These rows are the rollout queue, not a statement that every repository has been inventoried. No external initiative is started, paused or reprioritized by the table.

## Consumer integration contract

1. Pin package version and source-head compatibility. Load native input without changing it.
2. Call the specific adapter with explicit capture time and attributable source references. Never coerce `null`, an omitted inventory, empty page or partial result to zero or success.
3. Run `assertRecord` on all incoming stored records. Independently compare the record's source digest/version with the consumer's expected source, or rerun the adapter. `assertRecord` cannot determine upstream freshness. Unknown schema/version, malformed input or a detected stale source is a blocked projection, never fallback to a guessed complete state.
4. Show separate axes and exact scope. Display a known lower bound even when the total is unknown. Show upstream holds near any proposed next action.
5. Keep all effect decisions in the existing owning authorization path. No `within`, `complete`, `available` or `supported` state grants a right.
6. Before consumer rollout, prove native-shape compatibility at its new exact head, side-by-side display, malformed/stale-source rejection, and an observed human review and correction. Record effort and benefit separately from technical tests.

## Correction, removal and rollback

An existing projection is never edited in place by the CLI. For representation correction of the same source, supply the full replacement and expected old digest to `reviseRecord`; the result is a new record plus reasoned receipt. The CLI saves both as one bundle with an exclusive output path. The source tuple and scope must remain fixed. Retain prior bundles yourself; the candidate provides no durable or authenticated ledger.

If the source itself is corrected, obtain the new native input, rerun its adapter and create a new record. Treat the old record as historical; do not carry a passing check across the source digest change. Compare versions explicitly. Deduplicating overlapping counts or reconciling contradictory sources requires a separate scoped decision; this candidate refuses to auto-merge.

To recover from an invalid input or partial output failure, repair the input and use a new output filename. No source mutation has occurred. To roll back a consumer integration, remove its rendering/import call and retain native input and old projections for inspection. Reverting this candidate package does not require calendar, graph, runtime or Canon compensation because it has no external-effect path.

## Human-use closure still owed

The smallest next proof is one person reading the partial view for a real existing commitment, identifying a next move and its finish condition, then correcting one mistaken or missing item. Capture the exact build/source record, what changed, whether the commitment finished, and actual operation/review/correction time if known. Preserve unknown timing and incomplete inventory. Browser simulation and automated fixtures do not count as this observation.
