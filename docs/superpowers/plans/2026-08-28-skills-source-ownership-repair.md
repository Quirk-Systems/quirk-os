# Skills Source Ownership Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans.

**Goal:** Repair stale `quirk-os` documentation so `quirk-skills` is recognized as the portable candidate source owner while `quirk-os` retains runtime/projection responsibilities.

**Architecture:** Documentation-only projection repair. Existing local `quirk-os/skills/*` candidates remain untouched; no package migration, registry admission, runtime change, or authority transfer is performed.

**Tech Stack:** Markdown.

**Spec:** Approved three-PR design, 2026-08-28.

## Global Constraints
- projection-only
- candidate-only
- no runtime behavior changes
- no movement/deletion of existing Skill packages
- no changes to `skills/registry.json`
- no admission/canon implication

### Task 1: Repair architecture ownership wording
- [ ] Update `docs/skills/ARCHITECTURE.md` to replace future `quirk-skills` language with present candidate-source ownership.
- [ ] Preserve `quirk-os` ownership of loader/routing/grants/receipts/runtime projections.
- [ ] Label existing local packages as legacy/local candidates pending explicit migration decisions.

### Task 2: Repair Skills README projection
- [ ] Add source-ownership note to `skills/README.md` without changing package inventory or authority.

### Task 3: Verify and open draft PR
- [ ] Confirm only plan/docs changed.
- [ ] Open draft PR with no runtime or registry effect and independent merge gate.
