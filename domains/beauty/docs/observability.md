# Observability

## Goal

Make state transitions and failures inspectable without turning personal beauty evidence into telemetry exhaust.

## Required event envelope

```text
event_id
schema_version
session_id
correlation_id
actor_ref_pseudonymous
purpose
stage
result
failure_code
candidate_version
policy_version
timestamp
```

## Events

- `beauty.taste.session_started`
- `beauty.taste.choice_recorded`
- `beauty.taste.choice_abstained`
- `beauty.taste.evidence_derived`
- `beauty.taste.recommendation_ranked`
- `beauty.taste.insufficient_evidence`
- `beauty.taste.outcome_recorded`
- `beauty.taste.graph_update_proposed`
- `beauty.taste.graph_update_approved`
- `beauty.taste.graph_update_revised`
- `beauty.taste.graph_update_rejected`
- `beauty.taste.graph_update_denied`
- `beauty.taste.receipt_written`
- `beauty.taste.proof_verified`

## Metrics

- chain completion by stage;
- abstention rate;
- insufficient-evidence rate;
- recommendation expiry rate;
- outcome `not_tested` rate;
- graph proposal approve/revise/reject rate;
- denial count by failure code;
- stale revision rate;
- proof-verifier pass rate;
- correction rate by feature class.

## Logging prohibitions

Do not place in general logs:

- raw participant notes;
- full option images;
- sensitive attributes;
- access tokens, API keys, or service-role credentials;
- complete Preference Graph state;
- exact user identifiers when a scoped pseudonymous reference is sufficient.

## Alert conditions

- any graph mutation without a matching decision and receipt;
- any event with mismatched actor or purpose lineage;
- any `autoApply=true` proposal;
- any anonymous access to beauty tables;
- any real proof marked synthetic;
- any canonical status outside the canon path.
