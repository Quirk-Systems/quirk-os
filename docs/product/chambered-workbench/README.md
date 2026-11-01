# Chambered Workbench Candidate Pack

**Status:** Candidate product-design artifact  
**Authority ceiling:** `propose`  
**Repository effect:** documentation only  
**Runtime effect:** none  
**Canon effect:** none  
**Provider/resource effect:** none  
**Publication effect:** none

## Candidate decision

Bryan adopted the Four Chambers as the initial experiential architecture:

```text
Aperture → Foundry → Constellation → Gallery
```

The continuous workbench is the daily interface. Object lineage is the persistent substrate.

Bryan approved **Operator Contract Extraction** as the next candidate direction: one low-fidelity `HookCandidate` workbench plus its object, move, transition, evidence, and authority documentation contracts. That approval is limited to candidate product design. It does not approve executable schemas, runtime work, implementation planning, Canon promotion, provider access, publication, release, deployment, or merge.

This pack records the design as a candidate product artifact and deliberately separates it from implementation, runtime activation, canon promotion, provider access, publication, or automatic admission.

## Why this folder is named `chambered-workbench`

The initial product experience uses Four Chambers, but the architecture should not hard-code the number four. This folder treats the adopted Four Chambers as the first named chamber set inside a more general `n_chamber` grammar.

That gives Quirk a durable rule:

```text
Four Chambers is the first admitted experiential map.
N Chambers is the extensible chamber contract.
```

## Package contents

### Foundation candidate

- [`OPERATOR-SHELL-WIREFRAME-v0.1.md`](OPERATOR-SHELL-WIREFRAME-v0.1.md) — low-fidelity product wireframe for one object moving through Aperture, Foundry, Constellation, and Gallery.
- [`operator-shell-wireframe-v0.1.svg`](operator-shell-wireframe-v0.1.svg) — static SVG companion for review.
- [`N-CHAMBER-GRAMMAR.md`](N-CHAMBER-GRAMMAR.md) — chamber object contract, extension lifecycle, and invariants preventing visual metaphors from becoming accidental authority.
- [`ROADMAP.md`](ROADMAP.md) — planning map for docs, folders/files/resources, runtime code, iterative testing, feedback loops, approvals, nominations, and future chamber expansion.
- [`ADMISSION-CHECKLIST.md`](ADMISSION-CHECKLIST.md) — review gates and blockers before any implementation, canon, publication, or provider-resource access.

### Operator Contract Extraction candidate

- [`HOOK-CANDIDATE-WORKBENCH-v0.1.md`](HOOK-CANDIDATE-WORKBENCH-v0.1.md) — one synthetic `HookCandidate` traced through all four chambers without publishing creative content.
- [`HOOK-CANDIDATE-OBJECT-CONTRACT-v0.1.md`](HOOK-CANDIDATE-OBJECT-CONTRACT-v0.1.md) — identity, state, lineage, rights, evidence, and retention contract for the vertical proof object.
- [`MOVE-CONTRACT-v0.1.md`](MOVE-CONTRACT-v0.1.md) — discoverable operator moves with explicit capability, authority, prerequisites, effects, failures, and receipts.
- [`TRANSITION-CONTRACT-v0.1.md`](TRANSITION-CONTRACT-v0.1.md) — exact-version state movement and transition receipt requirements.
- [`EVIDENCE-CONTRACT-v0.1.md`](EVIDENCE-CONTRACT-v0.1.md) — evidence atoms, bundles, claims, contradictions, freshness, and decision-use rules.
- [`AUTHORITY-CONTRACT-v0.1.md`](AUTHORITY-CONTRACT-v0.1.md) — scoped grants and separation of proposing, evaluating, executing, deciding, and verifying.
- [`ADVERSARIAL-FIXTURES-v0.1.md`](ADVERSARIAL-FIXTURES-v0.1.md) — eleven design-level failures that must remain release-blocking before runtime work.

The extraction documents are design contracts, not executable schemas. They deliberately map to existing repository vocabulary without replacing or silently revising it.

## Product grammar

```text
source admitted
  → signal extracted
  → candidate composed
  → authority inspected
  → decision recorded
  → lineage preserved
```

## Shared operator shell

Every chamber uses the same daily interface frame:

```text
┌────────────────────────────────────────────────────────────────────┐
│ Top bar: project, object id, version, state, authority envelope    │
├──────────────┬──────────────────────────────┬──────────────────────┤
│ Chamber rail │                              │ Evidence + Authority │
│              │      Active object stage     │                      │
│ Aperture     │                              │ Sources              │
│ Foundry      │      Graph / composition     │ Claims               │
│ Constellation│      or artifact preview     │ Evaluations          │
│ Gallery      │                              │ Grants               │
│ + future     │                              │ Risks                │
├──────────────┴──────────────────────────────┴──────────────────────┤
│ Transition ledger: previous state → proposed state → receipt       │
└────────────────────────────────────────────────────────────────────┘
```

The `HookCandidate` extraction refines this frame into five persistent regions: context bar, lineage rail, chamber work surface, move inspector, and evidence/authority/transition drawer. Chamber navigation never implies an object-state transition.

## Compatibility posture

The candidate contracts reuse concepts already present in:

- `schemas/affordance.schema.json`;
- `schemas/proposed-move.schema.json`;
- `schemas/ledger-transition.schema.json`;
- `schemas/research-claim.schema.json`;
- `schemas/source-binding.schema.json`;
- the merged authority and Design Tribunal boundaries in `project-scaffold`.

Any future executable schema work must reconcile against the exact versions then present. These documents do not freeze, supersede, or amend those contracts.

Vocabulary bridge: existing chamber copy uses `inspect` as a human-facing label; the operator contracts map those moves to the existing affordance authority class `observe`. No new `inspect` grant kind is proposed.

## Admission posture

Merging this candidate pack, if later approved, would only preserve product-design documentation. It would not:

- add runtime code;
- create or modify schemas;
- create provider-resource grants;
- publish a creative asset or release candidate;
- canonize the operator contracts or Four Chambers;
- admit any future chamber;
- mutate Preference Graph state;
- authorize agent manifests, skills, connectors, deployments, or GitHub settings changes.

## Hard invariants

```text
Capability ≠ Authority
Confidence ≠ Permission
Candidate ≠ Canon
Preservation ≠ Promotion
Gallery ≠ Admission
Review ≠ Release
State ≠ Chamber
Static artifact ≠ Runtime shell
Four Chambers ≠ Fixed chamber ceiling
N Chambers ≠ Unbounded sprawl
```
