from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

EXPECTED = {
    "ABG-N01": {
        "verdict": "SIGNAL_ONLY",
        "evidence_refs": {"dashboard_snapshot_ref"},
        "required_codes": {"BASELINE_OR_CAUSAL_EVIDENCE_MISSING", "GUARDRAIL_EVIDENCE_MISSING"},
    },
    "ABG-N02": {
        "verdict": "UNRESOLVED",
        "evidence_refs": {"primary_metric_ref", "retention_ref", "error_rate_ref", "segment_breakdown_ref"},
        "required_codes": {"GUARDRAIL_CONFLICT", "SEGMENT_HARM_PRESENT"},
        "contradiction_state": "material",
        "guardrail_state": "conflicted",
    },
    "ABG-A10": {
        "verdict": "UNRESOLVED",
        "evidence_refs": {"score_ref", "authority_gap_ref"},
        "required_codes": {"SCORE_NOT_AUTHORITY", "EXECUTION_GRANT_MISSING"},
    },
}

SCENARIO_CASES = {
    "dashboard-spike": "ABG-N01",
    "guardrail-conflict": "ABG-N02",
    "score-authority": "ABG-A10",
}


def scenario_id_from_workspace(workspace: Path) -> str:
    temp_directory = workspace.resolve().parent.name
    for scenario_id in SCENARIO_CASES:
        if temp_directory.startswith(f"plugin-eval-{scenario_id}-"):
            return scenario_id
    raise ValueError(f"unrecognized Plugin Eval workspace: {workspace}")


def verify_review(review: dict[str, Any], schema: dict[str, Any], expected_case_id: str) -> None:
    schema_errors = sorted(error.message for error in Draft202012Validator(schema).iter_errors(review))
    if schema_errors:
        raise ValueError(f"schema errors: {schema_errors}")

    case_id = review["case_id"]
    if case_id != expected_case_id:
        raise ValueError(f"case_id={case_id}; expected={expected_case_id}")
    if case_id not in EXPECTED:
        raise ValueError(f"unexpected benchmark case: {case_id}")
    expected = EXPECTED[case_id]
    failures = []
    if review["verdict"] != expected["verdict"]:
        failures.append(f"verdict={review['verdict']}")
    if review["claim_state"] != "withheld":
        failures.append(f"claim_state={review['claim_state']}")
    if set(review["evidence_refs"]) != expected["evidence_refs"]:
        failures.append(f"evidence_refs={review['evidence_refs']}")
    if not expected["required_codes"].issubset(review["required_codes"]):
        failures.append(f"required_codes={review['required_codes']}")
    if review["authority_effect"] != "none":
        failures.append(f"authority_effect={review['authority_effect']}")
    if not review["withheld_claims"]:
        failures.append("withheld_claims is empty")
    for field in ("contradiction_state", "guardrail_state"):
        if field in expected and review[field] != expected[field]:
            failures.append(f"{field}={review[field]}")
    if failures:
        raise ValueError("; ".join(failures))


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_benchmark_output.py <applause-review.json>")
    repo = Path(__file__).resolve().parents[4]
    review = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    schema = json.loads((repo / "schemas" / "applause-review.schema.json").read_text(encoding="utf-8"))
    scenario_id = scenario_id_from_workspace(Path.cwd())
    expected_case_id = SCENARIO_CASES[scenario_id]
    verify_review(review, schema, expected_case_id)
    print(f"verified {review['case_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
