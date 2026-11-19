# Changelog

## 2026-10-05 — Intent Shaper issue #131

- Apply purpose, validity, precedence, and conflict checks to current instructions with personalization enabled or disabled. Off-mode projections use the selected records and perform no saved/profile/persona/history reads.
- Validate complete Personalization Plans with timestamp formats, purpose and validity checks for used preferences, and normalized Persona Hand weights (absolute tolerance `1e-9`). Empty off-mode hands remain valid.
- Bind draft-skill status to its contract declaration; example output cannot hide self-admission. Keep Intent Shaper outside the manifested runtime registry.
- Add eight adversarial conformance fixtures and regression coverage for all ten findings. Refresh the synthetic harness fixture's material digest without representing its test-data counts as execution evidence.

This is the implementation successor to the already merged, zero-file PR #134. Evidence remains candidate-only; this change grants no runtime, admission, deployment, or merge authority.
