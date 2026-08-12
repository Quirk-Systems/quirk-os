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
from pathlib import Path
import re
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

REPO_ROOT = Path(__file__).resolve().parents[2]
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
ALLOWED_AUTHORITY_EFFECTS = {"none", "read_candidate", "propose_reversible"}
MANUAL_REQUIREMENTS = (
    "keyboard",
    "focus_order_visibility",
    "screen_reader_semantics",
    "reflow_zoom",
    "contrast",
    "reduced_motion",
    "errors",
    "status_announcements",
)
MACHINE_CHECK_FIELDS = (
    "focus_order_declared",
    "focus_visible_tokens",
    "screen_reader_semantics_declared",
    "reflow_zoom_support_declared",
    "contrast_tokens_verified",
    "reduced_motion_support_declared",
    "errors_identifiable",
    "status_announcements_mapped",
)


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


def _canonical_json_sha256(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _isoformat(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _manual_evidence_summary(entries: Any) -> dict[str, str]:
    summary = {requirement: "missing" for requirement in MANUAL_REQUIREMENTS}
    if not isinstance(entries, list):
        return summary
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        requirement = str(entry.get("requirement", ""))
        if requirement in summary and entry.get("status") == "provided":
            summary[requirement] = "provided"
    return summary


def _evaluate_generated_ui_gate(plan: Mapping[str, Any] | None, *, as_of: datetime) -> dict[str, Any]:
    candidate = dict(plan or {})
    plan_id = str(candidate.get("plan_id") or "generated-ui.plan.missing")
    semantic_fallback_ref = str(candidate.get("semantic_fallback_ref") or "missing://semantic-fallback")
    component_refs: list[str] = []
    reject_reasons: set[str] = set()

    if not candidate:
        reject_reasons.add("GENERATED_UI_PLAN_MISSING")

    components = candidate.get("component_manifests")
    if not isinstance(components, list) or not components:
        reject_reasons.add("COMPONENT_MANIFEST_MISSING")
        components = []

    for component in components:
        if not isinstance(component, Mapping):
            reject_reasons.add("COMPONENT_MANIFEST_MISSING")
            continue
        component_id = str(component.get("component_id", ""))
        if component_id:
            component_refs.append(component_id)

        version = str(component.get("version", ""))
        if not SEMVER_RE.fullmatch(version):
            reject_reasons.add("COMPONENT_VERSION_INVALID")

        manifest_ref = str(component.get("manifest_ref", ""))
        expected_hash = str(component.get("content_hash_sha256", ""))
        if not manifest_ref:
            reject_reasons.add("COMPONENT_MANIFEST_MISSING")
        else:
            manifest_path = (REPO_ROOT / manifest_ref).resolve()
            if not manifest_path.is_file():
                reject_reasons.add("COMPONENT_MANIFEST_INACCESSIBLE")
            else:
                if not SHA256_RE.fullmatch(expected_hash):
                    reject_reasons.add("COMPONENT_HASH_UNVERIFIABLE")
                elif _canonical_json_sha256(manifest_path) != expected_hash:
                    reject_reasons.add("COMPONENT_HASH_UNVERIFIABLE")

        for action in component.get("user_actions", []):
            if not isinstance(action, Mapping):
                reject_reasons.add("AUTHORITY_EXPANSION_REQUESTED")
                continue
            if str(action.get("authority_effect")) not in ALLOWED_AUTHORITY_EFFECTS:
                reject_reasons.add("AUTHORITY_EXPANSION_REQUESTED")

    authority_effects = candidate.get("authority_effects")
    if not isinstance(authority_effects, list) or not authority_effects:
        reject_reasons.add("AUTHORITY_EXPANSION_REQUESTED")
    else:
        for effect in authority_effects:
            if str(effect) not in ALLOWED_AUTHORITY_EFFECTS:
                reject_reasons.add("AUTHORITY_EXPANSION_REQUESTED")

    if not semantic_fallback_ref or semantic_fallback_ref == "missing://semantic-fallback":
        reject_reasons.add("SEMANTIC_FALLBACK_MISSING")

    reconstruction = candidate.get("reconstruction_contract")
    if not isinstance(reconstruction, Mapping):
        reject_reasons.add("RECONSTRUCTION_INPUTS_MISSING")
    else:
        input_refs = reconstruction.get("input_refs")
        replay_hash = str(reconstruction.get("replay_hash_sha256", ""))
        deterministic_renderer_ref = str(reconstruction.get("deterministic_renderer_ref", ""))
        if not isinstance(input_refs, list) or not input_refs or not deterministic_renderer_ref or not SHA256_RE.fullmatch(
            replay_hash
        ):
            reject_reasons.add("RECONSTRUCTION_INPUTS_MISSING")

    freshness = candidate.get("freshness")
    valid_until = None
    if isinstance(freshness, Mapping):
        valid_until = _parse_time(str(freshness.get("valid_until"))) if freshness.get("valid_until") else None
    if valid_until is None or valid_until < as_of:
        reject_reasons.add("COMPONENT_MANIFEST_STALE")

    accessibility = candidate.get("accessibility")
    machine_checks: Mapping[str, Any] = {}
    manual_evidence: Any = []
    if isinstance(accessibility, Mapping):
        if isinstance(accessibility.get("machine_checks"), Mapping):
            machine_checks = accessibility["machine_checks"]
        manual_evidence = accessibility.get("manual_evidence", [])
    if any(machine_checks.get(field) is not True for field in MACHINE_CHECK_FIELDS):
        reject_reasons.add("ACCESSIBILITY_MACHINE_CHECK_FAILED")

    manual_summary = _manual_evidence_summary(manual_evidence)
    manual_missing = any(status != "provided" for status in manual_summary.values())

    if reject_reasons:
        status = "rejected"
        reason_codes = sorted(reject_reasons)
    elif manual_missing:
        status = "blocked_manual"
        reason_codes = ["MANUAL_EVIDENCE_MISSING"]
    else:
        status = "candidate_evidence_complete"
        reason_codes = ["CANDIDATE_EVIDENCE_COMPLETE"]

    return {
        "receipt_id": f"receipt.generated-ui.{plan_id.removeprefix('generated-ui.plan.')}",
        "plan_id": plan_id,
        "status": status,
        "reason_codes": reason_codes,
        "component_refs": sorted(set(component_refs)),
        "semantic_fallback_ref": semantic_fallback_ref,
        "runtime_authorized": False,
        "deployment_authorized": False,
        "manual_evidence_summary": manual_summary,
        "evaluated_at": _isoformat(as_of),
    }


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

    elif operation == "generated_ui_gate":
        result = _evaluate_generated_ui_gate(payload.get("generated_ui_plan"), as_of=as_of)

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
