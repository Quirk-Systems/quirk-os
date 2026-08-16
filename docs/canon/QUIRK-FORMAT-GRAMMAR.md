# Quirk Format Grammar

**Status:** Candidate  
**Scope:** GitHub canonical-source templates for Quirk objects and operating packs.

## Required front matter

Every durable Quirk document starts by making these fields obvious:

```text
Title
Object ID
Object kind
Version
Status
Owner
Authority ceiling
Canonical source
Purpose
```

YAML-backed objects should use typed fields. Markdown-backed objects should render the same information above the fold.

## Canonical section order

1. Purpose
2. Non-goals
3. Owners, actors, and authority
4. Inputs
5. Outputs
6. Object grammar
7. Lifecycle
8. Interfaces
9. Data and provenance
10. Permissions and consent
11. Failure states
12. Evidence and evaluations
13. Migrations and compatibility
14. Examples
15. Decision log
16. Open findings and Proposed Moves

Sections may be marked not applicable, but consequential absence must be explicit.

## GitHub-flavored Markdown rules

- Use ATX headings.
- Keep exactly one H1.
- Use fenced code blocks with language identifiers.
- Use task lists only for actual admission or execution work.
- Use tables for comparisons and contracts, not long prose.
- Use Mermaid for inspectable architecture, never as the sole source of semantics.
- Link canonical paths with repository-relative links when possible.
- Do not embed secrets, private identifiers, access tokens, or sensitive personal data.
- Distinguish examples from executable Canon.
- Preserve rejected and superseded decisions through links and receipts.

## Semantic labels

Use these labels when they improve truth:

```text
CANON
EVIDENCE
INFERENCE
PROPOSAL
OPEN
REJECTED
SUPERSEDED
```

They describe epistemic or lifecycle state. They do not grant authority.

## Template law

> A template may standardize what must be considered. It may not fabricate answers, owners, dates, authority, evidence, or applicability.
