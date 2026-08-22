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

This pack records the design as a candidate product artifact and deliberately separates it from implementation, runtime activation, canon promotion, provider access, publication, or automatic admission.

## Why this folder is named `chambered-workbench`

The initial product experience uses Four Chambers, but the architecture should not hard-code the number four. This folder treats the adopted Four Chambers as the first named chamber set inside a more general `n_chamber` grammar.

That gives Quirk a durable rule:

```text
Four Chambers is the first admitted experiential map.
N Chambers is the extensible chamber contract.
```

## Package contents

- [`OPERATOR-SHELL-WIREFRAME-v0.1.md`](OPERATOR-SHELL-WIREFRAME-v0.1.md) — low-fidelity product wireframe for one object moving through Aperture, Foundry, Constellation, and Gallery.
- [`operator-shell-wireframe-v0.1.svg`](operator-shell-wireframe-v0.1.svg) — static SVG companion for review.
- [`N-CHAMBER-GRAMMAR.md`](N-CHAMBER-GRAMMAR.md) — chamber object contract, extension lifecycle, and invariants preventing visual metaphors from becoming accidental authority.
- [`ROADMAP.md`](ROADMAP.md) — planning map for docs, folders/files/resources, runtime code, iterative testing, feedback loops, approvals, nominations, and future chamber expansion.
- [`ADMISSION-CHECKLIST.md`](ADMISSION-CHECKLIST.md) — review gates and blockers before any implementation, canon, publication, or provider-resource access.

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

## Admission posture

Merging this candidate pack, if later approved, would only preserve product-design documentation. It would not:

- add runtime code;
- create or modify schemas;
- create provider-resource grants;
- publish a public artifact;
- canonize Four Chambers;
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
Static artifact ≠ Runtime shell
Four Chambers ≠ Fixed chamber ceiling
N Chambers ≠ Unbounded sprawl
```
