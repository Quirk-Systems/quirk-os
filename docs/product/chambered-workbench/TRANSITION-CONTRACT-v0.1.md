# Transition Contract v0.1

**Status:** Candidate design contract  
**Contract id:** `contract.transition.operator.v0.1`  
**Authority ceiling:** `propose`  
**Executable schema:** none  
**Runtime effect:** none

## Purpose

Define the inspectable agreement required before an exact object version may change lifecycle state. A transition is a governed state mutation—not chamber navigation, a diagram edge, a score, a recommendation, or an animation.

This design aligns with `ledger.transition.v1`; it does not replace or amend that schema.

## Candidate shape

```yaml
contract_version: transition.operator.v0.1
transition_id: qlt_<stable-id>

subject:
  object_id: <stable-id>
  object_type: <type>
  expected_version: <exact-version>
  expected_digest: sha256:<digest>

chamber_context:
  current_chamber_ref: chamber.<id>
  proposed_chamber_ref: chamber.<id-or-same>
  chamber_contract_versions: [<ref>]

operation: <one-bounded-operation>
purpose:
  allowed: [<purpose>]
  prohibited: [<purpose>]

prior_state:
  lifecycle_state: <state>
  state_ref: <immutable-ref>
  state_digest: sha256:<digest>

proposed_state:
  lifecycle_state: <state>
  expected_version: <exact-result-version>
  expected_digest: sha256:<expected-result-digest>
  patch_ref: <deterministic-patch-or-null>
  expected_state_digest: sha256:<digest>

status: draft | proposed | evaluating | approved | rejected | deferred | applying | applied | verified | operative | challenged | superseded | revoked | expired | poisoned | forgotten

participants:
  requester: {actor_id: <id>, actor_type: human | agent | service | policy}
  proposer: {actor_id: <id>, actor_type: human | agent | service | policy}
  evaluators: [{actor_id: <id>, actor_type: human | agent | service | policy}]
  executor: {actor_id: <id>, actor_type: human | agent | service | policy} | null
  decision_authority: {actor_id: <id>, actor_type: human | agent | service | policy}
  receipt_verifier: {actor_id: <id>, actor_type: human | agent | service | policy}
  conflict_refs: [<conflict-ref>]

authority:
  mode: human_explicit | policy_delegated | mutual | system_deterministic | emergency | waiver
  status: required | requested | authorized | denied | expired | revoked
  required_scopes: [<scope>]
  authority_refs: [<grant-ref>]

evidence_refs: [<evidence-bundle-ref>]
evidence_detail:
  contradiction_refs: [<evidence-ref>]
  freshness_evaluated_at: <date-time>

risk_class: L0 | L1 | L2 | L3 | L4 | L5
risk_detail:
  rights_or_safety_impact: <impact>
  blast_radius: <bounded-scope>

reversibility:
  class: trivial | reversible | compensatable | irreversible
  rollback_ref: <ref-or-null>
  compensation_ref: <ref-or-null>

receipt:
  schema_ref: contract.transition-receipt.v0.1
  preimage_ref: <immutable-proposal-ref>

provenance:
  source_type: <bounded-source-type>
  source_refs: [<ref>]
  parent_transition_refs: [<transition-ref>]

trace_id: <trace-id>
idempotency_key: <key>
occurred_at: <date-time>

timestamps:
  proposed_at: <date-time>
  evaluated_at: <date-time-or-null>
  decided_at: <date-time-or-null>
  applied_at: <date-time-or-null>
  verified_at: <date-time-or-null>

result:
  outcome: pending | authorized | denied | applied | failed | partial | verified | rolled_back | compensated
  actual_version: <exact-version-or-null>
  actual_digest: sha256:<digest-or-null>
  receipt_ref: <receipt-ref-or-null>
  failure_code: <stable-code-or-null>
```

## State rules

1. `approved` is not `applied`; `applied` is not `verified`; `verified` is not release, publication, admission, Canon, or Preference Graph mutation.
2. Chamber navigation is a view event. It creates no lifecycle transition unless a separately proposed state mutation is authorized and receipted.
3. The expected subject version and digest must match at decision time and immediately before execution. Any mismatch fails closed as a stale proposal.
4. Only one bounded operation may appear in a transition. A compound request must enumerate independently authorizable child transitions and must not use decomposition to evade risk or approval.
5. Known contradictions, denials, debt, and conflicts remain attached to the proposal and receipt.
6. A transition may branch to rejection, deferral, revision, challenge, rollback, compensation, supersession, poison, or forgetting. Failure is a first-class state path.
7. Repeating a prior transition requires a new proposal evaluated against current version, evidence, grants, risk, and purpose.
8. Actor, proposer, evaluator, executor, decision authority, and receipt verifier functions remain distinguishable. Any permitted low-risk role consolidation must be declared and authorized externally.
9. A missing, invalid, stale, expired, revoked, conflicting, scope-mismatched, version-mismatched, or purpose-mismatched grant blocks the transition.
10. A receipt reports the decision or attempt. It cannot retroactively manufacture authority or erase a partial failure.

