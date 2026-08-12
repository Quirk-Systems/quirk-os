# Quirk Core Golden Project Pack

**Status:** PROPOSED  
**Owner:** Quirk Core  
**Canonical surface:** Git  
**Collaborative surface:** Google Drive  
**Runtime authority:** Quirk Governance + Quirk Runtime  
**Inspection:** Quirk Control  
**Evidence:** Quirk Evaluation & Evidence  
**Protocol family:** `golden-pack.v1`

> Every consequential mutation owes a receipt.  
> History is not authority.  
> Storage is not consent.  
> Comments are not commands.  
> No Zombie Truth.  
> Every decision eventually owes an outcome.

## 1. Outcome

Build Quirk Core as an independently reusable operating foundation for a stateful human–agent ecosystem without turning the repo into a mythology dump or a framework-shaped mood board.

A Golden Project Pack is complete only when it is:

1. **Strange intact** — Quirk-specific value survives normalization.
2. **Materially useful** — contracts, schemas, examples, tests, and procedures can be used.
3. **Reusable without Bryan** — a competent contributor can reconstruct intent, authority, evidence, and next actions from the repository.
4. **Inspectably governed** — consequential changes move through proposals, evidence, authority, gates, receipts, and outcomes.
5. **Reversible where possible** — irreversible changes are explicit, exceptional, and proportionately authorized.

## 2. System placement

Quirk Ledger is not a new primary Quirk system. It is the accountable state-transition and provenance protocol inside Quirk Core.

```text
CANONICAL PLANE
Git-backed definitions, schemas, policies, prompts, evals, ADRs
        ↓
RUNTIME PLANE
Authority resolution, policy checks, mutation execution, receipts
        ↓
PROJECTION PLANE
Postgres/search/vector/control views, dashboards, indexes
        ↕
WORK PLANE
Drive drafts, research packets, comments, media production, review
```

The planes may synchronize. They may not silently substitute for one another.

## 3. Machinery map

| Object | Job | Must not become |
|---|---|---|
| **Ledger** | Accountable history of consequential state transitions | Generic telemetry or a dumping ground |
| **Log** | Time-ordered operational or diagnostic record | Canonical truth merely because it exists |
| **Eval** | Measures behavior, quality, integrity, or outcomes | A vibes score with no test object |
| **Gate** | Enforces a release or authority threshold | A checklist nobody can fail |
| **Capability** | Versioned promise that Quirk can produce an outcome | A loose feature label |
| **Agent Skill** | Executable procedure implementing or supporting a capability | A giant prompt blob |
| **Proposed Move** | Bounded, reviewable candidate change | A comment that mutates state |
| **Receipt** | Portable proof of an authorized, verified transition | A claim that a write probably happened |
| **Outcome Record** | Evidence of what a decision caused after release | A victory lap |
| **Poison Marker** | Negative institutional knowledge preventing recurrence | Silent deletion of an error |

## 4. Canonical mutation path

```text
intent
→ classify L0–L5
→ proposal
→ provenance
→ evidence
→ authority
→ pre-eval
→ approval
→ domain mutation
→ verification
→ ledger commit
→ receipt
→ projection
→ communication
→ outcome eval
→ keep / revise / reverse / poison / promote
```

### Mutation classes

- **L0 Ephemeral:** no ledger.
- **L1 Operational:** telemetry/log only.
- **L2 Consequential:** ledger + receipt.
- **L3 Canonical:** ledger + authority + evidence + eval.
- **L4 Rights-sensitive:** explicit human authority + purpose/retention/forgetting rules.
- **L5 Irreversible or high impact:** human approval + mitigation/rollback or explicit irreversibility acceptance.

## 5. Google Drive operating contract

Drive is the multiplayer workbench, not the canonical source of truth.

Drive owns:

- research packets and source collections;
- editorial drafts and comments;
- product-design explorations;
- multimedia source assets and production files;
- review packets and handoffs;
- release receipts and human-readable summaries.

Git owns:

- canonical definitions and laws;
- typed schemas and contracts;
- versioned prompts and skills;
- eval fixtures and CI gates;
- ADRs, migrations, changelogs, and release manifests.

### Drive-to-Git promotion

```text
Drive draft
→ review comments
→ Proposed Move
→ evidence + affected objects
→ Git branch / PR
→ evals and gates
→ approval
→ merge
→ canonical receipt
→ Drive projection marked superseded or canonicalized
```

