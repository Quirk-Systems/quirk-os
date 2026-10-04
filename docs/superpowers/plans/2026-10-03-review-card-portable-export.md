# Review Card and Portable Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only Quirk OS PR review card whose complete captured evidence can be copied, verified, and reopened offline.

**Architecture:** A bounded GitHub collector supplies immutable response bytes to a deterministic Python package. Closed contracts, static rendering, and an exclusively created directory preserve separate integrity, coverage, freshness, review, and authorization states. Existing Quirk envelopes and receipts are reused without introducing a service or runtime integration.

**Tech Stack:** Linux/Python 3.12+, standard library, unittest, existing `jsonschema==4.26.0` and `PyYAML==6.0.3`; static HTML/CSS and Markdown. No new dependency.

**Spec:** [Approved specification](../specs/2026-10-03-review-card-portable-export-design.md). Read both documents before execution. Bryan approved the spec with “Spec Approvals”; documentation publication was authorized with “Publishing Authorized by Bryan.” This plan awaits review and execution-method selection.

## Global Constraints

- Live source: only `Quirk-Systems/quirk-os`, HTTPS GET, positive integer PR, validated exact head; no remote writes, redirects, automatic retries, source-driven tool dispatch, or arbitrary URL fetching.
- Audience `private_operator`; origin `live_capture`, `synthetic_fixture`, or `caller_supplied`; authorization fixed `none`. Bot evidence never grants human acceptance.
- New protocols `review-snapshot.v1`, `review-card-content.v1`, `review-bundle-manifest.v1`; existing `source-binding.v2`, `projection-envelope.v1`, `sync-run-receipt.v2` remain unchanged.
- Stable subject key `review.github.quirk-systems.quirk-os.pr.NUMBER`; binding IDs retain the `binding.` grammar. Subject head and producer source commit remain separate.
- Integrity: `verified_against_anchor`, `internally_consistent`, `invalid`; coverage: `complete`, `partial`, `unavailable`; freshness: `not_checked`, `unchanged`, `stale`, `unavailable`; review: `ready_for_review`, `blocked`, `stale`.
- 32 MiB total input payload bytes; 2 MiB per HTTP response; 256 payload files; 128 evidence records per group; JSON nesting 32; 16,384 characters per displayed text field.
- 100 pages across the capture; 200 HTTP requests; 10-second request timeout; 120-second capture deadline. No automatic retries in version one.
- Credentials only from `GITHUB_TOKEN`; never persist credentials, request headers, raw transport errors, or token-bearing links. Read-only token scope is an operator prerequisite.
- Output is a new directory, never overwrite/delete a prior export; `manifest.json` is the final no-overwrite marker. Interrupted attempts remain diagnosable and non-successful.
- Reject symlink components, absolute/traversal/backslash/drive paths, duplicate or case-fold-colliding names, reserved payload paths, and input/output overlap.
- Exact-byte payload hashing; sorted-key compact UTF-8 JSON hashing, not an RFC canonicalization claim. Manifest excludes itself; receipt excludes itself and manifest from output hashes.
- Reject duplicate JSON keys, non-finite numbers, unsupported versions, invalid Unicode/timestamps/SHA values, missing schema closure, and remote schema resolution.
- Static HTML with inline CSS, no JavaScript or external assets; Markdown semantic fallback; 390 px layout, wrapping hashes, local table scrolling, ordered headings, visible keyboard focus, textual reasons.
- Exit `0`: command mechanics succeeded, even if review is explicitly blocked; `2`: invalid input/contract/incomplete export; `3`: capture identity/access failure; `4`: unsafe or occupied output.
- No Supabase/Vercel integration, merge/deploy/approval actuator, zip format, review-comment capture, tenant access, or runtime admission. Do not edit the overlapping distill-loop work or import unmerged PR #76.
- Fixture/mechanical evidence is not Bryan's usefulness judgment; Linux/Python 3.12+ is the initial portability target. Other platforms require actual exercise.

## Review Focus

