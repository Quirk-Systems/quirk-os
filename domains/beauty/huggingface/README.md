# Hugging Face Evaluation Boundary

## v0.1 decision

Hugging Face is not a runtime dependency. No model or dataset is downloaded, trained, or uploaded for the proof.

This directory prepares a later evaluation package for:

- deterministic ranking fixtures;
- explanation-preservation tests;
- failure labels;
- model-provider comparisons;
- reproducible benchmark reporting.

## Privacy ceiling

Do not upload real participant preference evidence, notes, identifiers, images, outcomes, or graph state to the Hub.

Public or shared publication requires:

1. de-identification review;
2. participant and purpose authorization;
3. dataset-card completion;
4. provenance and license review;
5. leakage testing;
6. explicit Bryan approval.

## v0.1 contents

- `DATASET_CARD.md` — candidate private dataset documentation;
- `eval-row.schema.json` — strict row contract;
- `sample-eval.jsonl` — synthetic fixtures only.

## Deferred model benchmark

After the deterministic proof succeeds, explanation renderers may be evaluated on:

- evidence preservation;
- unsupported-claim rate;
- uncertainty preservation;
- authority-boundary compliance;
- sensitive-inference refusal;
- instruction-injection resistance;
- comprehension by the participant.

A leaderboard cannot promote a model into authority. It only informs a bounded adapter choice.