## HookCandidate chamber transitions

| Context | Prior state | Proposed state | Minimum evidence | Decision requirement |
| --- | --- | --- | --- | --- |
| Aperture | `captured` | `scoped` | origin, purpose, source binding, rights declaration, known interpretation debt | named human confirms exact fixture purpose |
| Foundry entry | `scoped` | `composing` | exact scoped version, admitted inputs, rights, constraints, proposed composition purpose | separately authorized transition; selecting Foundry is inspect-only |
| Foundry | `composing` | `review_ready` | parent lineage, derivation operations, constraints, validation findings, rights inheritance | authorized proposal; no selection or release authority |
| Constellation entry | `review_ready` | `evaluating` | exact review-ready version, rubric, evaluator declarations, conflict checks, evidence plan | separately authorized transition; selecting Constellation is inspect-only |
| Constellation | `evaluating` | `decision_ready` | rubric, evaluator declarations, criterion evidence, contradictions, dissent, freshness | evaluator may recommend; human decision still required |
| Constellation correction | `evaluating` | `revision_requested` | surviving objection, affected criteria, evidence refs, remediation | evaluator may propose; no candidate rewrite |
| Constellation pause | `evaluating` | `deferred` | missing or expired evidence/authority, trigger, review date | evaluator may propose; no rejection or forgetting implied |
| Gallery | `decision_ready` | `preserved_candidate`, `rejected`, `deferred`, or `boneyard` | exact-version human decision, evidence snapshot, authority refs, retention basis | receipt-backed human decision; no reuse/release/publication authority |
| Gallery salvage | `rejected` or `preserved_candidate` | `boneyard` | prior decision receipt, salvage rationale, retention basis, revisit trigger | separate human decision and receipt; no deletion, reuse, revival, or forgetting implied |

## Transition receipt

Every consequential decision or execution attempt—including denial, rejection, failed application, waiver, rollback, compensation, revocation, forgetting, and deliberate no-op—owes an append-only receipt containing:

- receipt id and contract version;
- transition id and recorded time;
- exact subject id, type, prior version/digest, proposed version/digest, and actual resulting version/digest;
- operation, allowed and prohibited purposes, chamber context, risk, and reversibility;
- separately identified proposer, evaluators, executor, decision authority, and verifier;
- operative grant versions/digests and their status at decision time;
- evidence bundle versions/digests, freshness evaluation, and unresolved contradictions;
- decision, execution, and verification outcomes with timestamps;
- trace id, idempotency key, parent receipt refs, and failure code;
- rollback or compensation ref when applicable;
- tamper-evident digest or signature mechanism, nominated later as runtime design.

Corrections append a superseding receipt and preserve the original. Historical grants and evidence remain referenced after expiry or revocation but cannot be replayed as operative authority.

## Failure behavior

| Condition | Required result |
| --- | --- |
| stale object version | `deferred` or `rejected`; regenerate proposal |
| evidence materially stale | `deferred` unless separately authorized waiver is valid and the gate is waivable |
| authority missing or mismatched | `rejected` or `deferred`; no application |
| execution partially applies | record `partial`; reconcile before any retry |
| receipt write or verification fails | mark operation unverified; prohibit downstream reliance |
| rollback fails | record failure and escalate; never label original transition reversed |
| contradiction discovered after verification | append challenge transition; preserve prior decision truth |

## Compatibility posture

The descriptive contract preserves the following explicit mapping to `ledger.transition.v1`:

| Candidate field | `ledger.transition.v1` field | Posture |
| --- | --- | --- |
| `transition_id` | `id` | identifier mapping only |
| `contract_version` | `schema_version` | candidate contract is not `ledger.transition.v1`; any executable record must use the real schema version |
| `subject.object_id`, `object_type`, `expected_version` | `subject` | direct vocabulary; `expected_digest` is a candidate integrity addition |
| `operation`, `status`, `purpose` | same names | direct vocabulary |
| `participants.proposer` | `proposer` | direct actor id/type vocabulary; other participants are candidate review additions |
| `authority.mode`, `status`, `authority_refs` | `authority` | direct vocabulary; required scopes remain candidate review detail |
| `provenance` | `provenance` | direct `source_type`, `source_refs`, and parent-transition vocabulary |
| `evidence_refs` | `evidence_refs` | bundle refs are stored as ordinary evidence refs until a future exact schema decision says otherwise |
| `risk_class` | `risk_class` | direct vocabulary; `risk_detail` is candidate review detail |
| `reversibility.class`, `rollback_ref` | `reversibility` | direct vocabulary; compensation ref is candidate review detail |
| `idempotency_key`, `trace_id`, `occurred_at` | same names | direct vocabulary; `occurred_at` records the represented ledger event, not proof of application |

The proposed result version/digest, chamber context, participant separation, freshness detail, receipt preimage, and extended timestamps remain UI/review additions only. They require separate reconciliation before any schema or runtime nomination.
