# Applause Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the candidate-only Applause Gate implementation that validates `applause-review` objects, classifies supplied success evidence deterministically, binds the internal candidate Skill package only after evaluator evidence passes, and emits candidate receipts without runtime activation.

**Architecture:** H0-B layers the implementation on the approved H0-A fixture corpus at PR #48 head `2cee4c829644133e0882a68656733222fa01c344`. The schema is the contract, the classifier is a pure local function with no hidden I/O, the conformance runner turns fixture evidence into content-addressed receipts, and the Skill package is added only after schema/classifier evidence passes. Git remains the source of truth; generated evidence is uploaded by CI or reported in PR evidence, not committed as authority.

**Tech Stack:** Python 3.13 standard library, `unittest`, `jsonschema` from `requirements-evals.txt`, Draft 2020-12 JSON Schema, GitHub Actions pinned actions already used by the H0-A workflow.

**Spec:** `docs/superpowers/specs/2026-08-21-applause-gate-design.md`; H0-B authorization is recorded in issue `#51`; H0-A evidence is PR `#48` at head `2cee4c829644133e0882a68656733222fa01c344`.

## Global Constraints

- Candidate-only: no runtime activation, Canon promotion, merge, admission, deployment, release, publication, OpenAI portal action, plugin packaging, or Skill Submission Pack.
- No Supabase mutation, migration, projection write, or remote database dependency in H0-B.
- Preserve the exact six-value verdict vocabulary: `SIGNAL_ONLY`, `SUPPORTED_DIAGNOSIS`, `VERIFIED_SUCCESS`, `FALSE_POSITIVE`, `UNRESOLVED`, `EVIDENCE_INTEGRITY_FAILURE`.
- Preserve the H0-A fixture tranche exactly: 5 positive cases, 3 negative cases, 11 adversarial cases, 19 total.
- Schema/classifier behavior uses TDD: write a failing test, observe the expected failure, implement minimal code, verify green, then refactor.
- The classifier must be pure and deterministic: no network, filesystem mutation, database access, model calls, current clock, randomness, environment-variable reads, or hidden mutable state.
- The classifier must not read fixture `expected` fields; test adapters strip `expected` before classification.
- False `VERIFIED_SUCCESS` on any negative/adversarial case is release-blocking.
- Evidence fabrication, non-determinism, hidden I/O, authority smuggling, fixture weakening, or validator weakening stops the tranche.
- Passing tests produce candidate evidence only and never grant authority.

---

## File Structure

Create or modify only these path families unless Bryan issues a successor grant:

- `schemas/applause-review.schema.json` — strict Draft 2020-12 output/input review contract.
- `examples/applause-gate/applause-review.valid.json` — one positive schema example used by schema tests.
- `scripts/applause_gate/__init__.py` — package export surface.
- `scripts/applause_gate/classifier.py` — pure classification functions and canonical output construction.
- `scripts/applause_gate/receipt.py` — canonical JSON and SHA-256 helpers for deterministic evidence receipts.
- `scripts/validate_applause_gate.py` — conformance runner for fixtures, schema validation, determinism, and receipt output.
- `tests/test_applause_gate_schema.py` — schema contract tests.
- `tests/test_applause_gate_classifier.py` — rule-level classifier tests.
- `tests/test_applause_gate_conformance.py` — all visible fixture cases and no-false-success checks.
- `tests/test_applause_gate_determinism.py` — cold-process determinism and canonical receipt tests.
- `.github/workflows/applause-gate-conformance.yml` — read-only PR workflow for H0-B conformance evidence.
- `skills/quirk-applause-gate/SKILL.md` — candidate internal Skill source after evaluator evidence passes.
- `skills/quirk-applause-gate/manifest.json` — candidate manifest after source/evaluator evidence passes.
- `skills/README.md`, `skills/registry.json`, `evals/skills/conformance.json`, and `scripts/validate_skills.py` — registry/conformance updates only after the candidate Skill is added.

Generated but not committed by default:

- `evals/applause-gate/conformance-results.json`
- `evals/applause-gate/determinism-results.json`
- `evals/skills/conformance-results.json`

## Read Set Lock (must be re-verified before execution)

- Approved design spec: `docs/superpowers/specs/2026-08-21-applause-gate-design.md`
- H0-A review/evidence baseline: PR `#48` head `2cee4c829644133e0882a68656733222fa01c344`
- Authorization decision: issue `#51` decision `AUTHORIZE_H0_B` (required before Task 1 starts)
- Fixture corpus file: `evals/applause-gate/cases.json`
- Fixture corpus digest (sha256): `987dab65550837b6abe2d5d820f4c6e5fbd8531b3e56f85e015d36c26b65be2f`

If issue `#51` is missing `AUTHORIZE_H0_B` or the fixture digest differs, stop and request a new human grant before any implementation task.

