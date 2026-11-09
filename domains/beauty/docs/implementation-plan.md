# Implementation Plan

## Workstream 0 — Boundary admission

**Done in pack:** canonical boundary, candidate ceiling, proof requirement.

Merge criterion: the authoritative Quirk Git repository contains only the boundary under `docs/canon/`; all other pack files remain candidate.

## Workstream 1 — Deterministic kernel

1. Keep failing adversarial tests first.
2. Implement explicit choice validation.
3. Derive contrast-based candidate evidence.
4. Rank candidates deterministically.
5. Emit evidence-linked factors and expiry.
6. Deny unscoped or insufficient inputs.

Merge criterion: Node 22 and canonical Node 24 CI pass with identical fixture output.

## Workstream 2 — Human Gate adapter

1. Bind proposal to actor, purpose, expected graph revision, and expiry.
2. Keep `autoApply: false` structurally required.
3. Require approve/revise/reject.
4. Replace candidate local receipt writer with Quirk core's authenticated effect receipt service.
5. Add forged, replayed, expired, and cross-purpose grant fixtures.

Merge criterion: no candidate module can call the graph repository without the gate adapter.

## Workstream 3 — Supabase projection

1. Apply migration to an isolated development project.
2. Verify exposed schema grants.
3. Run RLS tests as two users plus anonymous access.
4. Confirm append-only event behavior.
5. Verify service-role keys never reach a client surface.

Merge criterion: RLS evidence and schema digest attached to the PR.

## Workstream 4 — Product surface

1. Build the seven states in `product-design/experience-contract.md`.
2. Show evidence before outcome capture.
3. Include abstain, insufficient evidence, expiry, revise, reject, and conflict states.
4. Run the usability script.

Merge criterion: one participant can explain every transition without operator coaching.

## Workstream 5 — Real-world proof

1. Select one testable beauty choice.
2. Complete the runbook.
3. Generate the evidence bundle.
4. Pass the verifier.
5. Review the receipt and failure log.

Release criterion: `proof/evidence/real-proof.json` passes and Bryan separately decides whether any candidate artifact advances.
