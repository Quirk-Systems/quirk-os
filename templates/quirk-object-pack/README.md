# Quirk Object Pack Templates

This candidate generator creates a consistent source pack for any admitted or candidate Quirk object family.

## Supported object kinds

`chatbot`, `platform`, `system`, `repository`, `prompt`, `chain`, `workflow`, `sequence`, `tool`, `evaluation`, `harness`, `automation`, `bot`, `content`, `slate`, `argument_set`, `permutation_set`, `plugin`, `capability`, `skill`, `agent`, `product`, `service`, and `revenue_stream`.

## Generated modules

Every pack starts with the same inspectable modules:

1. `MANIFEST.yaml`
2. `README.md`
3. `REPO-MANAGEMENT.md`
4. `SYSTEM-PROMPT.md`
5. `CUSTOM-INSTRUCTIONS.md`
6. `SETTINGS.yaml`
7. `PROJECT-INSTRUCTIONS.md`
8. `REFERENCES.md`
9. `SKILL.md`
10. `EVALS.yaml`
11. `OPERATING-WORKFLOW.yaml`

A module may state “not applicable,” but it may not silently disappear. This makes absence deliberate and reviewable.

## Command

```bash
python scripts/scaffold_quirk_object_pack.py \
  --kind agent \
  --id agent.example \
  --title "Example Agent" \
  --owner human.bryan \
  --output /tmp/agent-example
```

The generator writes candidate source only. It does not register, activate, deploy, or canonize the object.