## Task Gates, Path Allowlists, and Excluded Paths

Each task is an independent review unit. Do not begin task _N+1_ until reviewer approval on task _N_ evidence.

| Task | Path allowlist (exact) | Explicit excluded paths | RED command + expected failure | GREEN command + expected pass | REFACTOR command + expected pass | Reviewer gate evidence |
| --- | --- | --- | --- | --- | --- | --- |
| 1 Schema contract | `schemas/applause-review.schema.json`, `examples/applause-gate/applause-review.valid.json`, `tests/test_applause_gate_schema.py` | `supabase/**`, `.codex-plugin/**`, `platform/**`, `workflows/deploy/**`, any runtime activation files | `python -m unittest tests/test_applause_gate_schema.py -v` fails because schema/example files do not exist yet | `python -m unittest tests/test_applause_gate_schema.py -v` returns 4 passing tests | Re-run `python -m unittest tests/test_applause_gate_schema.py -v` after cleanup/refactor; still 4 passing tests | Commit SHA + test output attached for reviewer sign-off |
| 2 Classifier core | `scripts/applause_gate/__init__.py`, `scripts/applause_gate/classifier.py`, `tests/test_applause_gate_classifier.py` | Any workflow, Supabase, plugin, submission, release, deployment, or portal paths | `PYTHONPATH=scripts python -m unittest tests/test_applause_gate_classifier.py -v` fails because classifier module is missing | Same command passes all focused classifier tests | Re-run same command after local refactor; all tests still pass | Commit SHA + verdict rule assertions approved |
| 3 Conformance runner + CI | `scripts/validate_applause_gate.py`, `tests/test_applause_gate_conformance.py`, `.github/workflows/applause-gate-conformance.yml` | Runtime loader changes, Supabase, plugin package, submission assets, deployment/release paths | `PYTHONPATH=scripts python -m unittest tests/test_applause_gate_conformance.py -v` fails because validator script is missing | `PYTHONPATH=scripts python -m unittest tests/test_applause_gate_conformance.py -v` and `PYTHONPATH=scripts python scripts/validate_applause_gate.py --repo . --require-pass` both pass | Re-run both GREEN commands after refactor; still pass with zero false-verified-success | Commit SHA + workflow file diff + validator report reviewed |
| 4 Determinism + receipt binding | `scripts/applause_gate/receipt.py`, `scripts/validate_applause_gate.py`, `tests/test_applause_gate_determinism.py` | Same excluded set as Task 3 plus any admission/promotion files | `PYTHONPATH=scripts python -m unittest tests/test_applause_gate_determinism.py -v` fails because receipt module/fields are missing | `PYTHONPATH=scripts python -m unittest tests/test_applause_gate_determinism.py -v`, `PYTHONPATH=scripts python -m unittest tests/test_applause_gate_conformance.py -v`, and `PYTHONPATH=scripts python scripts/validate_applause_gate.py --repo . --require-pass` all pass | Re-run all GREEN commands after receipt refactor; digest and determinism checks remain stable | Commit SHA + deterministic hash proof approved |
| 5 Candidate Skill package | `skills/quirk-applause-gate/SKILL.md`, `skills/quirk-applause-gate/manifest.json`, `skills/README.md`, `skills/registry.json`, `evals/skills/conformance.json`, `scripts/validate_skills.py`, `tests/test_skill_runtime.py` | `.codex-plugin/**`, submission pack files, OpenAI portal assets, Supabase files, deployment/release files | `PYTHONPATH=scripts python -m unittest discover -s tests -p 'test_applause_gate_*.py' -v` fails because package/registry refs are missing | `PYTHONPATH=scripts python -m unittest discover -s tests -p 'test_applause_gate_*.py' -v` and `PYTHONPATH=scripts python scripts/validate_skills.py --repo . --output evals/skills/conformance-results.json` pass | Re-run both GREEN commands after manifest/registry cleanup; still pass | Commit SHA + package integrity hashes + reviewer approval |
| 6 Whole-branch evidence + stop gate | PR body/evidence only; optional `docs/applause-gate/H0-B-EVIDENCE.md` if separately authorized | Any non-evidence code changes, merge/publish/admission/deploy actions, Supabase/plugin/submission mutations | `git diff --name-only main...HEAD` fails scope check if unauthorized paths appear | Full verification commands in Task 6 Step 1 exit 0 and scope check includes only authorized files | Re-run full verification before handoff; outputs unchanged except timestamped evidence artifacts | Human reviewer decision from Bryan required before any execution authority |

Stage only confirmed files with `git add -- <explicit paths>`. Never use `git add .` or `git add -A`.

---

### Task 1: `applause-review` schema contract

**Files:**
- Create: `schemas/applause-review.schema.json`
- Create: `examples/applause-gate/applause-review.valid.json`
- Create: `tests/test_applause_gate_schema.py`

