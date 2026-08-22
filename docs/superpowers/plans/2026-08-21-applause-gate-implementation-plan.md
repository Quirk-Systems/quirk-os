# Applause Gate H0-B Candidate Implementation Plan

> **PLAN-ONLY SUCCESSOR:** This document supersedes the plan at `d36b4582c752cdcd7542377054b286efbb203861`, which was merged through PR #63 at `7541767cc5d30fe9a101b9e1f7eff817b68aac9f`; PR #63 therefore cannot truthfully remain draft. The clean successor draft on `agent/quirk-applause-gate-plan-v2` is the only plan-review surface. Issue #51 grant `5380917867` selected `INLINE_EXECUTION_WITH_TASK_GATES`, was bound to PR #64 reviewed head `50e3fb63abf64f91cbeeeb4bc8b4dff7ac2dba8c` and plan blob `e287b41e7ee6d6586022bf0d4e0b79170a8c7702`, and authorized task-gated descendants on PR #64's branch; that draft subsequently accumulated implementation and protected-surface changes. This plan proposes that PR #64 remain untouched as historical evidence and that no PR #64 byte, commit, test result, receipt, review, or CI result be imported, ratified, or usable as H0-B evidence. This text cannot approve or revoke authority by itself: execution remains stopped under this successor until a later Bryan-authored decision names the clean successor draft's exact post-revision head SHA/blob/run/job, selects `Subagent-Driven`, explicitly supersedes grant `5380917867` in full, and names implementation branch `agent/quirk-applause-gate`. Any plan-content change invalidates that approval.

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to implement this plan task-by-task. Use a fresh implementer for each task and a distinct reviewer for contract compliance and code quality before the next task begins.

**Goal:** Build a candidate-only Applause Gate evaluator that converts validated, typed evidence facts into deterministic `applause-review` objects, produces content-addressed evidence, and binds an unregistered internal Skill package without runtime activation.

**Architecture:** H0-B preserves the approved H0-A fixture corpus byte-for-byte, adds a reviewed typed-request projection that strips fixture oracle metadata before classification, and keeps the decision core pure. Visible conformance, deterministic evidence, and a reviewer verdict must bind the exact evaluator commit before Skill files may appear. The Skill source and manifest remain quarantined from the central registry and shared runtime evaluator.

**Tech Stack:** Python 3.13, standard library, `unittest`, `jsonschema==4.26.0`, `PyYAML==6.0.3`, Draft 2020-12 JSON Schema, and pinned GitHub Actions already used by the repository.

**Spec:** `docs/superpowers/specs/2026-08-21-applause-gate-design.md` at approved H0-A commit `2cee4c829644133e0882a68656733222fa01c344`.

**Authorization basis:** Issue #51 comment `5379655626` is the original bounded H0-B grant for `agent/quirk-applause-gate`. Latest issue #51 authority watermark `5380917867` was bound to PR #64's reviewed head `50e3fb63abf64f91cbeeeb4bc8b4dff7ac2dba8c` and plan blob `e287b41e7ee6d6586022bf0d4e0b79170a8c7702`, selected `INLINE_EXECUTION_WITH_TASK_GATES`, and authorized task-gated descendants on PR #64's branch; its exact body SHA-256 is `871a0d009bc9896c7421f1eed3dbebaead84f25eb97231c3c1c120ade81a26b0`. Issue #52 comment `5380558390` approved only `d36b4582c752cdcd7542377054b286efbb203861`; it is historical and non-transferable. The effective successor approval must be a new byte-closed issue #52 decision naming the exact clean-successor evidence, explicitly superseding both prior approvals and all PR #64 descendant execution authority, replacing inline mode with `Subagent-Driven`, and retaining every candidate ceiling. Until that exact decision exists, this successor grants no execution. PR metadata is an evidence projection, not the source of human authority.

**Execution mode:** `Subagent-Driven`, pending exact-SHA successor approval. Approval of this plan does not execute it. Execution starts only in a later turn from the exact approved successor plan SHA on the separately authorized implementation branch.

**Plan-review binding:** exactly one open draft PR with head `agent/quirk-applause-gate-plan-v2`, base `main` at `7541767cc5d30fe9a101b9e1f7eff817b68aac9f`, and changed path exactly this plan file. Task 0 resolves and freezes its PR number, head SHA, and issue-decision comment ID. The plan-review branch is not an implementation branch.

## Global Constraints

- Candidate-only. No runtime activation, Canon promotion, admission, merge, deployment, release, publication, OpenAI portal action, plugin packaging, or Skill Submission Pack.
- Authorized candidate execution means explicit unit-test or validator invocation only in an isolated local worktree or PR-CI evidence job. Runtime activation means any shared loader/import route, registry/discovery entry, installed entry point, API/service/worker/job/schedule, deployment, model/tool routing, or external consumer; all are prohibited.
- No Supabase mutation, migration, projection write, remote database access, model call, or connected-tool dependency in classifier behavior.
- No authority expansion from passing tests, receipts, CI, confidence, available credentials, branch position, registry location, or completed-looking artifacts.
- Preserve the exact verdict vocabulary: `SIGNAL_ONLY`, `SUPPORTED_DIAGNOSIS`, `VERIFIED_SUCCESS`, `FALSE_POSITIVE`, `UNRESOLVED`, `EVIDENCE_INTEGRITY_FAILURE`.
- Every H0-B JSON input uses `load_json_strict`; duplicate keys and non-finite literals fail before schema or classifier logic.
- Preserve the H0-A corpus at exactly 5 positive, 3 negative, and 11 adversarial cases.
- False `VERIFIED_SUCCESS`, fabricated evidence, non-determinism, hidden I/O, benchmark leakage, fixture weakening, validator weakening, or authority smuggling stops the tranche.
- `evaluate` remains the H0-A domain-family label and the quarantined candidate manifest uses it verbatim. No mapping to the shared Skill-family enum is claimed; compatibility or ontology amendment belongs to a separately authorized admission decision.
- The entire shared `skills/`, `evals/skills/`, `schemas/skill-package.schema.json`, `scripts/validate_skills.py`, `tests/test_skill_runtime.py`, and `scripts/sync_control_plane/` surfaces are protected and must not change. The Skill candidate lives only under the non-discoverable `candidate-packs/applause-gate/` quarantine root.
- The repository is public. Never place sealed held-out cases, private evidence, secrets, tokens, credentials, personal data, or provider-only payloads in source, PR text, logs, comments, or artifacts.
- Passing visible conformance never authorizes ABG-07. Stop unconditionally before mutation campaigns, sealed held-out evaluation, Plugin Eval, packaging, projection, submission, merge, admission, deployment, or publication.
- The inherited H0-A workflow contains `workflow_dispatch`; it is protected predecessor debt, not authority. Never invoke it manually or reuse its checkout semantics as H0-B evidence. The new H0-B workflow has no manual trigger.
- Treat PR #64 and its branch as a tainted prior execution lane after successor approval. Do not merge, cherry-pick, rebase, copy, regenerate from, or cite its implementation, tests, fixtures, Skill files, receipts, reviews, workflow results, or commits as satisfying any task. Every RED and GREEN byte and every receipt must be produced anew from the exact approved successor plan SHA on `agent/quirk-applause-gate`.

## Immutable Predecessor

H0-B is layered on exact commit `2cee4c829644133e0882a68656733222fa01c344`. These H0-A files are immutable inputs:

- `.github/workflows/applause-gate-fixtures.yml`
- `docs/superpowers/specs/2026-08-21-applause-gate-design.md`
- `evals/applause-gate/cases.json`
- `scripts/validate_applause_gate_fixtures.py`
- `tests/test_applause_gate_fixtures.py`

The approved compact bytes of `evals/applause-gate/cases.json` have SHA-256 `987dab65550837b6abe2d5d820f4c6e5fbd8531b3e56f85e015d36c26b65be2f`. Every task must prove those paths have no byte changes from the immutable predecessor. H0-B validation must additionally fail closed on the unresolved PR #63 review inputs—whole-corpus byte drift, `candidate_version` drift, non-closed `expected`, non-list/non-string evidence refs, and case-payload replacement—without modifying the protected H0-A validator or corpus.

## Exact H0-B Path Allowlist

The current plan-only revision may change exactly one repository path:

- `docs/superpowers/plans/2026-08-21-applause-gate-implementation-plan.md`

After successor approval, that plan path becomes immutable and is excluded from the implementation write set. Only these implementation paths may then change:

- `schemas/applause-review.schema.json` — closed request/review contract.
- `examples/applause-gate/applause-review.valid.json` — schema-valid review example.
- `evals/applause-gate/h0-b-requests.json` — typed requests derived from H0-A cases.
- `evals/applause-gate/h0-b-assertions.json` — evaluation-only required/prohibited codes; never classifier input.
- `evals/applause-gate/receipts/evaluator/<64-lowercase-hex>.json` — exactly one content-addressed evaluator receipt.
- `evals/applause-gate/receipts/binding/<64-lowercase-hex>.json` — exactly one content-addressed Skill-binding receipt.
- `scripts/applause_gate/__init__.py` — exports typed candidate interfaces.
- `scripts/applause_gate/canonical.py` — pure canonical JSON and semantic input-digest helpers.
- `scripts/applause_gate/json_io.py` — strict duplicate/non-finite-rejecting JSON loader.
- `scripts/applause_gate/fixture_projection.py` — evaluation-only fixture-to-request projection.
- `scripts/applause_gate/classifier.py` — pure decision core.
- `scripts/applause_gate/receipt.py` — canonical payload and digest helpers.
- `scripts/validate_applause_gate.py` — schema/conformance/receipt runner.
- `scripts/validate_applause_gate_package.py` — quarantined package validator.
- `tests/test_applause_gate_schema.py`
- `tests/test_applause_gate_projection.py`
- `tests/test_applause_gate_classifier.py`
- `tests/test_applause_gate_purity.py`
- `tests/test_applause_gate_conformance.py`
- `tests/test_applause_gate_determinism.py`
- `tests/test_applause_gate_skill_package.py`
- `candidate-packs/applause-gate/skill/SKILL.md` — quarantined source, outside shared Skill discovery.
- `candidate-packs/applause-gate/skill/manifest.schema.json` — closed candidate-only package contract.
- `candidate-packs/applause-gate/skill/manifest.json` — evaluator-receipt-bound candidate manifest.
- `candidate-packs/applause-gate/skill/conformance.json` — four quarantined Skill cases.
- `.github/workflows/applause-gate-conformance.yml` — PR-only candidate evidence workflow.

Any additional file requires a successor human grant before it is created or modified.

## Provider Operation Allowlist

Authorized provider operations during this plan-only revision:

- create `agent/quirk-applause-gate-plan-v2` at exact base `7541767cc5d30fe9a101b9e1f7eff817b68aac9f` if absent;
- update only this plan file on that branch and open exactly one draft successor PR targeting `main`;
- update only that successor PR's title/body without closing keywords, reviewer requests, labels, ready-for-review transition, or merge settings;
- record one successor approval decision on issue #52 only after the plan update produces an exact head SHA and successful exact-head Golden Gates run/job, preserving prior decisions as historical evidence while explicitly superseding issue #51 comment `5380917867` and issue #52 comment `5380558390`;
- read repository, PR, issue, review, and CI evidence needed to verify those mutations.

Authorized provider operations during later execution, only after exact-SHA successor approval:

- non-force push commits to `agent/quirk-applause-gate`;
- create `agent/quirk-applause-gate` at the approved clean-successor plan SHA if the branch is absent;
- open one draft implementation PR targeting `main`, or update that exact draft, with candidate evidence;
- read the frozen successor plan PR, the implementation PR, their exact-head CI, and repository files required by this plan;
- update only the implementation draft PR title/body with candidate evidence;
- allow `pull_request` CI to run and upload candidate evidence artifacts for the exact PR head.

Not authorized:

- additional issue comments or any issue state/label changes after the single successor approval decision;
- reviewer requests, review submission, or ready-for-review transition;
- manual workflow dispatch;
- force push, branch deletion, tag, release, merge, auto-merge, deployment, publication, portal action, or external-provider mutation.

The clean successor PR must remain draft and plan-only. After the byte-closed successor decision, PR #64 and every descendant of its reviewed head are untouched historical evidence with no execution, runtime, Canon, provider, packaging, publication, merge, or admission authority; neither plan PR is the implementation PR. The conformance workflow is repository-read-only but writes ephemeral GitHub Actions artifacts. That evidence write is narrow, public-repository-safe, and does not grant authority.

## Standard TDD Evidence Contract

Behavioral tasks use three preserved phases:

1. `RED`: an importable harness executes and fails a named behavioral assertion. Syntax/collection failures and unexpected missing harness, module, dependency, or input failures do not qualify; only a task-declared absent subject-under-test artifact may qualify under the stricter exception below.
2. `GREEN`: the smallest implementation makes the focused assertion pass.
3. `REFACTOR`: cleanup preserves focused and repository-native green results.

For every phase, record durably: Tasks 1–5 in the Task 6 evaluator receipt, and Task 7 in the Task 8 binding receipt:

- phase, task ID, command, exit code, selected test IDs, pass/fail/skip counts;
- expected failure code and assertion text for `RED`;
- test blob SHA, commit SHA, tree SHA, Python version, dependency versions;
- stdout/stderr SHA-256 and any warnings or limitations;
- `authority_effect: none`, `runtime_effect: none`, `canon_effect: none`, `admission_effect: none`, and `release_publication_effect: none`.
- truthful repository/provider effects separately: `repository_visibility: public_candidate`, plus the exact subset of `local_commit`, `git_push`, `draft_pr_create`, `draft_pr_update`, `ci_run`, and `ci_artifact_upload` that occurred. These effects never imply release publication or authority.

Tests and behavior capable of satisfying them must not first appear in the same commit. An importable stub or permissive harness may join the RED commit only when the preserved run proves it is incapable of passing the named behavioral assertions. Preserve that `RED` commit, then a `GREEN` implementation commit. If refactoring changes bytes, preserve a separate `REFACTOR` commit; otherwise record `refactor_commit_sha: null` and the fresh post-GREEN rerun. Push only after the green/refactor head is ready, retaining every RED commit in ancestry.

