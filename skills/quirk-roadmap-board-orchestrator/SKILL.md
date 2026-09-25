---
name: quirk-roadmap-board-orchestrator
description: Translate Quirk evidence, forecasts, goals, dependencies, authority, capacity, and risk into governed Roadmap, Route, Project, Experiment, and Task Board projections.
version: 0.2.0
status: candidate
family: connect
authority_ceiling: propose
manifest: manifest.json
eval_suite: ../../evals/skills/conformance.json
---

# Quirk Roadmap Board Orchestrator

## Quirk contract

- Version: `0.2.0`
- Status: `candidate`
- Authority ceiling: `propose`
- Invariant: the Board is a projection, not Canon

## Procedure

1. Resolve the desired outcome and decision authority.
2. Separate Forecast, Scenario, Bet, Roadmap Item, Route, Task, and Outcome.
3. Decompose work into observable Moves with acceptance evidence.
4. Map dependencies, capacity, WIP, cost of delay, risk, and reversibility.
5. Preserve a priority vector rather than one fake-precise score.
6. Admit work to Ready only when authority, criteria, evidence floor, dependencies, capacity, and rollback are present.
7. Stop pulling work when WIP or error budgets are exhausted.
8. Rebalance from observed outcomes and updated forecasts through Proposed Moves.

## Output

Roadmap projection, dependency graph, Task Board, blocked-work report, capacity scenario, and decision queue.

## Stop conditions

Do not fabricate owners, dates, authority, or certainty; do not let a board edit become a canonical decision.

## Machine binding

- Manifest: [`manifest.json`](manifest.json)
- Eval suite: [`../../evals/skills/conformance.json`](../../evals/skills/conformance.json)
- Mapping contract: [`../../mappings/skill-package.v1.yaml`](../../mappings/skill-package.v1.yaml)
- Runtime status: candidate source only; the runtime loader must reject this version until a separate admission record and scoped grant exist.

## Invocation contract

Use this skill only when its trigger contract matches, required sources and authority are available, and no trigger collision remains unresolved. The caller owns purpose and authority. The skill owns procedure and evidence. A successful run may emit `roadmap_projection` and Proposed Moves; it may not convert either into Canon, active runtime state, or an irreversible write.

## Evaluation and learning

Positive, adversarial, regression, and authority cases are mandatory. Feedback appends evidence and may produce a mutation candidate. It never rewrites this running version. Any successor must receive a new version, digest, evaluation record, and external admission decision.

## Universal stop rule

Capability, credentials, connected tools, successful validation, model confidence, or repeated use never create authority. Stop before self-activation, self-escalation, Canon promotion, history mutation, or action beyond the external grant.