- PR identity remains stable while its base branch or mergeability changes: report observed metadata, never infer branch-policy permission from head checks (Task 2).
- Provider `User` actors, deleted actors, and nullable timestamps: preserve unknown attribution; never classify a login as Bryan's acceptance (Tasks 2 and 6).
- Empty, repeated, or whitespace-only CLI check names: distinguish unknown requirements from explicit no-check requirements and reject invalid names (Task 7).
- Copy to a Unicode/space-containing path and run from a different working directory: resolve bundle-local resources independently of the original host (Tasks 5 and 7).
- A later observation is for another PR or predates capture: reject identity/time mismatch rather than claim unchanged present freshness (Tasks 2 and 7).

---

## File structure and interface decisions

All product paths below are new. The only existing project file consumed as configuration is `requirements.txt`; it does not need modification. Existing schemas/helpers/workflows remain untouched.

| Files | Responsibility / owning task |
| --- | --- |
| `scripts/review_card/__init__.py`, `types.py`, `contracts.py` | Version, shared immutable types, strict parser, bounded schema/semantic validation / 1 |
| `schemas/review-snapshot.schema.json`, `review-card-content.schema.json`, `review-bundle-manifest.schema.json` | New closed protocols / 1 |
| `scripts/review_card/project.py` | Provider normalization, requirement evaluation, projection states / 2 |
| `scripts/review_card/render.py` | Deterministic HTML/Markdown pair / 3 |
| `scripts/review_card/paths.py`, `bundle.py` | Safe local reads/writes, receipt/inventory, export completion / 4 |
| `scripts/review_card/verify.py` | Offline inventory, anchor, closure, semantic/render consistency / 5 |
| `scripts/review_card/capture.py` | Allowlisted bounded transport and paginated capture / 6 |
| `scripts/review_card/__main__.py` | Commands, structured summaries, exit codes / 7 |
| `fixtures/review-card/complete/snapshot.json`, `payloads/*.json` | Checked-in synthetic source responses; no fabricated live readiness / 1, extended in 2 |
| `tests/review_card_helpers.py`, `tests/test_review_card_contracts.py`, `test_review_card_project.py`, `test_review_card_render.py`, `test_review_card_bundle.py`, `test_review_card_verify.py`, `test_review_card_capture.py`, `test_review_card_cli.py` | Shared fixture constructor/fake transport and owning-unit adversarial tests / 1–7 |
| `docs/review-card/README.md`, `docs/review-card/TRIAL.md`, `.github/workflows/review-card-conformance.yml` | Operator instructions, unfilled actual-use record, candidate-commit evidence / 7 |

Paths in the test row after the first are under `tests/`; schema names after the first are under `schemas/`. Every task stages only its listed files and intentional fixture changes.

Use these shared types in `types.py`: `JsonObject = dict[str, Any]`; frozen `CapturedSnapshot(snapshot: JsonObject, payloads: dict[str, bytes])`; frozen `RenderedCard(html: bytes, markdown: bytes)`; frozen `ExportResult(path: Path, manifest_sha256: str, projection: JsonObject)`; frozen `VerificationReport(integrity: str, issues: tuple[str, ...], captured: CapturedSnapshot | None, projection: JsonObject | None, manifest_sha256: str | None)`. `ReviewCardError(code: str, message: str, exit_code: int = 2)` carries sanitized typed failures. Invalid verification reports contain no trusted projection.

Protocol decisions: all owned nested objects are closed. Snapshot fields are `schema_version`, `repository`, `pr_number`, `capture_started_at`, `capture_completed_at`, `initial_head_sha`, `final_head_sha`, `intended_outcome`, `required_checks` (null or unique strings), `producer` (`version`, `source_commit`), `audience`, `origin`, `observations`, `coverage`. Observation fields are `id`, `kind`, `sequence`, `request_path`, `observed_at`, `source_url`, `payload_path`, `payload_sha256`, `scope` (`head_sha`, `role`), `provider_id`, `provider_timestamp`, `missing_reasons`. Kinds: `pr_metadata`, `check_runs`, `commit_statuses`, `pr_reviews`, `collection_error`; missing reasons are typed string codes keyed by nullable provider fields. Coverage accounts for `pr_metadata`, `check_runs`, `commit_statuses`, `pr_reviews`, with `pages_attempted`, `pagination_ended`, `status`, `reasons` per category.

