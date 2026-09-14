# Architecture

## 1. Boundary first

`quirk.products.beauty` is a domain pack, not an autonomous authority domain and not a standalone platform by default.

The domain owns beauty meaning. Quirk core owns power.

| Concern | Quirk Beauty owns | Delegated owner |
|---|---|---|
| Beauty vocabulary and attributes | Yes | — |
| Beauty comparison context | Yes | — |
| Choice and outcome experience | Yes | — |
| Candidate evidence derivation | Yes | — |
| Candidate recommendation ranking | Yes | — |
| Identity and tenancy | No | Quirk core |
| Grants, expiry, revocation, Human Gate | No | Quirk core governance |
| Preference Graph canonical service | No | Preference Graph / Quirk core |
| Immutable effect receipts | No | Quirk core evidence |
| Product/catalog truth | No | Quirk Commerce / catalog authority |
| Publishing, messaging, purchasing | No | Action Router and effect owners |
| Model secrets and execution | No | Model gateway |
| Canon admission | No | Human-controlled semantic registry |

## 2. Canonical, runtime, projection

### Canonical

`docs/canon/QUIRK-BEAUTY-DOMAIN-BOUNDARY.yaml` and its bound payload contain the only admitted semantics in this pack. It defines purpose, ownership, delegation, exclusions, invariants, and proof requirements.

### Runtime

The candidate kernel in `src/` computes evidence, ranks recommendations, records explicit outcomes, proposes graph changes, and enforces a local reference gate. It is replaceable and cannot define canon.

### Projection

The candidate Supabase migration stores scoped runtime events. It is a reconstructable projection. It cannot redefine the canonical boundary or become the authoritative Preference Graph.

## 3. Vertical slice

```text
explicit choice
      │
      ▼
candidate preference evidence
      │
      ▼
deterministic recommendation ── optional explanation renderer
      │
      ▼
real-world human test
      │
      ▼
explicit outcome observation
      │
      ▼
graph-update proposal (autoApply=false)
      │
      ▼
Human Gate: approve / revise / reject
      │
      ▼
Quirk core Preference Graph mutation
      │
      ▼
immutable effect receipt
```

No stage may skip lineage. No stage inherits authority from the previous stage.

## 4. Model boundary

The v0.1 ranking kernel is deterministic and model-independent.

A model may later:

- translate cited factors into clearer language;
- classify user-provided notes into candidate attributes;
- suggest questions when evidence is insufficient.

A model may not:

- invent evidence;
- alter the deterministic rank without a visible candidate override;
- infer satisfaction;
- decide the graph mutation;
- convert a recommendation into a purchase or publication;
- promote the domain pack or its objects into canon.

## 5. Data boundaries

Every event carries:

- actor;
- purpose partition;
- context;
- source type;
- timestamp;
- lineage identifiers;
- candidate or decision status.

No query should merge purpose partitions by default. No public or aggregate view belongs in v0.1.

## 6. Event contracts

| Event | Source | Effect class | Mutable? |
|---|---|---:|---:|
| `beauty.choice.recorded` | explicit human action | A3 internal event | append-only |
| `beauty.evidence.derived` | deterministic kernel | A1 candidate | append-only |
| `beauty.recommendation.proposed` | deterministic kernel | A2 proposal | expires |
| `beauty.outcome.recorded` | explicit human report | A3 internal event | append-only |
| `beauty.graph_update.proposed` | domain adapter | A2 proposal | expires |
| `core.graph_update.decided` | human gate | bounded authority | append-only |
| `core.preference_graph.updated` | core effect broker | A3 mutation | versioned |
| `core.effect.receipted` | core evidence writer | evidence | append-only |

## 7. Deployment boundary

The pack must remain non-deployed until:

1. target Quirk core interfaces are bound;
2. real RLS tests pass against the intended Supabase project;
3. authoritative receipt signing replaces the candidate local digest helper;
4. the real-world proof passes;
5. Bryan admits the runtime separately.
