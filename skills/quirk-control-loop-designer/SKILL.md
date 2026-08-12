---
name: quirk-control-loop-designer
description: Convert a desired Quirk operating condition into explicit sensors, targets, bounded controllers, actuators, constraints, recovery, and human authority without unstable self-management.
version: 0.2.0
status: candidate
family: evolve
authority_ceiling: propose
manifest: manifest.json
eval_suite: ../../evals/skills/conformance.json
---

# Quirk Control Loop Designer

## Quirk contract

- Version: `0.2.0`
- Status: `candidate`
- Authority ceiling: `propose`
- Default controller: threshold plus deadband and hysteresis

## Procedure

1. Name the controlled object and desired condition.
2. Define a trustworthy signal, aggregation window, and sampling interval.
3. Set target, tolerance, error budget, and uncertainty.
4. Choose the simplest adequate controller.
5. Define reversible actuators and their independent authority ceilings.
6. Add saturation, cooldown, rate limits, maximum batch size, and circuit breakers.
7. Specify rollback, compensation, escalation, and safe degraded state.
8. Simulate delayed, noisy, missing, adversarial, and contradictory signals.
9. Require evidence before changing controller parameters.

## Output

A typed `ControlPolicy`, simulation fixtures, observability requirements, and admission blockers.

## Stop conditions

Do not control a system using untrusted sensors, allow a controller to rewrite its own limits, or use model capability as permission to actuate.

## Machine binding

- Manifest: [`manifest.json`](manifest.json)
- Eval suite: [`../../evals/skills/conformance.json`](../../evals/skills/conformance.json)
- Mapping contract: [`../../mappings/skill-package.v1.yaml`](../../mappings/skill-package.v1.yaml)
- Runtime status: candidate source only; the runtime loader must reject this version until a separate admission record and scoped grant exist.

## Invocation contract

Use this skill only when its trigger contract matches, required sources and authority are available, and no trigger collision remains unresolved. The caller owns purpose and authority. The skill owns procedure and evidence. A successful run may emit `control_policy` and Proposed Moves; it may not convert either into Canon, active runtime state, or an irreversible write.

## Evaluation and learning

Positive, adversarial, regression, and authority cases are mandatory. Feedback appends evidence and may produce a mutation candidate. It never rewrites this running version. Any successor must receive a new version, digest, evaluation record, and external admission decision.

## Universal stop rule

Capability, credentials, connected tools, successful validation, model confidence, or repeated use never create authority. Stop before self-activation, self-escalation, Canon promotion, history mutation, or action beyond the external grant.
