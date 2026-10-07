# Quirk workflow delivery conventions v0.1

Status: REVIEW CANDIDATE — manual conventions, not runtime configuration.
Owner for review: Bryan.
Observed source: quirk-os main 5096cf047b8d4eecd0d9312ea7bc4615ae322c92, 2026-10-03.
Scope: deliver small subsystem slices using existing repository boundaries.

## Placement

| Concern | Home | Rule |
| --- | --- | --- |
| Shared meanings and invariants | Quirk Core and applicable organization registries | Reference the owning source; propose amendments there |
| Composition, runbooks, subsystem delivery | quirk-os docs/ | Keep the smallest coherent slice with its operating owner |
| Reusable blank records | quirk-os templates/ | Separate templates from completed runs |
| Executable domain workflow definitions | quirk-os workflows/ | Add only when a consumer and validation contract exist |
| CI and reusable repository checks | .github/workflows/ in the owning repository | CI is distinct from a human operating workflow |
| Organization governance and reusable CI | Quirk-Systems/.github | Follow its own evidence and change process |
| A checklist attached to a product or domain | Existing domain documentation | Keep domain-specific criteria near their source |

[Quirk Checklists](../checklists/README.md) is the first documentation example. No new repository, registered capability, object kind, or mandatory organization policy is created.

## Defaults

| Choice | Working default | Change only when |
| --- | --- | --- |
| Scope | One outcome, one bounded move, one stop, one receipt | Multiple steps are necessary for that outcome |
| Trigger | Manual; scheduling off | A separately scoped automation is requested and configured |
| Authority | Reuse the actual authorization and its limits | The requested action materially changes scope or authority |
| Failure | Block dependent effects when required evidence or authority is missing | An applicable policy explicitly permits a bounded fallback |
| Retry | No automatic mutation retry without a defined duplicate-effect policy | Idempotency/recovery behavior is implemented and tested |
| Branch | agent/<bounded-change> | Existing branch already owns the same work |
| PR | Draft until evidence is coherent | Exact-head checks and review package support handoff |
| Identity | Stable descriptive local IDs plus explicit version | Register a shared ID only through its owning process |
| Review | Bryan's actual decision, bound to the reviewed subject | A later explicit delegation changes the review arrangement |
| State | Intended, written, observed, verified, authorized recorded separately | Never collapse these into one complete flag |
| Reuse | Scoped and evidence-backed | Broader reuse earns evidence and any needed authorization |
| Measurement | Preparation, review, correction; unknown until timed | Add metrics only to resolve a concrete decision |
| Setup | Documents and existing tools first | A real run exposes a repeatable failure requiring machinery |

These are defaults for this candidate procedure, not claims that repository settings enforce them.

## Delivery sequence

1. Inspect existing artifacts, open PRs, source owners, and applicable instructions.
2. Specify the smallest usable output, input, owner, stop condition, proof, and authorization boundary.
3. Pick the relevant distinctions from the [distinctions guide](distinctions-workflow.md).
4. Reuse a template. For a full object pack, use the existing [object-pack templates](../../templates/quirk-object-pack/README.md); preserve their required modules and explicit not-applicable entries. This lightweight guide does not change the generator.
5. Produce the bounded output and record checks against its exact version.
6. Open or update the owning PR. Retain an exact-head proof summary and any limitations.
7. Obtain the applicable human decision. Merge, activation, and promotion remain separate actions.
8. Run one real-use trial, measure burden, then keep, revise, or retire the procedure.

## Setup before executable automation

The existing [operating-workflow template](../../templates/quirk-object-pack/OPERATING-WORKFLOW.template.yaml) is the starting point, not an installed runner. Before wiring a subsystem to it, specify:

- input/output contracts and consumer;
- permitted tools, scope, external grants, and stop behavior;
- idempotency key, duplicate handling, bounded retries, and recovery for effects;
- receipt destination and failure behavior if receipt persistence fails;
- positive and adversarial fixtures;
- observability, rollback, and the human decision required for activation.

Do not emit executable-looking configuration with undefined actions and claim delivery. A configured schedule, green check, or completed checklist has only the authority its actual control grants.

## First subsystem proof

Use the [checklist template](../../templates/checklist-run.md) on one existing bounded task. Require evidence for the tested subject; include an unknown item and a stale-evidence case. A useful first result lets another reader identify what is done, blocked, and awaiting a decision without reconstructing chat. Record time and corrections before claiming efficiency gains.
