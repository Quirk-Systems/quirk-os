# Mixed-media Production Preparation Implementation Plan

> For agentic workers: use superpowers:executing-plans for bounded inline execution and verification.

**Goal:** Turn a mixed-media brief into a bounded, inspectable candidate plan with source identity and explicit delivery gates.
**Architecture:** Add a domain-specific brief compiler and local-byte inspection CLI to the existing quirk-os candidate. Emit the existing loop-spec/v1 and prepare_candidate argument shape. Do not extend the action executor, install grants, or modify the frozen parent evaluator.
**Tech stack:** Python 3.12+, existing jsonschema dependency; no added package.
**Spec:** ../../mixed-media/README.md

## Global constraints
Owner repository: Quirk-Systems/quirk-os. Base: PR #79 at e6344a1a13f359bf8e485a6d2b4d3143749c2600. Candidate only. No source media uploads, production activation, publication, graph writes, preference updates, automatic grants or schema promotion.

## Tasks
- [x] Tests: run `python -m unittest discover -s tests -p 'test_mixed_media*.py' -v`; observe failure before compiler implementation.
- [x] Implement `compile_plan(brief)`, `impact_of(plan, revisions)`, `inspect_sources(brief, root)`, `prepare_arguments(plan)` and CLI in scripts/mixed_media_candidate.py against the accompanying executable tests.
- [x] Verify strict schema, DAG references/cycles, branch-local invalidation, rights gates, immutable inputs, fixed authority, finite budgets, path confinement, digest mismatch, unsupported operation and bounded export.
- [x] Compile synthetic-review.json and inspect its two local source files; preserve actual results in the private/local execution receipt.
- [ ] Publish additive files on a child candidate branch and open a stacked draft PR; leave parent and main unchanged.
- [ ] Reconcile current projection labels on existing Notion/Drive/Airtable records; never rewrite historical proof or last-sync timestamps.
- [ ] Read back every remote write and record remaining live/provider/human-use gates rather than claiming full production completion.
