# Repository Management — {{OBJECT_TITLE}}

## Source authority

- Canonical candidate source:
- Runtime projection:
- Work-plane sources:
- Human-facing projections:
- Supersession policy:

## Branch and commit policy

```text
agent/<bounded-change>
```

Commits should state the changed contract or behavior. Do not mix unrelated repairs.

## Pull-request posture

- Default: draft.
- Required checks:
- Required human authority:
- Stacked dependencies:
- Merge prohibition:
- Release evidence:

## Issue grammar

Every consequential gap becomes one of:

```text
Finding → Proposed Move → Implementation → Evidence → Decision → Outcome
```

## Versioning

Document schema, behavior, data, prompt, and interface compatibility separately.

## Release gates

- [ ] Contracts validate.
- [ ] Positive and adversarial fixtures pass.
- [ ] Authority and permissions are independently enforced.
- [ ] Migration and rollback or compensation are proven.
- [ ] Observability and receipts exist.
- [ ] Documentation and examples match runtime behavior.
- [ ] Human admission is recorded.
