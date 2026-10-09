# Private decision Inspector

The Inspector turns one source comparison into an explicit next move and finish condition. It reuses the shared OS, Preference and Skills review contract: inspect a proposed repair, choose your response, give a rationale, then preview and export an unsigned candidate record. Nothing is selected automatically.

This is a local consumer in the `Quirk-Systems/quirk-os` candidate package. It does not migrate an external application or complete the proposed repair. Decision Before Machinery, Candidate Before Canon and the existing Human Gates remain in force.

## Try the synthetic example

From the package directory, after installing dependencies and generating fixtures:

```sh
mkdir -p private
node scripts/cli.mjs inspector fixtures/review-request.json fixtures/review-next-request.json private/next-move.html
```

Open the saved HTML in a browser that runs JavaScript. [Decision-Inspector.html](Decision-Inspector.html) contains the same synthetic example. File previews may show the page without running its controls; the CLI below provides a fallback. Actual browser and iPhone interaction remain unverified.

1. Inspect a source card, including its count scope, changed fields, claims to recheck and retained holds. Choose one proposed repair.
2. Choose a response and explain why. A preview appears only after the decision passes the shared checks.
3. Read the JSON preview, then use **Download JSON**. If the viewer blocks downloading, copy the displayed JSON into a private file.

| Response | Next move and finish condition | Meaning |
| --- | --- | --- |
| Use this move (`selected`) | Preserves the proposed move and all acceptance criteria | Records this choice; does not approve execution |
| Revise it (`revised`) | Requires your own nonempty next move and finish condition | Records a revised proposal without changing the source |
| Defer it (`deferred`) | Both fields are `null` | Records why this repair should wait; does not resolve it |

Every response requires a nonempty rationale. Switching between source cards keeps each draft in page memory. Changing any answer invalidates the preview, so it must be prepared again before export. Reloading or closing the page discards unexported drafts. If the comparison has no proposed repairs, there is no decision to capture.

## Export contents and trust boundary

The export includes the full bounded displayed context: all repair options, counts, changed fields, claims and holds, plus the chosen proposal and response. It carries comparison, context and retained-request digests. It contains no raw source requests, but source references and derived text may still be sensitive. Keep real inputs, generated pages and exports outside tracked directories or under ignored `private/`; public fixtures stay synthetic.

The record fixes `status: "candidate"`, `signature: null`, `human_origin: "claim_only"`, `executed: false` and `observed_benefit: null`. Selecting a proposal cannot remove an original hold, including one absent from the newer record. Runtime, calendar, Canon, graph and training rights remain false. A rationale, timestamp or successful verification establishes neither authenticated human origin nor completed work.

The saved page checks JSON shape and internal consistency using the shared browser-safe model. It copies supplied digests; it does not authenticate their contents or verify the current upstream state. The Node builder also checks the context digest. Replay against both retained requests is required to check that the entire exported context and proposal reproduce from those inputs. Replay still does not authenticate those inputs or the person claiming the response.

The page has no network requests, external resources or persistent browser storage. Its script is authorized by a content hash in the generated Content Security Policy; this is a script restriction, not a signature for the page. Previewing changes only page memory. Downloading is an explicit local file action.

## CLI capture and verification

These commands exercise the same contract with synthetic data:

```sh
node scripts/cli.mjs decide fixtures/review-request.json fixtures/review-next-request.json fixtures/decision-answer.json private/unsigned-decision.json
node scripts/cli.mjs verify-decision fixtures/review-request.json fixtures/review-next-request.json private/unsigned-decision.json
```

For a real comparison, retain the exact before and after request files used to generate the Inspector. Verify its downloaded or copied JSON against those files:

```sh
node scripts/cli.mjs verify-decision private/before.json private/after.json private/Quirk-Unsigned-Decision.json
```

For CLI capture, supply an answer object with exactly `source_ref`, `response`, `rationale`, `next_move`, `finish_condition` and `captured_at`. The source must identify one proposed repair. The response rules above apply; `captured_at` must be a valid explicit date-time at or after the newer request's capture time. Rationale is bounded to 2,000 Unicode code points; move and finish fields to 4,000 each. The complete formatted JSON export, including its final newline, is limited to 8 MiB of UTF-8. The shared model enforces this whole-export byte limit in addition to the portable schemas. Each retained request and CLI answer input is limited to 1 MiB. A selected answer uses the first acceptance criterion as its move and all criteria joined with a space as its finish condition. `fixtures/decision-answer.json` is a runnable example; `fixtures/decision-context.json` and `fixtures/unsigned-decision.json` show the generated structures.

All CLI output paths use exclusive creation and private permissions. Use a new filename for a new result. If verification fails, retain the failed export for inspection, confirm the exact input pair, and rebuild the page or decision from corrected inputs. Do not edit digests to make a record pass. Removing the Inspector integration requires no effect compensation because it has no repair execution path.

## Reuse in another consumer

| Package export | API | Responsibility |
| --- | --- | --- |
| `./decision` | `buildDecisionContext(before, after)` | Recompute the comparison and bind the displayed options |
| `./decision` | `buildUnsignedDecision(context, answer)` | Validate an explicit response and retain the original proposal |
| `./decision` | `verifyUnsignedDecision(before, after, decision)` | Reproduce the full export against retained requests |
| `./inspector` | `buildDecisionInspector(before, after)` | Generate the self-contained page without writing a file |

The Node wrapper and generated page share `src/decision-model.mjs`; response semantics do not need separate implementations in later adapters. `src/decision-schema.mjs` generates the two portable JSON schemas. The DOM controller takes explicit clock and download dependencies; its tests exercise handlers without claiming browser conformance. Consumer adoption still owes its own source acquisition, private retention, browser compatibility and Human Gates.

## What closes this pass—and what remains

This capability closes the gap between inspecting a change and retaining an explicit, replay-verifiable response. Its shared model supports both the local page and CLI, so later application adapters can reuse the same decision semantics.

Focused contract and controller tests check intended responses and failure handling. They are not browser interaction evidence. Opening the local page for an automated browser test was blocked by the environment's browser security policy; real browser behavior, iPhone viewing and downloads still need observation.

The next useful human-use proof is one existing commitment: inspect its real change, export one response, and record whether the resulting next move was clearer and whether its finish condition was reached. Keep unknown inventory, timing and benefit unknown. A captured choice alone does not demonstrate useful completed work.
