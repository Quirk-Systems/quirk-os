---
name: quirk-evidence-instrumenter
description: Design receipts, lineage, traces, metrics, logs, and evaluation evidence so Quirk can know what ran, why, under whose authority, at what cost, and with what observed result.
version: 0.2.0
status: candidate
family: preserve
authority_ceiling: propose
manifest: manifest.json
eval_suite: ../../evals/skills/conformance.json
---

# Quirk Evidence Instrumenter

## Quirk contract

- Version: `0.2.0`
- Status: `candidate`
- Authority ceiling: `propose`
- Primary output: observable execution contract

## Required receipt fields

- run and trace identity;
- actor, purpose, authority grant, agent, skill, and manifest version;
- input source references and fingerprints;
- tools, models, workflow version, timestamps, and retries;
- output references and hashes;
- validation, eval scores, warnings, and exceptions;
- latency, compute cost, and human review time;
- acceptance, reuse, and observed effect;
- parent runs and transformation lineage.

## Procedure

Instrument before autonomy. Separate contract validation, content tests, and ongoing monitors. Preserve failed and blocked runs. Use idempotency keys and immutable evidence references. Define which metrics are diagnostic versus decision-authorizing.

## Stop conditions

Do not collect sensitive data merely because it is measurable, and do not let telemetry silently expand operational authority.

## Machine binding

- Manifest: [`manifest.json`](manifest.json)
- Eval suite: [`../../evals/skills/conformance.json`](../../evals/skills/conformance.json)
- Mapping contract: [`../../mappings/skill-package.v1.yaml`](../../mappings/skill-package.v1.yaml)
- Runtime status: candidate source only; the runtime loader must reject this version until a separate admission record and scoped grant exist.

## Invocation contract

Use this skill only when its trigger contract matches, required sources and authority are available, and no trigger collision remains unresolved. The caller owns purpose and authority. The skill owns procedure and evidence. A successful run may emit `evidence_contract` and Proposed Moves; it may not convert either into Canon, active runtime state, or an irreversible write.

## Evaluation and learning

Positive, adversarial, regression, and authority cases are mandatory. Feedback appends evidence and may produce a mutation candidate. It never rewrites this running version. Any successor must receive a new version, digest, evaluation record, and external admission decision.

## Universal stop rule

Capability, credentials, connected tools, successful validation, model confidence, or repeated use never create authority. Stop before self-activation, self-escalation, Canon promotion, history mutation, or action beyond the external grant.
