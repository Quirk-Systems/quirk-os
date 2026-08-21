# Quirk Commerce — Weird Money Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the smallest executable Quirk Commerce domain pack that turns one Quirk asset into a governed commercial hypothesis, bounded market experiment, evidence receipt, and decision without vendor lock-in or authority leakage.

**Architecture:** Canonical commercial contracts live in Git as JSON Schema and policy code. Supabase projects them into a `quirk_commerce` runtime schema while reusing existing `quirk_assets` and `quirk_experiments`; adapters expose capability-scoped operations behind Quirk-owned manifests; external operator surfaces remain projections. v0.1 proves the system with the manual reference adapter plus a Stripe event adapter that normalizes processor evidence without granting autonomous money movement.

**Tech Stack:** JSON Schema Draft 2020-12, Python 3 + `jsonschema` + PyYAML using existing repository validator patterns, PostgreSQL/Supabase with RLS and append-only evidence, GitHub Actions, JSON/YAML fixtures.

**Spec:** `docs/superpowers/specs/2026-08-21-quirk-commerce-weird-money-pack-design.md`

**Normative review amendment:** `docs/superpowers/specs/2026-08-21-quirk-commerce-weird-money-pack-review-amendment.md`

## Global Constraints

- Quirk owns the ontology; vendors are adapters.
- Distribution, Marketing, Merchant, and Commerce remain distinct layers.
- Capability never implies authority.
- Projection is not authority.
- No Zombie Truth: vendor/runtime divergence is surfaced, not silently reconciled.
- `OfferCandidate` is an object type; the lifecycle state is `OFFER_EVIDENCED`.
- `CommercialExperiment` extends an existing `quirk_experiments.id`; it does not fork experiment history.
- Commercial authority references canonical Quirk grants/receipts; commerce does not create a second authority ledger.
- Runtime authority is evaluated from grant references at consequential transitions; cached state cannot confer authority.
- Customer references are pseudonymous by default; raw payment credentials and vendor secrets never enter Quirk evidence records.
- All new Supabase tables require RLS and fail closed until explicit policies are admitted.
- External adapter IDs are namespaced and never become Quirk primary identity.
- v0.1 has no autonomous pricing, ad buying, marketplace aggregation, generalized CRM, tax engine, or universal storefront builder.

---

## File Structure

Create a focused `quirk_commerce` implementation beside existing sync-control-plane patterns:

```text
schemas/
  commerce-money-path.schema.json
  commerce-offer-candidate.schema.json
  commerce-experiment-extension.schema.json
  commerce-adapter-manifest.schema.json
  commerce-adapter-operation.schema.json
  commerce-event.schema.json
  commerce-revenue-receipt.schema.json
  commerce-decision.schema.json

scripts/
  quirk_commerce/
    __init__.py
    lifecycle.py
    authority.py
    adapters.py
    evidence.py
    decisions.py
    projections.py
  validate_quirk_commerce.py

adapters/
  commerce/
    manual/manifest.json
    stripe/manifest.json

mappings/
  commerce/
    airtable-projection.json
    notion-projection.json
    google-drive-projection.json
    cloudflare-projection.json

evals/
  quirk-commerce/
    fixtures.json
    valid/
    cases/
    conformance-results.json

examples/
  quirk-commerce/
    weird-money-001/
      asset.json
      money-path.json
      offer-candidate.json
      experiment-extension.json
      adapter-operation.json
      commerce-event.json
      revenue-receipt.json
      decision.json
      README.md

supabase/migrations/
  20260821xxxxxx_quirk_commerce_contracts.sql
  20260821xxxxxx_quirk_commerce_security.sql

.github/workflows/
  quirk-commerce-conformance.yml

docs/commerce/
  README.md
  ADMISSION.md
  ADAPTERS.md
  OPERATOR-PROJECTIONS.md
  PROOF-001.md
```

---

### Task 1: Canonical Commercial Object Schemas and Lifecycle

**Files:**
- Create: `schemas/commerce-money-path.schema.json`
- Create: `schemas/commerce-offer-candidate.schema.json`
- Create: `schemas/commerce-experiment-extension.schema.json`
- Create: `schemas/commerce-revenue-receipt.schema.json`
- Create: `schemas/commerce-decision.schema.json`
- Create: `scripts/quirk_commerce/__init__.py`
- Create: `scripts/quirk_commerce/lifecycle.py`
- Test via: `scripts/validate_quirk_commerce.py`

