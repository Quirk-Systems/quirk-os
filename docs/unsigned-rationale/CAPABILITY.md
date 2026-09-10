# Capability candidate: unsigned rationale custody

`capability.unsigned-rationale-custody` · version `0.1.0` · status `CANDIDATE` · proposed owning repository: `Quirk-Systems/quirk-os`.

**Outcome:** a caller can preserve a comparison and reopen its exact saved rationale while distinguishing damaged transport from changed or unchecked sources. The user finish condition remains a real decision that Bryan can understand and resume.

This implements two reusable capabilities under one versioned protocol: deterministic export/reopen and source freshness reconciliation. Keeping them together avoids two competing packet identities. They can serve Studio, a skill, or a workflow through a bounded consumer adapter; no installed skill or admitted runtime capability is created by these files.

## Mission and boundaries

| Concern | Contract |
|---|---|
| Authorized actor | Agent authoring the local candidate under Bryan's instruction to continue coding/documenting; later callers need their own workspace authorization |
| Inputs | One validated two-source rationale packet; optional caller-supplied source observations; explicitly selected local file for fingerprinting |
| Outputs | Deterministic unsigned bundle; structured validity/freshness result; local source metadata with exact byte digest |
| Local effects | Create a new export directory and protocol files; read explicitly selected files/bundle |
| Downstream effects | `effects_allowed:false`, `training_allowed:false`, `preference_graph_apply_allowed:false`; no promotion or external action |
| Scope limits | Fixed format version, fixed bundle file names, exact allowed fields, two sources, bounded strings/claim arrays |
| Recovery | Preserve input and failed partial directory; retry export to a fresh destination; re-inspect stale source into a new revision |
| Migration | No database, no database migration, no existing data rewrite; incompatible protocol versions require an explicit new parser/migration and replay fixtures |
| Deployment | Python standard-library local tool; no service provisioning, telemetry upload, provider call, or application route |
| Stop condition | Candidate code and documentation reproduced with bounded positive/adversarial proofs; runtime admission and human benefit remain open |

The permission flags constrain use of the exported comparison. They do not mean the filesystem operation produced no effect. The intended local write, measured exported bytes, and eventual human usefulness remain distinct.

## Sources and meaning

| Source | Classification | Use and limitation |
|---|---|---|
| Prior `Quirk-Studio` build pack, `Build-Playbook.md` export specification | Candidate source | Defines intended packet shape and deterministic serialization; does not prove an existing application implementation |
| Existing Quirk OS repository instructions | Inspected source; admission status belongs to repository governance | Ownership, candidate branch/review, release and no-database requirements; repository source does not confer live authority |
| [Protocol schema](../../schemas/unsigned-rationale.schema.json) and [implementation](../../scripts/unsigned_rationale.py) | New candidate definitions | Shape plus explicit semantic enforcement; compatibility with real OS/Preference consumers remains unproved |
| [Synthetic example](../../examples/unsigned-rationale/example.json) and its two local source files | Synthetic fixture | Reproducible byte and rationale preservation; no user preference or actual screen observation |
| Source observations supplied at reopen | Caller assertions | Used for reconciliation only; this module does not authenticate the observation producer |

Prior playbook SHA-256: `413d9fb053efd33f6a28de09e57262c7fe27daa642ea810d68d862ee6e351fea`. Inspected Quirk OS main revision: `499f94b8d12e29dd7804cc9b537fd70f6a8048d8`. These record design/source lineage; no remote fetch is required to run this slice. The candidate implementation revision and executed results belong in the PR evidence receipt.

The module preserves the existing flat `quirk.unsigned-rationale` record. The generic Compound Quirk Systems envelope is an integration mapping concern; adding it here would create a second, incompatible wire format. Future adapters must map the rationale ID/revision, fixed candidate restrictions, source references, and packet digest explicitly, retaining unresolved questions and provenance. Unknown extension fields are rejected in this strict version and require a defined compatibility change.

## Composition contract

| Producer → consumer | Shared object and permitted behavior | Evidence required before use |
|---|---|---|
| Source capture → rationale builder | Source ID, permitted locator, capture time, revision/digest or explicit reasons | Exact byte digest; correct unknown-state representation |
| Rationale builder → exporter | Schema-shaped packet preserving source/interpretation labels and user's text | Validation plus duplicate ID/reference and authority-boundary checks |
| Bundle → inspector adapter | Verified saved packet and separate source freshness | Consumer reads real return shape, handles failed reopen, and displays saved status |
| Authorized source resolver → freshness reconciliation | Current observation by source ID, outside the saved packet | Resolver authorization and identity mapping; changed/missing/unchecked fixtures |
| Inspector → human judgment | Exact saved rationale plus visible uncertainty | Bryan's completion, comprehension, cleanup, assistance, and helpfulness observations |

No integration is established merely by matching schema fields. Source resolution, UI rendering, object authorization, Preference adaptation, and runtime enforcement need consumer-specific evidence.

## Proof obligations

Positive examples must preserve Unicode/string contents, array order, source identity, restrictions, and the outcome across export/reopen. Determinism must refer to exact final bytes. Freshness checks must preserve saved rationale while reporting the caller's available identity evidence.

| Adversarial pressure | Required rejection or preservation |
|---|---|
| Set a permission flag true or change candidate status | Reject the packet |
| Duplicate a JSON key or attach an unknown field | Reject instead of silently selecting a meaning |
| Fabricate a claim reference to a missing source | Reject the broken cross-reference |
| Omit unknown-digest/revision explanation | Reject fabricated completeness |
| Alter packet or sidecar; omit commit marker | Refuse successful reopen |
| Export twice to one destination | Refuse overwrite and retain original bundle |
| Report matching revision with changed digest | Preserve saved record; expose stale source evidence |
| Supply instructions inside source/rationale text | Preserve as data; no execution path |
| Present successful export as proof of user benefit | Keep the helpfulness decision unobserved until a user actually supplies it |

The last row attacks the appealing false success case: an immaculate receipt that helped nobody finish anything. Report only the specific tests executed in the evidence receipt; this table is an obligation list, not a pass claim. Structural schema documentation does not establish full JSON Schema standards validation.

## System dividend and next earned move

**Implemented:** reusable deterministic artifact transport, explicit unknown source identity, a stable failure surface, and freshness reconciliation isolated from source fetching. This reduces repeated serialization and recovery design work for future consumers; no measured time savings are claimed.

**Proposed:** a thin Quirk Now adapter reusing this protocol and its failure states. It must preserve the existing application/Preference result shapes, data custody, and grants. Add no provider until a demonstrated consumer requirement earns it.

**Open:** actual UI journey and iPhone recovery, trusted source-resolution adapter, runtime admission, independent human review where required, and Bryan's real-use benefit. The keep/mutate/drop decision requires an observed task and his judgment. Technical proof alone does not close those obligations.
