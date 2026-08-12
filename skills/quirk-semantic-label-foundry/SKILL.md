---
name: quirk-semantic-label-foundry
description: Design, apply, calibrate, and review Quirk classification and labeling systems without allowing labels to become hidden permission, retention, release, or routing authority.
version: 0.2.0
status: candidate
family: perceive
authority_ceiling: propose
manifest: manifest.json
eval_suite: ../../evals/skills/conformance.json
---

# Quirk Semantic Label Foundry

## Quirk contract

- Version: `0.2.0`
- Status: `candidate`
- Authority ceiling: `propose`
- Invariant: **labels describe; policies decide**

## Procedure

1. Resolve the purpose, population, taxonomy version, and decision consequence.
2. Apply deterministic rules and canonical identity matching first.
3. Use entity resolution, similarity, or model classification only when needed.
4. Record method, confidence, evidence spans, and intended validity scope.
5. Route uncertain or consequential assignments to human review.
6. Learn from reviewed corrections without rewriting historical assignments.
7. Monitor class balance, drift, disagreement, and abuse of `other`.
8. Propose new distinctions when unknown, novel, unclassified, or not-applicable is more truthful.

## Output

Taxonomy mapping, assignment batch, confidence distribution, review queue, drift report, and replay fixtures.

## Stop conditions

Do not let a label directly grant access, delete data, ship code, control retention, or authorize release.

## Machine binding

- Manifest: [`manifest.json`](manifest.json)
- Eval suite: [`../../evals/skills/conformance.json`](../../evals/skills/conformance.json)
- Mapping contract: [`../../mappings/skill-package.v1.yaml`](../../mappings/skill-package.v1.yaml)
- Runtime status: candidate source only; the runtime loader must reject this version until a separate admission record and scoped grant exist.

## Invocation contract

Use this skill only when its trigger contract matches, required sources and authority are available, and no trigger collision remains unresolved. The caller owns purpose and authority. The skill owns procedure and evidence. A successful run may emit `label_review_pack` and Proposed Moves; it may not convert either into Canon, active runtime state, or an irreversible write.

## Evaluation and learning

Positive, adversarial, regression, and authority cases are mandatory. Feedback appends evidence and may produce a mutation candidate. It never rewrites this running version. Any successor must receive a new version, digest, evaluation record, and external admission decision.

## Universal stop rule

Capability, credentials, connected tools, successful validation, model confidence, or repeated use never create authority. Stop before self-activation, self-escalation, Canon promotion, history mutation, or action beyond the external grant.
