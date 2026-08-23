# Real-World Proof Runbook

## Objective

Complete one honest Taste Engine sequence with one consenting human and one beauty decision that can actually be tested.

## Preconditions

- Use one declared purpose partition, such as `personal_beauty_recommendation`.
- Choose options the participant can meaningfully compare.
- Record only explicit attributes; do not infer sensitive characteristics.
- Ensure the recommended option can be tested in the real world.
- Do not use affiliate compensation, sponsorship, or purchase pressure in the proof.

## Run

### 1. Record the choice

Present at least two options. The participant selects one or explicitly abstains. Capture context, options, timestamp, and `sourceType: explicit_human_choice`.

An abstention is valid but cannot complete this proof because it yields no preference evidence.

### 2. Derive preference evidence

Run the deterministic candidate kernel. Inspect the contrasts. Remove any attribute that was not actually presented or observed.

### 3. Produce the recommendation

Rank at least two new candidate options. Show:

- recommended option;
- score and confidence;
- evidence IDs;
- strongest positive and negative factors;
- expiry;
- a visible statement that the result is a recommendation, not an action.

### 4. Test in reality

The participant uses or experiences the recommendation in the declared context. Do not treat purchase as use.

### 5. Record the outcome

The participant explicitly records `preferred`, `rejected`, or `mixed`, plus a brief note. The record must say it came from an explicit human report.

### 6. Review the graph update

Show the exact proposed feature deltas, evidence, purpose, expected graph revision, and expiry.

The participant chooses:

- **Approve** — apply the proposal as written.
- **Revise** — replace the proposed deltas with explicit corrections.
- **Reject** — apply nothing; preserve the rejection receipt outside the passing proof bundle.

### 7. Apply and receipt

Only an approved or revised decision may cross the Human Gate. Capture the before/after graph revision and immutable receipt.

### 8. Assemble and verify

Build `proof/evidence/real-proof.json`, calculate artifact digests, and run:

```bash
npm run proof:verify -- proof/evidence/real-proof.json --trust-registry proof/evidence/trusted-core-keys.json
```

A failing verifier is a failed proof, not a documentation inconvenience.

## Cryptographic receipt requirement

A core-looking string is not a core receipt. The real proof bundle must include a detached Ed25519 `coreAttestation` signed by `quirk.core.evidence`. Verification also requires an external trusted-key registry supplied at runtime. The domain pack does not mint, trust, or rotate those keys.

```bash
npm run proof:verify -- \
  proof/evidence/real-proof.json \
  --trust-registry proof/evidence/trusted-core-keys.json
```

The trusted registry must come from Quirk core's Git-canonical trust policy, not from the proof participant or provider projection.
