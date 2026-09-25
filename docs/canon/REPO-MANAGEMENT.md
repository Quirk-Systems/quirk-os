# Quirk Repository Management Canon Candidate

## Repository as authority boundary

A repository owns versioned source only for the objects explicitly assigned to it. It does not become authoritative for live runtime state merely because code is stored there.

## Required repository files

```text
README.md
CONTRIBUTING.md or repository management contract
docs/canon/
schemas/
tests/
evals/
migrations/ or explicit no-database declaration
.github/workflows/
decision records
release criteria
```

## Branch policy

```text
main                         admitted repository state
agent/<bounded-change>       agent-authored candidate
human/<bounded-change>       human-authored candidate
release/<version>            controlled release preparation
```

Stacked PRs must name their parent branch and preserve independent check signals.

## Commit policy

A commit should express one meaningful contract or behavior change. Generated files and their source generator should land together.

## Pull-request policy

Every consequential PR states:

- intended outcome;
- authority ceiling;
- source and dependency branches;
- contracts changed;
- migrations;
- positive and adversarial tests;
- evidence;
- protected actions not authorized;
- remaining human decision.

Default to draft until the evidence package is coherent.

## Issue policy

Use issues for durable gaps and decisions. A useful issue contains outcome, evidence, authority, acceptance, blockers, and next proof.

## Release policy

A green build is evidence of execution, not automatic admission. Release requires explicit version, changelog, migrations, rollback or compensation, security and rights review, observability, and human authority.
