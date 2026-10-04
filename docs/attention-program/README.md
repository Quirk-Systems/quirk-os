# Attention Program

Candidate implementation under `Quirk-Systems/quirk-os`. This module makes one Goal and one bounded Program inspectable and usable as local planning records. It does not activate a Quirk runtime manifest or change existing governance policies.

## Goal and success

Complete one existing recurring commitment with less total human effort while preserving essential obligations and limiting discretionary work in progress.

The initial method is a 14-day trial. Its duration, two-use evidence threshold, and two-initiative WIP limit are explicit trial choices, not empirically optimal values.

Three conditions define evidence supporting the goal:

1. At least two comparable trial uses were completed and reported useful by the human beneficiary.
2. Credited baseline effort exceeds all trial operating, review, correction, setup, and maintenance effort. Unconfirmed costs or a missing comparable baseline keep the result inconclusive. Only completed, useful trial deliveries receive baseline credit; failed attempts still incur their full costs.
3. Required evidence reports no displaced protected obligation, and WIP is within the declared program and self-reported outside inventory. The trial ends in a recorded keep, revise, pause, or stop decision. A keep decision does not authorize expansion or prove improvement by itself.

These are self-reported operational observations. The tool cannot independently verify hours worked, completeness of the outside inventory, truth of entries, or benefit experienced by another person.

## Program workstreams

| Workstream | Mechanism delivered | Human input still necessary |
| --- | --- | --- |
| Capacity and commitments | Known sleep/work/commute constraints; optional initiative queue; WIP checks | Current outside initiative count and availability of a proposed time slot |
| Bounded execution | Initiative phases, next moves, session budget and conflict checks | Perform the actual planning or other selected work |
| Evidence and burden | Baseline/trial observations, all-in effort arithmetic, unknown and adverse results | Record actual observations and confirm overhead, including honest zeros |
| Decision and ending | Trial expiry, pause/recovery, explicit closure, no automatic renewal | Choose and explain keep, revise, pause, or stop |

Workstreams organize one program; they do not each create a discretionary initiative. Existing duties and essential care consume capacity before optional work. Cluster IDs are optional navigation and never confer authority.

## Start locally

Node 24 is the tested CLI environment. There are no downloaded packages or network dependencies.

```bash
node tools/attention-program/cli.mjs validate programs/attention-program.example.json
node tools/attention-program/cli.mjs report programs/attention-program.example.json --as-of 2026-01-06
node tools/attention-program/cli.mjs build programs/attention-program.example.json --out /tmp/attention-demo.html
node --test tools/attention-program/engine.test.mjs
```

The checked-in example is synthetic and date-frozen for reproducible testing. It contains no observed benefit. Copy it outside a public checkout, set the actual owner, dates, goal, schedule, and initial initiative, and leave unknown inventory and costs unconfirmed. Do not put private program records in this public repository.

Open the generated HTML in a modern browser. It contains the engine and initial record and requires no server, account, CDN, or model. The browser must provide Web Crypto for receipt hashes. A script-disabled preview is a document preview, not an execution environment; open the downloaded HTML in a browser for the controls.

The panel supports inventory confirmation, adding and changing initiatives, checking and editing the known schedule, planning and canceling sessions, recording and correcting evidence, recording costs, changing trial phase, closing, exporting, importing, and restoring the original record. Every mutation updates the visible local record and creates a receipt. Planning a session does not write to any calendar.

Browser changes stay in that browser's storage. Export JSON to retain a portable copy, especially before clearing storage or changing devices. Generated HTML is a snapshot; browser changes do not modify the original saved HTML or synchronize to another application. Import validates data and receipts before asking to replace the current local record. Export is available when browser storage fails. Restore requires a deliberate user action.

## CLI record updates

Write the command in a local JSON file:

```json
{"type":"confirm_inventory","external_in_progress":0}
```

The zero above is illustrative. Enter the actual outside count; do not use zero to represent unknown.

```bash
node tools/attention-program/cli.mjs apply /path/program.json /path/command.json --expected-revision 0 --out /path/program-next.json
```

The CLI validates the prior record and receipt chain. Explicit expected revision prevents accidental stale updates. Output files use exclusive creation and do not overwrite an existing record. `--at` permits deterministic replay of a supplied UTC timestamp with milliseconds; timestamps are reported context, not trusted attestations.

For the date-frozen synthetic example only, append `--at 2026-01-06T12:00:00.000Z` to the apply command. Otherwise today's date correctly makes that historical trial expired. For real records, set current trial dates during initial definition and use the actual current time; do not backdate commands to evade expiry.

## Boundaries and failure behavior

- Source definition: versioned candidate JSON/schema and engine in this repository.
- Operational record: private JSON, held by the operator. Browser HTML is a replaceable local view over that record.
- Authority: `candidate`, `propose`, `external_effects: false` remain fixed. Program phases describe local work tracking only. The module has no external adapters, credentials, canon promotion, merge, deployment, messaging, deletion, or calendar authority.
- Capacity: calculations subtract the union of declared constraints, including overnight sleep and alternating work weekends. Remaining time is before other life needs. A session additionally requires the operator's availability confirmation. No real calendar is inspected.
- Evidence: observations are separate from planned sessions. The program never marks work complete because a plan, file, or fixture exists. Imported observations cannot use a fixture source.
- Recovery: rejected commands leave the prior record unchanged. Schedule updates must remain compatible with retained plans. Canceling a session frees its budget. Correcting an observation replaces its current values once; it does not add another observed use. These three operations retain the original value in the receipt even when it came from a revision-zero seed. Use these commands rather than hand-editing a receipt-bound exported record. Export/import restores valid snapshots. Simultaneous browser edits must surface a revision conflict. Receipt hashes detect inconsistent local records; anyone able to rewrite all bytes can recompute them. They are neither signatures nor independent evidence.
- Stopping: expired/closed trials cannot start new work. Historical evidence and cost corrections can still be recorded so late data is not hidden. Closure needs a disposition and reason; renewal requires a separately defined trial.
- Privacy: private records are never uploaded by this module. Shared arrangements and third-party data still need their applicable consent.

## Design decisions

1. Extended the existing operating foundation rather than creating a new system or repository. Its README already separates definitions, enforcement, and projections, and `programs/quirk-sync-control-plane.yaml` establishes candidate Program records.
2. Chose a deterministic local runner over a model-driven controller. Limits, interval arithmetic, validation, and honest unknown states require no model calls.
3. Kept operational benefit separate from program completion and technical test status. Passing fixtures cannot create field evidence.
4. Kept the 111-cluster taxonomy optional. The operating record needs only the distinctions that change decisions.
5. Kept one useful next move visible. No automatic task generator, new recurring notification, or compulsory tracking of relationships or leisure is introduced.

## Acceptance and admission

The implementation includes executed acceptance/adversarial tests and a reproducible CLI. See [EVIDENCE.md](EVIDENCE.md) for actual results and limitations. The capability deposited is a candidate local program evaluator and portable record interface.

Admission disposition: **Constrain** — local candidate record operation and review. Field effectiveness, broader independent usability, production integration, and Quirk-wide admission remain unproven. Existing human admission and repository merge requirements remain in force.

The decisive next move for an actual trial is to confirm existing discretionary commitments and choose one genuinely available planning slot. A baseline can then be observed without inventing prior timing.
