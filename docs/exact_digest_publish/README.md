# Exact digest publication enforcement

**Object ID:** `capability.exact-digest-publish`  
**Object kind:** Capability implementation candidate  
**Version:** 0.1.0  
**Status:** Candidate; verification must be read from actual evidence  
**Owner:** Quirk-Systems/quirk-os  
**Authority ceiling:** Local protected-sink publication within an explicitly configured scope  
**Canonical source:** This repository; [semantic proposal in quirk-core PR #10](https://github.com/Quirk-Systems/quirk-core/pull/10)

## Purpose

Require an independent human grant alongside a passing evaluation before publishing one exact artifact digest. The guard operates at the local publication boundary. Neither evaluation success nor a caller-supplied approval field grants permission.

The owning runtime is `quirk-os`; `quirk-core` owns the semantic contract. This is a bounded Linux implementation for a protected local filesystem sink. No external publication service is integrated or enabled by this candidate.

## Read and reproduce

The [implementation plan](PLAN.md) records the object mapping, work sequence, acceptance checks, and evidence limits. The typed records are:

- [Proposed Move](../../evals/exact_digest_publish/proposed-move.json)
- [Plan Artifact](../../evals/exact_digest_publish/plan-artifact.json)

From the repository root on Linux, run the subprocess enforcement suite as root in a disposable test environment:

```bash
python -m unittest discover -s tests/exact_digest_publish -v
```

Root is needed by the test harness to launch distinct unprivileged Unix identities. Root is not the adversary being tested. A test run that cannot establish those identities cannot prove the process-isolation boundary.

The suite creates and removes a disposable installation with root-owned source/configuration, a broker-owned private state directory, a separate socket directory, and distinct broker, authorizer, evaluator, composer, and unrecognized-caller identities. It does not provision a production service.

For attributable machine-readable evidence, the runner records actual unittest outcomes, all required case IDs, source hashes, timestamps, and the UID/GID environment:

```bash
python -m scripts.exact_digest_publish.proof run --output /tmp/exact-digest-proof.json
python -m scripts.exact_digest_publish.proof resolve --run /tmp/exact-digest-proof.json
```

`run` uses only the standard library. `resolve` requires the repository's `jsonschema==4.26.0` dependency. Resolution validates the existing Artifact and Proposed Move schemas and creates references to the preserved run and source manifest. It marks the move `verified` only when every declared case passed, none were skipped, no suite errors occurred, and source hashes match. A zero-test preflight failure produces unresolved evidence and a nonzero exit code. Run JSON is unsigned: fetch it from the trusted execution source before resolving it.

## Runtime interface

`scripts.exact_digest_publish.broker` accepts `--config`. The root-owned JSON configuration has exactly these fields:

```text
version: 1
broker_uid, authorizer_uid, evaluator_uid, composer_uid: four distinct non-root UIDs
state_dir: absolute broker-owned directory, mode 0700
socket_path: absolute socket path in a separate broker-owned traversable directory
destination_id: one bounded local-sink identifier
authority_mode: test_fixture or human_session
policy: id, revision, evaluation_ttl_seconds, max_grant_seconds, max_payload_bytes
```

The broker must run as `broker_uid`, with no supplementary groups and protected root-owned source. Launch it using a trusted interpreter, protected full import tree, clean environment, and trusted working directory: source checks occur after Python imports. Its state binds to the configured identities, destination, and authority mode; restarting cannot silently change that binding. The test fixture is the executable setup reference in `tests/exact_digest_publish/test_enforcement.py`.

`scripts.exact_digest_publish.client --config` sends one JSON request from standard input and verifies the server's Unix peer UID. The caller never supplies an authoritative role. A publication subject contains `artifact_id`, `payload_digest`, `operation: publish`, `destination_id`, and `policy_digest`; its scope digest binds all five fields.

| Principal | Operations |
| --- | --- |
| Composer | `stage`, `publish`, `reconcile`, `status` |
| Evaluator | `evaluate`, `status` |
| Authorizer | `grant`, `revoke`, `set_policy`, `inspect`, `status` |

`scripts.exact_digest_publish.authorizer` accepts `--config`, `--subject`, and `--expires-in`. It requires the configured authorizer UID, `human_session` mode, and a terminal response containing the displayed exact scope digest. It supplies no unattended approval flag. The separate authorizer account remains the trust root; the helper does not prove biological human presence or protect an already compromised authorizer session.

## Authority boundary

| Component | Permitted responsibility |
| --- | --- |
| Evaluator principal | Record evaluation evidence for an exact subject and policy |
| Composer principal | Request a publication using existing evidence and authority |
| Authorizer principal | Record or revoke approval through the separate authorization operation |
| Trusted broker | Identify peers, enforce policy, protect state, publish exact bytes, and record the receipt |

The operating system must distinguish these principals. Evaluator and composer processes must lack write access to broker code, configuration, private state, authorizer credentials, and the protected sink. Merely assigning different role labels to callers in one unrestricted process does not establish this boundary.

A passing evaluation is evidence. A grant is permission. A receipt records an effect. They remain separate records even when the publication guard composes them.

## Trust assumptions

- The Linux kernel, root, broker process, and deployment control plane are trusted.
- Broker code, configuration, private state, and destination ownership are protected from evaluator and composer identities.
- The authorizer identity is controlled by a trusted human authorization path. An automated test's authorizer is a synthetic fixture, not a real human approval.
- Privileged file descriptors, private directories, and authorizer credentials are not delegated to evaluator or composer processes.
- The local protected sink is the complete effect under test. Any production external destination needs its own enforced credential boundary and evidence.

If these assumptions do not hold, a local pass cannot establish the claimed guarantee. In particular, an evaluator running as root or as the authorizer can bypass the intended separation.

## Failure and evidence interpretation

Missing, mismatched, invalidated, expired, or revoked authority must block the requested effect. Historical evaluation and approval records remain inspectable without becoming reusable for a new digest or policy.

Read a proof result together with its tested source digest, command, environment, and declared limitations. Candidate implementation completion does not assert live deployment, real human presence, external publication, or Canon admission.

At the durable authorization commit, the broker requires a current passing evaluation and a matching, unexpired, unrevoked, unused grant. The grant is consumed before dispatch. Grant and evaluation expiry are rechecked immediately before the atomic publication operation, which refuses to replace an existing output. Expiry during dispatch preparation produces `not_published` while preserving the consumed intent. A receipt marked `unknown` is unresolved; use `reconcile` for that same request ID instead of creating a replacement attempt. `confirmed` records the verified local output, while `not_published` records its absence. Repeating a known request returns its historical receipt without creating another effect or restoring the consumed grant.

No new evaluation or grant can be processed during that serialized commit-and-dispatch operation.

The planned stages use existing Proposed Move, Artifact, evaluation, and receipt distinctions. They add no `Shape`, `Plan`, `Implementation`, or `Proof` foundational kind.
