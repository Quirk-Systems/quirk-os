---
name: quirk-data-refinery
description: Plan and execute bounded, idempotent cleaning of structured and unstructured Quirk data while preserving raw sources, provenance, exceptions, rollback, and human review.
---

# Quirk Data Refinery

## Quirk contract

- Version: `0.1.0`
- Status: `candidate`
- Authority ceiling: `propose`
- Default mode: dry-run and sampled proof

## Refinery route

`inventory → fingerprint → preserve raw → parse → normalize → repair → deduplicate → resolve entities → classify → validate → quarantine → project → receipt`

## Requirements

- Content-address every input and transform version.
- Make batches resumable and replay-safe.
- Preserve original bytes or source references before transformation.
- Use deterministic rules before probabilistic inference.
- Quarantine malformed, suspicious, conflicting, or rights-unclear records.
- Never silently delete, merge, or overwrite history.
- Report pre/post quality metrics and sampled examples.
- Set maximum batch size, cost, time, and blast radius.

## Output

A cleanup plan, transform specification, exception queue, quality delta, rollback or compensation route, and run-receipt template.

## Stop conditions

Stop when identity collisions, uncertain ownership, protected data, unclear licensing, or irreversible cleanup exceeds the supplied authority grant.
