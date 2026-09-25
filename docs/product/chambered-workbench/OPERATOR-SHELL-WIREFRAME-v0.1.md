# Operator Shell Wireframe v0.1

**Status:** Candidate  
**Scope:** Low-fidelity product-design artifact  
**Object:** `object.demo.intake-to-lineage.v0.1`  
**Authority ceiling:** `propose`  
**Runtime effect:** none

## Purpose

Show one object moving through the initial chamber path:

```text
Aperture → Foundry → Constellation → Gallery
```

The wireframe proves the core interface rule: the active object moves, but evidence, authority, risk, and the transition ledger remain visible throughout.

## Persistent shell

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ QU IRK / Chambered Workbench / object.demo.intake-to-lineage.v0.1          │
│ State: Candidate       Authority: inspect + propose only       Canon: no   │
├───────────────┬──────────────────────────────────────┬─────────────────────┤
│ CHAMBERS      │ ACTIVE OBJECT STAGE                   │ EVIDENCE/AUTHORITY  │
│               │                                      │                     │
│ ◉ Aperture    │ [chamber-specific workspace]          │ Sources             │
│ ○ Foundry     │                                      │ Claims              │
│ ○ Constell.   │                                      │ Evaluations         │
│ ○ Gallery     │                                      │ Grants              │
│ + future      │                                      │ Risks / blockers    │
├───────────────┴──────────────────────────────────────┴─────────────────────┤
│ TRANSITION LEDGER: prior → proposed → required authority → receipt schema  │
└────────────────────────────────────────────────────────────────────────────┘
```

## Stage 1 — Aperture

```text
┌───────────────┬──────────────────────────────────────┬─────────────────────┐
│ CHAMBERS      │ APERTURE                             │ EVIDENCE/AUTHORITY  │
│ ◉ Aperture    │                                      │ Source: uploaded    │
│ ○ Foundry     │ Incoming reference                   │ Status: admitted    │
│ ○ Constell.   │ ┌────────────────────────────────┐   │ Extraction: draft   │
│ ○ Gallery     │ │ source.ref.product-vision.001  │   │ Grant: inspect only │
│ + future      │ └────────────────────────────────┘   │ Blocker: intent gap │
│               │                                      │                     │
│               │ Extracted signal                    │                     │
│               │ - desired shell visible             │                     │
│               │ - object lineage required           │                     │
│               │ - cinematic render blocked          │                     │
└───────────────┴──────────────────────────────────────┴─────────────────────┘
TRANSITION: raw source → admitted source + extracted signal
RECEIPT: `receipt.aperture.extract.v0.1`
```

Aperture separates source from signal and records interpretation debt. It does not compose, execute, publish, or promote.

## Stage 2 — Foundry

```text
┌───────────────┬──────────────────────────────────────┬─────────────────────┐
│ CHAMBERS      │ FOUNDRY                              │ EVIDENCE/AUTHORITY  │
│ ✓ Aperture    │                                      │ Inputs admitted: 3  │
│ ◉ Foundry     │ Candidate composition                │ Inputs excluded: 1  │
│ ○ Constell.   │ ┌──────────────┐   ┌──────────────┐  │ Recipe: draft      │
│ ○ Gallery     │ │ source       │ + │ constraints  │  │ Grant: propose     │
│ + future      │ └──────┬───────┘   └──────┬───────┘  │ External: blocked  │
│               │        └──────┬───────────┘          │ Canon: blocked     │
│               │               ▼                      │                     │
│               │     candidate.operator-shell.v0.1    │                     │
└───────────────┴──────────────────────────────────────┴─────────────────────┘
TRANSITION: admitted signal → candidate artifact
RECEIPT: `receipt.foundry.compose.v0.1`
```

Foundry creates candidate artifacts only from explicitly admitted inputs. It cannot treat capability availability as execution permission.

## Stage 3 — Constellation

```text
┌───────────────┬──────────────────────────────────────┬─────────────────────┐
│ CHAMBERS      │ CONSTELLATION                        │ EVIDENCE/AUTHORITY  │
│ ✓ Aperture    │                                      │ Coverage: partial   │
│ ✓ Foundry     │           [candidate]                │ Confidence: useful  │
│ ◉ Constell.   │              ●                       │ Authority: propose  │
│ ○ Gallery     │        ┌─────┼─────┐                 │ Reversible: yes     │
│ + future      │   evidence  grants risks             │ Blast radius: docs  │
│               │        │      │     │                │ Missing: review     │
│               │   sources  no pub no runtime         │ Decision: pending   │
└───────────────┴──────────────────────────────────────┴─────────────────────┘
TRANSITION: candidate artifact → decision candidate
RECEIPT: `receipt.constellation.review.v0.1`
```

Constellation answers what may change, under whose authority, based on which evidence, with what consequences.

## Stage 4 — Gallery

```text
┌───────────────┬──────────────────────────────────────┬─────────────────────┐
│ CHAMBERS      │ GALLERY                              │ EVIDENCE/AUTHORITY  │
│ ✓ Aperture    │                                      │ Receipt: written    │
│ ✓ Foundry     │ Lineage                              │ Outcome: pending    │
│ ✓ Constell.   │ source                               │ Amendment: allowed  │
│ ◉ Gallery     │   ↓                                  │ Canon: still no     │
│ + future      │ signal                               │ Reuse: review-only  │
│               │   ↓                                  │ Graph update: no    │
│               │ candidate → decision → receipt       │ Boneyard: possible  │
└───────────────┴──────────────────────────────────────┴─────────────────────┘
TRANSITION: decision candidate → preserved lineage record
RECEIPT: `receipt.gallery.preserve.v0.1`
```

Gallery preservation does not make the object executable or canonical. Abandoned work can retain value without being available for action.

## Required wireframe behaviors

- The same object id remains visible across chambers.
- State changes are ledgered before and after transition.
- The right rail shows evidence and authority at every stage.
- Blocked actions are first-class interface elements, not hidden errors.
- Confidence is displayed separately from permission.
- Canon state is visible and remains `no`.
- Provider-resource and publication access remain blocked.
- Future chambers appear as an extensible rail affordance, not a hard-coded promise.

## Deliberately excluded from this artifact

- runtime code;
- React components;
- database schema;
- automation;
- provider access;
- public publication;
- canon promotion;
- skill packaging;
- connector changes;
- CI changes.