Every execution Bash shell, fenced command tranche, agent handoff, and reusable oracle must enter `set -euo pipefail` before doing work. No helper may rely on a caller's shell options. Do not invoke a mutating or validating helper in an `if`, `&&`, `||`, negation, or command-substitution context that suppresses `errexit`; functions that emit state set and export validated globals instead.

Task 6 must replay each Task 1–5 RED SHA and its GREEN/REFACTOR descendant in clean ephemeral worktrees; Task 8 must do the same for Task 7 before hashing the binding receipt. A valid RED imports and executes the intended harness, then fails the named behavioral acceptance assertion for the declared reason. An unexpected missing harness/module/dependency/input, syntax error, collection failure, timeout, or unrelated failure invalidates the cycle. An intentionally absent subject-under-test artifact is allowed only when the task names it in advance, the importable harness reaches the acceptance assertion, the structured missing-artifact finding is the asserted RED reason, all unrelated tests run, and replay proves the later implementation—not a test edit—resolves that same assertion. The replayed commands, outputs, exit codes, test IDs, tree/commit SHAs, and output digests become the durable TDD evidence; transient terminal logs do not become authority.

The RED commit freezes the behavioral test blobs. GREEN stages only implementation files that actually changed; it must verify every RED test blob SHA is unchanged. Editing a behavioral test after observed RED invalidates that cycle and requires a new RED commit/replay. The exact staged-set guard receives the phase-specific changed list, never every file named by the task.

## Standard Commit and Scope Guard

Run before every commit:

```bash
set -euo pipefail
verify_frozen_successor_approval
test "$(git rev-parse --abbrev-ref HEAD)" = "agent/quirk-applause-gate"
test -z "$(git diff --cached --name-only)"
git diff --exit-code 2cee4c829644133e0882a68656733222fa01c344 HEAD -- \
  .github/workflows/applause-gate-fixtures.yml \
  docs/superpowers/specs/2026-08-21-applause-gate-design.md \
  evals/applause-gate/cases.json \
  scripts/validate_applause_gate_fixtures.py \
  tests/test_applause_gate_fixtures.py
```

After staging the task’s exact files:

```bash
assert_staged_exact() {
  set -euo pipefail
  expected="$(printf '%s\n' "$@" | LC_ALL=C sort)"
  actual="$(git diff --cached --name-only | LC_ALL=C sort)"
  test "$actual" = "$expected"
  test -z "$(git diff --name-only)"
  test -z "$(git ls-files --others --exclude-standard)"
  for path in "$@"; do
    test "$(git ls-files --stage -- "$path" | wc -l)" -eq 1
    test "$(git ls-files --stage -- "$path" | awk '{print $1}')" = "100644"
    test "$(git cat-file -t ":$path")" = "blob"
  done
}
test -z "$(git diff --cached --name-only --diff-filter=DRTUXB)"
git diff --cached --check
git diff --cached --name-status
```

Invoke `assert_staged_exact` immediately after each `git add -- ...` with that phase's same complete path list. The implementer must stop on any extra, missing, unstaged, untracked, deleted, renamed, type-changed, conflicted, or whitespace-error path. At the start of every Task 1–8, before edits or tests, enter `set -euo pipefail`, re-declare the reusable guards, run `verify_frozen_successor_approval`, and require `test -z "$(git status --porcelain=v1)"` in the isolated implementation worktree. Task 0 establishes the frozen values and performs the equivalent initial guard. The Standard Commit and Scope Guard reruns approval freshness immediately before every RED, GREEN, REFACTOR, receipt, or package commit; a later edit/deletion/revocation or authority-watermark drift stops all further commits.

## Reusable Successor-Approval Freshness Guard

Task 0 freezes `PLAN_PR`, `PLAN_BRANCH`, `PLAN_SHA`, `PLAN_BLOB_SHA`, `GOLDEN_RUN_ID`, `GOLDEN_JOB_ID`, `GOLDEN_RUN_ATTEMPT`, and `APPROVAL_COMMENT_ID`; every later task receives those exact eight values from the Task 0 handoff and must not re-resolve or substitute a newer plan, run, job, or decision. Shell functions and variables are not assumed to survive an agent, process, or task boundary: re-declare this exact function in a fail-fast shell before each required invocation, then call it with the frozen values. A failed check is a revocation/drift stop, never a reason to refresh the values automatically. The successor decision is a closed, byte-exact record: extra prose, missing/duplicate fields, unknown authority keys, denial/revocation text, or any other byte fails equality.

```bash
verify_successor_approval() {
  set -euo pipefail
  expected_plan_sha="$1"
  expected_comment_id="$2"
  expected_plan_pr="$3"
  expected_plan_branch="$4"
  expected_plan_blob="$5"
  expected_run_id="$6"
  expected_job_id="$7"
  expected_run_attempt="$8"
  [[ "$expected_plan_sha" =~ ^[0-9a-f]{40}$ ]]
  [[ "$expected_comment_id" =~ ^[0-9]+$ ]]
  [[ "$expected_plan_pr" =~ ^[0-9]+$ ]]
  [[ "$expected_plan_blob" =~ ^[0-9a-f]{40}$ ]]
  [[ "$expected_run_id" =~ ^[0-9]+$ ]]
  [[ "$expected_job_id" =~ ^[0-9]+$ ]]
  [[ "$expected_run_attempt" =~ ^[1-9][0-9]*$ ]]
  test "$expected_plan_branch" = "agent/quirk-applause-gate-plan-v2"

  local plan_meta current_plan_sha issue_comments approval_matches approval_json latest_bryan_comment_id expected_body
  local expected_body_sha actual_body_sha
  local issue51_comments authority_json latest_issue51_bryan_id authority_body_sha run_json jobs_json job_json
  local plan_commit_json plan_commit_at authority_created_at run_created_at run_completed_at job_completed_at approval_created_at
  local plan_paths_text fixture_sha workflow_blob
  local -a plan_paths
  plan_meta="$(gh pr view "$expected_plan_pr" --repo Quirk-Systems/quirk-os \
    --json state,isDraft,baseRefName,baseRefOid,headRefName,headRefOid)"
  test "$(jq -r '.state' <<<"$plan_meta")" = "OPEN"
  test "$(jq -r '.isDraft' <<<"$plan_meta")" = "true"
  test "$(jq -r '.baseRefName' <<<"$plan_meta")" = "main"
  test "$(jq -r '.baseRefOid' <<<"$plan_meta")" = "7541767cc5d30fe9a101b9e1f7eff817b68aac9f"
  test "$(jq -r '.headRefName' <<<"$plan_meta")" = "$expected_plan_branch"
  current_plan_sha="$(jq -r '.headRefOid' <<<"$plan_meta")"
  test "$current_plan_sha" = "$expected_plan_sha"

  plan_paths_text="$(gh pr diff "$expected_plan_pr" \
    --repo Quirk-Systems/quirk-os --name-only)"
  test -n "$plan_paths_text"
  mapfile -t plan_paths <<<"$plan_paths_text"
  test "${#plan_paths[@]}" -eq 1
  test "${plan_paths[0]}" = \
    "docs/superpowers/plans/2026-08-21-applause-gate-implementation-plan.md"

  git cat-file -e "$expected_plan_sha^{commit}"
  test "$(git rev-parse "$expected_plan_sha:docs/superpowers/plans/2026-08-21-applause-gate-implementation-plan.md")" = \
    "$expected_plan_blob"
  test "$(git ls-tree "$expected_plan_sha" -- \
    docs/superpowers/plans/2026-08-21-applause-gate-implementation-plan.md | awk '{print $1 " " $2}')" = \
    "100644 blob"
  fixture_sha="$(git show \
    "$expected_plan_sha:evals/applause-gate/cases.json" | sha256sum | cut -d' ' -f1)"
  test "$fixture_sha" = \
    "987dab65550837b6abe2d5d820f4c6e5fbd8531b3e56f85e015d36c26b65be2f"
  workflow_blob="$(git rev-parse \
    "$expected_plan_sha:.github/workflows/golden-gates.yml")"
  test "$workflow_blob" = "4d4751ca21236828fe001977fe56be01365896cc"

  issue51_comments="$(gh api --paginate --slurp \
    repos/Quirk-Systems/quirk-os/issues/51/comments | jq 'add')"
  authority_json="$(jq '[.[] | select(.id == 5380917867) | select(.user.login == "bryansayler" and .user.id == 207279)]' \
    <<<"$issue51_comments")"
  test "$(jq 'length' <<<"$authority_json")" -eq 1
  authority_json="$(jq '.[0]' <<<"$authority_json")"
  test "$(jq -r '.created_at' <<<"$authority_json")" = \
    "$(jq -r '.updated_at' <<<"$authority_json")"
  authority_body_sha="$(jq -j '.body' <<<"$authority_json" | sha256sum | cut -d' ' -f1)"
  test "$authority_body_sha" = \
    "871a0d009bc9896c7421f1eed3dbebaead84f25eb97231c3c1c120ade81a26b0"
  latest_issue51_bryan_id="$(jq \
    '[.[] | select(.user.login == "bryansayler" and .user.id == 207279)] | max_by(.id).id' \
    <<<"$issue51_comments")"
  test "$latest_issue51_bryan_id" = "5380917867"

  run_json="$(gh api "repos/Quirk-Systems/quirk-os/actions/runs/$expected_run_id")"
  test "$(jq -r '.head_sha' <<<"$run_json")" = "$expected_plan_sha"
  test "$(jq -r '.head_branch' <<<"$run_json")" = "$expected_plan_branch"
  test "$(jq -r '.event' <<<"$run_json")" = "pull_request"
  test "$(jq -r '.path' <<<"$run_json")" = ".github/workflows/golden-gates.yml"
  test "$(jq -r '.name' <<<"$run_json")" = "Golden Gates"
  test "$(jq -r '.run_attempt' <<<"$run_json")" = "$expected_run_attempt"
  test "$(jq -r '.status' <<<"$run_json")" = "completed"
  test "$(jq -r '.conclusion' <<<"$run_json")" = "success"
  test "$(jq --argjson pr "$expected_plan_pr" \
    '[.pull_requests[] | select(.number == $pr)] | length' <<<"$run_json")" -eq 1
  jobs_json="$(gh api --paginate \
    "repos/Quirk-Systems/quirk-os/actions/runs/$expected_run_id/jobs?per_page=100" \
    --jq '.jobs[]' | jq -s)"
  test "$(jq 'length' <<<"$jobs_json")" -eq 1
  job_json="$(jq --argjson id "$expected_job_id" \
    '[.[] | select(.id == $id and .name == "structural-integrity")]' <<<"$jobs_json")"
  test "$(jq 'length' <<<"$job_json")" -eq 1
  job_json="$(jq '.[0]' <<<"$job_json")"
  test "$(jq -r '.head_sha' <<<"$job_json")" = "$expected_plan_sha"
  test "$(jq -r '.status' <<<"$job_json")" = "completed"
  test "$(jq -r '.conclusion' <<<"$job_json")" = "success"
  test "$(jq '[.steps[] | select(.name == "Validate Golden Project Pack" and .status == "completed" and .conclusion == "success")] | length' <<<"$job_json")" -eq 1
  test "$(jq '[.steps[] | select(.status != "completed" or .conclusion != "success")] | length' <<<"$job_json")" -eq 0

  issue_comments="$(gh api --paginate --slurp \
    repos/Quirk-Systems/quirk-os/issues/52/comments | jq 'add')"
  approval_matches="$(jq --arg sha "$expected_plan_sha" --argjson id "$expected_comment_id" \
    '[.[] | select(.id == $id) | select(.user.login == "bryansayler" and .user.id == 207279) | select(.body | contains("SUPERSEDE_ABG_03_EXECUTION_APPROVAL")) | select(.body | contains("plan_head: `" + $sha + "`"))]' \
    <<<"$issue_comments")"
  test "$(jq 'length' <<<"$approval_matches")" -eq 1
  approval_json="$(jq '.[0]' <<<"$approval_matches")"
  expected_body="$(cat <<EOF
SUPERSEDE_ABG_03_EXECUTION_APPROVAL
decision: \`APPROVE_ABG_03_PLAN\`
plan_pr: \`#$expected_plan_pr\`
plan_branch: \`$expected_plan_branch\`
plan_path: \`docs/superpowers/plans/2026-08-21-applause-gate-implementation-plan.md\`
plan_head: \`$expected_plan_sha\`
plan_blob: \`$expected_plan_blob\`
fixture_sha256: \`987dab65550837b6abe2d5d820f4c6e5fbd8531b3e56f85e015d36c26b65be2f\`
golden_gates_workflow: \`.github/workflows/golden-gates.yml\`
golden_gates_workflow_blob: \`4d4751ca21236828fe001977fe56be01365896cc\`
golden_gates_run: \`$expected_run_id\`
golden_gates_job: \`$expected_job_id\`
golden_gates_job_name: \`structural-integrity\`
golden_gates_run_attempt: \`$expected_run_attempt\`
golden_gates_event: \`pull_request\`
golden_gates_conclusion: \`success\`
execution_mode: \`Subagent-Driven\`
implementation_branch: \`agent/quirk-applause-gate\`
authorization_scope: \`later H0-B candidate implementation only\`
execution_in_this_turn: \`false\`
runtime_activation: \`forbidden\`
canon_promotion: \`forbidden\`
admission: \`forbidden\`
supabase_mutation: \`forbidden\`
plugin_or_submission_packaging: \`forbidden\`
openai_portal_action: \`forbidden\`
deployment: \`forbidden\`
release_publication: \`forbidden\`
merge_authorized: \`false\`
provider_ceiling: \`non-force implementation-branch pushes, PR CI artifacts, and one draft implementation PR metadata only\`
authority_watermark_comment: \`5380917867\`
authority_watermark_body_sha256: \`871a0d009bc9896c7421f1eed3dbebaead84f25eb97231c3c1c120ade81a26b0\`
superseded_execution_pr: \`#64\`
superseded_execution_grant_comment: \`5380917867\`
superseded_execution_head: \`50e3fb63abf64f91cbeeeb4bc8b4dff7ac2dba8c\`
superseded_execution_plan_blob: \`e287b41e7ee6d6586022bf0d4e0b79170a8c7702\`
superseded_execution_mode: \`INLINE_EXECUTION_WITH_TASK_GATES\`
authority_watermark_disposition: \`issue #51 comment 5380917867 is superseded in full and has no continuing execution force\`
pr64_disposition: \`PR #64, its branch, every existing or later commit, and all code, tests, receipts, CI, and evidence on it are excluded from this authorization\`
execution_origin_rule: \`agent/quirk-applause-gate must begin at plan_head; no PR #64 byte or evidence may be merged, cherry-picked, copied, or reused\`
reconciliation_evidence_pr: \`#64\`
reconciliation_evidence_head: \`50e3fb63abf64f91cbeeeb4bc8b4dff7ac2dba8c\`
reconciliation_artifact_path: \`docs/applause-gate/ABG-03-MERGE-RECONCILIATION.md\`
reconciliation_artifact_blob: \`e542f7687ab6024c57619fd813c778d7239af286\`
reconciliation_disposition: \`historical bytes only; not executable evidence under this approval\`
superseded_plan_head: \`d36b4582c752cdcd7542377054b286efbb203861\`
superseded_issue52_decision_comment: \`5380558390\`
h0_b_grant_comment: \`5379655626\`
invalidation_rule: \`any plan-content change invalidates this approval\`
EOF
)"
  test "$(jq -r '.body' <<<"$approval_json")" = "$expected_body"
  expected_body_sha="$(printf '%s' "$expected_body" | sha256sum | cut -d' ' -f1)"
  actual_body_sha="$(jq -j '.body' <<<"$approval_json" | sha256sum | cut -d' ' -f1)"
  test "$actual_body_sha" = "$expected_body_sha"
  test "$(jq -r '.created_at' <<<"$approval_json")" = \
    "$(jq -r '.updated_at' <<<"$approval_json")"
  approval_created_at="$(jq -r '.created_at' <<<"$approval_json")"
  authority_created_at="$(jq -r '.created_at' <<<"$authority_json")"
  run_created_at="$(jq -r '.created_at' <<<"$run_json")"
  run_completed_at="$(jq -r '.updated_at' <<<"$run_json")"
  job_completed_at="$(jq -r '.completed_at' <<<"$job_json")"
  plan_commit_json="$(gh api \
    "repos/Quirk-Systems/quirk-os/commits/$expected_plan_sha")"
  plan_commit_at="$(jq -r '.commit.committer.date' <<<"$plan_commit_json")"
  for timestamp in \
    "$plan_commit_at" "$authority_created_at" "$run_created_at" \
    "$run_completed_at" "$job_completed_at" "$approval_created_at"
  do
    test "$timestamp" != "null"
    jq -en --arg timestamp "$timestamp" \
      '$timestamp | fromdateiso8601 | type == "number"' >/dev/null
  done
  jq -en \
    --arg plan "$plan_commit_at" \
    --arg authority "$authority_created_at" \
    --arg run_start "$run_created_at" \
    --arg run_end "$run_completed_at" \
    --arg job_end "$job_completed_at" \
    --arg approval "$approval_created_at" \
    '($plan | fromdateiso8601) <= ($run_start | fromdateiso8601) and
     ($authority | fromdateiso8601) < ($approval | fromdateiso8601) and
     ($run_end | fromdateiso8601) <= ($approval | fromdateiso8601) and
     ($job_end | fromdateiso8601) <= ($approval | fromdateiso8601)' >/dev/null
  latest_bryan_comment_id="$(jq \
    '[.[] | select(.user.login == "bryansayler" and .user.id == 207279)] | max_by(.id).id' \
    <<<"$issue_comments")"
  test "$expected_comment_id" = "$latest_bryan_comment_id"

  test "$(git rev-parse --abbrev-ref HEAD)" = "agent/quirk-applause-gate"
  git merge-base --is-ancestor "$expected_plan_sha" HEAD
  git diff --exit-code "$expected_plan_sha" HEAD -- \
    docs/superpowers/plans/2026-08-21-applause-gate-implementation-plan.md
}

verify_frozen_successor_approval() {
  set -euo pipefail
  verify_successor_approval \
    "$PLAN_SHA" "$APPROVAL_COMMENT_ID" "$PLAN_PR" "$PLAN_BRANCH" \
    "$PLAN_BLOB_SHA" "$GOLDEN_RUN_ID" "$GOLDEN_JOB_ID" "$GOLDEN_RUN_ATTEMPT"
}
```

