---
name: quirk-intent-shaper
description: Compile explicit intent, purpose-scoped preference evidence, persona selection, voice/tone/aesthetic rules, platform effects, settings, authority, and task affordances into a reversible Personalization Plan and adaptive response experience.
---

# Quirk Intent Shaper

## Quirk contract

- Version: `0.1.0`
- Status: `candidate`
- Authority ceiling: `propose`
- Primary output: `PersonalizationPlan`
- Canonical schema: `schemas/personalization-plan.schema.json`
- Exploratory source: `skills/quirk-intent-shaper/skill-scratchpad.md`
- Evaluation suite: `evals/intent-shaper/cases.json`

## Use when

Use this skill when output quality depends materially on one or more of:

- the user’s current desired change rather than the literal wording alone;
- a purpose-specific persona or functional lens;
- voice, tone, lexical, aesthetic, or formatting preferences;
- platform-specific expectations;
- task-specific interaction affordances;
- known negative preferences or anti-patterns;
- conflicting, uncertain, stale, or inferred preference evidence;
- preserving human authority while adapting future behavior.

Do not invoke merely because a user has a profile. Personalization must improve the current outcome.

## Inputs

- current request and surrounding conversation;
- goal, desired change, urgency, stakes, destination, and output class;
- relevant purpose-scoped Preference Graph edges;
- persona candidates and role definitions;
- voice, tone, aesthetic, and lexical contracts;
- settings and explicit controls;
- platform capabilities and constraints;
- available task affordances;
- authority and consent boundaries;
- recent feedback receipts and supersession history.

## Procedure

1. **Resolve intent.** State the desired change, task class, stakes, destination, and completion evidence.
2. **Partition purpose.** Retrieve only preference evidence valid for this purpose and context.
3. **Rank authority.** Apply `explicit current instruction > explicit purpose-scoped preference > reaffirmed durable preference > observed behavior > inference`.
4. **Expose conflicts.** Never silently average incompatible preferences.
5. **Select a Persona Hand.** Choose one primary lens plus bounded supporting lenses; do not flatten the user into one persona.
6. **Compile expression.** Produce voice, tone, aesthetic, lexical, structural, and negative constraints.
7. **Resolve platform affects.** Model how destination, modality, latency, privacy, collaboration, and versioning change the response.
8. **Select task affordances.** Choose the smallest interface or output form that improves the task: diff, decision card, ranked pair, map, simulator, checklist, code patch, batch review, timeline, generated UI, or plain prose.
9. **Generate candidates.** Produce one default candidate and alternatives only when uncertainty or choice is useful.
10. **Run the Alignment Tribunal.** Score intent fit, preference fit, platform fit, task fit, evidence, authority, accessibility, and strange-intact quality.
11. **Emit a receipt.** Record used evidence, ignored evidence, conflicts, confidence, deviations, and proposed preference updates.

## Output

```yaml
personalization_plan:
  intent:
  purpose_partition:
  persona_hand:
  voice:
  tone:
  aesthetic:
  preferences_used:
  preferences_rejected:
  platform_affects:
  task_affordances:
  settings:
  authority:
  uncertainty:
  evaluation:
  learning:
```

## Invariants

- Intent outranks persona performance.
- Truth and safety outrank style.
- Current explicit instructions outrank remembered preferences.
- Purpose-specific preferences do not leak into unrelated contexts.
- A platform changes affordances, not identity.
- A persona is a lens, not a claim about the user’s permanent self.
- Negative preferences are first-class constraints.
- Inference never becomes Canon without human admission.
- Personalization can be disabled, inspected, corrected, scoped, expired, or forgotten.
- Capability to adapt does not imply authority to update memory or settings.
- The best interface may be no generated interface at all.

## Stop conditions

Stop and request one material clarification—or proceed with an explicitly stated conservative assumption—when:

- two current explicit instructions conflict;
- the task is consequential and personalization could obscure evidence or risk;
- the selected platform cannot support the required affordance safely;
- memory is stale, untrusted, or outside the current purpose;
- adaptation would require sensitive inference;
- the system would need to impersonate the user rather than support them;
- a proposed preference update would silently change future behavior.

## Admission posture

This candidate may infer and propose a plan. It may not:

- write Canon;
- activate itself;
- alter user settings;
- promote an inferred preference;
- erase preference history;
- execute a protected action;
- choose a permanent persona;
- deploy an adaptive interface to production without a separate grant.
