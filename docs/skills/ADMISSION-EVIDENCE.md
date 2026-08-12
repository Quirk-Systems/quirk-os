# Quirk Skills v0.2 — Admission Evidence

## Candidate-local evidence supplied

- 11/11 packages have strict machine-readable manifests.
- Every manifest is bound to its exact `SKILL.md` Git blob SHA and its own canonical SHA-256 digest.
- Every package declares candidate status, family, authority ceiling, triggers, collisions, typed contracts, method, tools, resources, quality, learning, compatibility, provenance, and stop conditions.
- 44 executable cases cover positive, adversarial, regression, and authority behavior for every skill.
- Runtime-loader tests reject candidate loading, source tampering, manifest tampering, self-approval, over-ceiling grants, expired grants, undeclared actions, empty action scopes, and digest mismatch.
- A positive loader control accepts only an ephemeral admitted copy with a separate approval record and scoped grant.
- Run receipts validate independently from admission and remain explicitly immutable.
- Source and runtime mappings forbid silent loss and reverse mutation of Canon.
- Bounded skill-package placeholder markers are rejected by conformance.
- Local proof: 14/14 runtime tests and 44/44 skill cases pass.
- GitHub proof: Skills validation and Sync Control Plane Conformance pass on the reconciled stack.

## Gate matrix

| Gate | Candidate-local proof | Remaining external proof |
| --- | --- | --- |
| Quirk Approval | digest-bound package and explicit decision boundary | accountable approve/revise/reject/supersede decision |
| Procedures | 11 versioned procedures and 44 executable cases | live bounded trials |
| Processes | loader, grant, receipt, learning, and supersession sequence | operational owner and review cadence |
| Profiling | trigger, family, inputs, outputs, resources, and anti-patterns | observed routing precision/recall |
| Interoperability | mapping contract and runtime-manifest references | independent consumer round trip |
| Security | fail-closed loader and least-action grants | threat review and revocation/replay proof |
| Statistical | calibrated forecaster cases and explicit score threshold | empirical sample and drift evidence |
| Lexical | stable IDs and grammar separation | portfolio collision review |
| Quirk Pedantry | no hidden authority, no silent loss, no invisible-context dependency | human edge-case adjudication |

## Inherited gate state

The inherited Golden Project Pack gate now distinguishes candidate merge from Golden admission. PR #3 remains `PROPOSED`; its Ship It Without Bryan findings remain explicit admission holds, but they no longer falsely make structurally valid descendant candidates unmergeable. This child does not resolve, waive, or rewrite those admission findings.

## Decision ceiling

This evidence can justify **candidate completeness and candidate merge-readiness** only. It cannot by itself mark a package admitted, active, current, chooseable, useable, canonical, or deployed.