**Interfaces:**
- Consumes: existing Quirk object references, `quirk_assets.id`, `quirk_experiments.id`, canonical grant/receipt reference strings.
- Produces: `validate_transition(from_state: str, to_state: str, *, grant_valid: bool, evidence_refs: list[str]) -> list[str]` and five stable JSON contracts.

- [ ] **Step 1: Write the failing lifecycle unit fixture**

Create `evals/quirk-commerce/cases/QC-001-lifecycle.json`:

```json
{
  "from": "EVIDENCED",
  "to": "APPROVED_TO_SELL",
  "grant_valid": false,
  "evidence_refs": ["receipt.revenue.test"],
  "expected": "BLOCK"
}
```

- [ ] **Step 2: Add the canonical state machine**

Create `scripts/quirk_commerce/lifecycle.py` with this public surface:

```python
LIFECYCLE = (
    "OBSERVED",
    "CANDIDATE",
    "PROOF_DESIGNED",
    "APPROVED_TO_TEST",
    "TESTING",
    "EVIDENCED",
    "OFFER_EVIDENCED",
    "APPROVED_TO_SELL",
    "LIVE",
    "RETIRED",
)

HUMAN_GATED = {
    ("PROOF_DESIGNED", "APPROVED_TO_TEST"),
    ("OFFER_EVIDENCED", "APPROVED_TO_SELL"),
}


def validate_transition(from_state: str, to_state: str, *, grant_valid: bool, evidence_refs: list[str]) -> list[str]:
    errors: list[str] = []
    if from_state not in LIFECYCLE or to_state not in LIFECYCLE:
        return ["unknown lifecycle state"]
    if LIFECYCLE.index(to_state) != LIFECYCLE.index(from_state) + 1 and to_state != "RETIRED":
        errors.append("transition is not adjacent or retire")
    if (from_state, to_state) in HUMAN_GATED and not grant_valid:
        errors.append("explicit valid grant required")
    if to_state in {"EVIDENCED", "OFFER_EVIDENCED", "APPROVED_TO_SELL", "LIVE"} and not evidence_refs:
        errors.append("evidence reference required")
    return errors
```

- [ ] **Step 3: Write JSON Schemas using repository conventions**

Each schema MUST use Draft 2020-12, `additionalProperties:false`, stable `$id`, explicit required fields, and string patterns for Quirk references. `commerce-experiment-extension.schema.json` MUST require `quirk_experiment_id`; it MUST NOT define an independent experiment identity/history contract.

For `commerce-revenue-receipt.schema.json`, require at minimum:

```json
{
  "receipt_id": "receipt.revenue.*",
  "quirk_experiment_id": "uuid",
  "offer_candidate_ref": "offer.*",
  "event_type": "purchase|preorder|pledge|subscription_start|subscription_renewal|refund|cancellation|payout|local_payment|no_sale",
  "currency": "ISO-4217 string",
  "gross_amount_minor": 0,
  "fees_minor": 0,
  "refund_amount_minor": 0,
  "net_amount_minor": 0,
  "vendor": "namespaced adapter id",
  "vendor_event_ref": "opaque string",
  "participant_ref": "pseudonymous internal ref or null",
  "occurred_at": "date-time",
  "captured_at": "date-time",
  "evidence_refs": ["..."],
  "authority_receipt_ref": "receipt.*",
  "immutable": true
}
```

Store money as integer minor units; never floating-point currency.

- [ ] **Step 4: Add schema loading to the conformance runner skeleton**

Create `scripts/validate_quirk_commerce.py` using the same `Draft202012Validator`/`FormatChecker` pattern as `scripts/validate_sync_control_plane.py` and fail if any new schema is itself invalid.

- [ ] **Step 5: Run the validator and verify QC-001 is blocked**

Run:

```bash
python scripts/validate_quirk_commerce.py --require-admit
```

Expected at this stage: non-zero exit because the full fixture/eval suite is incomplete, while QC-001 reports `BLOCK` for the missing grant.

- [ ] **Step 6: Commit**

```bash
git add schemas/commerce-*.schema.json scripts/quirk_commerce scripts/validate_quirk_commerce.py evals/quirk-commerce/cases/QC-001-lifecycle.json
git commit -m "feat(commerce): add canonical object contracts and lifecycle"
```

---

### Task 2: Authority Reference Boundary

**Files:**
- Create: `scripts/quirk_commerce/authority.py`
- Create: `evals/quirk-commerce/cases/QC-002-stale-grant.json`
- Create: `evals/quirk-commerce/cases/QC-003-scope-creep.json`
- Modify: `scripts/validate_quirk_commerce.py`

