# Admission Checklist

**Status:** Candidate review checklist  
**Authority ceiling:** `propose`

## Candidate PR pass criteria

- [ ] All changed files are under `docs/product/chambered-workbench/`.
- [ ] PR is opened as draft.
- [ ] PR title and body state that this is documentation only.
- [ ] No runtime code is added.
- [ ] No schemas, validators, CI, package manifests, or workflows are added.
- [ ] No provider-resource access is requested or implied.
- [ ] No publication access is requested or implied.
- [ ] No canon promotion is claimed.
- [ ] No preference graph mutation is claimed.
- [ ] Four Chambers is treated as the initial chamber set, not a fixed ceiling.
- [ ] N-chamber expansion requires nomination, evidence, review, and separate approval.

## Product-design review checklist

- [ ] The active object remains centered.
- [ ] Evidence remains visible in every chamber.
- [ ] Authority remains visible in every chamber.
- [ ] The transition ledger remains visible in every chamber.
- [ ] Source and signal are distinct.
- [ ] Candidate and canon are distinct.
- [ ] Confidence and permission are distinct.
- [ ] Blocked transitions explain why they are blocked.
- [ ] Receipt schema is visible before consequential transition.
- [ ] Gallery preservation does not imply reuse or promotion.
- [ ] Future chambers cannot bypass the shell contract.

## Release-blocking fixture backlog

These are not implemented in this PR. They are required before runtime work.

- [ ] Candidate cannot self-promote to canon by entering Gallery.
- [ ] Confidence cannot produce or expand authority.
- [ ] Foundry cannot include excluded or reference-only inputs.
- [ ] Transition cannot execute without a receipt schema.
- [ ] Stale grant remains inspectable but unusable.
- [ ] Receipt cannot be silently altered after write.
- [ ] Outcome evidence can contradict the original evaluation.
- [ ] Preference Graph mutation remains blocked until human confirmation.
- [ ] Provider-resource access requires a separate grant kind.
- [ ] Publication access requires a separate grant kind.
- [ ] Gallery preservation cannot imply reuse permission.
- [ ] New chamber cannot duplicate an existing chamber under prettier words.
- [ ] New chamber cannot lower authority/evidence requirements.

## Human approval checklist for later phases

Before implementation planning:

- [ ] exact PR head reviewed;
- [ ] changed files reviewed;
- [ ] candidate scope accepted or revised;
- [ ] runtime exclusion still intact;
- [ ] follow-up implementation scope explicitly named.

Before runtime code:

- [ ] written implementation plan exists;
- [ ] package/module boundaries are approved;
- [ ] schemas and fixtures are approved;
- [ ] tests are named before code;
- [ ] rollback path exists.

Before canon promotion:

- [ ] exact-head decision receipt exists outside the candidate artifact;
- [ ] semantic review passed;
- [ ] authority-integrity fixtures passed;
- [ ] evidence/provenance review passed;
- [ ] migration and compatibility impact is understood;
- [ ] human approval names the exact object/version/scope admitted.
