# Agent and Platform System Prompt Architecture

## Prompt layers

```text
Platform invariant
→ Organization governance
→ Repository / project instruction
→ Agent manifest
→ Skill contract
→ Purpose-scoped context
→ Current explicit user instruction
→ Tool result and evidence
```

Conflict resolution follows authority and specificity. Current explicit user intent wins over preferences but cannot override external law, safety, or unavailable authority.

## System prompt modules

1. Role
2. Objective
3. Authority
4. Source precedence
5. Required behavior
6. Prohibited behavior
7. Tools and object scope
8. Output contract
9. Evidence and receipts
10. Stop conditions
11. Evaluation hooks
12. Version and provenance

## Platform adaptation

Each platform adapter may change transport, formatting, latency behavior, or available affordances. It may not silently change the semantic decision, authority ceiling, or source-of-truth relationship.

## Prompt registration

Every durable prompt records:

```yaml
prompt_id:
version:
status:
owner_ref:
purpose:
inputs_schema_ref:
outputs_schema_ref:
authority_ceiling:
model_constraints:
tool_scope:
reference_refs:
eval_refs:
content_hash:
```

Prompt text without provenance, evaluation, and a bounded purpose remains working material rather than Canon.
