# GitHub Integration Receipt Plan

## Intended write

- Repository: `Quirk-Systems/quirk-os`
- Base: `main`
- Head: `candidate/quirk-beauty-domain-pack-v0.1.1`
- PR state: draft
- Merge: prohibited until separate exact-head review

## Commit separation

1. `canon(beauty): add human-approved domain boundary`
2. `feat(beauty): add candidate Taste Engine proof pack`
3. `ci(beauty): add isolated verification workflow`

Separating commits lets reviewers approve or reject the boundary independently from implementation machinery.

## Required receipts

Record branch creation, each commit SHA, final tree SHA, PR URL/number, exact head SHA, workflow run IDs, check conclusions, review disposition, and any superseding commit. A successful check never expands authority.
