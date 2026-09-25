---
name: quirk-distillation-synthesizer
description: Convert high-volume Quirk sources into smaller, stronger, traceable claims, distinctions, patterns, implications, Proposed Moves, and independently reusable assets.
version: 0.2.0
status: candidate
family: distill
authority_ceiling: infer
manifest: manifest.json
eval_suite: ../../evals/skills/conformance.json
---

# Quirk Distillation Synthesizer

## Quirk contract

- Version: `0.2.0`
- Status: `candidate`
- Authority ceiling: `infer`
- Quality rule: compression must preserve decisive nuance

## Distillation ladder

1. Extract what each source actually says.
2. Normalize terms, entities, dates, and comparison frames.
3. State atomic claims.
4. Attach supporting and contradicting evidence.
5. Identify distinctions that change interpretation.
6. Detect patterns across sources and contexts.
7. Synthesize only what becomes visible through combination.
8. State operational implications.
9. Propose the smallest justified Move.
10. Nominate durable outputs as Asset or Golden candidates.

## Output

A decision brief, research pack, implementation spec, Map, prompt pack, capability proposal, dataset, or other typed asset with provenance.

## Stop conditions

Do not produce a longer summary and call it synthesis; do not erase disagreement, uncertainty, or the source material’s original charge.

## Machine binding

- Manifest: [`manifest.json`](manifest.json)
- Eval suite: [`../../evals/skills/conformance.json`](../../evals/skills/conformance.json)
- Mapping contract: [`../../mappings/skill-package.v1.yaml`](../../mappings/skill-package.v1.yaml)
- Runtime status: candidate source only; the runtime loader must reject this version until a separate admission record and scoped grant exist.

## Invocation contract

Use this skill only when its trigger contract matches, required sources and authority are available, and no trigger collision remains unresolved. The caller owns purpose and authority. The skill owns procedure and evidence. A successful run may emit `synthesis_pack` and Proposed Moves; it may not convert either into Canon, active runtime state, or an irreversible write.

## Evaluation and learning

Positive, adversarial, regression, and authority cases are mandatory. Feedback appends evidence and may produce a mutation candidate. It never rewrites this running version. Any successor must receive a new version, digest, evaluation record, and external admission decision.

## Universal stop rule

Capability, credentials, connected tools, successful validation, model confidence, or repeated use never create authority. Stop before self-activation, self-escalation, Canon promotion, history mutation, or action beyond the external grant.
