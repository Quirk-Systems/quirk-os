# Release Criteria

## Canonical boundary gate

- [x] Stable domain ID and purpose.
- [x] Owns, delegates, exclusions, and invariants declared.
- [x] Human approval limited to the boundary.
- [x] Repository admission remains separate from human approval.
- [ ] Canon diff independently reviewed at an exact commit SHA.
- [ ] Boundary merged through the authoritative `quirk-os` gate.

## Candidate implementation gate

- [x] Dependency-free Node package.
- [x] Deterministic Taste Engine.
- [x] Strict schemas and adversarial fixtures.
- [x] Synthetic proof runner and real-proof verifier.
- [x] Supabase, Airtable, Cloudflare, and OpenAI authority ceilings.
- [x] CI and PR template.
- [ ] Target-repository CI passes on Node 22 and Node 24.
- [ ] Supabase migration passes isolated two-user and anonymous tests.
- [ ] Connected Airtable projection passes field-authority tests.
- [ ] Cloudflare candidate passes local Worker tests; deployment remains separately gated.
- [ ] OpenAI explanation eval passes without unsupported evidence or authority language.

## Real proof gate

- [ ] Participant consent recorded.
- [ ] Real-world outcome explicitly reported.
- [ ] Graph update reviewed by the same authorized human.
- [ ] Approved or revised update applied through Quirk core.
- [ ] Immutable core receipt captured.
- [ ] `npm run proof:verify -- proof/evidence/real-proof.json --trust-registry proof/evidence/trusted-core-keys.json` passes.

## Runtime admission

A passing proof does not activate runtime. Bryan must issue a fresh, exact-scope runtime decision after reviewing the proof receipt.
