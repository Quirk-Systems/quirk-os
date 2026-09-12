# Carry Forward usefulness evaluator

Candidate code for deciding whether an assisted task merits another attempt. A lower work time can disappear after setup, supervision, cleanup and maintenance. This evaluator accounts for all five costs and keeps the person's judgment about meaning separate from arithmetic.

This directory is a reusable component, not a complete workbench or an installed skill. Its tests are synthetic. It contains no populated career records. It uses no runtime model calls or network requests.

## Run

Node.js with built-in `node:test` support is sufficient; tested with Node v24.19.0. No packages are required.

```sh
node --test examples/carry-forward/usefulness.test.cjs
```

```js
const U = require('./examples/carry-forward/usefulness.js');
// trialSpec must match UsefulnessTrial.schema.json.
// U.validate(trialSpec) returns true or throws.
// U.evaluate(trialSpec) returns a candidate assessment, never an action grant.
```

The browser UMD global is `QuirkUsefulness`. The schema defines the input; the companion implementation additionally rejects numeric overflow. JSON Schema format validation must be enabled by a downstream schema validator.

## Interpreting output

| Field | Meaning |
| --- | --- |
| `baseline_total_minutes`, `assisted_total_minutes` | Sum of five supplied cost fields, or null when any is unknown. Consult each input's basis before labeling a total observed. |
| `delta_minutes` | Baseline minus assisted total only when all completeness gates pass; otherwise null. A positive value alone does not establish benefit or causality. |
| `evidence_state` | `observed` means supplied observations are complete, not independently authenticated. `estimated` and `incomplete` cannot claim measured savings. |
| `recommendation` | `needs_evidence`, `review_keep`, `review_tradeoff`, or `review_drop`. Every result is a review proposal. |
| `state`, `authority` | Always `candidate` and `propose`. |

Completeness requires a meaningful task with reason, performed actual use with timestamp and description, evidence and retained-asset references, retained-value description, comparable tasks, known error counts, and fully observed costs. More errors or an equal/higher assisted total requires tradeoff review. A recorded judgment that the task does not matter suggests reviewing whether to drop it.

The pure evaluator checks reference syntax only. Its host must resolve every exact reference and withhold the recommendation and delta when evidence is missing, stale, conflicting, expired, rights-unknown, fictional or derived. A generated retained asset can be useful; it cannot serve as evidence of a real outcome. The host must reject future observations. Arbitrary supplied notes are not authenticated facts.

The optional `validation/` checker addresses structural defects found during a separate skill evaluation. It is not called by this evaluator and is not an authorization engine.

[Usefulness protocol and ownership](../../docs/product/carry-forward/README.md)