Invoke the guard immediately before every authority-bearing action named below, not merely once per task. No local commit, test result, reviewer verdict, receipt, successful check, or already-open provider object can waive it.

## Implementation-PR and H0-B CI Oracles

The implementation workflow has exact workflow name `Applause Gate Candidate Conformance`, path `.github/workflows/applause-gate-conformance.yml`, and sole job ID/name `applause-gate-candidate`. Its required named steps are `Assert exact PR head`, `Run Applause candidate verification`, `Sanitize candidate evidence`, and `Upload candidate evidence`. Branch protection currently supplies no useful required-check set, so “all required checks” is never an acceptance rule.

Re-declare these exact fail-closed functions in the current shell before use:

```bash
resolve_implementation_pr() {
  set -euo pipefail
  expected_head_sha="$1"
  [[ "$expected_head_sha" =~ ^[0-9a-f]{40}$ ]] || return 1
  local rows
  rows="$(gh pr list --repo Quirk-Systems/quirk-os --state open \
    --head agent/quirk-applause-gate \
    --json number,isDraft,baseRefName,headRefName,headRefOid)" || return 1
  test "$(jq 'length' <<<"$rows")" -eq 1 || return 1
  test "$(jq -r '.[0].isDraft' <<<"$rows")" = "true" || return 1
  test "$(jq -r '.[0].baseRefName' <<<"$rows")" = "main" || return 1
  test "$(jq -r '.[0].headRefName' <<<"$rows")" = \
    "agent/quirk-applause-gate" || return 1
  test "$(jq -r '.[0].headRefOid' <<<"$rows")" = \
    "$expected_head_sha" || return 1
  IMPLEMENTATION_PR="$(jq -r '.[0].number' <<<"$rows")" || return 1
  [[ "$IMPLEMENTATION_PR" =~ ^[1-9][0-9]*$ ]] || return 1
  export IMPLEMENTATION_PR
}

inspect_pre_push_implementation_target() {
  set -euo pipefail
  new_head_sha="$1"
  presence="$2"
  [[ "$new_head_sha" =~ ^[0-9a-f]{40}$ ]]
  test "$presence" = "optional" -o "$presence" = "required"
  local rows remote_sha pr_sha
  rows="$(gh pr list --repo Quirk-Systems/quirk-os --state open \
    --head agent/quirk-applause-gate \
    --json number,state,isDraft,baseRefName,headRefName,headRefOid)"
  test "$(jq 'length' <<<"$rows")" -le 1
  PRE_PUSH_PR_COUNT="$(jq 'length' <<<"$rows")"
  if test "$PRE_PUSH_PR_COUNT" -eq 1; then
    test "$(jq -r '.[0].state' <<<"$rows")" = "OPEN"
    test "$(jq -r '.[0].isDraft' <<<"$rows")" = "true"
    test "$(jq -r '.[0].baseRefName' <<<"$rows")" = "main"
    test "$(jq -r '.[0].headRefName' <<<"$rows")" = "agent/quirk-applause-gate"
    pr_sha="$(jq -r '.[0].headRefOid' <<<"$rows")"
  else
    test "$presence" = "optional"
    pr_sha=""
  fi
  remote_sha="$(git ls-remote --heads origin \
    refs/heads/agent/quirk-applause-gate | awk '{print $1}')"
  if test -n "$pr_sha"; then
    test "$remote_sha" = "$pr_sha"
  fi
  if test -n "$remote_sha"; then
    [[ "$remote_sha" =~ ^[0-9a-f]{40}$ ]]
    git fetch --no-tags origin "$remote_sha"
    git merge-base --is-ancestor "$remote_sha" "$new_head_sha"
  fi
  PRE_PUSH_REMOTE_SHA="$remote_sha"
  export PRE_PUSH_PR_COUNT PRE_PUSH_REMOTE_SHA
}

verify_h0b_ci() {
  set -euo pipefail
  expected_head_sha="$1"
  [[ "$expected_head_sha" =~ ^[0-9a-f]{40}$ ]]
  [[ "$IMPLEMENTATION_PR" =~ ^[1-9][0-9]*$ ]]
  local runs run jobs job
  runs="$(gh api --paginate \
    'repos/Quirk-Systems/quirk-os/actions/workflows/applause-gate-conformance.yml/runs?event=pull_request&branch=agent%2Fquirk-applause-gate&per_page=100' \
    --jq '.workflow_runs[]' | jq -s --arg sha "$expected_head_sha" \
      '[.[] | select(.head_sha == $sha and .event == "pull_request" and .path == ".github/workflows/applause-gate-conformance.yml" and .name == "Applause Gate Candidate Conformance")]')"
  test "$(jq 'length' <<<"$runs")" -eq 1
  run="$(jq '.[0]' <<<"$runs")"
  test "$(jq -r '.status' <<<"$run")" = "completed"
  test "$(jq -r '.conclusion' <<<"$run")" = "success"
  test "$(jq --argjson pr "$IMPLEMENTATION_PR" \
    '[.pull_requests[] | select(.number == $pr)] | length' <<<"$run")" -eq 1
  test "$(jq '.pull_requests | length' <<<"$run")" -eq 1
  [[ "$(jq -r '.run_attempt' <<<"$run")" =~ ^[1-9][0-9]*$ ]]
  CI_RUN_ID="$(jq -r '.id' <<<"$run")"
  CI_WORKFLOW_ID="$(jq -r '.workflow_id' <<<"$run")"
  CI_RUN_ATTEMPT="$(jq -r '.run_attempt' <<<"$run")"

  jobs="$(gh api --paginate \
    "repos/Quirk-Systems/quirk-os/actions/runs/$CI_RUN_ID/jobs?per_page=100" \
    --jq '.jobs[]' | jq -s)"
  test "$(jq 'length' <<<"$jobs")" -eq 1
  job="$(jq '[.[] | select(.name == "applause-gate-candidate")]' <<<"$jobs")"
  test "$(jq 'length' <<<"$job")" -eq 1
  job="$(jq '.[0]' <<<"$job")"
  test "$(jq -r '.head_sha' <<<"$job")" = "$expected_head_sha"
  test "$(jq -r '.status' <<<"$job")" = "completed"
  test "$(jq -r '.conclusion' <<<"$job")" = "success"
  for step in \
    "Assert exact PR head" \
    "Run Applause candidate verification" \
    "Sanitize candidate evidence" \
    "Upload candidate evidence"
  do
    test "$(jq --arg step "$step" \
      '[.steps[] | select(.name == $step and .status == "completed" and .conclusion == "success")] | length' \
      <<<"$job")" -eq 1
  done
  test "$(jq '[.steps[] | select(.status != "completed" or .conclusion != "success")] | length' \
    <<<"$job")" -eq 0
  CI_JOB_ID="$(jq -r '.id' <<<"$job")"
  export CI_RUN_ID CI_WORKFLOW_ID CI_RUN_ATTEMPT CI_JOB_ID
}
```

Missing, duplicate, wrong-head, wrong-event, wrong-path, wrong-name, pending, neutral, skipped, cancelled, stale, action-required, or failed runs/jobs/steps stop the tranche. Each receipt and the PR evidence projection bind the four emitted CI identities plus the workflow path/name, job name, event, and exact head SHA.

---

### Task 0: Approval, ancestry, privacy, and scope preflight

**Files:** None.

**Interfaces:**
- Consumes: the uniquely resolved clean successor draft PR, its Bryan-authored successor decision on issue #52, immutable H0-A SHA, authorized implementation branch, and current repository state.
- Produces: `H0B-PREFLIGHT-PASS` terminal evidence only; no file or provider mutation.

- [ ] **Step 1: Resolve the exact successor approval independently of mutable PR prose**

Run:

```bash
PLAN_BRANCH="agent/quirk-applause-gate-plan-v2"
PLAN_ROWS="$(gh pr list --repo Quirk-Systems/quirk-os --state open --base main \
  --head "$PLAN_BRANCH" --json number,isDraft,baseRefName,baseRefOid,headRefName,headRefOid)"
test "$(jq 'length' <<<"$PLAN_ROWS")" -eq 1
PLAN_PR="$(jq -r '.[0].number' <<<"$PLAN_ROWS")"
PLAN_META="$(gh pr view "$PLAN_PR" --repo Quirk-Systems/quirk-os --json state,isDraft,baseRefName,baseRefOid,headRefName,headRefOid)"
PLAN_SHA="$(jq -r '.headRefOid' <<<"$PLAN_META")"
test "${#PLAN_SHA}" -eq 40
PLAN_BLOB_SHA="$(git rev-parse "$PLAN_SHA:docs/superpowers/plans/2026-08-21-applause-gate-implementation-plan.md")"

ISSUE_COMMENTS="$(gh api --paginate --slurp repos/Quirk-Systems/quirk-os/issues/52/comments | jq 'add')"
APPROVAL_MATCHES="$(jq --arg sha "$PLAN_SHA" \
  '[.[] | select(.user.login == "bryansayler" and .user.id == 207279) | select(.body | contains("SUPERSEDE_ABG_03_EXECUTION_APPROVAL")) | select(.body | contains("plan_head: `" + $sha + "`"))]' <<<"$ISSUE_COMMENTS")"
test "$(jq 'length' <<<"$APPROVAL_MATCHES")" -eq 1
APPROVAL_JSON="$(jq '.[0]' <<<"$APPROVAL_MATCHES")"
APPROVAL_COMMENT_ID="$(jq -r '.id' <<<"$APPROVAL_JSON")"
test "$APPROVAL_COMMENT_ID" != "null"
GOLDEN_RUN_ID="$(jq -r '.body | capture("(?m)^golden_gates_run: `(?<v>[0-9]+)`$").v' <<<"$APPROVAL_JSON")"
GOLDEN_JOB_ID="$(jq -r '.body | capture("(?m)^golden_gates_job: `(?<v>[0-9]+)`$").v' <<<"$APPROVAL_JSON")"
GOLDEN_RUN_ATTEMPT="$(jq -r '.body | capture("(?m)^golden_gates_run_attempt: `(?<v>[1-9][0-9]*)`$").v' <<<"$APPROVAL_JSON")"
verify_successor_approval \
  "$PLAN_SHA" "$APPROVAL_COMMENT_ID" "$PLAN_PR" "$PLAN_BRANCH" \
  "$PLAN_BLOB_SHA" "$GOLDEN_RUN_ID" "$GOLDEN_JOB_ID" "$GOLDEN_RUN_ATTEMPT"
test "$(git rev-parse HEAD)" = "$PLAN_SHA"
```

