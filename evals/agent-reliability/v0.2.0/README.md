# Agent assurance v0.2.0 — candidate extension

Owner: Quirk OS evaluation subsystem (`Quirk-Systems/quirk-os`).
Base: `03f70e1a790bac09294fe0f31a3c5f0d0fb4418e`.
Decision: **Constrain** to local evaluation. No executor, grants, publication,
database mutation, model invocation, or Canon promotion is introduced.

## What you can do

From the repository root with Python 3.11+:

```sh
python -m unittest discover -s tests -p test_agent_reliability.py -q
python -m unittest discover -s tests -p test_agent_assurance.py -q
python scripts/validate_agent_assurance.py
```

The last command audits the actual existing authority and completion graders,
then checks disclosure and task-pair fixtures. Exit 0 means these checks passed;
1 means a check failed; 2 means invalid inputs. Reports include canonical JSON
SHA-256 fixture identities and explicitly say `NO_LIVE_MODEL_OBSERVATIONS`.
The existing v0.1.2 CLI, fixture bytes and semantics remain unchanged.

## Three recommendations implemented

1. **Test the grader:** `audit_grader(callback, controls)` runs each known-answer
   control twice in each forward/reverse/forward traversal. It detects wrong
   answers, exceptions, non-boolean answers, unstable verdicts, and changed JSON
   arguments. It deep-copies inputs, and reports control identities and failures.
   CI exercises this against the existing 24 authority and four completion cases.
   Six independent parity controls exercise four deliberately defective graders.
2. **Check content as well as destination:** `disclosure(candidate, policy)`
   requires exact object, destination, purpose, payload digest and permitted
   classification. The policy is a separate caller-supplied object. The paired
   public/confidential fixtures share the same allowed destination; only the
   public payload is eligible. Payload edits after review and changed purposes
   also fail. No secret contents are included: fixtures are synthetic.
3. **Keep adversarial tests fair:** `task_pair(a, b, reviews)` requires identical
   goals, tools, permissions, constraints and initial state, with distinct
   cooperative/impatient registers. Both exact variants need a valid review
   assertion from someone other than the producer. Changed tasks, invalid reviews,
   self-review, and stale review hashes cannot qualify as matched agent tests.
   Rejected pairs are invalid tests, not agent failures.

## Limits that matter

These are structural checks and synthetic tests, not live-model results or
production enforcement. The grader audit is not a sandbox: callbacks must be
trusted local code. It cannot detect transient restored mutations, external
effects, or all hidden state. It does not prove statistical judge reliability.
Disclosure labels/policy origin and review identities are assertions; a runtime
adapter must authenticate them. Hashes bind bytes, not truth. This is not a
natural-language secret detector. Task equality does not prove a task is possible;
the independent semantic review remains necessary. No genuine blinded review,
agent improvement, lower leakage rate, independent usability or deployment safety
is claimed. Voice drift, tool behavior, goals and permissions remain distinct.

## Decisions, sources and next evidence

Extend the existing Python harness rather than create a second authority service.
Keep v0.1.2 as a frozen comparison baseline and make this an additive v0.2.0
assurance extension. The CI workflow runs both; neither can issue permission.

Research leads from the October 16 brief:
- https://arxiv.org/abs/2610.16067v1 — evaluator integrity
- https://arxiv.org/abs/2610.16005v1 — purpose/content disclosure boundary
- https://arxiv.org/abs/2610.16155v1 — task-integrity constrained adversarial testing

These identify inspiration; this implementation does not independently reproduce
the papers or import their reported numerical results as Quirk evidence.

Next: independently review the code, then collect six genuine cooperative/impatient
pairs with frozen model/configuration, goals/tools/grants and blinded task-validity
reviews. Measure invalid-test rate separately from valid-task agent failure rate.
Live calls or external effects require their own approved scope and credentials;
this implementation request does not supply those. Stop on credential exposure,
external effects, changed baselines or unverifiable evidence. Preserve failures.

Rollback: revert this additive change and its CI entries; v0.1.2 is untouched.
Capability deposit: reusable local grader audit and two inert contract checkers.
Author testing is not independent release review. No admission to production.

## Source-grounded task candidates

The additive [real-task pack](real-tasks/README.md) contains six repository tasks
with executable reference queries, immutable source identities, two exact prompts
per task, and an unfilled independent-review template. Run
`python scripts/validate_agent_real_tasks.py check` for construction checks.
It intentionally reports zero eligible asserted pairs until actual independent
reviews are supplied. It does not replace or relabel the synthetic fixtures above.
