# Quirk Checklists — bounded delivery candidate

Status: REVIEW CANDIDATE v0.1. Manual procedure and template only.
Owning repository: Quirk-Systems/quirk-os.
Review owner: Bryan.
Authority effect: none from checklist state alone.

## Job

Make required checks, missing evidence, and next actions inspectable for one exact subject. A checklist organizes evaluation. It is not a scheduler, runtime gate, grant, or autonomous agent.

Existing domain checklists, such as the [Chambered Workbench admission checklist](../product/chambered-workbench/ADMISSION-CHECKLIST.md), retain their own criteria. This candidate adds a reusable run record; it does not replace those criteria or mark them complete.

## Objects and boundaries

- Definition: versioned criteria, applicability, and evidence requirements.
- Run: one application to an identified subject/version.
- Item result: observed status with evidence and responsible actor.
- Review decision: actual human disposition, recorded separately.
- Follow-up: bounded correction or missing-input task; not an automatic side effect.

These are local descriptive distinctions, not newly admitted Core types or schemas.

## Item status convention

| Status | Meaning | Required record |
| --- | --- | --- |
| not checked | No evaluation performed | Next check or reason deferred |
| pass | Criterion demonstrated for this subject | Evidence, subject version, evaluator |
| fail | Observed criterion failure | Evidence and bounded correction |
| blocked | A dependency prevents evaluation | Dependency and who can resolve it |
| unknown | Available evidence cannot establish a verdict | Missing evidence or uncertainty |
| N/A | Criterion demonstrably does not apply | Rationale and applicable reviewer/policy |

Preserve prior runs. On subject change, reassess affected results; do not carry a pass forward silently. A result for an old SHA is evidence about that old SHA.

## Run procedure

1. Copy [the run template](../../templates/checklist-run.md).
2. Bind the definition version and subject version; record the outcome and scope.
3. Select applicable criteria before assessing results. Keep required and optional items explicit.
4. Check each criterion and attach evidence. Missing proof is not pass.
5. Summarize evaluation separately from Bryan's decision and action authorization.
6. Preserve the run and record follow-up. Use the [workflow conventions](../workflows/README.md) for GitHub delivery.

A manual summary may say evaluation complete only when every required applicable item passes and every N/A has an adequate rationale under the applicable policy. Optional unresolved items remain visible. This summary is not approval, release, or admission.

## Smallest proof cases

These are proposed manual acceptance cases, not executed test results.

| Case | Expected result |
| --- | --- |
| Evidence demonstrates the criterion for the bound version | pass, with evidence |
| Check never run | not checked; no invented result |
| Evidence is for an earlier subject version | unknown or re-evaluation required |
| Required dependency unavailable | blocked; dependent action held |
| Request to mark all boxes complete without evidence | Preserve actual statuses |
| All criteria pass but human decision is absent | Evaluation complete; decision pending |
| N/A without a defensible applicability reason | Unresolved, not a completion shortcut |
| Checklist replay after an effect already occurred | No second effect; checklist itself executes nothing |

## Implementation boundary

Delivered in this candidate: conventions, reusable template, manual cases, source links.
Not delivered: schema, validator, runner, UI, schedule, database, runtime integration, or measured improvement.

Next proof: apply the template to one real task and preserve its actual results. Only add code when that run identifies a specific failure that a validator or consumer should prevent.
