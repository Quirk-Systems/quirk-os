# Candidate Quirk Beauty Taste Engine

Everything in this directory is candidate-only. It operationalizes one proof chain and cannot admit itself into canon or runtime.

## Commands

```bash
npm run validate
npm test
npm run proof:synthetic
npm run proof:verify -- proof/evidence/real-proof.json --trust-registry proof/evidence/trusted-core-keys.json
```

## Package surfaces

- `src/` — deterministic kernel and pure adapters;
- `schemas/` — strict exchange contracts;
- `fixtures/` — positive and release-killing cases;
- `supabase/` — private projection migration and RLS evidence plan;
- `airtable/` — whitelisted operational projection;
- `cloudflare/` — undeployed request-boundary candidate;
- `openai/` — explanation-only adapter and evals;
- `proof/` — synthetic evidence and real-world runbook.
