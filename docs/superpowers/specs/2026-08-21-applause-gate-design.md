# Applause Gate Candidate Design — H0-A

Date: 2026-08-21  
Status: **candidate / fixture-only / non-operative**  
Authority ceiling: **infer**

## Decision

Adopt Approach C: staged dual-boundary. Prove the internal diagnostic contract first, then consider a separately authorized skills-only package derived from the evaluated source. This H0-A tranche stops before evaluator implementation, Supabase mutation, plugin packaging, submission drafting, merge, or publication.

## Problem

Visible signals are routinely promoted into success claims before meaning, causality, version lineage, guardrails, and contradictory evidence have been established. `Applause Gate` is a candidate evaluator for separating:

`signal → interpretation → diagnosis → verified success`

The evaluator itself does **not** exist in H0-A. H0-A only freezes the claims vocabulary and fixture corpus that a later implementation would have to satisfy.

## Governing question

Does the supplied evidence justify the claimed success, or only show that something noticeable happened?

## Candidate identity

- Internal ID: `quirk-applause-gate`
- Working public identity: `Applause Before Diagnosis`
- Candidate version: `0.1.0-fixture-only`
- Family: `evaluate`
- Authority ceiling: `infer`
- Future primary output: `applause_review`

None of those fields admits, activates, publishes, or packages the candidate.

## Verdict contract

The fixture corpus locks six candidate verdicts:

1. `SIGNAL_ONLY` — something changed, but meaning or cause remains unproved.
2. `SUPPORTED_DIAGNOSIS` — the explanation is supported, but the full success claim remains bounded.
3. `VERIFIED_SUCCESS` — outcome, causal support, evaluated version, and declared guardrails are supported.
4. `FALSE_POSITIVE` — the visible signal does not support the claimed success.
5. `UNRESOLVED` — material evidence conflicts or remains incomplete.
6. `EVIDENCE_INTEGRITY_FAILURE` — version, receipt, source, holdout, digest, or lineage cannot be trusted.

H0-A deliberately defines no scalar success score. A single number would invite the exact premature-certainty failure this evaluator is intended to detect.

## Fixture tranche

The corpus contains exactly:

- 5 positive cases;
- 3 negative cases;
- 11 adversarial cases.

The adversarial set covers proxy substitution, cherry-picked windows, multiple comparisons, holdout reuse/leakage, novelty effects, segment harm, survivorship/selection bias, stale or wrong-version evidence, social pressure as evidence, score/confidence authority smuggling, and receipt/digest tampering.

Negative and adversarial cases are structurally prohibited from expecting `VERIFIED_SUCCESS`.

## H0-A repository surface

This tranche may add only:

- this design document;
- `evals/applause-gate/cases.json`;
- `scripts/validate_applause_gate_fixtures.py`;
- `tests/test_applause_gate_fixtures.py`;
- `.github/workflows/applause-gate-fixtures.yml`.

It may not add `skills/quirk-applause-gate/`, a skill manifest, an evaluator module, a runtime loader change, a Supabase migration/write, `.codex-plugin/plugin.json`, public listing copy, submission artifacts, release metadata, or deployment configuration.

## Structural validator

The H0-A validator is intentionally not the future evaluator. It only proves that the fixture corpus itself has not drifted across these structural invariants:

- stable candidate ID and schema version;
- exact 5/3/11 case counts;
- exact stable IDs `ABG-P01..P05`, `ABG-N01..N03`, `ABG-A01..A11`;
- unique IDs;
- required evidence-bound fields;
- closed verdict vocabulary;
- negative/adversarial cases cannot expect `VERIFIED_SUCCESS`;
- the candidate boundary explicitly denies evaluator implementation, Supabase mutation, plugin packaging, submission drafting, merge, and publication.

Passing structural validation is **candidate evidence only** and has `admission_effect: none`.

## CI boundary

The fixture workflow is pull-request scoped, read-only (`contents: read`), path-filtered to this H0-A surface, and uploads only the generated fixture-validation report. It has no secrets, deployments, provider writes, `pull_request_target`, schedules, or production actions.

## Future H0-B / later work — explicitly unauthorized here

A later human grant would be required before any of the following:

- implement deterministic evaluator behavior;
- add a `SKILL.md` or manifest;
- integrate shared skill conformance;
- run Plugin Eval against a local skill path;
- create a plugin package;
- write any Supabase projection evidence;
- draft a Skill Submission Pack;
- merge or publish anything.

## H0-A acceptance criteria

H0-A is complete only when fresh evidence shows:

1. the fixture test suite passes;
2. structural validation returns `PASS` with counts 5/3/11 and total 19;
3. the committed diff contains only the five allowed H0-A paths;
4. a draft PR targets `main` from `agent/quirk-applause-gate-fixtures`;
5. the PR body explicitly states the stop boundary and does not claim admission, evaluator completion, packaging, submission readiness, merge readiness, or publication.
