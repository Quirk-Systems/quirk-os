"""Deterministic contract policy for the Quirk Intent Shaper candidate.

This module does not generate personalized prose. It evaluates whether a proposed
Personalization Plan respects precedence, purpose boundaries, platform effects,
affordance discipline, and human authority.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol

from jsonschema import FormatChecker

SOURCE_RANK: dict[str, int] = {
    "explicit_current": 50,
    "purpose_scoped_setting": 45,
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
    "vercel": {
        "effects": ["deploy_preview", "versioned", "environment_bound"],
        "affordance_bias": ["diff", "check_run", "deployment_preview"],
    },
    "cloudflare": {
        "effects": ["edge_runtime", "cache_aware", "environment_bound"],
        "affordance_bias": ["diff", "check_run", "configuration"],
    },
    "email": {
        "effects": ["asynchronous", "forwardable", "context_limited"],
        "affordance_bias": ["plain_answer", "decision_card", "checklist"],
    },
    "voice": {
        "effects": ["linear", "interruptible", "transient"],
        "affordance_bias": ["plain_answer", "checklist"],
    },
    "mobile": {
        "effects": ["small_screen", "touch_first", "interruption_prone"],
        "affordance_bias": ["plain_answer", "decision_card", "checklist"],
    },
    "web": {
        "effects": ["responsive", "linkable", "progressive_disclosure"],
        "affordance_bias": ["plain_answer", "map", "timeline"],
    },
    "music": {
        "effects": ["time_based", "performance_bound", "multimodal"],
        "affordance_bias": ["timeline", "draft", "checklist"],
    },
    "code": {
        "effects": ["executable", "versioned", "testable"],
        "affordance_bias": ["code_patch", "diff", "check_run"],
    },
    "other": {
        "effects": ["explicit_constraints_required"],
        "affordance_bias": ["plain_answer"],
    },
}

PERSONA_BASES = {
    "explicit_current",
    "explicit_saved",
    "declared_function",
    "inferred_nonsensitive",
}
PERSONA_CLAIM_MARKERS = {
    "sensitive_inference_rejected": {
        "biometric",
        "disability",
        "ethnicity",
        "health",
        "medical",
        "political",
        "race",
        "religion",
        "sensitive",
        "sexual",
    },
    "identity_claim_rejected": {"identity", "permanent"},
    "authority_claim_rejected": {"authority"},
    "impersonation_rejected": {"impersonat"},
}
ADAPTATION_ACTIONS = {
    "propose_preference",
    "persist_preference",
    "update_memory",
    "change_settings",
    "write_canon",
}
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")

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


class PersonalizationEvidencePort(Protocol):
    """Boundary for evidence that personalization-off must never read."""

    trace: list[str]

    def read_preferences(self, scope: str) -> list[dict[str, Any]]: ...

    def read_profile(self, scope: str) -> dict[str, Any] | None: ...

    def read_persona(self, scope: str) -> dict[str, Any] | None: ...

    def read_history(self, scope: str) -> list[dict[str, Any]]: ...


class RecordingEvidencePort:
    """Deterministic test adapter that records every protected read."""

    def __init__(self, evidence: Mapping[str, Any] | None = None) -> None:
        self._evidence = deepcopy(dict(evidence or {}))
        self.trace: list[str] = []

    def _read(self, kind: str, default: Any) -> Any:
        self.trace.append(kind)
        return deepcopy(self._evidence.get(kind, default))

    def read_preferences(self, scope: str) -> list[dict[str, Any]]:
        del scope
        return self._read("preferences", [])

    def read_profile(self, scope: str) -> dict[str, Any] | None:
        del scope
        return self._read("profile", None)

    def read_persona(self, scope: str) -> dict[str, Any] | None:
        del scope
        return self._read("persona", None)

    def read_history(self, scope: str) -> list[dict[str, Any]]:
        del scope
        return self._read("history", [])


class FailOnReadEvidencePort(RecordingEvidencePort):
    """Sentinel proving that a disabled path crosses no protected boundary."""

    def __init__(self) -> None:
        # Deliberately accept and materialize no protected evidence. The only
        # way this adapter can observe protected state is through a read call,
        # which then fails below.
        self.trace: list[str] = []

    def _read(self, kind: str, default: Any) -> Any:
        del default
        self.trace.append(kind)
        raise RuntimeError(f"protected personalization read attempted: {kind}")


def _parse_time(value: str | None) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str) or not FormatChecker().conforms(value, "date-time"):
        raise ValueError("date-time must use RFC 3339 syntax")
    normalized = value[:-1] + "+00:00" if value.endswith(("Z", "z")) else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("date-time must include an RFC 3339 offset")
    return parsed


def _is_expired(preference: Mapping[str, Any], *, as_of: datetime) -> bool:
    valid_until = _parse_time(preference.get("valid_until"))
    return valid_until is not None and valid_until < as_of


def _is_active(preference: Mapping[str, Any], *, as_of: datetime) -> bool:
    valid_from = _parse_time(preference.get("valid_from"))
    return (valid_from is None or valid_from <= as_of) and not _is_expired(preference, as_of=as_of)


def _preference_rank(preference: Mapping[str, Any]) -> tuple[int, float]:
    source = str(preference.get("source"))
    if source not in SOURCE_RANK:
        raise ValueError(f"Unsupported preference source: {source}")
    return SOURCE_RANK[source], float(preference.get("confidence", 0))


def _canonical_value(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _resolve_preferences(
    preferences: Iterable[Mapping[str, Any]],
    *,
    scope: str,
    as_of: datetime,
    personalization_enabled: bool = True,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    all_preferences = [dict(item) for item in preferences]
    usable: list[dict[str, Any]] = []
    ignored: list[dict[str, Any]] = []
    for item in all_preferences:
        if not personalization_enabled and item.get("source") != "explicit_current":
            ignored.append(item)
            continue
        if not _is_active(item, as_of=as_of):
            ignored.append(item)
            continue
        item_scope = str(item.get("scope", ""))
        if item_scope not in {scope, "global"}:
            ignored.append(item)
            continue
        usable.append(item)

    by_dimension: dict[str, list[dict[str, Any]]] = {}
    for item in usable:
        by_dimension.setdefault(str(item.get("dimension", item.get("ref"))), []).append(item)

    selected: list[dict[str, Any]] = []
    conflicts: list[str] = []
    for dimension, candidates in by_dimension.items():
        candidates.sort(
            key=lambda item: (
                _preference_rank(item)[0],
                _preference_rank(item)[1],
                str(item.get("ref")),
            ),
            reverse=True,
        )
        winning_source_rank = _preference_rank(candidates[0])[0]
        top = [item for item in candidates if _preference_rank(item)[0] == winning_source_rank]
        values = {_canonical_value(item.get("value")) for item in top}
        if len(values) > 1:
            conflicts.append(dimension)
            ignored.extend(candidates)
            continue
        selected.append(top[0])
        ignored.extend(item for item in candidates if item is not top[0])

    return selected, ignored, sorted(conflicts)


def _select_preference(
    preferences: Iterable[Mapping[str, Any]],
    *,
    scope: str,
    as_of: datetime,
    personalization_enabled: bool = True,
) -> dict[str, Any]:
    selected, ignored, conflicts = _resolve_preferences(
        preferences, scope=scope, as_of=as_of,
        personalization_enabled=personalization_enabled,
    )
    return {
        "selected_refs": [item["ref"] for item in selected],
        "ignored_refs": [item["ref"] for item in ignored],
        "stored_retrieval": personalization_enabled,
        "conflicts": conflicts,
    }


def _matches_expected(actual: Any, expected: Any) -> bool:
    if isinstance(expected, Mapping):
        return isinstance(actual, Mapping) and all(
            key in actual and _matches_expected(actual[key], value) for key, value in expected.items()
        )
    if isinstance(expected, list):
        return (
            isinstance(actual, list)
            and len(actual) == len(expected)
            and all(_matches_expected(actual_item, expected_item) for actual_item, expected_item in zip(actual, expected))
        )
    return actual == expected


def _persona_rejection_reasons(selection: Mapping[str, Any]) -> list[str]:
    allowed_fields = {
        "ref",
        "role",
        "weight",
        "selection_basis",
        "sensitive_inference",
        "impersonates_user",
        "consent_ref",
    }
    reasons: list[str] = []
    unexpected = sorted(set(selection) - allowed_fields)
    if unexpected:
        reasons.append(f"unexpected_fields:{','.join(unexpected)}")
    if not isinstance(selection.get("ref"), str) or not selection.get("ref"):
        reasons.append("invalid_ref")
    if not isinstance(selection.get("role"), str) or not selection.get("role"):
        reasons.append("invalid_role")
    weight = selection.get("weight")
    if type(weight) not in {int, float} or not 0 <= weight <= 1:
        reasons.append("invalid_weight")
    if selection.get("selection_basis") not in PERSONA_BASES:
        reasons.append("unsupported_selection_basis")
    if selection.get("sensitive_inference") is not False:
        reasons.append("sensitive_inference_rejected")
    if selection.get("impersonates_user") is not False:
        reasons.append("impersonation_rejected")
    claim_tokens = set(
        re.findall(
            r"[a-z0-9]+",
            " ".join(str(selection.get(field, "")) for field in ("ref", "role")).casefold(),
        )
    )
    for reason, markers in PERSONA_CLAIM_MARKERS.items():
        if any(
            token == marker or (marker == "impersonat" and token.startswith(marker))
            for token in claim_tokens
            for marker in markers
        ):
            reasons.append(reason)
    return reasons


def _normalized_persona_weights(selections: Iterable[Mapping[str, Any]]) -> bool:
    weights = [selection.get("weight") for selection in selections]
    return (
        bool(weights)
        and all(type(weight) in {int, float} and 0 <= weight <= 1 for weight in weights)
        and math.isclose(math.fsum(weights), 1.0, rel_tol=0, abs_tol=1e-9)
    )


def validate_plan_policy(plan: Mapping[str, Any]) -> list[str]:
    """Check relational invariants after the plan passes its canonical schema.

    JSON Schema validates individual weights and timestamp formats; this policy
    checks their aggregate and whether selected evidence applies when the plan
    was created. Disabled plans have an empty hand enforced by the schema.
    """

    errors: list[str] = []
    if plan["settings"]["personalization_enabled"]:
        hand = plan["persona_hand"]
        primary = hand["primary"]
        selections = ([primary] if primary is not None else []) + hand["supporting"]
        if not _normalized_persona_weights(selections):
            errors.append("persona_hand:invalid_weight_total")
    as_of = _parse_time(plan["created_at"])
    scope = plan["purpose_partition"]["scope_key"]
    excluded_scopes = set(plan["purpose_partition"].get("excluded_scopes", []))
    for index, preference in enumerate(plan["preferences"]):
        if preference["decision"] != "use":
            continue
        if preference["scope"] not in {scope, "global"} or preference["scope"] in excluded_scopes:
            errors.append(f"preferences/{index}:purpose_scope_mismatch")
        if not _is_active(preference, as_of=as_of):
            errors.append(f"preferences/{index}:inactive_preference")
    return errors


def _feedback_binding(payload: Mapping[str, Any]) -> tuple[bool, str | None]:
    receipt = payload.get("feedback_receipt")
    proposal_ref = payload.get("adaptation_proposal_ref")
    if not isinstance(receipt, Mapping):
        return False, "feedback_receipt_missing"
    required = {"receipt_ref", "receipt_digest", "immutable", "proposal_ref"}
    if set(receipt) != required:
        return False, "feedback_receipt_shape_invalid"
    if receipt.get("immutable") is not True:
        return False, "feedback_receipt_not_immutable"
    if not isinstance(receipt.get("receipt_ref"), str) or not receipt["receipt_ref"]:
        return False, "feedback_receipt_ref_invalid"
    digest = receipt.get("receipt_digest")
    if not isinstance(digest, str) or not SHA256_PATTERN.fullmatch(digest):
        return False, "feedback_receipt_digest_invalid"
    if not isinstance(proposal_ref, str) or not proposal_ref:
        return False, "adaptation_proposal_missing"
    if receipt.get("proposal_ref") != proposal_ref:
        return False, "feedback_receipt_proposal_mismatch"
    return True, None


def evaluate_personalization_boundary(
    payload: Mapping[str, Any],
    evidence_port: PersonalizationEvidencePort,
) -> dict[str, Any]:
    """Prove off mode exits before any saved/profile/persona/history read."""

    settings = payload.get("settings")
    if not isinstance(settings, Mapping):
        return {"status": "rejected", "reason_code": "settings_missing", "read_trace": list(evidence_port.trace)}

    enabled_setting = settings.get("personalization_enabled")
    if not isinstance(enabled_setting, bool):
        return {
            "status": "rejected",
            "reason_code": "personalization_setting_invalid",
            "read_trace": list(evidence_port.trace),
        }

    scope = str(payload.get("scope", "global"))
    current_input = payload.get("current_request_preferences", [])
    current_valid = isinstance(current_input, list)
    if current_valid:
        for item in current_input:
            if (not isinstance(item, Mapping)
                    or any(not isinstance(item.get(key), str) or not item[key]
                           for key in ("ref", "dimension", "scope", "source"))
                    or item["source"] not in SOURCE_RANK
                    or type(item.get("confidence")) not in {int, float}
                    or not 0 <= item["confidence"] <= 1
                    or not math.isfinite(item["confidence"])
                    or "value" not in item):
                current_valid = False
                break
            try:
                json.dumps(item["value"], sort_keys=True, allow_nan=False)
            except (TypeError, ValueError):
                current_valid = False
                break
    if not current_valid:
        return {
            "status": "rejected",
            "reason_code": "current_preference_invalid",
            "read_trace": list(evidence_port.trace),
        }
    current = [dict(item) for item in current_input]
    try:
        as_of = _parse_time(payload.get("as_of")) or datetime.now(timezone.utc)
        for item in current:
            _parse_time(item.get("valid_from"))
            _parse_time(item.get("valid_until"))
    except (AttributeError, TypeError, ValueError):
        return {
            "status": "rejected",
            "reason_code": "current_preference_timestamp_invalid",
            "read_trace": list(evidence_port.trace),
        }
    enabled = enabled_setting
    if not enabled:
        if settings.get("adaptation_mode") != "off" or settings.get("implicit_signal_use") != "off":
            return {
                "status": "rejected",
                "reason_code": "off_mode_settings_conflict",
                "read_trace": list(evidence_port.trace),
            }
        if any(item.get("source") != "explicit_current" for item in current):
            return {
                "status": "rejected",
                "reason_code": "off_mode_noncurrent_evidence",
                "read_trace": list(evidence_port.trace),
            }
        selected, ignored, conflicts = _resolve_preferences(
            current,
            scope=scope,
            as_of=as_of,
            personalization_enabled=False,
        )
        if conflicts:
            return {
                "status": "rejected",
                "reason_code": "current_instruction_conflict",
                "conflicts": conflicts,
                "read_trace": list(evidence_port.trace),
            }
        projection = {
            "preferences": [
                {
                    "dimension": item.get("dimension"),
                    "value": item.get("value"),
                    "source": item.get("source"),
                }
                for item in selected
            ],
            "voice_profile_ref": None,
            "aesthetic_profile_ref": None,
            "persona_ref": None,
            "history_used": False,
        }
        return {
            "status": "accepted",
            "personalization_enabled": False,
            "ignored_refs": [item["ref"] for item in ignored],
            "read_trace": list(evidence_port.trace),
            "protected_projection": projection,
        }

    saved = evidence_port.read_preferences(scope)
    profile = evidence_port.read_profile(scope)
    persona = evidence_port.read_persona(scope)
    history = evidence_port.read_history(scope)
    selection = _select_preference(
        [*current, *saved],
        scope=scope,
        as_of=as_of,
        personalization_enabled=True,
    )
    return {
        "status": "accepted",
        "personalization_enabled": True,
        "read_trace": list(evidence_port.trace),
        "selected_refs": selection["selected_refs"],
        "profile_loaded": profile is not None,
        "persona_loaded": persona is not None,
        "history_items": len(history),
    }


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
            if not manifest_path.is_relative_to(REPO_ROOT.resolve()) or not manifest_path.is_file():
                reject_reasons.add("COMPONENT_MANIFEST_INACCESSIBLE")
            else:
                try:
                    actual_hash = _canonical_json_sha256(manifest_path)
                except (OSError, ValueError, TypeError):
                    reject_reasons.add("COMPONENT_MANIFEST_INACCESSIBLE")
                else:
                    if not SHA256_RE.fullmatch(expected_hash) or actual_hash != expected_hash:
                        reject_reasons.add("COMPONENT_HASH_UNVERIFIABLE")

        actions = component.get("user_actions", [])
        if not isinstance(actions, list):
            reject_reasons.add("AUTHORITY_EXPANSION_REQUESTED")
            actions = []
        for action in actions:
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
        try:
            valid_until = _parse_time(str(freshness.get("valid_until"))) if freshness.get("valid_until") else None
        except (TypeError, ValueError):
            valid_until = None
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
    # The boundary owns timestamp validation and its structured rejection.
    as_of = None if operation == "personalization_boundary" else (
        _parse_time(payload.get("as_of")) or datetime.now(timezone.utc)
    )

    if operation == "generated_ui_gate":
        plan = payload.get("generated_ui_plan")
        result = _evaluate_generated_ui_gate(plan if isinstance(plan, Mapping) else None, as_of=as_of)
    elif operation == "resolve_preference":
        enabled = payload.get("personalization_enabled", True)
        if not isinstance(enabled, bool):
            result = {"status": "rejected", "reason_code": "personalization_setting_invalid"}
        else:
            result = _select_preference(
                payload.get("preferences", []),
                scope=str(payload.get("scope", "global")),
                as_of=as_of,
                personalization_enabled=enabled,
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
        rejection_reasons = [
            reason
            for selection in [primary, *supporting]
            for reason in _persona_rejection_reasons(selection)
        ]
        selections = [primary, *supporting]
        weights = [
            float(selection["weight"])
            for selection in selections
            if type(selection.get("weight")) in {int, float}
        ]
        if not _normalized_persona_weights(selections):
            rejection_reasons.append("invalid_weight_total")
        if rejection_reasons:
            result = {
                "status": "rejected",
                "rejection_reasons": sorted(set(rejection_reasons)),
                "primary_ref": None,
                "supporting_refs": [],
                "authority_effect": False,
                "permanent_identity_claim": False,
            }
        else:
            result = {
                "status": "accepted",
                "primary_ref": primary["ref"],
                "supporting_refs": [item["ref"] for item in supporting],
                "weight_total": round(sum(weights), 6),
                "authority_effect": False,
                "permanent_identity_claim": False,
            }

    elif operation == "platform_affect":
        platform = str(payload["platform"])
        affect = PLATFORM_AFFECTS.get(platform)
        if affect is None:
            result = {
                "status": "rejected",
                "platform": platform,
                "reason_code": "unsupported_platform",
            }
        else:
            result = {
                "status": "accepted",
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
            "ignored_refs": selection["ignored_refs"],
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

    elif operation == "personalization_boundary":
        adapter_mode = payload.get("adapter_mode", "recording")
        if adapter_mode == "fail_on_read":
            evidence_port: PersonalizationEvidencePort = FailOnReadEvidencePort()
        elif adapter_mode == "recording":
            evidence_port = RecordingEvidencePort(payload.get("stored_evidence"))
        else:
            result = {"status": "rejected", "reason_code": "unknown_adapter_mode", "read_trace": []}
            evidence_port = None  # type: ignore[assignment]
        if evidence_port is not None:
            try:
                result = evaluate_personalization_boundary(payload, evidence_port)
            except RuntimeError:
                result = {
                    "status": "rejected",
                    "reason_code": "protected_read_attempted",
                    "read_trace": list(evidence_port.trace),
                }

    elif operation == "adaptation_guard":
        requested_action = str(payload.get("requested_action", ""))
        binding_valid, binding_error = _feedback_binding(payload)
        if requested_action not in ADAPTATION_ACTIONS:
            status = "rejected"
            reason_code = "unknown_requested_action"
        elif not binding_valid:
            status = "blocked"
            reason_code = binding_error
        elif requested_action == "propose_preference":
            status = "proposed"
            reason_code = None
        else:
            status = "blocked"
            reason_code = "human_admission_required"
        result = {
            "status": status,
            "reason_code": reason_code,
            "requested_action": requested_action,
            "repeated_successes": int(payload.get("repeated_successes", 0)),
            "feedback_receipt_required": True,
            "feedback_receipt_verified": binding_valid,
            "adaptation_proposal_ref": payload.get("adaptation_proposal_ref"),
            "admission_present": bool(payload.get("admission_ref")),
            "auto_apply": False,
            "human_admission_required": requested_action != "propose_preference",
            "memory_updated": False,
            "settings_updated": False,
            "canon_updated": False,
        }

    else:
        raise ValueError(f"Unsupported QIS operation: {operation}")

    expected = case.get("expected", {})
    passed = _matches_expected(result, expected)
    return {
        "id": case["id"],
        "operation": operation,
        "passed": passed,
        "expected": expected,
        "actual": result,
    }


def evaluate_cases(cases: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [evaluate_case(case) for case in cases]
