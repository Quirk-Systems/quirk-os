# Source-aware review capability — candidate

Owner: `Quirk-Systems/quirk-os`. Capability: `capability.partials-source-review/v0.1.0`. Operating depth: one Vertical Slice. Mission: consume existing partial records with explicit source expectations, preserve useful partials and every input disposition, and produce a reproducible inspect-only mobile review.

Acceptance evidence: exact replay; stale/mismatched source rejection; preserved unknown counts and upstream holds; mixed-batch accounting; duplicate/conflict handling; inert mobile output; and an unchanged no-effect ceiling. Bound: 1–32 JSON entries, at most 1 MiB, supplied age limit 0–604800 seconds. This is local CPU/file work only. No external consumer, service, account, runtime or authority policy is changed.

## Receiver operations

```sh
node scripts/cli.mjs review fixtures/review-request.json new-review.json
node scripts/cli.mjs review-panel fixtures/review-request.json new-review.html
```

Import `reviewRecords`, `verifyReview`, or `renderReviewPanel` through `@quirk-systems/partials-candidate/review`. The CLI reads one regular request file within the byte bound and exclusively creates one output. The static [example review](Review-Panel.html) includes all three adapter record shapes and one intentionally malformed input. Its captures are explicitly synthetic; no new source or human-use evidence is asserted.

The request contract has `captured_at`, `max_age_seconds`, and entries containing `source_ref`, `record`, `max_count`, and `expectation`. An expectation is either null or `{subject, source_ref, observed_at}`. Obtain the expected subject from the owning input/adapter or a separately checked source; copying the old record's subject supplies no independent freshness evidence. The record and expectation timestamps must be within the supplied age limit and must not be in the future. Age limits are caller policy, not validated defaults about personal capacity or safety.

| Result | Meaning | Recovery |
| --- | --- | --- |
| `matched` | Full subject tuple agrees; both timestamps fit the supplied bound | Inspect partial facts and holds; no admission follows |
| `quarantined / invalid_record` | Structural or semantic record failure | Repair at owning source, preserve original request, rerun |
| `quarantined / expectation_missing` | No source expectation supplied | Obtain and document an expectation |
| `quarantined / subject_mismatch` | Identity, source version or digest differs | Fetch/recompute the correct version; never rename stale evidence as current |
| `quarantined / stale_capture` or `future_capture` | Timestamp lies outside policy | Re-observe source or correct time with evidence; never refresh a timestamp merely to pass |
| `quarantined / identity_conflict` | Same system, subject ID and scope ID have differing data, expectations or count policy | Reconcile explicitly outside the review; all conflicting valid versions are held |
| `duplicate / exact_replay` | Exact record, expectation and policy already represented | Retain row and reference first input; no domain count is added |

Every input has an indexed row and canonical JSON fingerprint. Quarantined raw data is not rendered. Valid inputs' upstream holds remain in the review-level authority even when quarantined. Counts describe dispositions, never a summed cross-system inventory. No human choice or conflict resolution is fabricated.

## Receipt and recovery

The request remains the retained source artifact. A result records its request digest, every disposition, matched records and policy, fixed authority, and a digest over the result before the receipt. `verifyReview(request, result)` reruns the transform and compares the entire result; matching a supplied hash alone is insufficient. Source references, timestamps and digests are unsigned caller data. The candidate does not provide authenticated history, remote current-head checks or a persistent quarantine service.

Corrections produce a new request and output file; prior artifacts remain intact. Reverting this consumer removes only the review import/CLI usage. Native inputs, graph, calendar, runtime and Canon remain untouched. Existing partial-record v1alpha1 remains compatible; the new request and result schemas have separate version identities. The original `panel` command is still a basic snapshot renderer. Consumers requiring source comparison must use `review-panel`.

## Compounding dividend and boundaries

Implemented: one reusable source-aware consumer shared by OS, Preference and Skills records; one request/result grammar; one receipt; one mobile renderer; explicit failure and recovery paths. The contract, deterministic tests and future freshness monitoring are distinct mechanisms. No monitor or controller was introduced.

Measured technical delta: tests expose a stale but structurally valid record that the basic snapshot renderer can display; the review consumer quarantines it while preserving the matched control. Mixed input tests retain valid records and account for malformed ones. This proves the bounded fixture behavior, not user benefit or production reliability.

Compounding fixtures exercised: mixed-source preservation (2), identity accounting (3), uncertain classification to review (4), stale guidance (7), and successful capability denied self-promotion (11). Canon resolution, research synthesis, skill routing, Roadmap admission and product publication fixtures are outside this consumer's operations; no passing claim is made for them.

OPEN: independent human review, observed browser/iPhone review and correction, real completion/effort/benefit, authenticated expectation acquisition, and external application wiring. Next Proposed Move: wire one existing Inspector to this request/result API and observe a real source correction without silently modifying its timestamp or granting authority.

Disposition: **Constrain** — locally implemented candidate consumer; broader rollout and human benefit remain unverified.
