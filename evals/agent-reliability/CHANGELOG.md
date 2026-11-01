# Agent reliability candidate changelog

## 2026-10-07 — PR #108 validation repair

- Reject empty, whitespace-only, and non-string authority policy/object snapshot digests.
- Require completion evidence digests to be nonempty strings.
- Reject supplied malformed and non-finite production scores while retaining the missing-production-data status for absent scores.
- Add three adversarial regressions: 54 focused tests and 171 repository tests pass locally.
- Preserve candidate-only evaluation, zero effects, and no runtime authority. Hosted checks and fresh repaired-head review remain required.
