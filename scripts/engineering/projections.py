"""Candidate-only projections and local evaluation exports.

There is no network/provider client here. Callers separately own authentication,
authorization, source classification, minimization, and remote writes. The
validators below are bounded structural/secret heuristics, not authentication or
general DLP. Projections and comparisons cannot grant authority or admit a
candidate.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from datetime import datetime
from statistics import fmean
from typing import Any
from urllib.parse import urlsplit


CARD_FIELDS = frozenset({
    "record_id", "record_kind", "candidate_id", "run_id", "graph_node_id",
    "action_id", "evidence_id", "subject_key", "state", "platform",
    "external_id", "external_url", "source_refs", "evidence_refs", "outcome",
    "payload", "observed_at",
})
RECORD_KINDS = frozenset({"ACTION", "EVIDENCE", "BINDING"})
STATES = frozenset({
    "PROPOSED", "RUNNING", "OBSERVED", "SUCCEEDED", "FAILED", "BLOCKED",
    "SUPERSEDED",
})
PLATFORMS = frozenset({
    "GitHub", "Airtable", "Hugging Face", "Agent Ready", "Cloudflare",
    "Supabase", "Local",
})
PAYLOAD_FIELDS = frozenset({
    "schema_version", "summary", "operation", "outcome_code", "reason_codes",
    "metrics", "budget", "attempt", "duration_ms", "source_revision",
    "evaluator_digest", "synthetic", "public", "status",
})
METRIC_FIELDS = frozenset({
    "correct", "total", "passed", "failed", "score", "baseline", "candidate",
    "delta", "human_reconstruction_seconds", "authority_violations",
})
BUDGET_FIELDS = frozenset({
    "max_steps", "max_seconds", "max_spend", "max_actions", "max_resources",
    "max_bytes", "token_limit", "requests",
})
CASE_FIELDS = frozenset({
    "case_id", "split", "input", "expected", "evidence_class", "source_ref",
})
TRIAL_SET_FIELDS = frozenset({"evaluator_digest", "budget", "trials"})
TRIAL_FIELDS = frozenset({
    "case_id", "correct", "authority_violation", "human_trial_observed",
    "context_id", "manual_rescues", "observer_type", "observer_ref",
    "observation_ref", "human_reconstruction_seconds",
})
FORBIDDEN_AUTHORITY = re.compile(
    r"(?:^|_)(?:grant|granted|approval|approved|admission|admitted)(?:_|$)",
    re.IGNORECASE,
)
SENSITIVE_KEY = re.compile(
    r"(?:secret|token|password|passwd|api[_-]?key|authorization|cookie|"
    r"private[_-]?(?:key|content|source)|raw[_-]?(?:source|content))",
    re.IGNORECASE,
)
SENSITIVE_TEXT = re.compile(
    r"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|\bBearer\s+\S{8,}|"
    r"(?<![A-Za-z0-9])(?:sk-[A-Za-z0-9_-]{12,}|hf_[A-Za-z0-9]{12,}))",
    re.IGNORECASE,
)
HEX_256 = re.compile(r"^[a-f0-9]{64}$")


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("value must be finite JSON") from exc


def _reject_sensitive(value: Any, path: str = "value", *, depth: int = 0) -> None:
    if depth > 8:
        raise ValueError(f"{path} exceeds safe nesting depth")
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{path} contains a non-string key")
            if FORBIDDEN_AUTHORITY.search(key):
                raise ValueError(f"{path}.{key} is forbidden authority metadata")
            if SENSITIVE_KEY.search(key) and not (
                path == "payload.budget" and key == "token_limit"
            ):
                raise ValueError(f"{path}.{key} is sensitive or raw private content")
            _reject_sensitive(child, f"{path}.{key}", depth=depth + 1)
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _reject_sensitive(child, f"{path}[{index}]", depth=depth + 1)
    elif isinstance(value, str):
        if len(value) > 4096:
            raise ValueError(f"{path} exceeds safe text length")
        if SENSITIVE_TEXT.search(value):
            raise ValueError(f"{path} appears to contain a secret")


def _nonempty(value: Any, field: str, *, maximum: int = 2048) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonempty string")
    if len(value) > maximum:
        raise ValueError(f"{field} exceeds safe length")
    _reject_sensitive(value, field)
    return value


def _validate_json(value: Any, path: str = "value", *, depth: int = 0) -> None:
    if depth > 8:
        raise ValueError(f"{path} exceeds safe nesting depth")
    if value is None or isinstance(value, (str, bool, int)):
        if isinstance(value, str) and len(value) > 4096:
            raise ValueError(f"{path} exceeds safe text length")
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{path} must be finite")
        return
    if isinstance(value, list):
        if len(value) > 1000:
            raise ValueError(f"{path} contains too many values")
        for index, child in enumerate(value):
            _validate_json(child, f"{path}[{index}]", depth=depth + 1)
        return
    if isinstance(value, dict):
        if len(value) > 100:
            raise ValueError(f"{path} contains too many fields")
        for key, child in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{path} contains a non-string key")
            _validate_json(child, f"{path}.{key}", depth=depth + 1)
        return
    raise ValueError(f"{path} must contain JSON values only")


def _validate_ref_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    if len(value) > 100:
        raise ValueError(f"{field} contains too many references")
    result = []
    for index, item in enumerate(value):
        item = _nonempty(item, f"{field}[{index}]")
        _validate_reference(item, f"{field}[{index}]")
        result.append(item)
    return result


def _validate_reference(value: str, field: str,
                        *, allowed_schemes: set[str] | None = None) -> str:
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError(f"{field} contains control characters")
    parsed = urlsplit(value)
    if allowed_schemes is not None and parsed.scheme not in allowed_schemes:
        raise ValueError(f"{field} uses an unsupported scheme")
    if parsed.scheme and parsed.netloc and (
        parsed.username is not None or parsed.password is not None
    ):
        raise ValueError(f"{field} must not contain credentials")
    if parsed.query or parsed.fragment:
        raise ValueError(f"{field} must not contain a query or fragment")
    return value


def _validate_url(value: Any, field: str, *, allow_empty: bool) -> str:
    if value == "" and allow_empty:
        return ""
    value = _nonempty(value, field)
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{field} must be an http(s) URL")
    return _validate_reference(value, field, allowed_schemes={"http", "https"})


def _validate_time(value: Any, field: str) -> str:
    value = _nonempty(value, field, maximum=100)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be ISO8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone")
    return value


def _safe_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    unexpected = set(payload) - PAYLOAD_FIELDS
    if unexpected:
        raise ValueError(f"payload contains non-allowlisted fields: {sorted(unexpected)}")
    _reject_sensitive(payload, "payload")
    _validate_json(payload, "payload")
    for field in (
        "schema_version", "summary", "operation", "outcome_code",
        "source_revision", "status",
    ):
        if field in payload and not isinstance(payload[field], str):
            raise ValueError(f"payload.{field} must be a string")
    if "evaluator_digest" in payload:
        _validate_digest(payload["evaluator_digest"])
    for field in ("synthetic", "public"):
        if field in payload and type(payload[field]) is not bool:
            raise ValueError(f"payload.{field} must be boolean")
    if "attempt" in payload and (
        type(payload["attempt"]) is not int or payload["attempt"] < 0
    ):
        raise ValueError("payload.attempt must be a nonnegative integer")
    if "duration_ms" in payload and (
        isinstance(payload["duration_ms"], bool)
        or not isinstance(payload["duration_ms"], (int, float))
        or not math.isfinite(payload["duration_ms"])
        or payload["duration_ms"] < 0
    ):
        raise ValueError("payload.duration_ms must be finite and nonnegative")
    if "metrics" in payload:
        if not isinstance(payload["metrics"], dict):
            raise ValueError("payload.metrics must be an object")
        unexpected = set(payload["metrics"]) - METRIC_FIELDS
        if unexpected:
            raise ValueError(f"payload.metrics contains non-allowlisted fields: {sorted(unexpected)}")
        for field, value in payload["metrics"].items():
            if isinstance(value, bool):
                continue
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"payload.metrics.{field} must be finite numeric or boolean")
    if "budget" in payload:
        if not isinstance(payload["budget"], dict):
            raise ValueError("payload.budget must be an object")
        unexpected = set(payload["budget"]) - BUDGET_FIELDS
        if unexpected:
            raise ValueError(f"payload.budget contains non-allowlisted fields: {sorted(unexpected)}")
        _validate_budget(payload["budget"])
    if "reason_codes" in payload and (
        not isinstance(payload["reason_codes"], list)
        or len(payload["reason_codes"]) > 100
        or any(not isinstance(item, str) or not item or len(item) > 200
               for item in payload["reason_codes"])
    ):
        raise ValueError("payload.reason_codes must be a list of strings")
    return copy.deepcopy(payload)


def airtable_record(card: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Map a canonical candidate card to a write-ready Airtable record.

    The SHA-256 covers canonical JSON for the outer fields object before the hash
    field is added.
    """
    if not isinstance(card, dict):
        raise ValueError("card must be an object")
    forbidden = [key for key in card
                 if isinstance(key, str) and FORBIDDEN_AUTHORITY.search(key)]
    if forbidden:
        raise ValueError(f"forbidden authority fields: {sorted(forbidden)}")
    missing, extra = CARD_FIELDS - set(card), set(card) - CARD_FIELDS
    if missing or extra:
        raise ValueError(f"card fields mismatch: missing={sorted(missing)} extra={sorted(extra)}")
    for field in ("record_id", "candidate_id", "run_id", "graph_node_id",
                  "subject_key", "state", "platform"):
        _nonempty(card[field], field)
    if card["record_kind"] not in RECORD_KINDS:
        raise ValueError("record_kind must be ACTION, EVIDENCE, or BINDING")
    if card["state"] not in STATES:
        raise ValueError("state is outside the candidate projection lifecycle")
    if card["platform"] not in PLATFORMS:
        raise ValueError("platform is not allowlisted")
    for field in ("action_id", "evidence_id", "external_id"):
        if not isinstance(card[field], str):
            raise ValueError(f"{field} must be a string")
        _reject_sensitive(card[field], field)
    if card["record_kind"] == "ACTION":
        _nonempty(card["action_id"], "action_id")
    elif card["record_kind"] == "EVIDENCE":
        _nonempty(card["evidence_id"], "evidence_id")
    elif not card["external_id"] and not card["external_url"]:
        raise ValueError("binding requires external_id or external_url")
    source_refs = _validate_ref_list(card["source_refs"], "source_refs")
    evidence_refs = _validate_ref_list(card["evidence_refs"], "evidence_refs")
    external_url = _validate_url(card["external_url"], "external_url", allow_empty=True)
    if not isinstance(card["outcome"], str) or len(card["outcome"]) > 2000:
        raise ValueError("outcome must be a bounded string")
    _reject_sensitive(card["outcome"], "outcome")
    observed_at = _validate_time(card["observed_at"], "observed_at")
    payload = _safe_payload(card["payload"])
    fields: dict[str, Any] = {
        "Record ID": card["record_id"],
        "Record Kind": card["record_kind"],
        "Candidate ID": card["candidate_id"],
        "Loop Run ID": card["run_id"],
        "Graph Node ID": card["graph_node_id"],
        "Action ID": card["action_id"],
        "Evidence ID": card["evidence_id"],
        "Subject Key": card["subject_key"],
        "State": card["state"],
        "Platform": card["platform"],
        "External ID": card["external_id"],
        "External URL": external_url,
        "Source Refs JSON": _canonical_json(source_refs),
        "Evidence Refs JSON": _canonical_json(evidence_refs),
        "Outcome": card["outcome"],
        "Payload JSON": _canonical_json(payload),
        "Observed At": observed_at,
        "Authority Ceiling": "CANDIDATE_PREPARE",
        "Admission Effect": "none",
        "Projection Version": "1",
    }
    fields["Content SHA-256"] = hashlib.sha256(
        _canonical_json({"fields": fields}).encode("utf-8")
    ).hexdigest()
    return {"fields": fields}


