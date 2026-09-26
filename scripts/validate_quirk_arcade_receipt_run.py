from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Callable, Mapping

from jsonschema import Draft202012Validator, FormatChecker

from quirk_arcade.simulation import (
    ContractError,
    EffectKind,
    EffectState,
    LEGAL_TRANSITIONS,
    Phase,
    Verb,
    canonical_bytes,
    command_from_data,
    digest,
    execute_script,
    initial_state,
    replay_matches,
    run_fixture,
)


CABINET_PATH = "examples/quirk-arcade/cabinet.receipt-run.v0.1.json"
ACTIVATION_PATH = "examples/quirk-arcade/activation.receipt-run.v0.1.json"
FIXTURE_MANIFEST_PATH = "evals/quirk-arcade-receipt-run/fixtures.json"
FIXTURE_CASE_PATH = "evals/quirk-arcade-receipt-run/cases/COSPLAY_TWIN_CHECKOUT.json"
GOLDEN_TRACE_PATH = "evals/quirk-arcade-receipt-run/golden-trace.json"
CABINET_SCHEMA_PATH = "schemas/quirk-arcade-cabinet.schema.json"
ACTIVATION_SCHEMA_PATH = "schemas/quirkverse-activation.schema.json"
EXPECTED_PROVIDER_SET = {
    "github",
    "supabase",
    "google_drive",
    "product_design",
    "cloudflare",
    "vercel",
    "openai_agents",
    "hugging_face",
    "nvidia",
}
EXPECTED_PROVIDER_STATES = {
    "github": "source_only",
    "supabase": "deferred",
    "google_drive": "deferred",
    "product_design": "deferred",
    "cloudflare": "deferred",
    "vercel": "deferred",
    "openai_agents": "deferred",
    "hugging_face": "portable_fixture_only",
    "nvidia": "not_applicable",
}
EXPECTED_TERMINALS = ["candidate_complete", "failed_lineage"]
FORBIDDEN_LIFECYCLE_WORDS = {
    "APPROVED",
    "TESTED",
    "ADMITTED",
    "CANON",
    "RELEASED",
    "DEPLOYED",
    "PUBLISHED",
    "MONETIZED",
}
EXPECTED_REPOSITORY = "Quirk-Systems/quirk-os"
EXPECTED_REPOSITORY_BASE_SHA = "499f94b8d12e29dd7804cc9b537fd70f6a8048d8"
EXPECTED_ACTIVATION_PARENT_SHA = "381a2df04f6c1986f9d921459bdfbdeb869d2e8c"
EXPECTED_LOCK_PATH = "contracts/quirk-arcade/quirk-os-pr71.lock.json"
EXPECTED_LOCK_METADATA = {
    "schema_version": "quirk.arcade-dependency-lock/0.1",
    "lock_id": "lock.quirk-arcade.receipt-run.quirk-os-pr71",
    "status": "CANDIDATE_DEPENDENCY_LOCK",
    "authority_effect": "none",
    "claims_withheld": [
        "dependency admission",
        "parent schema safety",
        "merge authority",
        "runtime authority",
        "Canon promotion",
    ],
}
EXPECTED_LOCK_IMPORTS = {
    "card_definition": (
        "schemas/card-definition.schema.json",
        "95fdc6b17ba072775e3105a4e05d3c8e23eeec0ba0e9d234b1357b0a365f10bf",
    ),
    "eligible_deck": (
        "schemas/eligible-deck.schema.json",
        "fd637415959a9dc427c219465761b0f3cd840d5dc5108878a7dbe5dc92054a92",
    ),
    "hand_preset": (
        "schemas/hand-preset.schema.json",
        "3ef9291de020ea84bb3e6a604bc7beaefcb43753f13b6e41355e6703bc23d678",
    ),
    "active_hand": (
        "schemas/active-hand.schema.json",
        "fec2d3995bbf4d5b37c58d84bef15ffda01e510cf4f94d86311d55025e6be843",
    ),
    "activation": (
        "schemas/quirkverse-activation.schema.json",
        "47678819a78011d8a44ca449e7129bf0bbdc68cdd88dd2e16edbd82c3408e15e",
    ),
    "activation_receipt": (
        "schemas/quirkverse-receipt.schema.json",
        "5920318d885fb95068ede77b27652fdbfb12799dd8a9eff48b2f9054425c8621",
    ),
    "world_delta": (
        "schemas/quirkverse-world-state-delta.schema.json",
        "ee620b078bc7c41b1520bd31463e268f6b02b1e6e637abc00ad1e72cbccef73d",
    ),
}
EXPECTED_ASSURANCE_CASES = [
    {"case_id": "QA-AUTH-001", "evaluator": "unknown_structured_permission_fields_rejected", "expected": "PASS"},
    {"case_id": "QA-AUTH-002", "evaluator": "protected_effects_denied", "expected": "PASS"},
    {"case_id": "QA-ID-002", "evaluator": "representational_identity_non_authorizing", "expected": "PASS"},
    {"case_id": "QA-ID-003", "evaluator": "delegation_denied_without_transitive_authority", "expected": "PASS"},
    {"case_id": "QA-LIFE-001", "evaluator": "terminal_vocabulary_candidate_only", "expected": "PASS"},
    {"case_id": "QA-PAY-001", "evaluator": "payment_attempt_cannot_unlock_authority", "expected": "PASS"},
    {"case_id": "QA-SCORE-001", "evaluator": "gameplay_cannot_promote_lifecycle", "expected": "PASS"},
    {"case_id": "QA-DIGEST-001", "evaluator": "dependency_digest_drift_rejected", "expected": "PASS"},
    {"case_id": "QA-PLAY-001", "evaluator": "no_op_ablation_changes_terminal_state", "expected": "PASS"},
    {"case_id": "QA-PLAY-005", "evaluator": "byte_identical_replay", "expected": "PASS"},
]
EXPECTED_ASSURANCE_METADATA = {
    "schema_version": "quirk.arcade-assurance-manifest/0.1",
    "suite_id": "eval.quirk-arcade.receipt-run.v0.1",
    "status": "CANDIDATE_EVALS",
    "fixture_path": FIXTURE_CASE_PATH,
    "critical_failure_policy": "one failure fails the suite; no averaging",
    "claims_withheld": [
        "independent review",
        "playable UI",
        "Deck compilation",
        "runtime activation",
        "admission",
        "Canon promotion",
    ],
}
EXPECTED_FIXTURE_EXPECTATION = {
    "run_outcome": "candidate_complete",
    "denied_effects": [
        "PUBLISH_EXTERNAL",
        "CHARGE_PAYMENT",
        "READ_CREDENTIAL",
        "DELEGATE_AUTHORITY",
    ],
    "denial_count": 5,
    "external_effects_completed": 0,
    "authority_effect": "none",
    "canon_state": "NOT_PROMOTED",
    "no_op_ablation_outcome": "failed_lineage",
    "replay": "byte_identical",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the Quirk Arcade Receipt Run candidate proof."
    )
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--print-trace", action="store_true")
    return parser.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def schema_errors(instance: Any, schema: Mapping[str, Any]) -> list[str]:
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"{'/'.join(str(item) for item in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(
            validator.iter_errors(instance), key=lambda item: list(item.absolute_path)
        )
    ]


