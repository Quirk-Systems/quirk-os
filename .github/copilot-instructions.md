# Quirk OS is contract-first: keep Canonical schemas, Runtime evaluators, Projections, and Evidence separate.
# For this stack, child admission work starts from `agent/quirk-intent-shaper` at `f5effa3d6da3e5879e10007492aeff39a1c643be` or a traceable descendant.
# Install eval deps with `python -m pip install --disable-pip-version-check -r requirements-evals.txt`.
# Run focused checks with `python -m unittest tests.test_intent_shaper tests.test_qis_harness -v` and `python scripts/validate_intent_shaper.py --repo . --output evals/intent-shaper/conformance-results.json`.
# Validate harness evidence with `python scripts/validate_qis_harness.py --repo . --receipt <receipt-path>`.
# Bryan is the only admission authority; capability never grants merge, activation, deployment, persistence, Canon promotion, or self-approval authority.
# Every consequential transform owes a receipt with exact commands, counts, failures, limitations, SHAs, and canonical `receipt_hash`.
# Treat unexpected fields, missing evidence, unknown enum values, and failed safety comparisons as hard failures.
# Keep PR-triggered workflows read-only, path-filtered, `if: always()` on artifact upload, and free of secrets, schedules, deployments, external writes, and `pull_request_target`.
# Stop if the branch ancestry, issue target, required evidence paths, or actual repo commands do not match these instructions.