def _validate_digest(value: Any) -> str:
    if not isinstance(value, str) or HEX_256.fullmatch(value) is None:
        raise ValueError("evaluator_digest must be a lowercase SHA-256 digest")
    return value


def export_evaluation_cases(cases: list[dict[str, Any]],
                            evaluator_digest: str) -> str:
    """Return deterministic local JSONL for explicit synthetic/public cases."""
    evaluator_digest = _validate_digest(evaluator_digest)
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases must be a nonempty list")
    rows, seen = [], set()
    required = {"case_id", "split", "input", "expected", "evidence_class"}
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("each case must be an object")
        forbidden = [key for key in case
                     if isinstance(key, str) and FORBIDDEN_AUTHORITY.search(key)]
        if forbidden:
            raise ValueError(f"forbidden authority fields: {sorted(forbidden)}")
        missing, extra = required - set(case), set(case) - CASE_FIELDS
        if missing or extra:
            raise ValueError(f"case fields mismatch: missing={sorted(missing)} extra={sorted(extra)}")
        case_id = _nonempty(case["case_id"], "case_id", maximum=200)
        if case_id in seen:
            raise ValueError("duplicate case_id")
        seen.add(case_id)
        if case["split"] not in {"capability", "regression", "heldout"}:
            raise ValueError("split must be capability, regression, or heldout")
        if case["evidence_class"] not in {"synthetic", "public"}:
            raise ValueError("evidence_class must explicitly be synthetic or public")
        _reject_sensitive(case["input"], f"{case_id}.input")
        _reject_sensitive(case["expected"], f"{case_id}.expected")
        _validate_json(case["input"], f"{case_id}.input")
        _validate_json(case["expected"], f"{case_id}.expected")
        source_ref = case.get("source_ref")
        if case["evidence_class"] == "public" and source_ref is None:
            raise ValueError("public cases require source_ref")
        if source_ref is not None:
            source_ref = _validate_url(source_ref, "source_ref", allow_empty=False)
        row = {
            "schema_version": "quirk-evaluation-case/v1",
            "case_id": case_id,
            "split": case["split"],
            "input": copy.deepcopy(case["input"]),
            "expected": copy.deepcopy(case["expected"]),
            "evaluation_metadata": {
                "authority_effect": "none",
                "evaluator_digest": evaluator_digest,
                "evidence_class": case["evidence_class"],
                "status": "candidate",
            },
        }
        if source_ref is not None:
            row["source_ref"] = source_ref
        rows.append(row)
    return "".join(_canonical_json(row) + "\n"
                   for row in sorted(rows, key=lambda row: row["case_id"]))


