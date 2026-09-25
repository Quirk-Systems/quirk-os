---
name: quirk-probabilistic-forecaster
description: Produce calibrated Quirk forecasts and scenarios for demand, capacity, cost, risk, throughput, quality, timing, and opportunity, with time-ordered validation and planning implications.
version: 0.2.0
status: candidate
family: decide
authority_ceiling: infer
manifest: manifest.json
eval_suite: ../../evals/skills/conformance.json
---

# Quirk Probabilistic Forecaster

## Quirk contract

- Version: `0.2.0`
- Status: `candidate`
- Authority ceiling: `infer`
- Invariant: a forecast is not a commitment

## Procedure

1. Define target metric, grain, horizon, decision, and data cutoff.
2. Audit missingness, regime changes, leakage, and measurement drift.
3. Establish naïve and seasonal baselines.
4. Compare candidate models with rolling-origin backtests.
5. Report point estimates and calibrated uncertainty intervals.
6. Reconcile forecasts across project, program, portfolio, and time levels when required.
7. Produce downside, expected, upside, and disruption scenarios.
8. Identify assumptions, uncertainty drivers, and triggers for refresh.
9. Translate the forecast into planning implications and Proposed Moves.

## Output

Forecast object, backtest report, calibration evidence, scenario set, and roadmap implications.

## Stop conditions

Do not use random cross-validation on time series, hide uncertainty, or promote a forecast directly into a Roadmap commitment.

## Machine binding

- Manifest: [`manifest.json`](manifest.json)
- Eval suite: [`../../evals/skills/conformance.json`](../../evals/skills/conformance.json)
- Mapping contract: [`../../mappings/skill-package.v1.yaml`](../../mappings/skill-package.v1.yaml)
- Runtime status: candidate source only; the runtime loader must reject this version until a separate admission record and scoped grant exist.

## Invocation contract

Use this skill only when its trigger contract matches, required sources and authority are available, and no trigger collision remains unresolved. The caller owns purpose and authority. The skill owns procedure and evidence. A successful run may emit `forecast_pack` and Proposed Moves; it may not convert either into Canon, active runtime state, or an irreversible write.

## Evaluation and learning

Positive, adversarial, regression, and authority cases are mandatory. Feedback appends evidence and may produce a mutation candidate. It never rewrites this running version. Any successor must receive a new version, digest, evaluation record, and external admission decision.

## Universal stop rule

Capability, credentials, connected tools, successful validation, model confidence, or repeated use never create authority. Stop before self-activation, self-escalation, Canon promotion, history mutation, or action beyond the external grant.
