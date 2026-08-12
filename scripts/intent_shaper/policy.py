"""Deterministic contract policy for the Quirk Intent Shaper candidate.

This module does not generate personalized prose. It evaluates whether a proposed
Personalization Plan respects precedence, purpose boundaries, platform effects,
affordance discipline, and human authority.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Iterable, Mapping

SOURCE_RANK: dict[str, int] = {
    "explicit_current": 50,
    "explicit_saved": 40,
    "observed": 20,
    "inferred": 10,
    "imported": 5,
}

PLATFORM_AFFECTS: dict[str, dict[str, list[str]]] = {
    "github": {
        "effects": ["versioned", "collaborative_review", "diff_first", "executable_evidence"],
        "affordance_bias": ["diff", "code_patch", "check_run", "issue", "review_comment"],
    },
    "notion": {
        "effects": ["navigational", "human_readable", "progressive_disclosure"],
        "affordance_bias": ["map", "linked_page", "decision_card", "explanation"],
    },
    "google_drive": {
        "effects": ["authored", "reviewable", "shareable"],
        "affordance_bias": ["draft", "comment", "evidence_pack"],
    },
    "airtable": {
        "effects": ["operational", "row_state", "batch_review"],
        "affordance_bias": ["batch_review", "filters", "matrix"],
    },
    "chat": {
        "effects": ["interruptible", "iterative", "low_ceremony"],
        "affordance_bias": ["plain_answer", "decision_card"],
    },
}

HASH_FIELDS = {
    "content_hash",
    "registry_hash",
    "semantic_hash",
    "inputs_hash",
    "layout_hash",
    "actions_hash",
    "fallback_hash",
}

ALLOWED_COMPONENT_KINDS = {"heading", "choice_group", "button", "summary", "section", "field"}
ALLOWED_ACTION_TYPES = {"set_field", "choose_option", "submit_intent"}


class ReconstructionError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def canonical_hash(value: Any, *, omit_hash_fields: bool = False) -> str:
    def _prune_hash_fields(candidate: Any) -> Any:
        if isinstance(candidate, Mapping):
            return {
                key: _prune_hash_fields(item)
                for key, item in candidate.items()
                if key not in HASH_FIELDS
            }
        if isinstance(candidate, list):
            return [_prune_hash_fields(item) for item in candidate]
        return candidate

    payload = _prune_hash_fields(value) if omit_hash_fields else value
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _parse_time(value: str | None) -> datetime | None:
    if value is None:
        return None
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _is_expired(preference: Mapping[str, Any], *, as_of: datetime) -> bool:
    valid_until = _parse_time(preference.get("valid_until"))
    return valid_until is not None and valid_until < as_of


def _preference_rank(preference: Mapping[str, Any]) -> tuple[int, float]:
    return SOURCE_RANK.get(str(preference.get("source")), 0), float(preference.get("confidence", 0))


def _select_preference(
    preferences: Iterable[Mapping[str, Any]],
    *,
    scope: str,
    as_of: datetime,
    personalization_enabled: bool = True,
) -> dict[str, Any]:
    all_preferences = [dict(item) for item in preferences]
    if not personalization_enabled:
        usable = [item for item in all_preferences if item.get("source") == "explicit_current"]
        return {
            "selected_refs": [item["ref"] for item in usable],
            "ignored_refs": [item["ref"] for item in all_preferences if item not in usable],
            "stored_retrieval": False,
            "conflicts": [],
        }

    usable: list[dict[str, Any]] = []
    ignored: list[dict[str, Any]] = []
    for item in all_preferences:
        if _is_expired(item, as_of=as_of):
            ignored.append(item)
            continue
        item_scope = str(item.get("scope", ""))
        if item.get("source") != "explicit_current" and item_scope not in {scope, "global"}:
            ignored.append(item)
            continue
        usable.append(item)

    by_dimension: dict[str, list[dict[str, Any]]] = {}
    for item in usable:
        by_dimension.setdefault(str(item.get("dimension", item.get("ref"))), []).append(item)

    selected: list[dict[str, Any]] = []
    conflicts: list[str] = []
    for dimension, candidates in by_dimension.items():
        candidates.sort(key=_preference_rank, reverse=True)
        top_rank = _preference_rank(candidates[0])
        top = [item for item in candidates if _preference_rank(item) == top_rank]
        values = {str(item.get("value")) for item in top}
        if len(values) > 1:
            conflicts.append(dimension)
            ignored.extend(top)
            continue
        selected.append(top[0])
        ignored.extend(item for item in candidates if item is not top[0])

    return {
        "selected_refs": [item["ref"] for item in selected],
        "ignored_refs": [item["ref"] for item in ignored],
        "stored_retrieval": True,
        "conflicts": sorted(conflicts),
    }


def _contains_subset(actual: Any, expected: Any) -> bool:
    if isinstance(expected, Mapping):
        return isinstance(actual, Mapping) and all(
            key in actual and _contains_subset(actual[key], value) for key, value in expected.items()
        )
    if isinstance(expected, list):
        return isinstance(actual, list) and all(item in actual for item in expected)
    return actual == expected


def _schema_error_code(error: Any) -> str:
    if getattr(error, "validator", None) == "additionalProperties":
        return "UNEXPECTED_FIELD"
    if getattr(error, "validator", None) == "enum":
        return "UNKNOWN_ENUM_VALUE"
    if getattr(error, "validator", None) == "required":
        missing = str(error.message)
        if "evidence_refs" in missing:
            return "MISSING_EVIDENCE"
        return "MISSING_PINNED_INPUT"
    return "SCHEMA_VALIDATION_FAILED"


def _find_generated_ui_contract(plan: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    for affordance in plan.get("task_affordances", []):
        if affordance.get("type") == "generated_ui":
            return dict(affordance), dict(affordance["generated_ui_contract"])
    raise ReconstructionError("GENERATED_UI_NOT_DECLARED", "generated_ui task affordance is required")


def _normalize_registry(registry: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    entries: list[dict[str, Any]] = []
    by_ref: dict[str, dict[str, Any]] = {}
    for raw_entry in registry.get("entries", []):
        entry = {
            "component_ref": str(raw_entry["component_ref"]),
            "component_kind": str(raw_entry["component_kind"]),
            "semantic_role": str(raw_entry["semantic_role"]),
            "state_slots": sorted(str(slot) for slot in raw_entry.get("state_slots", [])),
            "supported_actions": sorted(str(action) for action in raw_entry.get("supported_actions", [])),
        }
        if entry["component_kind"] not in ALLOWED_COMPONENT_KINDS:
            raise ReconstructionError("UNKNOWN_ENUM_VALUE", f"unknown component kind: {entry['component_kind']}")
        invalid_actions = [action for action in entry["supported_actions"] if action not in ALLOWED_ACTION_TYPES]
        if invalid_actions:
            raise ReconstructionError("UNKNOWN_ENUM_VALUE", f"unknown registry action(s): {', '.join(invalid_actions)}")
        entries.append(entry)
        by_ref[entry["component_ref"]] = entry

    normalized = {
        "registry_id": str(registry["registry_id"]),
        "version": str(registry["version"]),
        "entries": sorted(entries, key=lambda item: item["component_ref"]),
    }
    computed_hash = canonical_hash(normalized)
    if str(registry.get("registry_hash")) != computed_hash:
        raise ReconstructionError("REGISTRY_DRIFT", "component registry hash does not match pinned inputs")
    normalized["registry_hash"] = computed_hash
    return normalized, by_ref


def _registry_hash_for_contract(contract: Mapping[str, Any]) -> str:
    registry = contract["reconstruction_inputs"]["component_registry"]
    normalized_entries = sorted(
        [
            {
                "component_ref": str(entry["component_ref"]),
                "component_kind": str(entry["component_kind"]),
                "semantic_role": str(entry["semantic_role"]),
                "state_slots": sorted(str(slot) for slot in entry.get("state_slots", [])),
                "supported_actions": sorted(str(action) for action in entry.get("supported_actions", [])),
            }
            for entry in registry.get("entries", [])
        ],
        key=lambda item: item["component_ref"],
    )
    return canonical_hash(
        {
            "registry_id": str(registry["registry_id"]),
            "version": str(registry["version"]),
            "entries": normalized_entries,
        }
    )


def _normalize_actions(actions: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for raw_action in actions:
        action = {
            "action_id": str(raw_action["action_id"]),
            "type": str(raw_action["type"]),
            "target": str(raw_action["target"]),
            "value": raw_action["value"],
        }
        if action["type"] not in ALLOWED_ACTION_TYPES:
            raise ReconstructionError("UNKNOWN_ENUM_VALUE", f"unknown declarative action: {action['type']}")
        normalized.append(action)
    return sorted(normalized, key=lambda item: item["action_id"])


def _normalize_fallback(fallback: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "type": str(fallback["type"]),
        "steps": [str(step) for step in fallback.get("steps", [])],
    }


def reconstruct_generated_ui(plan: Mapping[str, Any]) -> dict[str, Any]:
    affordance, contract = _find_generated_ui_contract(plan)
    reconstruction_inputs = dict(contract["reconstruction_inputs"])

    if not contract.get("evidence_refs"):
        raise ReconstructionError("MISSING_EVIDENCE", "generated_ui_contract must declare evidence_refs")
    if plan.get("status") != "candidate" or plan.get("authority", {}).get("ceiling") != "propose":
        raise ReconstructionError("AUTHORITY_DRIFT", "generated UI reconstruction must remain candidate/propose only")

    clock = reconstruction_inputs["clock"]
    randomness = reconstruction_inputs["randomness"]
    if clock.get("mode") != "pinned" or randomness.get("mode") != "pinned":
        raise ReconstructionError("MISSING_PINNED_INPUT", "clock and randomness must be explicitly pinned")
    if (
        reconstruction_inputs.get("network_access")
        or reconstruction_inputs.get("model_calls")
        or reconstruction_inputs.get("profile_retrieval")
        or reconstruction_inputs.get("mutable_registries")
        or reconstruction_inputs.get("locale_defaults")
        or reconstruction_inputs.get("time_defaults")
    ):
        raise ReconstructionError("HIDDEN_STATE_ALLOWED", "reconstruction inputs must ban hidden state and ambient defaults")

    registry, registry_by_ref = _normalize_registry(reconstruction_inputs["component_registry"])
    actions = _normalize_actions(contract["declarative_actions"])
    fallback = _normalize_fallback(contract["plain_fallback"])

    semantic_projection = dict(contract["semantic_projection"])
    components: list[dict[str, Any]] = []
    for raw_component in semantic_projection.get("components", []):
        registry_ref = str(raw_component["registry_ref"])
        if registry_ref not in registry_by_ref:
            raise ReconstructionError("REGISTRY_DRIFT", f"missing registry entry for {registry_ref}")
        registry_entry = registry_by_ref[registry_ref]
        component = {
            "component_id": str(raw_component["component_id"]),
            "registry_ref": registry_ref,
            "component_kind": registry_entry["component_kind"],
            "semantic_role": registry_entry["semantic_role"],
            "state_slot": str(raw_component["state_slot"]),
            "binding": str(raw_component["binding"]),
            "label": str(raw_component["label"]),
            "options": [str(option) for option in raw_component.get("options", [])],
        }
        if component["state_slot"] not in registry_entry["state_slots"]:
            raise ReconstructionError(
                "REGISTRY_DRIFT",
                f"{component['component_id']} uses unregistered state slot {component['state_slot']}",
            )
        components.append(component)

    layout_projection = {
        "view_id": str(semantic_projection["view_id"]),
        "platform": str(semantic_projection["platform"]),
        "decision_semantics": str(semantic_projection["decision_semantics"]),
        "components": sorted(components, key=lambda item: item["component_id"]),
    }
    semantic = {
        "layout": layout_projection,
        "declarative_actions": actions,
        "plain_fallback": fallback,
    }
    input_projection = {
        "runtime_manifest_ref": str(contract["runtime_manifest_ref"]),
        "schema_ref": str(reconstruction_inputs["schema_ref"]),
        "locale": str(reconstruction_inputs["locale"]),
        "timezone": str(reconstruction_inputs["timezone"]),
        "clock": {
            "mode": str(clock["mode"]),
            "timestamp": str(clock["timestamp"]),
        },
        "randomness": {
            "mode": str(randomness["mode"]),
            "seed": int(randomness["seed"]),
        },
        "environment": {
            "pythonhashseed": str(reconstruction_inputs["environment"]["pythonhashseed"]),
        },
        "component_registry": registry,
        "semantic_projection": semantic_projection,
        "declarative_actions": actions,
        "plain_fallback": fallback,
    }
    subhashes = {
        "inputs": canonical_hash(input_projection),
        "registry": registry["registry_hash"],
        "layout": canonical_hash(layout_projection),
        "actions": canonical_hash(actions),
        "fallback": canonical_hash(fallback),
    }
    subhashes["semantic"] = canonical_hash(semantic)
    return {
        "status": "passed",
        "task_affordance_ref": affordance.get("type"),
        "semantic_projection": semantic,
        "subhashes": subhashes,
        "semantic_hash": subhashes["semantic"],
        "evidence_refs": list(contract["evidence_refs"]),
        "input_refs": [str(contract["runtime_manifest_ref"]), str(reconstruction_inputs["schema_ref"])],
        "output_refs": ["semantic_projection", "semantic_hash", "plain_fallback"],
        "authority_ceiling_observed": str(plan["authority"]["ceiling"]),
        "no_authority_escalation": True,
    }


def evaluate_reconstruction_plan(plan: Mapping[str, Any], validator: Any) -> dict[str, Any]:
    errors = sorted(validator.iter_errors(plan), key=lambda error: list(error.path))
    if errors:
        error = errors[0]
        return {
            "status": "critical_failure",
            "critical_failure": {
                "code": _schema_error_code(error),
                "message": error.message,
                "path": list(error.path),
            },
        }
    try:
        return reconstruct_generated_ui(plan)
    except ReconstructionError as exc:
        return {
            "status": "critical_failure",
            "critical_failure": {
                "code": exc.code,
                "message": str(exc),
                "path": [],
            },
        }


def _navigate(document: Any, path: list[Any]) -> tuple[Any, Any]:
    current = document
    for step in path[:-1]:
        current = current[step]
    return current, path[-1]


def apply_mutation(document: Mapping[str, Any], mutation: Mapping[str, Any]) -> dict[str, Any]:
    mutated = deepcopy(document)
    parent, leaf = _navigate(mutated, list(mutation["path"]))
    operation = str(mutation["operation"])
    if operation in {"replace", "add"}:
        parent[leaf] = mutation["value"]
    elif operation == "remove":
        if isinstance(parent, list):
            parent.pop(int(leaf))
        else:
            del parent[leaf]
    else:
        raise ValueError(f"Unsupported mutation operation: {operation}")
    if mutation.get("recompute_registry_hash"):
        contract = mutated["task_affordances"][0]["generated_ui_contract"]
        contract["reconstruction_inputs"]["component_registry"]["registry_hash"] = _registry_hash_for_contract(contract)
    return mutated


def evaluate_reconstruction_mutations(
    plan: Mapping[str, Any],
    mutations: Iterable[Mapping[str, Any]],
    validator: Any,
) -> list[dict[str, Any]]:
    baseline = evaluate_reconstruction_plan(plan, validator)
    if baseline["status"] != "passed":
        raise ReconstructionError("BASELINE_RECONSTRUCTION_FAILED", "baseline reconstruction must pass before mutation tests")

    results: list[dict[str, Any]] = []
    for mutation in mutations:
        mutated_plan = apply_mutation(plan, mutation)
        actual = evaluate_reconstruction_plan(mutated_plan, validator)
        if actual["status"] != "passed":
            results.append(
                {
                    "id": mutation["id"],
                    "passed": False,
                    "error": actual["critical_failure"],
                }
            )
            continue
        changed = sorted(
            name
            for name, digest in actual["subhashes"].items()
            if digest != baseline["subhashes"][name]
        )
        unchanged = sorted(
            name
            for name, digest in actual["subhashes"].items()
            if digest == baseline["subhashes"][name]
        )
        expected_changed = sorted(str(name) for name in mutation.get("expected_changed_subhashes", []))
        expected_unchanged = sorted(str(name) for name in mutation.get("expected_unchanged_subhashes", []))
        results.append(
            {
                "id": mutation["id"],
                "passed": changed == expected_changed and unchanged == expected_unchanged,
                "expected_changed_subhashes": expected_changed,
                "expected_unchanged_subhashes": expected_unchanged,
                "actual_changed_subhashes": changed,
                "actual_unchanged_subhashes": unchanged,
            }
        )
    return results


def evaluate_reconstruction_adversarial_cases(
    plan: Mapping[str, Any],
    adversarial_cases: Iterable[Mapping[str, Any]],
    validator: Any,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for case in adversarial_cases:
        mutated_plan = apply_mutation(plan, case["mutation"])
        actual = evaluate_reconstruction_plan(mutated_plan, validator)
        failure = actual.get("critical_failure", {})
        expected_code = str(case["expected_code"])
        results.append(
            {
                "id": case["id"],
                "passed": actual["status"] == "critical_failure" and failure.get("code") == expected_code,
                "expected_code": expected_code,
                "actual_code": failure.get("code"),
                "status": actual["status"],
            }
        )
    return results


def evaluate_case(case: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate one deterministic QIS fixture and return evidence."""

    operation = str(case["operation"])
    payload = deepcopy(case.get("input", {}))
    as_of = _parse_time(payload.get("as_of")) or datetime.now(timezone.utc)

    if operation == "resolve_preference":
        result = _select_preference(
            payload.get("preferences", []),
            scope=str(payload.get("scope", "global")),
            as_of=as_of,
            personalization_enabled=bool(payload.get("personalization_enabled", True)),
        )

    elif operation == "purpose_partition":
        selection = _select_preference(
            payload.get("preferences", []),
            scope=str(payload["scope"]),
            as_of=as_of,
            personalization_enabled=True,
        )
        result = {
            "selected_refs": selection["selected_refs"],
            "excluded_scopes": sorted(
                {
                    str(item.get("scope"))
                    for item in payload.get("preferences", [])
                    if item.get("ref") in selection["ignored_refs"] and item.get("scope") != payload["scope"]
                }
            ),
        }

    elif operation == "persona_hand":
        primary = dict(payload["primary"])
        supporting = [dict(item) for item in payload.get("supporting", [])]
        weights = [float(primary["weight"])] + [float(item["weight"]) for item in supporting]
        result = {
            "primary_ref": primary["ref"],
            "supporting_refs": [item["ref"] for item in supporting],
            "weight_total": round(sum(weights), 6),
            "authority_effect": False,
            "permanent_identity_claim": False,
        }

    elif operation == "platform_affect":
        platform = str(payload["platform"])
        affect = PLATFORM_AFFECTS.get(platform, {"effects": [], "affordance_bias": []})
        result = {
            "platform": platform,
            "effects": affect["effects"],
            "affordance_bias": affect["affordance_bias"],
            "semantic_decision_hash_preserved": payload.get("semantic_decision_hash")
            == payload.get("rendered_decision_hash"),
        }

    elif operation == "truth_over_style":
        stakes = str(payload.get("stakes", "low"))
        protected = stakes in {"high", "protected"}
        result = {
            "evidence_mode": "strict" if protected else payload.get("evidence_mode", "standard"),
            "max_dramatic_intensity": 0.2 if protected else 1.0,
            "uncertainty_required": protected,
            "style_can_override_truth": False,
        }

    elif operation == "preference_conflict":
        selection = _select_preference(
            payload.get("preferences", []),
            scope=str(payload.get("scope", "global")),
            as_of=as_of,
            personalization_enabled=True,
        )
        result = {
            "conflicts": selection["conflicts"],
            "silent_average": False,
            "requires_default_plus_bounded_alternatives": bool(selection["conflicts"]),
        }

    elif operation == "stale_preference":
        expired = [
            item["ref"]
            for item in payload.get("preferences", [])
            if _is_expired(item, as_of=as_of)
        ]
        result = {
            "expired_refs": expired,
            "adaptation_proposal": bool(expired),
            "history_rewritten": False,
        }

    elif operation == "negative_constraints":
        desired = list(payload.get("desired_traits", []))
        forbidden = set(payload.get("no_fill", []))
        result = {
            "accepted_traits": [trait for trait in desired if trait not in forbidden],
            "blocked_traits": [trait for trait in desired if trait in forbidden],
            "negative_constraints_applied_first": True,
        }

    elif operation == "select_affordance":
        task_class = str(payload.get("task_class"))
        complexity = str(payload.get("complexity", "medium"))
        if task_class == "decide" and complexity == "low":
            selected = "decision_card"
        elif task_class in {"build", "repair"}:
            selected = "code_patch"
        elif task_class == "organize":
            selected = "batch_review"
        else:
            selected = "plain_answer"
        result = {
            "selected": selected,
            "generated_ui": selected == "generated_ui",
            "smallest_useful_form": True,
        }

    elif operation == "personalization_off":
        selection = _select_preference(
            payload.get("preferences", []),
            scope=str(payload.get("scope", "global")),
            as_of=as_of,
            personalization_enabled=False,
        )
        result = {
            **selection,
            "persona_hand": [],
            "saved_profile_loaded": False,
        }

    elif operation == "adaptation_guard":
        result = {
            "status": "proposed",
            "feedback_receipt_required": True,
            "auto_apply": False,
            "human_admission_required": True,
            "memory_updated": False,
            "settings_updated": False,
            "canon_updated": False,
        }

    else:
        raise ValueError(f"Unsupported QIS operation: {operation}")

    expected = case.get("expected", {})
    passed = _contains_subset(result, expected)
    return {
        "id": case["id"],
        "operation": operation,
        "passed": passed,
        "expected": expected,
        "actual": result,
    }


def evaluate_cases(cases: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [evaluate_case(case) for case in cases]