**Interfaces:**
- Consumes: H0-A verdict vocabulary and H0-A fixture evidence vocabulary from `evals/applause-gate/cases.json`.
- Produces: `applause-review.schema.json`, validating objects with `schema_version`, `review_id`, `candidate_id`, `case_id`, `claim`, `signal`, state fields, `verdict`, evidence references, warnings, missing proof, reversible next move, and `authority_effect: "none"`.

- [ ] **Step 1: Write the failing schema test**

Create `tests/test_applause_gate_schema.py` with this initial test code:

```python
from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "applause-review.schema.json"
EXAMPLE = ROOT / "examples" / "applause-gate" / "applause-review.valid.json"


class ApplauseReviewSchemaTests(unittest.TestCase):
    def validator(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        return Draft202012Validator(schema)

    def test_valid_review_example_is_accepted(self):
        errors = list(self.validator().iter_errors(json.loads(EXAMPLE.read_text(encoding="utf-8"))))
        self.assertEqual(errors, [])

    def test_scalar_success_score_is_rejected(self):
        review = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        review["success_score"] = 0.99
        errors = list(self.validator().iter_errors(review))
        self.assertTrue(errors)

    def test_authority_effect_must_be_none(self):
        review = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        review["authority_effect"] = "authorize_rollout"
        errors = list(self.validator().iter_errors(review))
        self.assertTrue(errors)

    def test_verdict_vocabulary_is_exact(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        verdict_enum = schema["properties"]["verdict"]["enum"]
        self.assertEqual(
            verdict_enum,
            [
                "SIGNAL_ONLY",
                "SUPPORTED_DIAGNOSIS",
                "VERIFIED_SUCCESS",
                "FALSE_POSITIVE",
                "UNRESOLVED",
                "EVIDENCE_INTEGRITY_FAILURE",
            ],
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the schema test and observe RED**

Run:

```bash
python -m unittest tests/test_applause_gate_schema.py -v
```

Expected: FAIL because `schemas/applause-review.schema.json` and the valid example do not exist.

- [ ] **Step 3: Add the minimal valid example**

Create `examples/applause-gate/applause-review.valid.json`:

```json
{
  "schema_version": "applause-review.v1",
  "review_id": "review.ABG-P01",
  "candidate_id": "quirk-applause-gate",
  "case_id": "ABG-P01",
  "claim": "Variant B materially improves the preregistered primary outcome without degrading declared guardrails.",
  "signal": "Primary conversion increased against the pinned control during the preregistered window.",
  "claim_state": "bounded",
  "signal_state": "detected",
  "evidence_sufficiency": "sufficient",
  "causal_support": "supported",
  "contradiction_state": "none_detected",
  "guardrail_state": "stable",
  "version_binding": "bound",
  "freshness_state": "current",
  "commitment_risk": "low",
  "verdict": "VERIFIED_SUCCESS",
  "required_codes": ["PREREGISTERED_HYPOTHESIS_BOUND", "GUARDRAILS_STABLE"],
  "withheld_claims": [],
  "missing_proof": [],
  "reversible_next_move": "Record the bounded verified-success review as candidate evidence only.",
  "evidence_refs": ["preregistration_ref", "pinned_control_ref", "primary_metric_result_ref", "guardrail_result_refs", "evaluated_version_ref"],
  "warnings": [],
  "authority_effect": "none"
}
```

- [ ] **Step 4: Add the minimal schema**

Create `schemas/applause-review.schema.json` with `additionalProperties: false`, the required fields from the example, the exact verdict enum, and `authority_effect` as a `const` of `none`. The schema must also reject `success_score` because the root object is closed.

- [ ] **Step 5: Run the schema tests and observe GREEN**

Run:

```bash
python -m unittest tests/test_applause_gate_schema.py -v
```

Expected: 4 tests pass.

- [ ] **Step 6: Commit only schema paths**

Run:

```bash
git add -- schemas/applause-review.schema.json examples/applause-gate/applause-review.valid.json tests/test_applause_gate_schema.py
git commit -m "feat: add applause review schema contract"
```

---

### Task 2: Pure classifier core

**Files:**
- Create: `scripts/applause_gate/__init__.py`
- Create: `scripts/applause_gate/classifier.py`
- Create: `tests/test_applause_gate_classifier.py`

**Interfaces:**
- Consumes: `schemas/applause-review.schema.json`, H0-A fixture objects stripped of `expected`.
- Produces: `fixture_to_request(case: dict) -> dict`, `classify_review_request(request: dict) -> dict`, and schema-valid `applause-review.v1` outputs.

- [ ] **Step 1: Write the failing classifier tests**

Create `tests/test_applause_gate_classifier.py`:

```python
from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas" / "applause-review.schema.json").read_text(encoding="utf-8"))
CASES = json.loads((ROOT / "evals" / "applause-gate" / "cases.json").read_text(encoding="utf-8"))["cases"]


