# Verification Report

**Evidence date:** 2026-08-25

**Local receipt environment:** Node `v24.19.0`, npm `11.9.0`

**Compatibility evidence:** This local receipt is Node 24 only. The pull-request matrix supplies Node 22 compatibility evidence.

This file records local deterministic evidence. GitHub branch, pull-request, and check state remain external repository evidence and are not hardcoded here.

## Fresh local execution

```text
npm test
24 tests passed
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
PACK VALID: 19 required files present; canon ceiling intact; source lineage bound; Cloudflare receipt gate fail-closed; boundary hash sha256:264c636c364db2caa08b2d4370eb10618c721d74f2588f8359546d8a9b45fb21.
```

Boundary digest:

```text
sha256:264c636c364db2caa08b2d4370eb10618c721d74f2588f8359546d8a9b45fb21
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