Card content fields are `schema_version`, `renderer_version`, `subject`, `capture`, `origin`, `intended_outcome`, `required_checks`, `evidence_groups`, `coverage`, `integrity`, `freshness`, `capture_disposition`, `display_state`, `authorization`, `conflicts`, `limitations`, `next_proposed_move`. Subject includes repository, PR and captured head. Groups retain normalized record ID, original commit/time/actor provenance and payload references; separate `checks`, `statuses`, `automated_reviews`, `human_reviews`, `unknown_reviews`. Explicit actor classification is absent in v1; GitHub Bot means automated, User/absent means unknown, human group stays empty. No acceptance field is inferred.

Manifest fields are `schema_version`, `subject`, `snapshot_sha256`, `producer`, `renderer_version`, `payload_count`, `inventory`; inventory entries contain `path`, `size_bytes`, `sha256`, `role` and are sorted by path. Preserve the snapshot's capture producer separately from the manifest's export producer; a later build may use a different source commit, and verification checks each against its own receipt/envelope references rather than silently rewriting capture provenance. Schema reference closure comprises the three new schemas plus the three reused schemas and their recursively reachable local references. `$id` identifiers are not permission to fetch a remote schema.

Fixture constants: `HEAD_A = "a" * 40`, `HEAD_B = "b" * 40`, producer commit `"c" * 40`, PR `123`, outcome `"Inspect exact-head evidence"`, check `"review-card-conformance"`, times `2026-10-03T12:00:00Z` and `2026-10-03T12:00:01Z`, renderer/package version `1.0.0`. `make_capture(*, origin="synthetic_fixture", required_checks=None, final_head=HEAD_A) -> CapturedSnapshot` and `FakeTransport` live in `tests/review_card_helpers.py`; test overrides of origin test evaluation branches, never count as live trial evidence.

## Before execution

Refresh main, instructions, existing schemas and open overlapping PR heads; compare inspected main `8af1f4f5bc4754e1af982d52729aa235e9578ccd` and published spec commit `d5652fd6b602cdf5aa509a79cf4d0ff99e545290`. Check the actual new-file inventory for collisions. Create an isolated worktree using the execution skill; stop for a material interface conflict. Read the approved spec and this plan, then run existing schema/unit conformance checks to establish the baseline. The documentation branch is not a product release.

### Task 1: Strict contracts and synthetic fixture

**Files:** Create `scripts/review_card/{__init__,types,contracts}.py`, the three new schemas named above, `fixtures/review-card/complete/snapshot.json`, `fixtures/review-card/complete/payloads/{pr-before,checks,statuses,reviews,pr-after}.json`, `tests/review_card_helpers.py`; test `tests/test_review_card_contracts.py`.

**Interfaces:** Produces the shared types above, `canonical_json(value: Any) -> bytes`, `sha256(data: bytes) -> str`, `parse_json(data: bytes) -> Any`, `validate_snapshot(captured: CapturedSnapshot, schemas: Mapping[str, JsonObject]) -> None`, `validate_projection(projection: JsonObject, schemas: Mapping[str, JsonObject]) -> None`, `validate_manifest(manifest: JsonObject, schemas: Mapping[str, JsonObject]) -> None`, `schema_closure(root: Path) -> dict[str, bytes]`. `schemas` uses local bundle-relative `schemas/...` keys; all validation uses local-only registries plus format checking and semantic checks. Constants for every global budget live in `contracts.py`.

- [ ] **Step 1: Write contract tests.** Pin assertions such as:
  ```python
  self.assertEqual(canonical_json({"z": 1, "é": 2}), '{"z":1,"é":2}'.encode())
  with self.assertRaises(ReviewCardError): parse_json(b'{"x":1,"x":2}')
  with self.assertRaises(ReviewCardError): parse_json(b'{"x":NaN}')
  self.assertIsNone(validate_snapshot(make_capture(), local_schemas))
  with self.assertRaises(ReviewCardError): validate_snapshot(with_grant_field, local_schemas)
  ```
  Add named boundary cases for depth 32/33, byte size 32 MiB/+1, payload count 256/257, group size 128/129, malformed SHA/time, surrogate Unicode, missing schema and remote `$ref`. Each boundary accepted below/at the limit must be structurally valid; duplicate identical IDs deduplicate semantically in Task 2, conflicting IDs survive as conflicts.
