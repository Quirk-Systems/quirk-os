# Quirk Distinctions Workflow v0.1

Date: 2026-10-03
Status: Repository review candidate; manual procedure authorized by Bryan on 2026-10-03; effectiveness unmeasured.
Source: Bryan's distinctions drill and instruction, “Apply Workflow Changes as Recommended.”
Implementation scope: reusable manual checklist and receipt. No runtime enforcement or systemwide installation is claimed.

## Use on the next bounded task

1. **Define the work.** Name the object, desired result, source evidence, and allowed scope. Preserve corrections verbatim; separate them from inferred preferences.
2. **Inspect the relevant distinctions.** Use the table below where it affects a decision. Do not build extra machinery merely to fill every category.
3. **Check structure and behavior separately.** Record schema results and exactly what was checked. Check applicable behavioral obligations before execution, including grant validity, scope, and required authority. A structural pass cannot substitute for an unchecked behavioral condition.
4. **Select one bounded move.** State the input, action, stop condition, expected evidence, and existing authorization. If scope expands, prepare the proposal and obtain the needed decision before the expanded action.
5. **Execute and compare.** Preserve the original, produce the candidate, record actual results and human judgment separately. Unknown results stay unknown.
6. **Carry forward narrowly.** Keep, mutate, or drop based on the evidence. Record the scope in which reuse is supported. Reuse does not manufacture permission for future actions.

## Distinctions that change decisions

| Distinction | Working meaning | Workflow check |
| --- | --- | --- |
| Ontology | Kinds of things and meaningful relationships | Are receipt, candidate, preference, and grant distinct objects? |
| Taxonomy | Classification | Are labels applied consistently without changing an object's authority? |
| Topology | Connection structure | Can an unintended connection bypass a dependency or gate? |
| Type | Kind of value | Is this the expected kind of object? |
| Schema | Record constraints | What structure and constraints actually passed validation? |
| Contract | Behavioral obligations | Were required preconditions and effects checked at the relevant boundary? |
| Capability | Ability to achieve an outcome | Is this merely described, available here, or demonstrated? |
| Skill | Reusable procedure | Is the procedure appropriate to this input and scope? |
| Tool | Callable operation | What inputs, outputs, and side effects does this call have? |
| Agent | System choosing and executing steps toward a goal | What bounds its choices and execution? |

Schema and contract can overlap: a schema may encode some contract constraints. Record coverage instead of assuming complete separation or complete equivalence.

## Data to Ways

| Stage | Required description | Reveal-timing scenario |
| --- | --- | --- |
| Data | Observation with provenance | “Keep the reveal until the last bar.” |
| Graph | Explicit connections | Correction linked to the track, passage, and candidate preference |
| Maps | Useful view of connections | Where setup and reveal occur within this track |
| Routes | Possible paths to an outcome | Reorder the reveal or rewrite the setup |
| Moves | Bounded actions | Revise one passage and compare with the original |
| Ways | Practice with evidence supporting reuse in a stated scope | Reveal check remains a candidate beyond this track |

This is a working interpretation from the drill, not a claim of Canon admission. Moving through these stages does not automatically increase evidence, permission, or generality.

## First-run application and evidence boundary

The drill's reveal-timing example is illustrative. The source drill did not include the lyric passage needed to perform an actual revision. The checklist is ready; a lyric revision and comparison have not been performed.

When a real passage is available: preserve the original, create one last-bar-reveal revision, ask Bryan to compare, and record his actual judgment. Do not infer universal preference or approval from schema acceptance.

For the next real task, time preparation, review, and correction separately; record rework and unresolved distinction errors. Treat that run as a baseline. Compare later similar tasks with the same measures before claiming gains. Keep the checklist if its demonstrated benefit earns its burden; shorten or remove checks that add no decision value.

## Change receipt

- Added a six-step manual workflow and a reusable run receipt.
- Separated structural validation, behavioral checks, usefulness, and authorization.
- Added explicit scope for reuse and evidence for capability claims.
- Added effort tracking with unknown values preserved.
- Repository documentation added on an isolated review branch; no performance gain measured and no runtime or automation changed.


## Repository placement and GitHub workflow

This guide belongs to Quirk OS because it composes bounded work. Its reusable manual record lives at [templates/distinctions-run-receipt.md](../../templates/distinctions-run-receipt.md).

- Shared meanings: [Core working-intent reconciliation](https://github.com/Quirk-Systems/quirk-core/blob/b3162b0cd6dcc6c07570f240ca33c711ed860f0b/docs/working-intent-2026-09-10.md). This source remains REVIEW CANDIDATE. Data means represented state, Graph typed relationships, Maps purposeful perspectives and projections, Routes possible paths, Moves bounded intentional transformations, and Ways reusable methods. The drill examples above are applications, not replacements for those meanings.
- Repository procedure: [repository management candidate](../canon/REPO-MANAGEMENT.md).
- Organization governance and reusable CI: [Quirk-Systems/.github](https://github.com/Quirk-Systems/.github). This manual template does not replace that repository's exact-range evidence receipt contract.

For a GitHub change:

1. Inspect current main, relevant instructions, and open work. Reuse an existing branch/PR when it owns the same change.
2. Create an isolated agent branch for one bounded change; record the source base SHA.
3. Preserve observations, inferences, structural checks, behavioral checks, and allowed effects separately in the run receipt.
4. Open a draft PR describing outcome, scope, authority ceiling, changed contracts, migrations, tests, evidence, and the remaining human decision. Use the existing repository checks; this guide adds no Actions workflow.
5. Inspect the changed paths and results on the exact successor head. Name each check's coverage and anything not run. A check executing is not proof it is required by branch policy.
6. Present the exact head to Bryan for human review. Record his actual disposition; do not convert an assistant assessment into human approval. Any later change needs fresh evidence and an assessment of approval applicability.
7. Merge, activation, deployment, and Canon promotion retain their own applicable authorization requirements. A manual receipt or green check does not authorize them.

Observed placement baseline (2026-10-03): Quirk OS main `5096cf047b8d4eecd0d9312ea7bc4615ae322c92`; Core main `b3162b0cd6dcc6c07570f240ca33c711ed860f0b`. Existing Golden Gates runs `python scripts/validate_golden_pack.py` on pull requests. It does not measure this procedure's usefulness or enforce these manual steps.
