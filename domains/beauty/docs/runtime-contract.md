# Candidate Runtime Contract

The runtime contract is expressed as commands and events rather than binding the domain to HTTP, MCP, a specific framework, or a language model.

## Commands

### `DeclareTastePurpose`

**Input:** actor, purpose, beauty context, consent receipt reference.  
**Output:** session.  
**Fails:** missing purpose, unsupported realm, absent consent.

### `RecordTasteChoice`

**Input:** session, presented options, selection or abstention.  
**Output:** append-only `TasteChoice`.  
**Fails:** option not presented, selection plus abstention, fewer than two options.

### `DerivePreferenceEvidence`

**Input:** explicit choice and visible option attributes.  
**Output:** zero or more candidate evidence records.  
**Fails:** hidden or absent contrast, cross-purpose input, non-explicit choice.

### `RankBeautyRecommendation`

**Input:** actor, purpose, candidates, scoped evidence, generation time.  
**Output:** ordered candidate recommendations with factors and expiry.  
**Fails:** malformed candidates. Insufficient evidence is a valid result, not an exception.

### `RecordRealWorldOutcome`

**Input:** recommendation, explicit report, tested flag, note, context.  
**Output:** append-only outcome.  
**Fails:** purchase/click/engagement source, wrong actor/purpose/option, fabricated real-world test.

### `ProposePreferenceGraphUpdate`

**Input:** current graph revision, recommendation, real-world outcome.  
**Output:** candidate proposal with `autoApply: false`.  
**Fails:** not tested, no supported features, stale or cross-scope lineage.

### `DecidePreferenceGraphUpdate`

**Owner:** Quirk core Human Gate.  
**Input:** exact proposal, actor, purpose, decision, corrections, expiry.  
**Output:** append-only decision.  
**Fails:** silence, inferred satisfaction, wrong scope, stale grant, revision without correction.

### `ApplyPreferenceGraphUpdate`

**Owner:** Quirk core effect broker.  
**Input:** graph, exact unexpired proposal, exact unexpired human decision.  
**Output:** new graph revision and effect receipt.  
**Fails:** reject, stale revision, wrong actor/purpose, replay, forged or expired decision.

## Failure codes

| Code | Meaning |
|---|---|
| `choice.not_explicit` | source is not an explicit human choice |
| `choice.selection_out_of_scope` | selected option was not presented |
| `evidence.no_contrast` | visible attributes cannot explain the contrast |
| `outcome.invalid_source` | behavior substituted for an explicit report |
| `proposal.no_real_world_test` | graph change requested without real-world use |
| `gate.not_human_confirmed` | no explicit human decision |
| `gate.actor_mismatch` | authority crossed actors |
| `gate.purpose_mismatch` | authority crossed purpose partitions |
| `gate.stale_revision` | graph changed after proposal creation |
| `gate.expired` | proposal or decision expired |
| `gate.rejected` | human rejected the mutation |

## Idempotency and replay

The candidate local kernel is pure where possible. Production adapters must use idempotency keys, nonces, expected revisions, and authoritative receipt checks supplied by Quirk core. A prior approval cannot be replayed against a new proposal or revision.
