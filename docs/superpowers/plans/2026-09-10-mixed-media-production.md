# Mixed-media production candidate implementation plan

**Goal:** Compile bounded mixed-media briefs into reviewable dependency plans without provider effects.
**Architecture:** Add a pure compiler and local-byte inspection CLI to the existing quirk-os candidate. Emit the existing loop-spec/v1 and prepare_candidate argument shape. Do not extend the action executor, install grants, or modify the frozen parent evaluator.
**Tech stack:** Python 3.12+, existing jsonschema dependency; no added package.
**Spec:** ../../mixed-media/README.md

## Global constraints
Owner repository: Quirk-Systems/quirk-os. Base: PR #79 at e6344a1a13f359bf8e485a6d2b4d3143749c2600. Candidate only. No source media uploads, production activation, publication, graph writes, preference updates, automatic grants or schema promotion.

## Tasks
- [x] Tests: run `python -m unittest discover -s tests -p 'test_mixed_media*.py' -v`; observe failure before compiler implementation.
- [x] Implement `compile_plan(brief)`, `impact_of(plan, revisions)`, `inspect_sources(brief, root)`, `prepare_arguments(plan)` and CLI in scripts/mixed_media_candidate.py against the accompanying executable tests.
- [x] Verify strict schema, DAG references/cycles, branch-local invalidation, rights gates, immutable inputs, fixed authority, finite budgets, path confinement, digest mismatch, unsupported operation and bounded export.
- [x] Compile synthetic-review.json and inspect its two local source files; preserve actual results in the private/local execution receipt.
- [x] Publish additive files on a child candidate branch and open a stacked draft PR; leave parent and main unchanged.
- [x] Reconcile current projection labels on existing Notion/Drive/Airtable records; never rewrite historical proof or last-sync timestamps.
- [x] Read back every remote write and record remaining live/provider/human-use gates rather than claiming full production completion.

## Completion evidence and limits

Draft PR #81 preserves this additive implementation on a child of PR #79. Implementation head `54273281de451f81d04b6c531138cb9254f7bb49` passed 36 local tests with zero skipped and three hosted workflows: Golden Gates, Sync Control Plane Conformance, and Engineering Candidate Conformance. The hosted engineering job also reports successful full Python tests, frozen regression, candidate pilot and private SQL projection steps. The local checkout contained this slice plus exact parent schema snapshots; it did not rerun the complete parent suite locally.

The existing Drive and Notion control-plane documents received a candidate implementation handoff and were read back. Notion's stale PR #5 draft label was corrected and old runtime proof was labeled historical. Fresh Airtable reads showed its earlier stale merge assertions were already reconciled, so those records and their old synchronization timestamps were preserved. Eight new candidate preparation/integration Moves were written to the existing Work Queue and read back: four Done preparation tasks, one Proposed consumer task and three Waiting adapter, human-trial and delivery tasks. Native private workspace IDs are intentionally excluded here.

Supabase management still reported INACTIVE; no restore, migration, production adapter, sharing change, or paid provider operation was performed. Independent code review and real human usefulness remain unverified. The compiler's zero-external-effects assertion does not describe the separately authorized source/document/work-record edits performed by the host assistant.
