# Quirk Outcome Classes v0.1

Quirk Outcome Classes classify the kind of evidenced state change produced by Quirk work.

They do **not** classify the work performed, the asset produced, the system responsible, the metric used, confidence, or completion status.

```text
Outcome = who or what changed
        + from which prior state
        + into which new state
        + within what boundary
        + proven by what evidence
        + retained for how long
```

## The 11 classes

| Key | Class | Core question |
|---|---|---|
| `epistemic` | Clarity | What can now be understood, distinguished, or predicted? |
| `decisional` | Commitment | What valid choice has now been made, owned, and made actionable? |
| `structural` | Structure | What is now arranged, separated, consolidated, bounded, or related differently? |
| `capability` | Capability | Who or what can now perform a function to a defined standard? |
| `interoperability` | Interoperability | What independently owned entities can now work together without bespoke glue? |
| `operational` | Operation | What valuable behavior now occurs repeatedly, reliably, and observably? |
| `governance` | Governance | What authority, permission, consent, accountability, or reversibility is now enforceable? |
| `behavioral` | Adoption | What do intended actors now actually do differently? |
| `experiential` | Experience | What changed in comprehension, trust, perception, emotion, or memorability? |
| `material` | Material Value | What consequential resource, performance, risk, market, or creative result changed? |
| `continuity` | Continuity | What now survives handoff, time, personnel change, provider change, or failure? |

## Critical separations

- Outputs are not outcomes.
- Evidence levels are not outcome classes.
- Golden is a quality grade, not an outcome class.
- Quirk Systems describe where responsibility lives; Outcome Classes describe how reality changed.
- Every Outcome Contract has exactly one primary class and zero to three secondary classes.

Primary-class test:

> Which change must be true for us to consider this outcome successful, even if every other expected benefit fails?

## Lifecycle

```text
proposed
→ bounded
→ instrumented
→ pursued
→ observed
→ verified
→ retained
```

Exception states:

```text
rejected
superseded
abandoned
decayed
invalidated
```

## Supporting objects

- `OutcomeClass`
- `OutcomeContract`
- `OutcomeObservation`
- `OutcomeEvidence`
- `OutcomeVerdict`
- `OutcomeLink`
- `OutcomeLedger`
- `OutcomeMap`
- `OutcomePortfolio`

Recommended OutcomeLink relationships:

```text
depends_on
enables
contributes_to
conflicts_with
degrades
proves
supersedes
retains
```

## Architecture decision

Quirk Outcome starts as a cross-system protocol/package governed by Evaluation & Evidence and enforced through Control. It should become a primary Quirk System only after it independently owns substantial runtime behavior, policy, storage, APIs, dashboards, and lifecycle operations.

## Golden Outcome Gate

An outcome may be marked Golden only when:

1. A real before-state and after-state are distinguishable.
2. The beneficiary is explicit.
3. The primary class is singular.
4. The change matters beyond completion theater.
5. Evidence was defined before the verdict.
6. Negative effects and guardrails were examined.
7. Ownership and authority are clear.
8. Confidence matches the evidence.
9. Another actor can inspect the claim.
10. The result survives its declared retention window.
11. It remains useful without Bryan performing interpretive CPR.
