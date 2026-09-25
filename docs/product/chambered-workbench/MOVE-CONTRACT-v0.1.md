# Move Contract v0.1

**Status:** Candidate design contract  
**Contract id:** `contract.move.operator.v0.1`  
**Authority ceiling:** `propose`  
**Executable schema:** none  
**Runtime effect:** none

## Purpose

Turn an affordance into an inspectable, bounded invitation. A move explains what may be attempted, why it matters, what it needs, what it would change, which authority it requires, how it can fail, and what receipt it owes.

A move being visible means the system can describe it. Visibility never grants permission.

Operator-facing move names may use `inspect_*`, but their authority class is `observe` from `affordance.schema.json`. `Inspect` is interaction copy in this pack, not a second authority enum or grant scope.

## Candidate shape

```yaml
contract_version: operator.move.v0.1
move_id: move.<stable-id>
title: <operator-facing-title>
purpose: <one-bounded-purpose>
chamber_context_ref: chamber.<id>

subject:
  object_id: <stable-object-id>
  expected_version: <exact-version>
  expected_state: <lifecycle-state>

invitation:
  operator_question: <what-can-I-do-and-why>
  expected_output: <artifact-or-decision-produced>
  consequence_preview: <what-would-change>
  remains_unchanged: [<invariant>]

move_class: observe | infer | propose
required_capabilities: [<capability-ref>]

authority:
  required_scopes: [<scope>]
  acceptable_grant_kinds: [<grant-kind>]
  decision_authority_ref: <actor-or-role-ref>
  status: absent | requested | authorized | denied | expired | revoked

preconditions: [<machine-or-human-check>]
input_refs: [<object-evidence-or-policy-ref>]
evidence_requirements: [<requirement>]
contradiction_policy: block | escalate | permit_with_debt

state_effect:
  from_state: <state>
  proposed_state: <state>
  patch_summary: <plain-language-change>

actual_state_effects: []
execution_posture: not_authorized

risk:
  class: L0 | L1 | L2 | L3 | L4 | L5
  rights_or_safety_impact: <impact>

reversibility:
  class: trivial | reversible | compensatable | irreversible
  rollback_or_compensation_ref: <ref-or-null>

availability:
  status: available | conditional | blocked | awaiting_authority | unavailable_for_subject
  reason_code: <stable-code>
  operator_explanation: <plain-language-reason>
  remediation: <smallest-permissible-next-step>

separation:
  proposer_ref: <actor-ref>
  evaluator_refs: [<actor-ref>]
  executor_ref: <actor-ref-or-null>
  decision_authority_ref: <actor-ref>
  receipt_verifier_ref: <actor-ref>
  conflict_refs: [<conflict-ref>]

receipt:
  required: true | false
  schema_ref: <receipt-contract-ref>
  preimage_ref: <transition-proposal-ref>

fallback: <safe-alternative>
prohibited_when: [<condition>]
expires_at: <date-time-or-null>
```

## Move rules

1. `required_capabilities` answers whether an actor can perform an operation. `authority.required_scopes` answers whether that actor may perform it on this subject for this purpose and time.
2. `move_class` reuses the documentary portion of the current affordance authority ladder. Only `observe`, `infer`, and `propose` are valid in this extraction. `execute_reversible`, `enforce_invariant`, and `execute_protected` remain existing compatibility vocabulary but are outside this contract's authority ceiling.
3. The subject binds an exact version. A stale screen cannot authorize a move against a newer object.
4. A consequential move is proposed before execution. Its transition preimage is inspectable before a decision.
5. Confidence, score, consensus, repeated use, chamber position, or prior success cannot alter `authority.status`.
6. A blocked move remains visible with reason and remediation unless disclosure would create a documented security risk.
7. `fallback` is mandatory for product-facing moves. Failure must leave a navigable state rather than a dead end.
8. An evaluator records evidence and findings; evaluation does not authorize execution or admission.
9. A move cannot silently expand affected objects, purpose, scopes, provider resources, publication surfaces, or duration after approval.
10. External execution, release, publication, provider-resource mutation, canon admission, and Preference Graph mutation always use explicit protected scopes and separate grants.
11. Any applied consequential move emits a transition receipt. A preview is not a receipt, and a receipt cannot retroactively manufacture authority.
12. Every move in this extraction keeps `actual_state_effects: []` and `execution_posture: not_authorized`. A non-empty actual effect, execution token, applied patch, provider call, publication target, or runtime handle is a scope breach.
13. A `propose` move requesting governed change references a separate complete `proposed-move.v1` record. This candidate contract cannot serve as a reduced shadow proposal, approval, implementation record, or receipt.

## HookCandidate move catalog

### Aperture

