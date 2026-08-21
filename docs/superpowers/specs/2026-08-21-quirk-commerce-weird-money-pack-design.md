# Quirk Commerce — Weird Money Pack

**Status:** Candidate design — not canonical, not runtime-approved, not authorized for autonomous commercial execution.

**Date:** 2026-08-21

**Repository:** `Quirk-Systems/quirk-os`

## 1. Purpose

Quirk Commerce — Weird Money Pack is a candidate domain pack for turning unusual signals, capabilities, artifacts, performances, knowledge, experiments, and audience responses into inspectable commercial hypotheses and bounded market tests.

It is not a generic side-hustle generator, storefront product, payment wrapper, or vendor-specific commerce layer. Its purpose is to make commercialization legible, evidence-backed, reversible, and governed.

The pack must preserve the Quirk constitutional rule that capability never implies authority. A commercially plausible artifact is not approved to sell merely because a model can package it, a platform can publish it, or an audience appears interested.

## 2. Design principles

1. **Quirk owns the ontology; vendors are adapters.** Shopify, WooCommerce, Medusa, Gumroad, Patreon, crowdfunding platforms, local commerce, social commerce, marketplaces, Lemon Squeezy, Stripe, and future systems must sit behind Quirk-owned contracts.
2. **Distribution, Marketing, Merchant, and Commerce are distinct layers.** They cooperate but do not collapse into one object or vendor abstraction.
3. **Commercial evidence is provenance-bearing evidence.** Clicks, signups, purchases, refunds, repeat purchases, referrals, contributions, preorders, local transactions, marketplace orders, subscriptions, and qualitative rejection must retain source, context, time, and confidence.
4. **Projection is not authority.** Airtable, Notion, Google Drive, storefronts, marketplaces, and dashboards may project commercial state but may not independently canonize it.
5. **Human gates exist at consequential transitions.** Inferred satisfaction, stale approval, and adjacent-scope approval must never become execution authority.
6. **Proof before machinery.** The first release proves one complete commercialization path before building a generalized merchant platform.
7. **No Zombie Truth.** Vendor state and Quirk state may diverge; the discrepancy must be surfaced rather than silently reconciled.

## 3. Architectural placement

The pack lives inside `quirk-os` as a candidate domain pack and reuses existing Quirk assets, experiments, runs, pipelines, annotations, versions, diffs, receipts, Preference Graph structures, proposed-move mechanics, and evaluation infrastructure.

It does not create a separate top-level operating system. A future `quirk-commerce` service may become justified only when operational scale, deployment independence, or security boundaries require it.

### 3.1 Layer model

```text
Quirk Object / Signal Layer
        |
        v
Commercial Discovery
        |
        +--> Distribution
        +--> Marketing
        +--> Merchant
        +--> Commerce
        |
        v
Human Gate
        |
        v
Bounded Execution
        |
        v
Evidence + Revenue Receipts
        |
        +--> Preference Graph evidence
        +--> Capability evidence
        +--> Offer / channel / pricing evidence
        +--> Retire / revise / expand proposal
```

## 4. First-class commercial layers

### 4.1 Distribution

Distribution answers: **Where and how can this reach a plausible buyer or participant?**

Responsibilities:

- channel candidates;
- audience/channel fit;
- publishing surfaces;
- syndication plans;
- channel-specific constraints;
- channel cost and expected reach;
- attribution boundaries;
- local versus digital delivery;
- owned, earned, paid, partner, marketplace, and direct distribution distinctions.

Examples of adapters:

- owned web properties;
- email;
- social networks and social commerce;
- creator platforms;
- marketplaces;
- local events and in-person retail;
- affiliate and partner channels;
- Shopify storefronts;
- WooCommerce sites;
- Gumroad and Lemon Squeezy product pages;
- Patreon membership surfaces;
- crowdfunding campaign surfaces.

### 4.2 Marketing

Marketing answers: **What promise, framing, creative, audience, and evidence make the offer legible and desirable without laundering uncertainty?**

Responsibilities:

- positioning hypotheses;
- message variants;
- creative assets;
- audience segmentation;
- launch and campaign briefs;
- funnel hypotheses;
- attribution plans;
- channel-specific copy and creative transforms;
- evidence capture from tests;
- rejection and failure analysis.

Marketing may propose but cannot manufacture proof. A high-performing ad or landing page is evidence about message/channel response, not automatic evidence that the underlying product is durable or profitable.

### 4.3 Merchant

Merchant answers: **What sellable catalog, pricing, inventory, access, fulfillment, entitlement, tax, refund, and customer-service semantics are required to transact?**