- [ ] **Step 2: Run red.** `PYTHONPATH=scripts python -m unittest discover -s tests -p 'test_review_card_contracts.py' -v`; expect import/function failure for the new package.
- [ ] **Step 3: Implement the listed contracts/types and fixture.** Check input size/depth before recursive validation; catch parser recursion errors as typed failures. Preserve exact payload bytes. Close all nested protocol objects; validate embedded source bindings separately because the reused envelope permits generic objects. Schema-load lookup cannot access the network.
- [ ] **Step 4: Run green.** Repeat Step 2; all contract tests pass, including format and authority rejection.
- [ ] **Step 5: Commit.** Stage this task's files; `git commit -m "feat: define bounded review card contracts"`.

### Task 2: Exact-head normalization and independent review axes

**Files:** Create `scripts/review_card/project.py`; test `tests/test_review_card_project.py`; extend shared helpers/fixtures only for required cases.

**Interfaces:** Consumes Task 1 contracts/types. Produces `project(captured: CapturedSnapshot, *, integrity: str, observation: JsonObject | None = None, offline: bool = False) -> JsonObject` and `validate_observation(observation: JsonObject, captured: CapturedSnapshot) -> None`. Observation file shape: closed `{repository, pr_number, head_sha, observed_at, observer_ref, source_url}`, matching identity and timestamp no earlier than capture completion; it is separately attributed caller data, not authenticated proof.

- [ ] **Step 1: Write projection tests.** Representative assertions:
  ```python
  p = project(live_test_capture, integrity="internally_consistent")
  self.assertEqual(p["projection"]["display_state"], "ready_for_review")
  self.assertEqual(p["projection"]["authorization"], "none")
  self.assertIsNone(p["canonical_uri"])
  self.assertEqual(project(unknown_checks, integrity="internally_consistent")["projection"]["display_state"], "blocked")
  self.assertEqual(project(changed_head, integrity="internally_consistent")["projection"]["display_state"], "stale")
  self.assertEqual(project(live_test_capture, integrity="internally_consistent", offline=True)["projection"]["freshness"], "not_checked")
  ```
  Named tests pin explicit `[]`, missing/pending/failing checks, same name with distinct app/context identities, old-review commit, synthetic merge SHA, provider User/Bot/null attribution, duplicate IDs same/different hashes, reordered records, missing timestamps, altered base/mergeability, wrong-PR/older observation, and synthetic/caller origin. Offline present state is blocked unless a valid comparable observation supplies freshness; historical `capture_disposition` remains unchanged. Fixtures never establish live provenance.
- [ ] **Step 2: Run red.** `PYTHONPATH=scripts python -m unittest discover -s tests -p 'test_review_card_project.py' -v`; expect missing `project` implementation.
- [ ] **Step 3: Implement `project` and `validate_observation`.** Stable sort by kind/provider ID/head/source timestamp; arrival sequence is provenance only. Match required names exactly across qualifying head checks/statuses; multiple distinct contexts are ambiguous. Within one context, require a unique comparable latest provider observation; missing/equal-conflicting times block. Only check conclusion `success` and status state `success` satisfy a requirement. Preserve nonqualifying evidence visibly. Set stale first for comparable changed heads; otherwise apply the spec's blockers. Do not infer merge policies. Populate one work/candidate/pull source binding, hash nested content for envelope `content_hash`, and use explicit capture completion for `generated_at`.
- [ ] **Step 4: Run green.** Repeat Step 2 plus Task 1 tests; all axes and normalization cases pass.
- [ ] **Step 5: Commit.** `git commit -m "feat: project exact-head review evidence"` after staging this task's files.

### Task 3: Deterministic static cards

**Files:** Create `scripts/review_card/render.py`; test `tests/test_review_card_render.py`.

**Interfaces:** Consumes validated Task 2 projection. Produces `render_card(projection: JsonObject) -> RenderedCard`; accepts only renderer `1.0.0`. No filesystem access or transport. HTML and Markdown share semantic field/excerpt ordering.

