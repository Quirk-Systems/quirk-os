# Quirk Agents

Status: **candidate / non-operative**.

An agent is an actor that binds candidate Skills to tools, input/output schemas, a trigger contract, stop conditions, and a receipt obligation. Skills say *how* to do something; an agent manifest says *who* may invoke which skills, through which tools, and where it must stop.

Each agent lives in `agents/<slug>/agent.yaml` and must satisfy [`schemas/agent-manifest.schema.json`](../schemas/agent-manifest.schema.json). The central [`registry.json`](registry.json) is a rebuildable candidate inventory. It is not Canon and cannot admit, activate, or project anything.

| Agent | Status | Ceiling | Skills | Purpose |
| --- | --- | --- | --- | --- |
| `agent.quirk-sync-steward` | candidate | propose | 11 | Cross-platform identity, authority boundaries, immutable evidence, bounded retries, and rebuildable projections |

## Runtime rule

Binding a skill, holding a tool, or passing conformance never implies authority (`capability_does_not_imply_authority: true`). Admission is an external decision governed by [`policies/manifest-admission-policy.yaml`](../policies/manifest-admission-policy.yaml). No agent may self-activate, approve its own transition, expand its own authority, promote Canon, merge, or deploy.

## What `scripts/validate_agents.py` enforces

- Schema validity (Draft 2020-12 with `FormatChecker`). Status, version, ceiling, domain, routing-policy, and rights-review vocabularies are `$ref`-reused from `schemas/runtime-manifest.schema.json`.
- Folder ↔ `metadata.id` ↔ registry agreement in both directions, plus all registry digests.
- Every bound skill exists in `skills/registry.json`; `quirk-distilled-*` skills are never bindable.
- Authority ranks use an explicit ladder, independently of unordered schema enums. Schema vocabulary changes fail conformance.
- **Ceiling rule:** each bound skill's ceiling must be ≤ the agent's ceiling, so an agent never binds authority it does not hold. Skill `execute_bounded` ranks as runtime `execute_reversible`.
- `authority.prohibited` covers every `protected_actions` entry in the admission policy.
- Referenced policy, schema, evaluation, trigger, admission, and rights-review evidence files exist inside the repository.
- Schema-invalid manifests never reach semantic checks; failure reports and metrics remain available.
- The supported admission policy is pinned, including rule IDs, requirements, conditions, and protected actions; unsupported policy changes fail conformance.
- Static admission-policy v0.4 rules: multi-skill agents block on collisions; `active` requires nonempty `eval_refs` and an admission record with evidence; requester ≠ approver and the approver must be a well-formed human principal; the agent ceiling may not exceed `admission.granted_ceiling`; `admission.evaluated_content_hash` must match the manifest content; `data_productization` requires an approved rights review.

```bash
pip install -r requirements-evals.txt
python -m unittest tests.test_agent_manifest -v
python scripts/validate_agents.py --repo . --output evals/agents/conformance-results.json \
  --metrics-output evals/agents/conformance-metrics.json --write-step-summary
```

## Structural checks are not admission

The validator pins policy v0.4, including its verification contract, to detect drift. It checks only local contract structure and file references. A syntactically valid `human.*` name is not proof of consent. The runtime verifier owns live approval identity, scope, expiry, revocation, and attestation checks; this candidate validator does not call it or confer its authority. Even an active test fixture can pass only structural conformance.

`observability.ci_metrics_refs` declares generated output paths and is checked for repository containment; those outputs need not exist before CI runs. `benchmark_refs` names source files and must resolve to existing repository files. Telemetry never substitutes for admission evidence.

References use normalized POSIX repository-relative paths on every host; Windows separators, drive/stream syntax, traversal, and control characters are rejected. Malformed paths and filesystem failures produce unresolved-reference findings. Every changed repository path triggers agent CI because referenced evidence can live anywhere in the repository. Existing manifests rejected by parsing or schema validation are not mislabeled as absent registry orphans.

## Digest policy

Recorded in `registry.json` as `digest_policy` and checked by the validator:

| Field | Computed over |
| --- | --- |
| `source_blob_sha` | git blob SHA-1 of the raw `agent.yaml` bytes (pins exact bytes) |
| `manifest_sha256` | SHA-256 of canonical JSON (sorted keys, compact, UTF-8) of the parsed YAML |
| `admission.evaluated_content_hash` | same as `manifest_sha256`, with the `admission` block removed |
| `registry_sha256` | SHA-256 of canonical JSON of the registry without `registry_sha256` |

Agent and policy YAML, schema JSON, and registry JSON are parsed with duplicate keys rejected, and must contain only JSON-representable values (quote timestamps).

## Adding or changing an agent

1. Create or edit `agents/<slug>/agent.yaml` with `metadata.id: agent.<slug>` and `status: candidate`.
2. Regenerate the registry entries and seal:

   ```bash
   python - <<'EOF'
   import json, sys
   from pathlib import Path
   sys.path.insert(0, "scripts")
   from validate_agents import build_registry_entry, seal_registry
   root = Path(".").resolve()
   path = root / "agents" / "registry.json"
   registry = json.loads(path.read_text())
   registry["agents"] = [build_registry_entry(root, p) for p in sorted(root.glob("agents/*/agent.yaml"))]
   path.write_text(json.dumps(seal_registry(registry), indent=2) + "\n")
   EOF
   ```

3. Run the validator and tests above.

## Deferred

Projection of agents into the Supabase `manifest_registry` table is intentionally deferred; this registry is repository-only inventory until a separate decision.
