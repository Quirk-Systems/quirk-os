# RFC Discussion Seed — Quirk-Shaped Architectural Interoperability

**Discussion status:** Seeded in repository — ready to publish as a native GitHub Discussion in the **Architecture / RFC** category once Discussions are enabled.  
**Native Discussion URL:** _(to be filled in once published)_  
**Category:** Architecture / RFC  
**Closes:** [#13](https://github.com/Quirk-Systems/quirk-os/issues/13)

---

## Context and cross-references

| Reference | Link |
|-----------|------|
| Parent issue (v0.2 repair) | [#7 — v0.2 repair](https://github.com/Quirk-Systems/quirk-os/issues/7) |
| Implementation issues | [#8](https://github.com/Quirk-Systems/quirk-os/issues/8) · [#9](https://github.com/Quirk-Systems/quirk-os/issues/9) · [#10](https://github.com/Quirk-Systems/quirk-os/issues/10) · [#11](https://github.com/Quirk-Systems/quirk-os/issues/11) · [#12](https://github.com/Quirk-Systems/quirk-os/issues/12) |
| Pull request | [#5 — Sync control plane hardening](https://github.com/Quirk-Systems/quirk-os/pull/5) |
| Interoperability contract | [`docs/sync-control-plane/INTEROPERABILITY.md`](../docs/sync-control-plane/INTEROPERABILITY.md) |
| Cloudflare ADR | [`decisions/ADR-0001-cloudflare-boundary.md`](../decisions/ADR-0001-cloudflare-boundary.md) |
| Conformance evidence | [`docs/sync-control-plane/VERIFICATION-2026-08-11.md`](../docs/sync-control-plane/VERIFICATION-2026-08-11.md) |
| Hardening notes | [`docs/sync-control-plane/HARDENING-V0.2.md`](../docs/sync-control-plane/HARDENING-V0.2.md) |

---

## Proposition

Quirk should standardize interoperability around stable object identity, independent authority grants, versioned mapping contracts, immutable receipts, and rebuildable vendor projections—not bidirectional free-for-all sync.

Quirk interoperability means:

> **stable identity, independent authority, typed translation, immutable receipts, and rebuildable projections—not everything editing everything.**

---

## Decisions requested — explicit positions needed

For each question below, participants are asked to record a **named position** (Adopt / Adapt / Defer / Reject) with a short rationale. Minority positions will be preserved in the decision record.

### 1. Canonical envelopes

> Should all platform adapters emit the same canonical `projection-envelope` schema, or may domain adapters add typed extensions?

| Position | Rationale |
|----------|-----------|
| _(add your position here)_ | |

**Proposed default:** All adapters MUST include the required canonical fields. Domain adapters MAY add optional typed extensions declared in a versioned extension schema.

---

### 2. Admitted runtime writes

> Should runtime writes always originate from an admitted manifest (`runtime-manifest.schema.json`), including human-operated maintenance tools?

| Position | Rationale |
|----------|-----------|
| _(add your position here)_ | |

**Proposed default:** Yes. Every state-changing run, including manual maintenance, MUST reference an admitted manifest. Capability and credentials never imply permission.

---

### 3. Reconstruction proof

> What is the minimum evidence for a projection to be called reconstructable?

| Position | Rationale |
|----------|-----------|
| _(add your position here)_ | |

**Proposed default:** A projection is reconstructable when: (a) the canonical source record exists and is unambiguously identified, (b) a versioned, bidirectionally-tested field mapping exists, and (c) a `sync-run-receipt` documents the last successful rebuild.

---

### 4. Cloudflare scope

> Should Cloudflare remain fully deferred (`DEFER_UNBOUND` per ADR-0001), or be admitted for a narrow edge-security role before application delivery?

| Position | Rationale |
|----------|-----------|
| _(add your position here)_ | |

**Proposed default:** Remain `DEFER_UNBOUND` until all six admission evidence items in ADR-0001 are satisfied and a separate human admission decision is recorded.

---

### 5. Receipt correction authority

> Which receipt corrections require a new human decision versus a superseding technical receipt?

| Position | Rationale |
|----------|-----------|
| _(add your position here)_ | |

**Proposed default:** Corrections that change object identity, authority grants, or Canon state require a new human decision. Corrections that fix field mapping errors or re-emit receipts for unchanged state may use a superseding technical receipt with a `supersedes` reference.

---

## Strong default platform boundaries

```text
GitHub    = Canon (versioned source of truth)
Supabase  = private runtime state and receipts
Drive     = work plane (human input surface)
Airtable  = human projection
Notion    = human projection
Vercel    = admitted delivery projection
Cloudflare = deferred edge candidate (DEFER_UNBOUND)
```

---

## Anti-patterns (to be rejected by all adapters)

- newest copy wins;
- successful execution becomes permission;
- dashboard edits silently mutate Canon;
- one vendor ID becomes object identity;
- deleted evidence is called cleanup;
- model confidence becomes release authority.

---

## Admission question

What evidence would make this contract safe enough to adopt across every Quirk repo without requiring Bryan's invisible interpretation at runtime?

---

## How to record a position

1. Reply to this Discussion (or, until Discussions are enabled, open an issue referencing this file).
2. State your position on each numbered question using the table format above.
3. Minority positions MUST be preserved — do not delete dissenting entries.
4. Decisions that achieve consensus will be converted to typed **Proposed Moves** (`proposed-move.schema.json`) or **ADRs** in `decisions/`.

---

## Next steps

- [ ] Enable GitHub Discussions in repository settings.
- [ ] Create **Architecture / RFC** category.
- [ ] Publish this seed as a native Discussion and record the URL in the `Native Discussion URL` field above.
- [ ] Link resulting Discussion URL back into [PR #5](https://github.com/Quirk-Systems/quirk-os/pull/5) and this file.
- [ ] Collect explicit positions on all five questions.
- [ ] Convert decided questions into Proposed Moves or ADRs.
