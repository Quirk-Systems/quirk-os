---
name: quirk-roadmap-board-orchestrator
description: Translate Quirk evidence, forecasts, goals, dependencies, authority, capacity, and risk into governed Roadmap, Route, Project, Experiment, and Task Board projections.
---

# Quirk Roadmap Board Orchestrator

## Quirk contract

- Version: `0.1.0`
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
