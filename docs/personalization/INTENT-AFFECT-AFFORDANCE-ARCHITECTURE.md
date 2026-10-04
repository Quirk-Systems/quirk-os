# Intent × Persona × Affect × Affordance

**Status:** Candidate architecture  
**Parent:** Quirk Sync Control Plane  
**Skill:** `skill.quirk-intent-shaper`

## Thesis

Quirk personalization should not be a personality prompt pasted on top of every task.

It should be a governed compilation process:

```text
current intent
+ purpose-scoped preference evidence
+ bounded persona lenses
+ expression contracts
+ platform affects
+ task affordances
+ authority and uncertainty
= reversible Personalization Plan
```

## Control objective

Choose an experience plan that improves the user’s intended outcome while preserving truth, authority, accessibility, inspectability, and reversibility.

```text
maximize:
  intent fit
  preference fit
  task leverage
  platform fit
  evidence quality
  independent reuse
  strange intact

subject to:
  authority
  safety
  privacy
  accessibility
  current explicit instructions
  purpose boundaries
```

No single score should hide tradeoffs. Candidate plans remain a Pareto set until policy or a human selects one.

## Precedence

```text
current explicit instruction
> current purpose-scoped setting
> reaffirmed durable preference
> recent explicit feedback
> repeated observed behavior
> bounded inference
> population default
```

Negative constraints apply before positive style optimization.

## Architecture layers

### 1. Intent plane

Resolves:

- desired change;
- task class;
- stakes;
- destination;
- audience;
- completion evidence;
- constraints and non-goals.

### 2. Preference plane

Stores purpose-scoped edges with:

- source;
- confidence;
- comparison target;
- time;
- validity;
- reversibility;
- sensitivity;
- supersession.

### 3. Persona plane

Selects a temporary Persona Hand:

- primary functional lens;
- supporting lenses;
- weights;
- task role;
- explicit exclusions.

### 4. Expression plane

Compiles:

- voice;
- tone vector;
- lexical rules;
- aesthetic principles;
- structural preferences;
- no-fill rules;
- accessibility needs.

### 5. Platform-affect plane

Maps the destination into operational pressure:

- versioning;
- collaboration;
- privacy;
- latency;
- screen and modality;
- reversibility;
- execution capability;
- expected evidence.

### 6. Task-affordance plane

Selects useful interaction primitives from an admitted registry.

### 7. Evaluation plane

Runs pointwise and counterfactual checks before preference ranking.

### 8. Learning plane

Creates immutable feedback receipts and proposed preference updates.

## Platform Affect contract

A `PlatformAffect` does not say what the user likes. It says how a platform changes the task.

```yaml
platform_affect:
  platform: github
  effects:
    - versioned
    - collaborative_review
    - diff_first
    - executable_evidence
  preferred_affordances:
    - patch
    - check_run
    - issue
    - review_comment
  prohibited:
    - infer_merge_authority
    - claim_success_without_checks
```

## Task Affordance contract

```yaml
task_affordance:
  type: ranked_pair
  purpose: reveal_preference
  reversible: true
  evidence:
    - explicit_selection
  accessibility:
    keyboard: required
    screen_reader: required
  fallback: numbered_text_options
```

## Adaptation states

```text
UNKNOWN
→ OBSERVED
→ INFERRED
→ PROPOSED
→ CONFIRMED
→ PURPOSE-SCOPED
→ SUPERSEDED / EXPIRED / FORGOTTEN
```

No implicit signal may jump directly to `CONFIRMED`.

## Feedback semantics

A user edit can mean several different things:

- the fact was wrong;
- the task was misunderstood;
- the platform form was wrong;
- the preference was wrong;
- the preference changed;
- the candidate was good but not chosen;
- the user wanted variety.

The receipt must classify the cause before updating confidence.

## Generated UI admission

Generated UI is not an admitted affordance in Intent Shaper v0.2. The candidate schema rejects it. A future version may add it only when:

1. the task benefits from interaction;
2. the component grammar is admitted;
3. every action declares state effects;
4. protected actions have explicit gates;
5. keyboard and screen-reader paths exist;
6. a plain-text fallback exists;
7. the interface can be reconstructed from its plan;
8. the user can inspect why it was selected.

## Why this fights generic enterprise AI

The [competitor review](../../research/competitors/quirk-enterprises-swipe-fight-2026-08-11.md) attributes connected ERP, CRM, WMS, cloud, and data language to https://quirkenterprise.com/. “Generic” is a positioning interpretation, not a verified defect. Comparable personalization/governance evidence was **not found in review** of that homepage and https://quirkenterprise.com/insights; no snapshots or search log were retained, and those pages were not fetched again for this repair.

