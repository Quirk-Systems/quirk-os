# Golden Project Pack — Candidate Merge vs Golden Admission

Status: **governance contract**

This repository distinguishes **candidate existence** from **admission authority**.

A candidate object may be committed and merged so it can be inspected, tested, reviewed, superseded, or rejected. Repository presence does not make it canonical, active, current, chooseable, useable, live, deployed, or runtime-authorized.

## Two gates

### 1. Candidate merge gate

A `PROPOSED`, `CANDIDATE`, `DRAFT`, or `EXPERIMENTAL` pack may merge when:

- required artifacts exist and parse;
- schemas satisfy structural metadata requirements;
- the six Core laws and eleven Golden Prompt IDs are present;
- the Proposed Move queue is internally consistent;
- each move is structurally valid and dependencies resolve;
- historical tribunal evidence is internally consistent and references known moves;
- unresolved admission blockers remain visible in the queue and tribunal report;
- CI contains no unresolved placeholders or structural contradictions.

A green candidate merge gate means only: **safe to preserve and continue evaluating as a candidate**.

### 2. Golden admission gate

Any status that implies admission or operational availability—`GOLDEN`, `ADMITTED`, `LIVE`, `CURRENT`, `ACTIVE`, `CHOOSEABLE`, or `USEABLE`—fails closed while any `blocks_merge: true` Proposed Move remains unresolved.

A blocking move is resolved only by the validator's recognized terminal dispositions and must carry the required evidence and receipt. No CI change may silently manufacture those receipts.

## Historical evidence rule

Tribunal evidence is a historical observation, not a mutable projection of the current queue.

`tribunals/ship-without-bryan/pr-3/EVIDENCE.json` therefore remains bound to the head and blocker set it actually evaluated. The live Proposed Move queue may evolve after that snapshot. CI verifies historical evidence for internal consistency and known references; it does not rewrite history to make old evidence resemble current state.

This is a direct application of:

- **History is not authority.**
- **Storage is not consent.**
- **Comments are not commands.**
- **No Zombie Truth.**

## Authority ceiling for PR #3

PR #3 is `PROPOSED`. Merging it does not:

- promote the Golden Project Pack to Canon;
- activate Quirk Ledger or any capability;
- grant runtime or provider write authority;
- apply additional production migrations;
- approve Vercel, Cloudflare, Supabase, or Google Drive as authoritative surfaces;
- resolve the sixteen Ship It Without Bryan admission moves;
- create a Golden release receipt.

Those moves remain admission work until separately evidenced, adjudicated, and receipted.

## Why this distinction exists

Requiring every candidate to satisfy its final admission contract before it can exist in the repository creates an impossible governance cycle: the evidence, fixtures, review history, and supersession machinery needed to evaluate the candidate cannot themselves be safely preserved.

Candidate merge is therefore **preservation without promotion**. Golden admission remains a separate consequential transition with its own evidence and authority.