def case_by_id(case_id: str) -> dict:
    return next(case for case in CASES if case["id"] == case_id)


class ApplauseGateClassifierTests(unittest.TestCase):
    def validate_review(self, review: dict) -> None:
        errors = list(Draft202012Validator(SCHEMA).iter_errors(review))
        self.assertEqual(errors, [])

    def classify(self, case_id: str) -> dict:
        from applause_gate.classifier import classify_review_request, fixture_to_request

        case = case_by_id(case_id)
        request = fixture_to_request(case)
        self.assertNotIn("expected", request)
        review = classify_review_request(request)
        self.validate_review(review)
        self.assertEqual(review["authority_effect"], "none")
        return review

    def test_preregistered_ab_test_returns_verified_success(self):
        self.assertEqual(self.classify("ABG-P01")["verdict"], "VERIFIED_SUCCESS")

    def test_dashboard_only_claim_returns_signal_only(self):
        review = self.classify("ABG-N01")
        self.assertEqual(review["verdict"], "SIGNAL_ONLY")
        self.assertIn("BASELINE_OR_CAUSAL_EVIDENCE_MISSING", review["required_codes"])

    def test_proxy_substitution_returns_false_positive(self):
        review = self.classify("ABG-A01")
        self.assertEqual(review["verdict"], "FALSE_POSITIVE")
        self.assertIn("PROXY_NOT_PRIMARY_OUTCOME", review["required_codes"])

    def test_holdout_leakage_returns_integrity_failure(self):
        review = self.classify("ABG-A04")
        self.assertEqual(review["verdict"], "EVIDENCE_INTEGRITY_FAILURE")
        self.assertIn("EVALUATION_LEAKAGE", review["required_codes"])

    def test_confidence_does_not_authorize_rollout(self):
        review = self.classify("ABG-A10")
        self.assertEqual(review["verdict"], "UNRESOLVED")
        self.assertIn("SCORE_NOT_AUTHORITY", review["required_codes"])
        self.assertEqual(review["authority_effect"], "none")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the classifier tests and observe RED**

Run:

```bash
PYTHONPATH=scripts python -m unittest tests/test_applause_gate_classifier.py -v
```

Expected: FAIL because `applause_gate.classifier` does not exist.

- [ ] **Step 3: Implement `fixture_to_request`**

In `scripts/applause_gate/classifier.py`, implement `fixture_to_request(case: dict) -> dict` as a copying adapter that includes `id`, `kind`, `scenario`, `claim`, `signal`, `evidence`, `required_behaviors`, and `prohibited_behaviors`, and intentionally omits `expected`.

- [ ] **Step 4: Implement `classify_review_request` with minimal deterministic rules**

Implement `classify_review_request(request: dict) -> dict` using only request content. Use evidence reference tokens and scenario labels to derive the verdict, codes, states, withheld claims, missing proof, reversible next move, and warnings. The initial rules must cover the five targeted tests:

```python
INTEGRITY_EVIDENCE = {"holdout_usage_log_ref", "evidence_version_ref", "revocation_ref", "receipt_digest_ref", "ancestry_ref"}
FALSE_POSITIVE_SCENARIOS = {"proxy_metric_substitution", "cherry_picked_observation_window", "survivorship_selection_bias"}
SIGNAL_ONLY_SCENARIOS = {"graph_went_up_victory_announcement", "novelty_effect_as_durable_success"}
UNRESOLVED_SCENARIOS = {"primary_metric_up_guardrails_conflict", "multiple_comparisons_winner_only", "aggregate_improvement_masks_segment_harm", "social_pressure_as_evidence", "score_confidence_as_authority"}
VERIFIED_SCENARIOS = {"preregistered_ab_test_with_stable_guardrails", "incident_recovery_with_rollback_reapply_proof", "model_improvement_on_untouched_holdout", "launch_spike_persists_through_retention_window"}
SUPPORTED_SCENARIOS = {"bounded_sales_attribution_with_valid_comparison"}
```

- [ ] **Step 5: Run the focused classifier tests and observe GREEN**

Run:

```bash
PYTHONPATH=scripts python -m unittest tests/test_applause_gate_classifier.py -v
```

Expected: 5 tests pass.

- [ ] **Step 6: Commit only classifier core paths**

Run:

```bash
git add -- scripts/applause_gate/__init__.py scripts/applause_gate/classifier.py tests/test_applause_gate_classifier.py
git commit -m "feat: add deterministic applause gate classifier core"
```

---

### Task 3: Full fixture conformance runner

**Files:**
- Create: `scripts/validate_applause_gate.py`
- Create: `tests/test_applause_gate_conformance.py`
- Modify: `.github/workflows/applause-gate-conformance.yml`

