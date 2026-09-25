# N-Chamber Grammar

**Status:** Candidate planning grammar  
**Authority ceiling:** `propose`  
**Purpose:** prevent the adopted Four Chambers from becoming a brittle ceiling or a decorative metaphor.

## Core rule

A chamber is not a page, vibe, room, or brand flourish. A chamber is an operator context with a bounded product responsibility, explicit transition contract, and visible authority model.

```text
Chamber = Purpose + Inputs + Allowed transformations + Required evidence + Authority ceiling + Output contract + Failure states
```

## Initial chamber set

```text
Aperture       capture, classify, separate source from signal
Foundry        compose candidate artifacts from admitted inputs
Constellation  inspect relationships, evidence, authority, risk, and transition readiness
Gallery        preserve lineage, receipts, outcomes, amendments, contradictions, and boneyard value
```

These four are the first experiential architecture. They do not limit future chamber count.

## Chamber object contract

Every future chamber candidate must define:

```yaml
id: chamber.<slug>.v0.1
name: Human-readable chamber name
status: candidate | admitted | deprecated | rejected
purpose: One bounded operational purpose
owner: Human or team accountable for the chamber definition
inputs: Objects and states accepted by the chamber
outputs: Objects and states produced by the chamber
allowed_transitions: Explicit prior_state -> proposed_state transitions
authority_ceiling: inspect | propose | reversible_change | external_action | admission
required_evidence: Evidence classes needed before each transition
blocked_actions: Actions the chamber must never perform
ledger_events: Receipt schemas emitted by chamber actions
interfaces: Workbench regions, APIs, docs, schemas, or review surfaces touched
failure_states: Known bad states and required UI handling
evaluation: Positive and adversarial fixtures required before admission
retention: What is preserved, forgotten, or boneyarded
promotion_path: How the chamber can be nominated, reviewed, admitted, amended, deprecated, or retired
```

## Extension lifecycle

```text
1. Nominate chamber candidate
2. Define chamber contract
3. Add low-fidelity workbench sketch
4. Write positive and adversarial fixtures
5. Review for overlap with existing chambers
6. Prove no authority expansion
7. Prove no evidence laundering
8. Prove no candidate-to-canon self-promotion
9. Decide: reject, revise, preserve as candidate, or admit
10. Record receipt outside the chamber candidate itself
```

## Admission tests for a new chamber

A chamber candidate is blocked when it:

- duplicates an existing chamber under new language;
- hides authority escalation behind workflow convenience;
- allows confidence to unlock permission;
- makes Gallery preservation imply reuse permission;
- moves object state without a receipt;
- adds runtime capability without a human decision artifact;
- introduces provider-resource or publication access by implication;
- turns an aesthetic metaphor into a governing rule;
- cannot explain why a transition is blocked;
- cannot distinguish source, signal, candidate, decision, receipt, and outcome.

## Candidate future chambers

These are not admitted. They are examples for testing the n-chamber contract.

| Candidate | Purpose | Risk to test |
|---|---|---|
| `Tribunal` | structured review and verdict workbench | evaluator escalation or consensus laundering |
| `Market` | offer, commerce, and campaign projection planning | publication or customer-data access leakage |
| `Lab` | experiments, simulations, and cheapest disproofs | treating test success as canon admission |
| `Vault` | sensitive assets, restricted evidence, and retention controls | preservation without consent or over-retention |
| `Stage` | creative performance, release prep, and media packaging | asset rights, provenance, and publication bleed |
| `Forge` | runtime implementation planning after admission | code sneaking into candidate design review |
| `Mirror` | outcome review and preference update proposals | inferred satisfaction becoming preference evidence |

## Naming discipline

A future chamber name must earn its job. Good names carry operational responsibility. Bad names merely look expensive in a render.

A chamber name fails when it is:

- visually evocative but semantically empty;
- interchangeable with any other product surface;
- unable to produce a clear transition contract;
- dependent on magic, mysticism, or generic AI spectacle;
- too broad to test.

## Governing invariant

```text
N Chambers increases expressive range.
It must never increase hidden authority.
```
