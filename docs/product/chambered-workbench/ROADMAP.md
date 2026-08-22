# Chambered Workbench Roadmap

**Status:** Candidate planning map  
**Authority ceiling:** `propose`  
**This document authorizes:** planning only  
**This document does not authorize:** runtime code, canon promotion, provider access, publication, deployment, or settings mutation.

## Phase 0 — Candidate product-design artifact

**Goal:** preserve the operator-shell direction in one documentation folder.

Files:

```text
docs/product/chambered-workbench/
  README.md
  OPERATOR-SHELL-WIREFRAME-v0.1.md
  operator-shell-wireframe-v0.1.svg
  N-CHAMBER-GRAMMAR.md
  ROADMAP.md
  ADMISSION-CHECKLIST.md
```

Acceptance:

- low-fidelity object journey is reviewable;
- evidence, authority, and transition ledger remain visible;
- Four Chambers appears as initial instance;
- n-chamber grammar prevents hard-coded ceiling;
- no runtime files exist outside this folder;
- PR remains draft until human review.

## Phase 1 — Product documentation expansion

**Goal:** make the candidate legible enough for design review without writing runtime code.

Candidate docs:

```text
OBJECT-JOURNEY.md
UI-REGION-CONTRACTS.md
TRANSITION-LEDGER-CONTRACT.md
EVIDENCE-AUTHORITY-RAIL.md
FAILURE-STATES.md
DESIGN-TOKENS-CANDIDATE.md
ACCESSIBILITY-NOTES.md
```

Review questions:

- Does each UI region have one job?
- Can a human see why an object is blocked?
- Are source, signal, candidate, decision, receipt, and outcome visually distinct?
- Does the interface preserve candidate state without smuggling canon status?

## Phase 2 — Resource inventory

**Goal:** identify files, resources, and references needed before implementation.

Resource classes:

- product sketches and low-fidelity SVGs;
- interaction notes;
- test object examples;
- sample evidence records;
- sample authority grants;
- sample transition receipts;
- failure fixtures;
- accessibility notes;
- provenance and rights notes for any visual references.

Blocked until separate authorization:

- production visual assets;
- public brand materials;
- provider credentials;
- external datasets;
- connected account access;
- customer data;
- publication surfaces.

## Phase 3 — Runtime planning, still no runtime code

**Goal:** draft implementation architecture after product-design review.

Candidate runtime modules:

```text
packages/workbench-shell/         # shell layout and chamber host
packages/chamber-registry/        # chamber manifests and lifecycle state
packages/object-lineage/          # lineage model and projections
packages/evidence-rail/           # source/claim/evaluation display contracts
packages/authority-rail/          # grants, blockers, and authority display contracts
packages/transition-ledger/       # transition receipts and state movement UI
packages/chamber-aperture/        # initial chamber implementation
packages/chamber-foundry/         # initial chamber implementation
packages/chamber-constellation/   # initial chamber implementation
packages/chamber-gallery/         # initial chamber implementation
```

No package should be created until an implementation plan is separately approved.

## Phase 4 — Schemas and fixtures

**Goal:** make the product behavior testable before UI polish.

Candidate schemas:

```text
ChamberManifest
WorkbenchObject
EvidenceClaim
AuthorityEnvelope
TransitionProposal
TransitionReceipt
LineageRecord
ChamberAdmissionDecision
```

Required adversarial fixtures:

- candidate self-promotion;
- confidence-as-permission;
- stale grant reuse;
- evidence laundering;
- provider-resource bleed;
- publication bleed;
- Gallery preservation as reuse permission;
- receipt mutation;
- source/signal collapse;
- untyped graph edge;
- chamber overlap;
- hidden transition;
- inferred satisfaction as preference evidence.

## Phase 5 — Iterative code and testing, after approval only

**Goal:** implement the smallest reversible vertical slice.

Slice:

```text
one object
one source
one extracted signal
one candidate artifact
one decision candidate
one receipt
one preserved lineage record
```

Minimum tests:

- unit tests for state transitions;
- schema validation for manifests and receipts;
- UI tests for visible blockers;
- replay tests for lineage records;
- fixture tests for authority leakage;
- accessibility checks for rail/state visibility;
- snapshot tests for shell layout, used carefully and not as proof of semantic correctness.

## Phase 6 — Feedback loops

**Goal:** make review useful without turning feedback into automatic preference or authority.

Feedback types:

```text
observation       what happened
critique          what appears wrong or weak
preference_signal possible taste evidence, not a rule
correction        human-supplied factual fix
approval          scoped decision with exact object version
rejection         scoped decision with reason and possible salvage
outcome           observed result after use
```

Rules:

- feedback can propose graph updates;
- preference mutation requires human confirmation;
- approval must name scope and object version;
- silence is not approval;
- repeated use is not permission expansion;
- positive reaction is not publication authority.

## Phase 7 — Nominations and approvals

**Goal:** give chambers and features a path into canon without self-promotion.

Nomination object:

```yaml
nomination_id:
candidate_type: chamber | feature | object_schema | runtime_module | design_rule
candidate_ref:
reason:
evidence:
known_risks:
required_reviewers:
authority_requested:
reversibility:
expiration:
```

Decision outcomes:

```text
reject
revise
preserve_as_candidate
admit_as_experimental
admit_as_canon
supersede
retire
```

Canon promotion requires a separate exact-head decision receipt. It cannot be recorded inside a candidate artifact as if the candidate approved itself.

## Phase 8 — Future chamber expansion

**Goal:** evolve beyond Four Chambers without product sprawl.

A future chamber earns admission only when it handles a recurring operator job that cannot be cleanly expressed inside an existing chamber.

Possible nomination backlog:

- `Tribunal` for structured evaluation and verdicts;
- `Lab` for experiments and cheapest disproof;
- `Market` for commerce/campaign projection planning;
- `Vault` for sensitive evidence and asset retention;
- `Stage` for creative release preparation;
- `Forge` for implementation planning after admission.

Backlog status: examples only, not nominated.
