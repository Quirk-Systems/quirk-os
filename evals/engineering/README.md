---
pretty_name: Quirk Loop, Graph, and Action Engineering Regression Fixtures
language:
  - en
tags:
  - synthetic
  - evaluation
  - regression
  - quirk
configs:
  - config_name: default
    data_files:
      - split: regression
        path: regression-cases.jsonl
---

# Engineering regression fixtures

Status: candidate, synthetic, regression-only.

The 11 JSONL rows are metadata descriptions of executable tests mapped one for
one to section 9 of docs/engineering/ADOPTION-SPEC.md. They are not newly
observed evaluation results, human outcomes, admission evidence, or a held-out
set. The comparator supports future capability and heldout input, but neither is
published here.

The JSONL was produced locally with
scripts.engineering.projections.export_evaluation_cases. Each row separates its
synthetic evidence classification and frozen evaluator digest under
evaluation_metadata. No repository, job, or dataset upload is performed.

## Frozen evaluator

The selector manifest is evaluator-manifest.json. It pins SHA-256 hashes for
the selected tests, their implementation modules and schemas, the section 9
specification, and the integrity runner. Its SHA-256 is:

    755642b9af869a2a4a2104cab7d5a61d0afa162607d276d677f10e5480889c35

The digest covers the exact UTF-8 file bytes, including the final newline. Every
JSONL row pins that value. The caller supplying this digest to comparison code
is responsible for binding it to a trusted source tree; the helper does not
authenticate the caller or repository revision.

## Run the selected tests

From the repository root after installing its development dependencies:

    .venv/bin/python evals/engineering/run_regression.py

The runner verifies the pinned source hashes, JSONL digest and 11-case selector
mapping before executing the selected repository tests. It does not turn their
results into an admission decision. Record the exact source revision, command,
exit status, and test output separately when an observed run is needed.

## JSONL schema

Each row contains schema_version, case_id, split, input, expected, and a separate
evaluation_metadata object. Every published row has split regression,
evidence_class synthetic, status candidate, and authority_effect none.

Load locally with Hugging Face Datasets:

    from datasets import load_dataset
    cases = load_dataset(
        "json",
        data_files={"regression": "evals/engineering/regression-cases.jsonl"},
    )

This repository has no Hugging Face upload step. The connected account inspected
during discovery lacked write-repos scope.

## Limits

The rows describe existing tests; they do not contain test outcomes. Synthetic
fixtures can detect known regressions but do not establish production behavior,
rare-failure safety, or human usefulness. Secret scanning in the exporter is a
bounded structural heuristic. Trusted callers remain responsible for source
classification and data minimization.