**Interfaces:**
- Consumes: opaque canonical grant/receipt projections supplied by the runtime.
- Produces: `evaluate_authority(requirement: dict, grant: dict, *, now: datetime) -> AuthorityDecision`.

- [ ] **Step 1: Write stale-grant and scope-creep fixtures**

`QC-002` must present a grant whose `effective_until` precedes the evaluation time and expect `BLOCK_STALE_GRANT`.

`QC-003` must grant `budget_minor=1000` and request `budget_minor=100000`, expecting `BLOCK_SCOPE_EXCEEDED`.

- [ ] **Step 2: Implement fail-closed authority evaluation**

Create `scripts/quirk_commerce/authority.py`:

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class AuthorityDecision:
    allowed: bool
    code: str
    grant_ref: str | None


def evaluate_authority(requirement: dict, grant: dict | None, *, now: datetime) -> AuthorityDecision:
    if grant is None:
        return AuthorityDecision(False, "BLOCK_NO_GRANT", None)
    if grant.get("revoked") is True:
        return AuthorityDecision(False, "BLOCK_REVOKED", grant.get("grant_id"))
    effective_until = datetime.fromisoformat(grant["effective_until"].replace("Z", "+00:00"))
    if now > effective_until:
        return AuthorityDecision(False, "BLOCK_STALE_GRANT", grant.get("grant_id"))
    requested_budget = int(requirement.get("budget_minor", 0))
    granted_budget = int(grant.get("budget_minor", 0))
    if requested_budget > granted_budget:
        return AuthorityDecision(False, "BLOCK_SCOPE_EXCEEDED", grant.get("grant_id"))
    requested_ops = set(requirement.get("operations", []))
    granted_ops = set(grant.get("operations", []))
    if not requested_ops.issubset(granted_ops):
        return AuthorityDecision(False, "BLOCK_SCOPE_EXCEEDED", grant.get("grant_id"))
    return AuthorityDecision(True, "ALLOW_BOUNDED", grant.get("grant_id"))
```

- [ ] **Step 3: Prove cached `authority_state` cannot authorize execution**

Add a validator attack case containing `"authority_state":"approved"` with no valid grant. Expected result: `BLOCK_NO_GRANT`.

- [ ] **Step 4: Run focused conformance**

Run:

```bash
python scripts/validate_quirk_commerce.py
```

Expected: QC-002 and QC-003 pass their negative assertions.

- [ ] **Step 5: Commit**

```bash
git add scripts/quirk_commerce/authority.py scripts/validate_quirk_commerce.py evals/quirk-commerce/cases/QC-002-stale-grant.json evals/quirk-commerce/cases/QC-003-scope-creep.json
git commit -m "feat(commerce): enforce canonical authority references"
```

---

### Task 3: Adapter Manifest and Operation Contracts

**Files:**
- Create: `schemas/commerce-adapter-manifest.schema.json`
- Create: `schemas/commerce-adapter-operation.schema.json`
- Create: `scripts/quirk_commerce/adapters.py`
- Create: `adapters/commerce/manual/manifest.json`
- Create: `adapters/commerce/stripe/manifest.json`
- Create: `evals/quirk-commerce/cases/QC-004-unsupported-entitlement.json`
- Create: `evals/quirk-commerce/cases/QC-005-ungranted-side-effect.json`

**Interfaces:**
- Consumes: adapter manifest + requested operation + authority decision.
- Produces: `validate_operation(manifest: dict, operation: dict, authority: AuthorityDecision) -> list[str]`.

- [ ] **Step 1: Define manifest schema from the review amendment**

Require exactly these safety-bearing fields:

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

- [ ] **Step 2: Define operation schema**

Every operation must declare:

```json
{
  "operation_id": "op.*",
  "adapter_id": "adapter.*",
  "capability": "checkout_create",
  "side_effect_classes": ["customer_visible_state"],
  "idempotency_key": "...",
  "authority_requirement": {
    "operations": ["checkout_create"],
    "budget_minor": 0
  },
  "input_refs": [],
  "expected_output_refs": []
}
```

- [ ] **Step 3: Implement capability + side-effect validation**

```python
def validate_operation(manifest: dict, operation: dict, authority) -> list[str]:
    errors: list[str] = []
    if operation["adapter_id"] != manifest["adapter_id"]:
        errors.append("adapter mismatch")
    if operation["capability"] not in manifest["capabilities"]:
        errors.append("unsupported capability")
    undeclared = set(operation["side_effect_classes"]) - set(manifest["side_effect_classes"])
    if undeclared:
        errors.append("undeclared side effect")
    if operation["side_effect_classes"] and not authority.allowed:
        errors.append("side effect requires valid authority")
    return errors
