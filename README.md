# quirk-os

Quirk OS is the operating foundation for a stateful human–agent ecosystem spanning preference, memory, governance, capabilities, creation, evaluation, assets, and control.

## Active architecture work

### Quirk Core Golden Project Pack

The first project pack defines the accountable machinery beneath Quirk Core:

- Ledgers and receipts
- operational logs and observability
- eval-driven development
- Golden gates
- capabilities and agent skills
- Proposed Move Queues
- Google Drive collaboration boundaries
- Current Research and Top Minds registries
- Multimedia Multipliziert
- eleven Quirk Golden Prompts

Start here: [`docs/golden-project-pack/README.md`](docs/golden-project-pack/README.md)

## Core laws

- Every consequential mutation owes a receipt.
- History is not authority.
- Storage is not consent.
- Comments are not commands.
- No Zombie Truth.
- Every decision eventually owes an outcome.

## Repository status

This repository is early and intentionally contract-first. Canonical definitions, runtime enforcement, and database/search projections remain separate. A polished document is not a release; Golden status requires executable schemas, evals, gates, evidence, and a successful **Ship It Without Bryan** review.

### Merge-ready notifications

The Merge Ready Notifier checks open PRs every 30 minutes (subject to GitHub
scheduling delays), or on manual dispatch from the default branch. It posts one
advisory PR comment per head/base SHA pair only when the PR is open, non-draft,
GitHub reports clean mergeability and approved required reviews, review threads
are resolved, head checks succeed, and the latest Actions runs for each
workflow/event at that head succeed. Missing or unknown data, absent review
approval, pending checks, and approval-blocked runs suppress notifications.
Branches without required-review approval reporting are deliberately not notified.

The workflow must first be integrated into the default branch to operate; this
does not authorize that integration or a merge. It executes only trusted
default-branch code, never PR code, and uses the repository token without an
external notification service. Comments are point-in-time observations, not
merge, admission, activation, or deployment authority. Recheck before acting.
Run its focused tests with `python3 -m unittest tests.test_merge_ready_notifier -v`.
