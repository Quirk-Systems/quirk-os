# GitHub Integration

## Repository topology

```text
quirk-os/
├── docs/canon/
│   ├── QUIRK-BEAUTY-DOMAIN-BOUNDARY.yaml
│   └── QUIRK-BEAUTY-DOMAIN-BOUNDARY.payload.json
├── decisions/ADR-0002-quirk-beauty-domain-boundary.md
├── domains/beauty/
│   ├── candidate/
│   ├── schemas/
│   ├── src/
│   ├── tests/
│   ├── proof/
│   ├── product-design/
│   ├── sales/
│   ├── supabase/
│   ├── openai/
│   └── huggingface/
├── supabase/migrations/20260821090000_quirk_beauty_taste_engine_candidate.sql
└── supabase/tests/quirk_beauty_taste_engine_rls.sql
```

## Two-review rule

Publication uses stacked draft pull requests so the two decisions cannot blur together:

1. `agent/beauty-domain-boundary-v0-1` → `main`
   - admitted boundary encodings;
   - canon index;
   - admission decision record;
   - no runtime or provider implementation.
2. `agent/beauty-taste-engine-v0-1` → boundary branch
   - candidate domain pack;
   - deterministic kernel and tests;
   - candidate Supabase migration and transactional proof;
   - CI and ownership rules.

Approval or merge of the first does not approve or activate the second. Candidate merge is preservation without promotion.

## Required pull-request evidence

- exact base commit and parent branch;
- authority ceiling;
- changed paths;
- Node 22 and 24 check results;
- pack validation output;
- synthetic proof output labeled inadmissible;
- negative proof-verifier result;
- isolated Supabase branch migration and RLS output when available;
- explicit protected actions not authorized;
- remaining human decision.

## Forbidden inference

A green check does not imply canon admission, runtime authorization, deployment approval, model-provider approval, Supabase production approval, or completion of the real-world proof.