```

- [ ] **Step 4: Add the manual reference adapter**

`adapter.manual.v1` must support evidence capture without pretending to verify processor events. Its evidence provenance class is `manual_observation` and its `money_movement` field is `false`.

- [ ] **Step 5: Add a Stripe v0 manifest with constrained scope**

`adapter.stripe.v0` declares read/event normalization capabilities and webhook verification requirements. It MUST set autonomous money movement to false for v0.1 and MUST NOT include secrets.

- [ ] **Step 6: Run negative fixtures**

Expected: unsupported entitlement projection fails; customer-visible or money-moving operation without valid grant fails.

- [ ] **Step 7: Commit**

```bash
git add schemas/commerce-adapter-*.schema.json scripts/quirk_commerce/adapters.py adapters/commerce evals/quirk-commerce/cases/QC-004-unsupported-entitlement.json evals/quirk-commerce/cases/QC-005-ungranted-side-effect.json
git commit -m "feat(commerce): add adapter capability and side-effect contracts"
```

---

### Task 4: Evidence Normalization and Revenue Receipts

**Files:**
- Create: `schemas/commerce-event.schema.json`
- Create: `scripts/quirk_commerce/evidence.py`
- Create: `evals/quirk-commerce/cases/QC-006-stripe-payment-unfulfilled.json`
- Create: `evals/quirk-commerce/cases/QC-007-refund-net-revenue.json`
- Create: `evals/quirk-commerce/cases/QC-008-local-manual-evidence.json`

**Interfaces:**
- Consumes: normalized vendor/manual events.
- Produces: `normalize_event(raw: dict, adapter_manifest: dict) -> dict` and `build_revenue_receipt(events: list[dict], authority_receipt_ref: str) -> dict`.

- [ ] **Step 1: Make processor success distinct from fulfilled value**

The normalized event schema must carry separate dimensions for `payment_state`, `order_state`, `fulfillment_state`, and `settlement_state`.

- [ ] **Step 2: Implement integer-money receipt arithmetic**

```python
def compute_net_minor(gross_minor: int, fees_minor: int, refund_minor: int) -> int:
    values = (gross_minor, fees_minor, refund_minor)
    if any((not isinstance(v, int) or v < 0) for v in values):
        raise ValueError("money values must be non-negative integer minor units")
    return gross_minor - fees_minor - refund_minor
```

A receipt whose computed net differs from supplied `net_amount_minor` must fail validation.

- [ ] **Step 3: Enforce evidence provenance classes**

Supported initial provenance classes:

```text
processor_verified
merchant_verified
marketplace_verified
manual_observation
synthetic_test
```

Manual observations can support a commercial decision but may not masquerade as processor-verified.

- [ ] **Step 4: Prove three disagreement cases**

QC-006: payment succeeds, fulfillment fails → payment evidence true, offer-success verdict false.

QC-007: purchase then refund → gross survives historically; current net reflects refund.

QC-008: local cash-equivalent event → accepted only with explicit manual provenance and evidence ref.

- [ ] **Step 5: Commit**

```bash
git add schemas/commerce-event.schema.json scripts/quirk_commerce/evidence.py evals/quirk-commerce/cases/QC-006-stripe-payment-unfulfilled.json evals/quirk-commerce/cases/QC-007-refund-net-revenue.json evals/quirk-commerce/cases/QC-008-local-manual-evidence.json
git commit -m "feat(commerce): normalize economic evidence and revenue receipts"
```

---

### Task 5: Full Adversarial Evaluation Suite and Decision Engine

**Files:**
- Create: `scripts/quirk_commerce/decisions.py`
- Create: `evals/quirk-commerce/fixtures.json`
- Create: `evals/quirk-commerce/cases/QC-009-rights-block.json`
- Create: `evals/quirk-commerce/cases/QC-010-projection-drift.json`
- Create: `evals/quirk-commerce/cases/QC-011-marketplace-delist.json`
- Create: `evals/quirk-commerce/cases/QC-012-patreon-churn.json`
- Create: `evals/quirk-commerce/cases/QC-013-crowdfunding-cancel.json`
- Create: `evals/quirk-commerce/cases/QC-014-marketing-ctr-conversion-disagreement.json`
- Create: `evals/quirk-commerce/cases/QC-015-cross-domain-overreach.json`
- Modify: `scripts/validate_quirk_commerce.py`

**Interfaces:**
- Consumes: experiment evidence summary.
- Produces: `decide(summary: dict) -> Literal['EXPAND','REVISE','RETEST','RETIRE','INSUFFICIENT_EVIDENCE']`.

- [ ] **Step 1: Encode all 15 adversarial cases from the design/review**

The fixture registry must contain exactly QC-001 through QC-015, each with expected action and expected finding codes.

- [ ] **Step 2: Implement conservative decision rules**

```python
def decide(summary: dict) -> str:
    if summary.get("rights_blocked"):
        return "RETIRE"
    if summary.get("authority_violation"):
        return "RETIRE"
    if summary.get("evidence_count", 0) == 0:
        return "INSUFFICIENT_EVIDENCE"
    if summary.get("refund_rate", 0) > summary.get("refund_stop_threshold", 1):
        return "REVISE"
    if summary.get("conversion_evidence") is False:
        return "RETEST"
    if summary.get("success_condition_met") is True and summary.get("failure_condition_met") is False:
        return "EXPAND"
    return "INSUFFICIENT_EVIDENCE"