Expected: all commands exit 0. PR body fields may mirror the decision for discoverability but cannot satisfy this gate. Any mismatch, missing/edited decision, changed plan byte, non-draft state, or head drift stops execution.

- [ ] **Step 2: Verify repository, branch, predecessor, dependency lock, and clean state**

Run:

```bash
test "$(git remote get-url origin)" = "https://github.com/Quirk-Systems/quirk-os.git"
test "$(git rev-parse --abbrev-ref HEAD)" = "agent/quirk-applause-gate"
git merge-base --is-ancestor 2cee4c829644133e0882a68656733222fa01c344 HEAD
git merge-base --is-ancestor 7541767cc5d30fe9a101b9e1f7eff817b68aac9f "$PLAN_SHA"
test -z "$(git status --porcelain=v1)"
test "$(git rev-parse 2cee4c829644133e0882a68656733222fa01c344:requirements-evals.txt)" = "083ac9bf8d74939d8286549caaebf0626e7d51ec"
```

Expected: all commands exit 0. No dependency-file modification or acquisition beyond installing this exact lock is permitted.

- [ ] **Step 3: Verify immutable H0-A bytes and protected shared paths**

Run the immutable-path command in the Standard Commit and Scope Guard. Then run:

```bash
git diff --exit-code "$PLAN_SHA" HEAD -- \
  docs/superpowers/plans/2026-08-21-applause-gate-implementation-plan.md \
  skills \
  evals/skills \
  schemas/skill-package.schema.json \
  scripts/validate_skills.py \
  tests/test_skill_runtime.py \
  scripts/sync_control_plane
```

Expected: no output and exit 0.

- [ ] **Step 4: Record the preflight result without mutation**

Run:

```bash
printf '%s\n' "H0B-PREFLIGHT-PASS plan=$PLAN_SHA approval_comment=$APPROVAL_COMMENT_ID mode=Subagent-Driven branch=agent/quirk-applause-gate predecessor=2cee4c829644133e0882a68656733222fa01c344"
```

Reviewer gate: a distinct reviewer confirms the approval binding, immutable inputs, exact branch, clean state, and protected paths before Task 1.

---

### Task 1: Closed request and review schema

**Files:**
- Create: `schemas/applause-review.schema.json`
- Create: `examples/applause-gate/applause-review.valid.json`
- Create: `scripts/applause_gate/json_io.py`
- Create: `tests/test_applause_gate_schema.py`

**Interfaces:**
- Consumes: six locked verdicts and typed diagnostic dimensions from H0-A.
- Produces: Draft 2020-12 `$defs.review_request`, `$defs.applause_review`, `load_json_strict(text: str) -> Any`, and strict schema-validation tests.

The request contract requires: `object_type`, `schema_version`, `request_id`, `candidate_id`, `subject`, `claim`, `signal`, `evaluated_version`, `observation_window`, `evidence_assessments`, `primary_outcome_state`, `causal_support`, `guardrail_state`, `contradiction_state`, `version_binding`, `freshness_state`, `integrity_state`, and `commitment_risk`.

The schema document itself requires top-level annotations `x-quirk-status: candidate`, `x-quirk-semantic-authority: false`, `x-quirk-runtime-authority: false`, and `x-quirk-canon-effect: none`. Tests prove schema validity, path location, or conformance cannot be interpreted as admission, runtime discovery, or Canon.

Each evidence assessment requires: `evidence_ref`, `evidence_kind`, `assertion_state`, `version_ref`, `content_digest`, and `integrity_state`. Reference presence alone never means verified support.
`evidence_ref` is a semantic identity key: two assessments with the same ref are invalid even when their other fields differ. Validate this before normalization/classification and test conflicting duplicates explicitly; `uniqueItems: true` alone is insufficient.

The review contract requires request identity plus two distinct hashes: `request_payload_sha256` over the complete validated request after schema-declared set normalization for replay/identity, and `diagnostic_facts_sha256` over only the declared decision-driving facts for oracle/metadata invariance. It also requires the diagnostic states, exact verdict, sorted `required_codes`, `withheld_claims`, `missing_proof`, preserved contradiction refs, supplied evidence refs, warnings, and a structured `next_move`.

`next_move.kind` is limited to `request_evidence`, `record_candidate_evidence`, `defer_for_review`, or `propose_reversible_test`; `execution_authorized` is always `false`. The review requires all five semantic effects to be `none`: authority, runtime, Canon, admission, and release publication. Provider/repository effects belong only in evidence envelopes, never classifier output.

- [ ] **Step 1: Create an importable permissive schema harness and table-driven tests**

The red harness defines both `$defs` as open objects and uses a permissive JSON-loader stub. Tests must cover the four exact candidate/non-authority schema annotations, one valid request/review, and mutations for every required field, enum, type, closed-object boundary, empty/duplicate reference list, malformed digest, wrong candidate/schema version, scalar success score, forbidden execution/provider/admission field, non-`none` effect, and executable next move. Loader tests must reject duplicate keys and literal `NaN`, `Infinity`, and `-Infinity` before schema validation.

- [ ] **Step 2: Run and preserve behavioral RED**

Run:

```bash
PYTHONPATH=scripts python -m unittest tests/test_applause_gate_schema.py -v
```

Expected: tests import successfully; the valid examples pass; rejection assertions fail because the permissive harness accepts invalid mutations. Preserve the RED commit and receipt.

Stage exactly the permissive schema, examples, and tests, then commit the executable RED harness:

```bash
git add -- \
  schemas/applause-review.schema.json \
  examples/applause-gate/applause-review.valid.json \
  scripts/applause_gate/json_io.py \
  tests/test_applause_gate_schema.py
assert_staged_exact \
  schemas/applause-review.schema.json \
  examples/applause-gate/applause-review.valid.json \
  scripts/applause_gate/json_io.py \
  tests/test_applause_gate_schema.py
git commit -m "test: add failing applause review contract tests"
```

- [ ] **Step 3: Implement the minimal closed schema and valid example**

Use `additionalProperties: false` at every object boundary, `minLength: 1`, `minItems: 1`, `uniqueItems: true` for set-like arrays, exact enums/consts, 64-lowercase-hex digest patterns, and explicit required arrays. Implement one strict JSON loader with an `object_pairs_hook` that rejects duplicate keys and `parse_constant` that rejects `NaN`, `Infinity`, and `-Infinity`; every H0-B JSON input goes through it before schema validation. Output serialization uses `allow_nan=False`; no success score exists.

Declare the complete normalization contract with schema extension `x-quirk-set-like: true`: request pointer `/evidence_assessments`, sorted by `(evidence_ref, evidence_kind, content_digest)`; review pointers `/required_codes`, `/withheld_claims`, `/missing_proof`, `/contradiction_refs`, `/evidence_refs`, and `/warnings`, each sorted by UTF-8 string bytes. No other array is unordered, and every declared set-like array must also use `uniqueItems: true`.

- [ ] **Step 4: Run GREEN and REFACTOR verification**

Run:

```bash
PYTHONPATH=scripts python -m unittest tests/test_applause_gate_schema.py -v
python -m unittest tests/test_applause_gate_fixtures.py -v
```

Expected: all selected tests pass with zero skips.

- [ ] **Step 5: Stage exactly and commit**

Freeze the RED test blob, stage only the schema and strict-loader implementations that changed, verify the phase-specific staged set, and commit:

```bash
RED_TEST_BLOB="$(git rev-parse HEAD:tests/test_applause_gate_schema.py)"
test "$(git hash-object tests/test_applause_gate_schema.py)" = "$RED_TEST_BLOB"
git add -- \
  schemas/applause-review.schema.json \
  scripts/applause_gate/json_io.py
assert_staged_exact schemas/applause-review.schema.json scripts/applause_gate/json_io.py
git commit -m "feat: add closed applause review contract"
```

Reviewer gate: schema completeness, request/review separation, closed effects, and no classifier behavior.

---

### Task 2: Oracle-free H0-A request projection

**Files:**
- Create: `evals/applause-gate/h0-b-requests.json`
- Create: `evals/applause-gate/h0-b-assertions.json`
- Create: `scripts/applause_gate/fixture_projection.py`
- Create: `tests/test_applause_gate_projection.py`

**Interfaces:**
- Consumes during authoring/review: immutable H0-A `cases.json` plus the request `$def` from Task 1.
- Consumes at runtime: only `h0-b-requests.json`; the loader is forbidden from opening H0-A cases or H0-B assertions.
- Produces: `load_request_projection(repo: Path) -> dict[str, dict]` and a physically separate evaluation-only assertion oracle keyed by correlation ID.

The request file contains the immutable predecessor SHA, exact raw fixture SHA-256, exactly 19 opaque correlations, and typed request objects. The assertion file contains expected verdicts, required/prohibited finding codes, and preserved-behavior checks. Only the conformance harness reads assertions, and only after classification.

The request object must not contain `id`, `case_id`, `kind`, `scenario`, `expected`, `required_behaviors`, `prohibited_behaviors`, or verdict labels. The outer harness attaches `case_id` only after classification.

- [ ] **Step 1: Write projection leakage and lineage tests against incapable empty artifacts**

Create an empty request projection, an empty closed assertion placeholder containing no case, verdict, behavior, or finding-code value, an importable loader, and tests split into `ProjectionIsolationTests` and `AssertionSeparationTests`. The placeholder exists only so the full RED suite never fails on a missing input; it is incapable of satisfying any acceptance assertion and is not the separately authored oracle. Projection tests require 19 unique correlations, schema-valid typed requests, exact source SHA binding, no forbidden oracle keys or verdict tokens at any request depth, and no reads of `cases.json` or `h0-b-assertions.json`.

Metamorphic families must mutate every H0-A `id`, `kind`, `scenario`, `expected`, `required_behaviors`, and `prohibited_behaviors` value; permute case order; rewrite every assertion byte; and rename correlation metadata while holding typed observation facts fixed. Every mutation must leave canonical request bytes identical. A second family alpha-renames opaque evidence-reference IDs consistently and requires the non-reference facts to remain identical. This proves structural separation; it does not substitute for independent human review of whether a typed fact secretly encodes the answer.

- [ ] **Step 2: Run and preserve behavioral RED**

Run:

```bash
PYTHONPATH=scripts python -m unittest tests/test_applause_gate_projection.py -v
```

Expected: imports and every input load succeed; named projection-coverage and assertion-binding acceptance tests fail only because the request projection and assertion placeholder are structurally empty. No missing-file/input failure qualifies. Preserve the exact failing test IDs/findings in the RED commit and receipt.

Stage exactly the empty request file, empty assertion placeholder, loader, and test, then commit the executable RED harness:

```bash
git add -- \
  evals/applause-gate/h0-b-requests.json \
  evals/applause-gate/h0-b-assertions.json \
  scripts/applause_gate/fixture_projection.py \
  tests/test_applause_gate_projection.py
assert_staged_exact \
  evals/applause-gate/h0-b-requests.json \
  evals/applause-gate/h0-b-assertions.json \
  scripts/applause_gate/fixture_projection.py \
  tests/test_applause_gate_projection.py
git commit -m "test: add failing oracle-isolation projection tests"
```

- [ ] **Step 3: Add typed requests without populating the assertion oracle**

Translate H0-A narrative observations into explicit diagnostic states without copying expected verdicts or behavior prescriptions into requests. Preserve contradictions, affected segments, comparison windows, version state, evidence integrity, and missing proof as typed facts. Run only `ProjectionIsolationTests`; then stage exactly the request file and loader changes and commit:

```bash
PYTHONPATH=scripts python -m unittest tests.test_applause_gate_projection.ProjectionIsolationTests -v
RED_TEST_BLOB="$(git rev-parse HEAD:tests/test_applause_gate_projection.py)"
test "$(git hash-object tests/test_applause_gate_projection.py)" = "$RED_TEST_BLOB"
git add -- evals/applause-gate/h0-b-requests.json scripts/applause_gate/fixture_projection.py
assert_staged_exact evals/applause-gate/h0-b-requests.json scripts/applause_gate/fixture_projection.py
git commit -m "feat: add oracle-isolated applause request facts"
```

- [ ] **Step 4: Have a distinct reviewer replace the empty placeholder with the assertion oracle**

The reviewer reads H0-A expectations and writes only `evals/applause-gate/h0-b-assertions.json`. They must not edit requests, loader, or projection tests. The file binds the exact request-file digest and uses closed objects. Stage exactly that file and commit:

```bash
git add -- evals/applause-gate/h0-b-assertions.json
assert_staged_exact evals/applause-gate/h0-b-assertions.json
git commit -m "test: add separately authored applause assertions"
```

- [ ] **Step 5: Run GREEN, schema validation, and oracle metamorphics**

