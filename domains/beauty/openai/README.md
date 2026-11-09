# OpenAI Adapter Boundary

## v0.1 decision

OpenAI is **not** a ranking dependency and is **not** required to complete the Taste Engine proof.

The deterministic kernel produces:

- selected option;
- score;
- confidence;
- evidence IDs;
- feature contributions;
- uncertainty and expiry.

A later OpenAI adapter may turn those facts into clearer explanation copy using schema-constrained output. It cannot change the option, score, evidence, purpose, authority, or graph proposal.

## Allowed use

```text
ranked recommendation + cited factors
                ↓
strict structured explanation renderer
                ↓
UI copy with the same evidence and uncertainty
```

## Forbidden use

- model chooses a different recommendation without a visible new candidate proposal;
- model invents product or ingredient facts;
- model infers satisfaction from behavior;
- model diagnoses health or skin conditions;
- model calls purchase, publish, message, or graph-update tools;
- model stores the participant's preference data by default;
- model output becomes canon.

## Implementation gate

Before adding the API adapter:

1. complete the deterministic proof path;
2. bind to Quirk's provider gateway and secret management;
3. use strict structured output against `recommendation-explanation.schema.json`;
4. set retention behavior deliberately for the relevant request and purpose;
5. add evals for evidence preservation, unsupported claims, refusal handling, and instruction injection;
6. show the original deterministic factors beside or behind the generated explanation.

No API key, SDK dependency, or live model call is included in v0.1.