```

Do not encode domain-general financial predictions. The decision is experiment-local.

- [ ] **Step 3: Generate deterministic conformance output**

`validate_quirk_commerce.py` writes `evals/quirk-commerce/conformance-results.json` with sorted-key canonical hash, `automatic_activation:false`, and admission decision `ELIGIBLE_FOR_HUMAN_ADMISSION` only when every contract/eval passes.

- [ ] **Step 4: Run the full suite**

Run:

```bash
python scripts/validate_quirk_commerce.py --require-admit
```

Expected: exit 0 and `fixture_count_15=true`, `all_fixtures_pass=true`, `automatic_activation=false`.

- [ ] **Step 5: Commit**

```bash
git add scripts/quirk_commerce/decisions.py scripts/validate_quirk_commerce.py evals/quirk-commerce
git commit -m "test(commerce): add adversarial admission suite"
```

---

### Task 6: Supabase Runtime Projection and RLS

**Files:**
- Create: `supabase/migrations/20260821xxxxxx_quirk_commerce_contracts.sql`
- Create: `supabase/migrations/20260821xxxxxx_quirk_commerce_security.sql`
- Create: `scripts/quirk_commerce/projections.py`
- Modify: `scripts/validate_quirk_commerce.py`

**Interfaces:**
- Consumes: canonical objects validated by Tasks 1-5.
- Produces: runtime rows in `quirk_commerce.*` and canonical/runtime round-trip mappers.

- [ ] **Step 1: Create the runtime schema without duplicating core objects**

The contracts migration must create:

```sql
create schema if not exists quirk_commerce;

