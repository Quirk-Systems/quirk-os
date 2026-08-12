---
name: quirk-value-foundry
description: Detect repeated successful Quirk Moves and propose their promotion into Methods, Skills, Capabilities, Tools, Goods, Data Products, and Golden candidates with evidence and rights.
version: 0.2.0
status: candidate
family: productize
authority_ceiling: propose
manifest: manifest.json
eval_suite: ../../evals/skills/conformance.json
---

# Quirk Value Foundry

## Quirk contract

- Version: `0.2.0`
- Status: `candidate`
- Authority ceiling: `propose`
- Primary output: reusable value candidate

## Promotion route

`repeated Move → pattern candidate → Method → Skill → Capability → Tool or Workflow → demonstrated Outcome → Good → Product → Golden candidate`

## Procedure

1. Identify repeated work and collect outcome evidence.
2. Separate the reusable mechanism from one-time context.
3. Test for hidden Bryan-context and independent reuse.
4. Type inputs, outputs, prerequisites, failure conditions, and authority.
5. Add evaluation fixtures and compare against the current method.
6. Determine the appropriate package: guide, template, skill, tool, service, dataset, signal feed, or Data Product.
7. Audit provenance, licensing, privacy, demand, cost to serve, and support burden.
8. Return a candidate with explicit blockers and admission evidence.

## Stop conditions

Do not productize unclear rights, unverified demand, personal data without purpose, or a capability that cannot fail safely.

## Machine binding

- Manifest: [`manifest.json`](manifest.json)
- Eval suite: [`../../evals/skills/conformance.json`](../../evals/skills/conformance.json)
- Mapping contract: [`../../mappings/skill-package.v1.yaml`](../../mappings/skill-package.v1.yaml)
- Runtime status: candidate source only; the runtime loader must reject this version until a separate admission record and scoped grant exist.

## Invocation contract

Use this skill only when its trigger contract matches, required sources and authority are available, and no trigger collision remains unresolved. The caller owns purpose and authority. The skill owns procedure and evidence. A successful run may emit `value_candidate` and Proposed Moves; it may not convert either into Canon, active runtime state, or an irreversible write.

## Evaluation and learning

Positive, adversarial, regression, and authority cases are mandatory. Feedback appends evidence and may produce a mutation candidate. It never rewrites this running version. Any successor must receive a new version, digest, evaluation record, and external admission decision.

## Universal stop rule

Capability, credentials, connected tools, successful validation, model confidence, or repeated use never create authority. Stop before self-activation, self-escalation, Canon promotion, history mutation, or action beyond the external grant.
