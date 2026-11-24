# Verification and evidence limits

Updated: 2026-11-24. Candidate only; authority effect: none.

The active source for this remediation is repo-native PR #70 at
`db2726830a26df40c696c148726e57e43a616d5f`, descended from
`main@80f53905f793751aa47ed4093d5dd035cab608ff`.
PRs #45/#46 are historical; #68 retains the separate boundary review surface.
The transport bundle is not available in this checkout. Its recorded SHA and
mapping in `SOURCE_LINEAGE.md` remain historical provenance, not a fresh bundle
verification or byte-for-byte import claim.

## Reproduced defects

- The public `verifyRealProof()` API accepted the synthetic fixture after changing
  `synthetic` and `participantConsent`; the CLI already held admission. Both now
  deny real admission while core attestation is unintegrated.
- Pack validation required a stale Worker source string (`missing_authority_receipt`)
  although current behavior uses `invalid_authority_receipt`. Static configuration
  checks no longer claim behavior; executable Worker tests cover receipt denial.
- No scoped integrity manifest or CI integrity check existed in this successor.
  The generator now covers Beauty files and seven explicit repository dependencies,
  rejects symbolic links, and detects modified, added, or removed controlled files.
  Unrelated repository files do not enter that manifest.
- Two tests depended on the caller's working directory. They now resolve their
  inputs relative to the test module and also run from the repository root.

## Reproducible local checks

Run from `domains/beauty/` using Node 22 or 24:

```sh
npm run ci
npm run proof:verify -- proof/synthetic-example.json
```

The second command must exit 1 with `core_attestation_not_integrated`. A missing
file or command is not a successful negative admission test. `npm run ci` runs
contracts, pack validation, synthetic machinery, and `manifest:check`.
After an intentional controlled-file edit, review the diff and run `npm run manifest`.
The manifest proves consistency, not publisher identity or approval.

Exact subject SHAs, runtime versions, successful command records, and path digests
belong in the separate `.quirk/evidence/` receipt. Current PR head and hosted job
readbacks belong in the PR description; local execution is not hosted CI evidence.

## Remaining holds

- Detached Quirk-core signature and independently administered trust-policy integration.
- Complete proof-chain binding, actor-bound consent, removal of candidate graph-application
  and receipt-issuance APIs, and synthetic projection review requested on #67.
- Independent review: CodeRabbit requires authenticated access; no review is claimed.
- Hosted execution: retrieved jobs in `quirk-os` and `project-scaffold` have zero
  executed steps and `runner_id=0`. Root cause and recovery require owner/provider evidence.
- Cloudflare Workers-runtime execution, installed Wrangler schema validation, and live
  compatibility with the candidate core-receipt URI contract.
- Supabase migration/RLS execution, Airtable protection tests, real participant outcomes,
  provider effects, deployment, and runtime admission.

Passing local tests does not satisfy these holds or carry forward canon approval.
