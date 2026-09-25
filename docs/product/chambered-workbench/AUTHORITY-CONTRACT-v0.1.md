# Authority Contract v0.1

**Status:** Candidate design contract  
**Contract id:** `contract.authority.operator.v0.1`  
**Authority ceiling:** `propose`  
**Executable schema:** none  
**Runtime effect:** none

## Purpose

Make permission inspectable without laundering capability, confidence, credentials, evaluation, repository access, prior success, or chamber location into authority.

The workbench displays and evaluates external authority records. It does not mint authority merely by rendering a control.

The existing N-Chamber document uses `inspect` as an operator-facing ceiling label. In this extraction, an `inspect_*` move maps to the existing affordance authority class `observe`. It does not create an `inspect` grant enum or widen `observe` authority.

## Candidate grant projection

```yaml
contract_version: authority.operator-projection.v0.1
grant_ref: <immutable-external-grant-ref>
grant_version: <version>
grant_digest: sha256:<digest>

mode: human_explicit | policy_delegated | mutual | system_deterministic | emergency | waiver
status: required | requested | authorized | denied | expired | revoked

issuer_ref: <authority-principal-ref>
grantee_ref: <human-agent-service-policy-or-role-ref>

scope:
  operations: [observe, infer, propose, execute_reversible, enforce_invariant, execute_protected]
  protected_actions: [preserve, reuse, external_test, release, publication, provider_resource_access, preference_mutation, admission, canon_promotion, forgetting, emergency_action, waiver]
  exact_subjects:
    - object_type: <object-type>
      object_id: <object-id>
      expected_version: <exact-version>
      expected_digest: sha256:<exact-object-digest>
      descendant_scope: none | <explicit-bounded-descendant-rule>
  allowed_purposes: [<purpose>]
  prohibited_purposes: [<purpose>]
  environments: [work, canonical, runtime, projection, provider, publication]
  maximum_risk_class: L0 | L1 | L2 | L3 | L4 | L5
  excluded_rights_or_safety_domains: [<domain>]

validity:
  issued_at: <date-time>
  not_before: <date-time>
  expires_at: <date-time>
  last_verified_at: <date-time>

delegation:
  parent_grant_ref: <grant-ref-or-null>
  remaining_depth: <integer>
  delegable_operations: [<operation>]
  scope_widening: prohibited

co_approval:
  required_function_refs: [<role-or-actor-ref>]
  quorum: <integer>
  separation_rules: [<rule>]
  approval_refs: [<approval-ref>]

constraints: [<bounded-condition>]
revocation_ref: <revocation-receipt-or-null>
provenance_refs: [<request-decision-policy-evidence-receipt-ref>]
```

This projection is intentionally richer than the current minimal AuthorityGrant token so the UI can expose scope and blockers. It does not change the signed grant format. Future runtime work must map to the exact authority contracts then in force rather than adopting this projection by implication.

## Decision functions

The shell must keep these functions distinguishable without inventing a competing role catalog:

| Function | May do | Must not infer |
| --- | --- | --- |
| requester | state intent and purpose | approval or grant scope |
| proposer | construct candidate object, move, or transition | authority to execute or approve |
| evaluator | produce findings and evidence under declared criteria | approval, release, or canon power |
| executor | apply only the authorized operation | permission from capability or credentials |
| decision authority | allow, deny, hold, or escalate the exact proposal | truth from authority or broader scope from prior approval |
| receipt verifier | compare actual result with approved result and attest record integrity | ability to rewrite the result or original evidence |
| issuer/delegator | create a grant within authority already held | power to widen inherited scope |
| revoker | terminate operative use at an effective time | deletion of historical evidence |

These function labels map to external Tribunal and authority roles. They do not supersede the five-role Tribunal compatibility boundary or create new repository roles.

## Authority decision

An authority check produces exactly one operator-facing result:

- `allow` — every required active grant matches actor, exact subject id/version/digest tuple, operation, purpose, environment, risk, validity, delegation, and co-approval;
- `deny` — an explicit applicable prohibition exists;
- `hold` — required evidence, freshness, exact version, grant, or approval is missing;
- `escalate` — grants conflict, scope is ambiguous, requested risk exceeds the active ceiling, or a separation rule fails.

Explicit denial and narrower restriction outrank broader permission. Ambiguity and conflict never default to allow.

## Non-authority signals

None of the following supplies or expands authority:

- model capability or tool availability;
- credentials or connected-account access;
- repository permissions;
- a successful dry run, test, build, or prior execution;
- confidence, score, consensus, applause, repeated use, or popularity;
- proximity in a graph or progression through a chamber;
- retention in Gallery;
- a previous grant for another object version, purpose, environment, or risk;
- user silence, inferred satisfaction, or lack of objection;
- an agent's claim that action is reversible.

## Expiry, revocation, delegation, and conflict rules

1. Expired, stale, revoked, superseded, or denied grants remain inspectable but unusable.
2. Reauthorization creates a new grant version; it does not reactivate or rewrite the old grant.
3. A child grant cannot expand the parent's exact subject tuple or descendant rule, operation, purpose, environment, risk, time window, protected action, or delegation depth.
4. Revocation takes effect at its recorded time and blocks later execution, including queued and replayed operations.
5. Approval of the exact `hook_candidate.hx-001@0.1.0` id/version/digest tuple does not cover another version, changed digest, derived child, different purpose, external environment, or broader action.
6. Gallery preservation authority grants only preservation. Reuse, external testing, release, publication, provider-resource access, admission, Canon promotion, forgetting, and Preference Graph mutation each require their own exact protected scope.
7. Emergency authority and waivers are consequential, time-bounded, non-self-issued transitions with named non-waivable boundaries and immutable receipts.
8. A proposed action that collapses producer, evaluator, executor, decision authority, and verifier functions fails separation unless a valid external low-risk policy explicitly permits the exact consolidation.
9. Decomposition cannot lower risk: a set of individually reversible moves is treated as consequential when their combined outcome is protected or hard to reverse.

## HookCandidate authority examples

| Proposed action | Minimum posture | Result in this artifact |
| --- | --- | --- |
| inspect redacted fixture | valid `observe` authority for the inspect move | design describes as available |
| infer structural role | infer capability plus allowed purpose | labeled inference only |
| draft derived variant | propose scope for exact parent and purpose | candidate version only |
| record evaluator finding | evaluator declaration and evidence scope | finding only; no approval |
| preserve human decision | exact-version human decision plus preservation grant | receipt-backed candidate preservation |
| reuse in another song | separate reuse scope and rights confirmation | blocked |
| run external audience test | external-action and provider-resource scopes plus rights | blocked |
| release or publish | explicit release/publication grant | blocked |
| admit to Canon | exact admission/Canon authority | blocked |
| update Preference Graph | human-confirmed bounded preference mutation grant | blocked |

## Compatibility posture

- The minimal merged `AuthorityGrant` fields—grant id, issuer, subject, scopes, issued time, expiry, and nonce—remain the runtime authority source where applicable.
- Current `ledger.transition.v1` authority mode/status vocabulary is reused.
- Current `affordance` operation ladder is reused.
- Design Tribunal separation remains external; this document projects its decision functions into the workbench.
- `entitlement-grant` explicitly has `authority_effect: none`; access to content or features cannot be reused as decision authority.

No executable grant kind, signature method, role enum, or authorization policy is created here.
