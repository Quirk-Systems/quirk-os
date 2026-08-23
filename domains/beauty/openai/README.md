# OpenAI Explanation Adapter — Candidate

This adapter is an optional renderer for an already-ranked, evidence-locked recommendation. It is not the Taste Engine.

## Allowed

- convert deterministic factors into concise human-readable reasons;
- preserve exact recommendation, purpose, score, confidence, and evidence IDs;
- surface uncertainty;
- return strict structured output.

## Forbidden

- choose or reorder candidates;
- invent evidence or product claims;
- infer an outcome or sensitive attribute;
- grant authority;
- issue a decision or receipt;
- publish, purchase, message, or mutate any graph;
- retain proof input by default.

`buildExplanationRequest()` requires the runtime to inject the model identifier and sets `store: false`. No API key, network call, or default model is committed in this pack.
