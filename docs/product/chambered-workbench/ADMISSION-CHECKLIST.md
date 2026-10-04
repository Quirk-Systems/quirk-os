# Admission Checklist

**Status:** Candidate review checklist  
**Authority ceiling:** `propose`

## Candidate PR pass criteria

- [ ] All changed files are under `docs/product/chambered-workbench/`.
- [ ] PR is opened as draft.
- [ ] PR title and body state that this is documentation only.
- [ ] No runtime code is added.
- [ ] No schemas, validators, CI, package manifests, or workflows are added.
- [ ] No provider-resource access is requested or implied.
- [ ] No publication access is requested or implied.
- [ ] No canon promotion is claimed.
- [ ] No preference graph mutation is claimed.
- [ ] Four Chambers is treated as the initial chamber set, not a fixed ceiling.
- [ ] N-chamber expansion requires nomination, evidence, review, and separate approval.
- [ ] Operator Contract Extraction is labeled as the approved **candidate direction**, not an approved implementation or Canon contract.
- [ ] Every new contract is explicitly descriptive and non-executable.
- [ ] No actual creative payload is included or published.

## Product-design review checklist

- [ ] The active object remains centered.
- [ ] Evidence remains visible in every chamber.
- [ ] Authority remains visible in every chamber.
- [ ] The transition ledger remains visible in every chamber.
- [ ] Source and signal are distinct.
- [ ] Candidate and canon are distinct.
- [ ] Confidence and permission are distinct.
- [ ] Chamber and lifecycle state are distinct.
- [ ] Exact object version and digest are visible before consequential decisions.
- [ ] Proposer, evaluator, executor, decision authority, and verifier functions remain inspectable and distinguishable.
- [ ] Existing authority and Design Tribunal roles are referenced rather than replaced by a new role dialect.
- [ ] Blocked transitions explain why they are blocked.
- [ ] Receipt schema is visible before consequential transition.
- [ ] Gallery preservation does not imply reuse or promotion.
- [ ] Future chambers cannot bypass the shell contract.
- [ ] A visual cycle does not claim learning, scale, or compounding without a measured return path and decision.
- [ ] Scores and telemetry cannot appear as proof without their evidence contracts.

## HookCandidate contract review

- [ ] `HookCandidate` remains a vertical test fixture and does not reserve or canonize a core object type.
- [ ] The selected fixture is synthetic, redacted, test-only, and non-releaseable.
- [ ] Material changes create exact new versions, digests, and typed lineage edges.
- [ ] `object_digest` covers the immutable candidate-subject snapshot while `payload_digest` covers payload bytes; versioned governance projections and active UI chamber remain separate and carry their own integrity refs.
- [ ] Rights do not inherit silently.
- [ ] Candidate preservation, rejection, deferral, boneyard, supersession, and retirement preserve decision reasons.
- [ ] Only documentary `observe`, `infer`, and `propose` moves appear in this extraction.
- [ ] Operator-facing `inspect_*` names map to `observe`; they do not create a second authority enum.
- [ ] `scoped → composing` and `review_ready → evaluating` are explicit governed transitions, not chamber-navigation side effects.
- [ ] Every move binds an exact subject version and declares consequence, invariant, evidence, authority, risk, reversibility, fallback, and receipt posture.
- [ ] Candidate move output never contains an execution token, provider credential, publication target, implementation reference, applied patch, or mutable receipt.
- [ ] Evidence sufficiency is named-decision-specific, not global.
- [ ] Authority grants match exact subject, version, operation, purpose, environment, risk, time, delegation, and co-approval.
- [ ] Authority scope binds paired object id/version/digest tuples rather than parallel lists.

## Release-blocking fixture backlog

These are not implemented in this PR. They are required before runtime work. The detailed design fixtures live in [`ADVERSARIAL-FIXTURES-v0.1.md`](ADVERSARIAL-FIXTURES-v0.1.md).

- [ ] `circular-diagram-is-not-loop`
- [ ] `automation-is-not-scale`
- [ ] `retention-without-reinvestment`
- [ ] `repetition-without-improvement`
- [ ] `benchmark-gaming`
- [ ] `self-certified-value`
- [ ] `learning-self-promotes`
- [ ] `capability-implies-authority`
- [ ] `candidate-location-implies-canon`
- [ ] `score-without-rubric-or-reviewer`
- [ ] `telemetry-without-event-lineage`
- [ ] Confidence cannot produce or expand authority.
- [ ] Foundry cannot include excluded or reference-only inputs.
- [ ] Transition cannot execute without a receipt schema.
- [ ] Stale grant remains inspectable but unusable.
- [ ] Receipt cannot be silently altered after write.
- [ ] Outcome evidence can contradict the original evaluation.
- [ ] Preference Graph mutation remains blocked until human confirmation.
- [ ] Provider-resource access requires a separate grant kind.
- [ ] Publication access requires a separate grant kind.
- [ ] Gallery preservation cannot imply reuse permission.
- [ ] New chamber cannot duplicate an existing chamber under prettier words.
- [ ] New chamber cannot lower authority/evidence requirements.

## Human approval checklist for later phases

Before implementation planning:

- [ ] exact PR head reviewed;
- [ ] changed files reviewed;
- [ ] candidate scope accepted or revised;
- [ ] runtime exclusion still intact;
- [ ] follow-up implementation scope explicitly named.

Before runtime code:

- [ ] written implementation plan exists;
- [ ] package/module boundaries are approved;
- [ ] schemas and fixtures are approved;
- [ ] tests are named before code;
- [ ] rollback path exists.

Before canon promotion:

- [ ] exact-head decision receipt exists outside the candidate artifact;
- [ ] semantic review passed;
- [ ] authority-integrity fixtures passed;
- [ ] evidence/provenance review passed;
- [ ] migration and compatibility impact is understood;
- [ ] human approval names the exact object/version/scope admitted.
