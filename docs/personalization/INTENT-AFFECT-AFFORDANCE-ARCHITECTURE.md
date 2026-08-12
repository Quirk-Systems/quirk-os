# Intent × Persona × Affect × Affordance

**Status:** Candidate architecture  
**Parent:** Quirk Sync Control Plane  
**Skill:** `skill.quirk-intent-shaper`

## Thesis

Quirk personalization should not be a personality prompt pasted on top of every task.

It should be a governed compilation process:

```text
current intent
+ purpose-scoped preference evidence
+ bounded persona lenses
+ expression contracts
+ platform affects
+ task affordances
+ authority and uncertainty
= reversible Personalization Plan
```

## Control objective

Choose an experience plan that improves the user’s intended outcome while preserving truth, authority, accessibility, inspectability, and reversibility.

```text
maximize:
  intent fit
  preference fit
  task leverage
  platform fit
  evidence quality
  independent reuse
  strange intact

subject to:
  authority
  safety
  privacy
  accessibility
  current explicit instructions
  purpose boundaries
```

No single score should hide tradeoffs. Candidate plans remain a Pareto set until policy or a human selects one.

## Precedence

```text
current explicit instruction
> current purpose-scoped setting
> reaffirmed durable preference
> recent explicit feedback
> repeated observed behavior
> bounded inference
> population default
```

Negative constraints apply before positive style optimization.

## Architecture layers

### 1. Intent plane

Resolves:

- desired change;
- task class;
- stakes;
- destination;
- audience;
- completion evidence;
- constraints and non-goals.

### 2. Preference plane

Stores purpose-scoped edges with:

- source;
- confidence;
- comparison target;
- time;
- validity;
- reversibility;
- sensitivity;
- supersession.

### 3. Persona plane

Selects a temporary Persona Hand:

- primary functional lens;
- supporting lenses;
- weights;
- task role;
- explicit exclusions.

### 4. Expression plane

Compiles:

- voice;
- tone vector;
- lexical rules;
- aesthetic principles;
- structural preferences;
- no-fill rules;
- accessibility needs.

### 5. Platform-affect plane

Maps the destination into operational pressure:

- versioning;
- collaboration;
- privacy;
- latency;
- screen and modality;
- reversibility;
- execution capability;
- expected evidence.

### 6. Task-affordance plane

Selects useful interaction primitives from an admitted registry.

### 7. Evaluation plane

Runs pointwise and counterfactual checks before preference ranking.

### 8. Learning plane

Creates immutable feedback receipts and proposed preference updates.

## Platform Affect contract

A `PlatformAffect` does not say what the user likes. It says how a platform changes the task.

```yaml
platform_affect:
  platform: github
  effects:
    - versioned
    - collaborative_review
    - diff_first
    - executable_evidence
  preferred_affordances:
    - patch
    - check_run
    - issue
    - review_comment
  prohibited:
    - infer_merge_authority
    - claim_success_without_checks
```

## Task Affordance contract

```yaml
task_affordance:
  type: ranked_pair
  purpose: reveal_preference
  reversible: true
  evidence:
    - explicit_selection
  accessibility:
    keyboard: required
    screen_reader: required
  fallback: numbered_text_options
```

## Adaptation states

```text
UNKNOWN
→ OBSERVED
→ INFERRED
→ PROPOSED
→ CONFIRMED
→ PURPOSE-SCOPED
→ SUPERSEDED / EXPIRED / FORGOTTEN
```

No implicit signal may jump directly to `CONFIRMED`.

## Feedback semantics

A user edit can mean several different things:

- the fact was wrong;
- the task was misunderstood;
- the platform form was wrong;
- the preference was wrong;
- the preference changed;
- the candidate was good but not chosen;
- the user wanted variety.

The receipt must classify the cause before updating confidence.

## Generated UI admission

Generated UI is permitted only when:

1. the task benefits from interaction;
2. the component grammar is admitted;
3. every action declares state effects;
4. protected actions have explicit gates;
5. keyboard and screen-reader paths exist;
6. a plain-text fallback exists;
7. the interface can be reconstructed from its plan;
8. the user can inspect why it was selected.

## Why this fights generic enterprise AI

A conventional integration firm can connect ERP, CRM, WMS, cloud, and data.

Quirk’s differentiator is the layer that decides:

- what the user is actually trying to accomplish;
- which version of the user is useful for this task;
- how the relationship should sound and feel;
- what each platform changes;
- what interface should exist now;
- which adaptation is allowed to persist;
- what evidence proves the adaptation helped.
