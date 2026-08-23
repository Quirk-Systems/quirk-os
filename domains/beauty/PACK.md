# Quirk Beauty Domain Pack v0.1.1

**Canonical ID:** `quirk.products.beauty`  
**Repository target:** `Quirk-Systems/quirk-os`  
**Canonical path:** `canon/domains/beauty/domain-boundary.yaml`  
**Candidate path:** `domains/beauty/`  
**Repository placement:** namespaced; no root README, security, changelog, or verification takeover  
**Required proof:** `choice → preference evidence → recommendation → real-world outcome → human-confirmed graph update`

## Truth status

This patch supersedes the incomplete local `v0.1` bundle. The earlier bundle contained eight files but referenced absent modules, tests, schemas, CI, provider adapters, and verification scripts. Its reported test and manifest results were therefore not reproducible from the mounted artifact.

`v0.1.1` preserves the human-approved domain semantics while correcting the execution surface:

- the boundary is **human-approved for canonical admission** but becomes Git-canonical only when merged through the repository gate;
- everything under `domains/beauty/` is candidate-only;
- synthetic proof validates machinery but cannot satisfy real-world proof;
- no provider integration grants runtime, publication, transaction, or graph-mutation authority.

## Boundary

Quirk Beauty owns beauty-specific taste semantics and experiences needed to observe, model, test, explain, and apply taste to the curation and production of beautiful things.

It delegates identity, authorization, Human Gate enforcement, immutable receipts, generic Preference Graph infrastructure, canonical doctrine, secrets, model execution, publication, transactions, and cross-domain orchestration to Quirk core systems.

## Verify

```bash
cd domains/beauty
npm run ci
npm run proof:verify -- proof/evidence/real-proof.json --trust-registry proof/evidence/trusted-core-keys.json
```

The second command must fail until one consenting human completes a real-world trial and confirms the graph update.

## Provider posture

| Surface | State | Authority ceiling |
|---|---|---|
| GitHub | intended authoritative review plane | branch/PR only; no merge implied |
| Supabase | candidate private projection | no canon, no direct graph mutation |
| Airtable | candidate operational projection | whitelisted fields only |
| Cloudflare | candidate request boundary | no deployment or secrets in Git |
| OpenAI | candidate explanation renderer | no ranking, outcome inference, or effects |
| Hugging Face | deferred evaluation packaging | no upload or participant data |
