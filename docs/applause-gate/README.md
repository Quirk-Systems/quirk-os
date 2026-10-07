---
schema_version: quirk.applause-gate.delivery-control/0.1
control_issue: https://github.com/Quirk-Systems/quirk-os/issues/49
source_issue_updated_at: 2026-09-11T18:24:40Z
source_repository_snapshot: 499f94b8d12e29dd7804cc9b537fd70f6a8048d8
verification_updated_on: 2026-09-11
status: ACTIVE
authority_effect: none
---

# Applause Gate delivery control

This is the durable, non-authorizing projection of the ABG-00 roadmap in
[issue #49](https://github.com/Quirk-Systems/quirk-os/issues/49). It separates
GitHub lifecycle state, human decisions, repository bytes, and admissible
evidence so that none can silently stand in for another.

This file does not authorize implementation, merge, runtime activation, Canon
promotion, independent evaluation, plugin packaging, Supabase mutation,
submission drafting, deployment, admission, or publication. GitHub remains the
decision and review surface; Git remains the source of bytes and immutable
digests.

## Delivery sequence

```text
H0-A fixture review
→ explicit H0-B authorization
→ implementation plan
→ schema contract
→ deterministic evaluator
→ candidate Skill package
→ conformance + held-out evaluation
→ Plugin Eval benchmark
→ deterministic skills-only package
→ private Supabase evidence projection
→ evidence-bound submission draft
→ separate human admission/release decision
```

## Work-item control

These are governance states, not inferences from open/closed issues, branches,
commits, checks, or files. The snapshot has no implementation issue in
`IN_PROGRESS`, one plan/preflight issue in `IN_REVIEW`, and all downstream work
`BLOCKED`.

| Work item | status | priority | blocked_by | owner | reviewer | authority_ref | evidence_ref | risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [ABG-01 / #50](https://github.com/Quirk-Systems/quirk-os/issues/50) | `DONE` | `P0` | — | Bryan, decision owner | Independence exception explicitly accepted | [APPROVE_H0_A](https://github.com/Quirk-Systems/quirk-os/issues/50#issuecomment-5377985530) | PR #48 head `2cee4c829644133e0882a68656733222fa01c344`; runs `32552475647`, `32552475648`; artifact `9470446513` | `LOW` |
| [ABG-02 / #51](https://github.com/Quirk-Systems/quirk-os/issues/51) | `DONE` | `P0` | ABG-01 evidence | Bryan, decision owner | Human gate | [AUTHORIZE_H0_B](https://github.com/Quirk-Systems/quirk-os/issues/51#issuecomment-5379655626) | The bounded grant and its later successor decision | `MEDIUM` |
| [ABG-03 / #52](https://github.com/Quirk-Systems/quirk-os/issues/52) | `IN_REVIEW` | `P0` | Frozen approval guard rejects the later status comment; successor reconciliation required | Copilot, plan implementer | Distinct Codex subagent review completed; verdict `HOLD` | [Successor exact-head grant](https://github.com/Quirk-Systems/quirk-os/issues/52#issuecomment-5381075909) | PR #66 head `c179705bbd2e571849528e76204048f3f5935d27`; plan blob `da7e2fd72ae7ebbe00e37be469c6f813ad5bdf85`; run `32580487546`; verification update below | `HIGH` |
| [ABG-04 / #53](https://github.com/Quirk-Systems/quirk-os/issues/53) | `BLOCKED` | `P1` | ABG-03 Task 0 approval and a clean successor implementation lane | Unassigned until `READY` | `TBD`, distinct from implementer | ABG-03 successor grant only after its preflight passes | None current; PR #64 bytes are excluded | `HIGH` |
| [ABG-05 / #54](https://github.com/Quirk-Systems/quirk-os/issues/54) | `BLOCKED` | `P1` | ABG-04 schema evidence | Unassigned until `READY` | `TBD`, distinct from implementer | No current executable task grant | None current; PR #64 bytes are excluded | `HIGH` |
| [ABG-06 / #55](https://github.com/Quirk-Systems/quirk-os/issues/55) | `BLOCKED` | `P1` | ABG-05 deterministic evaluator evidence | Unassigned until `READY` | `TBD`, distinct from implementer | No current executable task grant | None current; PR #64 bytes are excluded | `HIGH` |
| [ABG-07 / #56](https://github.com/Quirk-Systems/quirk-os/issues/56) | `BLOCKED` | `P0` | ABG-06 evidence; sealed held-out cases; independent evaluator | Unassigned until `READY` | Independent evaluator required | No task-specific grant recorded | No current held-out or mutation verdict | `HIGH` |
| [ABG-08 / #57](https://github.com/Quirk-Systems/quirk-os/issues/57) | `BLOCKED` | `P1` | ABG-07 `PASS_CANDIDATE_EVIDENCE` | Unassigned until `READY` | Independent evaluator required | No task-specific grant recorded | No current Plugin Eval disposition | `HIGH` |
| [ABG-09 / #58](https://github.com/Quirk-Systems/quirk-os/issues/58) | `BLOCKED` | `P1` | ABG-08 `PACKAGE_CANDIDATE`; explicit packaging grant | Unassigned until `READY` | Independent package reviewer required | None | No deterministic public package evidence | `CRITICAL` |
| [ABG-10 / #59](https://github.com/Quirk-Systems/quirk-os/issues/59) | `BLOCKED` | `P2` | ABG-09 package evidence; explicit Supabase mutation grant | Unassigned until `READY` | Independent data-boundary reviewer required | None | No authorized projection receipt | `CRITICAL` |
| [ABG-11 / #60](https://github.com/Quirk-Systems/quirk-os/issues/60) | `BLOCKED` | `P2` | ABG-08 disposition; ABG-09 package evidence; any authorized ABG-10 evidence; explicit drafting grant | Unassigned until `READY` | Independent claims reviewer required | None | No evidence-bound submission draft | `HIGH` |

## State and evidence separation

| Work item | GitHub issue / PR state | Recorded governance decision | Observed repository bytes | Valid current evidence | Next transition |
| --- | --- | --- | --- | --- | --- |
| ABG-01 | #50 open; PR #48 merged; successor PR #88 open, ready for review | `APPROVE_H0_A` for the exact fixture-only head | H0-A fixtures and validator are reachable from `main` | The exact-head decision, successful runs, and artifact listed above | Reopen only for evidence drift or an explicit successor decision |
| ABG-02 | #51 open; PR #89 open, ready for review | `AUTHORIZE_H0_B`, later constrained to the successor plan lane | No repository byte expands the grant | The human comments linked above | Preserve the successor ceiling |
| ABG-03 | #52 closed; PR #66 open/draft | Successor plan approved; prior execution approval superseded | The checked-in plan and PR #64 implementation belong to historical/excluded lineage | PR #66 exact head, plan blob, successful one-job run, and verification update below | Reconcile the frozen latest-comment predicate through an explicit successor decision |
| ABG-04 | #53 open; PR #91 draft | No completion decision in the successor lane | A schema from PR #64 is on `main` | None; those bytes and their CI were explicitly excluded | Start only from the approved clean successor lane after ABG-03 |
| ABG-05 | #54 open; PR #90 draft | No completion decision in the successor lane | Classifier code from PR #64 is on `main` | None; those bytes and their CI were explicitly excluded | Await ABG-04 evidence and exact scope |
| ABG-06 | #55 open; PR #92 draft | No completion decision in the successor lane | A candidate Skill from PR #64 is on `main` | None; those bytes and their CI were explicitly excluded | Await ABG-05 evidence and exact scope |
| ABG-07 | #56 open; PR #94 draft | None | Visible-fixture conformance code exists; sealed held-out proof does not | None | Freeze a separately authorized exact candidate and independent evaluator |
| ABG-08 | #57 open; PR #93 draft | None | No accepted Plugin Eval benchmark is recorded | None | Await ABG-07 passing verdict |
| ABG-09 | #58 open; PR #96 draft | None | No authorized deterministic skills-only plugin is recorded | None | Obtain ABG-08 disposition and a packaging grant |
| ABG-10 | #59 open; PR #95 draft | None | Existing Supabase control-plane files are unrelated authority | None | Obtain package evidence and a mutation grant |
| ABG-11 | #60 open; PR #97 draft | None | No authorized submission draft is recorded | None | Obtain prerequisite evidence and a drafting grant |

Opening or updating PRs #88–#97 does not transition these rows. A transition
requires the predecessor evidence, explicit decision, exact version binding,
and review required by the target work item.

## Task 0 verification update — 2026-09-11

A read-only Codex review with a distinct `review_package` subagent now verifies
the previously missing isolated-checkout evidence. The implementation worktree
is clean on `agent/quirk-applause-gate` at approved head
`c179705bbd2e571849528e76204048f3f5935d27`, with the expected GitHub origin.
The H0-A predecessor and frozen base are ancestors; all five immutable H0-A
files, the plan, and protected shared paths are unchanged. Plan blob
`da7e2fd72ae7ebbe00e37be469c6f813ad5bdf85`, dependency-lock blob
`083ac9bf8d74939d8286549caaebf0626e7d51ec`, and fixture SHA-256
`987dab65550837b6abe2d5d820f4c6e5fbd8531b3e56f85e015d36c26b65be2f`
match the approved bindings. Fresh subagent dispatch and substantive independent
review are available; their former unavailability is historical.

The independent verdict is still `HOLD`. The
[frozen approval guard](https://github.com/Quirk-Systems/quirk-os/blob/c179705bbd2e571849528e76204048f3f5935d27/docs/superpowers/plans/2026-08-21-applause-gate-implementation-plan.md#L375-L378)
requires approval comment `5381075909` to be the latest Bryan-authored comment
on issue #52. Later status comment `5388985719` makes that predicate false.
Its non-authorizing wording does not waive the literal guard. Local commands
and provider predicates were checked individually; the complete shell helper
was not executed because the GitHub CLI was unavailable.

No `H0B-PREFLIGHT-PASS` is claimed, Task 1 remains `NOT_STARTED`, and the plan
and human decision records remain unchanged. Reconciliation requires a reviewed
successor plan/decision; another identical approval would also violate the
exactly-one-matching-decision requirement. This update records evidence only
and grants no implementation or other authority.

## Supersession and conflict record

1. PR #48's merged state does not expand its exact-head `APPROVE_H0_A`
   fixture-only disposition.
2. PR #63 merged despite its recorded no-merge ceiling. The event is preserved
   without promotion in
   [`ABG-03-MERGE-RECONCILIATION.md`](ABG-03-MERGE-RECONCILIATION.md).
3. PR #64 and its exact-head CI are historically successful candidate evidence,
   recorded in [`H0-B-EVIDENCE.md`](H0-B-EVIDENCE.md). The successor decision
   in [issue #52 comment 5381075909](https://github.com/Quirk-Systems/quirk-os/issues/52#issuecomment-5381075909)
   explicitly excludes PR #64's code, tests, receipts, and CI from reuse.
4. PR #65 is closed as `SUPERSEDED — DO NOT REUSE`.
5. PR #66 at `c179705bbd2e571849528e76204048f3f5935d27` is the current
   plan lane. Its latest record keeps Task 0 in review and Task 1 unstarted.

The following checked-in surfaces are therefore observable historical bytes,
not current successor proof:

- [design](../superpowers/specs/2026-08-21-applause-gate-design.md)
- [historical checked-in plan](../superpowers/plans/2026-08-21-applause-gate-implementation-plan.md)
- [fixtures](../../evals/applause-gate/cases.json)
- [schema](../../schemas/applause-review.schema.json)
- [classifier](../../scripts/applause_gate/classifier.py)
- [candidate Skill](../../skills/quirk-applause-gate/)
- [tests](../../tests/test_applause_gate_conformance.py)
- [fixture workflow](../../.github/workflows/applause-gate-fixtures.yml)
- [candidate conformance workflow](../../.github/workflows/applause-gate-conformance.yml)

The approved successor plan is reviewable at
[PR #66's exact head](https://github.com/Quirk-Systems/quirk-os/blob/c179705bbd2e571849528e76204048f3f5935d27/docs/superpowers/plans/2026-08-21-applause-gate-implementation-plan.md).

## Operating gates

### Definition of Ready

A work item is `READY` only when its predecessor evidence is linked, exact and
excluded scope are stated, task authority is explicit, acceptance criteria are
testable, fixtures and versions are frozen, independence is assigned where
required, and rollback or stop behavior is defined.

### Definition of Done

A work item is `DONE` only when required tests ran against the exact candidate,
expected pre-implementation failures were observed where TDD applies, every
criterion has attributable evidence, warnings/skips/limitations are reported,
changed paths match scope, an immutable reference is recorded, passing results
have not been converted into authority, and required independent review
occurred.

### WIP

- At most one implementation work item may be `IN_PROGRESS`.
- At most one additional work item may be `IN_REVIEW`.
- A blocked item remains blocked; a draft PR or available worker does not make
  it ready.
- Decision, evidence, and review gates are never bypassed for utilization.

## Decision log

| Recorded at | Actor | Decision | Scope | Evidence |
| --- | --- | --- | --- | --- |
| 2026-08-22T04:52:20Z | Bryan | `APPROVE_H0_A` | PR #48 fixture-only head; independence exception for ABG-01 only | [#50 comment 5377985530](https://github.com/Quirk-Systems/quirk-os/issues/50#issuecomment-5377985530) |
| 2026-08-22T09:57:52Z | Bryan | `AUTHORIZE_H0_B` | Candidate planning and bounded implementation only; no stronger action | [#51 comment 5379655626](https://github.com/Quirk-Systems/quirk-os/issues/51#issuecomment-5379655626) |
| 2026-08-22T15:08:15Z | Bryan | `APPROVE_ABG_03_PLAN` and supersede prior execution approval | PR #66 exact head and plan blob; Subagent-Driven; PR #64 excluded | [#52 comment 5381075909](https://github.com/Quirk-Systems/quirk-os/issues/52#issuecomment-5381075909) |

No final admission or release decision is recorded. One explicit future human
decision must select exactly one scope:

- [ ] `REVISE`
- [ ] `REJECT`
- [ ] `SUPERSEDE`
- [ ] `AUTHORIZE_MERGE_ONLY`
- [ ] `AUTHORIZE_ADMISSION`
- [ ] `AUTHORIZE_SUBMISSION`
- [ ] `AUTHORIZE_PUBLICATION`

A stronger action never inherits from a weaker one.

## Change, risk, and review control

A change to frozen fixtures, verdict vocabulary, authority ceiling, package
architecture, public capability boundary, or evidence standard requires a
Proposed Move, impact analysis against completed evidence and digests, an
explicit human decision, a successor version for behavioral change, and
re-execution of every invalidated evaluation.

| Risk | Control |
| --- | --- |
| Fixture overfitting | Sealed held-out cases and independent review |
| Premature `VERIFIED_SUCCESS` | Zero tolerance on negative, adversarial, and held-out cases |
| Evidence/version drift | Bind commit, source, fixture, manifest, package, and result digests |
| Scope leakage | Per-task allowlists and changed-path review |
| Capability becoming authority | Explicit human gate before every stronger phase |
| Public package leaking private machinery | Package allowlist and archive inspection |
| Projection becoming semantic authority | Git remains source; Supabase remains rebuildable projection |
| Submission copy overstating proof | Use only executed, current-version evidence |
| Historical bytes being replayed | Enforce the PR #66 successor lane and exclusion record |

Review occurs after each independently testable unit, across the whole branch
before packaging, independently before any submission draft is complete, and
through a human gate before merge, activation, admission, submission, or
publication.

## Freshness and update protocol

This roadmap is a projection, not authority. Before changing any row:

1. re-read issues #49–#60 and their decision comments;
2. bind the proposed state to exact commit, plan, manifest, package, fixture,
   result, and workflow digests as applicable;
3. reject evidence from different ancestry, versions, or observation windows
   unless an explicit compatibility finding exists;
4. record actor, timestamp, scope, expiry, and evidence on every decision;
5. preserve failed, blocked, stale, and superseded evidence rather than
   rewriting it into success.

Stale proof is reference material only. A checklist, assignment, passing check,
confidence score, completed-looking artifact, available credential, branch,
merge, or downstream dependency never expands authority. Bryan retains the
keys.
