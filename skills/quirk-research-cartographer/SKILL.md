---
name: quirk-research-cartographer
description: Turn an open Quirk question into a navigable research route with terminology, primary sources, claims, evidence, contradictions, uncertainty, stopping conditions, and practical implications.
version: 0.2.0
status: candidate
family: research
authority_ceiling: infer
manifest: manifest.json
eval_suite: ../../evals/skills/conformance.json
---

# Quirk Research Cartographer

## Quirk contract

- Version: `0.2.0`
- Status: `candidate`
- Authority ceiling: `infer`
- Primary output: research map, not automatic decision

## Procedure

1. Decompose the question into decision-relevant subquestions.
2. Build a terminology map and identify ambiguous or imported language.
3. Define source hierarchy, freshness needs, and exclusion rules.
4. Retrieve primary sources before commentary where possible.
5. Extract claims and attach supporting, contradicting, and contextual evidence.
6. Map disagreement, missing coverage, and rival interpretations.
7. State confidence and what would change it.
8. Stop when the decision, experiment, implementation, or remaining uncertainty is clearer—not when the source pile is merely large.
9. Produce refresh triggers and Proposed Moves.

## Output

Question tree, source plan, claim/evidence graph, contradiction matrix, freshness report, synthesis route, and monitoring schedule.

## Stop conditions

Do not disguise source volume as certainty or silently collapse unresolved disagreement.

## Machine binding

- Manifest: [`manifest.json`](manifest.json)
- Eval suite: [`../../evals/skills/conformance.json`](../../evals/skills/conformance.json)
- Mapping contract: [`../../mappings/skill-package.v1.yaml`](../../mappings/skill-package.v1.yaml)
- Runtime status: candidate source only; the runtime loader must reject this version until a separate admission record and scoped grant exist.

## Invocation contract

Use this skill only when its trigger contract matches, required sources and authority are available, and no trigger collision remains unresolved. The caller owns purpose and authority. The skill owns procedure and evidence. A successful run may emit `research_map` and Proposed Moves; it may not convert either into Canon, active runtime state, or an irreversible write.

## Evaluation and learning

Positive, adversarial, regression, and authority cases are mandatory. Feedback appends evidence and may produce a mutation candidate. It never rewrites this running version. Any successor must receive a new version, digest, evaluation record, and external admission decision.

## Universal stop rule

Capability, credentials, connected tools, successful validation, model confidence, or repeated use never create authority. Stop before self-activation, self-escalation, Canon promotion, history mutation, or action beyond the external grant.
