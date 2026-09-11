# Plugin Capability Harvest and Quirk Fuckery

Status: **candidate / non-operative**

This slice turns exact, permitted capability observations and Quirk-owned portfolio context into provider-neutral mechanism and prompt candidates. “Quirk Fuckery” is the prospecting mode: find a valuable Move in completed Quirk work, compile its minimum typed role packet, replay it without conversational memory, measure Forward Carry, and deposit only a candidate.

It does not retrieve or reconstruct third-party prompts, copy proprietary code or documentation, infer hidden schemas, install plugins, invoke provider mutations, publish skills, change personal truth, grant authority, or write Canon.

## Boundary

The observation room emits hashes and structural facts. The prompt compiler accepts only closed fields and bounded `quirk:` or content-addressed references in every packet lane that reaches `PACKET_JSON`; raw external expression is rejected. The re-expression room accepts Quirk-owned Goal, Project, System and person references plus provider-neutral mechanism contracts. Unknown identity or rights is quarantined.

Clean-room and rights decisions are resolved through a host-configured read-only trust root. Registry keys are recomputed from the exact evidence record, records are freshness- and subject-bound, and the issuer must differ from the implementation actor. This verifies the supplied evidence envelope; it does not prove the human review itself occurred.

Installation, exposure, registered callability, observed runtime behavior, documented behavior, credentials and authority remain independent facts.

The filesystem scanner establishes installation only. Host catalogs, live registries, app/MCP declarations, documentation and runtime results must be supplied as separate typed observations and fingerprinted with `python -m scripts.plugin_capability_harvest fingerprint surfaces.json`. The tool never promotes one lane into another.

## Runtime seam

`to_loop_spec()` maps a validated prompt candidate to the existing `loop-spec/v1` contract with `CANDIDATE_PREPARE` authority only. It does not claim that an extra approval flag is runtime-enforced. The established loop runner remains the sole owner of dispatch, grants, interruption recovery, approval/grant checks and action receipts. This package cannot activate its output.

## Verify

```bash
python -m unittest tests.test_plugin_capability_harvest -v
python -m scripts.plugin_capability_harvest --help
```

The CLI exposes `scan`, `fingerprint`, `diff`, `prompt`, `to-loop-spec`, and `receipt`. Each command writes JSON to stdout only; callers own durable append-only storage and any later grant.

Release posture is `CONSTRAIN` until independent review, no-memory replay, cross-topology comparison, schema validation, and measured positive Forward Carry are present. Passing tests never grant authority or admission.
