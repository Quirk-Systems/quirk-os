# Quirk Commerce — Weird Money Pack Review Amendment

**Status:** Normative companion to the candidate design for implementation planning.

**Reviewed:** 2026-08-21

## Admission verdict

APPROVE WITH INCORPORATED CLARIFICATIONS. The design is coherent enough to enter implementation planning once the following four clarifications are treated as normative.

## A1. Lifecycle states must not collide with object types

`OfferCandidate` remains an object type, not a lifecycle state. Replace the ambiguous lifecycle state `OFFER_CANDIDATE` with `OFFER_EVIDENCED`.

Normative lifecycle:

```text
OBSERVED
  -> CANDIDATE
  -> PROOF_DESIGNED
  -> APPROVED_TO_TEST
  -> TESTING
  -> EVIDENCED
  -> OFFER_EVIDENCED
  -> APPROVED_TO_SELL
  -> LIVE
  -> RETIRED
```

`EVIDENCED -> OFFER_EVIDENCED` means sufficient evidence exists to propose the offer for sale; it does not itself authorize sale.

## A2. Commercial projections must extend existing Quirk experiment and authority machinery, not duplicate it

The candidate runtime table names in the design are logical projections, not permission to fork canonical systems.

- `CommercialExperiment` MUST reference an existing `quirk_experiments.id` and may have a commerce-specific extension row. It MUST NOT create an independent experiment authority/history system.
- Commercial grants and authority receipts MUST reference the existing Quirk grant/receipt contract once resolved in-repo. A commerce-specific table may only project/query those receipts; it MUST NOT become a second canonical authority ledger.
- `RevenueReceipt` is distinct because it records economic evidence, but its `authority_receipt_ref` MUST point to canonical authority evidence rather than a mutable local approval flag.

## A3. Authority is referenced and evaluated, not stored as self-validating mutable state

Fields named `authority_state` in `MoneyPath` and `OfferCandidate` are implementation shorthand only. Runtime schemas SHOULD use references/projections such as:

```text
authority_requirement
authority_grant_ref
authority_receipt_ref
authority_evaluated_at
authority_effective_until
```

Effective authority MUST be recomputed/validated at consequential transitions. Cached projections may improve UX but can never confer authority after a grant has expired, been revoked, or is outside scope.

## A4. Adapter contracts require side-effect and reliability semantics

A capability list alone is insufficient for safe commerce execution. Every adapter manifest MUST include:

```text
adapter_id
adapter_version
vendor
capabilities[]
read_scopes[]
write_scopes[]
side_effect_classes[]
auth_method
webhook_verification
idempotency_support
retry_semantics
rate_limit_semantics
money_movement
external_publication
pii_classes[]
secret_classes[]
data_retention
reconciliation_strategy
failure_modes[]
```

Each executable adapter operation MUST declare whether it can publish externally, move money, create customer-visible state, mutate catalog/order/subscription state, or expose personal data. Human grants bind to those operation scopes, not merely to an adapter name.

## Privacy / data-minimization clarification

`customer_or_participant_ref` in `RevenueReceipt` SHOULD be an internal pseudonymous reference by default. Raw customer PII, payment credentials, and vendor secrets MUST NOT be copied into Quirk evidence records when a stable opaque reference is sufficient.

## v0.1 implementation cut

The implementation plan should prove the contracts before broad vendor integration:

1. canonical commercial schemas and validators;
2. canonical-to-commercial experiment linkage;
3. authority reference/evaluation boundary;
4. adapter manifest + operation contract;
5. manual adapter as the reference adapter;
6. one processor/checkout adapter after contract tests pass;
7. one merchant/distribution projection only as required for the end-to-end proof;
8. evidence receipt and decision memo;
9. Supabase projection + RLS;
10. operator projections after runtime truth exists.

No vendor-specific adapter is canonicalized merely because it is listed in the design.
