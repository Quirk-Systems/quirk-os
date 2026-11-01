"""Validate the Quirk agent candidate layer.

Checks every ``agents/<slug>/agent.yaml`` against ``schemas/agent-manifest.schema.json``,
reconciles ``agents/registry.json`` in both directions, cross-checks bound skills
against ``skills/registry.json``, and applies the statically checkable rules of
``policies/manifest-admission-policy.yaml``. Passing is evidence only: nothing here
admits, activates, or projects an agent.

Digest policy (recorded in the registry as ``digest_policy``):

* ``source_blob_sha`` - git blob SHA-1 over the raw ``agent.yaml`` bytes.
* ``manifest_sha256`` - SHA-256 over canonical JSON of the parsed YAML.
* content hash (``admission.evaluated_content_hash``) - SHA-256 over canonical JSON
  of the parsed YAML with the ``admission`` block removed.
* ``registry_sha256`` - SHA-256 over canonical JSON of the registry without
  ``registry_sha256``.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012


DISTILLED_PREFIX = "quirk-distilled-"
SKILL_ID_PREFIX = "skill."
AGENT_ID_PREFIX = "agent."
MANIFEST_SCHEMA = "agent-manifest.schema.json"
REGISTRY_SCHEMA = "agent-registry.schema.json"
RUNTIME_SCHEMA = "runtime-manifest.schema.json"
POLICY_PATH = "policies/manifest-admission-policy.yaml"
# Pin the supported policy semantics; policy changes require validator review.
EXPECTED_POLICY = {'api_version': 'quirk.dev/policy/v1alpha1',
 'kind': 'Policy',
 'metadata': {'id': 'policy.manifest-admission', 'version': '0.4.0', 'status': 'candidate'},
 'invariant': 'capability_never_implies_authority',
 'rules': [{'id': 'well_formed_requester',
            'require': 'admission.requested_by matches '
                       '"^(human|agent|service|system)\\\\.[a-z0-9._-]+$"'},
           {'id': 'no_self_approval', 'require': 'admission.requested_by != admission.approved_by'},
           {'id': 'independent_human_approval',
            'require': 'admission.approved_by matches "^human\\\\.[a-z0-9._-]+$"'},
           {'id': 'evaluated_hash_matches',
            'require': 'admission.evaluated_content_hash == content_hash'},
           {'id': 'explicit_grant', 'require': 'admission.authority_grant_ref'},
           {'id': 'legal_transition', 'require': 'admission.transition_ref'},
           {'id': 'active_requires_evidence',
            'require': 'eval_refs and stop_conditions and admission.evidence_refs'},
           {'id': 'rights_before_productization',
            'when': 'domains contains data_productization',
            'require': 'rights_review.outcome == approved and rights_review.license_verified and '
                       'rights_review.privacy_review == approved and '
                       'rights_review.provenance_complete'},
           {'id': 'collisions_fail_closed',
            'when': 'manifest_kind == orchestrator and len(skill_refs) > 1',
            'require': 'trigger_contract.collision_behavior == block'}],
 'protected_actions': ['activate_manifest',
                       'promote_canon',
                       'expand_authority',
                       'merge_pull_request',
                       'deploy_production'],
 'verification_contract': {'hash_profile': 'runtime-manifest-content.v1',
                           'attestation_schema': 'manifest-approval-attestation.v1',
                           'approval_root': 'exact_head_scoped_human_github_review',
                           'ownership_source': 'protected_base_branch_CODEOWNERS_and_installed_account_ID_mapping',
                           'database_independence': 'projection',
                           'database_write_role': 'quirk_manifest_verifier',
                           'bootstrap': 'blocked_until_host_policy_and_repository_protection_are_admitted',
                           'requirements': ['compute_content_hash_including_all_metadata',
                                            'resolve_review_identity_scope_expiry_revocation_and_evaluation_materials',
                                            'compare_entire_admission_envelope_with_resolved_consent',
                                            'refuse_fabricated_refs_and_ambiguous_or_unavailable_approval',
                                            'reverify_immediately_before_database_transaction',
                                            'preserve_append_only_history_and_zero_effect_replay'],
                           'limitations': ['PostgreSQL_does_not_independently_resolve_GitHub_or_recompute_Python_JSON_hashes',
                                           'privileged_verifier_or_database_administrator_compromise_is_outside_this_boundary',
                                           'review_resolution_and_database_write_are_not_cross_provider_atomic']}}

# Skill packages use their own ceiling ladder; ``execute_bounded`` is the only rung
# absent from the runtime-manifest ladder and is ranked as ``execute_reversible``.
SKILL_CEILING_EQUIVALENTS = {"execute_bounded": "execute_reversible"}
AUTHORITY_LADDER = (
    "observe", "infer", "propose", "execute_reversible", "enforce_invariant", "execute_protected",
)

DIGEST_POLICY = {
    "source_algorithm": "git-blob-sha1-raw-bytes",
    "manifest_algorithm": "sha256-canonical-json-of-parsed-yaml-v1",
    "content_algorithm": "sha256-canonical-json-of-parsed-yaml-without-admission-v1",
    "registry_algorithm": "sha256-canonical-json-without-registry_sha256-v1",
}


class _UniqueKeyLoader(yaml.SafeLoader):
    """Safe loader that rejects duplicate mapping keys instead of keeping the last one."""


def _construct_unique_mapping(loader: _UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(None, None, f"duplicate key {key!r}", key_node.start_mark)
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping)


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key {key!r}")
        result[key] = value
    return result


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def git_blob_sha(payload: bytes) -> str:
    return hashlib.sha1(f"blob {len(payload)}\0".encode("utf-8") + payload).hexdigest()


def load_agent_yaml(payload: bytes) -> dict[str, Any]:
    data = yaml.load(payload.decode("utf-8"), Loader=_UniqueKeyLoader)  # noqa: S506 - SafeLoader subclass
    if not isinstance(data, dict):
        raise ValueError("agent manifest must be a mapping")
    canonical_json_bytes(data)  # rejects YAML-only types such as timestamps
    return data


def manifest_sha256(manifest: dict[str, Any]) -> str:
    return sha256_hex(manifest)


def content_sha256(manifest: dict[str, Any]) -> str:
    candidate = copy.deepcopy(manifest)
    candidate.pop("admission", None)
    return sha256_hex(candidate)


def registry_sha256(registry: dict[str, Any]) -> str:
    return sha256_hex({key: value for key, value in registry.items() if key != "registry_sha256"})


def _manifest_is_symlink(root: Path, manifest_path: Path) -> bool:
    return any(path.is_symlink() for path in (root / "agents", manifest_path.parent, manifest_path))


def build_registry_entry(root: Path, manifest_path: Path) -> dict[str, Any]:
    if _manifest_is_symlink(root, manifest_path):
        raise ValueError("agent source must be a regular file, not a symlink")
    payload = manifest_path.read_bytes()
    manifest = load_agent_yaml(payload)
    metadata = manifest["metadata"]
    return {
        "id": metadata["id"],
        "version": metadata["version"],
        "status": metadata["status"],
        "authority_ceiling": manifest["authority"]["ceiling"],
        "manifest_path": manifest_path.relative_to(root).as_posix(),
        "source_blob_sha": git_blob_sha(payload),
        "manifest_sha256": manifest_sha256(manifest),
    }


def seal_registry(registry: dict[str, Any]) -> dict[str, Any]:
    sealed = dict(registry)
    sealed.pop("registry_sha256", None)
    sealed["registry_sha256"] = registry_sha256(sealed)
    return sealed


def _schema_errors(validator: Draft202012Validator, instance: Any) -> list[str]:
    return [
        f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(instance), key=lambda item: [str(p) for p in item.absolute_path])
    ]


def _repo_file(root: Path, ref: Any) -> Path | None:
    if not isinstance(ref, str) or not ref or "://" in ref:
        return None
    # One portable interpretation on POSIX and Windows, including drive/ADS syntax.
    if "\\" in ref or ":" in ref or any(ord(char) < 32 or ord(char) == 127 for char in ref):
        return None
    pure = PurePosixPath(ref)
    if pure.as_posix() != ref or ".." in pure.parts or ref == ".":
        return None
    try:
        if pure.is_absolute():
            return None
        candidate = (root / ref).resolve()
        if root != candidate and root not in candidate.parents:
            return None
        return candidate
    except (ValueError, RuntimeError, OSError):
        return None


def _is_file(path: Path | None) -> bool:
    try:
        return path is not None and path.is_file()
    except (ValueError, RuntimeError, OSError):
        return False


def validate_repository(root: Path) -> dict[str, Any]:
    root = root.resolve()
    started = time.perf_counter()
    findings: list[dict[str, str]] = []
    scanned = {"files": 0, "bytes": 0}

    def fail(code: str, message: str) -> None:
        findings.append({"level": "error", "code": code, "message": message})

    def read_bytes(path: Path) -> bytes:
        payload = path.read_bytes()
        scanned["files"] += 1
        scanned["bytes"] += len(payload)
        return payload

    schemas: dict[str, dict[str, Any]] = {}
    resources = Registry()
    for name in (RUNTIME_SCHEMA, MANIFEST_SCHEMA, REGISTRY_SCHEMA):
        path = root / "schemas" / name
        try:
            schema = json.loads(read_bytes(path), object_pairs_hook=_unique_json_object)
            Draft202012Validator.check_schema(schema)
            if not isinstance(schema, dict) or not isinstance(schema.get("$id"), str):
                raise ValueError("schema must be an object with a string $id")
            if schema.get("$schema", "https://json-schema.org/draft/2020-12/schema") != "https://json-schema.org/draft/2020-12/schema":
                raise ValueError("unsupported schema dialect; expected Draft 2020-12")
            resource = Resource.from_contents(schema, default_specification=DRAFT202012)
            resources = resources.with_resource(schema["$id"], resource)
            schemas[name] = schema
        except Exception as exc:  # noqa: BLE001 - every failure is reported as a finding
            fail("SCHEMA_INVALID", f"schemas/{name}: {exc}")

    def make_validator(name: str) -> Draft202012Validator | None:
        schema = schemas.get(name)
        if schema is None:
            return None
        return Draft202012Validator(schema, registry=resources, format_checker=FormatChecker())

    manifest_validator = make_validator(MANIFEST_SCHEMA)
    registry_validator = make_validator(REGISTRY_SCHEMA)

    ceiling_schema = schemas.get(RUNTIME_SCHEMA, {}).get("properties", {}).get("authority_ceiling", {})
    ceiling_order = ceiling_schema.get("enum", []) if isinstance(ceiling_schema, dict) else []
    rank = {ceiling: index for index, ceiling in enumerate(AUTHORITY_LADDER)}
    vocabulary_valid = (isinstance(ceiling_order, list) and all(isinstance(value, str) for value in ceiling_order)
            and len(ceiling_order) == len(AUTHORITY_LADDER) and set(ceiling_order) == set(AUTHORITY_LADDER))
    if not vocabulary_valid:
        fail("CEILING_VOCABULARY_DRIFT", f"schemas/{RUNTIME_SCHEMA}: authority vocabulary differs from the pinned ladder")

    protected_actions: set[str] = set()
    try:
        policy = yaml.load(read_bytes(root / POLICY_PATH), Loader=_UniqueKeyLoader)
        if policy != EXPECTED_POLICY:
            fail("POLICY_DRIFT", f"{POLICY_PATH}: unsupported policy; update and review the validator before conformance")
        protected_actions = set(EXPECTED_POLICY["protected_actions"])
        if not protected_actions:
            fail("POLICY_PROTECTED_ACTIONS_MISSING", f"{POLICY_PATH}: protected_actions is empty")
    except Exception as exc:  # noqa: BLE001
        fail("POLICY_INVALID", f"{POLICY_PATH}: {exc}")

    skill_ceilings: dict[str, str] = {}
    try:
        skill_registry = json.loads(read_bytes(root / "skills" / "registry.json"), object_pairs_hook=_unique_json_object)
        if not isinstance(skill_registry, dict) or not isinstance(skill_registry.get("skills"), list):
            raise ValueError("skill registry must contain a skills array")
        parsed_ceilings: dict[str, str] = {}
        for entry in skill_registry["skills"]:
            if not isinstance(entry, dict) or not isinstance(entry.get("id"), str) or not isinstance(entry.get("authority_ceiling"), str):
                raise ValueError("each skill must have string id and authority_ceiling")
            skill_id, ceiling = entry["id"], entry["authority_ceiling"]
            if skill_id in parsed_ceilings:
                raise ValueError(f"duplicate skill id {skill_id!r}")
            if SKILL_CEILING_EQUIVALENTS.get(ceiling, ceiling) not in rank:
                raise ValueError(f"unknown skill ceiling {ceiling!r}")
            parsed_ceilings[skill_id] = ceiling
        skill_ceilings = parsed_ceilings
    except Exception as exc:  # noqa: BLE001
        fail("SKILL_REGISTRY_INVALID", f"skills/registry.json: {exc}")

    agents_dir = root / "agents"
    agent_dirs = sorted(path for path in agents_dir.iterdir() if path.is_dir()) if agents_dir.is_dir() else []
    entries_on_disk: dict[str, dict[str, Any]] = {}
    discovered_manifests: set[str] = set()

    for agent_dir in agent_dirs:
        manifest_path = agent_dir / "agent.yaml"
        rel = manifest_path.relative_to(root).as_posix()
        if _manifest_is_symlink(root, manifest_path):
            discovered_manifests.add(rel)
            fail("AGENT_SOURCE_SYMLINK", f"{rel}: agent source must be a regular file, not a symlink")
            continue
        if not manifest_path.is_file():
            fail("AGENT_MANIFEST_MISSING", rel)
            continue
        discovered_manifests.add(rel)
        try:
            payload = read_bytes(manifest_path)
            manifest = load_agent_yaml(payload)
        except Exception as exc:  # noqa: BLE001
            fail("AGENT_PARSE_FAILURE", f"{rel}: {exc}")
            continue

        if manifest_validator is None or len(schemas) != 3 or not vocabulary_valid:
            fail("AGENT_SCHEMA", f"{rel}: required schemas unavailable")
            continue
        try:
            schema_errors = _schema_errors(manifest_validator, manifest)
        except Exception as exc:  # noqa: BLE001 - unresolved schemas fail closed
            fail("AGENT_SCHEMA", f"{rel}: {exc}")
            continue
        for message in schema_errors:
            fail("AGENT_SCHEMA", f"{rel}: {message}")
        if schema_errors:
            continue

        metadata = manifest.get("metadata") if isinstance(manifest.get("metadata"), dict) else {}
        authority = manifest.get("authority") if isinstance(manifest.get("authority"), dict) else {}
        agent_id = metadata.get("id")
        status = metadata.get("status")
        ceiling = authority.get("ceiling")

        if agent_id != f"{AGENT_ID_PREFIX}{agent_dir.name}":
            fail("AGENT_ID_DRIFT", f"{rel}: metadata.id {agent_id!r} does not match folder {agent_dir.name!r}")

        prohibited = authority.get("prohibited") if isinstance(authority.get("prohibited"), list) else []
        missing_prohibited = sorted(protected_actions - set(prohibited))
        if missing_prohibited:
            fail("AGENT_PROHIBITED_INCOMPLETE", f"{rel}: protected actions not prohibited: {missing_prohibited}")

        skills = manifest.get("skills") if isinstance(manifest.get("skills"), list) else []
        for skill_ref in skills:
            skill_id = skill_ref[len(SKILL_ID_PREFIX):] if isinstance(skill_ref, str) and skill_ref.startswith(SKILL_ID_PREFIX) else skill_ref
            if isinstance(skill_id, str) and skill_id.startswith(DISTILLED_PREFIX):
                fail("AGENT_DISTILLED_SKILL", f"{rel}: auto-distilled skill may not be bound: {skill_ref}")
                continue
            if skill_id not in skill_ceilings:
                fail("AGENT_UNKNOWN_SKILL", f"{rel}: {skill_ref} is not in skills/registry.json")
                continue
            skill_ceiling = SKILL_CEILING_EQUIVALENTS.get(skill_ceilings[skill_id], skill_ceilings[skill_id])
            if skill_ceiling not in rank or ceiling not in rank:
                fail("AGENT_CEILING_UNKNOWN", f"{rel}: cannot rank {ceiling!r} against {skill_ref} ceiling {skill_ceiling!r}")
            elif rank[skill_ceiling] > rank[ceiling]:
                fail("AGENT_SKILL_CEILING_EXCEEDS_AGENT", f"{rel}: {skill_ref} ceiling {skill_ceiling} exceeds agent ceiling {ceiling}")

        trigger = manifest.get("trigger_contract") if isinstance(manifest.get("trigger_contract"), dict) else {}
        if len(skills) > 1 and trigger.get("collision_behavior") != "block":
            fail("AGENT_COLLISION_FAIL_OPEN", f"{rel}: multiple skills require trigger_contract.collision_behavior: block")

        refs: list[Any] = [authority.get("admission_policy_ref")]
        for key in ("inputs", "outputs"):
            binding = manifest.get(key)
            refs.append(binding.get("schema_ref") if isinstance(binding, dict) else None)
        refs.extend(trigger.get("evidence_refs") or [])
        refs.extend(manifest.get("eval_refs", []))
        for block in ("admission", "rights_review"):
            if isinstance(manifest.get(block), dict):
                refs.extend(manifest[block].get("evidence_refs", []))
        observability = manifest.get("observability", {})
        refs.extend(observability.get("benchmark_refs", []))
        # Metrics are output destinations, not existing admission evidence.
        for ref in observability.get("ci_metrics_refs", []):
            if _repo_file(root, ref) is None:
                fail("AGENT_METRICS_PATH_INVALID", f"{rel}: unsafe metrics destination: {ref!r}")
        for ref in refs:
            if ref is None:
                continue
            target = _repo_file(root, ref)
            if not _is_file(target):
                fail("AGENT_REF_MISSING", f"{rel}: referenced file not found: {ref!r}")

        if not manifest.get("stop_conditions"):
            fail("AGENT_STOP_CONDITIONS_MISSING", f"{rel}: stop_conditions must be declared")

        admission = manifest.get("admission")
        if status == "active":
            if not isinstance(admission, dict):
                fail("AGENT_ADMISSION_MISSING", f"{rel}: active agent requires an admission record")
            elif not admission.get("evidence_refs"):
                fail("AGENT_ADMISSION_EVIDENCE_MISSING", f"{rel}: active agent admission requires evidence_refs")
        if isinstance(admission, dict):
            if re.fullmatch(r"(human|agent|service|system)\.[a-z0-9._-]+", admission["requested_by"]) is None:
                fail("AGENT_REQUESTER_INVALID", f"{rel}: requester must be a well-formed principal")
            if re.fullmatch(r"human\.[a-z0-9._-]+", admission["approved_by"]) is None:
                fail("AGENT_INDEPENDENT_APPROVAL_REQUIRED", f"{rel}: approval requires an independent human principal")
            if admission.get("requested_by") == admission.get("approved_by"):
                fail("AGENT_SELF_APPROVAL", f"{rel}: admission requested_by and approved_by must differ")
            granted = admission.get("granted_ceiling")
            if granted not in rank or ceiling not in rank:
                fail("AGENT_CEILING_UNKNOWN", f"{rel}: cannot rank ceiling {ceiling!r} against grant {granted!r}")
            elif rank[ceiling] > rank[granted]:
                fail("AGENT_CEILING_EXCEEDS_GRANT", f"{rel}: ceiling {ceiling} exceeds granted ceiling {granted}")
            if admission.get("evaluated_content_hash") != content_sha256(manifest):
                fail("AGENT_EVALUATED_HASH_MISMATCH", f"{rel}: admission.evaluated_content_hash does not match manifest content")

        domains = manifest.get("domains") if isinstance(manifest.get("domains"), list) else []
        if "data_productization" in domains:
            review = manifest.get("rights_review") if isinstance(manifest.get("rights_review"), dict) else {}
            if not (
                review.get("outcome") == "approved"
                and review.get("license_verified") is True
                and review.get("privacy_review") == "approved"
                and review.get("provenance_complete") is True
            ):
                fail("AGENT_RIGHTS_REVIEW_MISSING", f"{rel}: data_productization requires an approved rights review")

        entries_on_disk[str(agent_id)] = {
            "id": agent_id,
            "version": metadata.get("version"),
            "status": status,
            "authority_ceiling": ceiling,
            "manifest_path": rel,
            "source_blob_sha": git_blob_sha(payload),
            "manifest_sha256": manifest_sha256(manifest),
        }

    registry_path = agents_dir / "registry.json"
    registry_entries: dict[str, dict[str, Any]] = {}
    try:
        registry = json.loads(read_bytes(registry_path), object_pairs_hook=_unique_json_object)
        if registry_validator is None:
            raise ValueError("registry schema unavailable")
        registry_errors = _schema_errors(registry_validator, registry)
        for message in registry_errors:
            fail("REGISTRY_SCHEMA", f"agents/registry.json: {message}")
        if registry_errors:
            raise ValueError("registry semantics skipped after schema failure")
        if registry.get("status") != "candidate":
            fail("REGISTRY_AUTHORITY_BREACH", "agents/registry.json must remain candidate")
        if registry.get("digest_policy") != DIGEST_POLICY:
            fail("REGISTRY_DIGEST_POLICY_DRIFT", "agents/registry.json digest_policy does not match the validator")
        for entry in registry.get("agents", []):
            entry_id = str(entry.get("id"))
            if entry_id in registry_entries:
                fail("REGISTRY_DUPLICATE_AGENT", entry_id)
            registry_entries[entry_id] = entry
        if registry.get("registry_sha256") != registry_sha256(registry):
            fail("REGISTRY_DIGEST_FAILURE", "agents/registry.json registry_sha256 mismatch")
    except Exception as exc:  # noqa: BLE001
        fail("REGISTRY_INVALID", f"agents/registry.json: {exc}")

    for agent_id in sorted(set(entries_on_disk) - set(registry_entries)):
        fail("AGENT_UNREGISTERED", f"{agent_id}: agent folder is missing from agents/registry.json")
    validated_by_path = {entry["manifest_path"]: entry for entry in entries_on_disk.values()}
    for agent_id, entry in sorted(registry_entries.items()):
        if entry["manifest_path"] not in discovered_manifests:
            fail("REGISTRY_ORPHAN", f"{agent_id}: registered manifest is absent: {entry['manifest_path']}")
        elif entry["manifest_path"] in validated_by_path and validated_by_path[entry["manifest_path"]]["id"] != agent_id:
            fail("REGISTRY_MANIFEST_DRIFT", f"{agent_id}: registry ID does not match the referenced manifest")
    for agent_id in sorted(set(registry_entries) & set(entries_on_disk)):
        for key, expected in entries_on_disk[agent_id].items():
            if registry_entries[agent_id].get(key) != expected:
                fail("REGISTRY_MANIFEST_DRIFT", f"{agent_id}: registry {key} mismatch")

    elapsed = time.perf_counter() - started
    return {
        "api_version": "quirk.dev/agent-conformance/v1alpha1",
        "kind": "AgentConformanceReport",
        "status": "pass" if not findings else "fail",
        "evaluated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "agent_count": len(entries_on_disk),
        "manifest_digests": {agent_id: entry["manifest_sha256"] for agent_id, entry in sorted(entries_on_disk.items())},
        "findings": findings,
        "metrics": {
            "elapsed_seconds": round(elapsed, 6),
            "files_scanned": scanned["files"],
            "bytes_scanned": scanned["bytes"],
            "finding_count": len(findings),
        },
        "authority": {
            "admits_agents": False,
            "activates_agents": False,
            "projects_to_supabase": False,
            "promotes_canon": False,
            "meaning": "candidate-local structural conformance only; approval authenticity is not verified",
            "verifies_approval_authenticity": False,
        },
    }


def _step_summary(report: dict[str, Any]) -> str:
    metrics = report["metrics"]
    lines = [
        "## Quirk agent candidate conformance",
        "",
        f"- Status: **{report['status']}**",
        f"- Agents: {report['agent_count']}",
        f"- Findings: {metrics['finding_count']}",
        f"- Files scanned: {metrics['files_scanned']} ({metrics['bytes_scanned']} bytes)",
        f"- Elapsed: {metrics['elapsed_seconds']:.3f}s",
    ]
    if report["findings"]:
        lines += ["", "| Code | Message |", "| --- | --- |"]
        for finding in report["findings"]:
            message = finding["message"].replace("|", "\\|")
            lines.append(f"| `{finding['code']}` | {message} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the Quirk agent candidate layer.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--output", help="Write the JSON conformance report to this repository-relative path.")
    parser.add_argument("--metrics-output", help="Write elapsed time and workload metrics as JSON to this path.")
    parser.add_argument(
        "--write-step-summary",
        action="store_true",
        help="Append a Markdown summary to $GITHUB_STEP_SUMMARY when it is set.",
    )
    args = parser.parse_args(argv)

    root = Path(args.repo).resolve()
    report = validate_repository(root)

    if args.output:
        output = root / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.metrics_output:
        metrics_path = root / args.metrics_output
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_path.write_text(json.dumps(report["metrics"], indent=2) + "\n", encoding="utf-8")
    if args.write_step_summary and os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as handle:
            handle.write(_step_summary(report))

    if report["findings"]:
        for finding in report["findings"]:
            print(f"{finding['level'].upper()} {finding['code']}: {finding['message']}", file=sys.stderr)
        print(f"agent conformance failed: {len(report['findings'])} finding(s), {report['agent_count']} agent(s)", file=sys.stderr)
        return 1

    print(f"validated {report['agent_count']} candidate agent(s), manifest schema, registry integrity, skill bindings, and static admission-policy rules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