Quirk's proposed differentiator is the layer that decides (not a demonstrated competitive outcome):

- what the user is actually trying to accomplish;
- which version of the user is useful for this task;
- how the relationship should sound and feel;
- what each platform changes;
- what interface should exist now;
- which adaptation is allowed to persist;
- what evidence proves the adaptation helped.

## Implementation provenance and remaining admission gates

Owner: `Quirk-Systems/quirk-os`; documentation repair date: 2026-10-04. [PR #15](https://github.com/Quirk-Systems/quirk-os/pull/15) is merged (GitHub metadata: 2026-10-04T04:08:03Z), although its body still describes an older draft posture and twenty-case results. Merge is implementation provenance, not runtime admission.

The local HEAD reflog and `origin/main` ref identify `c4bc0f0bdff10ccc217c8115035bd918129fe4b0`. The [Skill at that revision](https://github.com/Quirk-Systems/quirk-os/blob/c4bc0f0bdff10ccc217c8115035bd918129fe4b0/skills/quirk-intent-shaper/SKILL.md) was retrieved and remains candidate, version 0.2.0, ceiling `propose`. The [cases at that revision](https://github.com/Quirk-Systems/quirk-os/blob/c4bc0f0bdff10ccc217c8115035bd918129fe4b0/evals/intent-shaper/cases.json) correspond to the locally read suite: 25 cases (QIS-001–012, QIS-012A/B, QIS-R01–R11). This is a source inventory, not a new passing test result. Always derive execution counts from the current `cases` array; QIS-013–018 admission exercises are a separate supply set, not silently counted as evaluator fixtures.

GitHub's PR commit listing includes historical `acbb91e9964d02dadb0cd3c3c7c0cae74ff2bffb`, evaluated `f5effa3d6da3e5879e10007492aeff39a1c643be`, repair `0f840d3e99fa19991e530fd366a0537ea9837cc8`, and head `b33954b6b3dd18e36a045d5acefd0c9423a6a867`. Parent deepened history by 200 and verified both historical active-set receipts. Do not substitute historical PR hashes or stale check results for current-tree receipts.

The move's implementation evidence pins all eight layers below to `c4bc0f0bdff10ccc217c8115035bd918129fe4b0`, owner `Quirk-Systems/quirk-os`. GitHub file retrieval supplied Skill/case blob IDs; directory metadata at that exact revision supplied the remaining path/blob IDs. Local source sections were read, but those six pinned file contents were not separately downloaded or executed. The map establishes baseline source provenance and existence, not current repair coverage, passing checks, or admission:

| Layer / repository path | Git blob at pinned main |
| --- | --- |
| Skill: `skills/quirk-intent-shaper/SKILL.md` | `b4d8e65acc119fba537a84f4d4fddbc8853bc41d` |
| Cases: `evals/intent-shaper/cases.json` | `8f56f79735be28b96f953ec6223d24de5b9ae353` |
| Schema: `schemas/personalization-plan.schema.json` | `8148b29cbb8deffad45529050cdcbcd29ac690bb` |
| Policy: `policies/personalization-adaptation-policy.yaml` | `aca1427648b4ab5abfe42c9378c614750222f001` |
| Evaluator: `scripts/intent_shaper/policy.py` | `f1fa4aee2fd7db94cfe3129645728f4ade7d40ac` |
| Validator: `scripts/validate_intent_shaper.py` | `a9228d0652f2e1296143d927ce95be33ae78fa0d` |
| Tests: `tests/test_intent_shaper.py` | `c8bd6ccaf4fd79e4f7b9ccf09d8ae849219fbbc9` |
| Workflow: `.github/workflows/intent-shaper-conformance.yml` | `5fa720e94d6dc9fad438867733edd07f21097d2f` |

Each has a canonical revision-pinned URL in the [move's `evidence_refs`](../../proposed-moves/personalization/qpm_intent_shaper_candidate.json). The new `scripts/intent_shaper/contracts.py` was not present in that revision's directory metadata and is not falsely pinned to it; current repairs need the parent's post-implementation receipts. Synthetic admission supplies are labeled **synthetic exercise/context only** and moved to `source_refs`/`resolution_artifacts`, not implementation `evidence_refs`.

### Governance rebinding is not implementation evidence

The existing `.quirk/evidence/2026-08-21-quirk-os-evidence-adoption.json`, also retrieved at abbreviated revision `5637a99`, identifies an October 4 rebinding of `3099e1c8a156c97828cec7e99d9e61dbc6e36f8f` → `6b2394c3af34e60c9a19b8cc6cefa69337a72cda`. It explicitly excludes Intent Shaper implementation coverage and runtime authority. Parent's successful historical receipt validation resolves the historical active-set blocker, not the current repair/admission gates.

The parent reports that the active evidence set resolves reachable squash `6b2394c`, the historical ancestry blocker is already repaired, and the pinned historical validator **passes 2 receipts after deepening by 200**. `5637a99` rewrote the August-named adoption path with October rebinding content, now published. Neither published receipt is rewritten by this repair.

The original adoption receipt was retrieved from [that path at squash `6b2394c3af34e60c9a19b8cc6cefa69337a72cda`](https://github.com/Quirk-Systems/quirk-os/blob/6b2394c3af34e60c9a19b8cc6cefa69337a72cda/.quirk/evidence/2026-08-21-quirk-os-evidence-adoption.json); GitHub reports blob `518c46bb8ad2546c4703098df96696036c4f0662`, matching the adoption artifact's pinned blob. Original bytes remain preserved in existing Git history, including receipt ID, historical `verified` status, commands, digest, and authority effect `none`. No additional archive or historical edit is needed. The original stranded subject is not reintroduced into the fail-closed active evidence set; historical preservation does not satisfy current implementation/admission gates.

The parent fetched the pinned validator to `/tmp/quirk-evidence-policy/validate_evidence_receipts.py` and will check current whole-diff byte-bound receipts after implementation commits. [PR #42's correction](../evidence/PR_42_CORRECTION.md) remains governance context only, not proof of the missing implementation.

**Pending current-repair evidence:** the move includes the planned path `.quirk/evidence/2026-10-04-intent-shaper-governance-repair.json`. It was absent from the evidence directory when reviewed on 2026-10-04 at 04:49. This is a forward reference, not an existing, passing, or verified receipt. Parent will generate it after the final implementation commit, commit the receipt in a descendant, and finalize whole-diff coverage with the pinned ecosystem validator. Neither the reference nor this document self-claims verification; runtime admission remains separate and blocked.

Before that implementation commit, run the Intent Shaper tests and conformance entry point against the final files, after the last documentation/metadata edits. The current `scripts/validate_intent_shaper.py` reads the plan/schema, canonical move, admission supplies/schema, policy, and entire cases array from the repository; its shared contract validator uses Draft 2020-12 with `FormatChecker`. That integration was checked in source, not treated as a passing run. Record actual command results and counts in the parent's byte-bound receipt, not inferred results from schema-test coverage alone.

### User authorization is real; observations are still missing

The exact current user approvals are recorded separately in [`admission-supplies.json`](../../evals/intent-shaper/admission-supplies.json):

- `Authorized by Bryan with Synthetically Generated and Marked Supplies` — source user turn `2026-10-04T04:28:25.038+00:00`
- `authorize merging updated main into the current branch so I can implement the repairs` — source user turn `2026-10-04T04:37:35.835+00:00`
- `Authorize all human approvals required` — source user turn `2026-10-04T04:37:35.835+00:00`

They authorize the bounded repairs and marked synthetic exercises, and are not generated observations. Source timestamps are the original user turns, as confirmed by the provenance correction; the artifact's `recorded_at` is capture time, not an approval source date. They do not specify a runtime purpose/source/sink/action/expiry scope or explicitly waive each missing observation. No approval is re-requested for already authorized repairs.

The governing [REVISE decision](https://github.com/Quirk-Systems/quirk-os/issues/16#issuecomment-5264312477) requires QIS-012–018 canonical, hash-pinned evidence; actual paired trial (QIS-013), manual accessibility observation or explicit human rescoping (QIS-014), and preference-summary inspection/correction (QIS-017); exact runtime scope and a new decision (QIS-018). Generated UI stays denied. Candidate-only denial exercises cannot prove UI accessibility, reconstruction, or fallback operability.

The new [supplies schema](../../schemas/intent-shaper-admission-supplies.schema.json) is deliberately candidate-only: it rejects synthetic exercises relabeled as human admission, nonempty claimed observations, supplied runtime grants/incomplete scopes claiming admission, and receipt references self-labeled verified. It does not verify receipt bytes. The conformance entry point loads this artifact with Draft 2020-12/format checks; passing supply validation means truthful blocked supplies, not admission. Parent/operator must generate actual byte-bound receipts after implementation using the pinned ecosystem validator, rather than hand-author passing receipts. An explicit narrowly scoped waiver from an authorized human may resolve specified gates only when separately recorded with its exact scope and a new decision; none is recorded here.
