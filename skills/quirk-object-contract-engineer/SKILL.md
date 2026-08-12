---
name: quirk-object-contract-engineer
description: Convert a Quirk object, event, dataset, agent, skill, capability, or workflow into an interoperable contract with semantics, schema, lifecycle, evidence, authority, and compatibility rules.
version: 0.2.0
status: candidate
family: structure
authority_ceiling: propose
manifest: manifest.json
eval_suite: ../../evals/skills/conformance.json
---

# Quirk Object Contract Engineer

## Quirk contract

- Version: `0.2.0`
- Status: `candidate`
- Authority ceiling: `propose`
- Primary output: contract pack, never automatic admission

## Procedure

1. State the object’s grammatical job and why existing primitives are insufficient.
2. Define identity, required fields, optional fields, relations, and invariants.
3. Define lifecycle states and legal transitions.
4. Separate descriptive labels from permissions and policy.
5. Specify source authority, provenance, retention, and supersession.
6. Generate JSON Schema plus representative valid and invalid examples.
7. Define version compatibility, migration, rollback, and failure semantics.
8. Add class-specific evidence and eleven adversarial fixtures where consequential.

## Output contract

Return definitions, schema, state machine, authority matrix, examples, fixtures, migration notes, and admission blockers.

## Stop conditions

Do not promote an imported term into Canon, let code inheritance define ontology, or mark a contract active because it validates structurally.

## Machine binding

- Manifest: [`manifest.json`](manifest.json)
- Eval suite: [`../../evals/skills/conformance.json`](../../evals/skills/conformance.json)
- Mapping contract: [`../../mappings/skill-package.v1.yaml`](../../mappings/skill-package.v1.yaml)
- Runtime status: candidate source only; the runtime loader must reject this version until a separate admission record and scoped grant exist.

## Invocation contract

Use this skill only when its trigger contract matches, required sources and authority are available, and no trigger collision remains unresolved. The caller owns purpose and authority. The skill owns procedure and evidence. A successful run may emit `contract_pack` and Proposed Moves; it may not convert either into Canon, active runtime state, or an irreversible write.

## Evaluation and learning

Positive, adversarial, regression, and authority cases are mandatory. Feedback appends evidence and may produce a mutation candidate. It never rewrites this running version. Any successor must receive a new version, digest, evaluation record, and external admission decision.

## Universal stop rule

Capability, credentials, connected tools, successful validation, model confidence, or repeated use never create authority. Stop before self-activation, self-escalation, Canon promotion, history mutation, or action beyond the external grant.
