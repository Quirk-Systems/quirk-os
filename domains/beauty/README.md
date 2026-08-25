# Quirk Beauty Domain Pack v0.1.1 — Repo-Native Successor

**Status:** candidate implementation beneath a separately reviewable, human-admitted domain boundary.

This successor preserves one proof spine:

```text
explicit choice
→ candidate preference evidence
→ explained recommendation
→ explicit real-world outcome
→ human-reviewed graph-update proposal
→ approve / revise / reject
→ Quirk-core application
→ evidence receipt
```

## Authority ceiling

Repository presence, passing tests, provider capability, or a favorable evidence review does not activate runtime authority, apply a database migration, publish, transact, deploy, or promote candidate semantics into canon.

The canonical boundary lives outside this directory at `docs/canon/QUIRK-BEAUTY-DOMAIN-BOUNDARY.yaml`. The candidate implementation cannot rewrite it.

## v0.1.1 successor hardening

- preserves the held transport bundle as source lineage rather than importing orphan commits;
- uses the existing repo-native v0.1 Taste Engine candidate as an integration substrate only;
- repairs the Cloudflare authority boundary so `allowed: true` without a non-empty authority receipt fails closed;
- binds GitHub review and Node 22/24 execution to the repository-native PR head;
- keeps Supabase migration, Cloudflare Worker, OpenAI adapter, and other provider projections candidate and undeployed.

See `SOURCE_LINEAGE.md` for the exact held source head, tree, bundle digest, and disposition.
