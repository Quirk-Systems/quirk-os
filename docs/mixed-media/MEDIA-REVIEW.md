# Saved Media Care to private review handoff

Candidate implementation owned by `Quirk-Systems/quirk-os`.

## Outcome

A saved `media-care-check.v1` inspection can become a private, replayable review projection consumed by the existing `EvidenceGraph`. Original report bytes, asset references, selection attribution and every open finding are retained. Each finding becomes a proposed review task with a finish condition; nothing is dispatched or approved.

This is not another production planner, scheduler, grant registry or Quirk primitive. PR #81 remains the production-brief compiler. This adapter consumes the different existing report produced by PR #78; it does not convert findings directly into executable production stages.

## Compatibility

- Producer inspected: PR #78 at `53577f28d3c26f4502996982bf3e12c8ed115cc2`; report `media-care-check.v1`, tool `0.2.0`.
- Native graph consumer: PR #79 at `e6344a1a13f359bf8e485a6d2b4d3143749c2600`.
- Additive parent: PR #81 at `d3d44e461929c0446d1d8de8794e828ea71d180b`.
- Existing outer contract: `projection-envelope.v1`, `authority_class=projection`.
- Domain payload: `media-review-handoff.v1` inside `projection`; not a replacement foundational envelope.
- Graph: unchanged Engineering object/assertion v1 schemas and `EvidenceGraph`.

This is a bounded consumer profile, not the entire producer validator. Unknown protocol fields and unsupported producer versions fail closed. Metadata-view identities and digests do not impersonate canonical asset identities or media-byte hashes. Original asset references remain in the retained report and view mapping.

## Run and reopen

Use Python 3.12+ and the parent's unchanged `requirements-evals.txt` (`jsonschema==4.26.0`, `PyYAML==6.0.3`). No dependency or CI permission is added.

```sh
python -m unittest discover -s tests -p 'test_media_review.py' -v

python scripts/prepare_media_review.py prepare \
  --input examples/media-review/synthetic-report.json \
  --expected-sha256 e9ed13ab9764d25888580058b5fe23f5be11bf40c01da6a2b87bc001614ea41d \
  --tenant-id fixture-tenant --principal-id fixture-reviewer \
  --captured-at '2026-09-10T12:00:00+00:00' \
  --directory /tmp/quirk-media-review-new

python scripts/prepare_media_review.py verify \
  --expected-sha256 e9ed13ab9764d25888580058b5fe23f5be11bf40c01da6a2b87bc001614ea41d \
  --tenant-id fixture-tenant --principal-id fixture-reviewer \
  --captured-at '2026-09-10T12:00:00+00:00' \
  --directory /tmp/quirk-media-review-new
```

The export contains exact `source.json`, deterministic `review.json`, and plain `REVIEW.txt`. A new directory is required. Replay recomputes every byte against caller-supplied source, tenant, principal and historical capture expectations. Altered, partial and unexpected inventories fail. Exit 0 is local-operation success, not approval; exit 2 is rejection.

For real work, select the source and expected capture digest deliberately. Do not resolve a mismatch by blindly trusting a replacement file's new hash. The example capture is a synthetic timestamp, not a live authorization clock.

## Decomposition and settings

Goal: resume the selected review without reconstructing sources, alternatives or open issues. Tasks retain the original finding, source-bound ID, review method, finish condition, unassigned owner and `authorization=none`. Global findings precede selected-version dependencies, then alternatives. This is transparent ordering, not a quality score.

Ownership, provenance, rights and accessibility have named review methods. Unknown warning codes remain manual-review tasks. No portable Skill is registered or admitted. One task in progress is suggested, not installed as a system-wide limit. Review tasks are not loop steps.

Enforced bounds: source report 1 MiB; 64 assets; 128 findings; 256 dependency edges; 8 MiB per exported file. Duplicate keys, nonfinite JSON, unresolved references, cycles, missing selection dependencies and expanded authority are rejected. Impact queries are bounded to depth 8 and retain truncation. Sources older than seven days gain a revalidation hold without losing historical findings.

New POSIX directories use 0700 and files use 0600. Every graph object is principal-restricted. These are unencrypted, unsigned local files; host identity is not authenticated here. Symlink/non-following regular-file checks are defense in depth, not a hostile concurrent filesystem sandbox or a crash-durable distributed ledger.

## Evidence and authority

All imported graph assertions remain `declared`, including the producer's `integrity=verified` statement. The native graph excludes declarations from observed support. The producer is not rerun or authenticated. Agent selection stays agent-attributed and unsigned; no human preference or `prefers` edge is manufactured.

No rights clearance, accessibility quality, current freshness, human benefit, grant installation, source-media upload, classifier, rendering, training, delivery or production admission is inferred. Private in-memory graph preparation is not application to an accepted or persistent graph. Source-change impact is a query result, not an automatic repair trigger. Host-managed documentation/record updates are separate from the adapter's zero-provider-effect claim.

The focused local suite passed 30 tests. Exact source hashes and scope are in `MEDIA-REVIEW-EVIDENCE.json`. Parent full suites were not rerun locally. A separate private saved-report probe retained three asset descriptions and six findings, prepared six tasks, constructed ten graph objects and sixteen assertions, found nine affected objects, and passed export/reopen. No private source content or workspace identifiers are included in this public change.

The existing Engineering CI already covers these script/test paths. Assess hosted results at the new exact head, not the parent. Plugin Eval CLI was absent; no CLI run or numeric plugin score is claimed. The synthetic JSONL regression catalog is not held-out data or model-performance evidence. No Hugging Face upload occurred.

## Product finish and reversal

The existing Studio/Now consumer move remains open. Its next proof is to expose source, selection and warnings, reopen after a source change, and let a person judge reconstruction and cleanup. Record setup, supervision, cleanup, manual rescue and keep/change/drop. Automated tests do not finish the UI consumer, human trial, provider adapter or delivery move.

Reject the draft or revert the additive child commit to reverse the implementation. Main, the producer, the graph engine, frozen evaluators, provider settings, grants and historical receipts are unchanged by this adapter.