- [ ] **Step 1: Write renderer tests.** Assert `render_card(p) == render_card(p)`, both outputs contain `HEAD_A` and textual blocked reasons; HTML escapes `<script>` as `&lt;script&gt;`, Markdown escapes raw HTML and delimiters, both explicitly identify excerpts above 16,384 characters. Pin `test_no_action_controls_or_external_assets`, `test_unknown_actor_is_not_human`, `test_local_links_and_https_github_only`, `test_unsupported_renderer`, `test_historical_capture_header`, and `test_390px_styles_and_focus`. Reject credential-bearing/executable links instead of emitting them.
- [ ] **Step 2: Run red.** `PYTHONPATH=scripts python -m unittest discover -s tests -p 'test_review_card_render.py' -v`; expect missing renderer.
- [ ] **Step 3: Implement `render_card`.** Fixed inline stylesheet and CSP (`default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'`), UTF-8 charset, escaped attribute/text contexts. Use bounded excerpts with original payload links; no remote images/fonts/scripts. Header labels capture-time disposition as historical and includes present-freshness caveat. Use one h1, ordered h2 sections, breakable hashes, scrollable tables with accessible labels and visible focus. Every actionable-looking link is a citation/evidence link, not an execution control.
- [ ] **Step 4: Run green.** Repeat Step 2 and projection tests; deterministic bytes and injection cases pass. Record automated CSS assertions as mechanical checks, not a keyboard/browser trial.
- [ ] **Step 5: Commit.** `git commit -m "feat: render static review cards safely"` after staging this task's files.

### Task 4: Exclusive complete bundle publication

**Files:** Create `scripts/review_card/paths.py`, `scripts/review_card/bundle.py`; test `tests/test_review_card_bundle.py`.

**Interfaces:** Consumes validated capture, `project`, `render_card`, schema closure and hashing. Produces `load_snapshot(path: Path) -> CapturedSnapshot`, `read_bundle_files(path: Path) -> dict[str, bytes]`, `validate_relative_path(path: str) -> str`, `export_bundle(captured: CapturedSnapshot, destination: Path, *, producer: JsonObject, started_at: str, completed_at: str) -> ExportResult`, `write_rendered(card: RenderedCard, destination: Path, *, source: Path) -> Path`. Package schema resources resolve from installed module location, never cwd. Snapshot input is the declared snapshot/payload closure only; extra files are rejected.

- [ ] **Step 1: Write bundle tests.** Pin complete-file inventory, exact payload byte preservation, succeeded receipt with `run_type == "project"`, `authority_ref is None`, non-null completion/hash, and output hashes excluding `receipt.json`/`manifest.json`. Assert a blocked card can yield a succeeded export with explicit outcome. Pin occupied output exit 4 without changes; absolute/`../`/backslash/drive/case collision/reserved paths and symlink ancestors fail; input overlap fails; fault injection at payload write/marker publication leaves no `manifest.json`, never removes earlier exports, and retry to another destination succeeds.
- [ ] **Step 2: Run red.** `PYTHONPATH=scripts python -m unittest discover -s tests -p 'test_review_card_bundle.py' -v`; expect missing bundle functions.
- [ ] **Step 3: Implement the listed path/bundle functions.** On the initial Linux target use descriptor-relative no-follow reads and exclusive/no-follow file creation to reject symlink swaps, not just preflight `resolve()`. Reserve the new directory exclusively, write the declared files, validate all schema/semantic/render/ref checks in memory and read back bytes, then finalize receipt and sorted inventory. Receipt `input_refs` use `sha256:DIGEST` for the input snapshot; `output_refs` are sorted bundle-relative output paths excluding receipt/manifest; `evidence_refs` are sorted payload paths; `content_hashes` maps exactly those output paths to digests. Set `metrics.exporter_version`/`metrics.exporter_commit`, null `authority_ref`, immutable true and explicit review disposition in `outcome`; derive receipt ID/idempotency key from input digest and explicit times. Manifest temporary file is outside the bundle; publish using a Linux same-filesystem exclusive hard link and remove only that temporary file. No replace operation, success marker on failure, or directory-transaction claim. Copy the exact schema closure; manifest roles distinguish payload/schema/protocol/card/instructions. Static bundle README states scope and external-anchor limits.
- [ ] **Step 4: Run green.** Repeat Step 2 and Tasks 1–3; all write/ref/hash/fault tests pass.
- [ ] **Step 5: Commit.** `git commit -m "feat: export complete review bundles exclusively"` after staging this task's files.

