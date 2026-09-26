---
name: quirk-distilled-decision-brief-2d699dfa
description: Distilled decision brief replay of Quirk Distillation Synthesizer, auto-written from run receipt receipt.quirk-distillation-synthesizer.trial.0007 and unreviewed until a distill promotion receipt binds it.
version: 0.1.0
status: candidate
family: distill
authority_ceiling: infer
manifest: manifest.json
eval_suite: ../../evals/skills/distilled/quirk-distilled-decision-brief-2d699dfa.json
---

# Distilled decision brief replay of Quirk Distillation Synthesizer

## Quirk contract

- Version: `0.1.0`
- Status: `candidate` (auto-distilled, unreviewed)
- Authority ceiling: `infer` (never above the source skill)
- Tier: distilled candidate. Not in the manifested registry, not loadable into any run context, and not admissible until a distill promotion receipt binds this exact digest.
- Quality rule: a replay is only as good as the evidence each move produced in the source run.

## Distilled from

- Source skill: `quirk-distillation-synthesizer` version `0.2.0`
- Source manifest digest: `eb3b41048844dba81b0dbed6cd4647fd7bab64332ad8fce9274e475e49ffab48`
- Run receipt: `receipt.quirk-distillation-synthesizer.trial.0007` (status `completed`, grant `grant.quirk-distillation-synthesizer.trial.0007`)
- Run trace: `trace.quirk-distillation-synthesizer.trial.0007`
- Task class: `decision_brief`
- Observed ceiling: `infer`

## Moves that worked

1. `read_sources` with evidence `ledger.evidence.trial-0007.sources`. Fourteen sources fingerprinted; two duplicates collapsed with provenance kept.
2. `normalize_claims` with evidence `ledger.evidence.trial-0007.claims`. Thirty-one atomic claims, each bound to at least one source.
3. `map_contradictions` with evidence `ledger.evidence.trial-0007.contradictions`. Three live contradictions preserved in the matrix rather than averaged away.
4. `emit_synthesis_pack` with evidence `asset.synthesis-pack.roadmap-q4-adoption.0007`.

## Excluded from distillation

- `cache_sources`: not declared by the source skill; excluded, never distilled
- `emit_proposed_move`: outcome was skipped

## Routing signals observed

- claim extraction
- contradiction matrix
- decision brief

## Stop conditions

Stop before any move that is not listed above, before any write the source grant did not allow, and before treating this candidate as reviewed, admitted, active, or canonical.

## Governance

- Written by `agent.distill-loop` from an immutable run receipt. The trigger cannot approve its own output.
- Promotion requires a distill promotion receipt whose requester and approver are distinct actors and whose digests match this package byte for byte.
- Promotion moves this package to the reviewed-candidate tier only. Admission, activation, and Canon remain separate external decisions with their own receipts.
- The starter eval suite covers positive and authority cases. Adversarial and regression cases must be authored by a reviewer before promotion; the loop does not invent adversarial evidence.

## Machine binding

- Manifest: [`manifest.json`](manifest.json)
- Eval suite: [`../../evals/skills/distilled/quirk-distilled-decision-brief-2d699dfa.json`](../../evals/skills/distilled/quirk-distilled-decision-brief-2d699dfa.json)
- Mapping contract: [`../../mappings/skill-package.v1.yaml`](../../mappings/skill-package.v1.yaml)
- Ledger: [`../distill-ledger.json`](../distill-ledger.json)
- Runtime status: candidate source only; the runtime loader must reject this version until a separate admission record and scoped grant exist.

## Universal stop rule

Capability, credentials, connected tools, successful validation, model confidence, or repeated use never create authority. Stop before self-activation, self-escalation, Canon promotion, history mutation, or action beyond the external grant.
