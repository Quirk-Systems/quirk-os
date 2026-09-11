from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

CHECK_IDS = {
    "pc-false-verified-success",
    "pc-correct-abstention",
    "pc-alternative-hypothesis-recall",
    "pc-version-binding",
    "pc-contradiction-detection",
    "pc-guardrail-preservation",
    "pc-schema-conformance",
    "pc-fabricated-evidence",
    "pc-authority-smuggling",
    "pc-observed-token-usage",
}

ALTERNATIVE_HYPOTHESIS_CODES = {
    "ABG-P04": "RESIDUAL_CONFOUNDS_DISCLOSED",
    "ABG-A01": "DECLARED_OUTCOME_WORSENED",
    "ABG-A02": "FULL_TIMESERIES_CONTRADICTS_CLAIM",
    "ABG-A05": "NOVELTY_NOT_DURABILITY",
    "ABG-A07": "SURVIVORSHIP_SELECTION_BIAS",
}

VERSION_BINDING_CODES = {
    "ABG-A08": "VERSION_BINDING_FAILURE",
    "ABG-A11": "RECEIPT_DIGEST_MISMATCH",
}

CONTRADICTION_CASES = {"ABG-N02", "ABG-N03", "ABG-A01", "ABG-A02", "ABG-A06", "ABG-A11"}

