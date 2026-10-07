# PR #111 authority-binding repair

Inspected parent: `cefcae57c5680908c564c8938ff351533dc4c99d`.
Current-main reconciliation base: `38ba6b9b6a3ddd2ee34807bfde5cf5be4673691f`.
The original repair at `8bb334214935ba16d04609cd2dae46c2c3e77929` was a merge
commit; its scoped-grant changes are explicitly retained after the linear rebase.
This is candidate implementation evidence, not Bryan's approval or live admission.

## Boundary contract

Both model-tool resolution and request serialization require an admitted canonical
skill, its exact source, a model-tool grant, a trusted current-grant lookup, exact
requested object references, and the host's current timestamp. There is no legacy
ungated call path. Schemas for the runtime manifest, registry, skill, and grant are
enforced before nested use. All failed verdicts emit zero model-visible tools;
serialization raises before producing a request.

The model-tool grant extends the existing skill grant fields without changing the
strict base-grant schema. After complete extended-grant schema validation and
current-record equality, only the base schema's fields are passed to the existing
loader. `load_skill_for_execution` checks canonical source/manifest
integrity, identity, admission, expiry, actions, authority ceiling, well-formed
requester identity, independent human approver, and trusted approval-registry
bindings. Neither principal checks nor schema validation are bypassed.

Resolution and serialization accept host-installed `approval_registry`, `verifier`,
and activation `context`. Omitted dependencies deny. Runtime manifest admission
uses current main's computed content hash, exact approval envelope, trusted
verifier, and manifest registry authorization. The same registry is passed through
the skill loader for a separate skill authorization; a positive manifest check
cannot substitute for a positive skill check. Database failure, non-boolean
approval, and revoked/stale decisions deny on every invocation. The resolver
also compares the entire supplied grant with the current authoritative record.
Missing/revoked records and lookup failures deny. Revocation must be represented by
removing the active record or returning a nonmatching current record.

`runtime_manifest_sha256` and `tool_registry_sha256` are SHA-256 digests of the
complete canonical JSON values using `projection_digest`. No fields are excluded.
This binds tool refs, allowed actions, scope, authority requirements, admission,
identity/version, and concrete parameter schemas to the authoritative grant.
Changing admission hash strings together cannot bypass this binding. These digests
are external to the inputs, so no circular digest construction is needed.

Requested exact object references must be a nonempty subset of both the grant and
every emitted binding's `object_scope`. Missing binding scope denies. Every binding
must explicitly declare `requires_authority`; every listed authority token must be
in the grant's `authorities`. An explicit empty requirements list means none.
Actions must be declared on the canonical skill's matching registered tool and
allowed by the grant. Wildcards have no expansion semantics. Only the common
observe/infer/propose authority tiers are currently interoperable; execution tiers
with different vocabulary fail closed pending an explicit reviewed mapping.

## Trust and deployment limits

The host owns the lookup implementation, schema files, source inputs, and clock.
Never accept a lookup callback or historical `now` from the model/request payload.
The checked-in fixture uses a fixed clock and in-memory authority record solely for
evaluation. The conformance CLI and unit tests inject explicitly synthetic
registry/verifier dependencies. These are not runtime defaults and cannot be
constructed from a model payload. They are not real grants or approval evidence.

This boundary governs schema exposure for a requested scope. It does not execute
actions or constrain arbitrary future model arguments. A live dispatcher must
validate actual arguments and their object references and recheck current grant,
expiry, scope, and authority immediately before effects. Do not reuse successful
resolution as an execution permit. Provider/dispatcher wiring, authoritative-store
provenance, and revocation-between-projection-and-dispatch evidence remain separate
activation prerequisites. No token, cost, latency, or upkeep gain is established.

## Fresh successor-head proof

After publishing, record the exact successor SHA, tree SHA, current main SHA, and
merge-base. Re-run on that exact successor (and current-main integration if main
moves); parent-head green checks do not transfer. Retain logs and JSON outputs with
those SHAs and command exit codes:

```sh
python -m unittest discover -s tests -p 'test_*.py' -v
python scripts/validate_sync_control_plane.py --repo . --output /tmp/pr111-sync.json --require-admit
python scripts/validate_skills.py --repo . --output /tmp/pr111-skills.json
PYTHONPATH=scripts python scripts/validate_distill_loop.py --repo . --output /tmp/pr111-distill.json --require-pass
python scripts/validate_golden_pack.py
```

Require fresh Golden Gates, candidate-conformance, skill-candidate-conformance,
and candidate-distill-loop-conformance workflow results. Record both PR head and
checkout SHA when CI tests a synthetic merge commit. Retain artifacts and review
all new substantive findings. The adapter tests require a benign schema to remain
visible and deny changed actions, grant tampering, expiry (including the boundary),
future grants, revocation after success, unavailable authority state, wrong scope,
missing binding constraints, authority mismatch, changed source/manifest/registry,
malformed schemas, and unknown actions. Failed serialization must expose no request.

Bryan's exact-successor-head approval, merge authorization, and live activation
are three separate decisions. Bot credit-limit notices are review-tool noise.
Passing conformance or fixture labels such as ELIGIBLE_FOR_HUMAN_ADMISSION do not
supply any of those decisions. Preserve draft status pending that handoff.
