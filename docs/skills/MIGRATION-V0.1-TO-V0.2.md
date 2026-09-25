# Migration — Skill Packages v0.1 to v0.2

## What changed

v0.1 consisted primarily of portable prose procedures. v0.2 preserves those procedures and adds machine contracts, immutable identity, executable evals, runtime loader boundaries, receipt grammar, and an explicit mapping contract.

## Per-package migration

1. Preserve the original skill ID and procedure.
2. Add versioned frontmatter and candidate status.
3. Add `manifest.json`.
4. Bind the manifest to the exact `SKILL.md` Git blob SHA.
5. Compute the canonical manifest SHA-256.
6. Register four eval classes.
7. Route runtime use through an external admission decision and scoped grant.
8. Record executions with immutable receipts.
9. Route feedback to a successor candidate rather than mutating v0.2.

## Compatibility

- Existing references to the skill ID remain valid as candidate-source references.
- Runtime activation references must additionally pin version and manifest digest.
- Existing `quirk_sync` candidate manifest rows are projections and must be reconciled to these digests before any admission.
- No v0.1 package is implicitly admitted or superseded merely because v0.2 exists.
- Any mismatch creates a typed Proposed Move; it is never silently repaired.

## Rollback

Remove the v0.2 manifest/eval projection or pin the previous candidate source. Do not delete v0.2 evidence. Record a superseding decision and retain both versions.