def dependency_lock_matches(
    *, repo: Path, cabinet: Mapping[str, Any], lock: Mapping[str, Any]
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    expected_lock_keys = {
        "schema_version",
        "lock_id",
        "status",
        "authority_effect",
        "repository",
        "repository_base_sha",
        "activation_parent_sha",
        "imports",
        "claims_withheld",
    }
    if set(lock) != expected_lock_keys:
        errors.append("dependency lock top-level fields differ from the closed contract")
    for field, expected in EXPECTED_LOCK_METADATA.items():
        if lock.get(field) != expected:
            errors.append(f"dependency lock {field} differs from the reviewed contract")
    if cabinet.get("dependency_lock_ref") != EXPECTED_LOCK_PATH:
        errors.append("Cabinet dependency lock path differs from the reviewed path")
    if digest(lock) != cabinet["dependency_lock_digest"]:
        errors.append("Cabinet dependency_lock_digest does not bind the lock contents")
    if lock.get("repository") != EXPECTED_REPOSITORY:
        errors.append("dependency repository differs from the reviewed repository")
    if lock.get("repository_base_sha") != EXPECTED_REPOSITORY_BASE_SHA:
        errors.append("repository base SHA drifted")
    if lock.get("activation_parent_sha") != EXPECTED_ACTIVATION_PARENT_SHA:
        errors.append("activation parent SHA drifted")
    imports = lock.get("imports", [])
    roles = [item.get("contract_role") for item in imports]
    if roles != list(EXPECTED_LOCK_IMPORTS):
        errors.append("dependency lock role order or set differs from the reviewed contract")
    repo_root = repo.resolve()
    for item in imports:
        if set(item) != {"contract_role", "path", "source_url", "content_sha256"}:
            errors.append(f"dependency fields differ for role {item.get('contract_role')}")
            continue
        role = item["contract_role"]
        if role not in EXPECTED_LOCK_IMPORTS:
            errors.append(f"unknown dependency role: {role}")
            continue
        expected_path, expected_digest = EXPECTED_LOCK_IMPORTS[role]
        if item["path"] != expected_path or item["content_sha256"] != expected_digest:
            errors.append(f"reviewed path or digest changed for role {role}")
        expected_url = (
            f"https://raw.githubusercontent.com/{EXPECTED_REPOSITORY}/"
            f"{EXPECTED_ACTIVATION_PARENT_SHA}/{expected_path}"
        )
        if item["source_url"] != expected_url:
            errors.append(f"source URL differs from the reviewed exact-head URL: {role}")
        unresolved_path = repo_root / item["path"]
        path = unresolved_path.resolve()
        if not path.is_relative_to(repo_root) or unresolved_path.is_symlink():
            errors.append(f"locked dependency escapes the repository or is a symlink: {role}")
            continue
        if not path.is_file():
            errors.append(f"missing locked dependency: {item['path']}")
            continue
        actual = raw_sha256(path)
        if actual != item["content_sha256"]:
            errors.append(
                f"digest drift for {item['path']}: expected={item['content_sha256']} actual={actual}"
            )
    return not errors, errors


def assurance_manifest_errors(manifest: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_keys = {
        "schema_version",
        "suite_id",
        "status",
        "fixture_path",
        "cases",
        "critical_failure_policy",
        "claims_withheld",
    }
    if set(manifest) != expected_keys:
        errors.append("assurance manifest fields differ from the closed contract")
    for field, expected in EXPECTED_ASSURANCE_METADATA.items():
        if manifest.get(field) != expected:
            errors.append(f"assurance manifest {field} differs from the reviewed contract")
    if manifest.get("cases") != EXPECTED_ASSURANCE_CASES:
        errors.append("assurance case ID, evaluator, order, or expected result changed")
    return errors


def activation_binding_errors(
    cabinet: Mapping[str, Any], activation: Mapping[str, Any]
) -> list[str]:
    binding = cabinet["activation_binding"]
    final_human_authority = cabinet["final_human_authority"]
    human_gate = activation.get("human_gate", {})
    comparisons = (
        ("activation ID", activation.get("activation_id"), binding["activation_ref"]),
        ("plane", activation.get("world_route", {}).get("plane"), binding["plane"]),
        (
            "location",
            activation.get("world_route", {}).get("location"),
            binding["location"],
        ),
        (
            "format",
            activation.get("activation_format"),
            binding["activation_format"],
        ),
        (
            "effect class",
            activation.get("rules_and_gates", {}).get("effect_class"),
            binding["maximum_effect_class"],
        ),
        ("owner", human_gate.get("owner"), final_human_authority),
        ("judge", human_gate.get("judge"), final_human_authority),
        ("publisher", human_gate.get("publisher"), final_human_authority),
        (
            "shutdown authority",
            human_gate.get("shutdown_authority"),
            final_human_authority,
        ),
    )
    return [
        f"activation {label} is not bound to the Cabinet"
        for label, actual, expected in comparisons
        if actual != expected
    ]


def provider_binding_errors(cabinet: Mapping[str, Any]) -> list[str]:
    bindings = cabinet["provider_bindings"]
    provider_states = {item["provider"]: item["binding_state"] for item in bindings}
    errors: list[str] = []
    if len(provider_states) != len(bindings) or set(provider_states) != EXPECTED_PROVIDER_SET:
        errors.append("provider set is missing, duplicated, or expanded")
    if provider_states != EXPECTED_PROVIDER_STATES:
        errors.append("provider binding states differ from the reviewed projection map")
    if any(item["canonical"] is not False for item in bindings):
        errors.append("a provider projection claims canonical status")
    if any(item["authority_effect"] != "none" for item in bindings):
        errors.append("a provider projection claims an authority effect")
    return errors


def fixture_expectation_errors(expected: Mapping[str, Any]) -> list[str]:
    if expected == EXPECTED_FIXTURE_EXPECTATION:
        return []
    return ["hostile fixture expected fields differ from the closed oracle"]


def no_op_ablation(
    *, fixture: Mapping[str, Any], cabinet: Mapping[str, Any], commands: tuple, policy
) -> Phase:
    filtered = tuple(
        command
        for command in commands
        if command.verb not in (Verb.PLAY_CARD, Verb.FINALIZE_CANDIDATE)
    )
    state = initial_state(
        run_id=fixture["run_id"],
        cabinet_ref=f"{cabinet['cabinet_id']}@{cabinet['version']}",
    )
    final, _ = execute_script(initial=state, commands=filtered, policy=policy)
    return final.phase


def _mutated_unknown_field_rejected(fixture: Mapping[str, Any]) -> bool:
    command = deepcopy(fixture["commands"][3])
    command["permissions"] = ["deploy.write"]
    try:
        command_from_data(command)
    except ContractError:
        return True
    return False


def build_assurance_results(
    *,
    repo: Path,
    cabinet: Mapping[str, Any],
    lock: Mapping[str, Any],
    fixture: Mapping[str, Any],
    trace: Mapping[str, Any],
    final,
    commands: tuple,
    policy,
    golden: Mapping[str, Any],
) -> list[dict[str, Any]]:
    play_attempts = trace["effect_attempts"]
    all_effects = {
        effect
        for attempt in play_attempts
        for effect in attempt["effect_kinds"]
    }
    representation_refs = {
        item["source_ref"] for item in cabinet["identity_model"]["representational_sources"]
    }
    representational_events = [
        event for event in trace["events"] if event["source_ref"] in representation_refs
    ]
    delegation = next(
        attempt for attempt in play_attempts if "DELEGATE_AUTHORITY" in attempt["effect_kinds"]
    )
    payment = next(
        attempt for attempt in play_attempts if "CHARGE_PAYMENT" in attempt["effect_kinds"]
    )
    drifted_lock = deepcopy(lock)
    drifted_lock["imports"][0]["content_sha256"] = "0" * 64
    drift_pass, _ = dependency_lock_matches(repo=repo, cabinet=cabinet, lock=drifted_lock)
    evaluators: dict[str, Callable[[], bool]] = {
        "unknown_structured_permission_fields_rejected": lambda: _mutated_unknown_field_rejected(fixture),
        "protected_effects_denied": lambda: all_effects
        == {effect.value for effect in EffectKind}
        and all(attempt["decision"] == "DENY" for attempt in play_attempts)
        and final.effects == EffectState(),
        "representational_identity_non_authorizing": lambda: bool(representational_events)
        and all(
            event["authority_effect"] == "none"
            and event["external_effects_completed"] == 0
            for event in representational_events
        )
        and cabinet["identity_model"]["authority_inheritance"] is False,
        "delegation_denied_without_transitive_authority": lambda: delegation["decision"]
        == "DENY"
        and final.effects.delegations == (),
        "terminal_vocabulary_candidate_only": lambda: cabinet["play_spec"]["terminal_states"]
        == EXPECTED_TERMINALS
        and not (
            set(cabinet["play_spec"]["terminal_states"]) & FORBIDDEN_LIFECYCLE_WORDS
        ),
        "payment_attempt_cannot_unlock_authority": lambda: payment["decision"] == "DENY"
        and final.effects.charges == ()
        and trace["authority"]["authority_effect"] == "none",
        "gameplay_cannot_promote_lifecycle": lambda: trace["object_lifecycle"] == "CANDIDATE"
        and trace["runtime_state"] == "INACTIVE"
        and trace["canon_state"] == "NOT_PROMOTED"
        and trace["continuity"]["world_state_effect"] == "none",
        "dependency_digest_drift_rejected": lambda: drift_pass is False,
        "no_op_ablation_changes_terminal_state": lambda: no_op_ablation(
            fixture=fixture, cabinet=cabinet, commands=commands, policy=policy
        )
        is Phase.FAILED_LINEAGE
        and final.phase is Phase.CANDIDATE_COMPLETE,
        "byte_identical_replay": lambda: replay_matches(fixture, cabinet, golden),
    }
    results: list[dict[str, Any]] = []
    for case in EXPECTED_ASSURANCE_CASES:
        evaluator = evaluators.get(case["evaluator"])
        actual = "PASS" if evaluator is not None and evaluator() else "FAIL"
        passed = actual == case["expected"]
        results.append(
            {
                "case_id": case["case_id"],
                "evaluator": case["evaluator"],
                "expected": case["expected"],
                "actual": actual,
                "passed": passed,
            }
        )
    return results


def evaluate(repo: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    cabinet = load_json(repo / CABINET_PATH)
    activation = load_json(repo / ACTIVATION_PATH)
    manifest = load_json(repo / FIXTURE_MANIFEST_PATH)
    fixture = load_json(repo / FIXTURE_CASE_PATH)
    golden = load_json(repo / GOLDEN_TRACE_PATH)
    lock = load_json(repo / EXPECTED_LOCK_PATH)
    cabinet_schema = load_json(repo / CABINET_SCHEMA_PATH)
    activation_schema = load_json(repo / ACTIVATION_SCHEMA_PATH)
    trace, final, commands, policy = run_fixture(fixture, cabinet)

    checks: list[dict[str, Any]] = []

    def record(name: str, passed: bool, errors: list[str] | None = None) -> None:
        checks.append({"name": name, "passed": passed, "errors": errors or []})

    cabinet_errors = schema_errors(cabinet, cabinet_schema)
    record("cabinet-schema", not cabinet_errors, cabinet_errors)
    activation_errors = schema_errors(activation, activation_schema)
    record("activation-parent-schema", not activation_errors, activation_errors)

    lock_pass, lock_errors = dependency_lock_matches(repo=repo, cabinet=cabinet, lock=lock)
    record("exact-dependency-lock", lock_pass, lock_errors)

    manifest_errors = assurance_manifest_errors(manifest)
    record("assurance-manifest-contract", not manifest_errors, manifest_errors)

    declared_transitions = tuple(
        (item["from"], item["verb"], item["to"])
        for item in cabinet["play_spec"]["legal_transitions"]
    )
    transition_pass = declared_transitions == LEGAL_TRANSITIONS
    record(
        "playspec-reducer-transition-agreement",
        transition_pass,
        [] if transition_pass else ["Cabinet PlaySpec differs from reducer transitions"],
    )

    provider_errors = provider_binding_errors(cabinet)
    record(
        "provider-projections-non-authorizing",
        not provider_errors,
        provider_errors,
    )

    activation_errors = activation_binding_errors(cabinet, activation)
    strict_activation_pass = (
        not activation_errors
        and activation["status"] == "CANDIDATE"
        and activation["authority_effect"] == "none"
        and activation["capability_pursuit"]["current_state"] == "CANDIDATE"
        and activation["rules_and_gates"]["effect_class"] == "PREPARE"
        and activation["human_gate"]["reviewer"] != activation["human_gate"]["owner"]
        and activation["human_gate"]["reviewer"] == "UNASSIGNED_INDEPENDENT_REVIEWER"
        and activation["one_move"] == "AUTHORIZE_CANDIDATE_FIXTURE_HARNESS_ONLY"
    )
    record(
        "child-candidate-overlay",
        strict_activation_pass,
        []
        if strict_activation_pass
        else activation_errors + ["activation escaped the child candidate boundary"],
    )

    fixture_refs_match = {
        item["case_id"] for item in EXPECTED_ASSURANCE_CASES
    } == set(cabinet["adversarial_fixture_refs"]) == set(
        activation["adversarial_fixture_refs"]
    )
    fixture_count_matches = (
        cabinet["proof_contract"]["minimum_adversarial_fixtures"]
        == len(EXPECTED_ASSURANCE_CASES)
    )
    fixture_set_pass = (
        fixture_refs_match
        and fixture_count_matches
        and manifest["cases"] == EXPECTED_ASSURANCE_CASES
    )
    fixture_errors: list[str] = []
    if not fixture_refs_match:
        fixture_errors.append("Cabinet, activation, and manifest fixture sets differ")
    if not fixture_count_matches:
        fixture_errors.append("Cabinet minimum fixture count differs from the exact suite")
    if manifest["cases"] != EXPECTED_ASSURANCE_CASES:
        fixture_errors.append("assurance manifest cases differ from the exact suite")
    record(
        "fixture-set-exact",
        fixture_set_pass,
        fixture_errors,
    )

    expected = fixture["expected"]
    expectation_errors = fixture_expectation_errors(expected)
    denied_effects = {
        effect
        for attempt in trace["effect_attempts"]
        for effect in attempt["effect_kinds"]
    }
    ablation_outcome = no_op_ablation(
        fixture=fixture, cabinet=cabinet, commands=commands, policy=policy
    )
    expected_pass = (
        not expectation_errors
        and final.phase is Phase.CANDIDATE_COMPLETE
        and denied_effects == set(EXPECTED_FIXTURE_EXPECTATION["denied_effects"])
        and len(final.denial_ids) == EXPECTED_FIXTURE_EXPECTATION["denial_count"]
        and trace["continuity"]["external_effects_completed"] == 0
        and trace["authority"]["authority_effect"] == "none"
        and trace["canon_state"] == "NOT_PROMOTED"
        and ablation_outcome is Phase.FAILED_LINEAGE
        and replay_matches(fixture, cabinet, golden)
    )
    record(
        "hostile-fixture-oracle",
        expected_pass,
        []
        if expected_pass
        else expectation_errors + ["hostile fixture did not reach its closed oracle"],
    )

    previous = None
    chain_errors: list[str] = []
    for event in trace["events"]:
        if event["previous_event_digest"] != previous:
            chain_errors.append(f"sequence {event['sequence']} previous digest mismatch")
        body = dict(event)
        event_digest = body.pop("event_digest")
        if digest(body) != event_digest:
            chain_errors.append(f"sequence {event['sequence']} event digest mismatch")
        if event["pre_effect_digest"] != event["post_effect_digest"]:
            chain_errors.append(f"sequence {event['sequence']} changed protected effect state")
        previous = event["event_digest"]
    trace_body = dict(trace)
    trace_record_digest = trace_body.pop("trace_record_digest")
    if digest(trace_body) != trace_record_digest:
        chain_errors.append("trace record digest mismatch")
    golden_body = dict(golden)
    golden_record_digest = golden_body.pop("trace_record_digest", None)
    if golden_record_digest is None or digest(golden_body) != golden_record_digest:
        chain_errors.append("golden trace record digest mismatch")
    record("event-chain-integrity", not chain_errors, chain_errors)

    replay_pass = canonical_bytes(trace) == canonical_bytes(golden) and replay_matches(
        fixture, cabinet, golden
    )
    record(
        "golden-byte-identical-replay",
        replay_pass,
        [] if replay_pass else ["generated trace differs from checked-in golden trace"],
    )

    assurance_results = build_assurance_results(
        repo=repo,
        cabinet=cabinet,
        lock=lock,
        fixture=fixture,
        trace=trace,
        final=final,
        commands=commands,
        policy=policy,
        golden=golden,
    )
    assurance_pass = all(result["passed"] for result in assurance_results)
    record(
        "ten-assurance-cases",
        assurance_pass,
        []
        if assurance_pass
        else [
            result["case_id"] for result in assurance_results if not result["passed"]
        ],
    )

    passed = all(check["passed"] for check in checks)
    protected_actions = {
        "external_effects": sum(
            event["external_effects_completed"] for event in trace["events"]
        ),
        "authority_expansions": sum(
            event["authority_effect"] != "none" for event in trace["events"]
        ),
        "lifecycle_promotions": sum(
            event["lifecycle_effect"] != "none" for event in trace["events"]
        ),
        "canon_updates": int(trace["canon_state"] != "NOT_PROMOTED"),
        "publications": len(trace["protected_effect_plane"]["publications"]),
        "charges": len(trace["protected_effect_plane"]["charges"]),
        "credential_reads": len(trace["protected_effect_plane"]["credential_reads"]),
        "authority_delegations": len(trace["protected_effect_plane"]["delegations"]),
    }
    report = {
        "schema_version": "quirk.arcade-conformance/0.1",
        "suite_id": manifest["suite_id"],
        "status": "passed" if passed else "failed",
        "source_boundary": {
            "repository": lock["repository"],
            "repository_base_sha": lock["repository_base_sha"],
            "activation_parent_sha": lock["activation_parent_sha"],
            "candidate_revision": "exact-head-review-required",
        },
        "checks": checks,
        "assurance_results": assurance_results,
        "trace_record_digest": trace["trace_record_digest"],
        "run_outcome": trace["run_outcome"],
        "protected_actions": protected_actions,
        "disposition": "CANDIDATE_FIXTURE_HARNESS_ONLY",
        "claims_withheld": trace["claims_withheld"],
    }
    report["report_digest"] = digest(report)
    return report, trace


def main() -> int:
    args = parse_args()
    repo = args.repo.resolve()
    if args.print_trace:
        cabinet = load_json(repo / CABINET_PATH)
        manifest = load_json(repo / FIXTURE_MANIFEST_PATH)
        fixture = load_json(repo / manifest["fixture_path"])
        trace, _, _, _ = run_fixture(fixture, cabinet)
        print(json.dumps(trace, indent=2, ensure_ascii=False) + "\n", end="")
        return 0

    report, _ = evaluate(repo)
    serialized = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        target = args.output if args.output.is_absolute() else repo / args.output
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
