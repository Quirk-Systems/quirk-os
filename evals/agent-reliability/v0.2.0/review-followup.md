# PR 154 review and repair — 2026-10-31

Original reviewed head: a73c8fef356977403fe4dbf2cbfd035c1edc22c3.
Base: 03f70e1a790bac09294fe0f31a3c5f0d0fb4418e.

Confirmed findings, repaired:
- P2: null/list/scalar task contracts raised AttributeError instead of INVALID_PAIR.
  Added five malformed contract subcases; observed failures before repair.
- P2: fixture inventory accepted altered expected labels. Freeze each registered
  expected verdict and validate inventory shape, provenance and case structure.
  Added failing relabelled-answer and malformed-inventory regression tests first.
- P2: the initial PR had no repository Evidence Binding receipt covering its diff.
  The standalone verification-receipt.json is historical author evidence, not a
  replacement for .quirk/evidence/evidence-receipt.v1. Add a subject-bound receipt.
- Portability: replace hardcoded /tmp test cwd with TemporaryDirectory.

Local follow-up: 14 assurance tests pass; full discovery runs 447 tests with one
skip and no failures (446 passed). Existing 58 reliability tests remain included.
Golden candidate gates and agent conformance pass; 16 Golden admission holds
remain. Initial dependency gap was resolved by installing requirements-evals.txt.
Original verification receipt is preserved as historical evidence, superseded for
current code claims by the follow-up receipt. No independent review is asserted.

Hosted run 41208744315 at original head failed before executing steps (empty step
list, runner_id=0). This establishes no hosted test result. Do not call CI green
or infer the exact infrastructure cause. Repository rulesets are empty and main
is unprotected in inspected API state; no required check is being removed.

Human merge authorization: Bryan said “Merge when confident. Iterate until
confident.” This covers this PR, not deployment, production authority or Canon.
Technical scope remains synthetic/local candidate evaluation. Source truth,
reviewer authentication, live models and production enforcement remain unproved.
Preserve history with a merge commit so evidence subject ancestry survives.

Reusable lesson: test malformed nested values, not only missing top-level keys;
fixed case names are insufficient without a fixed expected-answer inventory.
