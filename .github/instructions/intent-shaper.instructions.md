---
applyTo: "schemas/personalization-plan.schema.json,scripts/intent_shaper/**,scripts/validate_intent_shaper.py,evals/intent-shaper/**,tests/test_intent_shaper.py,schemas/qis-evidence-envelope.schema.json,scripts/validate_qis_harness.py,evals/qis-agent-harness/**,tests/test_qis_harness.py,.github/workflows/qis-agent-harness.yml"
---

# Reuse the existing Intent Shaper vocabulary: `candidate`, `approval_ref`, `persona_hand`, `platform_affects`, `task_affordances`, `evaluation`, `learning`, `evidence_refs`, and `receipt_hash`.
# Change the smallest coherent slice across schema, evaluator, fixtures, tests, evidence, and workflow together.
# Fail closed on unexpected fields, missing evidence files, unknown enum values, non-zero failures, or ancestry mismatches.
# Keep comparisons exact: explicit instructions outrank saved preference evidence; negative constraints outrank positive styling; critical failures block `PASS`.
# Use only these commands for drift-sensitive verification: `python -m unittest tests.test_intent_shaper tests.test_qis_harness -v`, `python scripts/validate_intent_shaper.py --repo . --output evals/intent-shaper/conformance-results.json`, and `python scripts/validate_qis_harness.py --repo . --receipt <receipt-path>`.
