# Verification repair routes — 2026-10-08

## 2026-10-09 — Step decomposition and bounded observation loop

Routes now decompose into dependency-ordered inspect, propose and verify steps,
each carrying its completion proof and gate. A loop reevaluates supplied cases
against frozen goal obligations/requested authority. It preserves newly exposed
failures, distinguishes structural blocker reduction from tradeoffs/regressions,
stops on authority/contract failures, and bounds observations to three rounds.
Two successive unchanged comparisons stop for no progress. Candidate eligibility
stops at review; it never becomes live completion. Attempts to shrink goal
obligations, repeat a mutation, exceed budget or continue after a stop are rejected.

Run `python scripts/route_agent_verification.py --loop /absolute/path/to/loop.json`.
Input has exactly `goal_id`, integer `round_limit` (1–3), and `observations`.
Each observation has exactly `mutation_id` and `evaluation`; evaluation uses
the original `{kind, case}` contract. Outputs retain normalized blockers,
observation/mutation digests, step proposals and stop reason. Caller-provided
observations and mutation IDs are assertions, not authenticated causal evidence.
No source text or mutation IDs are echoed; dependency/request bindings are hashed.

Executed synthetic examples prove that repairing a failed obligation reduces
blockers while leaving user benefit `NOT_MEASURED`; a second example refreshes
stale evidence but exposes self-sign-off, preserving the surprise as `TRADEOFF`
and stopping for `REGRESSION_REVIEW`. These demonstrate loop logic, not measured
real-world benefit. The deterministic planner collects no observations itself
and executes no repair. It is a candidate component for a coordinator, not an
autonomous deployed engine.

Ten new loop test methods plus the prior 67 focused tests pass locally (77
total), in a partial checkout pinned to PR head
`7de7063b780cabc579b15cac9d530fa4eec28e93` plus this change. Hosted full-repository
checks and independent review are separate evidence. Rollback the added loop
module/tests and the CLI flag to recover the previous diagnostic interface.

Status: locally tested candidate; admission decision **Constrain** to an inert
diagnostic tool. Independent usability, live provenance and system-wide runtime
integration have not been established.

## Changelog

Agent reliability failures can now produce a focused verification question,
proposed repair action, resume proof and next gate. The new adapter invokes the
existing v0.1.2 authority/completion evaluators, preserves their candidate-only
verdicts, groups related failures and puts authority reconciliation before
dependent evidence work. It creates no executor or new authority source.

## Use

Python 3.11+, standard library only, from the repository root:

```sh
python -m unittest discover -s tests -p 'test_*reliability*.py' -q
python -m unittest discover -s tests -p 'test_verification_routes.py' -q
python scripts/route_agent_verification.py /absolute/path/to/case.json
```

The input is exactly `{ "kind": "authority" | "completion", "case": ... }`.
`case` uses the existing evaluator's contract documented in
`evals/agent-reliability/v0.1.2/README.md` and its `fixtures.json`. To construct an
executable example without private context:

```sh
python -c 'import json; from pathlib import Path; p=json.loads(Path("evals/agent-reliability/v0.1.2/fixtures.json").read_text()); f=next(f for f in p["completion"] if not f["expected"]); Path("/tmp/quirk-verification-case.json").write_text(json.dumps({"kind":"completion","case":f["case"]}))'
python scripts/route_agent_verification.py /tmp/quirk-verification-case.json
```

Exit 0 means `CANDIDATE_ONLY`, 1 means `BLOCKED`, and 2 means `INVALID_INPUT`.
Invalid JSON, duplicate fields, nonfinite numbers and input over 1 MiB return a
generic error without echoing parser fragments. Invalid envelopes cannot import
an approval or verdict. Output omits source-case text and provider receipt
payloads. This is minimization, not a general credential detector.

Each proposed route exposes `question`, `proposed_action`, `resume_proof` and
`next_gate`. `next_route` selects the first prerequisite to investigate; all
other blockers remain visible. Actions are prose proposals with `executable=false`.
They are never arbitrary commands. Unknown failure codes route to manual diagnosis
without echoing unrecognized text. A human question is needed only when a real
decision remains missing after reconciling existing authority.

## Evidence and limits

Baseline: the existing evaluator returns candidate status and reason codes.
This change preserves that behavior and adds repair guidance. All 28 frozen
authority/completion fixtures retain their expected verdicts; no unsupported
completion is rescued by the router. Nine new test methods cover fixture parity,
prerequisite ordering, deduplication, unmapped failures, imported approval,
source-text injection, malformed envelopes, changed dependencies and CLI failures.
Together with the 58 existing reliability tests, 67 focused tests pass locally.
These are synthetic/contract tests in a partial checkout of main
`03f70e1a790bac09294fe0f31a3c5f0d0fb4418e`, not a full repository test run.

No usability lift, model-quality improvement, authenticated input provenance,
independent review, cold handoff, production safety or automatic root-cause repair
is claimed. The inherited evaluator checks asserted records; a validator label
does not prove its origin. This tool does not authenticate or execute grants,
perform provider reads, dispatch effects, retry actions or mark live work complete.

## Decision and next move

Chosen: an additive deterministic adapter around existing checks. Rejected:
duplicating the evaluator or constructing another model-powered scoring system.
Object: candidate diagnostic tool, owned by Quirk OS; input is an evaluation case,
output is an inert repair proposal; permission and activation effect are none.
Reusable deposit: failure-to-question/action/proof mapping, with tests. Changes
to evaluator reasons invalidate mapping coverage and require another run.

Next move: independently review route usefulness against one real failed run,
then integrate the adapter at a named coordinator boundary under that boundary's
contract. Do not describe this draft as system-wide enforcement. Rollback: remove
the additive adapter, CLI, tests and this changelog; original evaluators are unchanged.

Sources: current calibration design `Quirk-Prompt-Calibration-Design.md`, read
version 1 on 2026-10-08 (implementation stages remain separate); existing Quirk OS
agent reliability pack at the pinned base above. This repair adapter implements
neither the calibration compiler nor its live GitHub/Supabase coordinators.

