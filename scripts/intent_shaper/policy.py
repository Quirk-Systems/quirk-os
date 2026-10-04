"""Deterministic contract policy for the Quirk Intent Shaper candidate.

This module does not generate personalized prose. It evaluates whether a proposed
Personalization Plan respects precedence, purpose boundaries, platform effects,
affordance discipline, and human authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol

from jsonschema import Draft202012Validator, FormatChecker

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
SUPPORTED_RENDERERS = {"renderer.generated-ui.canonical-json.v1", "renderer.generated-ui.v1"}
ACCESSIBILITY_CHECKER_ID = "quirk.intent-shaper.manifest-contract-checker"
ACCESSIBILITY_CHECKER_VERSION = "1.0.0"


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
    if not isinstance(value, str):
        raise ValueError("date-time must be a string")
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


def _canonical_json_sha256(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _contained_json(path_ref: Any) -> tuple[Path, Any] | None:
    if not isinstance(path_ref, str) or not path_ref or Path(path_ref).is_absolute():
        return None
    root = REPO_ROOT.resolve()
    path = (root / path_ref).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        return None
    try:
        return path, json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def _generated_ui_schema_validator() -> Draft202012Validator:
    schema = json.loads((REPO_ROOT / "schemas/personalization-plan.schema.json").read_text(encoding="utf-8"))
    generated_ui_schema = {
        "$schema": schema["$schema"],
        "$defs": schema["$defs"],
        "$ref": "#/$defs/GeneratedUiPlan",
    }
    return Draft202012Validator(generated_ui_schema, format_checker=FormatChecker())


def _component_contract_errors(
    component: Mapping[str, Any],
    artifact: Any,
    semantic_fallback_ref: str,
) -> list[str]:
    if not isinstance(artifact, Mapping):
        return ["COMPONENT_MANIFEST_INACCESSIBLE"]
    schema = json.loads((REPO_ROOT / "schemas/personalization-plan.schema.json").read_text(encoding="utf-8"))
    artifact_schema = {
        "$schema": schema["$schema"],
        "$defs": schema["$defs"],
        "$ref": "#/$defs/ComponentArtifactManifest",
    }
    validator = Draft202012Validator(artifact_schema, format_checker=FormatChecker())
    if list(validator.iter_errors(artifact)):
        return ["COMPONENT_MANIFEST_INACCESSIBLE"]
    pinned_fields = ("component_id", "version", "data_bindings", "state_bindings", "user_actions")
    if any(component.get(key) != artifact.get(key) for key in pinned_fields):
        return ["COMPONENT_HASH_UNVERIFIABLE"]
    if artifact.get("semantic_fallback_ref") != semantic_fallback_ref:
        return ["SEMANTIC_FALLBACK_MISSING"]
    return []


def _accessibility_contract_checks(contract: Any) -> dict[str, bool]:
    if not isinstance(contract, Mapping):
        return {field: False for field in MACHINE_CHECK_FIELDS}

    focus_order = contract.get("focus_order")
    semantics = contract.get("screen_reader_semantics")
    focus_ids = set(focus_order) if isinstance(focus_order, list) and all(isinstance(item, str) for item in focus_order) else set()
    semantic_ids = {
        item.get("control_id")
        for item in semantics
        if isinstance(item, Mapping)
    } if isinstance(semantics, list) else set()
    contrast_pairs = contract.get("contrast_pairs")
    reduced_motion = contract.get("reduced_motion")
    errors = contract.get("errors")
    announcements = contract.get("status_announcements")
    reflow_zoom = contract.get("reflow_zoom")
    focus_indicator = contract.get("focus_indicator")

    return {
        "focus_order_declared": bool(focus_order) and len(focus_ids) == len(focus_order),
        "focus_visible_tokens": (
            isinstance(focus_indicator, Mapping)
            and isinstance(focus_indicator.get("style"), str)
            and bool(focus_indicator["style"])
            and isinstance(focus_indicator.get("contrast_ratio"), (int, float))
            and focus_indicator["contrast_ratio"] >= 3.0
        ),
        "screen_reader_semantics_declared": (
            isinstance(semantics, list)
            and bool(semantics)
            and focus_ids == semantic_ids
            and all(
                isinstance(item.get("role"), str)
                and bool(item["role"])
                and isinstance(item.get("accessible_name"), str)
                and bool(item["accessible_name"])
                for item in semantics
                if isinstance(item, Mapping)
            )
        ),
        "reflow_zoom_support_declared": (
            isinstance(reflow_zoom, Mapping)
            and isinstance(reflow_zoom.get("minimum_viewport_width"), int)
            and reflow_zoom.get("minimum_viewport_width") <= 320
            and reflow_zoom.get("zoom_supported") is True
        ),
        "contrast_tokens_verified": (
            isinstance(contrast_pairs, list)
            and bool(contrast_pairs)
            and all(isinstance(ratio, (int, float)) and ratio >= 4.5 for ratio in contrast_pairs)
        ),
        "reduced_motion_support_declared": (
            isinstance(reduced_motion, Mapping)
            and reduced_motion.get("prefers_reduced_motion") is True
            and reduced_motion.get("nonessential_animation_disabled") is True
        ),
        "errors_identifiable": (
            isinstance(errors, Mapping)
            and errors.get("associated_with_control") is True
            and errors.get("programmatically_identifiable") is True
        ),
        "status_announcements_mapped": (
            isinstance(announcements, Mapping)
            and announcements.get("role") in {"status", "alert"}
            and announcements.get("aria_live") in {"polite", "assertive"}
        ),
    }


def _verified_machine_checks(
    accessibility: Any,
    component_artifacts: list[tuple[Mapping[str, Any], str]],
    *,
    as_of: datetime,
) -> bool:
    if not isinstance(accessibility, Mapping):
        return False
    declarations = accessibility.get("machine_checks")
    if not isinstance(declarations, Mapping) or not component_artifacts:
        return False
    computed: dict[str, bool] = {field: True for field in MACHINE_CHECK_FIELDS}
    for component, _ in component_artifacts:
        component_checks = _accessibility_contract_checks(component.get("accessibility_contract"))
        computed = {field: computed[field] and component_checks[field] for field in MACHINE_CHECK_FIELDS}
        evidence = component.get("accessibility_evidence")
        if not isinstance(evidence, Mapping):
            return False
        loaded = _contained_json(evidence.get("evidence_ref"))
        expected_digest = evidence.get("content_hash_sha256")
        if loaded is None or not SHA256_RE.fullmatch(str(expected_digest or "")):
            return False
        _, receipt = loaded
        if not isinstance(receipt, Mapping):
            return False
        actual_digest = hashlib.sha256(
            json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        if actual_digest != expected_digest:
            return False
        if (
            receipt.get("checker_id") != ACCESSIBILITY_CHECKER_ID
            or receipt.get("checker_version") != ACCESSIBILITY_CHECKER_VERSION
            or receipt.get("component_id") != component.get("component_id")
            or receipt.get("component_version") != component.get("version")
            or receipt.get("component_manifest_sha256") != _component_core_sha256(component)
            or receipt.get("checks") != component_checks
        ):
            return False
        try:
            checked_at = _parse_time(receipt["checked_at"])
        except (KeyError, TypeError, ValueError):
            return False
        if checked_at is None or checked_at > as_of:
            return False
    return all(computed.values()) and all(declarations.get(field) is computed[field] for field in MACHINE_CHECK_FIELDS)


def _component_core_sha256(component: Mapping[str, Any]) -> str:
    core = {key: value for key, value in component.items() if key != "accessibility_evidence"}
    canonical = json.dumps(core, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _verified_manual_evidence(entry: Mapping[str, Any], requirement: str, as_of: datetime) -> bool:
    if entry.get("status") != "provided":
        return False
    evidence_ref = entry.get("evidence_ref")
    if not isinstance(evidence_ref, str) or not evidence_ref.startswith("evals/intent-shaper/manual-evidence/"):
        return False
    loaded = _contained_json(evidence_ref)
    expected_digest = entry.get("evidence_sha256")
    if loaded is None or not SHA256_RE.fullmatch(str(expected_digest or "")):
        return False
    _, artifact = loaded
    if not isinstance(artifact, Mapping):
        return False
    actual_digest = hashlib.sha256(
        json.dumps(artifact, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    if actual_digest != expected_digest:
        return False
    if artifact.get("requirement") != requirement or not isinstance(artifact.get("observation"), str):
        return False
    if not artifact["observation"].strip():
        return False
    reviewer = entry.get("reviewed_by")
    if artifact.get("reviewed_by") != reviewer or not isinstance(reviewer, str) or not reviewer.startswith("human.") or len(reviewer) <= 6:
        return False
    if artifact.get("reviewed_at") != entry.get("reviewed_at"):
        return False
    try:
        reviewed_at = _parse_time(artifact["reviewed_at"])
    except (KeyError, TypeError, ValueError):
        return False
    return reviewed_at is not None and reviewed_at <= as_of


def _reconstruction_hash(renderer_ref: Any, input_refs: Any) -> str | None:
    if not isinstance(renderer_ref, str) or renderer_ref not in SUPPORTED_RENDERERS:
        return None
    if not isinstance(input_refs, list) or not input_refs:
        return None
    inputs: list[dict[str, str]] = []
    aliases = {
        "input.intent": "examples/personalization-plan.valid.json",
        "input.preferences": "examples/personalization-plan.valid.json",
        "input.component.issue-intake-form": "skills/quirk-intent-shaper/generated-ui/issue-intake-form.json",
    }
    for ref in input_refs:
        resolved_ref = aliases.get(ref, ref) if isinstance(ref, str) else ref
        loaded = _contained_json(resolved_ref)
        if loaded is None:
            return None
        _, value = loaded
        if not isinstance(value, (Mapping, list)):
            return None
        canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        inputs.append({"ref": ref, "content_hash_sha256": hashlib.sha256(canonical).hexdigest()})
    preimage = {"renderer_ref": renderer_ref, "inputs": inputs}
    return hashlib.sha256(
        json.dumps(preimage, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _isoformat(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _manual_evidence_summary(entries: Any, *, as_of: datetime) -> dict[str, str]:
    summary = {requirement: "missing" for requirement in MANUAL_REQUIREMENTS}
    if not isinstance(entries, list):
        return summary
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        requirement = str(entry.get("requirement", ""))
        if requirement in summary and _verified_manual_evidence(entry, requirement, as_of):
            summary[requirement] = "provided"
    return summary


def _evaluate_generated_ui_gate(
    plan: Any,
    *,
    as_of: datetime,
    authority_ceiling: str = "propose",
) -> dict[str, Any]:
    candidate = dict(plan) if isinstance(plan, Mapping) else {}
    plan_id = str(candidate.get("plan_id") or "generated-ui.plan.missing")
    if not re.fullmatch(r"generated-ui\.plan\.[a-z0-9._-]+", plan_id):
        plan_id = "generated-ui.plan.invalid"
    semantic_fallback_ref = str(candidate.get("semantic_fallback_ref") or "missing://semantic-fallback")
    component_refs: list[str] = []
    reject_reasons: set[str] = set()

    if plan is None:
        reject_reasons.add("GENERATED_UI_PLAN_MISSING")
    elif not isinstance(plan, Mapping):
        reject_reasons.add("GENERATED_UI_PLAN_INVALID")
    else:
        try:
            plan_validator = _generated_ui_schema_validator()
            plan_errors = list(plan_validator.iter_errors(candidate))
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            plan_errors = [None]
        if plan_errors:
            reject_reasons.add("GENERATED_UI_PLAN_INVALID")

    components = candidate.get("component_manifests")
    if not isinstance(components, list) or not components:
        reject_reasons.add("COMPONENT_MANIFEST_MISSING")
        components = []

    component_artifacts: list[tuple[Mapping[str, Any], str]] = []
    authority_ranks = {"none": -1, "read_candidate": 0, "propose_reversible": 2}
    ceiling_ranks = {"observe": 0, "infer": 1, "propose": 2}
    ceiling_rank = ceiling_ranks.get(authority_ceiling)
    if ceiling_rank is None:
        reject_reasons.add("AUTHORITY_EXPANSION_REQUESTED")

    for component in components:
        if not isinstance(component, Mapping):
            reject_reasons.add("COMPONENT_MANIFEST_MISSING")
            continue
        component_id = str(component.get("component_id", ""))
        if re.fullmatch(r"component\.[a-z0-9._-]+", component_id):
            component_refs.append(component_id)

        version = str(component.get("version", ""))
        if not SEMVER_RE.fullmatch(version):
            reject_reasons.add("COMPONENT_VERSION_INVALID")

        manifest_ref = str(component.get("manifest_ref", ""))
        expected_hash = str(component.get("content_hash_sha256", ""))
        if not manifest_ref:
            reject_reasons.add("COMPONENT_MANIFEST_MISSING")
        else:
            loaded = _contained_json(manifest_ref)
            if loaded is None:
                reject_reasons.add("COMPONENT_MANIFEST_INACCESSIBLE")
            else:
                _, artifact = loaded
                try:
                    actual_hash = hashlib.sha256(
                        json.dumps(artifact, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                    ).hexdigest()
                except (TypeError, ValueError):
                    reject_reasons.add("COMPONENT_MANIFEST_INACCESSIBLE")
                else:
                    if not SHA256_RE.fullmatch(expected_hash) or actual_hash != expected_hash:
                        reject_reasons.add("COMPONENT_HASH_UNVERIFIABLE")
                    else:
                        errors = _component_contract_errors(component, artifact, semantic_fallback_ref)
                        reject_reasons.update(errors)
                        if not errors:
                            component_artifacts.append((artifact, actual_hash))
                if (
                    isinstance(artifact, Mapping)
                    and isinstance(artifact.get("component_id"), str)
                    and re.fullmatch(r"component\.[a-z0-9._-]+", artifact["component_id"])
                    and artifact["component_id"] not in component_refs
                ):
                    component_refs.append(str(artifact["component_id"]))

        actions = component.get("user_actions", [])
        if not isinstance(actions, list):
            reject_reasons.add("AUTHORITY_EXPANSION_REQUESTED")
            actions = []
        for action in actions:
            if not isinstance(action, Mapping):
                reject_reasons.add("AUTHORITY_EXPANSION_REQUESTED")
                continue
            effect = str(action.get("authority_effect"))
            if effect not in ALLOWED_AUTHORITY_EFFECTS or ceiling_rank is None or authority_ranks[effect] > ceiling_rank:
                reject_reasons.add("AUTHORITY_EXPANSION_REQUESTED")

    authority_effects = candidate.get("authority_effects")
    if not isinstance(authority_effects, list) or not authority_effects:
        reject_reasons.add("AUTHORITY_EXPANSION_REQUESTED")
    else:
        for effect in authority_effects:
            effect = str(effect)
            if effect not in ALLOWED_AUTHORITY_EFFECTS or ceiling_rank is None or authority_ranks[effect] > ceiling_rank:
                reject_reasons.add("AUTHORITY_EXPANSION_REQUESTED")

    if (
        not semantic_fallback_ref
        or semantic_fallback_ref == "missing://semantic-fallback"
        or any(
            artifact.get("semantic_fallback_ref") != semantic_fallback_ref
            for artifact, _ in component_artifacts
        )
    ):
        reject_reasons.add("SEMANTIC_FALLBACK_MISSING")

    reconstruction = candidate.get("reconstruction_contract")
    if not isinstance(reconstruction, Mapping):
        reject_reasons.add("RECONSTRUCTION_INPUTS_MISSING")
    else:
        input_refs = reconstruction.get("input_refs")
        replay_hash = str(reconstruction.get("replay_hash_sha256", ""))
        deterministic_renderer_ref = str(reconstruction.get("deterministic_renderer_ref", ""))
        computed_replay_hash = _reconstruction_hash(deterministic_renderer_ref, input_refs)
        if (
            computed_replay_hash is None
            or not SHA256_RE.fullmatch(replay_hash)
            or computed_replay_hash != replay_hash
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
    manual_evidence: Any = []
    if isinstance(accessibility, Mapping):
        manual_evidence = accessibility.get("manual_evidence", [])
    if not _verified_machine_checks(accessibility, component_artifacts, as_of=as_of):
        reject_reasons.add("ACCESSIBILITY_MACHINE_CHECK_FAILED")

    manual_summary = _manual_evidence_summary(manual_evidence, as_of=as_of)
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


def _generated_ui_receipt(
    plan_id: str,
    reject_reasons: set[str],
    component_refs: list[str],
    semantic_fallback_ref: str,
    manual_summary: dict[str, str],
    as_of: datetime,
) -> dict[str, Any]:
    return {
        "receipt_id": f"receipt.generated-ui.{plan_id.removeprefix('generated-ui.plan.')}",
        "plan_id": plan_id,
        "status": "rejected",
        "reason_codes": sorted(reject_reasons),
        "component_refs": sorted(set(component_refs)),
        "semantic_fallback_ref": semantic_fallback_ref,
        "runtime_authorized": False,
        "deployment_authorized": False,
        "manual_evidence_summary": manual_summary
        or {requirement: "missing" for requirement in MANUAL_REQUIREMENTS},
        "evaluated_at": _isoformat(as_of),
    }


def evaluate_case(case: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate one deterministic QIS fixture and return evidence."""

    operation = str(case["operation"])
    payload = deepcopy(case.get("input", {}))
    invalid_gate_time = False
    try:
        as_of = _parse_time(payload.get("as_of")) or (
            datetime.min.replace(tzinfo=timezone.utc)
            if operation == "generated_ui_gate"
            else datetime.now(timezone.utc)
        )
    except (TypeError, ValueError):
        if operation != "generated_ui_gate":
            raise
        as_of = datetime.min.replace(tzinfo=timezone.utc)
        invalid_gate_time = True

    if operation == "generated_ui_gate":
        plan = payload.get("generated_ui_plan")
        result = _evaluate_generated_ui_gate(
            plan,
            as_of=as_of,
            authority_ceiling=str(payload.get("authority_ceiling", "propose")),
        )
        if invalid_gate_time:
            result["status"] = "rejected"
            result["reason_codes"] = ["GENERATED_UI_PLAN_INVALID"]
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
