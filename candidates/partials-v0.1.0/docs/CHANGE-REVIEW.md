# Change review — candidate capability

Owner: `Quirk-Systems/quirk-os`. Capability: `capability.partials-change-review/v0.1.0`. This vertical slice turns two retained review requests into an inspectable comparison and bounded Proposed Moves. It performs no source acquisition, correction, execution, admission, or automatic timestamp refresh.

The prior review capability answers whether records agree with supplied expectations. This consumer answers what changed between reviews, which claims need rechecking, and the smallest proposed repair. Acceptance evidence is deterministic replay, complete source accounting, honest uncertainty, retained holds, inert rendering, and executable adversarial cases. Native inputs, existing policies and all effect rights are protected.

## Run the consumer

```sh
node scripts/cli.mjs compare fixtures/review-request.json fixtures/review-next-request.json new-changes.json
node scripts/cli.mjs compare-panel fixtures/review-request.json fixtures/review-next-request.json new-changes.html
```

The [saved example](Changes-Panel.html) contains synthetic changes to existing adapter fixtures. It illustrates an OS expectation advancing ahead of its record, a Preference source replacement carrying old structural-check labels, a removed Skills source, and an unresolved malformed input. These are test cases, not observed user outcomes.

For application integration import `compareReviewRequests`, `verifyReviewChanges` and `renderReviewChanges` from `@quirk-systems/partials-candidate/changes`. Preserve both original request files. The API reruns the full source-aware review; it does not trust an uploaded result or receipt as truth. The after capture must be at or later than before. Each request remains bounded to 32 entries / 1 MiB, so a comparison has at most 64 source rows. Output writes use new filenames and private file permissions.

## Meaning and mapping

| Signal | Treatment | What remains unproved |
| --- | --- | --- |
| Exact `source_ref` in both requests | Pair the two rows, including quarantined and duplicate inputs | Authentication and current upstream state |
| Renamed reference | Removed plus added; no fuzzy identity merge | Whether it is actually the same source |
| Changed record ID, subject tuple, or full scope | Replacement; carried satisfied labels require revalidation | That earlier claims hold for the replacement |
| Changed knowledge, evidence, work, availability | Report changed fields independently; retain before/after count wording | Real completion, benefit or authority |
| Changed provenance or capture | Show recapture as an assertion; propose substantiation where needed | That a new timestamp means fresh evidence |
| Changed expectation, age limit or count policy | Report independently from record facts and compare review disposition | That a looser policy is justified |
| Removed source or hold | Keep removal visible and retain prior valid holds | Completion or discharge of an obligation |
| Invalid record | Opaque fingerprint and unresolved-input hold | Hidden fields and obligations |
| Duplicate order change | Identify representative by source reference; distinguish review accounting from record content | Additional independent evidence |

Every input's source reference survives into one union row; no domain totals are added. Review-context time changes are recorded even when all source rows remain unchanged. Invalid records are never used for nested facts, evidence labels, count summaries or authority claims. Their unknown obligations are explicitly unresolved. All aggregate authority values remain fixed to propose-only; repairs also individually carry no-execution and human-review requirements.

## Proposed repair selection

The consumer proposes at most one primary repair per row. It prioritizes invalid input, source removal, removed holds, missing expectations, identity conflicts and failed source checks, followed by changed policy, replaced bindings, recapture, additions and other changes. All changed fields remain visible even when a higher-priority repair is selected. A Proposed Move includes target reference, before/after evidence digests and an explicit acceptance condition. It is not a task admission or an instruction to perform an external operation.

For source replacement, an intersection of `evidence.satisfied` labels is named `claims_requiring_revalidation`. It means the same claim text appears on both sources; it does not establish truth, semantic equivalence or independent support. Newly introduced labels remain assertions. No automatic merge or evidence transfer exists.

## Recovery and lifecycle

Keep original requests and comparison artifacts. A correction produces a new native source or an explicitly corrected projection, then a new request and comparison. Do not alter old timestamps merely to make a review pass. A comparison receipt binds both request digests and its entire output before the receipt. `verifyReviewChanges(before, after, result)` checks exact replay of the complete result. None of these unsigned digests is an authenticated ledger.

Migration: existing partial, review-request and review-result contracts are unchanged. The new output is `quirk.partials-review-changes/v1alpha1`; consumers must opt into this specific schema and API. Rollback removes the comparison import or CLI call and retains sources; no calendar, graph, runtime or Canon compensation is needed.

## Compounding dividend and open work

Implemented: reuse of the existing validators and mobile shell; source-change classification; evidence-carryover warnings; prior-hold retention; Proposed Move acceptance conditions; comparison schema, CLI and synthetic fixtures. Evaluated fixture families include mixed-source retention, identity accounting, uncertainty, stale guidance and successful capability denied self-promotion. Controller, publishing, canonical reconciliation, research and routing fixtures are outside these operations.

The change-review tests are authored by a separate model agent after a read-only review of the existing consumers. This is implementation support, not independent human approval. The shared source manifest and compounding evidence bundle bind the delivered code and declare the limits of measured results.

OPEN: authenticated expectation acquisition, external Inspector wiring, observed browser/iPhone interaction and correction, independent human review, and measured user benefit. The cheapest next proof is for a person to inspect one real source change, choose or correct its proposed repair, and report what the view helped finish. Timing and benefit remain unknown until reported or measured.

Disposition: **Constrain**. Comparison and proposed repairs are implemented locally; authority and release claims remain candidate-only.
