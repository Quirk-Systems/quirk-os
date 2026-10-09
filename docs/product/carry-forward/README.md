# Carry Forward candidate continuation

An assisted workflow earns another attempt when the result matters, one actual use demonstrates its value, and something retained makes the next attempt easier. Automation count and polished assets are insufficient evidence.

This proposal adds a dependency-free usefulness evaluator, synthetic tests, an input schema and an optional evidence-bundle structural checker. A separate private Career workbench consumes the evaluator. This public repository contains reusable definitions and tests; populated career records remain in their existing private working home. The Career domain retains its ownership and Drive remains authoritative for its working records.

## One bounded use

1. Choose one task and write its acceptance criteria before attempting it. For an application draft, criteria may include supported claims, clear unresolved qualifications and correctly sourced pay. A generated example is not a real submission.
2. Record a comparable baseline. If only a remembered estimate exists, label it estimated and withhold measured savings.
3. Perform one assisted attempt. Count setup, work, supervision, cleanup and maintenance. Leave unknown costs null. Record errors against the same criteria. Future maintenance is unknown or estimated until observed.
4. Retain one useful asset or correction with an exact version and evidence link. Explain how it helps the next attempt.
5. Let the person doing the work judge whether the result mattered and record keep, mutate, drop or undecided. Recompute after a source changes. One trial supports a local decision, not general effectiveness or causality.

Collect only what supports that decision. The initial trial may use a ten-minute operator budget; that budget is a proposal, not elapsed time or an established saving. Development, evaluation, setup and ongoing maintenance effort are not counted as zero merely because runtime model calls are zero.

## Design in the private workbench

The existing visual structure is retained. One Usefulness panel records incomplete drafts without replacing unknown values with zero. A note-capture timestamp is distinct from the time actual use occurred. Results display human disposition, evidence completeness, reference blockers and the next review action. Saving keep does not change an asset or confer authority.

Workspace 0.1 imports migrate to 0.2 while retaining object versions, quarantine and preparation receipts. Legacy browser storage remains recoverable. A 0.1 import containing the newly introduced trial kind is rejected. Corrupt saved data must not be silently overwritten.

## Integration boundary

| Responsibility | Owner / behavior |
| --- | --- |
| Reusable code, contracts, tests | Git; candidate proposal only |
| Career facts, review packets, application decisions | Existing Career domain and private Drive records |
| In-browser projection | Private local workspace; no automatic source edits or external actions |
| Supabase | Optional private snapshot proposal; unapplied and not connected |
| Admission and runtime activation | Not granted by tests, human disposition, a draft PR, or database persistence |

The Supabase proposal is an inspectable future contract. It requires an active test database, supported migration tooling and executed ownership/RLS tests before any integration claim. See [SUPABASE_CONTRACT.md](SUPABASE_CONTRACT.md).

## Evidence and limits

The generic evaluator has synthetic behavior tests covering overhead, incomplete evidence, quality tradeoffs, estimates, malformed values and authority-field injection. The optional checker has its own Python regression suite and provenance. The private host separately checks reference graphs, migration, actual form handlers and standalone packaging; those private fixtures are not published here.

Browser rendering and human cold use are unverified. No real time saving, hiring result, independent observation authentication, live Supabase compatibility or production readiness is asserted. Current disposition: constrain to candidate use, then evaluate one real task.
