# ABG-08 disposition: `REVISE_SKILL`

The frozen `quirk-applause-gate@0.1.0` candidate must not be packaged. The evaluation changed no candidate, admission, or runtime state.

## Findings

### Structural

- Draft predecessor evidence in PR #94 records `PASS_CANDIDATE_EVIDENCE` against evaluated commit `73a3d73f6f45f44918bd35ed8a02aa553131650b`, but the dependency PR remains draft and has no review or check-run evidence.
- Plugin Eval reports non-standard Codex frontmatter keys and a weak trigger description.
- The manifest names an `applause_gate` tool without an executable mapping from the Skill package to the Python classifier.

### Budget-related

- **Estimated, not measured:** 49 trigger tokens, 669 invoke tokens, 1,149 deferred tokens, and 1,867 total tokens.
- Plugin Eval classifies invoke and deferred cost as heavy.
- No observed token sample exists, so no measured budget conclusion is available.

### Code-related

- The classifier maps exact visible fixture scenario names; an unknown realistic scenario defaults to `UNRESOLVED`.
- Manifest inputs (`claim_context`, `evidence_refs`, `candidate_ref`) do not directly match the classifier request fields.
- The deterministic visible-case metric pack passes false-success, abstention, alternative-hypothesis, version-binding, contradiction, guardrail, schema, fabricated-evidence, and authority-smuggling checks. This is conformance evidence, not natural-language generalization evidence.

### Benchmark-observed

- Three public scenarios cover dashboard-only celebration pressure, conflicting guardrails, and score-as-authority. Their strengthened executable verifier checks schema, expected non-success verdicts, evidence preservation, contradictions, and authority behavior. No sealed held-out prompt was used.
- Current Plugin Eval rejects simulated `--dry-run`; the inspected config is the preview evidence.
- Codex CLI `0.154.0` reported `Not logged in`. The real first scenario remained incomplete for more than five minutes and was terminated.
- Zero scenarios completed, zero usage samples were emitted, and no Plugin Eval benchmark result was written.
- The strengthened verifier configuration was created after review and remains unexecuted because the same authentication blocker persists.

## Fix first

1. Complete and independently validate #56 / PR #94, then bind its final `PASS_CANDIDATE_EVIDENCE` receipt.
2. Provide an authenticated Codex runner and rerun all three benchmark scenarios to produce measured JSONL usage and a complete Plugin Eval result.
3. Bind the Skill package to an executable classifier interface whose inputs match the manifest contract.
4. Replace exact fixture-name lookup with evidence-driven behavior that can be benchmarked on realistic, non-held-out language.
5. Decide whether Codex compatibility justifies revising the trigger description/frontmatter and reducing estimated invoke/deferred cost.

## Unresolved release blockers

- `pc-observed-token-usage`: failed; measured sample count is zero.
- Live natural-language routing, output quality, and authority behavior were not observed.
- The draft predecessor verdict has not completed review/check validation.

Disposition: `REVISE_SKILL`. Packaging, admission, runtime activation, rollout, and publication remain unauthorized.
