---
schema_version: quirk.authorization-decision/0.1
artifact_id: quirk.applause-gate.abg-02.h0-b-authorization
decision: AUTHORIZE_H0_B
decision_actor: bryansayler
decision_recorded_at: 2026-08-22T09:57:52Z
projection_status: HISTORICAL_RECORD
current_execution_state: HOLD
authority_effect: none
---

# ABG-02 H0-B Authorization Record

## Decision and attribution

Bryan recorded `AUTHORIZE_H0_B` for candidate-only Applause Gate planning and
implementation in issue #51:

- actor: `@bryansayler`;
- timestamp: `2026-08-22T09:57:52Z`;
- decision reference:
  [`issue #51 comment 5379655626`](https://github.com/Quirk-Systems/quirk-os/issues/51#issuecomment-5379655626);
- repository: `Quirk-Systems/quirk-os`;
- base branch: `main`;
- implementation branch: `agent/quirk-applause-gate`.

The candidate-version and exact-path bindings come from the later human-approved
successor plan described below. This file projects the human comments into the
repository for discovery; it does not issue, renew, or expand authority.

The successor plan binds H0-A input
`quirk-applause-gate@0.1.0-fixture-only` to authorized H0-B candidate
`quirk-applause-gate@0.1.0`.

## H0-A predecessor gate

The first ABG-02 decision was `REVISE_BEFORE_AUTHORIZATION` because ABG-01 found
an unlocked verdict declaration, no regression test for that drift, and no
independent-review evidence. The technical blocker was then corrected with a
RED-to-GREEN cycle. Bryan accepted the documented reviewer-independence
exception and recorded `APPROVE_H0_A` for PR #48 at exact head
`2cee4c829644133e0882a68656733222fa01c344`.

Exact predecessor evidence:

- [initial `REVISE_H0_A` review](https://github.com/Quirk-Systems/quirk-os/issues/50#issuecomment-5377900222);
- [successor-head technical re-review](https://github.com/Quirk-Systems/quirk-os/issues/50#issuecomment-5377946377);
- [human independence exception and `APPROVE_H0_A`](https://github.com/Quirk-Systems/quirk-os/issues/50#issuecomment-5377985530);
- fixture SHA-256:
  `987dab65550837b6abe2d5d820f4c6e5fbd8531b3e56f85e015d36c26b65be2f`;
- successful Applause Gate run `32552475647`;
- successful Golden Gates run `32552475648`.

No H0-A blocker remained when Bryan recorded `AUTHORIZE_H0_B`. Any reopened or
new H0-A blocker stops H0-B; it cannot be waived by this record.

## Authorized implementation scope

The grant permits only:

1. Superpowers implementation planning;
2. the closed `applause-review` schema and valid example;
3. a pure, deterministic classifier with no hidden I/O;
4. visible-fixture projection, conformance, purity, determinism, and
   content-addressed receipt evidence;
5. a quarantined internal candidate Skill package after evaluator evidence
   passes;
6. repository-native tests and read-only PR CI evidence; and
7. one candidate-only draft implementation PR and its evidence metadata.

The six H0-A verdicts and the 5 positive / 3 negative / 11 adversarial corpus
remain immutable inputs.

## Controlling successor binding

The PR #64 execution watermark in issue #51 comment `5380917867` was superseded
in full by Bryan's later
[`SUPERSEDE_ABG_03_EXECUTION_APPROVAL`](https://github.com/Quirk-Systems/quirk-os/issues/52#issuecomment-5381075909).
The controlling binding is:

- plan PR: `#66`;
- plan branch: `agent/quirk-applause-gate-plan-v2`;
- plan head: `c179705bbd2e571849528e76204048f3f5935d27`;
- plan blob:
  `da7e2fd72ae7ebbe00e37be469c6f813ad5bdf85`;
- implementation branch: `agent/quirk-applause-gate`;
- execution mode: `Subagent-Driven`;
- Golden Gates run/job: `32580487546` / `97048971309`, `success`.

PR #64 and all of its code, tests, receipts, reviews, and CI evidence are
historical and excluded from the successor authorization. They may not be
merged, cherry-picked, copied, regenerated from, or cited as satisfying the
successor tasks.

## Exact write boundary

The approved plan is immutable during implementation. Only these paths may
change:

- `schemas/applause-review.schema.json`
- `examples/applause-gate/applause-review.valid.json`
- `evals/applause-gate/h0-b-requests.json`
- `evals/applause-gate/h0-b-assertions.json`
- `evals/applause-gate/receipts/evaluator/<64-lowercase-hex>.json`
- `evals/applause-gate/receipts/binding/<64-lowercase-hex>.json`
- `scripts/applause_gate/__init__.py`
- `scripts/applause_gate/canonical.py`
- `scripts/applause_gate/json_io.py`
- `scripts/applause_gate/fixture_projection.py`
- `scripts/applause_gate/classifier.py`
- `scripts/applause_gate/receipt.py`
- `scripts/validate_applause_gate.py`
- `scripts/validate_applause_gate_package.py`
- `tests/test_applause_gate_schema.py`
- `tests/test_applause_gate_projection.py`
- `tests/test_applause_gate_classifier.py`
- `tests/test_applause_gate_purity.py`
- `tests/test_applause_gate_conformance.py`
- `tests/test_applause_gate_determinism.py`
- `tests/test_applause_gate_skill_package.py`
- `candidate-packs/applause-gate/skill/SKILL.md`
- `candidate-packs/applause-gate/skill/manifest.schema.json`
- `candidate-packs/applause-gate/skill/manifest.json`
- `candidate-packs/applause-gate/skill/conformance.json`
- `.github/workflows/applause-gate-conformance.yml`

The shared `skills/`, `evals/skills/`, Skill-package schema, shared Skill
validator/runtime tests, sync-control-plane runtime, H0-A files, deployment
surfaces, and every unlisted path are excluded. Any additional path requires a
successor human grant.

## Tools and provider operations

| Operation | Decision |
| --- | --- |
| Local execution | Allowed only in an isolated worktree, task-by-task, after all Task 0 gates pass. |
| Tools | `superpowers:subagent-driven-development`, Bash, Git, GitHub CLI, `jq`, SHA-256 tooling, Python 3.13, the standard library, `unittest`, `jsonschema==4.26.0`, `PyYAML==6.0.3`, and pinned repository GitHub Actions. |
| Dependency acquisition | Limited to installing the exact unmodified `requirements-evals.txt` lock at Git blob `083ac9bf8d74939d8286549caaebf0626e7d51ec`; additions and version changes are not authorized. |
| Push | Non-force pushes to `agent/quirk-applause-gate` only. No push to `main`, force-push, branch deletion, or tag. |
| Draft PR | One draft implementation PR targeting `main` may be created or updated with candidate evidence. |
| Reviewer requests | Not authorized. Review submission and ready-for-review transition are also prohibited. |
| CI | Pull-request CI and candidate artifact upload are allowed. Only `.github/workflows/applause-gate-conformance.yml` may change; manual dispatch is prohibited. |

## Explicit authority ceilings

Implementation authority is not merge, activation, admission, deployment, or
publication authority. H0-B grants none of the following:

- runtime activation or shared discovery;
- Canon promotion;
- Supabase access, mutation, migration, or projection;
- plugin packaging;
- Skill Submission Pack or other submission drafting;
- OpenAI portal action;
- merge or auto-merge;
- admission;
- deployment;
- release or publication; or
- any external-provider mutation beyond the narrow draft-PR/CI operations above.

## Expiry, revocation, and stop conditions

No calendar expiry was stated, and this record does not invent one. The grant is
not evergreen or transferable: Bryan may revoke or supersede it, and the
execution binding becomes unusable on any plan-content change, fixture or
verdict drift, candidate-version change, wrong branch or ancestry, path escape,
force-push, reopened H0-A blocker, false `VERIFIED_SUCCESS`, fabricated
evidence, non-determinism, hidden I/O, benchmark leakage, validator weakening,
or authority smuggling.

The latest status record leaves Task 0 `IN_REVIEW`, with the isolated-local-
worktree, distinct-reviewer, and Subagent-Driven execution gates unsatisfied;
Task 1 is `NOT_STARTED`. No implementation may begin until those gates are
reconciled by valid human authority. Completion of candidate evidence ends at
handoff and never implies any stronger authority.

Silence, issue creation, assignment, labels, PR state, prior approval, passing
fixtures or CI, confidence, completed-looking artifacts, branch position, and
available credentials are explicitly non-authorizing.

## Roadmap and evidence links

- Parent delivery roadmap and decision log: [issue #49](https://github.com/Quirk-Systems/quirk-os/issues/49)
- ABG-02 human gate: [issue #51](https://github.com/Quirk-Systems/quirk-os/issues/51)
- Controlling plan decision and latest Task 0 status:
  [issue #52](https://github.com/Quirk-Systems/quirk-os/issues/52)
- Historical PR #64 evidence:
  [`H0-B-EVIDENCE.md`](H0-B-EVIDENCE.md)

**Authority ceiling:** this repository artifact records provenance only. The
linked Bryan-authored comments remain the decision sources.
