# One-to-Infinity Candidate Contracts

Version: `0.1.0-candidate`
Status: candidate-only / no-runtime / no-canon-promotion

## 1. Transformation Contract

Purpose: define the proposed value-producing transformation before machinery exists.

Required fields:

- `contract_type = one_to_infinity_transformation`
- `schema_version`
- `status = candidate`
- `candidate_only = true`
- `no_runtime = true`
- `no_canon_promotion = true`
- `transformation_id`
- `owner`
- `value_contract`
- `mechanism`
- `loop_classification`
- `economics`
- `evidence_requirements`
- `governance`
- `promotion_policy`

Required `value_contract` fields:

- `beneficiary`
- `problem`
- `before_state`
- `desired_after_state`
- `value_measure`
- `minimum_effect`
- `non_value_proxies`

Required `mechanism` fields:

- `trigger`
- `actor`
- `action`
- `observable_output`
- `retained_state`
- `reinvestment_rule`
- `constraints`
- `balancers`
- `delays`

Reject when:

- no retained state exists;
- retained state is not wired to a later cycle;
- a circular diagram is treated as loop proof;
- constraints, balancers, or delays are absent;
- automation is treated as scalability;
- the transformation claims canon or runtime status.

## 2. Run Contract

Purpose: record one bounded execution cycle without expanding authority.

Required fields:

- `contract_type = one_to_infinity_run`
- `schema_version`
- `run_id`
- `transformation_id`
- `cycle_index`
- `status`
- `authority_scope`
- `trigger`
- `inputs`
- `action_trace`
- `outputs`
- `observations`
- `retained_state_updates`
- `receipts`
- `metrics`
- `learning_updates`

Authority constraints:

- `human_gate_required = true`
- `provider_may_promote = false`
- `may_modify_promotion_policy = false`
- retained-state updates require promotion decision
- learning updates remain candidate until authorized

Reject when:

- provider execution is treated as authority;
- delayed feedback is interpreted immediately;
- retained learning persists without a human gate;
- a run claims canon, deployment, or publication status.

## 3. Evidence Contract

Purpose: record proof for exactly one evidence stage.

Allowed evidence stages:

- `value_proof`
- `retention_proof`
- `closure_proof`
- `economic_scalability_proof`
- `compounding_proof`

Required fields:

- `contract_type = one_to_infinity_evidence`
- `schema_version`
- `evidence_id`
- `transformation_id`
- `evidence_stage`
- `claim`
- `proof_status`
- `source_refs`
- `evaluator`
- `method`
- `baseline`
- `observed_result`
- `falsification`
- `limitations`
- `decision`

Additional requirements:

- economic scalability proof requires unit economics;
- compounding proof requires comparator, retained-state use, and positive measured delta;
- value proof requires beneficiary outcome or behavior evidence, not proxy motion alone;
- evaluator must not be the same agent that produced the output.

Reject when:

- benchmark score replaces beneficiary value;
- self-certification replaces review;
- repetition is labeled compounding;
- proxy success is laundered as outcome evidence;
- economic scalability lacks marginal cost, scarce attention, and constraint data.

## 4. Promotion Contract

Purpose: request or record a status transition while preventing accidental canonization.

Required fields:

- `contract_type = one_to_infinity_promotion`
- `schema_version`
- `promotion_request_id`
- `transformation_id`
- `source_status`
- `target_status`
- `requested_change`
- `required_evidence`
- `decision`
- `scope`
- `guards`
- `exclusions`

Required evidence IDs:

- `value_proof_evidence_id`
- `retention_proof_evidence_id`
- `closure_proof_evidence_id`
- `economic_scalability_proof_evidence_id`
- `compounding_proof_evidence_id`
- `artifact_digest`
- `exact_version`

Required guards:

- `no_auto_promotion = true`
- `no_provider_authority = true`
- `no_transitive_authority = true`
- `rollback_plan`
- `post_promotion_monitoring`

Reject when:

- learning promotes itself;
- agent confidence is treated as authority;
- provider execution is treated as semantic authority;
- approval lacks exact human decision receipt;
- scope implies canon, deployment, publication, or provider access.
