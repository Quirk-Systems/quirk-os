---
name: quirk-control-loop-designer
description: Convert a desired Quirk operating condition into explicit sensors, targets, bounded controllers, actuators, constraints, recovery, and human authority without unstable self-management.
---

# Quirk Control Loop Designer

## Quirk contract

- Version: `0.1.0`
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
