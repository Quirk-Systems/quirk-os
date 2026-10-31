# Agent reliability candidate changelog

## 2026-10-08 — Ubuntu 26 migration preflight

- Add a read-only, 15-minute Ubuntu 26.04 job running the same Python 3.12 fixtures, validator, pinned eval dependencies, and repository regressions as the existing job.
- Verify the exact PR head and record the runner image. Preserve the original check and all governance boundaries.
- Ubuntu 26 compatibility requires hosted results at the recorded head; no merge or runtime authority is granted. Revert the added job to remove the probe.

## 2026-10-07 — PR #108 validation repair

- Reject empty, whitespace-only, and non-string authority policy/object snapshot digests.
- Require completion evidence digests to be nonempty strings.
- Reject supplied malformed and non-finite production scores while retaining the missing-production-data status for absent scores.
- Add three adversarial regressions: 54 focused tests and 171 repository tests pass locally.
- Preserve candidate-only evaluation, zero effects, and no runtime authority. Hosted checks and fresh repaired-head review remain required.