### Task 5: Offline verification, anchor, and reopen view

**Files:** Create `scripts/review_card/verify.py`; test `tests/test_review_card_verify.py`.

**Interfaces:** Consumes Tasks 1–4 types, safe file reader, project and renderer. Produces `verify_bundle(path: Path, *, expected_manifest_sha256: str | None = None) -> VerificationReport`, `reopen_projection(report: VerificationReport, *, observation: JsonObject | None = None) -> JsonObject`. Verification is network-free. Reopen returns a fresh in-memory view; it never edits the archived projection/card/manifest.

- [ ] **Step 1: Write verifier tests.** Assert valid unanchored integrity `internally_consistent`, matching anchored integrity `verified_against_anchor`, changed payload/missing payload/missing schema/extra file/symlink/missing marker integrity `invalid` with no trusted projection. Rehashing altered payload+inventory must still fail original external anchor; internally consistent full replacement is explicitly not authenticity proof. Tail-loss count/ref failures and full internally rehashed tail replacement with original anchor are distinct tests. Altered card bytes, forged receipt output references, projection-head mismatch and unsupported renderer fail even after manifest rehash. Copy into `"copied PR évidence"`, delete original, change cwd, disable transport, and assert fresh-process verify/reopen still works with freshness `not_checked` and preserved `capture_disposition`.
- [ ] **Step 2: Run red.** `PYTHONPATH=scripts python -m unittest discover -s tests -p 'test_review_card_verify.py' -v`; expect missing verifier.
- [ ] **Step 3: Implement `verify_bundle` and `reopen_projection`.** Enumerate safe regular files, require exact inventory plus manifest, check byte sizes/hashes/counts and supported identities/versions, locally resolve schema closure, validate snapshot/binding/projection/receipt semantics, recompute receipt hash omitting only its own hash, compare projection to deterministic derivation, regenerate both card byte streams. Stored projection uses `internally_consistent` as its construction basis; a supplied anchor strengthens the returned report/reopen view without changing stored bytes. Check external digest before trusting content. Report integrity basis separately from source trust and review state. Reopen reprojects with `offline=True` and validated optional observation; anchor presence does not assert source authenticity.
- [ ] **Step 4: Run green.** Repeat Step 2 and bundle tests; every copy/tamper/closure case passes without network requests.
- [ ] **Step 5: Commit.** `git commit -m "feat: verify and reopen portable review bundles"` after staging this task's files.

### Task 6: Bounded exact-head GitHub collection

**Files:** Create `scripts/review_card/capture.py`; test `tests/test_review_card_capture.py`; extend `FakeTransport` helpers.

**Interfaces:** Consumes Task 1 types/parser/limits. Produces frozen `HttpResponse(status: int, headers: Mapping[str, str], body: bytes)`, `Transport.get(path: str, *, timeout: float) -> HttpResponse` protocol, `GitHubTransport(token: str | None)` implementation, and `capture_pr(pr_number: int, *, outcome: str, required_checks: list[str] | None, producer: JsonObject, transport: Transport, utc_now: Callable[[], str], monotonic: Callable[[], float]) -> CapturedSnapshot`. Headers are transient pagination/rate observations, never stored credentials. Clock injection gives deterministic tests and real live observations.