Run:

```bash
PYTHONPATH=scripts python -m unittest tests/test_applause_gate_projection.py -v
PYTHONPATH=scripts python -m unittest tests/test_applause_gate_schema.py -v
```

Expected: 19 projections validate; the forbidden-key/token scan is empty; all oracle/correlation mutations leave request bytes unchanged; the assertion file binds the exact request digest; H0-A raw bytes, candidate version, exact closed `expected` objects, case payload digest, evidence-ref types, and 5/3/11 counts pass the stricter H0-B overlay.

Reviewer gate: independently compare all 19 projections with H0-A narratives and reject any expected-verdict encoding.

---

### Task 3: Pure fact-based classifier

**Files:**
- Create: `scripts/applause_gate/__init__.py`
- Create: `scripts/applause_gate/canonical.py`
- Create: `scripts/applause_gate/classifier.py`
- Create: `tests/test_applause_gate_classifier.py`
- Create: `tests/test_applause_gate_purity.py`

**Interfaces:**
- Consumes: one schema-valid `review_request` containing typed facts only.
- Produces: `canonical_json_bytes(value: JSONValue) -> bytes`, `sha256_bytes(value: bytes) -> str`, `request_payload_digest(request: dict[str, JSONValue]) -> str`, `diagnostic_facts_digest(request: dict[str, JSONValue]) -> str`, `classify_review_request(request: dict[str, JSONValue]) -> dict[str, JSONValue]`, or deterministic `InvalidReviewRequest` with sorted error codes.

`JSONValue` is recursively restricted to exact built-in `dict`, `list`, `str`, finite `int`/`float` (excluding `bool` as a number), `bool`, or `None`; subclasses, custom mappings/sequences, lazy values, and non-finite numbers are rejected before deep copy or field access. Normal entry is a value materialized by `load_json_strict`; direct callers receive the same recursive type gate.

Decision precedence is exact:

1. `EVIDENCE_INTEGRITY_FAILURE` for tampered, leaked/reused holdout, revoked, stale/wrong-version, or digest/lineage mismatch evidence.
2. `FALSE_POSITIVE` when the declared primary outcome is contradicted by proxy substitution, selected-window reversal, survivorship/population distortion, or equivalent typed facts.
3. `UNRESOLVED` for material guardrail harm, contradiction, multiplicity, segment harm, incomplete causal support combined with a success claim, or social commitment pressure.
4. `SIGNAL_ONLY` when change is visible but outcome, causality, durability, or guardrails remain unsupported.
5. `SUPPORTED_DIAGNOSIS` when explanation and bounded causal support exist but the full success contract is incomplete.
6. `VERIFIED_SUCCESS` only when the declared primary outcome, valid comparison, causal support, evaluated version, current freshness, complete observation window, and all declared guardrails are supported with no higher-precedence condition.

Validate uniqueness before construction. Outputs sort only explicitly enumerated set-like fields and preserve every supplied contradiction/evidence reference without inventing or deduplicating references. `request_id` is copied only for correlation and never affects diagnostic fields.

`request_payload_digest` hashes the complete schema-valid request after a schema-guided constructor applies the exact JSON-Pointer/sort-key contract from Task 1; `uniqueItems: true` alone never authorizes reordering. Generic canonical JSON never reorders arrays, and any unlisted array retains order. Task 5 separately binds the raw request/assertion file bytes, so normalization cannot hide source drift. `diagnostic_facts_digest` hashes only these decision-driving fields: `observation_window` facts; each evidence assessment's `evidence_kind`, `assertion_state`, and `integrity_state`; `primary_outcome_state`; `causal_support`; `guardrail_state`; `contradiction_state`; `version_binding`; `freshness_state`; top-level `integrity_state`; and `commitment_risk`. It excludes request/candidate IDs, claim/signal prose, correlation IDs, evidence refs, version refs, and content digests. Constructors validate and explicitly sort the evidence-fact multiset before hashing; the classifier may branch only on this declared projection.

- [ ] **Step 1: Create an importable fail-closed stub and one failing test per rule family**

The stub returns a schema-valid `UNRESOLVED` review. Tests cover each verdict, all higher/lower precedence pairs, evidence-ref non-fabrication, authority effects, and one-fact flips.

- [ ] **Step 2: Run and preserve behavioral RED**

Run:

```bash
PYTHONPATH=scripts python -m unittest tests/test_applause_gate_classifier.py -v
PYTHONPATH=scripts python -m unittest tests/test_applause_gate_purity.py -v
```

Expected: imports and schema checks succeed; verdict assertions fail against the fail-closed stub. Preserve the RED commit and receipt.

Stage exactly the five Task 3 paths and commit the executable RED harness:

```bash
git add -- \
  scripts/applause_gate/__init__.py \
  scripts/applause_gate/canonical.py \
  scripts/applause_gate/classifier.py \
  tests/test_applause_gate_classifier.py \
  tests/test_applause_gate_purity.py
assert_staged_exact \
  scripts/applause_gate/__init__.py \
  scripts/applause_gate/canonical.py \
  scripts/applause_gate/classifier.py \
  tests/test_applause_gate_classifier.py \
  tests/test_applause_gate_purity.py
git commit -m "test: add failing pure-classifier contract"
```

- [ ] **Step 3: Implement the precedence table and canonical review construction**

Use request facts only. The scanned transitive closure is `applause_gate/__init__.py`, `classifier.py`, and `canonical.py`, because package initialization executes first. `__init__.py` may contain only pure relative symbol exports; `classifier.py` may import only `copy`, `typing`, and `.canonical`; `canonical.py` may import only `hashlib`, `json`, and `typing`. Reject other relative imports, dynamic imports, `open`, `input`, `eval`, `exec`, `compile`, mutable module caches, and imports of fixture/schema, OS/environment, clock/random, networking, subprocess, database, model, or provider modules.

- [ ] **Step 4: Prove purity dynamically and statically**

Purity tests require:

- input deep copy unchanged;
- custom/lazy mapping, sequence, scalar subclasses, and non-finite numbers are rejected before any user-defined method can run;
- no output aliases to input;
- mutating one result cannot affect another;
- repeated and interleaved calls are byte-identical;
- renamed request/correlation metadata changes `request_payload_sha256` but not `diagnostic_facts_sha256` or diagnostic output;
- malformed or unknown facts fail closed deterministically;
- identical or conflicting duplicate `evidence_ref` identities fail closed before hashing or precedence evaluation;
- static import allowlist passes;
- a clean subprocess installs the audit hook before importing `applause_gate`; during import it permits only interpreter import-machinery reads for the exact transitive module allowlist and declared standard-library modules, then switches to zero-I/O before classification. Any other filesystem, environment, clock, randomness, socket, subprocess, database, or model access fails;
- classifier execution succeeds in a temporary tree containing only the typed request, with H0-A cases and H0-B assertions absent;
- mutations to every oracle/behavior/fixture identifier and every assertion byte leave canonical diagnostic fields byte-identical;
- consistent alpha-renaming of opaque evidence refs changes `request_payload_sha256` and correlation/reference fields, but never `diagnostic_facts_sha256`, verdict, codes, missing-proof categories, effects, or next-move kind.

- [ ] **Step 5: Run GREEN and REFACTOR verification**

Run:

```bash
PYTHONPATH=scripts python -m unittest tests/test_applause_gate_classifier.py -v
PYTHONPATH=scripts python -m unittest tests/test_applause_gate_purity.py -v
PYTHONPATH=scripts python -m unittest tests/test_applause_gate_projection.py -v
```

Expected: all selected tests pass with zero skips.

- [ ] **Step 6: Stage exactly and commit GREEN**

Freeze both RED test blobs, stage only the three implementation paths that changed, verify the phase-specific staged set, and commit:

```bash
RED_CLASSIFIER_TEST_BLOB="$(git rev-parse HEAD:tests/test_applause_gate_classifier.py)"
RED_PURITY_TEST_BLOB="$(git rev-parse HEAD:tests/test_applause_gate_purity.py)"
test "$(git hash-object tests/test_applause_gate_classifier.py)" = "$RED_CLASSIFIER_TEST_BLOB"
test "$(git hash-object tests/test_applause_gate_purity.py)" = "$RED_PURITY_TEST_BLOB"
git add -- \
  scripts/applause_gate/__init__.py \
  scripts/applause_gate/canonical.py \
  scripts/applause_gate/classifier.py
assert_staged_exact \
  scripts/applause_gate/__init__.py \
  scripts/applause_gate/canonical.py \
  scripts/applause_gate/classifier.py
git commit -m "feat: add pure applause evidence classifier"
```

Reviewer gate: rule semantics, precedence, purity proof, oracle-key absence, evidence preservation, and no authority language.

---

### Task 4: Case-level conformance and critical mutation proof

**Files:**
- Create: `scripts/validate_applause_gate.py`
- Create: `tests/test_applause_gate_conformance.py`
- Create: `.github/workflows/applause-gate-conformance.yml`

**Interfaces:**
- Consumes: immutable H0-A expectations, typed requests, evaluation-only assertions, schema, and pure classifier.
- Produces: `validate(repo: Path) -> dict[str, Any]` with case-level records and independently verifiable aggregates.

Each case record includes actual/expected verdict, actual/required/prohibited codes, preserved contradiction refs, missing proof, withheld claims, evidence refs, schema errors, and effect fields.

Counters are defined exactly:

- `false_verified_success_count`: negative/adversarial H0-A case classified `VERIFIED_SUCCESS`.
- `fabricated_evidence_count`: emitted evidence ref absent from the request evidence-assessment IDs.
- `authority_smuggling_count`: any non-`none` effect, `execution_authorized != false`, or next-move kind outside the closed candidate enum.
- `schema_error_count`: total review-schema errors.
- `expectation_mismatch_count`: verdict or required/prohibited code mismatch.

- [ ] **Step 1: Write runner tests against an importable intentionally incomplete report**

Tests independently recompute every aggregate from case records and reject a hard-coded PASS. Add injected critical mutations: wrong verdict, fabricated evidence ref, removed contradiction, schema-invalid output, executable next move, weakened effect, and reordered case/result data.

- [ ] **Step 2: Run and preserve behavioral RED**

Run:

```bash
PYTHONPATH=scripts python -m unittest tests/test_applause_gate_conformance.py -v
```

Expected: import succeeds; aggregate and mutation assertions fail against the incomplete runner. Preserve the RED commit and receipt.

Stage exactly the incomplete runner and conformance test, then commit the executable RED harness:

```bash
git add -- scripts/validate_applause_gate.py tests/test_applause_gate_conformance.py
assert_staged_exact scripts/validate_applause_gate.py tests/test_applause_gate_conformance.py
git commit -m "test: add failing applause conformance gate"
```

- [ ] **Step 3: Implement case-level validation and fail-closed CLI**

CLI flags are `--repo`, `--output`, and `--require-pass`. `--require-pass` returns nonzero on any counter, mismatch, missing case, duplicate case, altered count, warning classified as blocking, or immutable fixture digest mismatch.

- [ ] **Step 4: Add PR-only CI**

Workflow requirements:

- set top-level `name: Applause Gate Candidate Conformance`; define exactly one job with both job ID and `name` equal to `applause-gate-candidate`;
- trigger only on `pull_request` paths for the exact H0-B allowlist; no `workflow_dispatch`, schedule, or `pull_request_target`;
- `permissions: contents: read`; no secrets or environments;
- checkout `${{ github.event.pull_request.head.sha }}` with a separately pinned action SHA and `persist-credentials: false`, then in the required step named `Assert exact PR head` require `git rev-parse HEAD` to equal that event head SHA; never bind evidence to the synthetic `${{ github.sha }}` merge ref;
- setup Python/action SHAs pinned;
- install exact unmodified `requirements-evals.txt`;
- in one required step named `Run Applause candidate verification`, run all Applause tests with `PYTHONPATH=scripts`, the immutable H0-A validator, the H0-B validator, and, once it exists, the quarantined-package validator;
- in a required step named `Sanitize candidate evidence`, fail closed unless the report has only the public-safe allowlist below; never copy raw command output into the artifact directory;
- name reports/artifacts with `${{ github.event.pull_request.head.sha }}` and retain them 30 days;
- upload only the sanitized directory in a required step named `Upload candidate evidence` using an exact pinned upload-action SHA and `if: success()`;
- upload only this closed field allowlist: correlation/case ID, verdict, finding codes, aggregate counts, source/payload/receipt digests, semantic effects, repository visibility, and provider-effect names;
- forbid subject, claim, signal, raw evidence, evidence bodies, request objects, environment values, stdout/stderr bodies, secrets, personal data, and held-out material. Every committed fixture is synthetic and public-safe.

- [ ] **Step 5: Run GREEN, mutation proof, and repository-native tests**

Run:

```bash
PYTHONPATH=scripts python -m unittest tests/test_applause_gate_conformance.py -v
PYTHONPATH=scripts python -m unittest discover -s tests -p 'test_applause_gate_*.py' -v
PYTHONPATH=scripts python scripts/validate_applause_gate_fixtures.py --repo . --require-pass
PYTHONPATH=scripts python scripts/validate_applause_gate.py --repo . --require-pass
```

Expected: all commands exit 0; 19 case records; counts 5/3/11; every critical mutation is killed; all five failure counters are zero on the unmutated candidate.

- [ ] **Step 6: Stage exactly and commit**

Freeze the RED conformance-test blob, stage only the runner and new workflow, verify the phase-specific staged set, and commit:

```bash
RED_TEST_BLOB="$(git rev-parse HEAD:tests/test_applause_gate_conformance.py)"
test "$(git hash-object tests/test_applause_gate_conformance.py)" = "$RED_TEST_BLOB"
git add -- \
  scripts/validate_applause_gate.py \
  .github/workflows/applause-gate-conformance.yml
assert_staged_exact \
  scripts/validate_applause_gate.py \
  .github/workflows/applause-gate-conformance.yml
git commit -m "test: add applause conformance and mutation gate"
```