Responsibilities:

- offer-to-SKU or offer-to-entitlement projection;
- catalog representation;
- price and pricing-option projection;
- inventory / availability representation;
- access and entitlement state;
- subscription / membership semantics;
- order lifecycle mapping;
- fulfillment requirements;
- refunds and cancellations;
- customer identity mapping;
- tax and compliance metadata boundaries;
- channel synchronization.

Merchant is the normalization boundary between Quirk offer semantics and vendor-specific catalog/order systems.

Primary adapter families:

- **Headless / programmable:** Medusa, custom merchant services;
- **Hosted commerce:** Shopify;
- **Site-native commerce:** WooCommerce;
- **Digital creator commerce:** Gumroad, Lemon Squeezy;
- **Membership:** Patreon and comparable systems;
- **Crowdfunding / preorder:** Kickstarter-like and campaign platforms;
- **Local commerce:** POS, in-person checkout, invoice, QR, event, retail, and service delivery;
- **Marketplace:** Etsy-like, app/plugin marketplaces, stock/media marketplaces, course marketplaces, and other vertical marketplaces.

### 4.4 Commerce

Commerce answers: **What economic event actually occurred, under what authority, and what evidence should survive?**

Responsibilities:

- checkout intent;
- payment state;
- subscription state;
- order state;
- refund state;
- contribution / pledge state;
- payout state;
- fee state;
- gross versus net revenue;
- tax / withholding metadata when available;
- attribution to offer/channel/experiment;
- evidence receipts.

Stripe and other payment processors belong primarily here as payment adapters. Shopify, WooCommerce, Medusa, Gumroad, Lemon Squeezy, Patreon, crowdfunding systems, social commerce, local systems, and marketplaces may span Merchant + Commerce because they combine catalog/order/payment or settlement concerns.

## 5. Candidate object model

The first release introduces only four new candidate commercial object types.

### 5.1 `MoneyPath`

A hypothesis describing how an existing Quirk object or capability may create economic value.

Required fields:

```text
id
source_object_ref
value_created
beneficiary
buyer_hypothesis
transformation
merchant_shape
commerce_model
pricing_hypothesis
distribution_hypotheses[]
marketing_hypotheses[]
proof_cost_ceiling
rights_constraints[]
authority_state
risk_profile
reversibility
status
provenance[]
```

### 5.2 `OfferCandidate`

A bounded candidate that could become purchasable, subscribable, pledgeable, bookable, commissionable, licensable, rentable, or otherwise economically exchangeable.

It must not assume a specific platform.

Required fields include:

```text
id
money_path_ref
offer_type
promise
buyer
included_value[]
excluded_value[]
price_model
fulfillment_model
access_model
rights_model
refund_model
channel_constraints[]
merchant_projection_state[]
authority_state
status
```

### 5.3 `CommercialExperiment`

A falsifiable and bounded test of one or more commercial hypotheses.

Required fields:

```text
id
offer_candidate_ref
hypothesis
experiment_type
target_audience
channel
marketing_variant_refs[]
merchant_adapter
commerce_adapter
budget_ceiling
time_ceiling
success_condition
failure_condition
stop_condition
rights_checks[]
required_grants[]
observability_plan
evidence_requirements[]
status
```

### 5.4 `RevenueReceipt`

An immutable evidence record for an economically meaningful event or bounded commercial outcome.

Examples include purchase, preorder, pledge, subscription start, subscription renewal, refund, cancellation, payout, local payment, marketplace sale, paid booking, paid commission, or explicit no-sale outcome after a controlled experiment.

Required fields:

```text
id
commercial_experiment_ref
offer_candidate_ref
event_type
gross_amount
fees
refund_amount
net_amount
currency
vendor
vendor_event_ref
customer_or_participant_ref
channel_ref
marketing_variant_ref
occurred_at
captured_at
provenance
confidence
authority_receipt_ref
```

## 6. Lifecycle

```text
OBSERVED
  -> CANDIDATE
  -> PROOF_DESIGNED
  -> APPROVED_TO_TEST
  -> TESTING
  -> EVIDENCED
  -> OFFER_CANDIDATE
  -> APPROVED_TO_SELL
  -> LIVE
  -> RETIRED
```

Transitions are evidence-backed and permission-aware.

Important constraints:

- `CANDIDATE -> PROOF_DESIGNED` may be automated as a proposal.
- `PROOF_DESIGNED -> APPROVED_TO_TEST` requires an explicit valid grant when the test has external side effects, spend, publication, outreach, checkout, or customer interaction.
- `EVIDENCED -> OFFER_CANDIDATE` may be suggested but not self-canonized.
- `OFFER_CANDIDATE -> APPROVED_TO_SELL` requires explicit approval.
- Vendor-side `active`, `published`, or `available` flags never override Quirk lifecycle state.

## 7. Adapter contracts

Adapters translate Quirk contracts into external systems and back. Each adapter declares capabilities instead of pretending all platforms are interchangeable.

### 7.1 Adapter capability dimensions

```text
catalog_write
catalog_read
pricing_write
inventory_write
checkout_create
payment_capture
subscriptions
memberships
pledges
preorders
refunds
fulfillment
entitlements
webhooks
orders_read
customers_read
payouts_read
fees_read
local_pos
marketplace_listing
social_listing
campaign_analytics
attribution
```

### 7.2 Capability examples

- Stripe: strong payment / subscription / refund / event adapter; not the canonical product catalog ontology.
- Shopify: merchant + commerce + distribution adapter.
- WooCommerce: merchant + commerce adapter tightly bound to site-owned distribution.
- Medusa: programmable merchant runtime and orchestration adapter.
- Gumroad / Lemon Squeezy: digital merchant + commerce + lightweight distribution adapters.
- Patreon: membership merchant + recurring commerce + creator distribution adapter.
- Crowdfunding platforms: campaign distribution + pledge/preorder commerce adapters.
- Social commerce: distribution + merchant projection + channel analytics adapter.
- Marketplaces: externally governed merchant catalog + commerce + discovery adapter.
- Local: merchant + commerce adapter family rather than one vendor; includes event, invoice, POS, booking, direct service, QR, cash-equivalent evidence, and manual receipt workflows.

## 8. Runtime projection

Supabase remains the preferred runtime projection.

The first schema extension should avoid duplicating `quirk_assets`, `quirk_experiments`, `quirk_runs`, or Preference Graph tables.

Candidate tables:

```text
commercial_money_paths
commercial_offer_candidates
commercial_experiments
commercial_adapter_bindings
commercial_events
commercial_revenue_receipts
commercial_authority_receipts
commercial_channel_evidence
```

All tables require RLS. External IDs must be namespaced by adapter/vendor and must never become primary Quirk identity.

## 9. Operator surfaces

### GitHub

Owns candidate contracts, schemas, lifecycle definitions, adapter interfaces, fixtures, evals, migrations, and evidence expectations.

### Supabase

Owns runtime projections and immutable / append-oriented event evidence where appropriate.

### Airtable

Acts as a commercial laboratory and triage surface for candidate ranking, market hypotheses, price tests, channel comparisons, and proof status. Airtable is not canonical commercial truth.

### Notion

Acts as human-readable briefing and decision surface for offer briefs, commercial experiment briefs, launch dossiers, market autopsies, and commercial decision memos.

### Google Drive

Stores bulky evidence and working artifacts: research, screenshots, customer interviews, ad/export data, campaign decks, creative masters, contracts, local receipts, and vendor exports.

### Cloudflare

Later-stage bounded execution layer for public experiments, Workers/API mediation, R2 asset delivery, redirects, short-lived landing pages, edge instrumentation, and security boundaries. It must not own Quirk authority state.

## 10. Distribution + Marketing + Merchant + Commerce flow

```text
Signal / Quirk Asset
   |
   v
MoneyPath
   |
   v
OfferCandidate
   |
   +--> Distribution Plan
   |       -> channels
   |       -> audiences
   |       -> owned / social / marketplace / local
   |
   +--> Marketing Plan
   |       -> promise
   |       -> creative
   |       -> variants
   |       -> attribution
   |
   +--> Merchant Projection
   |       -> catalog
   |       -> price
   |       -> entitlement / inventory
   |       -> vendor adapters
   |
   +--> Commerce Projection
           -> checkout / pledge / subscription / order
           -> payment / refund / payout
           -> revenue evidence

         [Human Gate]
              |
              v
       Bounded Execution
              |
              v
      RevenueReceipt + Evidence
```

## 11. Cheapest end-to-end proof

The v0.1 wedge must prove one strange fragment can become one market-tested commercial candidate without authority leakage.