- [ ] **Step 1: Write transport/capture tests.** Assert first/last PR GET surround all exact-`HEAD_A` evidence requests; a final `HEAD_B` yields stale projection with original head-scoped payloads. Pin multi-page termination, malicious/cross-host Link header, fixed GET-only allowlist, no redirects, request count 200/+1, page count 100/+1, response 2 MiB/+1, total 32 MiB/+1, deadline 120 seconds, timeout at most 10 seconds and no retries. Nullable/deleted actors and provider dates preserve typed absence. Denied/rate-limited/malformed/timeout evidence creates incomplete coverage when identity exists; initial identity failure raises exit 3. Seed a fake token in transport errors/URLs and assert it is absent from payloads, error summaries, cards and receipts.
- [ ] **Step 2: Run red.** `PYTHONPATH=scripts python -m unittest discover -s tests -p 'test_review_card_capture.py' -v`; expect missing collector.
- [ ] **Step 3: Implement the listed collector interfaces.** Use stdlib HTTPS with redirect handling disabled, bounded streaming and sanitized errors. Send pinned GitHub API version `2026-03-10` and JSON accept header. Read `/repos/Quirk-Systems/quirk-os/pulls/N`, then `/commits/HEAD/check-runs?filter=all&per_page=100&page=P`, `/commits/HEAD/statuses?per_page=100&page=P`, `/pulls/N/reviews?per_page=100&page=P`, then PR again (all under fixed repo prefix). Validate pagination only for the identical endpoint/head/allowed query with advancing page; never follow supplied hosts. Check-run API's provider ceiling/inconsistent counts block completeness rather than imply full history. Preserve successful response bytes and bounded sanitized collection-error payloads; account for every category, including failed final-head read. Never substitute empty evidence for failure or retarget to the final head.
- [ ] **Step 4: Run green.** Repeat Step 2 and Tasks 1–5; fake transport exhaustions and source-race cases pass. Tests invoke no real credentials/network.
- [ ] **Step 5: Commit.** `git commit -m "feat: capture bounded read-only PR evidence"` after staging this task's files.

### Task 7: Operator commands and candidate conformance evidence

**Files:** Create `scripts/review_card/__main__.py`, `docs/review-card/README.md`, `docs/review-card/TRIAL.md`, `.github/workflows/review-card-conformance.yml`; test `tests/test_review_card_cli.py`.

**Interfaces:** Consumes capture/export/verify/reopen/render/load interfaces above. Produces `main(argv: Sequence[str] | None = None) -> int` and one JSON result on stdout for each command. `capture --pr N --out NEW --outcome TEXT [--require-check NAME ... | --require-no-checks]`; `build --snapshot INPUT --out NEW`; `verify BUNDLE --expected-manifest-sha256 DIGEST`; `reopen BUNDLE [--expected-manifest-sha256 DIGEST] [--observation FILE]`; `render BUNDLE --out NEW`. Explicit empty requirements use `--require-no-checks`; omitted options mean null. Repeat names deduplicate in first-declaration order; empty/whitespace-only names are invalid, and meaningful names are never trimmed/rewritten. Runtime producer source commit is read from installed source via fixed `git rev-parse HEAD` argv without shell/source text after confirming product source/schema files are clean; if unavailable require explicit `--producer-commit SHA` on capture/build, label it operator supplied and never guess. A supplied commit cannot override a detected dirty/mismatched checkout.

