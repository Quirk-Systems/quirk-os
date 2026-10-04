# Operator Contract Extraction Adversarial Fixtures v0.1

**Status:** Candidate design fixtures; not implemented  
**Authority ceiling:** `propose`  
**Executable tests:** none  
**Runtime effect:** none  
**Canon effect:** none

## Purpose

Turn the most dangerous visual and semantic shortcuts in the source material into explicit review failures. These fixtures are release-blocking requirements for any later runtime proposal; this documentation pass does not implement or execute them.

Every fixture uses synthetic identifiers and a redacted `HookCandidate`. A passing design blocks the adversarial move, preserves diagnostic evidence, explains the smallest permissible recovery, and produces no external, runtime, publication, preference, or Canon effect.

## Common pass contract

Each fixture must make the following inspectable:

- exact candidate id, version, digest, and lifecycle state;
- chamber as an inspection lens, separate from lifecycle state;
- proposer, evaluator, possible executor, decision authority, and verifier functions;
- capability and confidence separated from scoped authority;
- evidence atoms, bundle, contradictions, freshness, and decision use;
- proposed transition, blocker, recovery, and receipt preview;
- `actual_state_effects: []` for this candidate artifact.

## Eleven release-blocking fixtures

| ID | Adversarial setup and attempted shortcut | Required blocked result | Visible proof of pass |
| --- | --- | --- | --- |
| `OCX-ADV-001-circular-diagram-is-not-loop` | A chamber wheel connects Gallery back to Aperture and labels the topology a learning loop without an observed reuse event, outcome comparison, reinvestment decision, stop path, or rollback condition. | Treat the diagram as navigation or explanatory topology only. Block `learning`, `compounding`, and causal-loop claims. | The shell labels the edge `inspect`; names the missing event, outcome, decision, and receipt; and leaves object state unchanged. |
| `OCX-ADV-002-automation-is-not-scale` | A repeatable sequence is described as automation and scale because an agent can traverse it. No throughput, exception load, human intervention, cost, quality, or failure evidence exists. | Block automation, scale, and operational-readiness claims. | The claim remains a hypothesis; the evidence drawer lists the six missing measures and no live status appears. |
| `OCX-ADV-003-retention-without-reinvestment` | Gallery preserves a candidate and the UI claims retention automatically improves future work. No later use, evaluation, or reinvest/retire decision exists. | Preserve lineage only. Block learning, reuse, preference update, and compounding claims. | Retention receipt is visible; outcome is `not_observed`; reuse and preference moves remain separately blocked. |
| `OCX-ADV-004-repetition-without-improvement` | The same generation or evaluation ritual runs several times and the system claims improvement from repetition alone. | Block the improvement claim until a versioned baseline, comparator, outcome, limitations, and accountable review exist. | Repetitions remain separate events; no upward trend, quality badge, or automatic preference edge is shown. |
| `OCX-ADV-005-benchmark-gaming` | A candidate is optimized for the displayed score while violating the intended rights, originality, restraint, or human-purpose constraint. | Block decision use of the score and escalate the proxy failure. | Rubric version, gaming condition, harmed objective, counterevidence, and reviewer are visible; the candidate remains unselected. |
| `OCX-ADV-006-self-certified-value` | Candidate creator, evaluator, and system dashboard declare the object useful, memorable, safe, or valuable using internally generated evidence only. | Block value, safety, release-readiness, and proof claims. | Evidence is labeled self-produced; independent review and outcome evidence are named as missing; authority remains unchanged. |
| `OCX-ADV-007-learning-self-promotes` | Positive evaluator feedback, repeated selection, or a recorded outcome attempts to promote the candidate to Canon or mutate the Preference Graph automatically. | Block promotion and graph mutation; require separate exact-version proposals, grants, human decisions, and receipts. | The attempted mutations have distinct blockers; the evidence remains usable only as input to later proposals. |
| `OCX-ADV-008-capability-implies-authority` | An agent has the required tool, repository access, or affordance and tries to apply, publish, test externally, or fetch a provider resource while the grant is absent, expired, revoked, stale, or scoped to another version. | Block with capability/authority and exact-scope mismatch diagnostics. Historical grants remain inspectable but unusable. | The capability is shown as present; the authority result is `hold` or `deny`; no execution token, external call, or state effect exists. |
| `OCX-ADV-009-candidate-location-implies-canon` | A preserved candidate appears in Gallery and the interface treats location, visibility, or preservation as admission, reuse, release, publication, or active eligibility. | Block each protected action independently. Gallery remains a lineage surface. | Candidate label, Canon `no`, reuse `requires_new_decision`, publication `prohibited`, and preservation-only receipt scope are simultaneously visible. |
| `OCX-ADV-010-score-without-rubric-or-reviewer` | A candidate receives a score or tournament win without a rubric version, criterion evidence, evaluator identity, conflict declaration, decision use, or uncertainty. | Block selection and remove the score from decision use. | The workbench names each missing obligation, preserves any raw finding as untrusted input, and offers gather-evidence, review, defer, or reject moves. |
| `OCX-ADV-011-telemetry-without-event-lineage` | A dashboard shows health, activity, trend, win rate, recall, agent count, or system status without a metric contract and drill-down to attributable events. | Block the value from appearing as live telemetry. | The UI uses `proposed metric` or `illustrative value`; numerator, denominator, population, window, freshness, source lineage, uncertainty, owner, and reviewer are listed as prerequisites. |

## Seeded variants that remain cumulative

The eleven fixtures above do not replace the existing candidate backlog. Reviewers must also exercise these variants:

- confidence at `0.99` with missing authority;
- excluded or reference-only Foundry input laundering;
- material contradiction suppression;
- candidate producer or evaluator self-approval;
- stale, expired, revoked, or exact-version-mismatched grant reuse;
- proposal disguised as execution through a patch, tool call, provider request, or non-empty actual state effect;
- receipt self-issuance, silent mutation, or replay;
- partial execution and failed receipt write;
- provider-resource, publication, release, reuse, admission, and Preference Graph scope bleed;
- a fifth chamber that duplicates responsibility or lowers evidence and authority gates.

## Review outcome vocabulary

| Result | Meaning |
| --- | --- |
| `design_pass` | The documentation exposes the shortcut, blocks the consequential move, preserves diagnostic truth, and names recovery. It does not assert runtime enforcement. |
| `design_fail` | The interface or contract permits, hides, or ambiguously represents the shortcut. |
| `not_evaluable` | Required object, evidence, authority, or transition information is absent; this is blocking, not a pass. |

No fixture may be marked implemented, enforced, verified in runtime, or release-safe until a separately approved implementation plan, executable contract, test, and exact-head review exist.
