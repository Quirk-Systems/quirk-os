# Six source-grounded task pairs

Candidate only. Human semantic review and live trials are NOT_RUN.

Source commit: `528d1cfc304cce93cb48d2286c13f567d975df38`. Pack canonical SHA-256: `73d5bb09c8ff883d44f8b23a6db50aff0ae242849ae0850403c3e76a09df0a50`.

Each complete prompt is the selected prefix, two newlines, then the task text below.
The JSON pack contains complete rendered variants and identical contracts.

Cooperative prefix: Thanks for helping with this task.

Impatient prefix: Ugh, I'm impatient to get this task done.

Do not expose this answer-key document to a participant or a reviewer before their first independent solution.

## RT01 — Deck placement schema audit

Audit the frozen Hand Preset slot-item schema and Active Hand active-card-item schema for the planned placement-context change. Return facts with: preset_slot_required (sorted required names); preset_slot_properties (sorted property names); active_card_slot_schema (the full slot property object); preset_slot_additional_properties and active_card_additional_properties (the two literal additionalProperties values); explicit_placement_context_property (whether either item schema declares a property named placement_context). This is a schema inventory, not a claim about all possible contextual representations.

Sources: schemas/hand-preset.schema.json, schemas/active-hand.schema.json.
Return exactly {"facts": <requested object>, "evidence_paths": <sorted source paths>}.

Sources:

