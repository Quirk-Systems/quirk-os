# Quirk Sync Control Plane

**Version:** 0.2.0 candidate  
**Authority ceiling:** observe, infer, persist private runtime state, rebuild projections, and propose  
**Admission:** human decision required  
**Protected:** Canon promotion, authority expansion, manifest activation, merge, destructive history mutation, and production deployment

The Sync Control Plane provides one interoperable identity, authority, mapping, evidence, and projection spine across GitHub, Supabase, Google Drive, Airtable, Notion, Vercel, and a deliberately deferred Cloudflare boundary.

## Authority topology

| Platform | Plane | Owns | Never owns |
| --- | --- | --- | --- |
| GitHub | canonical | schemas, policies, manifests, migrations, evals, executable specifications | live runtime state |
| Supabase | runtime | bindings, cursors, immutable receipts, transition ledger, Proposed Moves, outbox, observed outcomes | Canon or human admission |
| Google Drive | work | source intake, authored drafts, review packs, archive context | executable Canon |
| Airtable | projection | portfolio, work queue, decisions, binding and manifest inspection | Canon or runtime truth |
| Notion | projection | orientation, interpretation, onboarding, RFC synthesis | Canon or runtime truth |
| Vercel | delivery projection | admitted interface delivery | Canon, policy, or database authority |
| Cloudflare | deferred edge candidate | future inventory only | runtime, Canon, or unadmitted deployment |

## What v0.2 hardens

1. **Manifest admission** — `active` requires independent approval, an authority grant, evaluated content hash, legal transition evidence, and non-empty evals and stop conditions.
2. **Self-promotion rejection** — requester and approver cannot be the same actor; schema, policy, Python tests, and a database trigger all enforce the boundary.
3. **Immutable evidence** — receipts and manifest-transition records are append-only; corrections supersede rather than rewrite.
4. **Typed decision contracts** — freshness, trigger routing, label review, taxonomy gaps, contradictions, capacity, and rights are explicit objects.
5. **Drift control** — observed hash mismatch marks a binding drifted, blocks silent repair, and emits a typed Proposed Move.
6. **Bounded delivery** — outbox claims use leases and `SKIP LOCKED`; retries stop at five and enter dead letter with evidence.
7. **Projection reconstruction** — canonical identity plus runtime state can rebuild a projection envelope.
8. **Canonical/runtime mappings** — `receipt_id↔receipt_key`, `binding_id↔binding_key`, and `object_key↔object_id` are versioned and tested.
9. **Independent CI** — sync conformance runs separately from stacked Golden Project Pack admission.
10. **Cloudflare boundary** — represented as `DEFER_UNBOUND`, never silently promoted into the active platform topology.

## Execution flow

```text
GitHub candidate/canon
  -> validate schemas and admission contract
  -> Supabase private runtime
  -> immutable receipt + transition record
  -> bounded projection outbox
  -> Drive / Airtable / Notion projections
  -> Vercel only after admission
  -> Cloudflare remains deferred
  -> observed drift or feedback
  -> typed Proposed Move
  -> GitHub candidate change
```

## Local conformance

```bash
python -m pip install -r requirements-evals.txt
python -m unittest discover -s tests -p 'test_*.py' -v
python scripts/validate_sync_control_plane.py --repo . --require-admit
```

A successful run means **eligible for a human admission decision**. It does not activate the candidate.

## Database proof

Apply the candidate migration, then execute the transactional proof script:

```text
supabase/migrations/20260812030000_sync_control_plane_contracts.sql
supabase/migrations/20260812030001_sync_control_plane_evidence.sql
supabase/migrations/20260812030002_sync_control_plane_delivery.sql
supabase/tests/sync_control_plane_hardening.sql
```

The proof transaction rolls back all test data while asserting valid activation, self-promotion rejection, rights blocking, trigger collision blocking, duplicate identity rejection, idempotent receipts, append-only history, deferred Cloudflare representation, dead-letter exhaustion, drift-to-Proposed-Move behavior, and projection reconstruction.

## Admission checklist

- [ ] Candidate conformance workflow passes.
- [ ] Supabase transactional proof passes on the intended environment.
- [ ] Runtime and canonical mappings round-trip.
- [ ] All eleven fixtures pass.
- [ ] No browser-role runtime privileges exist.
- [ ] Stacked PR #3 and Never #0001 dependencies are reconciled.
- [ ] Bryan records approve, revise, reject, or supersede.

Until the checklist is complete: **keep the PR draft, manifests candidate, Vercel undeployed, and Cloudflare deferred.**
