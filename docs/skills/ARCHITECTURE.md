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

1. **Portable source package** — `SKILL.md`, package metadata, examples, and attributable eval references.
2. **Canonical admission record** — a separately accountable decision about one immutable digest.
3. **Runtime enforcement** — loader, grant validation, tool scoping, and receipts.
4. **Projection** — registries, dashboards, Airtable/Notion/Drive views, and analytics that can be rebuilt.

No layer inherits another layer’s authority. A projection cannot become Canon through recency or popularity. Runtime success cannot become admission. Source validation cannot become execution permission.

## Repository ownership

- `quirk-core`: admitted semantic definitions, invariants, and governance contracts.
- `quirk-skills`: portable Skill candidate source packages and their attributable package-local evaluation evidence. It is a candidate source repository and does not admit, activate, deploy, canonize, publish, or grant runtime authority.
- `quirk-os`: runtime loader, routing, enforcement, receipts, runtime-facing projections, and legacy/local Skill candidates that have not yet received an explicit migration disposition.
- future `quirk-evals`: reusable cross-repository conformance and adversarial suites only after duplication and independent consumers justify extraction.
- `quirk-generator`: scaffolds candidate packages; generated output defaults to candidate.
- `quirk-data`: rebuildable quality, usage, and evaluation projections only.
- `.github`: organization governance, portfolio truth, and reusable workflows after contracts are proven.

`quirk-skills` existing as a repository does not automatically move, admit, or reclassify the local packages under `quirk-os/skills/*`. Those packages remain where they are until a separate, explicit migration decision is bound to exact source and destination states.

Extraction remains a product decision, not an aesthetic preference for more repositories.

## Skill package contract

Every package defines identity, version, maturity, family, purpose, trigger boundaries, typed inputs and outputs, invariants, failure and stop conditions, method sequence, decisions, approvals, resources, tools, quality gates, learning rules, compatibility, provenance, and integrity.

Where a package uses `manifest.json`, `integrity.source_blob_sha` binds the manifest to the exact `SKILL.md` bytes using Git blob SHA-1 and `integrity.manifest_sha256` binds the canonical JSON form of the manifest while excluding only its self-digest field. Other candidate package formats must provide an equivalently explicit immutable source binding before evidence can be treated as version-specific.

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

A version must separately pass applicable Quirk Approval, Procedures, Processes, Profiling, Interoperability, Security, Statistical, Lexical, and Quirk Pedantry testing. Package-local evidence may support a bounded review disposition; human admission remains external by design.