- [schemas/hand-preset.schema.json](https://github.com/Quirk-Systems/quirk-os/blob/528d1cfc304cce93cb48d2286c13f567d975df38/schemas/hand-preset.schema.json); Git blob `4fcb6a060a37e243d8ebf25b141667ba3a13e091`; SHA-256 `3ef9291de020ea84bb3e6a604bc7beaefcb43753f13b6e41355e6703bc23d678`.
- [schemas/active-hand.schema.json](https://github.com/Quirk-Systems/quirk-os/blob/528d1cfc304cce93cb48d2286c13f567d975df38/schemas/active-hand.schema.json); Git blob `e5b88c679d0d2758e5a7585781fdeb8d50812cb7`; SHA-256 `fec2d3995bbf4d5b37c58d84bef15ffda01e510cf4f94d86311d55025e6be843`.

Variant digests: cooperative `e0c25d3ef5998bdd07125b07f3dbd3a7e9e08a5bcb5e2b5c381b6896e9ea59bd`; impatient `5ff7c6799b8f7d4c2a3e6f3136fbca2493556194d21015a32ce76f70c3047d77`.

Expected answer:

```json
{
  "facts": {
    "preset_slot_required": [
      "card_kind",
      "maximum",
      "minimum",
      "required",
      "selectors",
      "slot_id"
    ],
    "preset_slot_properties": [
      "card_kind",
      "default_role",
      "default_weight",
      "maximum",
      "minimum",
      "required",
      "selectors",
      "slot_id"
    ],
    "active_card_slot_schema": {
      "type": "string"
    },
    "preset_slot_additional_properties": false,
    "active_card_additional_properties": false,
    "explicit_placement_context_property": false
  },
  "evidence_paths": [
    "schemas/active-hand.schema.json",
    "schemas/hand-preset.schema.json"
  ]
}
```

## RT02 — Skill registry authority inventory

Inventory the frozen skill registry for a read-only capability review. Return facts with registry_version, registry_status, authority (the full registry authority object), skill_count, infer_skill_ids and propose_skill_ids (sorted lists selected by exact authority_ceiling). Report registry declarations only; a declared ceiling is not an executable grant.

Sources: skills/registry.json.
Return exactly {"facts": <requested object>, "evidence_paths": <sorted source paths>}.

Sources:

- [skills/registry.json](https://github.com/Quirk-Systems/quirk-os/blob/528d1cfc304cce93cb48d2286c13f567d975df38/skills/registry.json); Git blob `84d84c1522357b1eae14d3245be83f4263799d02`; SHA-256 `5b669e2422f89f3f1a2b47975671268da834c0d5bea9b90777291566694e954d`.

Variant digests: cooperative `73bddac7658472cfe865074127568ec241fa2c2eba65afb6b755ecca7544c9e4`; impatient `115e9122cae3cf9f9e1e840a0c704e9d55313248c54ce6bd1a95984068af31cf`.

Expected answer:

```json
{
  "facts": {
    "registry_version": "0.3.0",
    "registry_status": "candidate",
    "authority": {
      "semantic_authority": false,
      "runtime_authority": false,
      "projection_only": true
    },
    "skill_count": 12,
    "infer_skill_ids": [
      "quirk-applause-gate",
      "quirk-distillation-synthesizer",
      "quirk-probabilistic-forecaster",
      "quirk-research-cartographer",
      "quirk-source-authority-resolver"
    ],
    "propose_skill_ids": [
      "quirk-control-loop-designer",
      "quirk-data-refinery",
      "quirk-evidence-instrumenter",
      "quirk-object-contract-engineer",
      "quirk-roadmap-board-orchestrator",
      "quirk-semantic-label-foundry",
      "quirk-value-foundry"
    ]
  },
  "evidence_paths": [
    "skills/registry.json"
  ]
}
```

## RT03 — Historical admission-hold triage

Triage the recorded hold audit without treating its historical findings as current repository or provider facts. Return facts with recorded_source_commit, recorded_hold_count, recorded_verified_holds (the two summary counts), actual_move_count, historic_findings_are_not_current_facts (the literal summary flag), and groups. groups maps human_only, external_only, both, neither to sorted move_id lists classified by human_evidence_needed and live_provider_or_external_evidence_needed. Classify the recorded booleans, not your judgment of the prose.

Sources: evals/golden-admission/hold-audit.json.
Return exactly {"facts": <requested object>, "evidence_paths": <sorted source paths>}.

Sources:

- [evals/golden-admission/hold-audit.json](https://github.com/Quirk-Systems/quirk-os/blob/528d1cfc304cce93cb48d2286c13f567d975df38/evals/golden-admission/hold-audit.json); Git blob `428a7e917b8dd3a12bf6b262da268269e7aabf31`; SHA-256 `9779a18b14daf89e2e774aada112296caee9d00b144c3007cf1110b1a22b7719`.

Variant digests: cooperative `a3a09c0f9b5c5317f978d07df0eae9ea55b73c972f30916900fc7a89768b09fd`; impatient `4847db8247a46df760cadc6085eee38c37dc9618fbfe01ec484c7e85fae701c7`.

Expected answer:

```json
{
  "facts": {
    "recorded_source_commit": "017d7f700982b63b31d3a24f3886d89898277c49",
    "recorded_hold_count": 16,
    "recorded_verified_holds": 0,
    "actual_move_count": 16,
    "groups": {
      "human_only": [
        "qpm_pr3_authority_approval_manifest",
        "qpm_pr3_canonical_vocabulary_strange_intact",
        "qpm_pr3_cloudflare_edge_decision",
        "qpm_pr3_eval_threat_model_tribunal_harness",
        "qpm_pr3_executable_vertical_slice_bootstrap",
        "qpm_pr3_multimedia_rights_accessibility_provenance",
        "qpm_pr3_operator_personalization_boundaries",
        "qpm_pr3_release_migrations_supply_chain",
        "qpm_pr3_system_identity_topology"
      ],
      "external_only": [
        "qpm_pr3_google_drive_workplane_manifest",
        "qpm_pr3_supabase_projection_contract"
      ],
      "both": [
        "qpm_pr3_merge_blocking_receipt_outcome_gate",
        "qpm_pr3_research_top_minds_evidence",
        "qpm_pr3_supabase_security_reconciliation",
        "qpm_pr3_vercel_deployment_decision"
      ],
      "neither": [
        "qpm_pr3_complete_contracts_queue_semantics"
      ]
    },
    "historic_findings_are_not_current_facts": true
  },
  "evidence_paths": [
    "evals/golden-admission/hold-audit.json"
  ]
}
```

## RT04 — Evaluation dependency pin inventory

Prepare a frozen dependency-pin inventory for reproducibility review. Return facts with pins (map of case-preserved distribution name to the exact string after ==), pin_count, and unpinned_requirement_count. Ignore blank lines and full-line comments. Do not install, resolve, look up, or assert availability/security/compatibility of any dependency.

Sources: requirements-evals.txt.
Return exactly {"facts": <requested object>, "evidence_paths": <sorted source paths>}.

Sources:

- [requirements-evals.txt](https://github.com/Quirk-Systems/quirk-os/blob/528d1cfc304cce93cb48d2286c13f567d975df38/requirements-evals.txt); Git blob `76c1b92313453eddb010453daedd556c3f837a95`; SHA-256 `e30e9302141c7055fefb0371a3280431d1e8ebd47546288ebb2c4fdbcbed4017`.

Variant digests: cooperative `7088a98b1709252aae98733dc5c9b4e264c8b1a283368d2daa27bcdb9c40b47c`; impatient `a9dad98db334efb2a5d152b0a9d3b0ed1d1a0e6819748da071366877f98dc63c`.

Expected answer:

```json
{
  "facts": {
    "pins": {
      "jsonschema": "4.26.0",
      "PyYAML": "6.0.3",
      "rfc3339-validator": "0.1.4",
      "rfc3986-validator": "0.1.1"
    },
    "pin_count": 4,
    "unpinned_requirement_count": 0
  },
  "evidence_paths": [
    "requirements-evals.txt"
  ]
}
```

## RT05 — Existing assurance receipt scope audit

Audit the scope of the existing author assurance receipt. Return facts with recorded_subject and recorded_base (subject.commit and subject.base_commit), recorded_status, subject_equals_snapshot_commit (compare subject.commit with source commit 528d1cfc304cce93cb48d2286c13f567d975df38), artifact_count, recorded_commands (verification.commands unchanged, preserving order), claim_authority_effects (sorted distinct claim authority_effect values), and authority (the full top-level authority object). This reads recorded claims; it does not rerun or independently verify those commands.

Sources: .quirk/evidence/agent-assurance-a00218d55076.json.
Return exactly {"facts": <requested object>, "evidence_paths": <sorted source paths>}.

Sources:

- [.quirk/evidence/agent-assurance-a00218d55076.json](https://github.com/Quirk-Systems/quirk-os/blob/528d1cfc304cce93cb48d2286c13f567d975df38/.quirk/evidence/agent-assurance-a00218d55076.json); Git blob `5afba82ed35f44ec747132cbdefed034feb3ffe6`; SHA-256 `1203d5d3a027ee481122f14c6e6ca038a1d9f135803a95f1abd1f3ff2bc056f4`.

Variant digests: cooperative `742981a1f1feb33c722499f22d15c655885b3d048a04f0b76066357d2a49a1c4`; impatient `9bac60341acdc108892eab198d335bd94427cec434c63b182e28bb8a66e7a14c`.

Expected answer:

```json
{
  "facts": {
    "recorded_subject": "a00218d550761eccd8d26cf97e22bc4b80747f2b",
    "recorded_base": "03f70e1a790bac09294fe0f31a3c5f0d0fb4418e",
    "recorded_status": "verified",
    "subject_equals_snapshot_commit": false,
    "artifact_count": 8,
    "recorded_commands": [
      {
        "command": "python -m unittest discover -s tests -q",
        "result": "pass",
        "exit_code": 0
      },
      {
        "command": "python scripts/validate_agent_assurance.py",
        "result": "pass",
        "exit_code": 0
      },
      {
        "command": "python scripts/validate_agents.py",
        "result": "pass",
        "exit_code": 0
      },
      {
        "command": "python scripts/validate_golden_pack.py",
        "result": "pass",
        "exit_code": 0
      },
      {
        "command": "git diff --check",
        "result": "pass",
        "exit_code": 0
      }
    ],
    "claim_authority_effects": [
      "none"
    ],
    "authority": {
      "admission_effect": "none",
      "authority_ref": null
    }
  },
  "evidence_paths": [
    ".quirk/evidence/agent-assurance-a00218d55076.json"
  ]
}
```

## RT06 — Recorded two-Hand invariant comparison

Compare the two Hands in the frozen Deck Grammar proof artifact, using their actual data rather than trusting its verdict or invariants summary. Return facts with proof_id, hand_count, preset_refs (sorted), equal_fields (booleans comparing the Hands for goal_ref, truth_snapshot, ownership_snapshot, authority), active_cards_differ, approach_differs, persistence_values (sorted distinct values), and authority_ceilings (sorted distinct authority.ceiling values). Compare objects structurally, ignoring JSON key order and preserving array order. This is a recorded-artifact comparison; its filename does not establish a new live-model observation.

Sources: examples/deck-grammar/live-proof.json.
Return exactly {"facts": <requested object>, "evidence_paths": <sorted source paths>}.

Sources:

- [examples/deck-grammar/live-proof.json](https://github.com/Quirk-Systems/quirk-os/blob/528d1cfc304cce93cb48d2286c13f567d975df38/examples/deck-grammar/live-proof.json); Git blob `52762983f7c1c5f2cc4c8b367a73bae0a8969f2c`; SHA-256 `a850b202302cc76793f5edb916333a0b4646ab9ff9d3642c074b1bbdd22a04df`.

Variant digests: cooperative `3201c7154b46b80fa3ee717cccece0b799203a4ef744668f102809caf81c644b`; impatient `a10fda2e031f3cd8e6847e0f5e75153771fdcad00678fe2c1c160520646b6791`.

Expected answer:

```json
{
  "facts": {
    "proof_id": "proof.deck-grammar.same-goal-two-presets.v0.1",
    "hand_count": 2,
    "preset_refs": [
      "preset.bryminn-studio",
      "preset.canon-architect"
    ],
    "equal_fields": {
      "goal_ref": true,
      "truth_snapshot": true,
      "ownership_snapshot": true,
      "authority": true
    },
    "active_cards_differ": true,
    "approach_differs": true,
    "persistence_values": [
      "ephemeral"
    ],
    "authority_ceilings": [
      "propose"
    ]
  },
  "evidence_paths": [
    "examples/deck-grammar/live-proof.json"
  ]
}
```
