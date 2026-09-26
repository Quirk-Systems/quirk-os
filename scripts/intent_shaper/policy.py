"""Deterministic contract policy for the Quirk Intent Shaper candidate.

This module does not generate personalized prose. It evaluates whether a proposed
Personalization Plan respects precedence, purpose boundaries, platform effects,
affordance discipline, and human authority.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Protocol

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
ADAPTATION_ACTIONS = {
    "propose_preference",
    "persist_preference",
    "update_memory",
    "change_settings",
    "write_canon",
}
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


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
    normalized = value.replace("Z", "+00:00")
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
        if not _is_active(item, as_of=as_of):
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

    return {
        "selected_refs": [item["ref"] for item in selected],
        "ignored_refs": [item["ref"] for item in ignored],
        "stored_retrieval": True,
        "conflicts": sorted(conflicts),
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
    return reasons


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
    current = [dict(item) for item in payload.get("current_request_preferences", [])]
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
        projection = {
            "preferences": [
                {
                    "dimension": item.get("dimension"),
                    "value": item.get("value"),
                    "source": item.get("source"),
                }
                for item in current
            ],
            "voice_profile_ref": None,
            "aesthetic_profile_ref": None,
            "persona_ref": None,
            "history_used": False,
        }
        return {
            "status": "accepted",
            "personalization_enabled": False,
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
        as_of=_parse_time(payload.get("as_of")) or datetime.now(timezone.utc),
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


def evaluate_case(case: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate one deterministic QIS fixture and return evidence."""

    operation = str(case["operation"])
    payload = deepcopy(case.get("input", {}))
    as_of = _parse_time(payload.get("as_of")) or datetime.now(timezone.utc)

    if operation == "resolve_preference":
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
        if len(weights) != len(selections) or round(sum(weights), 6) != 1.0:
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