Reviewer gate: independent aggregate oracle, mutation sensitivity, workflow authority scan, privacy scan, and exact H0-A digest.

---

### Task 5: Deterministic evaluation payload and receipt envelope

**Files:**
- Create: `scripts/applause_gate/receipt.py`
- Create: `tests/test_applause_gate_determinism.py`
- Modify: `scripts/validate_applause_gate.py`

**Interfaces:**
- Consumes: exact case-level report, raw source bytes, and unchanged pure canonical helpers from Task 3.
- Produces: `build_evaluation_payload(...) -> dict` and `build_run_envelope(...) -> dict`.

Canonical JSON uses sorted keys, UTF-8, compact separators, `ensure_ascii=False`, and `allow_nan=False`. JSON input rejects duplicate keys. The serializer preserves array order and multiplicity; it never repairs invalid input. Validators reject duplicates first, and constructors sort only explicitly enumerated, already-unique set-like output fields.

The deterministic payload binds raw-byte SHA-256 for the schema, H0-A fixtures, H0-B request/assertion files, projection code, canonical helper, classifier, package exports, validator, receipt helper, and dependency lock; it also binds evaluated commit SHA, tree SHA, case results, aggregate counts, and all five semantic `none` effects. The payload hash excludes only its own hash field.

The run envelope contains actor, start/finish timestamps, workflow/job URL, OS, Python/jsonschema/PyYAML versions, command list, exit codes, warnings, and `evaluation_payload_sha256`. Envelope fields do not participate in deterministic replay equality.

- [ ] **Step 1: Write independent-oracle and mutation-sensitivity tests against an importable placeholder**

Tests recompute expected SHA-256 directly with `hashlib` and independent `json.dumps`, reject a constant/broken helper, and require every bound source mutation to change the payload hash or fail validation.

- [ ] **Step 2: Run and preserve behavioral RED**

Run:

```bash
PYTHONPATH=scripts python -m unittest tests/test_applause_gate_determinism.py -v
```

Expected: imports succeed; independent hash, environment-matrix, and mutation assertions fail against the placeholder. Preserve the RED commit and receipt.

Stage exactly the placeholder helper, validator change, and determinism test, then commit the executable RED harness:

```bash
git add -- \
  scripts/applause_gate/receipt.py \
  scripts/validate_applause_gate.py \
  tests/test_applause_gate_determinism.py
assert_staged_exact \
  scripts/applause_gate/receipt.py \
  scripts/validate_applause_gate.py \
  tests/test_applause_gate_determinism.py
git commit -m "test: add failing applause payload determinism tests"
```

- [ ] **Step 3: Reuse canonical helpers and split payload/envelope construction**

Import the unchanged Task 3 helpers; do not define a second canonicalizer. Classifier and canonical-helper code remain untouched. All filesystem/Git/environment observation lives in the runner or explicit arguments, never the decision core.

- [ ] **Step 4: Run the cold-process matrix**

Keep every committed raw artifact byte frozen. Run the validator from two temporary working directories with `PYTHONHASHSEED=1` and `2`, `TZ=UTC`, and `LC_ALL=C`; apply request-object key permutations and declared set-like evidence permutations only in memory after strict parsing. Expected: identical diagnostic facts, case results, canonical semantic objects, evaluation payload bytes/hash, and distinct permitted run envelopes.

Then make isolated physical-copy mutations that reorder JSON source keys or evidence entries on disk. Because the payload binds raw request/assertion byte digests, each physical byte reorder must change `evaluation_payload_sha256` or fail validation, while the independently recomputed `diagnostic_facts_sha256` remains invariant when decision-driving facts are semantically unchanged. Restore the frozen bytes before GREEN evidence. Never claim whole-payload equality across raw source-byte changes.

- [ ] **Step 5: Run GREEN and full candidate verification**

Run:

```bash
PYTHONPATH=scripts python -m unittest tests/test_applause_gate_determinism.py -v
PYTHONPATH=scripts python -m unittest discover -s tests -p 'test_applause_gate_*.py' -v
PYTHONPATH=scripts python scripts/validate_applause_gate.py --repo . --require-pass
```

Expected: all commands exit 0; source mutations change evidence; cold-process payload hashes match.

- [ ] **Step 6: Stage exactly and commit**

Freeze the RED determinism-test blob, stage only the receipt helper and validator changes, verify the phase-specific staged set, and commit:

```bash
RED_TEST_BLOB="$(git rev-parse HEAD:tests/test_applause_gate_determinism.py)"
test "$(git hash-object tests/test_applause_gate_determinism.py)" = "$RED_TEST_BLOB"
git add -- \
  scripts/applause_gate/receipt.py \
  scripts/validate_applause_gate.py
assert_staged_exact scripts/applause_gate/receipt.py scripts/validate_applause_gate.py
git commit -m "test: bind deterministic applause evaluation payload"
```

Reviewer gate: independent digest oracle, mutation sensitivity, environment matrix, source coverage, and payload/envelope separation.

---

### Task 6: Freeze evaluator evidence before Skill creation

**Files:**
- Create: `evals/applause-gate/receipts/evaluator/<evaluator-receipt-sha256>.json` where exactly one filename equals the canonical evaluator-receipt digest.

**Interfaces:**
- Consumes: exact evaluator-only Task 5 commit/tree, fresh PR CI for that SHA, and reviewer verdict.
- Produces: one immutable evaluator receipt referenced by Task 7.

- [ ] **Step 1: Verify no Skill package exists**

Run:

```bash
test ! -e candidate-packs/applause-gate/skill/SKILL.md
test ! -e candidate-packs/applause-gate/skill/manifest.schema.json
test ! -e candidate-packs/applause-gate/skill/manifest.json
test ! -e candidate-packs/applause-gate/skill/conformance.json
git diff --exit-code HEAD -- candidate-packs/applause-gate
```

Expected: exit 0.

- [ ] **Step 2: Push the green evaluator head and create/update only its draft implementation PR**

Re-declare the reusable guard and run `verify_frozen_successor_approval` immediately before the non-force push. Run it again after the push and immediately before creating or updating the draft implementation PR; do not combine either provider mutation with an unchecked operation. Push only `agent/quirk-applause-gate` without force. Resolve the implementation PR with the fail-closed cardinality oracle below. The clean successor plan PR remains untouched and draft. PR #64 remains untouched, and its branch, every existing or later commit, and all code, tests, receipts, CI, and evidence on it are excluded from satisfying this plan; no merge, cherry-pick, patch extraction, copy-forward, or evidence reuse is permitted. Verify the exact named H0-B workflow and job completed successfully on the evaluator SHA. Do not dispatch a workflow manually.

```bash
EVALUATOR_SHA="$(git rev-parse HEAD)"
inspect_pre_push_implementation_target "$EVALUATOR_SHA" optional
verify_frozen_successor_approval
git push origin HEAD:refs/heads/agent/quirk-applause-gate
verify_frozen_successor_approval

POST_PUSH_ROWS="$(gh pr list --repo Quirk-Systems/quirk-os --state open \
  --head agent/quirk-applause-gate \
  --json number,state,isDraft,baseRefName,headRefName,headRefOid)"
test "$(jq 'length' <<<"$POST_PUSH_ROWS")" -le 1
if test "$(jq 'length' <<<"$POST_PUSH_ROWS")" -eq 0; then
  verify_frozen_successor_approval
  gh pr create --repo Quirk-Systems/quirk-os --draft --base main \
    --head agent/quirk-applause-gate \
    --title "feat: add quarantined Applause Gate candidate evaluator" \
    --body "Candidate-only H0-B implementation evidence. Draft; no merge, runtime, Canon, admission, deployment, or publication authority."
fi
resolve_implementation_pr "$EVALUATOR_SHA"
verify_h0b_ci "$EVALUATOR_SHA"
```

Expected: before the push, open PRs for the branch have cardinality zero or exactly one valid draft targeting `main`, and any remote branch head is the open PR head and a fast-forward ancestor. Historical closed/merged PRs, including #63, are recorded as non-target provenance and excluded from open-target cardinality. Post-push/pre-create cardinality is again zero or one; post-create cardinality is exactly one at `$EVALUATOR_SHA`. An existing open non-draft, wrong-base, wrong-head-ref, wrong-head-SHA, non-fast-forward, or duplicate open PR stops before provider mutation. The captured run/workflow/attempt/job identities bind the evaluator receipt.

- [ ] **Step 3: Replay every behavioral RED/GREEN/REFACTOR cycle**

For Tasks 1–5, check out each recorded RED and GREEN/REFACTOR SHA in clean ephemeral worktrees, install only the pinned lock, rerun the declared commands, and require the exact expected assertion failure/pass. Record no receipt yet if any failure reason drifts, a RED unexpectedly passes, or a GREEN fails.

- [ ] **Step 4: Generate the content-addressed evaluator receipt**

Immediately before generating the receipt bytes, re-declare and run `verify_frozen_successor_approval`. The receipt records `approved_plan_sha`, `approved_plan_blob_sha`, successor issue #52 decision comment ID and body digest, issue #51 authority watermark `5380917867` and body SHA-256, superseded PR #64 grant/mode/head and no-reuse disposition, plan-review Golden Gates run/job/attempt identities, execution mode, implementation branch, original H0-B grant comment `5379655626`, exact fields `evaluator_commit_sha` and `evaluator_tree_sha`, source digests, `evaluation_payload_sha256`, replayed TDD cycles, implementation PR identity, exact H0-B CI run/workflow/attempt/job identities, commands, counts, warnings, reviewer identity, reviewer verdict `PASS_CANDIDATE_EVIDENCE`, all five semantic `none` effects, `repository_visibility: public_candidate`, and exact provider operations observed. These approval fields are non-authorizing provenance; they cannot create or expand a grant. Compute `evaluator_receipt_sha256` over canonical receipt bytes with only that self-field omitted; the filename and Task 7 reference must equal `evaluator_receipt_sha256`, not the payload digest.

- [ ] **Step 5: Validate receipt filename, content hash, ancestry, and freshness**

Run an independent oracle for both hashes and then rerun the exact evaluator commands. A wrapper-field mutation must change `evaluator_receipt_sha256`; a deterministic-payload mutation must change both hashes or fail validation. Missing, stale, mismatched, failing, or self-authorizing receipts stop the tranche.

- [ ] **Step 6: Stage the one receipt and commit**

Re-declare and run `verify_frozen_successor_approval` immediately before staging and committing; the earlier generation check does not carry forward. Verify the staged set contains exactly one path below `evals/applause-gate/receipts/evaluator/`, then commit:

```bash
[[ "$EVALUATOR_RECEIPT_SHA256" =~ ^[0-9a-f]{64}$ ]]
test "$(basename "$EVALUATOR_RECEIPT_PATH")" = "${EVALUATOR_RECEIPT_SHA256}.json"
test "$(dirname "$EVALUATOR_RECEIPT_PATH")" = "evals/applause-gate/receipts/evaluator"
git add -- "$EVALUATOR_RECEIPT_PATH"
assert_staged_exact "$EVALUATOR_RECEIPT_PATH"

verify_evaluator_receipt_ref() {
  set -euo pipefail
  receipt_ref_prefix="$1"
  PYTHONPATH=scripts python - \
    "$EVALUATOR_RECEIPT_PATH" "$EVALUATOR_RECEIPT_SHA256" "$receipt_ref_prefix" <<'PY'
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from applause_gate.json_io import load_json_strict

path, expected, prefix = sys.argv[1:]
raw = subprocess.run(
    ["git", "show", f"{prefix}{path}"],
    check=True,
    capture_output=True,
).stdout.decode("utf-8")
receipt = load_json_strict(raw)
if type(receipt) is not dict:
    raise SystemExit("evaluator receipt must be an exact object")
claimed = receipt.pop("evaluator_receipt_sha256", None)
canonical = json.dumps(
    receipt,
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=False,
    allow_nan=False,
).encode("utf-8")
actual = hashlib.sha256(canonical).hexdigest()
if claimed != expected or actual != expected or Path(path).name != f"{expected}.json":
    raise SystemExit(
        f"evaluator receipt digest mismatch: claimed={claimed} actual={actual} expected={expected}"
    )
PY
}

verify_evaluator_receipt_ref ":"
git commit -m "test: record applause evaluator candidate evidence"
test "$(git ls-tree HEAD -- "$EVALUATOR_RECEIPT_PATH" | awk '{print $1 " " $2}')" = \
  "100644 blob"
verify_evaluator_receipt_ref "HEAD:"
```

Reviewer gate: the reviewer of Task 6 must not be the Task 5 implementer. Passing evidence is a necessary condition already covered by Bryan's approved plan; it does not create new authority.

---

### Task 7: Receipt-bound quarantined Skill package

**Files:**
- Create: `candidate-packs/applause-gate/skill/SKILL.md`
- Create: `candidate-packs/applause-gate/skill/manifest.schema.json`
- Create: `candidate-packs/applause-gate/skill/manifest.json`
- Create: `candidate-packs/applause-gate/skill/conformance.json`
- Create: `scripts/validate_applause_gate_package.py`
- Create: `tests/test_applause_gate_skill_package.py`

**Interfaces:**
- Consumes: valid fresh evaluator receipt from Task 6.
- Produces: quarantined Skill version `0.1.0`, `status: candidate`, manifest `family: evaluate`, authority ceiling `infer`, and four candidate cases. It makes no shared-family compatibility claim.

The package validator must reject the package when the evaluator receipt is absent, stale, tampered, failing, bound to different evaluator bytes, or claims authority. Freshness is ancestry- and content-based, never equality between the later package head and the earlier evaluator head: (a) the recorded evaluator commit exists and its recorded tree equals `git show -s --format=%T <evaluator-sha>`; (b) that evaluator SHA is an ancestor of the package head; (c) every evaluator-bound source blob at the package head equals the digest recorded in the receipt; (d) every required CI/check observation has `head_sha` equal to the recorded evaluator SHA; and (e) the reviewer verdict binds that same evaluator SHA. `EVALUATOR_RECEIPT_STALE` means any one of those five predicates fails. It never reads ambient time, and it must not compare the package `HEAD` or tree for equality with the evaluator commit or tree. Any temporal lease would require an explicit `as_of` argument bound into the run envelope. The validator checks the closed local manifest schema, source Git-blob SHA, canonical manifest SHA-256, exact trigger/non-trigger wording, evaluator evidence, and the four positive/adversarial/regression/authority cases.

