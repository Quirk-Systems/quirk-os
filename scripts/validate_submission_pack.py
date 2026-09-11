from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


PACK_PATH = Path("docs/applause-gate/submission-pack.json")
SCHEMA_PATH = Path("schemas/submission-pack.schema.json")
LEDGER_CLASSIFICATIONS = {
    "CONFIRMED_PRODUCT_FACT",
    "PASSED_TEST_EVIDENCE",
    "PROPOSED_OR_UNVERIFIED",
    "MISSING",
    "CONTRADICTION",
}
PACK_STATUSES = {
    "PARTIAL_MISSING_INPUT",
    "BLOCKED_INPUT_CONFLICT",
    "BLOCKED_UNVERIFIED_EVIDENCE",
}
UNPERFORMED_ACTIONS = {
    "portal_scan",
    "portal_upload",
    "submission",
    "review",
    "attestation",
    "publication",
    "tag",
    "merge",
    "deployment",
}


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _canonical_hash(value: dict[str, Any], omitted_keys: set[str]) -> str:
    payload = {key: item for key, item in value.items() if key not in omitted_keys}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return _sha256_bytes(encoded.encode("utf-8"))


def validate(repo: Path, pack_relative_path: Path = PACK_PATH) -> dict[str, Any]:
    repo = repo.resolve()
    pack_path = repo / pack_relative_path
    schema_path = repo / SCHEMA_PATH
    validator_path = repo / "scripts" / "validate_submission_pack.py"

    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    schema_validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = [
        f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(schema_validator.iter_errors(pack), key=lambda item: list(item.absolute_path))
    ]

    ledger = pack.get("evidence_notes", {}).get("ledger", [])
    ledger_ids = [entry.get("id") for entry in ledger]
    if len(ledger_ids) != len(set(ledger_ids)):
        errors.append("evidence_notes/ledger: entry ids must be unique")
    classifications = {entry.get("classification") for entry in ledger}
    if not classifications.issubset(LEDGER_CLASSIFICATIONS):
        errors.append("evidence_notes/ledger: unknown classification")

    submitted = pack.get("package", {}).get("submitted_package", {})
    package_sha256 = submitted.get("sha256")
    cases = pack.get("review_cases", {})
    positive_cases = cases.get("positive", [])
    negative_cases = cases.get("negative", [])
    passed_evidence_ids = {
        entry.get("id")
        for entry in ledger
        if (
            package_sha256
            and entry.get("classification") == "PASSED_TEST_EVIDENCE"
            and entry.get("submitted_package_sha256") == package_sha256
        )
    }
    case_bindings_valid = bool(package_sha256)
    for case in [*positive_cases, *negative_cases]:
        if not package_sha256 or case.get("package_sha256") != package_sha256:
            errors.append(f"review_cases/{case.get('id', '<unknown>')}: submitted package digest mismatch")
            case_bindings_valid = False
        unsupported_refs = sorted(set(case.get("evidence_refs", [])) - passed_evidence_ids)
        if unsupported_refs:
            errors.append(
                f"review_cases/{case.get('id', '<unknown>')}: "
                f"non-passed current-package evidence references {unsupported_refs}"
            )
            case_bindings_valid = False

    status = pack.get("status")
    missing_inputs = pack.get("missing_inputs", [])
    contradictions = pack.get("contradictions", [])
    if status == "PARTIAL_MISSING_INPUT" and not missing_inputs:
        errors.append("status: PARTIAL_MISSING_INPUT requires missing_inputs")
    if status == "BLOCKED_INPUT_CONFLICT" and not contradictions:
        errors.append("status: BLOCKED_INPUT_CONFLICT requires contradictions")
    if (
        status == "BLOCKED_UNVERIFIED_EVIDENCE"
        and "PROPOSED_OR_UNVERIFIED" not in classifications
    ):
        errors.append(
            "status: BLOCKED_UNVERIFIED_EVIDENCE requires PROPOSED_OR_UNVERIFIED evidence"
        )

    unperformed_actions = set(pack.get("unperformed_actions", []))
    if unperformed_actions != UNPERFORMED_ACTIONS:
        errors.append("unperformed_actions: must explicitly list every required unperformed action")

    rule_snapshot = pack.get("rule_snapshot", {})
    public_copy = pack.get("public_copy", {})
    publisher = pack.get("package", {}).get("publisher", {})
    support = pack.get("package", {}).get("support_and_privacy", {})
    exact_case_counts = len(positive_cases) == 5 and len(negative_cases) == 3
    current_version_case_evidence = exact_case_counts and case_bindings_valid
    public_copy_complete = all(
        [
            public_copy.get("listing"),
            public_copy.get("supported_capabilities"),
            public_copy.get("starter_prompts"),
            public_copy.get("release_notes"),
        ]
    )
    package_boundary_complete = all(
        [
            submitted.get("public_name"),
            submitted.get("version"),
            submitted.get("sha256"),
            submitted.get("classification") == "skills-only",
            submitted.get("contains_mcp") is False,
            submitted.get("requires_authentication") is False,
            submitted.get("uses_live_data") is False,
            submitted.get("performs_external_actions") is False,
            submitted.get("capability_allowlist"),
        ]
    )
    publisher_facts_complete = all(publisher.values()) and all(support.values())
    independent_verdict_present = bool(pack.get("independent_verdict", {}).get("value"))
    submission_ready = all(
        [
            rule_snapshot.get("verified"),
            rule_snapshot.get("packaged_rules_ref"),
            rule_snapshot.get("conflict_assessment"),
            package_boundary_complete,
            publisher_facts_complete,
            current_version_case_evidence,
            public_copy_complete,
            independent_verdict_present,
            not missing_inputs,
            not contradictions,
            not pack.get("version_drift", []),
        ]
    )
    if submission_ready:
        errors.append("status: stop-status pack must not satisfy submission-ready conditions")

    report = {
        "schema_version": "submission-pack-validation.v1",
        "pack_path": pack_relative_path.as_posix(),
        "pack_sha256": _sha256_file(pack_path),
        "schema_sha256": _sha256_file(schema_path),
        "validator_sha256": _sha256_file(validator_path),
        "contract_valid": not errors,
        "submission_ready": False,
        "pack_status": status,
        "checks": {
            "status_vocabulary_valid": status in PACK_STATUSES,
            "ledger_vocabulary_valid": classifications.issubset(LEDGER_CLASSIFICATIONS),
            "field_lengths_evaluated": False,
            "positive_case_count": len(positive_cases),
            "negative_case_count": len(negative_cases),
            "exact_case_counts": exact_case_counts,
            "current_version_case_evidence": current_version_case_evidence,
            "package_boundary_complete": package_boundary_complete,
            "publisher_support_privacy_complete": publisher_facts_complete,
            "independent_verdict_present": independent_verdict_present,
            "all_required_actions_unperformed": unperformed_actions == UNPERFORMED_ACTIONS,
        },
        "errors": errors,
        "caveat": (
            "Contract validation is deterministic local evidence only; it is not submission readiness, "
            "OpenAI review, approval, attestation, or publication."
        ),
    }
    report["receipt_hash"] = _canonical_hash(report, omitted_keys={"receipt_hash"})
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the fail-closed Skills submission pack.")
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--pack", type=Path, default=PACK_PATH)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-contract-valid", action="store_true")
    args = parser.parse_args()

    report = validate(args.repo, args.pack)
    if args.output:
        output = args.output if args.output.is_absolute() else args.repo / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    return int(args.require_contract_valid and not report["contract_valid"])


if __name__ == "__main__":
    raise SystemExit(main())