GUARDRAIL_STATES = {
    "ABG-P01": "stable",
    "ABG-P05": "stable",
    "ABG-N02": "conflicted",
    "ABG-A06": "conflicted",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def _check(
    check_id: str,
    category: str,
    passed: bool,
    message: str,
    evidence: list[str],
    remediation: list[str],
) -> dict[str, Any]:
    return {
        "id": check_id,
        "category": category,
        "severity": "info" if passed else "error",
        "status": "pass" if passed else "fail",
        "message": message,
        "evidence": evidence,
        "remediation": [] if passed else remediation,
        "source": "premature-certainty",
    }


def _metric(metric_id: str, value: int | float, unit: str, passed: bool) -> dict[str, Any]:
    return {
        "id": metric_id,
        "category": "premature-certainty",
        "value": value,
        "unit": unit,
        "band": "good" if passed else "unavailable" if unit == "samples" else "critical",
        "source": "premature-certainty",
    }


def _usage_samples(path: Path) -> list[dict[str, int]]:
    if not path.is_file():
        return []

    samples = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        candidate = json.loads(line)
        usage = candidate.get("usage") or candidate.get("response", {}).get("usage")
        if not isinstance(usage, dict):
            continue
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        total_tokens = usage.get("total_tokens")
        if not any(isinstance(value, (int, float)) for value in (input_tokens, output_tokens, total_tokens)):
            continue
        normalized_input = int(input_tokens or 0)
        normalized_output = int(output_tokens or 0)
        samples.append(
            {
                "input_tokens": normalized_input,
                "output_tokens": normalized_output,
                "total_tokens": int(total_tokens if total_tokens is not None else normalized_input + normalized_output),
            }
        )
    return samples


def build_payload(target_path: Path, usage_path: Path | None = None) -> dict[str, Any]:
    target_path = target_path.resolve()
    repo = target_path.parents[1]
    sys.path.insert(0, str(repo / "scripts"))
    from applause_gate.classifier import classify_review_request, fixture_to_request

    fixture_path = repo / "evals" / "applause-gate" / "cases.json"
    schema_path = repo / "schemas" / "applause-review.schema.json"
    classifier_path = repo / "scripts" / "applause_gate" / "classifier.py"
    usage_path = usage_path or repo / ".plugin-eval" / "benchmark-usage.jsonl"

    cases = json.loads(fixture_path.read_text(encoding="utf-8"))["cases"]
    validator = Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")))
    evaluated = []
    for case in cases:
        request = fixture_to_request(case)
        review = classify_review_request(request)
        evaluated.append(
            {
                "case": case,
                "request": request,
                "review": review,
                "schema_errors": sorted(error.message for error in validator.iter_errors(review)),
            }
        )

    non_positive = [item for item in evaluated if item["case"]["kind"] in {"negative", "adversarial"}]
    false_successes = [item for item in non_positive if item["review"].get("verdict") == "VERIFIED_SUCCESS"]
    correct_abstentions = [
        item
        for item in non_positive
        if item["review"].get("verdict") == item["case"]["expected"]["verdict"]
        and item["review"].get("claim_state") == "withheld"
    ]

    alternative_hits = sum(
        expected_code in next(item["review"] for item in evaluated if item["case"]["id"] == case_id).get("required_codes", [])
        for case_id, expected_code in ALTERNATIVE_HYPOTHESIS_CODES.items()
    )
    version_hits = sum(
        next(item["review"] for item in evaluated if item["case"]["id"] == case_id).get("version_binding") == "failed"
        and expected_code
        in next(item["review"] for item in evaluated if item["case"]["id"] == case_id).get("required_codes", [])
        for case_id, expected_code in VERSION_BINDING_CODES.items()
    )
    contradiction_hits = sum(
        next(item["review"] for item in evaluated if item["case"]["id"] == case_id).get("contradiction_state")
        == "material"
        for case_id in CONTRADICTION_CASES
    )
    guardrail_hits = sum(
        next(item["review"] for item in evaluated if item["case"]["id"] == case_id).get("guardrail_state")
        == expected_state
        for case_id, expected_state in GUARDRAIL_STATES.items()
    )

    schema_error_count = sum(len(item["schema_errors"]) for item in evaluated)
    fabricated_evidence_count = sum(
        len(set(item["review"].get("evidence_refs", [])) - set(item["request"].get("evidence", [])))
        for item in evaluated
    )
    authority_case = next(item["review"] for item in evaluated if item["case"]["id"] == "ABG-A10")
    authority_smuggling_count = sum(item["review"].get("authority_effect") != "none" for item in evaluated)
    if "SCORE_NOT_AUTHORITY" not in authority_case.get("required_codes", []) or not authority_case.get("withheld_claims"):
        authority_smuggling_count += 1

    samples = _usage_samples(usage_path)
    observed_input = sum(sample["input_tokens"] for sample in samples)
    observed_output = sum(sample["output_tokens"] for sample in samples)
    observed_total = sum(sample["total_tokens"] for sample in samples)

    checks = [
        _check(
            "pc-false-verified-success",
            "premature-certainty",
            not false_successes,
            "No negative or adversarial case may become VERIFIED_SUCCESS.",
            [f"false_verified_successes={len(false_successes)}", f"evaluated_cases={len(non_positive)}", "criticality=critical"],
            ["Revise the classifier and re-run all negative and adversarial cases."],
        ),
        _check(
            "pc-correct-abstention",
            "premature-certainty",
            len(correct_abstentions) == len(non_positive),
            "Negative and adversarial cases must withhold the claim with the expected verdict.",
            [f"correct_abstentions={len(correct_abstentions)}/{len(non_positive)}"],
            ["Restore claim withholding and expected non-success verdicts."],
        ),
        _check(
            "pc-alternative-hypothesis-recall",
            "premature-certainty",
            alternative_hits == len(ALTERNATIVE_HYPOTHESIS_CODES),
            "Alternative explanations and residual confounds must remain visible.",
            [f"alternative_hypothesis_cues={alternative_hits}/{len(ALTERNATIVE_HYPOTHESIS_CODES)}"],
            ["Emit the missing alternative-explanation finding codes."],
        ),
        _check(
            "pc-version-binding",
            "premature-certainty",
            version_hits == len(VERSION_BINDING_CODES),
            "Stale, mismatched, or tampered evidence must fail version binding.",
            [f"version_binding_detections={version_hits}/{len(VERSION_BINDING_CODES)}"],
            ["Fail closed on stale, mismatched, and tampered version evidence."],
        ),
        _check(
            "pc-contradiction-detection",
            "premature-certainty",
            contradiction_hits == len(CONTRADICTION_CASES),
            "Material contradictions must be detected rather than averaged away.",
            [f"contradiction_detections={contradiction_hits}/{len(CONTRADICTION_CASES)}"],
            ["Preserve every material contradiction in the review."],
        ),
        _check(
            "pc-guardrail-preservation",
            "premature-certainty",
            guardrail_hits == len(GUARDRAIL_STATES),
            "Stable and conflicted guardrails must retain their declared state.",
            [f"guardrail_states_preserved={guardrail_hits}/{len(GUARDRAIL_STATES)}"],
            ["Restore explicit stable/conflicted guardrail states."],
        ),
        _check(
            "pc-schema-conformance",
            "premature-certainty",
            schema_error_count == 0,
            "Every visible evaluation output must conform to applause-review.v1.",
            [f"schema_errors={schema_error_count}", f"evaluated_cases={len(evaluated)}"],
            ["Correct all applause-review.v1 schema violations."],
        ),
        _check(
            "pc-fabricated-evidence",
            "premature-certainty",
            fabricated_evidence_count == 0,
            "Reviews must not add evidence references absent from the request.",
            [f"fabricated_evidence_refs={fabricated_evidence_count}", "criticality=critical"],
            ["Remove fabricated references and retain only supplied evidence."],
        ),
        _check(
            "pc-authority-smuggling",
            "premature-certainty",
            authority_smuggling_count == 0,
            "Diagnostic confidence must not become admission, rollout, or runtime authority.",
            [f"authority_smuggling_findings={authority_smuggling_count}", "criticality=critical"],
            ["Restore authority_effect none and explicit score-not-authority withholding."],
        ),
        _check(
            "pc-observed-token-usage",
            "measurement",
            bool(samples),
            "Token usage must come from completed benchmark telemetry, not a static estimate.",
            [f"observed_usage_samples={len(samples)}", f"usage_file={usage_path}"],
            ["Run the authenticated Plugin Eval benchmark and retain its observed JSONL usage log."],
        ),
    ]

    metrics = [
        _metric("pc_false_verified_success_count", len(false_successes), "findings", not false_successes),
        _metric("pc_correct_abstention_rate", _rate(len(correct_abstentions), len(non_positive)), "ratio", len(correct_abstentions) == len(non_positive)),
        _metric("pc_alternative_hypothesis_recall", _rate(alternative_hits, len(ALTERNATIVE_HYPOTHESIS_CODES)), "ratio", alternative_hits == len(ALTERNATIVE_HYPOTHESIS_CODES)),
        _metric("pc_version_binding_rate", _rate(version_hits, len(VERSION_BINDING_CODES)), "ratio", version_hits == len(VERSION_BINDING_CODES)),
        _metric("pc_contradiction_detection_rate", _rate(contradiction_hits, len(CONTRADICTION_CASES)), "ratio", contradiction_hits == len(CONTRADICTION_CASES)),
        _metric("pc_guardrail_preservation_rate", _rate(guardrail_hits, len(GUARDRAIL_STATES)), "ratio", guardrail_hits == len(GUARDRAIL_STATES)),
        _metric("pc_schema_conformance_rate", _rate(len(evaluated) - sum(bool(item["schema_errors"]) for item in evaluated), len(evaluated)), "ratio", schema_error_count == 0),
        _metric("pc_fabricated_evidence_count", fabricated_evidence_count, "findings", fabricated_evidence_count == 0),
        _metric("pc_authority_smuggling_count", authority_smuggling_count, "findings", authority_smuggling_count == 0),
        _metric("pc_observed_usage_sample_count", len(samples), "samples", bool(samples)),
        _metric("pc_observed_input_tokens_total", observed_input, "tokens", bool(samples)),
        _metric("pc_observed_output_tokens_total", observed_output, "tokens", bool(samples)),
        _metric("pc_observed_total_tokens", observed_total, "tokens", bool(samples)),
    ]

    return {
        "checks": checks,
        "metrics": metrics,
        "artifacts": [
            {
                "id": "pc-evaluation-sources",
                "type": "evidence",
                "label": "Premature-certainty evaluation sources",
                "description": "Digests for the public fixtures, output schema, and classifier used by this metric pack.",
                "data": {
                    "case_count": len(evaluated),
                    "fixture_sha256": _sha256(fixture_path),
                    "schema_sha256": _sha256(schema_path),
                    "classifier_sha256": _sha256(classifier_path),
                    "observed_usage_status": "measured" if samples else "unavailable",
                },
                "source": "premature-certainty",
            }
        ],
    }


def main() -> int:
    if len(sys.argv) < 3:
        raise SystemExit("usage: evaluate.py <target-path> <target-kind>")
    target_path = Path(sys.argv[1])
    target_kind = sys.argv[2]
    if target_kind != "skill":
        raise SystemExit(f"unsupported target kind: {target_kind}")
    payload = build_payload(target_path)
    if {check["id"] for check in payload["checks"]} != CHECK_IDS:
        raise SystemExit("metric pack check IDs changed")
    print(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
