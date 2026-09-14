---
pretty_name: Quirk Beauty Taste Engine Candidate Evals
license: other
task_categories:
  - text-classification
  - text-generation
tags:
  - synthetic
  - private
  - preference-evaluation
  - governance
---

# Dataset Card

## Status

Candidate, synthetic, private. Not approved for Hub upload.

## Purpose

Evaluate whether a recommendation or explanation system preserves explicit preference evidence and authority boundaries.

## Data sources

Only handcrafted synthetic fixtures in v0.1.

## Fields

- `id` — stable fixture identifier;
- `purpose` — preference partition;
- `choice` — explicit forced choice;
- `evidence` — expected contrast evidence;
- `candidates` — recommendation options;
- `expectedTopOptionId` — deterministic expected rank;
- `failureLabels` — behavior that must be rejected;
- `synthetic` — always `true` in v0.1.

## Intended use

- unit and integration tests;
- provider comparison after the core proof;
- error analysis;
- adversarial evaluation.

## Out-of-scope use

- training a personal preference model;
- demographic or sensitive-attribute inference;
- public claims of recommendation quality;
- replacing human outcomes;
- public upload without a new approval.

## Known limitations

Synthetic fixtures do not represent the messiness, contradiction, context dependence, or distribution of real beauty preference. They can test invariants, not market accuracy.
