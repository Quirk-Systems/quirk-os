---
name: quirk-evidence-instrumenter
description: Design receipts, lineage, traces, metrics, logs, and evaluation evidence so Quirk can know what ran, why, under whose authority, at what cost, and with what observed result.
---

# Quirk Evidence Instrumenter

## Quirk contract

- Version: `0.1.0`
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
