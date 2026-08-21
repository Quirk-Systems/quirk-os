# Quirk Beauty Domain Pack v0.1

**Status:** domain boundary human-admitted; repository merge pending; implementation candidate  
**Canonical ID:** `quirk.products.beauty`  
**First proving wedge:** Taste Engine  
**Required proof:** `choice → preference evidence → recommendation → real-world outcome → human-confirmed graph update`

## The useful truth

This pack does **not** canonize a beauty platform, product roadmap, GPT family, scoring formula, database, interface, model, or commercial offer.

It canonizes exactly one semantic object: **the Quirk Beauty domain boundary**. The YAML and its bound sorted-JSON payload are two encodings of that same boundary, not two separately admitted systems.

Everything under `domains/beauty/`, the Supabase migration, provider adapters, product-design material, and sales material remains candidate until it passes its own evidence, review, and admission gates.

## Domain boundary

Quirk Beauty owns the beauty-specific semantics and experiences required to observe, model, test, explain, and apply taste to the curation and production of beautiful things.

It delegates generic identity, authorization, Human Gate enforcement, immutable evidence receipts, Preference Graph infrastructure, canonical doctrine, model execution, publishing, transactions, and cross-domain orchestration to Quirk core systems.

Canonical source:

```text
docs/canon/QUIRK-BEAUTY-DOMAIN-BOUNDARY.yaml
docs/canon/QUIRK-BEAUTY-DOMAIN-BOUNDARY.payload.json
```

## v0.1 wedge

The Taste Engine candidate proves one bounded sequence:

1. A human makes an explicit choice between beauty options in a declared context.
2. The system derives candidate preference evidence from that choice.
3. The system ranks a candidate recommendation and explains the evidence used.
4. The human tests the recommendation in the real world and explicitly records the outcome.
5. The system proposes—but does not apply—a Preference Graph update.
6. The human approves, revises, or rejects the update through Quirk core.
7. Only a live, human-confirmed approval may be applied by core, leaving a receipt that Beauty may mirror.

A click, purchase, dwell time, repeat visit, or lack of complaint is **not** satisfaction evidence.

## Canon ceiling

| Area | Status |
|---|---|
| Domain purpose, ownership, delegation, exclusions, invariants, and required proof | **HUMAN-ADMITTED BOUNDARY** |
| Repository projection of the boundary | Pending draft-PR review and merge |
| Taste objects and schemas | Candidate |
| Scoring and recommendation algorithm | Candidate |
| Product-design flow | Candidate |
| Supabase projection | Candidate; not applied |
| OpenAI explanation adapter | Candidate, deferred |
| Hugging Face evaluation packaging | Candidate, deferred |
| Sales pilot and offer | Candidate |
| Real-world proof | Required and unfulfilled |

## Local verification

Run from `domains/beauty/`:

```bash
npm test
npm run validate
npm run proof:synthetic
```

`proof:synthetic` proves only that the candidate machinery can execute. It cannot satisfy the admission proof because the outcome must be real and the graph update must be human-confirmed.

To verify a real proof artifact:

```bash
npm run proof:verify -- proof/evidence/real-proof.json
```

The candidate database contract lives at repository root:

```text
supabase/migrations/20260821090000_quirk_beauty_taste_engine_candidate.sql
supabase/tests/quirk_beauty_taste_engine_rls.sql
```

The SQL proof must run on an isolated Supabase development branch before any runtime admission decision.

## Repository placement

```text
quirk-os/
├── docs/canon/
│   ├── QUIRK-BEAUTY-DOMAIN-BOUNDARY.yaml
│   └── QUIRK-BEAUTY-DOMAIN-BOUNDARY.payload.json
├── decisions/ADR-0002-quirk-beauty-domain-boundary.md
├── domains/beauty/                         # candidate pack and kernel
├── supabase/migrations/20260821090000_quirk_beauty_taste_engine_candidate.sql
└── supabase/tests/quirk_beauty_taste_engine_rls.sql
```

The stable identifier remains `quirk.products.beauty` even if repository folders are later reorganized.

## Non-goals for v0.1

- medical or dermatological diagnosis;
- face, race, ethnicity, health, or sensitive-attribute inference;
- autonomous publishing, messaging, purchasing, or graph mutation;
- affiliate ranking, sponsored placement, storefronts, or commerce;
- image analysis, virtual try-on, fine-tuning, or public dataset publication;
- generalized beauty truth claims;
- claiming recommendation lift from one proof run.

## Proof-complete condition

`v0.1` may be called **proof-complete** only when `proof/evidence/real-proof.json` passes the verifier and the evidence set contains all five chain transitions with a valid human decision and effect receipt. Proof completion still does not admit the runtime.