- [ ] **Step 1: Write subprocess CLI tests.** Pin exit codes 0/2/3/4 and independent review axes, stdout valid JSON, no token/traceback leak, required verify anchor, explicit no-check vs unknown vs invalid check names, invalid/wrong-PR/older observation, invalid PR/producer commit, blocked-success summary and unavailable identity. Run build→copy→fresh-process verify→reopen→render from a changed cwd/Unicode path with network disabled; compare saved capture card byte regeneration and reopen historical vs present state. Render writes only a new card pair with present freshness caveat and refuses existing/overlapping output. Offline commands must not initialize transport or read `GITHUB_TOKEN`.
- [ ] **Step 2: Run red.** `PYTHONPATH=scripts python -m unittest discover -s tests -p 'test_review_card_cli.py' -v`; expect absent CLI or failing command semantics.
- [ ] **Step 3: Implement `main` and operator docs.** Summaries include command status, subject/head, review state, coverage, freshness, integrity basis, output path, manifest digest and typed errors. `reopen` includes the derived view in JSON and does not overwrite the bundle. README explains anchor retention, capture scope, unknown requirements, historical status, origin, install/version requirements, interruption recovery, exact command examples and private audience. TRIAL remains an unfilled template for actual host/tool/PR/head, transfer steps, assistance/correction/cleanup and Bryan's stated usefulness judgment. No simulated user outcome.
- [ ] **Step 4: Add conformance workflow.** Pull-request path filters cover every new path, relevant reused schemas and `requirements.txt`; manual dispatch permitted. Use contents-read permission, PR head checkout with persisted credentials disabled, tested-head assertion and Python 3.12/3.13 matrix. Match current repository action pins with version comments: checkout `3d3c42e5aac5ba805825da76410c181273ba90b1` (v7.0.1), setup-python `5fda3b95a4ea91299a34e894583c3862153e4b97` (v7.0.0), upload-artifact `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` (v7.0.1); refresh upstream identity before execution. Install pinned existing requirements, run unittest suite with pipefail, build synthetic fixture export, verify its separately captured digest, retain logs/summary/fixture bundle for 30 days including failures. Keep Evidence Binding caller unchanged.
- [ ] **Step 5: Run green and candidate checks.** `PYTHONPATH=scripts python -m unittest discover -s tests -p 'test_review_card*.py' -v`; then repository full unittest discovery and existing schema conformance commands. Build/verify the checked-in synthetic fixture in a new temp directory; all checks pass and fixture summary says synthetic/blocked. Inspect HTML at 390 px and desktop, keyboard-only citation focus and Markdown parity in an available browser; record actual result or explicitly pending, never replace it with CSS assertions.
- [ ] **Step 6: Commit.** `git commit -m "feat: expose review card commands and conformance evidence"` after staging this task's files.

## Whole-branch review and actual-use checkpoint

Run the selected execution method's independent whole-branch review against the exact candidate commit. Invoke authenticated CodeRabbit on that scoped implementation diff; currently CLI 0.8.2 is installed but unauthenticated, so CodeRabbit evidence is pending. Provision through a user-controlled terminal or supported secret mechanism, never plaintext chat. A failed/unavailable CodeRabbit invocation is not replaced or relabeled by manual review. Fix material findings and rerun affected tests only as justified.

Perform one actual PR capture with explicitly declared outcome/check requirements, retain its manifest digest separately, copy to a separate destination/host and reopen without source access. Record both hosts and exact tool version. Ask Bryan to identify exact-head evidence and bot-versus-human approval, then record his actual usefulness/assistance/cleanup judgment in TRIAL. If browser, independent-host exercise, live access, hosted CI or authenticated review is unavailable, report that gate as pending and retain Constrain status; do not mark it passed. No merge, deployment or runtime admission is part of this execution plan.

## Coverage and self-review

| Spec sections | Owning work |
| --- | --- |
| 1–3 scope, reuse, package boundary | Global constraints, file map, pre-execution refresh; Tasks 1–7 |
| 4 journey, CLI, accessibility | Tasks 3 and 7; actual browser checkpoint |
| 5 contracts, identity, axes, receipt | Tasks 1, 2, 4 and 5 |
| 6 closure, safe completion, anchor, transfer | Tasks 4, 5 and 7 |
| 7 read-only transport, hostile inputs, exact limits | Tasks 1, 3, 4 and 6 |
| 8 deterministic order, errors, failure semantics | Tasks 1, 2, 4–7 |
| 9 acceptance and user/platform evidence | Tests in each task, CI and actual-use checkpoint |
| 10 review gates, admission/rollback boundary | Review checkpoint; disable future tool use without changing old exports |

Self-review performed before publication: every spec section has an owning task; shared function names/types match downstream consumers; all five Review Focus cases have explicit tests; limits/identity/protocol values are pinned; task steps name checkable outputs without implementing bodies. This is a seven-task plan of the same order of length as its spec, with no product code or executed feature tests claimed. Native execution is recommended for the tightly coupled package interfaces, followed by the required fresh whole-branch reviewer and scoped CodeRabbit gate.

## Primary documentation consulted

Read current endpoint details again during execution if provider behavior changes: [GitHub check runs](https://docs.github.com/en/rest/checks/runs), [commit statuses](https://docs.github.com/en/rest/commits/statuses), [PR reviews](https://docs.github.com/en/rest/pulls/reviews), and [REST pagination](https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api). Provider metadata is evidence with declared coverage, not authority.