| Move | Class | Expected effect | Authority posture |
| --- | --- | --- | --- |
| `inspect_origin` | observe | display origin and source bindings | no mutation |
| `classify_structural_role` | infer | propose `hook`, `refrain`, or `alternate` classification | inference remains labeled |
| `attach_source_binding` | propose | propose a new provenance reference | human confirmation for human-origin claims |
| `clarify_fixture_purpose` | propose | bind exact test purpose and prohibited uses | named responsible human required |
| `propose_scope_complete` | propose | propose `captured → scoped` | blocked until purpose and rights are bound |

### Foundry

| Move | Class | Expected effect | Authority posture |
| --- | --- | --- | --- |
| `inspect_constraints` | observe | show admitted and excluded constraints | no mutation |
| `propose_begin_composition` | propose | propose `scoped → composing` for the exact version | chamber navigation alone cannot enter the state |
| `draft_variant` | propose | create a derived candidate version with lineage | generator cannot select or release it |
| `compare_structure` | infer | produce a labeled structural comparison | no winner or preference inferred |
| `record_constraint_failure` | propose | attach a failure finding to exact version | finding remains challengeable |
| `propose_review_ready` | propose | propose `composing → review_ready` | requires complete lineage, constraints, and rights inheritance |

### Constellation

| Move | Class | Expected effect | Authority posture |
| --- | --- | --- | --- |
| `propose_begin_evaluation` | propose | propose `review_ready → evaluating` with rubric and declarations | chamber navigation alone cannot enter the state |
| `inspect_evidence_graph` | observe | display typed evidence and contradiction edges | no state effect |
| `record_finding` | propose | add evaluator finding with evidence and declaration | evaluator remains read-only to candidate content |
| `request_more_evidence` | propose | add a blocking evidence requirement | cannot rewrite prior evidence |
| `record_dissent` | propose | preserve disagreement and rationale | consensus cannot erase it |
| `propose_decision_ready` | propose | propose `evaluating → decision_ready` | exact-version human decision still required |
| `propose_revision_requested` | propose | propose `evaluating → revision_requested` with surviving objection | evaluator cannot apply the transition or rewrite the candidate |
| `propose_evaluation_deferred` | propose | propose `evaluating → deferred` with trigger and review date | deferral cannot imply rejection or forgetting |

### Gallery

| Move | Class | Expected effect | Authority posture |
| --- | --- | --- | --- |
| `inspect_decision_receipt` | observe | show immutable decision and evidence snapshot | no mutation |
| `inspect_boneyard_salvage` | observe | show reason, salvage, and revisit trigger | no revival implied |
| `fork_candidate` | propose | create a child candidate with no inherited approval | new version starts candidate-only |
| `propose_reuse_review` | propose | request a separately scoped reuse decision | preservation supplies no reuse permission |
| `propose_boneyard_retention` | propose | propose a receipt-backed boneyard retention decision from `decision_ready`, `rejected`, or `preserved_candidate` | cannot delete, forget, revive, reuse, or rewrite prior decisions |
| `record_observed_outcome` | propose | attach actual post-use evidence | requires evidence of use and cannot auto-update preference |

`publish`, `release`, `promote_to_canon`, `mutate_preference`, and provider-resource actions are not available moves in this candidate artifact.

## Compatibility mapping

| Candidate move field | Existing vocabulary |
| --- | --- |
| `move_class` | `affordance.authority_required` |
| operator-facing `inspect_*` | `affordance.authority_required: observe`; `inspect` is UI copy only |
| required capabilities | `affordance.required_capabilities` |
| state effect | `affordance.state_effects` plus `ledger-transition.subject/operation/patch` |
| evidence obligation | `affordance.evidence_emitted`, `proposed-move.evidence_refs` |
| risk and reversibility | `proposed-move.risk` and `reversibility`; `ledger-transition.risk_class` and `reversibility` |
| blocked conditions and fallback | `affordance.prohibited_when` and `fallback` |
| source, affected objects, authority | `proposed-move.source_refs`, `affected_objects`, and `authority_required` |
| disposition | `proposed-move.disposition` |

This mapping is a compatibility hypothesis. It creates no executable alias and freezes no migration.

## Failure behavior

| Failure | Safe response |
| --- | --- |
| capability missing | block; name missing capability |
| grant absent, invalid, stale, expired, revoked, or scope-mismatched | block; retain inspectable grant state |
| subject version drift | block; refresh object and regenerate transition proposal |
| evidence incomplete or stale | block or permit only the explicitly configured debt path |
| contradiction unresolved | escalate, defer, or reject according to declared policy |
| evaluator conflict undeclared | invalidate finding for decision use; preserve it as untrusted input |
| execution partially applies | record partial state, prohibit retry without idempotency and reconciliation evidence |
| receipt write fails | treat consequential operation as unverified and prohibit promotion or downstream reliance |
