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

## Authority boundary

Authority ceiling: `infer`.

Passing evidence can support a bounded diagnosis. It cannot publish, deploy, activate runtime state, promote Canon, authorize rollout, approve a payment, issue a refund, mutate Supabase, package a plugin, create a Skill Submission Pack, or self-admit this Skill.

A score, confidence estimate, successful test, green workflow, social commitment, or existing credential never becomes authority by itself. Consequential execution requires a separate scoped human grant.

## Procedure

1. Resolve the candidate, claim, supplied evidence references, evaluated version, and declared comparison or guardrails.
2. Preserve the supplied evidence set exactly; do not invent or silently normalize support.
3. Classify the claim using the deterministic Applause Gate evaluator.
4. Surface contradictions, missing proof, stale/version-mismatched evidence, leakage, proxy substitution, selection effects, and social-pressure risk.
5. Emit a schema-valid `applause-review.v1` object with `authority_effect: none`.
6. Emit candidate evidence only. Stop before rollout, publication, activation, admission, or irreversible action.

## Fail-closed conditions

Stop or withhold success when evidence is fabricated, tampered, stale, revoked, version-mismatched, contaminated, cherry-picked, proxy-substituted, socially pressured, or contradicted by declared guardrails.

Any false `VERIFIED_SUCCESS` on a negative or adversarial fixture is release-blocking candidate evidence.

## Professional-boundary rule

This candidate Skill does not replace medical, legal, financial, safety, or other licensed professional judgment. It evaluates evidence claims and their boundaries; it does not grant domain authority.

## Runtime status

No runtime activation is authorized. Candidate packaging and conformance evidence do not constitute admission. External human admission and a separately scoped runtime grant remain required before any executable Skill loading.
