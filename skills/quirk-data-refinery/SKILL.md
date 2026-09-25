---
name: quirk-data-refinery
description: Plan and execute bounded, idempotent cleaning of structured and unstructured Quirk data while preserving raw sources, provenance, exceptions, rollback, and human review.
version: 0.2.0
status: candidate
family: structure
authority_ceiling: propose
manifest: manifest.json
eval_suite: ../../evals/skills/conformance.json
---

# Quirk Data Refinery

## Quirk contract

- Version: `0.2.0`
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

## Machine binding

- Manifest: [`manifest.json`](manifest.json)
- Eval suite: [`../../evals/skills/conformance.json`](../../evals/skills/conformance.json)
- Mapping contract: [`../../mappings/skill-package.v1.yaml`](../../mappings/skill-package.v1.yaml)
- Runtime status: candidate source only; the runtime loader must reject this version until a separate admission record and scoped grant exist.

## Invocation contract

Use this skill only when its trigger contract matches, required sources and authority are available, and no trigger collision remains unresolved. The caller owns purpose and authority. The skill owns procedure and evidence. A successful run may emit `refinery_plan` and Proposed Moves; it may not convert either into Canon, active runtime state, or an irreversible write.

## Evaluation and learning

Positive, adversarial, regression, and authority cases are mandatory. Feedback appends evidence and may produce a mutation candidate. It never rewrites this running version. Any successor must receive a new version, digest, evaluation record, and external admission decision.

## Universal stop rule

Capability, credentials, connected tools, successful validation, model confidence, or repeated use never create authority. Stop before self-activation, self-escalation, Canon promotion, history mutation, or action beyond the external grant.
