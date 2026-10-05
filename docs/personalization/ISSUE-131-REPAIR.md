# Intent Shaper issue #131 repair

Scope: the three P1 and seven P2 findings in [issue #131](https://github.com/Quirk-Systems/quirk-os/issues/131). PR #134 was already merged with no file changes when this repair resumed. Its original head `2c9e72102fa86d029a75e0f71588b2278424a7b4` is a descendant of required candidate `f5effa3d6da3e5879e10007492aeff39a1c643be`; the reported ancestry blocker was incorrect. The implementation extends main `ec10bcc69c1a91d7c9bc4818e2378ea4df2368fb`, which contains both commits.

## Finding dispositions

| Finding | Enforcement and regression |
| --- | --- |
| P1 skill registration | Preserve the existing draft-source carveout and twelve-package manifest registry. Validate the actual draft contract status; regress unknown sources, draft manifests, active declarations, and registry injection. No runtime registration or admission is granted. |
| P2 purpose-scoped precedence | Preserve the existing schema source enum and executable rank. Check current > purpose setting > saved regardless of confidence. |
| P2 validity start | Filter before ranking in both modes; check future/expired current evidence and inclusive interval endpoints. Used plan preferences must be active at `created_at`. |
| P2 current conflicts | Preserve source-tier conflict detection before confidence. Apply it to disabled selection and reject conflicting off-mode projections before any protected read. |
| P2 exact lists | Preserve exact ordered list matching. Test omitted selected refs, traits, affordances, and nested projection entries. |
| P2 timestamp format | Preserve `FormatChecker` in the combined plan validator. Check malformed, offsetless, impossible-date, lowercase RFC 3339, offset, and nullable validity values. |
| P1 personalization off | Preserve schema prohibitions on persona/profile/persisted evidence and incompatible settings. Scope/time/conflict filtering now also governs current-request projections, including duplicate-ref leakage attempts. |
| P2 generated UI safeguards | Preserve required plain-text fallback, component bindings/actions, reconstruction, accessibility, and freshness contracts. Regress missing safeguards; the existing eleven gate fixtures remain non-authorizing. |
| P2 persona normalization | Share aggregate weight validation between Persona Hand evaluation and complete plan validation. Require total 1.0 within absolute tolerance `1e-9` for enabled hands; reject zero, excess, and deficient totals. Off mode retains the schema-enforced empty hand. |
| P1 explicit-current purpose | Apply the same active-purpose/global eligibility filter to every preference source before precedence. Validate used plan preference scopes as well. |

## Decision and proof boundary

Use the existing schema/evaluator/fixture vocabulary and candidate ceiling. Keep already landed fixes and the unadmitted draft carveout; expanding the runtime registry would add unrelated admission work. Eight new deterministic fixtures (`QIS-R12` through `QIS-R19`) extend the suite from 36 to 44. The corrected valid-provenance receipt remains synthetic test data, with its original counts and limitations preserved.

The complete plan validator combines schema format checks and relational policy checks; JSON Schema alone cannot sum weights or compare a preference interval with the plan timestamp. `created_at` defines eligibility for a captured plan. A later execution must reevaluate freshness rather than treating historical validation as perpetual authorization. No cross-scope override is introduced.

Run:

```bash
python -m unittest tests.test_intent_shaper tests.test_qis_harness -v
python scripts/validate_intent_shaper.py --repo . --output evals/intent-shaper/conformance-results.json
python scripts/validate_qis_harness.py --repo . --receipt evals/qis-agent-harness/receipt.valid-provenance.json
python -m unittest discover -s tests -p 'test_*.py' -v
python scripts/validate_skills.py --repo . --output /tmp/issue131-skills.json
python scripts/validate_golden_pack.py --metrics-output /tmp/issue131-golden-metrics.json
```

The immutable `.quirk/evidence` receipt binds the implementation subject, exact commands, and material hashes. Hosted validation must be checked against the successor PR head, with Evidence Binding using the pinned policy at `6136fa5fa77116abfbc103c822d9d244a0e870b3`. Passing checks support candidate conformance only; human accessibility observations, runtime admission, deployment, and merging remain outside this repair.

Rollback: revert the implementation and its corresponding evidence commit together. Resume: check the current PR head, issue scope, ancestry, and existing evidence before editing. Next move: review the bounded successor without merging it.
