# Exact source boundaries

| System | Source head | Inputs and use |
| --- | --- | --- |
| OS | `138039afad0826130505eb13230c5a0844c0f572` | [PR #74](https://github.com/Quirk-Systems/quirk-os/pull/74), Attention Program engine/schema/synthetic example; native validator and receipt checker used locally |
| Preference | `f70a713c097436172760d633ccee9bacb071483b` | [PR #2](https://github.com/Quirk-Systems/quirk-preference/pull/2), image-evidence intake producer, inspector, schema and producer fixture; five pinned byte checks |
| Skills | `8fbe2e9553ff140a783eaf8bbd7d97d64ec6c47c` | [RED-stage candidate](https://github.com/Quirk-Systems/quirk-skills/tree/8fbe2e9553ff140a783eaf8bbd7d97d64ec6c47c/skills/writing-cuntsnickery); candidate, scenarios, results, STATUS and READINESS; five pinned byte checks |
| OS architecture | `499f94b8d12e29dd7804cc9b537fd70f6a8048d8` | [Move contract](https://github.com/Quirk-Systems/quirk-os/blob/499f94b8d12e29dd7804cc9b537fd70f6a8048d8/docs/product/chambered-workbench/MOVE-CONTRACT-v0.1.md) and [Transition contract](https://github.com/Quirk-Systems/quirk-os/blob/499f94b8d12e29dd7804cc9b537fd70f6a8048d8/docs/product/chambered-workbench/TRANSITION-CONTRACT-v0.1.md); candidate authority/reconciliation boundaries retained, no claimed executable integration |

The OS engine is vendored unmodified in `adapters/native/os-engine.mjs`, Git blob `d4afe4364925f3404c2e430a3f370cdd23d9c2c3`. Its command function exists in that pinned module but is never called by the adapter. Adapter code performs validation, receipt checking and reporting only. Tests exercise native local commands on synthetic inputs to construct valid receipt-bearing cases.

Preference test snapshots are not production service endpoints. Skills Markdown remains contextual evidence; the adapter does not pretend that manual READINESS text is a structured upstream API. `test/upstream/skills/source-manifest.json` preserves individual URLs and blob identities.

Source snapshots are retained solely to reproduce candidate conformance, under their source repository terms. No upstream source is relabeled as this package's authored implementation. No inference of current-head compatibility, consumer activation, human benefit or Canon status follows from a pinned test.
