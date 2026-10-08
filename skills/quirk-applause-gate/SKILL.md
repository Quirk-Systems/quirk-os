---
name: quirk-applause-gate
description: Evaluate claimed wins by separating visible signal, interpretation, causal support, guardrails, evidence integrity, and authority boundaries before success language hardens.
version: 0.1.0
status: candidate
family: challenge
authority_ceiling: infer
manifest: manifest.json
eval_suite: ../../evals/skills/applause-gate-conformance.json
---

# Quirk Applause Gate

Status: `candidate / non-operative`.

Applause Gate evaluates claimed wins before success language hardens into lore. It separates observed signal from interpretation, causal support, guardrail behavior, evidence integrity, version/freshness binding, and execution authority.

## Triggers

Use this Skill when a request asks whether a claimed product, experiment, campaign, rollout, or operational success is supported by identified evidence, causality, and declared guardrails. The requested output must be a bounded evidence analysis before celebration, publication, promotion, or rollout.

## Non-triggers

- Do not use this Skill for generic analytics, reporting, forecasting, dashboarding, or metric calculation that does not ask whether a claimed success is supported.
- Do not use it for medical diagnosis or treatment advice, or for professional legal, financial, or safety judgment.
- Do not use it when the evidence set cannot be identified or when the request is to perform a consequential action rather than analyze its support.

## Input contract

- `claim_context`: the exact claim, candidate, comparison, declared outcome and guardrails, and evaluated version.
- `evidence_refs`: the supplied evidence set with enough provenance, freshness, and version information to test integrity.
- `candidate_ref`: the immutable candidate version being evaluated.

Missing required input causes abstention or a bounded missing-proof request; it never permits invented evidence.

## Output contract

- `applause_review`: a schema-valid `applause-review.v1` analysis with preserved contradictions and `authority_effect: none`.
- `candidate_receipt`: evidence binding the diagnosis to the candidate and supplied references.

Outputs are analysis and evidence only. They cannot publish, mutate, admit, activate, execute a downstream decision, or authorize rollout.

## Authority boundary

Authority ceiling: `infer`.

Passing evidence can support a bounded diagnosis. It cannot publish, deploy, activate runtime state, promote Canon, authorize rollout, approve a payment, issue a refund, mutate Supabase, package a plugin, create a Skill Submission Pack, or self-admit this Skill.

A score, confidence estimate, successful test, green workflow, social commitment, or existing credential never becomes authority by itself. Consequential execution requires a separate scoped human grant.

## Method

1. Resolve the candidate, claim, supplied evidence references, evaluated version, and declared comparison or guardrails.
2. Preserve the supplied evidence set exactly; do not invent or silently normalize support.
3. Classify the claim using the deterministic Applause Gate evaluator.
4. Surface contradictions, missing proof, stale/version-mismatched evidence, leakage, proxy substitution, selection effects, and social-pressure risk.
5. Emit a schema-valid `applause-review.v1` object with `authority_effect: none`.
6. Emit candidate evidence only. Stop before rollout, publication, activation, admission, or irreversible action.

## Quality gates

- The [frozen classifier fixture suite](../../evals/applause-gate/cases.json) must pass without false verified success, fabricated evidence, or authority smuggling.
- The four [shared candidate conformance cases](../../evals/skills/applause-gate-conformance.json) must all pass across the positive, adversarial, regression, and authority classes.
- The [deterministic evaluator evidence](../../docs/applause-gate/H0-B-EVIDENCE.md) establishes classifier and fixture conformance; package integrity is verified separately against this source binding.

Fixtures, evaluator evidence, scores, and passing workflows are candidate evidence only. None constitutes admission or a runtime grant.

## Stop conditions

Stop or withhold success when evidence is fabricated, tampered, stale, revoked, version-mismatched, contaminated, cherry-picked, proxy-substituted, socially pressured, or contradicted by declared guardrails.

Any false `VERIFIED_SUCCESS` on a negative or adversarial fixture is release-blocking candidate evidence.

Stop if the package would require connected tools, runtime writes, live data, authentication, or authority beyond `infer`; those require a separate design decision.

## Runtime status

No runtime activation is authorized. Candidate packaging and conformance evidence do not constitute admission. External human admission and a separately scoped runtime grant remain required before any executable Skill loading.