def _validate_budget(budget: Any) -> dict[str, float | int]:
    if not isinstance(budget, dict) or not budget:
        raise ValueError("budget must be a nonempty object")
    if set(budget) - BUDGET_FIELDS:
        raise ValueError("budget contains non-allowlisted fields")
    for name, value in budget.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"budget.{name} must be numeric")
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"budget.{name} must be finite and nonnegative")
    return copy.deepcopy(budget)


def _validate_trial_set(value: Any, expected_digest: str,
                        label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != TRIAL_SET_FIELDS:
        raise ValueError(f"{label} must contain evaluator_digest, budget, and trials")
    if value["evaluator_digest"] != expected_digest:
        raise ValueError(f"{label} evaluator_digest is not frozen")
    budget = _validate_budget(value["budget"])
    if not isinstance(value["trials"], list) or not value["trials"]:
        raise ValueError(f"{label}.trials must be a nonempty list")
    trials = {}
    required = {
        "case_id", "context_id", "correct", "authority_violation",
        "human_trial_observed", "manual_rescues",
    }
    for raw in value["trials"]:
        if not isinstance(raw, dict):
            raise ValueError(f"{label} trial must be an object")
        if required - set(raw) or set(raw) - TRIAL_FIELDS:
            raise ValueError(f"{label} trial fields are invalid")
        case_id = _nonempty(raw["case_id"], f"{label}.case_id", maximum=200)
        if case_id in trials:
            raise ValueError(f"{label} has duplicate case_id")
        if type(raw["correct"]) is not bool:
            raise ValueError(f"{label}.{case_id}.correct must be boolean")
        if type(raw["authority_violation"]) is not bool:
            raise ValueError(f"{label}.{case_id}.authority_violation must be boolean")
        if type(raw["human_trial_observed"]) is not bool:
            raise ValueError(f"{label}.{case_id}.human_trial_observed must be boolean")
        _nonempty(raw["context_id"], f"{label}.{case_id}.context_id", maximum=200)
        if type(raw["manual_rescues"]) is not int or raw["manual_rescues"] < 0:
            raise ValueError(f"{label}.{case_id}.manual_rescues must be a nonnegative integer")
        if raw["human_trial_observed"]:
            elapsed = raw.get("human_reconstruction_seconds")
            if raw.get("observer_type") != "human":
                raise ValueError(f"{label}.{case_id} is not an observed human trial")
            observer_ref = _nonempty(
                raw.get("observer_ref"), f"{label}.{case_id}.observer_ref", maximum=200
            )
            if not observer_ref.startswith("person.") or "@" in observer_ref:
                raise ValueError(f"{label}.{case_id}.observer_ref must be a person.* reference")
            observation_ref = _nonempty(
                raw.get("observation_ref"), f"{label}.{case_id}.observation_ref"
            )
            _validate_reference(
                observation_ref,
                f"{label}.{case_id}.observation_ref",
                allowed_schemes={"trial", "git", "http", "https"},
            )
            if (isinstance(elapsed, bool) or not isinstance(elapsed, (int, float))
                    or not math.isfinite(elapsed) or elapsed < 0):
                raise ValueError(f"{label}.{case_id} has invalid human reconstruction time")
        _reject_sensitive(raw, f"{label}.{case_id}")
        trials[case_id] = copy.deepcopy(raw)
    return {"budget": budget, "trials": trials}


def compare_trials(baseline: dict[str, Any], candidate: dict[str, Any],
                   evaluator_digest: str) -> dict[str, Any]:
    """Compare paired trials without admitting or authorizing the candidate."""
    evaluator_digest = _validate_digest(evaluator_digest)
    base = _validate_trial_set(baseline, evaluator_digest, "baseline")
    cand = _validate_trial_set(candidate, evaluator_digest, "candidate")
    if _canonical_json(base["budget"]) != _canonical_json(cand["budget"]):
        raise ValueError("baseline and candidate budgets must be equal")
    if set(base["trials"]) != set(cand["trials"]):
        raise ValueError("baseline and candidate must contain the same paired case IDs")
    case_ids = sorted(base["trials"])
    for key in case_ids:
        if base["trials"][key]["context_id"] != cand["trials"][key]["context_id"]:
            raise ValueError(f"paired case {key} must use the same context_id")
        if (
            base["trials"][key]["human_trial_observed"]
            and cand["trials"][key]["human_trial_observed"]
            and base["trials"][key]["observer_ref"] != cand["trials"][key]["observer_ref"]
        ):
            raise ValueError(f"paired case {key} must use the same observer_ref")
    baseline_correct = sum(base["trials"][key]["correct"] for key in case_ids)
    candidate_correct = sum(cand["trials"][key]["correct"] for key in case_ids)
    baseline_accuracy = baseline_correct / len(case_ids)
    candidate_accuracy = candidate_correct / len(case_ids)
    delta = candidate_accuracy - baseline_accuracy
    baseline_violations = sum(
        base["trials"][key]["authority_violation"] for key in case_ids)
    candidate_violations = sum(
        cand["trials"][key]["authority_violation"] for key in case_ids)
    observed_pairs = [
        key for key in case_ids
        if base["trials"][key]["human_trial_observed"]
        and cand["trials"][key]["human_trial_observed"]
    ]
    human_usefulness = None
    if observed_pairs:
        baseline_mean = fmean(float(base["trials"][key]["human_reconstruction_seconds"])
                              for key in observed_pairs)
        candidate_mean = fmean(float(cand["trials"][key]["human_reconstruction_seconds"])
                               for key in observed_pairs)
        reduction = baseline_mean - candidate_mean
        human_usefulness = {
            "observed_pair_count": len(observed_pairs),
            "baseline_mean_reconstruction_seconds": baseline_mean,
            "candidate_mean_reconstruction_seconds": candidate_mean,
            "mean_reduction_seconds": reduction,
            "mean_reduction_fraction": reduction / baseline_mean if baseline_mean else None,
            "baseline_manual_rescues": sum(
                base["trials"][key]["manual_rescues"] for key in observed_pairs
            ),
            "candidate_manual_rescues": sum(
                cand["trials"][key]["manual_rescues"] for key in observed_pairs
            ),
            "paired_context_ids": sorted({
                base["trials"][key]["context_id"] for key in observed_pairs
            }),
            "observation_refs": [
                {
                    "baseline": base["trials"][key]["observation_ref"],
                    "candidate": cand["trials"][key]["observation_ref"],
                    "case_id": key,
                    "observer_ref": base["trials"][key]["observer_ref"],
                }
                for key in observed_pairs
            ],
        }
    reason_codes = []
    if baseline_violations or candidate_violations:
        disposition = "candidate_rejected_authority_violation"
        reason_codes.append("AUTHORITY_VIOLATION")
    elif delta > 0:
        disposition = "candidate_improvement"
        reason_codes.append("CORRECTNESS_IMPROVED")
    elif delta < 0:
        disposition = "candidate_regression"
        reason_codes.append("CORRECTNESS_REGRESSED")
    elif human_usefulness and human_usefulness["mean_reduction_seconds"] > 0:
        disposition = "candidate_improvement"
        reason_codes.append("OBSERVED_HUMAN_RECONSTRUCTION_TIME_REDUCED")
    elif human_usefulness and human_usefulness["mean_reduction_seconds"] < 0:
        disposition = "candidate_regression"
        reason_codes.append("OBSERVED_HUMAN_RECONSTRUCTION_TIME_REGRESSED")
    else:
        disposition = "candidate_no_change"
        reason_codes.append("NO_OBSERVED_IMPROVEMENT")
    return {
        "status": "candidate",
        "disposition": disposition,
        "evaluator_digest": evaluator_digest,
        "paired_case_ids": case_ids,
        "budget": cand["budget"],
        "correctness": {
            "total": len(case_ids),
            "baseline_correct": baseline_correct,
            "candidate_correct": candidate_correct,
            "baseline_accuracy": baseline_accuracy,
            "candidate_accuracy": candidate_accuracy,
            "delta": delta,
        },
        "authority_violations": {
            "baseline": baseline_violations,
            "candidate": candidate_violations,
        },
        "human_usefulness": human_usefulness,
        "reason_codes": reason_codes,
        "auto_admission": False,
        "authority_effect": "none",
    }


def judgment_candidate(scope: str, comparison: dict[str, str],
                       source_ref: str, person: str) -> dict[str, Any]:
    """Create a minimal pairwise judgment candidate without accepting preference."""
    scope = _nonempty(scope, "scope", maximum=200)
    source_ref = _nonempty(source_ref, "source_ref")
    _validate_reference(
        source_ref, "source_ref", allowed_schemes={"trial", "git", "http", "https"}
    )
    person = _nonempty(person, "person", maximum=200)
    if not person.startswith("person.") or "@" in person:
        raise ValueError("person must be a pseudonymous person.* reference")
    if not isinstance(comparison, dict) or set(comparison) != {"left", "right"}:
        raise ValueError("comparison must contain only left and right")
    left = _nonempty(comparison["left"], "comparison.left", maximum=200)
    right = _nonempty(comparison["right"], "comparison.right", maximum=200)
    if left == right:
        raise ValueError("comparison endpoints must differ")
    identity = {
        "scope": scope,
        "comparison": {"left": left, "right": right},
        "source_ref": source_ref,
        "person": person,
    }
    return {
        "schema_version": "judgment-candidate/v1",
        "judgment_id": "judgment.candidate." + hashlib.sha256(
            _canonical_json(identity).encode("utf-8")).hexdigest()[:24],
        "status": "candidate",
        **identity,
        "accepted_preference": None,
        "authority_effect": "none",
    }
