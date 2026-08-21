# Verification Report

**Evidence date:** 2026-08-21  
**Local environment:** Node `v22.16.0`, npm `10.9.2`  
**Canonical CI target:** Node 24, with Node 22 compatibility evidence

This file records local deterministic evidence. GitHub branch, pull-request, and check state remain external repository evidence and are not hardcoded here.

## Fresh local execution

```text
npm test
19 tests passed
0 tests failed
```

Coverage includes:

- explicit-choice and abstention behavior;
- rejection of purchases and inferred satisfaction as outcomes;
- deterministic, purpose-scoped recommendation ranking;
- silence, rejection, stale revision, expiry, and cross-purpose Human Gate failures;
- full synthetic chain execution;
- rejection of synthetic proof as real proof;
- Supabase lifecycle-authority denial;
- composite actor/purpose/session scope constraints;
- database option validation;
- relational recommendation evidence;
- explicit service-writer grants and absent anonymous access;
- live-approval receipt requirements and `auto_apply=false`.

```text
npm run validate
PACK VALID: 14 required files present
canon ceiling intact
boundary hash matched
```

Boundary digest:

```text
sha256:e22c575b17d3a196e28c0a178e70a6dcfbd337218e105736fa2a5b5f1f117467
```

```text
npm run proof:synthetic
PASS: synthetic chain executed and receipt generated.
BLOCKED: synthetic execution does not satisfy the required real-world proof.
```

## Negative proof gate

The real-proof verifier was run against `proof/synthetic-example.json` and returned non-zero as required:

```text
proof.synthetic: Synthetic execution cannot satisfy the real-world proof.
proof.consent: Participant consent is required.
```

## Supabase evidence

Completed:

- migration contract was written failing-first;
- original SQL failed all six database contract groups;
- hardened SQL passes all six groups;
- transactional anonymous/two-user/service-writer proof is authored.

Not completed:

- migration execution on PostgreSQL/Supabase;
- live RLS, trigger, foreign-key, and rollback output;
- schema digest from an isolated branch;
- branch deletion receipt.

## Evidence not claimed

- Node 24 GitHub Actions result;
- merge or deployment;
- Supabase main-project mutation;
- OpenAI API request;
- Hugging Face upload or benchmark;
- real participant consent or real-world outcome;
- passing real-world proof;
- recommendation lift, commercial demand, or product-market fit.

## Verdict

**The admitted boundary is isolated. The candidate pack passes fresh local structural and adversarial verification. Database execution and one honest real-world proof remain blocking evidence, followed by a separate runtime-admission decision.**
