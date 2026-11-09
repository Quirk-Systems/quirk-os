# Release Criteria

## Human-admitted boundary

- [x] Domain purpose defined.
- [x] Ownership and delegation separated.
- [x] Exclusions and invariants defined.
- [x] Only the boundary semantics are marked canonical.
- [x] Bound payload hash verified.
- [x] Required proof chain defined.

## Candidate pack structurally complete

- [x] Candidate object and capability registries.
- [x] Typed declarations and strict JSON schemas.
- [x] Deterministic kernel.
- [x] Positive and adversarial tests.
- [x] Product-design experience contract.
- [x] Hardened Supabase projection contract.
- [x] Executable transactional Supabase proof.
- [x] OpenAI adapter boundary.
- [x] Hugging Face evaluation boundary.
- [x] Sales proof-to-offer ladder.
- [x] Node 22/24 CI workflow and CODEOWNERS.
- [x] Observability, privacy, versioning, and migration rules.

## Repository evidence still required

- [ ] Boundary-only draft PR independently reviewed.
- [ ] Candidate stacked draft PR independently reviewed.
- [ ] Boundary branch merged by explicit human decision.
- [ ] Candidate preservation merge separately decided.
- [ ] GitHub Actions passes on Node 22 and Node 24 in the target repository.

## Runtime and proof evidence still required

- [ ] Supabase migration applied to an isolated development branch only.
- [ ] Transactional SQL proof passes and rolls back.
- [ ] Supabase security/performance advisors reviewed after migration.
- [ ] Temporary Supabase branch deleted with evidence.
- [ ] Candidate local receipt writer replaced with Quirk core receipt service.
- [ ] One consenting human completes the real-world proof.
- [ ] `npm run proof:verify -- proof/evidence/real-proof.json` passes.
- [ ] Bryan issues a fresh approve/revise/reject/supersede decision for runtime admission.

## Current verdict

**BOUNDARY HUMAN-ADMITTED; REPOSITORY MERGE PENDING; PACK CANDIDATE; DATABASE PROOF PENDING; REAL-WORLD PROOF BLOCKED.**
