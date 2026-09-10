# Quirk partials foundation — candidate v0.1.0

This package represents useful incomplete information without converting unknowns into zeros, unfinished work into success, or available capability into authority. It provides an executable common record, three source adapters, a CLI, and a saved mobile review panel.

**Status: candidate, propose only.** Owning candidate repository: `Quirk-Systems/quirk-os`. This is the shared foundation stage. Adapters execute locally against pinned input shapes; consumers have not been deployed or migrated. No runtime, calendar, Canon, preference graph, training, admission, or submission grant exists.

## Use locally

Node 22+ is required; tested with Node 24.19.0. From this directory:

```sh
npm ci --ignore-scripts
npm run check
npm run fixtures
node scripts/cli.mjs report fixtures/os-partial.json 2
node scripts/cli.mjs panel fixtures/os-partial.json fixtures/preference-partial.json fixtures/skills-partial.json my-review.html
```

The report says the known lower bound exceeds 2 while the total remains unknown. The panel is a static HTML file with no scripts, network resources, connections, forms, or effect controls. Open [Example-Panel.html](docs/Example-Panel.html) as a saved file for a synthetic example. An actual iPhone task and browser interaction remain unverified.

For independent structural checking, install `jsonschema==4.26.0` in a Python environment and run `python scripts/independent_schema.py`. The script explicitly registers a stdlib date-time checker because optional format dependencies must not silently skip invalid dates. It validates the schema and eight fixtures and rejects ten structural negatives. `assertRecord` adds cross-field semantics; a schema-only pass is insufficient for consuming records.

## Contract and APIs

For bounded source-aware consumption, use the new [source review capability](docs/SOURCE-REVIEW.md). It compares explicit expected subject versions/digests, checks capture age, accounts for every input, and quarantines mismatches before rendering. `review-panel` is the first shared local consumer; external application wiring remains pending.

| Dimension | Meaning | Does not imply |
| --- | --- | --- |
| `knowledge` | Known identities, lower/upper bounds, explicit exact count within a named scope | Whole-system inventory or capacity |
| `evidence` | Satisfied, missing, conflicting checks and limitations | Completed work or authenticated human truth |
| `work` | Completed, remaining, failed units | Successful evaluation or safe retry |
| `availability` | Present, missing, unverified inputs | Permission to use an input |
| `authority` | Fixed propose-only ceiling plus retained upstream holds | Any executable grant |

`src/schema.mjs` is the one schema source; `schemas/partial-record.schema.json` is generated. `createRecord(overrides)` constructs a full record with unknown defaults for the four dimensions. `assertRecord(record)` rejects non-JSON, structural and semantic violations. `digestJSON(value)` uses sorted object keys, preserved array order and SHA-256; it is a local content identity, not a signature or a claim of RFC 8785 conformance. Records name a subject version/digest, scope, explicit capture time and source references.

`evaluate(record, {maxCount})` returns information and holds, always with `effectExecutionAllowed:false`. Bounds and counts only apply to that record's scope; comparing an OS initiative count with a Preference event count is invalid. Counts are never summed across adapters. A source-declared exact count remains a source assertion.

`reviseRecord(previous, replacement, {expectedDigest, reason})` accepts an explicit complete replacement, retains the prior digest and emits a receipt. It rejects stale predecessors, changed source/version/scope, and removed upstream holds. A new source version requires a new record and adapter evaluation. No implicit merge, global replay ledger, authenticated history, partial-effect retry, or Canon promotion is implemented.

## Adapt existing inputs

```sh
node scripts/cli.mjs adapt os test/upstream/os/program.example.json fixtures/os-options.json new-os-record.json
```

All CLI output paths use exclusive creation and private file permissions. Existing files are never overwritten. Keep private input, options, records and panels outside tracked directories or under ignored `private/`. Never place real schedules or conversation inventories in fixtures.

- OS: `fromOSProgram(program, {capturedAt, asOfDate, inventory?, useReport?})`. Validates the exact native Program shape and receipt chain using the byte-pinned candidate engine. Optional inventory is `{program_digest,known_items,lower_bound,source_refs}` for outside discretionary work; it cannot overlap inside identities or contradict a confirmed count. A use report is `{report,source_ref}`; it cannot create an observation, elapsed minutes or completion. Nothing calls `applyCommand`.
- Preference: `fromPreferenceInspection(inspection, {capturedAt, sourceRefs?})`. Consumes the pinned inspector output; valid local counts and replay semantics are checked. A last-page flag never establishes full export completeness. Metadata lineage, image bytes, unsigned identity, human origin, benefit and graph/training holds remain separate. Compatibility tests actually run the native producer and inspector.
- Skills: `adaptSkillsReadiness(input, options)`, where input is `{candidate,scenarios?,results?,artifacts?}` and options require `capturedAt` and nonempty `sourceRefs`. Optional `scenarioInventoryComplete` and `artifactInventoryComplete` default false and refer only to their own inventories. Artifact acquisition metadata states are `present`, `missing`, `unverified`, `intentionally_absent`. Historical RED reports are expected-negative history; they are not current passing results. Fixture sources require `provenanceKind:'synthetic'`.

See [adoption and recovery](docs/ADOPTION.md), [source pins](docs/SOURCES.md), and [evidence boundaries](docs/EVIDENCE.md). No user testimony or personal schedule is included in the public candidate.
