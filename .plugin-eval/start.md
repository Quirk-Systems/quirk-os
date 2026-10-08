# Plugin Eval Start Here: quirk-applause-gate

## At a Glance
- Recommended path: Measure Real Token Usage
- Benchmark config present: no
- Usage log present: no
- Quick local entrypoint: `plugin-eval start ~/work/quirk-os/quirk-os/skills/quirk-applause-gate --request 'Evaluate this local candidate Skill, benchmark realistic premature-certainty scenarios, and measure actual token usage without changing the Skill or any admission or runtime state.' --format markdown`
- First local command: `plugin-eval init-benchmark ~/work/quirk-os/quirk-os/skills/quirk-applause-gate`

## Why It Matters
- Start with a natural chat request, then let plugin-eval show the exact local command sequence behind it.
- Plugin Eval routed "Evaluate this local candidate Skill, benchmark realistic premature-certainty scenarios, and measure actual token usage without changing the Skill or any admission or runtime state." to Measure Real Token Usage because it asks for measured or observed token usage.

## Fix First
- Start with the recommended path before branching into secondary workflows.

## Recommended Next Step
- Measure Real Token Usage
- Why: Plugin Eval routed "Evaluate this local candidate Skill, benchmark realistic premature-certainty scenarios, and measure actual token usage without changing the Skill or any admission or runtime state." to Measure Real Token Usage because it asks for measured or observed token usage.
- Chat request: "Evaluate this local candidate Skill, benchmark realistic premature-certainty scenarios, and measure actual token usage without changing the Skill or any admission or runtime state."
- Local command: `plugin-eval init-benchmark ~/work/quirk-os/quirk-os/skills/quirk-applause-gate`

## Details
<details>
<summary>Full local sequence</summary>

- plugin-eval init-benchmark ~/work/quirk-os/quirk-os/skills/quirk-applause-gate
- plugin-eval benchmark ~/work/quirk-os/quirk-os/skills/quirk-applause-gate --config ~/work/quirk-os/quirk-os/skills/quirk-applause-gate/.plugin-eval/benchmark.json
- plugin-eval analyze ~/work/quirk-os/quirk-os/skills/quirk-applause-gate --observed-usage ~/work/quirk-os/quirk-os/skills/quirk-applause-gate/.plugin-eval/benchmark-usage.jsonl --format markdown
</details>
<details>
<summary>Other chat requests</summary>

- Full Skill Analysis: "Give me a full analysis of this skill, including benchmark setup." -> plugin-eval analyze ~/work/quirk-os/quirk-os/skills/quirk-applause-gate --format markdown
- Evaluate Skill: "Evaluate this skill." -> plugin-eval analyze ~/work/quirk-os/quirk-os/skills/quirk-applause-gate --format markdown
- Explain Token Budget: "Explain the token budget for this skill." -> plugin-eval explain-budget ~/work/quirk-os/quirk-os/skills/quirk-applause-gate --format markdown
- Measure Real Token Usage: "Measure the real token usage of this skill." -> plugin-eval init-benchmark ~/work/quirk-os/quirk-os/skills/quirk-applause-gate
- Benchmark With Starter Scenarios: "Help me benchmark this skill." -> plugin-eval init-benchmark ~/work/quirk-os/quirk-os/skills/quirk-applause-gate
- Start Here: "What should I run next?" -> plugin-eval analyze ~/work/quirk-os/quirk-os/skills/quirk-applause-gate --format markdown
</details>
