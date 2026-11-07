# Intent Shaper Admission

Use this loop only for candidate Intent Shaper admission work.

## Canonical objects
`schemas/personalization-plan.schema.json`, `schemas/qis-evidence-envelope.schema.json`

## Runtime objects
`scripts/intent_shaper/policy.py`, `scripts/validate_intent_shaper.py`, `scripts/validate_qis_harness.py`

## Projections
`.github/workflows/qis-agent-harness.yml`

## Evidence
`evals/intent-shaper/cases.json`, `evals/intent-shaper/conformance-results.json`, `evals/qis-agent-harness/*.json`, `tests/test_intent_shaper.py`, `tests/test_qis_harness.py`

## Admission loop
1. `python -m pip install --disable-pip-version-check -r requirements-evals.txt`
2. `python -m unittest tests.test_intent_shaper tests.test_qis_harness -v`
3. `python scripts/validate_intent_shaper.py --repo . --output evals/intent-shaper/conformance-results.json`
4. `python scripts/validate_qis_harness.py --repo . --receipt <receipt-path>`

Stop if ancestry no longer traces to `agent/quirk-intent-shaper` at `f5effa3d6da3e5879e10007492aeff39a1c643be`, if any evidence file is missing, or if any step suggests activation, deployment, Canon promotion, or self-approval.
