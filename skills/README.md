# Quirk Systems Compounder Skills

Status: **candidate / non-operative**.

The manifest registry now contains 12 candidate Skill packages. Eleven retain the Skills v0.2 shared conformance suite; `quirk-applause-gate` joins through a bounded v0.3 registry extension with its own four-case shared conformance slice. Every package remains evidence-only until separately admitted.

Each manifested package contains:

- `SKILL.md` — human/agent procedure;
- `manifest.json` — strict machine contract, source blob SHA, and canonical manifest digest;
- positive, adversarial, regression, and authority evaluation coverage;
- explicit trigger, tool, resource, authority, learning, compatibility, and stop contracts.

The central `registry.json` is a rebuildable candidate inventory. It is not Canon and cannot activate anything.

| Skill | Family | Ceiling | Primary output |
| --- | --- | --- | --- |
| `quirk-applause-gate` | challenge | infer | bounded applause review |
| `quirk-source-authority-resolver` | research | infer | authority census |
| `quirk-object-contract-engineer` | structure | propose | contract pack |
| `quirk-data-refinery` | structure | propose | refinery plan |
| `quirk-semantic-label-foundry` | perceive | propose | label review pack |
| `quirk-research-cartographer` | research | infer | research map |
| `quirk-distillation-synthesizer` | distill | infer | synthesis pack |
| `quirk-evidence-instrumenter` | preserve | propose | evidence contract |
| `quirk-control-loop-designer` | evolve | propose | control policy |
| `quirk-probabilistic-forecaster` | decide | infer | forecast pack |
| `quirk-roadmap-board-orchestrator` | connect | propose | roadmap projection |
| `quirk-value-foundry` | productize | propose | reusable value candidate |
| `quirk-deck-compiler` | structure | propose | purpose-filtered Deck, proposed Hand, and invariant proof |

`quirk-deck-compiler` remains a separate draft candidate under the Deck Grammar pack and is not part of the manifested registry.

## Applause Gate compatibility boundary

Applause Gate's package family is `challenge`, because that is the repository's existing schema vocabulary for evidence-challenging procedures. Its four shared cases live in `evals/skills/applause-gate-conformance.json`; the immutable 44-case v0.2 core suite remains unchanged. The conformance adapter under `scripts/applause_gate/skill_conformance.py` is evaluation-only and is intentionally not added to `scripts/sync_control_plane/skill_evaluator.py`.

## Distilled candidates

The post-run distill loop (`scripts/distill_loop/`, [`docs/distill-loop/README.md`](../docs/distill-loop/README.md)) may write packages into this directory under the `quirk-distilled-*` namespace. They are a tier below the manifested candidates above: auto-written from an immutable run receipt, recorded in the append-only [`distill-ledger.json`](distill-ledger.json), never part of `registry.json`, and never visible to a later run until a distill promotion receipt with distinct requester and approver binds their exact digest. Promotion moves them to reviewed candidate only; admission stays a separate external decision. `scripts/validate_skills.py` excludes the namespace from the twelve-skill drift gate and fails if a distilled id ever appears in the registry.

## Runtime rule

The runtime loader rejects candidate or unadmitted versions, over-ceiling grants, self-approved grants, expired grants, undeclared actions, manifest tampering, and source tampering. Passing evals remain evidence—not admission.

No Skill may self-activate, increase its own authority, promote Canon, rewrite history, persist an inferred preference or Hand, misrepresent access as ownership, or perform an irreversible write merely because capability, evidence, or credentials exist.