create table quirk_commerce.money_paths (...);
create table quirk_commerce.offer_candidates (...);
create table quirk_commerce.experiment_extensions (
  id uuid primary key default gen_random_uuid(),
  quirk_experiment_id uuid not null unique references public.quirk_experiments(id) on delete restrict,
  offer_candidate_id uuid not null references quirk_commerce.offer_candidates(id) on delete restrict,
  ...
);
create table quirk_commerce.adapter_bindings (...);
create table quirk_commerce.commercial_events (...);
create table quirk_commerce.revenue_receipts (...);
create table quirk_commerce.channel_evidence (...);
```

There MUST NOT be a second canonical experiment table or independent authority ledger.

- [ ] **Step 2: Add append-only economic evidence guards**

`commercial_events` and `revenue_receipts` must reject update/delete and use compensating/superseding records for corrections.

- [ ] **Step 3: Add lifecycle guard trigger**

A transition into `APPROVED_TO_TEST`, `APPROVED_TO_SELL`, or `LIVE` must require non-empty canonical grant/evidence refs. The database guard validates presence/shape only; runtime authority freshness/scope remains evaluated by the authority module so SQL does not pretend to own grant truth.

- [ ] **Step 4: Add fail-closed RLS/security migration**

Enable RLS on every table. Revoke browser roles by default following existing sync-control-plane security posture. Do not add permissive authenticated policies until an explicit access policy is admitted.

- [ ] **Step 5: Implement canonical/runtime mappers**

Public mapper signatures:

```python
def money_path_canonical_to_runtime(obj: dict) -> dict: ...
def money_path_runtime_to_canonical(row: dict) -> dict: ...
def offer_canonical_to_runtime(obj: dict) -> dict: ...
def offer_runtime_to_canonical(row: dict) -> dict: ...
def revenue_receipt_canonical_to_runtime(obj: dict) -> dict: ...
def revenue_receipt_runtime_to_canonical(row: dict) -> dict: ...
```

- [ ] **Step 6: Add static migration checks and mapper round-trip checks**

Require tokens proving schema creation, experiment FK, append-only evidence, RLS enabled, browser-role revoke, lifecycle guard, and no `commercial_authority_receipts` canonical table.

- [ ] **Step 7: Apply migrations only to a development branch/project during execution**

Before any live Supabase mutation, executor must use the connected Supabase project, create or select a development branch when available, and preserve the Human Gate for production. After migration, run security and performance advisors.

- [ ] **Step 8: Commit**

```bash
git add supabase/migrations/20260821*_quirk_commerce_*.sql scripts/quirk_commerce/projections.py scripts/validate_quirk_commerce.py
git commit -m "feat(commerce): add governed Supabase projection"
```

---

### Task 7: Operator Projection Contracts

**Files:**
- Create: `mappings/commerce/airtable-projection.json`
- Create: `mappings/commerce/notion-projection.json`
- Create: `mappings/commerce/google-drive-projection.json`
- Create: `mappings/commerce/cloudflare-projection.json`
- Create: `docs/commerce/OPERATOR-PROJECTIONS.md`
- Modify: `scripts/quirk_commerce/projections.py`

**Interfaces:**
- Consumes: runtime/canonical commercial objects.
- Produces: projection envelopes only; no projection may mutate canonical state.

- [ ] **Step 1: Define a shared projection envelope**

Each mapping must declare:

```json
{
  "surface": "airtable|notion|google_drive|cloudflare",
  "direction": "projection_only",
  "canonical_source": "github+supabase",
  "writable_fields": [],
  "proposal_fields": [],
  "authority": "none",
  "drift_behavior": "surface_discrepancy_and_block_promotion"
}
```

- [ ] **Step 2: Assign surface responsibilities**

Airtable: candidate ranking, price/channel experiments, triage.

Notion: offer brief, experiment brief, launch dossier, market autopsy, decision memo.

Google Drive: bulky evidence and working artifacts.

Cloudflare: later bounded public experiment delivery; no authority ownership and no canonical state.

- [ ] **Step 3: Implement projection generation**

```python
def build_projection(surface: str, canonical: dict, mapping: dict) -> dict:
    if mapping["direction"] != "projection_only":
        raise ValueError("commerce operator surfaces are projection-only in v0.1")
    return {
        "surface": surface,
        "canonical_ref": canonical["id"],
        "canonical_status": canonical["status"],
        "payload": {key: canonical.get(key) for key in mapping.get("project_fields", [])},
    }