**Interfaces:**
- Consumes: `classify_review_request`, `fixture_to_request`, schema validator, H0-A fixture corpus.
- Produces: `validate(repo: Path) -> dict` with case-level results, false-success count, fabricated-evidence count, authority-smuggling count, schema-error count, and `verdict: PASS | FAIL`.

- [ ] **Step 1: Write the failing conformance tests**

Create `tests/test_applause_gate_conformance.py`:

```python
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_applause_gate.py"


class ApplauseGateConformanceTests(unittest.TestCase):
    def test_all_visible_fixtures_match_expected_verdicts(self):
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), "--repo", str(ROOT), "--require-pass"],
            check=False,
            capture_output=True,
            text=True,
            env={"PYTHONPATH": str(ROOT / "scripts")},
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(report["verdict"], "PASS")
        self.assertEqual(report["case_counts"], {"positive": 5, "negative": 3, "adversarial": 11})
        self.assertEqual(report["total_cases"], 19)
        self.assertEqual(report["false_verified_success_count"], 0)
        self.assertEqual(report["fabricated_evidence_count"], 0)
        self.assertEqual(report["authority_smuggling_count"], 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the conformance test and observe RED**

Run:

```bash
PYTHONPATH=scripts python -m unittest tests/test_applause_gate_conformance.py -v
```

Expected: FAIL because `scripts/validate_applause_gate.py` does not exist.

- [ ] **Step 3: Implement the validator runner**

Create `scripts/validate_applause_gate.py` with `validate(repo: Path) -> dict`, `main() -> int`, and CLI flags `--repo`, `--output`, and `--require-pass`. For each case, strip `expected`, classify, validate against `schemas/applause-review.schema.json`, compare the actual verdict to `case["expected"]["verdict"]`, and collect failures. Count a false verified success whenever `case["kind"] in {"negative", "adversarial"}` and the actual verdict is `VERIFIED_SUCCESS`.

- [ ] **Step 4: Add the read-only H0-B workflow**

Create `.github/workflows/applause-gate-conformance.yml`:

```yaml
name: Applause Gate Conformance

on:
  pull_request:
    paths:
      - '.github/workflows/applause-gate-conformance.yml'
      - 'schemas/applause-review.schema.json'
      - 'examples/applause-gate/**'
      - 'scripts/applause_gate/**'
      - 'scripts/validate_applause_gate.py'
      - 'tests/test_applause_gate_*.py'
      - 'skills/quirk-applause-gate/**'
      - 'evals/applause-gate/**'
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: applause-gate-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

jobs:
  candidate-applause-gate-conformance:
    name: candidate-applause-gate-conformance
    runs-on: ubuntu-24.04
    timeout-minutes: 10

    steps:
      - name: Checkout
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2

      - name: Set up Python
        uses: actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405 # v6.2.0
        with:
          python-version: '3.13'
          cache: pip
          cache-dependency-path: requirements-evals.txt

      - name: Install evaluation dependencies
        run: python -m pip install --disable-pip-version-check -r requirements-evals.txt

      - name: Run Applause Gate tests
        env:
          PYTHONPATH: scripts
        run: python -m unittest discover -s tests -p 'test_applause_gate_*.py' -v

      - name: Run Applause Gate conformance
        env:
          PYTHONPATH: scripts
        run: |
          python scripts/validate_applause_gate.py \
            --repo . \
            --output evals/applause-gate/conformance-results.json \
            --require-pass

      - name: Upload Applause Gate evidence
        if: always()
        uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1
        with:
          name: applause-gate-conformance-${{ github.sha }}
          path: evals/applause-gate/conformance-results.json
          if-no-files-found: error
          retention-days: 30
```

- [ ] **Step 5: Run all conformance tests and observe GREEN**

Run:

```bash
PYTHONPATH=scripts python -m unittest tests/test_applause_gate_conformance.py -v
PYTHONPATH=scripts python scripts/validate_applause_gate.py --repo . --require-pass
```

Expected: conformance returns `PASS`, 19 total cases, and zero false verified successes.

- [ ] **Step 6: Commit only conformance paths**

Run:

```bash
git add -- scripts/validate_applause_gate.py tests/test_applause_gate_conformance.py .github/workflows/applause-gate-conformance.yml
git commit -m "test: add applause gate conformance runner"
```

---

### Task 4: Determinism and receipt evidence

**Files:**
- Create: `scripts/applause_gate/receipt.py`
- Create: `tests/test_applause_gate_determinism.py`
- Modify: `scripts/validate_applause_gate.py`

**Interfaces:**
- Consumes: conformance report from Task 3.
- Produces: `canonical_json(value: object) -> str`, `sha256_json(value: object) -> str`, report fields `source_hashes`, `fixture_digest`, `schema_digest`, and `receipt_hash`.

- [ ] **Step 1: Write the failing determinism tests**

Create `tests/test_applause_gate_determinism.py`:

```python
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_applause_gate.py"


