# Media Care to Evidence Graph Implementation Plan

**Goal:** Turn an existing saved Media Care inspection into a source-bound, private review handoff without rebuilding its producer, controller, registry, or authority model.

**Architecture:** Consume `media-care-check.v1` reports as unsigned declarations. Emit the existing `projection-envelope.v1` with existing Engineering graph object/assertion records. Use the actual `EvidenceGraph` consumer from PR #79 for impact/context checks; all upstream care assertions stay `declared`.

**Tech stack:** Python 3.12+, jsonschema, the unchanged Engineering graph implementation.

**Spec:** `docs/mixed-media/MEDIA-REVIEW.md` in this change; upstream PR #78 at 53577f28d3c26f4502996982bf3e12c8ed115cc2 and PR #79 at e6344a1a13f359bf8e485a6d2b4d3143749c2600.

## Global constraints

- This is an additive candidate report adapter, not a media decoder, source authenticity verifier, live agent runner, new portable Skill, or production provider adapter.
- Preserve original asset IDs, selection attribution, findings, source date, and unknown human benefit in the retained report.
- A caller-supplied raw SHA-256 binds the exact source bytes; a hash does not establish authority or truth.
- Every graph object is principal-restricted; metadata-view identities must not impersonate the canonical asset identities.
- No grant, preferences, training permission, activation, public publishing, paid jobs, or production settings changes.
- Source report <= 1 MiB, <= 64 assets, <= 128 findings, <= 256 dependency edges. Reject duplicate keys, nonfinite JSON, broken dependencies, cycles, malformed selections, and expanded authority.
- Export is new-directory-only with private POSIX permissions; local files are unencrypted and unsigned. No overwrite or automatic retry after an uncertain write.
- Public repository fixtures are synthetic. A Library snapshot is used only for a private local integration probe.

The additive parent was refreshed to mixed-media PR #81 at `d3d44e461929c0446d1d8de8794e828ea71d180b` after that draft appeared during this pass. Its production compiler remains unchanged; this adapter consumes saved care reports rather than production briefs.

## Task 1 — Report handoff and native consumer proof

Files: `scripts/prepare_media_review.py`, `tests/test_media_review.py`.

Interface: `prepare_report(raw: bytes, *, expected_sha256: str, tenant_id: str, principal_id: str, captured_at: str) -> dict`.

- [x] Fetch graph.py and three schemas at immutable commits; verify Git blob identities locally.
- [x] Author a synthetic native report fixture and failing behavior tests before implementing the adapter.
- [x] Observe `test_existing_projection_and_native_graph` fail because the adapter returns no projection.
- [x] Implement bounded parsing, scope checks, reference closure, conservative graph mapping, and one proposed review task per retained finding.
- [x] Run `python -m unittest discover -s tests -p test_media_review.py -v` and retain output.
- [x] Run the real saved report through the adapter and unchanged graph consumer, distinguishing current local behavior from the report's historical producer claims.

## Task 2 — Private export and replay

Same implementation/test files. Interface: `export_review(raw, destination, **host_context)` and `verify_review(destination, **host_context)`.

- [x] Author no-overwrite, tamper, changed-host-context, and private-output tests.
- [x] Export exact `source.json`, deterministic `review.json`, and plain `REVIEW.txt` in a newly created directory.
- [x] Reopen by recomputing all output bytes against the caller's exact source digest and host context; refuse partial or altered packages.
- [x] Retain human usefulness as unobserved. A replay result only establishes local consistency.

## Task 3 — Evidence, operational documentation, and projections

Files: operating guide, evaluation receipt, and synthetic JSONL regression descriptions. Existing path-scoped Engineering CI is reused; no workflow is added.

- [x] Record executed tests, source hashes, source pins, limits, and unavailable Plugin Eval CLI honestly.
- [ ] Create a draft candidate branch; do not merge or weaken existing gates.
- [ ] Correct existing Airtable stale merge/runtime assertions and verify retained statuses/timestamps.
- [ ] Append a dated continuation to the existing Drive work-plane Doc with revision control.
- [ ] Create bounded Linear work with implemented versus human/live-blocked acceptance states; retain exact reference links.
- [x] Record Supabase timeout/inactive and Hugging Face scope/server restrictions without provisioning or uploading.