Quarantine requirements:

- No Applause file exists anywhere under `skills/` or `evals/skills/`.
- Existing 11 registered Skills and 44 shared cases remain byte-identical.
- The unmodified shared validator and runtime tests remain green because the quarantine root is outside every shared discovery glob.
- The package validator fails `CANDIDATE_DISCOVERABLE` if any package path, registry reference, shared conformance reference, runtime import, or shared-family compatibility assertion would make the candidate discoverable.
- No runtime loader, shared validator, shared test, README, evaluator, registry, schema, or conformance modification.

- [ ] **Step 1: Add an importable package validator and behavioral tests while package files remain absent**

The validator returns structured `PACKAGE_MISSING`, `EVALUATOR_RECEIPT_MISSING`, `EVALUATOR_RECEIPT_STALE`, `EVALUATOR_RECEIPT_TAMPERED`, `SOURCE_TAMPERED`, `MANIFEST_TAMPERED`, `CANDIDATE_DISCOVERABLE`, and `SHARED_SURFACE_CHANGED` findings. On the real Task-6 tree, the evaluator receipt exists: the one acceptance test `test_candidate_package_is_receipt_bound` reaches the importable validator and is intentionally expected to fail because `PACKAGE_MISSING` prevents a passing package result. Separately, an isolated temporary-tree mutation removes the evaluator receipt and asserts that `EVALUATOR_RECEIPT_MISSING` is returned; that negative rejection assertion itself passes in RED and GREEN and is not the RED reason.

- [ ] **Step 2: Run and preserve RED**

Run:

```bash
PYTHONPATH=scripts python -m unittest tests/test_applause_gate_skill_package.py -v
```

Expected: imports succeed; exactly the named `test_candidate_package_is_receipt_bound` acceptance assertion fails because the real-tree result contains `PACKAGE_MISSING`. The isolated missing-receipt rejection test passes. Preserve that exact test ID, finding, assertion text, and failure count in the RED receipt; any other failure invalidates the cycle.

Stage exactly the validator and package test, then commit the executable RED harness while every candidate-package file is absent:

```bash
git add -- scripts/validate_applause_gate_package.py tests/test_applause_gate_skill_package.py
assert_staged_exact scripts/validate_applause_gate_package.py tests/test_applause_gate_skill_package.py
git commit -m "test: add failing quarantined-package binding tests"
```

- [ ] **Step 3: Create source, manifest, and four quarantined cases**

Before creating any Skill-package byte, re-declare and run `verify_frozen_successor_approval`. `SKILL.md` states precise triggers, non-triggers, typed input/output contract, method, evidence limits, medical/legal/financial/safety exclusions, candidate status, no live-data requirement, no connected tools, no publication/rollout authority, no runtime activation, and no self-promotion from evidence.

The local manifest declares only local read/evaluate/emit-candidate-review actions. It references `candidate-packs/applause-gate/skill/conformance.json` and the exact `evaluator_receipt_sha256`. It contains no admission, shared-family mapping, runtime grant, provider action, or publication object.

- [ ] **Step 4: Prove quarantine without shared handling**

Do not add candidate recognition to any shared validator or runtime. Hash the protected shared surfaces at the approved plan SHA and current head; require equality. Assert the candidate is absent from all `skills/*/manifest.json` discovery, registry IDs, imports, and shared conformance paths.

- [ ] **Step 5: Compute pre-commit integrity deterministically**

Compute the Skill Git-blob SHA with `git hash-object candidate-packs/applause-gate/skill/SKILL.md`. Compute canonical `manifest_sha256` with sorted-key compact UTF-8 JSON after removing only `integrity.manifest_sha256`, without importing or modifying the shared runtime. Write both values into the local manifest, stage only the four package files plus the changed package validator, then require `git rev-parse :candidate-packs/applause-gate/skill/SKILL.md` to equal the staged manifest's `integrity.source_blob_sha` and independently recompute the staged manifest digest before committing. The RED package-test blob must remain unchanged.

- [ ] **Step 6: Run GREEN and tamper/runtime rejection tests**

Run:

```bash
PYTHONPATH=scripts python scripts/validate_applause_gate_package.py --repo . --require-pass
PYTHONPATH=scripts python scripts/validate_skills.py --repo .
PYTHONPATH=scripts python -m unittest tests/test_applause_gate_skill_package.py -v
PYTHONPATH=scripts python -m unittest tests/test_skill_runtime.py -v
PYTHONPATH=scripts python -m unittest discover -s tests -p 'test_applause_gate_*.py' -v
```

Expected: all commands exit 0; one-byte source/manifest/receipt mutations fail; Applause is quarantined and undiscoverable; the protected shared surfaces are byte-identical; the central set remains 11 Skills/44 cases.

- [ ] **Step 7: Stage exactly and commit**

Re-declare and run `verify_frozen_successor_approval` again immediately before staging and committing the Skill binding; approval freshness at package creation does not carry forward. Freeze the RED package-test blob, stage only the four package files and validator change, verify the phase-specific staged set, and commit:

```bash
RED_TEST_BLOB="$(git rev-parse HEAD:tests/test_applause_gate_skill_package.py)"
test "$(git hash-object tests/test_applause_gate_skill_package.py)" = "$RED_TEST_BLOB"
git add -- \
  candidate-packs/applause-gate/skill/SKILL.md \
  candidate-packs/applause-gate/skill/manifest.schema.json \
  candidate-packs/applause-gate/skill/manifest.json \
  candidate-packs/applause-gate/skill/conformance.json \
  scripts/validate_applause_gate_package.py
assert_staged_exact \
  candidate-packs/applause-gate/skill/SKILL.md \
  candidate-packs/applause-gate/skill/manifest.schema.json \
  candidate-packs/applause-gate/skill/manifest.json \
  candidate-packs/applause-gate/skill/conformance.json \
  scripts/validate_applause_gate_package.py
git commit -m "feat: bind quarantined applause gate candidate skill"
test "$(git rev-parse HEAD:candidate-packs/applause-gate/skill/SKILL.md)" = \
  "$(PYTHONPATH=scripts python -c 'from pathlib import Path; from applause_gate.json_io import load_json_strict; print(load_json_strict(Path("candidate-packs/applause-gate/skill/manifest.json").read_text(encoding="utf-8"))["integrity"]["source_blob_sha"])')"
PYTHONPATH=scripts python scripts/validate_applause_gate_package.py --repo . --require-pass
```

Reviewer gate: exact receipt binding, local-schema closure, trigger collisions, quarantine, shared-surface hashes, discovery rejection, and no shared-evaluator/runtime modification.

---

### Task 8: Final binding receipt, full verification, and draft PR evidence

**Files:**
- Create: `evals/applause-gate/receipts/binding/<binding-receipt-sha256>.json`.
- Provider metadata: update only the uniquely resolved draft implementation PR; the clean successor plan PR and excluded historical PR #64 remain untouched.

**Interfaces:**
- Consumes: exact Skill/package commit, evaluator receipt, all task reviews, and fresh CI.
- Produces: one final candidate binding receipt and updated draft-PR evidence. Produces no downstream authority.

- [ ] **Step 1: Run full local verification with the correct import path**

Run:

```bash
EVALUATOR_RECEIPT_LIST="$(git ls-files \
  'evals/applause-gate/receipts/evaluator/[0-9a-f][0-9a-f]*.json')"
test -n "$EVALUATOR_RECEIPT_LIST"
mapfile -t EVALUATOR_RECEIPTS <<<"$EVALUATOR_RECEIPT_LIST"
test "${#EVALUATOR_RECEIPTS[@]}" -eq 1
EVALUATOR_RECEIPT_PATH="${EVALUATOR_RECEIPTS[0]}"
EVALUATOR_RECEIPT_SHA256="$(basename "$EVALUATOR_RECEIPT_PATH" .json)"
[[ "$EVALUATOR_RECEIPT_SHA256" =~ ^[0-9a-f]{64}$ ]]
test "$(git ls-tree HEAD -- "$EVALUATOR_RECEIPT_PATH" | awk '{print $1 " " $2}')" = \
  "100644 blob"
EVALUATOR_BINDING="$(
  PYTHONPATH=scripts python - "$EVALUATOR_RECEIPT_PATH" <<'PY'
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from applause_gate.json_io import load_json_strict

path = sys.argv[1]
raw = subprocess.run(
    ["git", "show", f"HEAD:{path}"],
    check=True,
    capture_output=True,
).stdout.decode("utf-8")
receipt = load_json_strict(raw)
if type(receipt) is not dict:
    raise SystemExit("evaluator receipt must be an exact object")
claimed = receipt.pop("evaluator_receipt_sha256", None)
canonical = json.dumps(
    receipt,
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=False,
    allow_nan=False,
).encode("utf-8")
actual = hashlib.sha256(canonical).hexdigest()
if claimed != actual or Path(path).name != f"{actual}.json":
    raise SystemExit("evaluator receipt self-hash/filename mismatch")
commit_sha = receipt.get("evaluator_commit_sha")
tree_sha = receipt.get("evaluator_tree_sha")
if not isinstance(commit_sha, str) or not isinstance(tree_sha, str):
    raise SystemExit("evaluator commit/tree binding missing")
print(commit_sha, tree_sha)
PY
)"
test "$(wc -w <<<"$EVALUATOR_BINDING")" -eq 2
test "$(wc -l <<<"$EVALUATOR_BINDING")" -eq 1
read -r EVALUATOR_SHA EVALUATOR_TREE_SHA <<<"$EVALUATOR_BINDING"
[[ "$EVALUATOR_SHA" =~ ^[0-9a-f]{40}$ ]]
[[ "$EVALUATOR_TREE_SHA" =~ ^[0-9a-f]{40}$ ]]
git cat-file -e "$EVALUATOR_SHA^{commit}"
test "$(git show -s --format=%T "$EVALUATOR_SHA")" = "$EVALUATOR_TREE_SHA"
git merge-base --is-ancestor "$EVALUATOR_SHA" HEAD

PYTHONPATH=scripts python -m unittest discover -s tests -v
PYTHONPATH=scripts python scripts/validate_applause_gate_fixtures.py --repo . --require-pass
PYTHONPATH=scripts python scripts/validate_applause_gate.py --repo . --require-pass
PYTHONPATH=scripts python scripts/validate_applause_gate_package.py --repo . --require-pass
PYTHONPATH=scripts python scripts/validate_skills.py --repo .
```

Expected: every command exits 0 with no unclassified warning or skip.

- [ ] **Step 2: Enforce exact H0-B paths and protected prefixes**

Verify immutable H0-A paths and protected shared paths, then run this package-head authority check against the approved plan SHA. It requires all 24 fixed implementation paths plus exactly one evaluator receipt and zero binding receipts; after the binding commit, the exact `$PACKAGE_SHA..HEAD` check permits only that one binding receipt. `git diff --name-only main...HEAD` may be recorded as PR inventory but is not the authority check.

```bash
python - "$PLAN_SHA" <<'PY'
import re
import subprocess
import sys

plan_sha = sys.argv[1]
expected = {
    ".github/workflows/applause-gate-conformance.yml",
    "candidate-packs/applause-gate/skill/SKILL.md",
    "candidate-packs/applause-gate/skill/conformance.json",
    "candidate-packs/applause-gate/skill/manifest.json",
    "candidate-packs/applause-gate/skill/manifest.schema.json",
    "evals/applause-gate/h0-b-assertions.json",
    "evals/applause-gate/h0-b-requests.json",
    "examples/applause-gate/applause-review.valid.json",
    "schemas/applause-review.schema.json",
    "scripts/applause_gate/__init__.py",
    "scripts/applause_gate/canonical.py",
    "scripts/applause_gate/classifier.py",
    "scripts/applause_gate/fixture_projection.py",
    "scripts/applause_gate/json_io.py",
    "scripts/applause_gate/receipt.py",
    "scripts/validate_applause_gate.py",
    "scripts/validate_applause_gate_package.py",
    "tests/test_applause_gate_classifier.py",
    "tests/test_applause_gate_conformance.py",
    "tests/test_applause_gate_determinism.py",
    "tests/test_applause_gate_projection.py",
    "tests/test_applause_gate_purity.py",
    "tests/test_applause_gate_schema.py",
    "tests/test_applause_gate_skill_package.py",
}
receipt_patterns = (
    re.compile(r"^evals/applause-gate/receipts/evaluator/[0-9a-f]{64}\.json$"),
    re.compile(r"^evals/applause-gate/receipts/binding/[0-9a-f]{64}\.json$"),
)
rows = subprocess.run(
    ["git", "diff", "--name-status", plan_sha, "HEAD"],
    check=True,
    capture_output=True,
    text=True,
).stdout.splitlines()
paths = set()
observed = set()
receipts = [0, 0]
for row in rows:
    status, path = row.split("\t", 1)
    if status != "A":
        raise SystemExit(f"forbidden diff status: {row}")
    observed.add(path)
    for index, pattern in enumerate(receipt_patterns):
        if pattern.fullmatch(path):
            receipts[index] += 1
            break
    else:
        if path not in expected:
            raise SystemExit(f"forbidden path: {path}")
        paths.add(path)
if paths != expected:
    raise SystemExit(f"implementation path mismatch: missing={sorted(expected - paths)} extra={sorted(paths - expected)}")
if receipts != [1, 0]:
    raise SystemExit(f"receipt cardinality mismatch: {receipts}")
for path in sorted(observed):
    entry = subprocess.run(
        ["git", "ls-tree", "HEAD", "--", path],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip().split()
    if len(entry) < 4 or entry[0:2] != ["100644", "blob"]:
        raise SystemExit(f"forbidden tree mode/type for {path}: {entry[0:2]}")
untracked = subprocess.run(
    ["git", "ls-files", "--others", "--exclude-standard"],
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()
if untracked:
    raise SystemExit(f"untracked paths remain: {untracked}")
PY
```