1. Capture one fragment as a `quirk_asset`.
2. Propose no more than three `MoneyPath` candidates.
3. Human selects one.
4. Create one `OfferCandidate`.
5. Select one distribution channel and one marketing thesis.
6. Select one Merchant adapter and one Commerce adapter.
7. Create one `CommercialExperiment` with cost/time/stop ceilings.
8. Require explicit approval before external publication, spend, outreach, checkout activation, or transaction enablement.
9. Execute the test.
10. Capture vendor events and manually observable outcomes.
11. Produce one `RevenueReceipt` or explicit no-revenue evidence receipt.
12. Generate a commercial decision memo: `EXPAND`, `REVISE`, `RETEST`, `RETIRE`, or `INSUFFICIENT_EVIDENCE`.

## 12. Initial proof adapters

For v0.1, do not build every named integration.

Recommended first adapter set:

1. **Stripe** — payment / checkout / subscription event spine.
2. **One merchant surface** — Shopify, WooCommerce, Medusa, Gumroad, or Lemon Squeezy chosen by cheapest proof requirements.
3. **One distribution surface** — owned landing page or one social / marketplace channel.
4. **Manual adapter** — required for local, platform gaps, and evidence-preserving tests before automation exists.

All other systems begin in the adapter registry as capability declarations and research targets, not fake integrations.

## 13. Evaluation suite

Minimum adversarial cases:

1. Viral asset without rights clearance cannot become `APPROVED_TO_SELL`.
2. Inferred user satisfaction cannot become preference evidence or approval.
3. Approval for a $10 test cannot self-expand into a $1,000 campaign.
4. Landing-page traffic with zero purchases cannot be labeled validated demand.
5. One friend purchase remains weak, provenance-visible evidence.
6. Success in music cannot automatically imply demand for apparel.
7. Airtable or Notion says `LIVE` while canonical runtime says `CANDIDATE`; projection loses.
8. Shopify product becomes externally active after Quirk grant expiration; system surfaces drift and proposes containment.
9. Stripe payment succeeds but order fulfillment fails; payment success cannot equal successful offer outcome.
10. Marketplace delists a product; Quirk records external status without rewriting prior evidence.
11. Patreon subscriber churns after one cycle; first-payment evidence remains true while retention evidence changes.
12. Crowdfunding pledge is canceled before settlement; pledge and realized revenue remain distinct.
13. Local cash-equivalent transaction is manually recorded; it requires explicit provenance and cannot masquerade as processor-verified evidence.
14. Merchant adapter cannot support a requested entitlement model; the system must refuse lossy projection.
15. Marketing variant wins CTR but loses conversion; evidence must preserve the disagreement.

## 14. Failure states

- vendor lock-in leaks into canonical schemas;
- stale vendor state projected as current truth;
- payment event mistaken for fulfilled value;
- likes / clicks mistaken for commercial demand;
- generated copy creates unsupported product claims;
- external publication occurs without valid grant;
- refund / cancellation data omitted from revenue claims;
- fees ignored when computing net revenue;
- multiple vendor identities merged without evidence;
- manual local transaction lacks provenance;
- marketplace policy changes silently invalidate an offer;
- a connector gains more execution scope than its grant permits.

## 15. Non-goals for v0.1

Do not build yet:

- universal storefront builder;
- generalized CRM;
- autonomous pricing engine;
- autonomous ad buying;
- affiliate network;
- marketplace aggregator;
- tax engine;
- universal fulfillment orchestration;
- loyalty program;
- full attribution warehouse;
- vendor-specific mega-schema;
- AI-generated financial forecasts presented as evidence.

## 16. Definition of done for design admission

This candidate design is ready for implementation planning only when:

- object boundaries are accepted;
- Distribution / Marketing / Merchant / Commerce separation is accepted;
- Quirk-owned adapter contract is accepted;
- v0.1 proof adapter strategy is accepted;
- authority transitions are accepted;
- the Supabase projection boundary is accepted;
- adversarial cases are sufficient to begin contract tests;
- no unresolved section materially changes the first wedge.

## 17. Decision log

### 2026-08-21

**Decision:** Keep Weird Money as a candidate domain pack inside `quirk-os`, not a separate top-level OS.

**Decision:** Expand the domain boundary to explicitly include Distribution, Marketing, Merchant, and Commerce.

**Decision:** Treat Shopify, WooCommerce, Medusa, Gumroad, Patreon, crowdfunding systems, local commerce, social commerce, marketplaces, Lemon Squeezy, Stripe, and future platforms as adapters behind Quirk-owned contracts.

**Decision:** Preserve Supabase as runtime projection; Airtable, Notion, Google Drive, external merchant systems, and dashboards remain bounded collaboration / projection / execution surfaces.

**Decision:** Require evidence receipts and human approval at consequential test and sale transitions.
