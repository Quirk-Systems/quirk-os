# Taste Engine Experience Contract

## Product outcome

A participant can make one beauty choice, understand the candidate evidence derived from it, test a recommendation, and deliberately control the Preference Graph update.

The experience must make the chain visible without forcing the participant to understand graph theory or governance jargon.

## Screen 1 — Purpose Gate

**Question:** What decision are we learning for?

Required:

- one named purpose partition;
- short statement of what will and will not be remembered;
- explicit start action;
- no preselected consent;
- exit without penalty.

Example surface copy:

> We are learning what fits your everyday lip preference. This trial will not use your choice for ads, campaigns, or purchases.

## Screen 2 — Choice Card

Required:

- two or more options;
- visible attributes used in comparison;
- `Choose A`, `Choose B`, and `Neither / Can't tell`;
- no recommendation language before the choice;
- keyboard and screen-reader labels;
- no dark pattern that makes abstention look like failure.

## Screen 3 — Evidence Receipt

Required:

- plain-language summary of what the system observed;
- feature-level contrasts;
- confidence and uncertainty;
- `Correct this` and `Do not use this` controls;
- explicit statement: “This is candidate evidence, not a permanent preference.”

## Screen 4 — Recommendation

Required:

- candidate option;
- reasons linked to evidence;
- strongest mismatch or uncertainty;
- expiry;
- alternate and abstain paths;
- no purchase CTA in v0.1;
- visible statement: “Recommendation, not action.”

## Screen 5 — Outcome Capture

Opened only after the participant has had a reasonable chance to test the option.

Required choices:

- `Preferred it`;
- `Rejected it`;
- `Mixed result`;
- `Did not test`.

Required:

- brief optional note;
- no inference from purchase, click, time, or return visit;
- context confirmation;
- “Did not test” closes the run without a graph proposal.

## Screen 6 — Graph Update Review

Show exact proposed changes:

```text
finish=satin          +0.15
chroma=muted          +0.15
fragrance=low         +0.15
purpose               personal_beauty_recommendation
expected revision     12
expires               2:45 PM
```

Controls:

- **Approve** — apply exactly as shown.
- **Revise** — edit or remove proposed feature changes.
- **Reject** — preserve the outcome but apply no graph mutation.

Nothing is preselected.

## Screen 7 — Receipt

Required:

- decision;
- applied or not applied;
- before/after revision;
- evidence references;
- receipt digest;
- `Undo / supersede` route if supported by Quirk core;
- statement of what authority was **not** granted.

## State transitions

```text
purpose_declared
  → choice_recorded | abandoned
  → evidence_reviewed | corrected | suppressed
  → recommendation_proposed | insufficient_evidence
  → outcome_recorded | not_tested
  → graph_update_proposed
  → approved | revised | rejected | expired
  → receipted
```

## Success condition

The participant can explain the recommendation and graph change without operator translation. A beautiful interface that obscures state truth fails.
