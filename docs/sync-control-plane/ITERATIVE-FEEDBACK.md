# Iterative Feedback Contract

Feedback is evidence that may propose change. It is not automatic Canon.

## Feedback cycle

1. **Observe** — collect run receipt, test result, review comment, drift signal, or user correction.
2. **Classify** — bug, contract gap, preference, policy question, infrastructure risk, or opportunity.
3. **Attach evidence** — source refs, affected objects, confidence, and reproduction.
4. **Choose movement** — fix candidate, Proposed Move, issue, discussion RFC, boneyard, or no change.
5. **Implement reversibly** — candidate branch and migration first.
6. **Re-evaluate** — 11 fixtures, database proof, projection reconstruction, and CI.
7. **Admit or reject** — explicit human decision; preserve dissent and supersession.

## Feedback surfaces

- PR review: concrete candidate feedback.
- GitHub Issues: bounded repair or evidence work.
- GitHub Discussion/RFC: unresolved architecture with multiple viable positions.
- Supabase receipt: observed execution state.
- Drive/Notion/Airtable: human-readable projections only.

## Quality requirements

Every feedback item names outcome, evidence, confidence, risk, reversibility, proof, and next move. A successful fix must add or strengthen a regression fixture.