```

- [ ] **Step 4: Add drift test**

A fixture with Airtable/Notion `LIVE` and canonical `CANDIDATE` must keep canonical `CANDIDATE`, report drift, and block promotion.

- [ ] **Step 5: Do not mutate connected operator systems yet**

Execution may create projections only after Tasks 1-6 pass and the user separately authorizes external writes. Airtable selection must be explicit because multiple relevant Quirk bases exist.

- [ ] **Step 6: Commit**

```bash
git add mappings/commerce docs/commerce/OPERATOR-PROJECTIONS.md scripts/quirk_commerce/projections.py
git commit -m "feat(commerce): define bounded operator projections"
```

---

### Task 8: Weird Money Proof 001 — Synthetic Contract Proof

**Files:**
- Create: `examples/quirk-commerce/weird-money-001/asset.json`
- Create: `examples/quirk-commerce/weird-money-001/money-path.json`
- Create: `examples/quirk-commerce/weird-money-001/offer-candidate.json`
- Create: `examples/quirk-commerce/weird-money-001/experiment-extension.json`
- Create: `examples/quirk-commerce/weird-money-001/adapter-operation.json`
- Create: `examples/quirk-commerce/weird-money-001/commerce-event.json`
- Create: `examples/quirk-commerce/weird-money-001/revenue-receipt.json`
- Create: `examples/quirk-commerce/weird-money-001/decision.json`
- Create: `examples/quirk-commerce/weird-money-001/README.md`
- Create: `docs/commerce/PROOF-001.md`

**Interfaces:**
- Consumes: all prior contracts.
- Produces: one deterministic end-to-end proof that the machinery works without external side effects.

- [ ] **Step 1: Use one source fragment from “69 Ways I Print Weird Money”**

Choose a low-rights-risk digital offer candidate, such as the unfinished-drafts-vault concept, and record its source as a Quirk asset fixture. The fixture must not claim real customer demand.

- [ ] **Step 2: Generate exactly three `MoneyPath` fixtures and select one explicitly**

The selection event must be represented as human evidence in the fixture, not inferred from model preference.

- [ ] **Step 3: Build one offer + experiment**

Use one Distribution hypothesis, one Marketing thesis, manual Merchant projection, and manual Commerce evidence adapter. Set explicit budget/time/stop ceilings.

- [ ] **Step 4: Run a synthetic no-side-effect event**

The event provenance must be `synthetic_test`. It proves normalization and receipt generation only; it cannot satisfy real demand evidence.

- [ ] **Step 5: Produce a decision of `INSUFFICIENT_EVIDENCE`**

This is the correct outcome for a synthetic plumbing test and proves the system refuses evidence laundering.

- [ ] **Step 6: Validate every fixture through the canonical schemas**

Run:

```bash
python scripts/validate_quirk_commerce.py --require-admit
```

Expected: contract suite passes while Proof 001 explicitly remains non-market evidence.

- [ ] **Step 7: Commit**

```bash
git add examples/quirk-commerce/weird-money-001 docs/commerce/PROOF-001.md
git commit -m "test(commerce): add Weird Money proof 001 contract wedge"
```

---

### Task 9: Stripe Evidence Adapter — No Autonomous Money Movement

**Files:**
- Create: `scripts/quirk_commerce/stripe_events.py`
- Create: `evals/quirk-commerce/valid/stripe-checkout-completed.json`
- Create: `evals/quirk-commerce/valid/stripe-refund.json`
- Create: `evals/quirk-commerce/cases/QC-016-stripe-unverified-webhook.json`
- Modify: `adapters/commerce/stripe/manifest.json`
- Modify: `scripts/validate_quirk_commerce.py`

**Interfaces:**
- Consumes: verified Stripe webhook payload projection supplied by a boundary that has already verified the signature.
- Produces: normalized `commerce-event` records; no checkout creation or autonomous capture in v0.1.

- [ ] **Step 1: Add explicit webhook trust input**

```python
def normalize_stripe_event(payload: dict, *, signature_verified: bool) -> dict:
    if not signature_verified:
        raise ValueError("unverified Stripe webhook")
    # map only fields needed by commerce-event schema
```

- [ ] **Step 2: Map checkout completion and refund without storing raw customer/payment data**

Persist Stripe event ID, amount/currency, status dimensions, opaque customer ref when necessary, timestamps, and provenance. Do not persist card data, client secrets, webhook secrets, or full raw customer objects.

- [ ] **Step 3: Add unverified-webhook adversarial case**

Expected: normalization fails before evidence creation.

- [ ] **Step 4: Run full conformance**

Expected: all prior tests plus Stripe normalization tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/quirk_commerce/stripe_events.py adapters/commerce/stripe/manifest.json evals/quirk-commerce/valid evals/quirk-commerce/cases/QC-016-stripe-unverified-webhook.json scripts/validate_quirk_commerce.py
git commit -m "feat(commerce): add Stripe evidence normalization adapter"
```

---

### Task 10: CI, Documentation, and Admission Evidence

**Files:**
- Create: `.github/workflows/quirk-commerce-conformance.yml`
- Create: `docs/commerce/README.md`
- Create: `docs/commerce/ADMISSION.md`
- Create: `docs/commerce/ADAPTERS.md`
- Modify: `README.md` only to link the candidate domain pack; do not label it Golden/Live.

**Interfaces:**
- Consumes: validator + conformance fixtures.
- Produces: reproducible candidate-admission evidence.

- [ ] **Step 1: Add CI workflow**

Use the repository’s existing Python validator approach. Workflow must run `python scripts/validate_quirk_commerce.py --require-admit` and upload or preserve `evals/quirk-commerce/conformance-results.json` as evidence where repository conventions permit.

- [ ] **Step 2: Document runtime boundaries and adapter semantics**

`docs/commerce/ADAPTERS.md` must explicitly state that Shopify, WooCommerce, Medusa, Gumroad, Patreon, crowdfunding systems, local commerce, social commerce, marketplaces, Lemon Squeezy, Stripe, and future systems are adapter families behind Quirk-owned contracts—not ontology owners and not automatically implemented.

