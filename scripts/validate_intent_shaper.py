#!/usr/bin/env python3
"""Validate the Quirk Intent Shaper candidate contracts and fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator, FormatChecker
import yaml

from intent_shaper.policy import SOURCE_RANK, evaluate_cases


REQUIRED_INVARIANTS = {
    "current_explicit_instruction_outranks_memory",
    "purpose_partition_prevents_preference_leakage",
    "persona_is_lens_not_identity_or_authority",
    "platform_affect_changes_form_not_semantic_decision",
    "negative_constraints_apply_before_style_optimization",
    "personalization_off_disables_saved_retrieval",
    "inference_never_self_promotes",
    "feedback_requires_immutable_receipt",
}
REQUIRED_PROHIBITIONS = {
    "sensitive_inference_without_consent",
    "permanent_persona_assignment",
    "impersonate_user",
    "cross_purpose_preference_leakage",
    "model_confidence_as_authority",
    "protected_action_from_preference",
}


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_policy(policy: object) -> list[str]:
    """Validate executable policy shape and detect drift from the evaluator."""

    if not isinstance(policy, dict):
        return ["policy:root:not_an_object"]
    errors: list[str] = []
    expected_keys = {
        "api_version",
        "kind",
        "metadata",
        "invariants",
        "precedence",
        "adaptation",
        "prohibited",
    }
    if set(policy) != expected_keys:
        errors.append("policy:root:unexpected_or_missing_fields")
    if policy.get("api_version") != "quirk.dev/policy/v1alpha1" or policy.get("kind") != "Policy":
        errors.append("policy:identity:invalid")

    metadata = policy.get("metadata")
    if not isinstance(metadata, dict):
        errors.append("policy:metadata:invalid")
    else:
        if metadata.get("id") != "policy.personalization-adaptation":
            errors.append("policy:metadata:id_mismatch")
        if metadata.get("version") != "0.2.0":
            errors.append("policy:metadata:version_mismatch")
        if metadata.get("status") != "candidate":
            errors.append("policy:metadata:status_must_be_candidate")

    precedence = policy.get("precedence")
    executable_precedence = [name for name, _ in sorted(SOURCE_RANK.items(), key=lambda item: item[1], reverse=True)]
    if precedence != executable_precedence:
        errors.append("policy:precedence:evaluator_drift")

    invariants = policy.get("invariants")
    if not isinstance(invariants, list) or set(invariants) != REQUIRED_INVARIANTS:
        errors.append("policy:invariants:invalid")

    adaptation = policy.get("adaptation")
    if not isinstance(adaptation, dict):
        errors.append("policy:adaptation:invalid")
    else:
        if adaptation.get("default_mode") != "propose_only" or adaptation.get("auto_apply") is not False:
            errors.append("policy:adaptation:authority_expansion")
        required_human = {"update_memory", "change_settings", "confirm_persona", "activate_skill", "deploy_generated_ui"}
        if set(adaptation.get("human_required", [])) != required_human:
            errors.append("policy:adaptation:human_gate_drift")

    prohibited = policy.get("prohibited")
    if not isinstance(prohibited, list) or set(prohibited) != REQUIRED_PROHIBITIONS:
        errors.append("policy:prohibited:invalid")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    repo = args.repo.resolve()
    schema_path = repo / "schemas/personalization-plan.schema.json"
    sample_path = repo / "examples/personalization-plan.valid.json"
    cases_path = repo / "evals/intent-shaper/cases.json"
    policy_path = repo / "policies/personalization-adaptation-policy.yaml"

    schema = json.loads(schema_path.read_text())
    sample = json.loads(sample_path.read_text())
    suite = json.loads(cases_path.read_text())
    policy = yaml.safe_load(policy_path.read_text())

    Draft202012Validator.check_schema(schema)
    sample_errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(sample),
        key=lambda error: list(error.path),
    )
    policy_errors = validate_policy(policy)
    results = evaluate_cases(suite["cases"])

    errors: list[str] = []
    errors.extend(f"sample:{'/'.join(map(str, error.path))}:{error.message}" for error in sample_errors)
    errors.extend(policy_errors)
    errors.extend(f"fixture:{result['id']}" for result in results if not result["passed"])

    report = {
        "suite_id": suite["suite_id"],
        "status": "passed" if not errors else "failed",
        "schema_valid": True,
        "sample_valid": not sample_errors,
        "policy_valid": not policy_errors,
        "fixtures_passed": sum(1 for result in results if result["passed"]),
        "fixtures_total": len(results),
        "results": results,
        "errors": errors,
    }
    report["content_hash"] = canonical_hash(report)

    output_path = args.output or (repo / "evals/intent-shaper/conformance-results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n")

    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "status",
                    "sample_valid",
                    "policy_valid",
                    "fixtures_passed",
                    "fixtures_total",
                    "content_hash",
                )
            },
            indent=2,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
