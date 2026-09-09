# Attention Program — implementation evidence

Admission: **Constrain** to local candidate record operation and review. No production, canon, runtime-manifest activation, or measured-life-improvement claim is made.

## Executed checks

| Check | Observed result |
| --- | --- |
| `node --test tools/attention-program/engine.test.mjs` | 46 tests passed; zero failed or skipped, Node v24.19.0 |
| CLI validate/report/build | Synthetic program validates; absent evidence produces inconclusive/null benefit; standalone HTML builds |
| CLI apply and rejection | Revision-zero record updates to revision one; stale revision and altered receipt-bound record rejected without creating output |
| Generated combined module | `node --check` passes after engine and record insertion; no unresolved build markers |
| Static interface checks | 91 unique IDs; 40 label targets resolve; no remote resource URLs or `innerHTML` sinks |
| Existing Golden Project Pack validator | Candidate merge checks pass; 16 pre-existing Golden-admission holds remain |
| JSON Schema | JSON syntax and correspondence to record shapes reviewed; an independent Draft 2020-12 validator was not executed |
| Browser interaction/visual check | BLOCKED: Cloud Browser URL policy refused the generated local file; no workaround attempted after that rejection |

The repository workflow runs the deterministic tests, validates the synthetic record, and builds a portable synthetic view with read-only repository permissions. Local execution is recorded here; GitHub CI status is separate and must be read from its actual run.

## Adversarial coverage

The executed corpus covers unknown and incomparable baselines; unconfirmed costs; failed task costs without completion credit; negative net benefit; mixed comparison groups; protected-obligation displacement; unknown and excessive outside WIP; sleep, commute, overnight work and alternating-weekend conflicts; overlapping plans; budget exhaustion; expired and closed trials; optional clusters; reserved authority injection; duplicate IDs; invalid dates, types, numeric values and sources; stale revisions; immutable inputs; changed receipts; state/receipt mismatch; and invalid imported plans.

Recovery cases additionally prove that schedule edits cannot invalidate retained plans, canceling a plan frees its budget while preserving the original value, observation correction affects totals once, prior values survive from revision-zero seeds, and unknown correction IDs are rejected.

## Counterevidence and repairs

- An early formula could have credited failed trials with baseline savings. The implemented formula credits completed, useful deliveries and charges every trial attempt.
- Two regression cases exposed supported outcomes despite unknown or excessive outside WIP. After repair, unknown WIP makes the overall result inconclusive and measured WIP excess makes it not supported. Measured effort arithmetic remains separately visible.
- Interface review found no supported way to change a schedule, cancel a plan, or correct an observation. Those three command paths and prior-value receipts were added and tested.
- A delegated CLI handoff required two recoveries: supplying a date inside the synthetic trial and supplying UTC milliseconds. The exact successfully executed syntax is now shown in README/help.
- The local Playwright runtime lacked a browser binary; its attempted binary download failed. Cloud Browser then rejected local-file navigation by policy. Browser interaction, responsive rendering, iOS behavior, export download behavior, and multi-tab browser behavior remain unverified. Static checks are not substitutes for those claims.

## Provenance and limits

Base: `499f94b8d12e29dd7804cc9b537fd70f6a8048d8` in `Quirk-Systems/quirk-os`.

The source hashes in [implementation-evidence.json](../../evals/attention-program/implementation-evidence.json) identify the implementation and acceptance corpus checked in this turn. The receipt excludes itself to avoid a self-referential digest. The eventual commit and CI run provide separate exact-head evidence.

Root implementation, delegated engine/tests/interface work, and the CLI handoff share model lineage and conversation context. They are useful engineering checks, not independent human admission. Actual beneficiary completion, user effort, upkeep, capacity outside the record, and outcome benefit remain unmeasured. Unknown fields in the private operating instance were not filled with fixture values.

The supported handoff audience is a technically comfortable operator using Node or a capable browser. Cold CLI use succeeded with the recorded recoveries. A broad first-time nontechnical usability claim is withheld until observed interaction testing succeeds.

Compute cost and human review time are unknown. No new paid service, running scheduler, deployed endpoint, or ongoing model dependency was created by this implementation.
