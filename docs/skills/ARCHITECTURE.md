# Quirk Skills Architecture v0.2

Status: **candidate / non-operative**. This architecture does not admit a skill, grant runtime authority, or promote Canon.

## Grammar

- **Capability:** what a system can do.
- **Skill:** how Quirk reliably performs a recognizable kind of work.
- **Move:** atomic action.
- **Way:** larger operating pattern.
- **Agent:** assembler/executor of externally granted skills.
- **Eval:** attributable evidence that a version meets a bounded contract.
- **Grant:** scoped, expiring permission to execute an admitted version.
- **Receipt:** immutable evidence of what actually ran.

## Four products, kept separate

1. **Portable source package** — `SKILL.md`, `manifest.json`, examples, and eval references.
2. **Canonical admission record** — a separately accountable decision about one immutable digest.
3. **Runtime enforcement** — loader, grant validation, tool scoping, and receipts.
4. **Projection** — registries, dashboards, Airtable/Notion/Drive views, and analytics that can be rebuilt.

No layer inherits another layer’s authority. A projection cannot become Canon through recency or popularity. Runtime success cannot become admission. Source validation cannot become execution permission.

## Repository ownership

- `quirk-core`: admitted semantic definitions, invariants, and governance contracts.
- `quirk-os`: runtime loader, routing, enforcement, receipts, and private projections.
- future `quirk-skills`: portable skill packages after three independent consumers justify extraction.
- future `quirk-evals`: reusable cross-repository conformance and adversarial suites after duplication exists.
- `quirk-generator`: scaffolds candidate packages; generated output defaults to candidate.
- `quirk-data`: rebuildable quality, usage, and evaluation projections only.
- `.github`: reusable organization workflows after the contract is proven here.

Extraction is a product decision, not an aesthetic preference for more repositories.

## Skill package contract

Every package defines identity, version, maturity, family, purpose, trigger boundaries, typed inputs and outputs, invariants, failure and stop conditions, method sequence, decisions, approvals, resources, tools, quality gates, learning rules, compatibility, provenance, and integrity.

`integrity.source_blob_sha` binds the manifest to the exact `SKILL.md` bytes using Git blob SHA-1. `integrity.manifest_sha256` binds the canonical JSON form of the manifest while excluding only its self-digest field.

## Runtime admission sequence

`candidate source → eval evidence → external admission decision → admitted immutable digest → scoped runtime grant → loader verification → bounded execution → immutable receipt`

The loader fails closed when:

- the package is not admitted;
- admission requester and approver are the same;
- source or manifest integrity fails;
- the grant targets another ID, version, or digest;
- the grant exceeds the package authority ceiling;
- the grant includes undeclared actions;
- issuance/expiry is invalid;
- the grant is not yet valid or has expired.

## Learning sequence

`observe → attempt → evaluate → feedback → mutation candidate → validate → external admission → successor version`

A running skill never rewrites itself. Historical versions remain addressable. Feedback produces a Proposed Move and receipt, not an invisible behavioral mutation.

## Admission

A version must separately pass applicable Quirk Approval, Procedures, Processes, Profiling, Interoperability, Security, Statistical, Lexical, and Quirk Pedantry testing. This PR supplies machine-verifiable package, integrity, runtime-boundary, and eval evidence. Human admission remains external by design.
