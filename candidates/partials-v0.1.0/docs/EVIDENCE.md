# Candidate evidence and limits

Disposition: **Constrain**. This candidate implements the shared foundation and three local adapters. Full deployed system-wide support, real-world benefit and admission are unearned claims and remain unassessed.

Validation commands and machine-readable results are in `evidence/`. `evidence/files.sha256` binds the checked package files; Git history binds the delivered candidate. Generated outputs and evidence themselves are excluded from that file list to avoid circular hashes. The evidence producer is the implementing assistant, with separate model review of the core and parallel adapter implementation. This is not independent human review.

| Check | Observed result | Scope |
| --- | --- | --- |
| Node conformance | 94 tests passed in the final recorded run | Unknown/zero, bounds, conflicting states, fixed authority, revision correction, real pinned input compatibility, mobile markup and CLI behavior |
| Independent validator | Python jsonschema 4.26.0; eight partial fixtures plus three review/comparison fixtures valid; thirteen structural negatives rejected | Draft 2020-12 structure and explicit stdlib date-time checker; not independent semantic equivalence |
| Reproducible inputs | Deterministic fixture generators; native source blob checks | Source identity and adapter shape compatibility |
| Static panel | Separate axes, lower bound, hold visibility, inert escaped input, no script/network/form elements | Markup and CLI tests; no actual browser interaction or iPhone task observed |
| Recovery | Stale predecessor, source drift, lost holds and overwrite attempts rejected; correction emits linked receipt bundle | Local projection recovery, no authenticated global ledger |

The independent validator initially exposed that its environment lacked the optional date-time checker. An impossible February date incorrectly passed until the independent script registered a stdlib checker. The final script explicitly exercises that negative; optional extras cannot silently bypass it.

No private conversation, user schedule, initiative names, self-reported benefit or private record is included in this candidate's evidence. Synthetic examples illustrate partial information only. Future real-use evidence must retain exact build/input provenance and distinguish subjective clarity from completed work, time savings and benefit net of effort.

Remaining release blockers: independent human code/contract review, actual mobile/browser review and correction, observed commitment completion and benefit, and each consumer's head-bound migration test. Complete schema validation or green workflows do not close these blockers. No Brag Tax admission or Ship It Without Bryan pass is claimed.

Source-aware review followup: `docs/SOURCE-REVIEW.md` defines the mission, bounded consumer operations, failure recovery, fixture comparator and remaining claims. `evidence/compounding-bundle.json` records its candidate capability dividend; prior evidence remains in Git history at d6b5beb7d2329c3fcd69d13585506d3800a39ad7.

Change-review followup: `docs/CHANGE-REVIEW.md` defines exact-reference pairing, source-binding replacement, opaque invalid inputs, retained holds and prioritized proposed repairs. Sixteen separately authored API/adversarial tests plus one CLI proof extend the prior 77-test suite. These model-authored tests do not satisfy independent human review. The comparison adds no external-effect path.
