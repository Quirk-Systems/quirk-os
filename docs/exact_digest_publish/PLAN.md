# Exact digest publication: bounded enforcement plan

**Object ID:** `artifact.exact-digest-publish.plan`  
**Object kind:** Artifact (`artifact_type: implementation_plan`)  
**Version:** 0.1.0  
**Status:** Produced; candidate implementation plan  
**Owner:** Quirk-Systems/quirk-os  
**Authority ceiling:** Candidate implementation and local verification  
**Canonical source:** This repository; semantic proposal in [quirk-core PR #10](https://github.com/Quirk-Systems/quirk-core/pull/10)

## Purpose

Implement the smallest bounded publication boundary in which passing evaluation cannot create human approval. The protected effect is publishing exact bytes into a local filesystem sink. Approval, evaluation, and the publication receipt must refer to the same artifact, digest, destination, and policy.

This plan does not authorize an external publication or admit a new foundational object kind.

## Reuse the existing grammar

`Shape`, `Plan`, `Implement`, and `Resolve Proof` name activities. They do not require four new kinds of object. One Proposed Move records the desired change, affected objects, dependencies, acceptance checks, implementation references, evidence, and disposition. An Artifact preserves this plan and its exact digest.

| Activity | Existing representation | Result carried forward |
| --- | --- | --- |
| Shape | Proposed Move: `desired_change`, `expected_outcome`, `affected_objects`, `authority_required`, `risk` | A bounded change with explicit ownership and authority |
| Plan | The same Proposed Move: `dependencies`, `implementation_ref`, `resolution_artifacts`, `acceptance_checks`; linked plan Artifact | A reviewable method and completion contract |
| Implement | Code and tests as versioned outputs; Proposed Move `implementation_ref` and `disposition` | An attributable implementation, without automatic admission |
| Resolve Proof | Actual eval results and receipt references; Proposed Move `eval_refs`, `evidence_refs`, `receipt_ref`, `resolution_note` | A conclusion limited to the exact tested implementation and boundary |

The source for this decision is the existing [architecture](https://github.com/Quirk-Systems/quirk-os/blob/10a2f7e9435c6555f0436c8e0882d9ee99081f68/docs/golden-project-pack/ARCHITECTURE.md), which already places an implementation patch or plan, pre-evals, regression checks, disposition, and receipt inside a Proposed Move. The schemas used here are copied unchanged from `quirk-os` main at `10a2f7e9435c6555f0436c8e0882d9ee99081f68`.

An Artifact's `status: produced` reports that its bytes exist. Its candidate maturity does not imply acceptance, authority, publication, or Canon. An evaluator's passing result cannot change those distinctions.

## Bounded implementation

1. Implement a broker under `scripts/exact_digest_publish/` with a protected state store and local sink. Treat the broker and its configuration as trusted control-plane components.
2. Obtain a caller's identity from the operating system. Give evaluator, composer, and authorizer callers distinct Unix identities; a caller-supplied role or approval field supplies no authority.
3. Permit evaluator callers to record evaluation evidence. Permit human-authorizer callers to grant and revoke approval through a separate operation. Composer callers may request publication; they cannot grant approval, change policy, or write the protected sink.
4. Bind publication to exact artifact identity, byte digest, destination, and current policy. At the publication boundary, require both a current passing evaluation and an effective matching human grant. Preserve historical records after invalidation or replacement.
5. Emit a receipt describing the bytes and destination actually published and the evaluation, grant, and policy used. Make the publication effect and receipt reconstructable together.
6. Verify the boundary using real subprocesses with distinct Unix UIDs, including attempted direct filesystem access and attempts to invoke another role's operations.

## Acceptance checks

- With no human grant, repeated passing evaluations leave the grant store unchanged and publication blocked.
- An evaluator or composer cannot mint a grant by supplying `approved: true`, a human identity, another operation name, or another role's record.
- A valid evaluation and grant permit only the exact approved bytes at the approved destination under the current policy.
- Changing artifact identity, bytes, destination, or policy invalidates the attempted use of an existing approval.
- Expiry, revocation, and evaluation invalidation block subsequent publication while retaining historical evidence.
- Evaluator and composer subprocesses cannot modify the authorizer, broker code/configuration, grant store, guard, or protected publication sink.
- Receipt references and output bytes agree, and failed requests produce no partial publication.
- Typed Proposed Move and plan Artifact instances validate against the existing schemas; the plan digest matches the actual plan bytes.

## Evidence and limits

The implementation's proof must name the exact source digest, test command, test outcomes, operating-system identities, and protected effect. Fixture success is evidence about that bounded runtime, not proof of deployed production enforcement.

Automated tests use a synthetic authorizer process. They can prove which operating-system principal supplied an approval. They cannot prove that a real human was present, understood the request, or intentionally approved it. Production use requires a separately trusted human authentication and confirmation path, with authorizer credentials unavailable to evaluator and composer processes.

The constrained result remains a candidate until actual evidence resolves these acceptance checks. Any unsupported production, human-presence, deployment, or Canon claim stays withheld.

## Completion and rollback

Before tests run, the Proposed Move remains `new`. An existing implementation may be recorded as `implemented`; a bounded `verified` disposition requires actual evidence and a receipt. Neither disposition grants production authority.

Removal of the candidate module and its configuration reverses installation. Revoking a grant blocks future use; it does not erase already published bytes or historical receipts. An external release would require its own compensation contract and authorization.
