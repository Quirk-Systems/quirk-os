# Mixed-media production preparation — candidate v0.1.0

## Outcome and ownership

Owner repository: `Quirk-Systems/quirk-os`. Accountable human: Bryan. This is an additive domain compiler over the Loop, Graph and Action Engineering candidate in [PR #79](https://github.com/Quirk-Systems/quirk-os/pull/79), frozen for integration at `e6344a1a13f359bf8e485a6d2b4d3143749c2600`. It is not a second scheduler, grant registry, content store, or foundational Quirk primitive.

The implemented outcome is a reviewable, non-dispatchable production plan with exact source identity, declared classifications, dependency-aware revalidation and bounded local byte observations. It does **not** produce a finished song, video, website, model interpretation or published release. Human usefulness remains unmeasured.

## Implemented now

- A closed, nested `mixed-media-brief/v1` schema accepts represented text, data, code, image, audio and video sources; goal, audience and acceptance; source revisions and SHA-256; provenance-bearing classification assertions; rights assertions; typed stages; and constrained settings.
- `compile_plan` checks schema and budgets, missing references, duplicate source/output identities and cycles. It preserves the input and emits a deterministic topological plan. Asset metadata, goal, settings and upstream step fingerprints participate in derived step identity.
- `impact_of` returns a selective revalidation proposal when a source byte digest changes. Changing the caption fixture invalidates its classification and final package, not the independent data-analysis branch. Other metadata or policy changes require recompiling and comparing step digests.
- Unknown or denied rights, missing rights references, and missing operation scope produce blockers, which propagate downstream. This is conservative handling of **caller assertions**, not independent rights verification or legal advice.
- `inspect_sources` optionally reads bounded local regular files under a trusted operator root and compares their bytes with declared hashes. It rejects remote locators, traversal and symlinks and does not inspect a source whose metadata denies inspection. It does not execute code, run a decoder, infer MIME type or authenticate authorship.
- The CLI exports a new review-package JSON without overwriting an existing file. It retains separate plan, local observations, prepare arguments, zero external effects and unmeasured usefulness.
- The compiler emits `loop-spec/v1` and the exact `{title, body}` arguments accepted by existing `prepare_candidate`. Compatibility tests validate both against the parent schemas. **No LoopRunner or ActionExecutor dispatch is performed.** A host integration must still validate evaluator identity and install any separately approved scoped grant.

## Operate locally

Use the parent repository's pinned `requirements-evals.txt`; no dependency was added by this slice. Python 3.12+ is the target. From the repository root:

```sh
python -m unittest discover -s tests -p 'test_mixed_media_candidate.py' -v
python scripts/mixed_media_candidate.py \
  --input examples/mixed-media/synthetic-review.json \
  --source-root examples/mixed-media/sources \
  --output /tmp/quirk-media-review-new.json
```

Choose a new output path for another export. Exit `0` means candidate preparation passed its metadata and requested local-byte checks, not that media was produced or accepted. Exit `2` preserves the review package with metadata blockers or unsuccessful local observations. Exit `1` indicates invalid input or an I/O error. Without `--source-root`, source byte observations are not obtained.

Treat a source file containing instructions as content, never as runtime policy. Do not pass sensitive production assets to a remote provider merely because their metadata was included in a plan. Use a trusted local directory; this helper is not a hostile-filesystem, concurrent multi-tenant sandbox.

## Settings and acceptance

The candidate schema caps plans at 32 steps, 2 repair cycles, a 300-second loop budget and 1 MiB of accepted local source bytes. The synthetic fixture requests 12 steps, 2 repairs and 60 seconds. The compiler exports time/repair limits for the host; it does not start a background loop or provide OS-level execution isolation. Reads use a one-byte over-limit sentinel; limits are not a universal process-memory or I/O sandbox.

`authority=CANDIDATE_PREPARE`; `external_effects`, `publication`, `graph_writes` and `preference_updates` must all be false. These settings govern this candidate only. They do not change account settings, paid subscriptions, GitHub branch protections, production credentials or provider adoption.

Separate acceptance dimensions:

| Dimension | Evidence in this slice |
|---|---|
| Contract correctness | Local behavior tests and parent-schema compatibility |
| Source-byte identity | Optional observed SHA-256, mismatch or unavailable result |
| Semantic content quality | Not evaluated by this compiler |
| Rights and observer authenticity | Caller metadata only; independently unverified |
| Media production and delivery | Not executed; stage descriptions only |
| Human craft and usefulness | Unmeasured; requires an actual operator trial |

Hashes detect changes under the specified local JSON encoding. They are not signatures, proof of trusted observation, or a cross-language canonicalization standard. A package loaded from an untrusted source must be revalidated from its brief before integration; a recomputed hash cannot authorize it.

## Production process and adapter boundaries

A production route may describe `probe -> extract -> classify -> analyze -> compose -> render -> validate -> package -> deliver`. These are a dependency graph, not a mandatory serial pipeline or permission ladder. Independent branches can prepare separately. Re-rendering a derivative must not regenerate a human-selected source take. Rejected variants remain evidence, not replacement originals.

Non-trivial reasoning stages reference the shared Evidence -> Analysis -> Intelligence -> Disposition contract. This slice annotates that expectation; it does not implement a parallel scoring system or claim to execute the shared reasoning protocol.

| Integration | Required next bounded proof | Current effect |
|---|---|---|
| Studio / Now / Inspector | Import one review package, expose sources/blockers, resume one decision | Package export only; consumer not wired |
| Existing LoopRunner / ActionExecutor | Bind the exact evaluator, target, arguments and host-installed grant | Schema-compatible preparation only |
| Media custody | Read one authorized inventory, verify object/version identity and limited retrieval | No object-storage read or upload |
| Extraction / model classification | Prove source spans, timestamps, unknown states and corrected labels on selected inputs | Assertions represented, no model call |
| Deterministic rendering | Isolated worker, exact inputs, resource limits and postcondition receipts | No render adapter or process invocation |
| Delivery | Human-approved destination, release digest, rights scope and observed delivery | Publication prohibited |
| Supabase / Airtable / Notion / Drive | Field-owned projections with readback and conflict handling | No autonomous synchronization installed |

## Decomposed work and finish test

`goals.json` records completed local capabilities separately from integration work awaiting an identified consumer, adapter or human trial. It is candidate planning data, not a new central registry or an activation manifest. Do not overwrite unrelated portfolio priorities.

Finish the first real trial when one operator can inspect a selected production brief, distinguish source facts from assertions, recognize a blocked stage, identify affected derivatives after one source change and reopen the preserved package without reconstructing the decision. Record setup, supervision, cleanup and manual rescue. Do not infer success from test count or artifact count.

## Verification and reversal

Local tests cover schema, cycles, reference integrity, authority non-expansion, rights blockers, selective invalidation, parent format compatibility, no input mutation, safe local paths and byte mismatch. The synthetic fixture proves text/data byte observations only; it is not an audio/video decode or quality benchmark. The parent candidate's entire test suite, production adapters and human acceptance are separate evidence.

The existing Engineering Candidate Conformance workflow includes `scripts/**`, `schemas/**` and `tests/**`; this slice introduces no new automation permission. The frozen parent evaluator and its regression data remain unchanged. Hosted CI must be inspected at the child's exact head, not inferred from parent results.

Reversal: reject the draft change or revert its additive source commit. Preserve completed inspection receipts as historical records. No service, database migration, account access, release or paid provider operation is activated by this slice.