- [ ] **Step 3: Push package head and require fresh exact-head CI**

Set `PACKAGE_SHA="$(git rev-parse HEAD)"`. Re-declare and run `verify_frozen_successor_approval` immediately before the non-force push. Re-run the implementation-PR cardinality oracle and require its exact head SHA to become `$PACKAGE_SHA`. Verify the exact named H0-B workflow/job passes on `$PACKAGE_SHA`; the reusable guard separately proves the clean successor remains open, draft, exact-head, and plan-path singleton. PR #64 remains untouched and excluded from execution and evidence reuse. No manual dispatch or other provider mutation.

```bash
PACKAGE_SHA="$(git rev-parse HEAD)"
inspect_pre_push_implementation_target "$PACKAGE_SHA" required
test "$PRE_PUSH_REMOTE_SHA" = "$EVALUATOR_SHA"
verify_frozen_successor_approval
git push origin HEAD:refs/heads/agent/quirk-applause-gate
resolve_implementation_pr "$PACKAGE_SHA"
verify_h0b_ci "$PACKAGE_SHA"
```

- [ ] **Step 4: Replay the Task 7 RED/GREEN/REFACTOR cycle**

Check out the recorded Task 7 RED and GREEN/REFACTOR SHAs in clean ephemeral worktrees. Require the package test to fail only with the declared missing-package/binding findings at RED and pass at GREEN/REFACTOR. Record command/output digests, test IDs, exit codes, commit/tree SHAs, and immutable test blob SHA for the binding receipt. Any drift stops the tranche.

- [ ] **Step 5: Generate and commit the binding receipt**

Re-declare and run `verify_frozen_successor_approval` immediately before generating the binding receipt and again immediately before staging/committing it. The binding receipt contains `approved_plan_sha`, `approved_plan_blob_sha`, successor issue #52 decision comment ID/body digest, issue #51 authority watermark `5380917867` and exact body digest, superseded PR #64 head/plan-blob/mode and no-reuse disposition, plan-review Golden Gates run/job/attempt identities, execution mode, implementation branch, original H0-B grant comment `5379655626`, package commit/tree, `evaluator_receipt_sha256`, Skill blob SHA, manifest SHA-256, candidate-case digest, package-validator digest, Task 7 TDD replay, exact test commands/counts, package-head H0-B CI run/workflow/attempt/job identities, reviewer verdict, quarantine proof, all five semantic `none` effects, `repository_visibility: public_candidate`, and exact provider operations observed. These approval fields are non-authorizing provenance. Compute `binding_receipt_sha256` over canonical receipt bytes with only that self-field omitted; a wrapper mutation must change it, and the filename must equal it.

Stage exactly one binding-receipt path and commit:

```bash
[[ "$BINDING_RECEIPT_SHA256" =~ ^[0-9a-f]{64}$ ]]
test "$(basename "$BINDING_RECEIPT_PATH")" = "${BINDING_RECEIPT_SHA256}.json"
test "$(dirname "$BINDING_RECEIPT_PATH")" = "evals/applause-gate/receipts/binding"
git add -- "$BINDING_RECEIPT_PATH"
assert_staged_exact "$BINDING_RECEIPT_PATH"

verify_binding_receipt_ref() {
  set -euo pipefail
  receipt_ref_prefix="$1"
  PYTHONPATH=scripts python - \
    "$BINDING_RECEIPT_PATH" "$BINDING_RECEIPT_SHA256" "$receipt_ref_prefix" <<'PY'
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from applause_gate.json_io import load_json_strict

path, expected, prefix = sys.argv[1:]
raw = subprocess.run(
    ["git", "show", f"{prefix}{path}"],
    check=True,
    capture_output=True,
).stdout.decode("utf-8")
receipt = load_json_strict(raw)
if type(receipt) is not dict:
    raise SystemExit("binding receipt must be an exact object")
claimed = receipt.pop("binding_receipt_sha256", None)
canonical = json.dumps(
    receipt,
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=False,
    allow_nan=False,
).encode("utf-8")
actual = hashlib.sha256(canonical).hexdigest()
if claimed != expected or actual != expected or Path(path).name != f"{expected}.json":
    raise SystemExit(
        f"binding receipt digest mismatch: claimed={claimed} actual={actual} expected={expected}"
    )
PY
}

verify_binding_receipt_ref ":"
git commit -m "test: record applause skill binding evidence"
test "$(git diff --name-status "$PACKAGE_SHA" HEAD)" = $'A\t'"$BINDING_RECEIPT_PATH"
test "$(git ls-tree HEAD -- "$BINDING_RECEIPT_PATH" | awk '{print $1 " " $2}')" = \
  "100644 blob"
verify_binding_receipt_ref "HEAD:"
```

- [ ] **Step 6: Push final receipt head and verify exact-head CI again**

Re-declare and run `verify_frozen_successor_approval` immediately before the non-force push. Re-run the implementation-PR cardinality oracle, then verify the exact named H0-B workflow/job on the receipt head and confirm the uniquely resolved implementation PR is still draft. The committed binding receipt covers the package-head CI observed before the receipt commit. Receipt-head CI is a post-commit provider observation recorded only in the implementation PR evidence projection; it must not be folded back into the receipt or trigger a fixed-point rewrite.

```bash
RECEIPT_SHA="$(git rev-parse HEAD)"
inspect_pre_push_implementation_target "$RECEIPT_SHA" required
test "$PRE_PUSH_REMOTE_SHA" = "$PACKAGE_SHA"
verify_frozen_successor_approval
git push origin HEAD:refs/heads/agent/quirk-applause-gate
resolve_implementation_pr "$RECEIPT_SHA"
verify_h0b_ci "$RECEIPT_SHA"
```

- [ ] **Step 7: Update only the draft implementation PR**

Re-declare and run `verify_frozen_successor_approval` immediately before the PR metadata mutation, and re-run the implementation-PR cardinality oracle with exact receipt-head SHA before selecting the target. Retitle `$IMPLEMENTATION_PR` to `feat: add quarantined Applause Gate candidate evaluator`. Add the immutable successor approval reference, exact commits, trees, digests, commands, counts, warnings, limitations, quarantine proof, provider effects, and receipt links. Do not edit either plan PR, post issue comments, request reviewers, add closing keywords, or mark ready.

```bash
verify_frozen_successor_approval
resolve_implementation_pr "$RECEIPT_SHA"
SANITIZED_PR_EVIDENCE_PATH="$(mktemp /tmp/abg-h0b-pr-evidence.XXXXXX.md)"
case "$SANITIZED_PR_EVIDENCE_PATH" in
  "$PWD"/*) exit 1 ;;
esac
trap 'rm -f -- "$SANITIZED_PR_EVIDENCE_PATH"' EXIT
SANITIZED_PR_BODY="$(cat <<EOF
## H0-B quarantined candidate evidence

- candidate_status: \`candidate_only\`
- approved_plan_sha: \`$PLAN_SHA\`
- approved_plan_blob_sha: \`$PLAN_BLOB_SHA\`
- approval_comment_id: \`$APPROVAL_COMMENT_ID\`
- evaluator_receipt_sha256: \`$EVALUATOR_RECEIPT_SHA256\`
- binding_receipt_sha256: \`$BINDING_RECEIPT_SHA256\`
- receipt_head_sha: \`$RECEIPT_SHA\`
- ci_workflow_id: \`$CI_WORKFLOW_ID\`
- ci_run_id: \`$CI_RUN_ID\`
- ci_run_attempt: \`$CI_RUN_ATTEMPT\`
- ci_job_id: \`$CI_JOB_ID\`
- authority_effect: \`none\`
- runtime_effect: \`none\`
- canon_effect: \`none\`
- admission_effect: \`none\`
- release_publication_effect: \`none\`
- repository_visibility: \`public_candidate\`
- limitation: \`visible synthetic conformance only\`
EOF
)"
printf '%s' "$SANITIZED_PR_BODY" >"$SANITIZED_PR_EVIDENCE_PATH"
test -s "$SANITIZED_PR_EVIDENCE_PATH"
! rg -n -i '\b(close[sd]?|fix(e[sd])?|resolve[sd]?)\s+#?[0-9]+' \
  "$SANITIZED_PR_EVIDENCE_PATH"
! rg -n -i \
  'execution_authorized:[[:space:]]*true|runtime_effect:[[:space:]]*(active|enabled)|canon_effect:[[:space:]]*(promoted|active)|admission_effect:[[:space:]]*(admitted|active)|release_publication_effect:[[:space:]]*(published|released|active)' \
  "$SANITIZED_PR_EVIDENCE_PATH"
! rg -n -i 'request reviewer|ready for review|merge this|auto-merge' \
  "$SANITIZED_PR_EVIDENCE_PATH"
! rg -n -i \
  '(^|[^a-z])(subject|claim|signal|raw evidence|evidence body|request object|environment value|stdout|stderr|secret|token|credential|personal data|held-out material)([^a-z]|$)' \
  "$SANITIZED_PR_EVIDENCE_PATH"
gh pr edit "$IMPLEMENTATION_PR" --repo Quirk-Systems/quirk-os \
  --title "feat: add quarantined Applause Gate candidate evaluator" \
  --body-file "$SANITIZED_PR_EVIDENCE_PATH"
PR_AFTER="$(gh pr view "$IMPLEMENTATION_PR" --repo Quirk-Systems/quirk-os \
  --json state,isDraft,baseRefName,headRefName,headRefOid,title,body)"
test "$(jq -r '.state' <<<"$PR_AFTER")" = "OPEN"
test "$(jq -r '.isDraft' <<<"$PR_AFTER")" = "true"
test "$(jq -r '.baseRefName' <<<"$PR_AFTER")" = "main"
test "$(jq -r '.headRefName' <<<"$PR_AFTER")" = "agent/quirk-applause-gate"
test "$(jq -r '.headRefOid' <<<"$PR_AFTER")" = "$RECEIPT_SHA"
test "$(jq -r '.title' <<<"$PR_AFTER")" = \
  "feat: add quarantined Applause Gate candidate evaluator"
test "$(jq -r '.body' <<<"$PR_AFTER")" = "$SANITIZED_PR_BODY"
rm -f -- "$SANITIZED_PR_EVIDENCE_PATH"
trap - EXIT
```

The closed generator and executable scans reject closing keywords, positive authority/effect claims, reviewer/ready/merge instructions, and raw/private fields. The temporary path is outside the implementation worktree and is deleted only after the provider readback proves exact title/body/draft/base/head. The body binds `$RECEIPT_SHA` and the exact receipt-head CI identities.

- [ ] **Step 8: Stop unconditionally**

Stop after the draft-PR update under every outcome. Do not start ABG-07, mutation campaigns beyond the visible critical mutations in Task 4, sealed held-out evaluation, Plugin Eval, plugin packaging, Supabase projection, submission drafting, merge, admission, activation, deployment, release, or publication.

Reviewer gate: whole-branch scope, exact-head evidence, privacy, quarantine, receipt ancestry, and unconditional stop.

---

## Requirement Coverage

- Plan-first and successor-SHA approval: Task 0, the frozen clean-successor draft PR, and the exact issue #52 successor decision.
- Exact path and provider boundaries: global allowlists, Standard Commit and Scope Guard, Tasks 0 and 8.
- Strict request/review contract: Task 1.
- H0-A preservation and oracle-free projection: Task 2.
- Pure deterministic classifier: Task 3.
- All 19 visible fixtures, critical mutations, and fail-closed counters: Task 4.
- Independent determinism oracle and content-addressed evidence: Task 5.
- Evaluator evidence before Skill files: Task 6.
- Receipt-bound candidate Skill without registry/runtime integration: Task 7.
- Repository-native verification and draft PR candidate evidence: Task 8.
- No authority expansion from tests or evidence: every task plus unconditional Task 8 stop.

## Self-Review Result

- Scope: one candidate evaluator and one quarantined internal Skill package; no second subsystem.
- Placeholder scan: no unresolved placeholder markers or implementation euphemisms remain.
- Type consistency: request, review, classifier, projection, conformance, payload, envelope, evaluator receipt, package validator, and binding receipt interfaces are named before downstream use.
- Truth boundary: fixture metadata and expected behaviors remain evaluation-only; evidence references are never treated as evidence facts.
- Authority boundary: shared registry/runtime/evaluator files are protected; provider writes are limited to the one issue #52 successor decision, the clean plan-only successor draft, and one separately resolved draft implementation PR. PR #64 is preserved as tainted historical evidence, its inline grant is explicitly superseded, reuse is forbidden, and ABG-07 is unconditionally excluded.
- Execution boundary: this plan becomes executable only through the unedited, byte-closed Bryan-authored issue #52 successor decision bound to the frozen clean-successor PR/head/blob/fixture/Golden-Gates evidence, mode `Subagent-Driven`, and branch `agent/quirk-applause-gate`.

## Execution Handoff

The plan is approved for later `Subagent-Driven` execution only when issue #52 contains exactly one unedited byte-closed successor decision matching Task 0, issue #51 comment `5380917867` with body SHA-256 `871a0d009bc9896c7421f1eed3dbebaead84f25eb97231c3c1c120ade81a26b0` remains the latest Bryan-authored issue #51 record and is explicitly superseded by that frozen issue #52 decision, the decision also supersedes issue #52 comment `5380558390`, the frozen Golden Gates run/job predate the decision and remain successful, and the clean successor PR still points at the named plan SHA/blob as an open plan-path-singleton draft. The executor starts `agent/quirk-applause-gate` at that exact plan SHA without importing any PR #64 descendant, begins at Task 0 before adding any implementation commit, uses a fresh implementer and distinct reviewer for every task, and stops after Task 8. This plan revision itself performs no H0-B implementation.
