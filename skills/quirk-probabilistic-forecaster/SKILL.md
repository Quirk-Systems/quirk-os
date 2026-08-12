---
name: quirk-probabilistic-forecaster
description: Produce calibrated Quirk forecasts and scenarios for demand, capacity, cost, risk, throughput, quality, timing, and opportunity, with time-ordered validation and planning implications.
---

# Quirk Probabilistic Forecaster

## Quirk contract

- Version: `0.1.0`
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