- [ ] **Step 3: Document admission criteria**

Admission requires:

```text
schemas valid
eval fixtures pass
no automatic activation
RLS/security proof
append-only revenue evidence
experiment linkage proof
authority non-duplication proof
adapter side-effect scope proof
synthetic proof 001 result = INSUFFICIENT_EVIDENCE
independent human review
```

- [ ] **Step 4: Run validator twice and prove deterministic output hash**

Run:

```bash
python scripts/validate_quirk_commerce.py --require-admit
cp evals/quirk-commerce/conformance-results.json /tmp/qc-first.json
python scripts/validate_quirk_commerce.py --require-admit
diff -u /tmp/qc-first.json evals/quirk-commerce/conformance-results.json
```

Expected: no diff.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/quirk-commerce-conformance.yml docs/commerce README.md evals/quirk-commerce/conformance-results.json
git commit -m "ci(commerce): add deterministic admission evidence"
```

---

### Task 11: Live Weird Money Proof 002 — Human-Gated Market Test

**Files:**
- Create after explicit approval: `examples/quirk-commerce/weird-money-002/` evidence pack
- Create after test: `docs/commerce/PROOF-002.md`

**Interfaces:**
- Consumes: admitted candidate contracts plus an explicit human grant for the exact market test.
- Produces: real-world channel evidence, economic/no-economic evidence, RevenueReceipt where applicable, and a bounded commercial decision.

- [ ] **Step 1: Stop before external action and present the proposed grant**

The executor must show exact:

```text
offer
audience
distribution channel
marketing claim
merchant surface
commerce adapter
publication scope
budget ceiling
time ceiling
stop conditions
rights/privacy checks
requested adapter operations
```

No external write, publish, outreach, checkout activation, or money movement occurs without explicit approval.

- [ ] **Step 2: Execute only the approved scope**

Any changed price, channel, budget, message claim, audience, vendor, or requested side-effect class requires a new/updated grant.

- [ ] **Step 3: Capture receipts and contradictory evidence**

Record clicks/signups/purchases/refunds/churn/fulfillment separately. Do not collapse them into a single success metric.

- [ ] **Step 4: Produce the decision memo**

Return exactly one of `EXPAND`, `REVISE`, `RETEST`, `RETIRE`, or `INSUFFICIENT_EVIDENCE`, with evidence refs and confidence. Expansion is a proposal, never automatic authority for a larger test.

- [ ] **Step 5: Human admission review**

The user decides whether any evidence updates commercial preference edges, capability confidence, adapter status, or offer lifecycle state.

- [ ] **Step 6: Commit the evidence pack after redacting secrets/PII**

```bash
git add examples/quirk-commerce/weird-money-002 docs/commerce/PROOF-002.md
git commit -m "evidence(commerce): record Weird Money proof 002"
```

---

## Plan Self-Review

### Spec coverage

- Domain boundary and four commercial layers: Tasks 1, 3, 7, 8.
- MoneyPath / OfferCandidate / CommercialExperiment / RevenueReceipt: Tasks 1, 4, 6.
- Lifecycle + human gates: Tasks 1, 2, 6, 11.
- Vendor-neutral adapters: Tasks 3, 9, 10.
- Supabase runtime projection and RLS: Task 6.
- Airtable / Notion / Drive / Cloudflare boundaries: Task 7.
- Adversarial evaluation suite: Task 5 plus QC-016 in Task 9.
- Cheapest proof: Task 8 synthetic contract proof, Task 11 real-world human-gated proof.
- Distribution / Marketing / Merchant / Commerce: represented in object contracts, adapter operations, proof fixtures, and operator projections without vendor schema leakage.
- Privacy/data minimization: Global Constraints, Tasks 4, 9, 11.

### Placeholder scan

The timestamp component in migration filenames is intentionally resolved at execution time to the next available Supabase migration timestamp; it is not a behavioral TBD. No product requirement, interface, test expectation, or authority rule is left unspecified.

### Type consistency

All commercial objects use opaque Quirk references in canonical schemas, UUID foreign keys only in runtime projection, integer minor units for money, `OFFER_EVIDENCED` as the lifecycle state, and canonical grant/receipt references for authority.

## Execution Gate

Implementation begins in an isolated worktree/branch. Tasks 1-10 create candidate software and deterministic proof without external commercial side effects. Task 11 is a separate human-gated live experiment and cannot be reached by momentum from Tasks 1-10.
