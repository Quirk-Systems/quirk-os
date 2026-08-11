# Quirk Sync Control Plane

**Status:** Candidate  
**Authority ceiling:** Observe, normalize, validate, persist runtime state, project, and propose.  
**Prohibited:** Canon promotion, authority expansion, irreversible mutation, history deletion, and production deployment without explicit admission.

This package bootstraps governed synchronization across GitHub, Supabase, Google Drive, Airtable, Notion, and Vercel. It stacks on the four-plane Ledger architecture in PR #3 and must satisfy Never #0001 from PR #4: capability never implies authority.

## Purpose

Quirk needs one interoperable identity and receipt model so agents, skills, data, orchestration runs, and human-facing views can move across platforms without creating six competing sources of truth.

The control plane provides:

- stable Quirk object keys independent of vendor IDs;
- explicit source bindings for every platform projection;
- versioned agent, skill, capability, and orchestrator manifests;
- idempotent sync receipts and replay-safe cursors;
- drift detection without automatic canon repair;
- projection outbox records for bounded downstream writes;
- human admission points for consequential or irreversible changes.

## Plane and platform authority

| Platform | Plane | Authoritative for | Never authoritative for |
| --- | --- | --- | --- |
| GitHub | Canonical | Schemas, policies, manifests, migrations, evals, executable specs | Live run state or human work-in-progress |
| Supabase | Runtime | Object bindings, cursors, receipts, run state, outbox, measured outcomes | Canon, permission expansion, or silent policy changes |
| Google Drive | Work | Source intake, review packs, authored working documents, archival context | Machine-executable canon |
| Airtable | Projection | Operational portfolio, work queue, decisions, agent/skill inspection | Canon or runtime truth |
| Notion | Projection | Human-readable wiki, orientation, interpretation, onboarding | Canon or runtime truth |
| Vercel | Projection | Approved application deployment and interface delivery | Canon, database authority, or orchestration policy |

## Canonical flow

```text
GitHub candidate or admitted canon
  → validated manifest and migration
  → Supabase runtime registry
  → receipt-backed projection outbox
  → Airtable / Notion / Drive / Vercel projections
  → observed drift or human feedback
  → Proposed Move
  → GitHub candidate change
```

No downstream projection writes directly back into Canon. A proposed reverse sync produces evidence and a Proposed Move.

## Identity model

Every cross-platform object has:

1. `object_key` — stable Quirk identity.
2. `kind` — data asset, agent, skill, capability, orchestrator, project, decision, document, deployment, or other admitted kind.
3. `canonical_uri` — Git-backed or explicitly approved canonical reference.
4. `source_bindings[]` — platform and vendor identifiers.
5. `content_hash` — normalized payload fingerprint.
6. `authority_class` — canonical, runtime, projection, or work.
7. `sync_direction` — pull, push, bidirectional-proposal, projection-only, or none.
8. `state` — discovered, candidate, active, drifted, paused, error, retired.
9. `run_receipts[]` — immutable evidence of attempted and completed work.

## Runtime tables

The candidate migration creates a non-exposed `quirk_sync` schema:

- `object_registry`
- `source_bindings`
- `manifest_registry`
- `sync_cursors`
- `run_receipts`
- `projection_outbox`

The schema is denied to `public`, `anon`, and `authenticated`. It is intended for trusted server-side orchestration only. No public policies, client mutation path, or self-promotion function is introduced.

## Agent and skill rules

An agent or skill manifest may describe tools and supported actions, but its `authority_ceiling` is independent of capability.

Every invocation must resolve:

```text
actor + purpose + authority grant + manifest version + tool scope + object scope
```

before execution.

A successful run may:

- update runtime state;
- emit evidence;
- enqueue a bounded projection;
- propose a manifest, schema, controller, or roadmap change.

A successful run may not activate its own new version or increase its own authority.

## Sync policies

### Pull

Fetch remote state, fingerprint it, preserve provenance, classify drift, and store the observation. Pull does not overwrite Canon.

### Push

Allowed only from an admitted source toward a declared projection. The outbox item must name the destination, payload hash, idempotency key, and authority grant.

### Bidirectional proposal

Changes on either side are observed. Conflicts produce a Proposed Move; they are not auto-merged.

### Projection only

The destination can be rebuilt from authoritative state and must not be treated as a source.

## Initial adapter responsibilities

### GitHub adapter

- discover repositories, branches, manifests, schemas, PRs, and release evidence;
- emit stable repository and file bindings;
- read admitted refs and candidate refs separately;
- never merge or promote without human authority.

### Supabase adapter

- persist runtime bindings, cursors, receipts, outbox, and observed outcomes;
- use migrations for DDL;
- remain private by default;
- expose no service credentials to a browser.

### Google Drive adapter

- inventory Docs, Sheets, Slides, files, folders, and revisions;
- preserve duplicate candidates and provenance;
- route unresolved changes to review;
- treat authored Docs and Sheets as work-plane records.

### Airtable adapter

- project projects, tools, work, decisions, sync bindings, agents, and skills;
- retain canonical URLs and object keys;
- never become source of truth because a record is easier to edit.

### Notion adapter

- publish a readable operating map, glossary, decisions, and status;
- show projection warnings and canonical references;
- collect human interpretation as proposed feedback.

### Vercel adapter

- deploy only approved interface builds;
- bind deployments to repository commit and manifest version;
- never infer approval from successful build capability.

## Drift response

| Drift class | Default response |
| --- | --- |
| Metadata-only | Refresh projection with receipt |
| Content mismatch | Mark drifted; enqueue review |
| Canon conflict | Block push; create Proposed Move |
| Missing remote object | Pause binding; preserve history |
| Permission mismatch | Stop; escalate |
| Unknown vendor state | Quarantine observation |
| Manifest version mismatch | Refuse invocation until reconciled |

## Acceptance gates

The package remains Candidate until all are demonstrated:

1. Schema validation succeeds.
2. Migration applies in isolation and rolls back or compensates cleanly.
3. Runtime schema is inaccessible to browser roles.
4. Replaying a run with the same idempotency key creates no duplicate mutation.
5. One object can bind to all six platforms without identity collision.
6. Drift creates evidence and a Proposed Move rather than silent repair.
7. Agent and skill authority ceilings are enforced independently of tools.
8. Projection outbox retries are bounded and inspectable.
9. A projection can be rebuilt from runtime and Canon.
10. Historical bindings and receipts survive retirement.
11. A capability cannot activate or promote itself.

## Bootstrap scope

This candidate intentionally does not:

- deploy a new Vercel project;
- merge PR #3 or PR #4;
- expose a public Supabase API;
- turn Airtable, Notion, or Drive into canonical stores;
- run full bulk synchronization across every existing object;
- resolve duplicate Drive or Notion identities without review.

It establishes the spine required to perform those actions safely.