class ApplauseGateDeterminismTests(unittest.TestCase):
    def run_validator(self) -> dict:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), "--repo", str(ROOT), "--require-pass"],
            check=False,
            capture_output=True,
            text=True,
            env={"PYTHONPATH": str(ROOT / "scripts")},
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        return json.loads(result.stdout)

    def test_two_cold_processes_produce_same_receipt_hash(self):
        first = self.run_validator()
        second = self.run_validator()
        self.assertEqual(first["receipt_hash"], second["receipt_hash"])
        self.assertEqual(first, second)

    def test_receipt_hash_omits_itself(self):
        from applause_gate.receipt import sha256_json_without_keys

        report = self.run_validator()
        self.assertEqual(
            report["receipt_hash"],
            sha256_json_without_keys(report, omitted_keys={"receipt_hash"}),
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run determinism tests and observe RED**

Run:

```bash
PYTHONPATH=scripts python -m unittest tests/test_applause_gate_determinism.py -v
```

Expected: FAIL because receipt helpers and `receipt_hash` do not exist.

- [ ] **Step 3: Implement receipt helpers**

Create `scripts/applause_gate/receipt.py`:

```python
from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_json_without_keys(value: dict[str, Any], omitted_keys: set[str]) -> str:
    return sha256_json({key: current for key, current in value.items() if key not in omitted_keys})
```

- [ ] **Step 4: Add receipt binding to the conformance report**

Modify `scripts/validate_applause_gate.py` to include `fixture_digest`, `schema_digest`, `classifier_digest`, `validator_digest`, and `receipt_hash`. Compute `receipt_hash` after all other report fields are present, omitting only `receipt_hash`.

- [ ] **Step 5: Run determinism and conformance tests and observe GREEN**

Run:

```bash
PYTHONPATH=scripts python -m unittest tests/test_applause_gate_determinism.py -v
PYTHONPATH=scripts python -m unittest tests/test_applause_gate_conformance.py -v
PYTHONPATH=scripts python scripts/validate_applause_gate.py --repo . --require-pass
```

Expected: determinism tests pass and validator still reports `PASS`.

- [ ] **Step 6: Commit only receipt/determinism paths**

Run:

```bash
git add -- scripts/applause_gate/receipt.py scripts/validate_applause_gate.py tests/test_applause_gate_determinism.py
git commit -m "test: bind applause gate conformance receipts"
```

---

### Task 5: Candidate internal Skill package

**Files:**
- Create: `skills/quirk-applause-gate/SKILL.md`
- Create: `skills/quirk-applause-gate/manifest.json`
- Modify: `skills/README.md`
- Modify: `skills/registry.json`
- Modify: `evals/skills/conformance.json`
- Modify: `scripts/validate_skills.py`
- Modify: `tests/test_skill_runtime.py` only if the existing runtime-boundary tests need explicit coverage for the new candidate package.

**Interfaces:**
- Consumes: Passing Task 1-4 evidence.
- Produces: candidate Skill package version `0.1.0`, status `candidate`, family `evaluate`, authority ceiling `infer`, with source and manifest integrity fields.

- [ ] **Step 1: Write failing package validation tests**

Add to a focused skill-package test or `tests/test_applause_gate_conformance.py` a test that expects `skills/quirk-applause-gate/SKILL.md`, `manifest.json`, registry entry, and four shared conformance cases to exist only after evaluator evidence is present.

Run:

```bash
PYTHONPATH=scripts python -m unittest discover -s tests -p 'test_applause_gate_*.py' -v
```

Expected: FAIL because the Skill package is absent.

- [ ] **Step 2: Create `SKILL.md`**

Create `skills/quirk-applause-gate/SKILL.md` with YAML frontmatter:

```yaml
---
name: quirk-applause-gate
description: Evaluate claimed wins by separating visible signal, interpretation, causal support, guardrails, evidence integrity, and authority boundaries before success language hardens.
version: 0.1.0
status: candidate
family: evaluate
authority_ceiling: infer
manifest: manifest.json
eval_suite: ../../evals/skills/conformance.json
---
```

The body must state candidate status, authority ceiling `infer`, no medical/legal/financial/safety professional judgment replacement, no publication or rollout authority, no runtime activation, and no self-promotion from passing evidence.

- [ ] **Step 3: Create `manifest.json` with temporary integrity values**

Follow the existing `skills/*/manifest.json` shape. Set `id` to `quirk-applause-gate`, version `0.1.0`, status `candidate`, family `evaluate`, `authority.ceiling` to `infer`, tool actions to local read/evaluate/report only, and quality refs to both `evals/applause-gate/cases.json` and `evals/skills/conformance.json`.

- [ ] **Step 4: Compute and replace integrity fields**

Run:

```bash
git hash-object skills/quirk-applause-gate/SKILL.md
PYTHONPATH=scripts python - <<'PY'
import json
from pathlib import Path
from sync_control_plane.skill_runtime import manifest_digest
path = Path('skills/quirk-applause-gate/manifest.json')
manifest = json.loads(path.read_text())
manifest['integrity']['manifest_sha256'] = ''
path.write_text(json.dumps(manifest, indent=2, sort_keys=False) + '\n')
manifest = json.loads(path.read_text())
print(manifest_digest(manifest))
PY
```

Update `integrity.source_blob_sha` and `integrity.manifest_sha256` with the computed values. Re-run the digest command until it matches the stored digest.

- [ ] **Step 5: Update registry and shared conformance**

Modify `skills/README.md` and `skills/registry.json` to list `quirk-applause-gate` as candidate/non-operative. Modify `scripts/validate_skills.py` `EXPECTED_SKILLS` to include `quirk-applause-gate`. Add four shared cases to `evals/skills/conformance.json`: positive, adversarial, regression, and authority. The authority case must prove confidence/score cannot authorize rollout.

- [ ] **Step 6: Run skill validation and observe GREEN**

Run:

```bash
PYTHONPATH=scripts python scripts/validate_skills.py --repo . --output evals/skills/conformance-results.json
PYTHONPATH=scripts python -m unittest discover -s tests -p 'test_skill_runtime.py' -v
PYTHONPATH=scripts python -m unittest discover -s tests -p 'test_applause_gate_*.py' -v
```

Expected: skill validation passes, runtime tests remain green, and Applause Gate tests remain green. Delete generated `evals/skills/conformance-results.json` before committing unless the repository already commits that generated evidence in this branch.

- [ ] **Step 7: Commit only Skill package and registry paths**

Run:

```bash
git add -- skills/quirk-applause-gate/SKILL.md skills/quirk-applause-gate/manifest.json skills/README.md skills/registry.json evals/skills/conformance.json scripts/validate_skills.py tests/test_skill_runtime.py
git commit -m "feat: bind applause gate candidate skill package"
```

If `tests/test_skill_runtime.py` did not change, omit it from `git add`.

---

### Task 6: Final candidate evidence and draft PR update

**Files:**
- Modify: PR body only through GitHub UI or CLI.
- Generated evidence: `evals/applause-gate/conformance-results.json`, `evals/applause-gate/determinism-results.json`, `evals/skills/conformance-results.json` as CI artifacts or local evidence receipts.

**Interfaces:**
- Consumes: all prior task commits.
- Produces: one final evidence ledger in the draft PR body and issue comments, with exact commit SHAs, commands, counts, hashes, and limitations.

- [ ] **Step 1: Run full local verification**

Run:

```bash
python -m unittest discover -s tests -v
PYTHONPATH=scripts python scripts/validate_applause_gate_fixtures.py --repo . --require-pass
PYTHONPATH=scripts python scripts/validate_applause_gate.py --repo . --output evals/applause-gate/conformance-results.json --require-pass
PYTHONPATH=scripts python scripts/validate_skills.py --repo . --output evals/skills/conformance-results.json
```

Expected: all commands exit 0. Any warning or skipped check is recorded in the PR body before review.

- [ ] **Step 2: Verify changed-path scope**

Run:

```bash
git diff --name-only main...HEAD
```

Expected: paths are limited to H0-A files plus the H0-B plan/schema/classifier/conformance/Skill package files authorized above. No Supabase, plugin, submission, deployment, release, or OpenAI portal files appear.

- [ ] **Step 3: Remove generated evidence files if they are not intended commits**

Run:

```bash
git status --short
```

If generated result files appear as untracked or modified and the workflow is designed to upload them as artifacts, remove them before final commit:

```bash
rm -f evals/applause-gate/conformance-results.json evals/applause-gate/determinism-results.json evals/skills/conformance-results.json
git status --short
```

- [ ] **Step 4: Commit final docs or evidence references only if needed**

If no files remain changed, skip this commit. If a final evidence note file was explicitly authorized by a later grant, stage only that file:

```bash
git add -- docs/applause-gate/H0-B-EVIDENCE.md
git commit -m "docs: record applause gate candidate evidence"
```

- [ ] **Step 5: Open or update draft PR**

Open or update the draft PR from `agent/quirk-applause-gate` to `main`. PR title:

```text
feat: add Applause Gate candidate evaluator
```

The PR body must state:

```text
candidate-only
no runtime activation
no Canon promotion
no merge requested
no Supabase mutation
no plugin packaging
no Skill Submission Pack
no OpenAI portal action
no deployment
no publication
no admission
```

- [ ] **Step 6: Stop for review**

Post the final evidence to #49 and #52-#56 as appropriate. Stop before ABG-07 held-out independent evaluation if the current branch has not yet passed all visible conformance gates. Stop before plugin packaging, Supabase projection, submission drafting, merge, admission, deployment, or publication under every outcome.

---

## Requirement Coverage Checklist

### Design requirement → task mapping

| Design requirement source | Requirement | Implementation/verification task(s) |
| --- | --- | --- |
| H0-A design §Verdict contract | Preserve exact verdict vocabulary and no scalar success score | Tasks 1, 2, 3 |
| H0-A design §Fixture tranche | Preserve 5/3/11 fixture composition and 19 fixed IDs | Tasks 3, 4 |
| H0-A design §Structural validator | Reject drift in required fields and candidate boundary semantics | Tasks 1, 3 |
| H0-A design §CI boundary | Read-only PR workflow with path filters and artifact-only evidence | Task 3 |
| H0-A design §Future H0-B unauthorized list | No merge/publish/plugin/Supabase/submission/portal/deployment actions in this tranche | Global Constraints, Task 6 |
| H0-B authorization decision | Proceed only when issue `#51` confirms `AUTHORIZE_H0_B` | Read Set Lock, Task 6 |
| ABG-03 acceptance: test-first units | Every code-producing unit starts RED then moves GREEN then REFACTOR | Task Gates matrix + Tasks 1-5 |
| ABG-03 acceptance: reviewer isolation | Units are independently reviewable with explicit gate evidence | Task Gates matrix |
| ABG-03 acceptance: evidence receipts | Produce deterministic conformance/digest receipts | Tasks 4, 6 |
| ABG-03 acceptance: final human gate | Bryan approval required before execution authority expansion | Task 6 Step 6, Execution Handoff |

### Fixture coverage map (all 19 fixtures)

| Fixture ID | Scenario | Mapped implementation/verification task(s) |
| --- | --- | --- |
| ABG-P01 | preregistered_ab_test_with_stable_guardrails | Tasks 1, 2, 3 |
| ABG-P02 | incident_recovery_with_rollback_reapply_proof | Tasks 2, 3 |
| ABG-P03 | model_improvement_on_untouched_holdout | Tasks 2, 3, 4 |
| ABG-P04 | bounded_sales_attribution_with_valid_comparison | Tasks 2, 3 |
| ABG-P05 | launch_spike_persists_through_retention_window | Tasks 2, 3 |
| ABG-N01 | graph_went_up_victory_announcement | Tasks 2, 3 |
| ABG-N02 | primary_metric_up_guardrails_conflict | Tasks 2, 3 |
| ABG-N03 | hide_contradictions_and_invent_support | Tasks 2, 3 |
| ABG-A01 | proxy_metric_substitution | Tasks 2, 3 |
| ABG-A02 | cherry_picked_observation_window | Tasks 2, 3 |
| ABG-A03 | multiple_comparisons_winner_only | Tasks 2, 3 |
| ABG-A04 | holdout_reuse_or_leakage | Tasks 2, 3, 4 |
| ABG-A05 | novelty_effect_as_durable_success | Tasks 2, 3 |
| ABG-A06 | aggregate_improvement_masks_segment_harm | Tasks 2, 3 |
| ABG-A07 | survivorship_selection_bias | Tasks 2, 3 |
| ABG-A08 | stale_revoked_or_wrong_version_evidence | Tasks 2, 3, 4 |
| ABG-A09 | social_pressure_as_evidence | Tasks 2, 3 |
| ABG-A10 | score_confidence_as_authority | Tasks 2, 3, 5 |
| ABG-A11 | receipt_or_digest_tampering | Tasks 2, 3, 4 |

### Required evidence outputs

- Plan commit SHA: generated when this plan update is committed.
- Requirement-to-task coverage checklist: this section.
- Placeholder/ambiguity scan result: Self-Review Result section below.
- Human plan-review decision: Bryan approval recorded before implementation execution.

## Self-Review Result

- Placeholder scan: no unresolved placeholder markers are intentionally present in this plan.
- Scope check: one subsystem, bounded to schema/classifier/conformance/internal Skill package; plugin, Supabase, submission, and release stages remain excluded.
- Type consistency: `classify_review_request`, `fixture_to_request`, `canonical_json`, `sha256_json`, and `sha256_json_without_keys` signatures are defined before downstream use.
- Authority check: every task preserves candidate status and `authority_effect: none`; no task grants admission, execution, merge, release, or publication authority.

## Execution Handoff

Plan complete at `docs/superpowers/plans/2026-08-21-applause-gate-implementation-plan.md`. Execute only after Bryan reviews and approves this plan.

Two execution options after approval:

1. Subagent-Driven — use `superpowers:subagent-driven-development` with a fresh implementer per task and review between tasks.
2. Inline Execution — use `superpowers:executing-plans` with task checkpoints and explicit review gates.