A Drive comment may create a Proposed Move. It can never directly change canon.

## 6. Current Research

Current Research is a governed evidence pipeline, not a bookmarks folder.

Every adopted external idea produces:

- a source record;
- one or more bounded claim records;
- date published and date accessed;
- source authority and conflict disclosures;
- contradictions and uncertainty;
- an adoption decision: **adopt / adapt / reject / monitor**;
- affected Quirk objects;
- freshness review date;
- a provenance receipt.

No time-sensitive claim is presented without an `as_of` date.

## 7. Top Minds

Top Minds is a contestable registry of thinkers and primary works whose ideas materially improve Quirk.

Fame grants no authority. Each Mind Card must include:

- the strongest contribution;
- primary artifacts;
- what Quirk adopts;
- what Quirk refuses or modifies;
- disagreements and falsifiers;
- applicability by Quirk object;
- freshness and source quality;
- conflict-of-interest or vendor context.

## 8. Multimedia Multipliziert

**Technical ID:** `quirk.media_multiplication`

> Every derivative owes a source receipt and a medium-native reason to exist.

Multimedia Multipliziert turns one canonical object into multiple useful forms without copy-paste content confetti. Each derivative must add a medium-specific affordance: interaction, demonstration, spatial explanation, performance, accessibility, compression, searchability, or participation.

Required controls:

- canonical object and version;
- transformation type;
- audience and job;
- added affordance;
- claim fidelity;
- rights and licensing;
- accessibility package;
- provenance manifest;
- medium-native evals;
- release receipt;
- supersession/sunset behavior.

Use C2PA Content Credentials where supported for public media; use Quirk receipts for every derivative regardless of format.

## 9. Golden Gates

A release fails when any required gate fails.

1. **Canon Gate** — definitions, boundaries, IDs, and versions are coherent.
2. **Schema Gate** — machine-readable artifacts validate.
3. **Authority Gate** — required approvals and purpose scopes exist.
4. **Evidence Gate** — consequential claims are supported and contradictions surfaced.
5. **Integrity Gate** — no silent mutation, zombie truth, receipt fiction, or projection drift.
6. **Security + Privacy Gate** — least privilege, secret exclusion, rights-sensitive handling, forgetting behavior.
7. **Interop Gate** — receipts/events preserve semantics across supported boundaries.
8. **Eval Gate** — balanced, calibrated, adversarial, and regression suites pass.
9. **Documentation Gate** — architecture, examples, runbooks, migrations, and decisions resolve.
10. **Strange Intact Gate** — normalization did not erase the useful Quirk.
11. **Ship It Without Bryan Gate** — an independent evaluator can use, explain, test, and extend the pack.

## 10. Pack contents

- `ARCHITECTURE.md` — planes, object grammar, queues, procedures, and boundaries.
- `CURRENT-RESEARCH.md` — standards census and research operating model.
- `TOP-MINDS.md` — initial council and Mind Card contract.
- `MULTIMEDIA-MULTIPLIZIERT.md` — cross-media object model and production gates.
- `prompts/QUIRK-GOLDEN-PROMPTS.md` — eleven reusable prompts with iterative critique.
- `schemas/*.schema.json` — executable object contracts.
- `.github/workflows/golden-gates.yml` — initial repository gate.
- `scripts/validate_golden_pack.py` — fail-closed structural validation.

## 11. Release evidence

A Golden release must include:

```yaml
release:
  version: 0.1.0
  canonical_commit: "<sha>"
  authority_receipt: "<receipt-ref>"
  eval_report: "<eval-ref>"
  migration: "<migration-ref-or-none>"
  rollback: "<rollback-ref-or-explicitly-irreversible>"
  unresolved_consequential_moves: 0
  silent_mutations: 0
  zombie_truths: 0
  poisoned_dependencies: 0
  ship_without_bryan: passed
```

## 12. Definition of done

The pack is not Golden because the documents sound finished. It is Golden when:

- schemas parse and examples execute;
- all consequential object types have lifecycle and failure states;
- proposed changes cannot self-promote;
- outcome evaluation closes the decision record;
- research claims are currentized and source-backed;
- media derivatives retain provenance and add real affordance;
- CI can reject known classes of fuckery;
- a contributor can ship a safe extension without oral tradition.
