# Measurement Plan: quirk-applause-gate

## At a Glance
- Recommended toolsets: token-usage-observer, task-outcome-scorecard, latency-efficiency
- Toolset count: 5
- Summary: Combine cost, outcome, and trust signals so you can tell whether the skill or plugin is genuinely helping instead of only looking well-structured on paper.

## Why It Matters
- Combine cost, outcome, and trust signals so you can tell whether the skill or plugin is genuinely helping instead of only looking well-structured on paper.
- Token Usage Observer: Measure how many tokens the skill or plugin actually burns in representative runs.
- Task Outcome Scorecard: Measure whether the skill helps users finish the intended job with fewer retries and less cleanup.
- Latency And Efficiency: Track whether the skill speeds users up enough to justify its cost.

## Fix First
- Token Usage Observer: Static estimates are useful guardrails, but observed usage is what tells you whether a real workflow is affordable and whether caching or reasoning changes the picture.
- Task Outcome Scorecard: A low-token skill is still a miss if it fails the task, and a verbose skill may be worth it if it consistently improves first-pass success.
- Latency And Efficiency: DX improvements usually win when they reduce waiting or rework, not only when they reduce absolute token counts.

## Recommended Next Step
- Start with Token Usage Observer
- Why: Measure how many tokens the skill or plugin actually burns in representative runs.
- Chat request: "What should I run next?"
- Local command: `plugin-eval start ~/work/quirk-os/quirk-os/skills/quirk-applause-gate --request 'What should I run next?' --format markdown`

## Details
<details>
<summary>Recommended toolsets</summary>

- token-usage-observer
- task-outcome-scorecard
- latency-efficiency
</details>
<details>
<summary>All toolsets</summary>

- Token Usage Observer [high] Measure how many tokens the skill or plugin actually burns in representative runs. Signals: observed_usage_sample_count, observed_input_tokens_avg, observed_total_tokens_avg, estimate_vs_observed_input_ratio. Evidence: Responses API usage logs, Codex-like session exports, JSONL traces captured from local benchmarking harnesses. Starter pack: token-usage-pack.
- Task Outcome Scorecard [high] Measure whether the skill helps users finish the intended job with fewer retries and less cleanup. Signals: task_success_rate, first_pass_success_rate, retry_rate, human_override_rate. Evidence: Task run logs, Structured user acceptance checklist, Before/after comparison runs on the same prompts. Starter pack: task-outcomes-pack.
- Tool Call Audit [medium] Check whether the agent uses the right tools, arguments, and sequencing when the skill is active. Signals: tool_call_success_rate, invalid_tool_argument_rate, recoverable_tool_failure_rate. Evidence: Tool invocation traces, Recorded sessions, Golden-path scenario replays. Starter pack: tool-audit-pack.
- Latency And Efficiency [high] Track whether the skill speeds users up enough to justify its cost. Signals: p50_time_to_first_acceptable_answer_seconds, p95_time_to_task_completion_seconds, tokens_per_successful_run. Evidence: Benchmark harness timings, Manual stopwatch runs on canonical tasks, Responses API timestamps combined with usage logs. Starter pack: latency-efficiency-pack.
- Human Rubric Review [medium] Capture clarity, trust, and usefulness signals that automated checks will miss. Signals: clarity_score_avg, confidence_score_avg, follow_up_question_rate. Evidence: Reviewer scorecards, Team rubric sheets, Annotated transcripts. Starter pack: human-rubric-pack.
</details>
<details>
<summary>Use From Codex Chat</summary>

Start with a natural chat request, then let plugin-eval show the exact local command sequence behind it.

Start with this chat request: "Measure the real token usage of this skill."
Why this path: Plugin Eval recommended Measure Real Token Usage from the current local state for this skill.
Quick local entrypoint: plugin-eval start ~/work/quirk-os/quirk-os/skills/quirk-applause-gate --request 'Measure the real token usage of this skill.' --format markdown
Plugin Eval will run first: plugin-eval init-benchmark ~/work/quirk-os/quirk-os/skills/quirk-applause-gate

Other chat requests you can use:
- Full Skill Analysis: say "Give me a full analysis of this skill, including benchmark setup." -> plugin-eval analyze ~/work/quirk-os/quirk-os/skills/quirk-applause-gate --format markdown
- Evaluate Skill: say "Evaluate this skill." -> plugin-eval analyze ~/work/quirk-os/quirk-os/skills/quirk-applause-gate --format markdown
- Explain Token Budget: say "Explain the token budget for this skill." -> plugin-eval explain-budget ~/work/quirk-os/quirk-os/skills/quirk-applause-gate --format markdown
- Measure Real Token Usage: say "Measure the real token usage of this skill." -> plugin-eval init-benchmark ~/work/quirk-os/quirk-os/skills/quirk-applause-gate
- Benchmark With Starter Scenarios: say "Help me benchmark this skill." -> plugin-eval init-benchmark ~/work/quirk-os/quirk-os/skills/quirk-applause-gate
- Start Here: say "What should I run next?" -> plugin-eval analyze ~/work/quirk-os/quirk-os/skills/quirk-applause-gate --format markdown
</details>
