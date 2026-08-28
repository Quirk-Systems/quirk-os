from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass, replace
from enum import Enum
import hashlib
import json
from typing import Any, Iterable, Mapping, Sequence


SIMULATION_VERSION = "receipt-run/v0.1"


class ContractError(ValueError):
    """Raised when fixture material does not satisfy the closed contract."""


class Phase(str, Enum):
    SETUP = "setup"
    OBSERVE = "observe"
    SHAPE = "shape"
    TEST = "test"
    RECEIPT = "receipt"
    CANDIDATE_COMPLETE = "candidate_complete"
    FAILED_LINEAGE = "failed_lineage"


class Verb(str, Enum):
    START_RUN = "start_run"
    CAPTURE_SIGNAL = "capture_signal"
    FORM_CANDIDATE = "form_candidate"
    PLAY_CARD = "play_card"
    SEAL_RECEIPT = "seal_receipt"
    FINALIZE_CANDIDATE = "finalize_candidate"


class EffectKind(str, Enum):
    PUBLISH_EXTERNAL = "PUBLISH_EXTERNAL"
    CHARGE_PAYMENT = "CHARGE_PAYMENT"
    READ_CREDENTIAL = "READ_CREDENTIAL"
    DELEGATE_AUTHORITY = "DELEGATE_AUTHORITY"


class Decision(str, Enum):
    ADVANCE = "ADVANCE"
    DENY = "DENY"
    SEAL = "SEAL"
    FINALIZE = "FINALIZE"
    FAIL_LINEAGE = "FAIL_LINEAGE"


RIGHTS = (
    "observe",
    "infer",
    "propose",
    "execute_reversible",
    "enforce_invariant",
    "execute_protected",
)
SOURCE_KINDS = ("human", "agent", "character", "persona", "creature", "familiar")
PROTECTED_EFFECTS = tuple(effect.value for effect in EffectKind)
TERMINAL_PHASES = (Phase.CANDIDATE_COMPLETE, Phase.FAILED_LINEAGE)
LEGAL_TRANSITIONS = (
    ("setup", "start_run", "observe"),
    ("observe", "capture_signal", "shape"),
    ("shape", "form_candidate", "test"),
    ("test", "play_card", "test"),
    ("test", "seal_receipt", "receipt"),
    ("receipt", "finalize_candidate", "candidate_complete"),
)


@dataclass(frozen=True)
class EffectRequest:
    kind: EffectKind
    target_ref: str
    amount_cents: int
    requested_right: str


@dataclass(frozen=True)
class Command:
    command_id: str
    run_id: str
    controller_ref: str
    source_ref: str
    source_kind: str
    verb: Verb
    payload_ref: str
    card_ref: str
    effects: tuple[EffectRequest, ...]


@dataclass(frozen=True)
class ActorPolicy:
    policy_ref: str
    version: str
    controller_ref: str
    controller_kind: str
    maximum_right: str
    effect_class_ceiling: str
    authorization_assertion_ref: str
    permitted_verbs: tuple[str, ...]
    prohibited_effects: tuple[str, ...]
    cards_cannot_expand_authority: bool
    representations_cannot_expand_authority: bool
    local_only: bool


@dataclass(frozen=True)
class EffectState:
    publications: tuple[str, ...] = ()
    charges: tuple[tuple[str, int], ...] = ()
    credential_reads: tuple[str, ...] = ()
    delegations: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class RunState:
    run_id: str
    cabinet_ref: str
    phase: Phase
    sequence: int
    observation_refs: tuple[str, ...]
    candidate_refs: tuple[str, ...]
    tested_effects: tuple[str, ...]
    denial_ids: tuple[str, ...]
    effects: EffectState
    terminal_reason: str


def _plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _plain(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        _plain(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def initial_state(*, run_id: str, cabinet_ref: str) -> RunState:
    return RunState(
        run_id=run_id,
        cabinet_ref=cabinet_ref,
        phase=Phase.SETUP,
        sequence=0,
        observation_refs=(),
        candidate_refs=(),
        tested_effects=(),
        denial_ids=(),
        effects=EffectState(),
        terminal_reason="",
    )


def _expect_exact_keys(value: Mapping[str, Any], keys: Iterable[str], *, label: str) -> None:
    expected = set(keys)
    actual = set(value)
    if actual != expected:
        raise ContractError(
            f"{label} keys differ: missing={sorted(expected - actual)} extra={sorted(actual - expected)}"
        )


def effect_from_data(value: Mapping[str, Any]) -> EffectRequest:
    _expect_exact_keys(
        value,
        ("kind", "target_ref", "amount_cents", "requested_right"),
        label="effect",
    )
    try:
        effect = EffectRequest(
            kind=EffectKind(value["kind"]),
            target_ref=value["target_ref"],
            amount_cents=value["amount_cents"],
            requested_right=value["requested_right"],
        )
    except (TypeError, ValueError) as error:
        raise ContractError(f"invalid effect: {error}") from error
    validate_effect(effect)
    return effect


def command_from_data(value: Mapping[str, Any]) -> Command:
    _expect_exact_keys(
        value,
        (
            "command_id",
            "run_id",
            "controller_ref",
            "source_ref",
            "source_kind",
            "verb",
            "payload_ref",
            "card_ref",
            "effects",
        ),
        label="command",
    )
    if not isinstance(value["effects"], list):
        raise ContractError("command effects must be an array")
    try:
        command = Command(
            command_id=value["command_id"],
            run_id=value["run_id"],
            controller_ref=value["controller_ref"],
            source_ref=value["source_ref"],
            source_kind=value["source_kind"],
            verb=Verb(value["verb"]),
            payload_ref=value["payload_ref"],
            card_ref=value["card_ref"],
            effects=tuple(effect_from_data(item) for item in value["effects"]),
        )
    except (TypeError, ValueError) as error:
        raise ContractError(f"invalid command: {error}") from error
    validate_command(command)
    return command


def policy_from_data(value: Mapping[str, Any]) -> ActorPolicy:
    _expect_exact_keys(
        value,
        (
            "policy_ref",
            "version",
            "controller_ref",
            "controller_kind",
            "maximum_right",
            "effect_class_ceiling",
            "authorization_assertion_ref",
            "permitted_verbs",
            "prohibited_effects",
            "cards_cannot_expand_authority",
            "representations_cannot_expand_authority",
            "local_only",
        ),
        label="policy",
    )
    if not isinstance(value["permitted_verbs"], list) or not isinstance(
        value["prohibited_effects"], list
    ):
        raise ContractError("policy verbs and effects must be arrays")
    try:
        policy = ActorPolicy(
            policy_ref=value["policy_ref"],
            version=value["version"],
            controller_ref=value["controller_ref"],
            controller_kind=value["controller_kind"],
            maximum_right=value["maximum_right"],
            effect_class_ceiling=value["effect_class_ceiling"],
            authorization_assertion_ref=value["authorization_assertion_ref"],
            permitted_verbs=tuple(value["permitted_verbs"]),
            prohibited_effects=tuple(value["prohibited_effects"]),
            cards_cannot_expand_authority=value["cards_cannot_expand_authority"],
            representations_cannot_expand_authority=value[
                "representations_cannot_expand_authority"
            ],
            local_only=value["local_only"],
        )
    except (TypeError, ValueError) as error:
        raise ContractError(f"invalid policy: {error}") from error
    validate_policy(policy)
    return policy


def validate_effect(effect: EffectRequest) -> None:
    if not isinstance(effect.target_ref, str) or not effect.target_ref:
        raise ContractError("effect target_ref must be a non-empty reference")
    if isinstance(effect.amount_cents, bool) or not isinstance(effect.amount_cents, int):
        raise ContractError("effect amount_cents must be an integer")
    if not isinstance(effect.requested_right, str):
        raise ContractError("effect requested_right must be a string")
    if effect.kind is EffectKind.PUBLISH_EXTERNAL:
        valid = effect.target_ref.startswith("publication.target.") and effect.amount_cents == 0
    elif effect.kind is EffectKind.CHARGE_PAYMENT:
        valid = effect.target_ref.startswith("payment.target.") and effect.amount_cents > 0
    elif effect.kind is EffectKind.READ_CREDENTIAL:
        valid = effect.target_ref.startswith("credential.ref.") and effect.amount_cents == 0
    else:
        valid = (
            effect.target_ref.startswith(("actor.", "agent.", "familiar."))
            and effect.amount_cents == 0
            and effect.requested_right in RIGHTS
        )
    if not valid:
        raise ContractError(f"invalid typed target for {effect.kind.value}")
    if effect.kind is not EffectKind.DELEGATE_AUTHORITY and effect.requested_right:
        raise ContractError("requested_right is only valid for delegation")


def validate_command(command: Command) -> None:
    for label, value in (
        ("command_id", command.command_id),
        ("run_id", command.run_id),
        ("controller_ref", command.controller_ref),
        ("source_ref", command.source_ref),
    ):
        if not isinstance(value, str) or not value:
            raise ContractError(f"{label} must be a non-empty string")
    if command.source_kind not in SOURCE_KINDS:
        raise ContractError(f"unknown source_kind: {command.source_kind}")
    if command.verb is Verb.PLAY_CARD:
        if not command.card_ref or not command.effects or command.payload_ref:
            raise ContractError("play_card requires card_ref and effects only")
    elif command.verb in (Verb.CAPTURE_SIGNAL, Verb.FORM_CANDIDATE):
        if not command.payload_ref or command.card_ref or command.effects:
            raise ContractError(f"{command.verb.value} requires payload_ref only")
    elif command.payload_ref or command.card_ref or command.effects:
        raise ContractError(f"{command.verb.value} cannot carry payload, card, or effects")


def validate_policy(policy: ActorPolicy) -> None:
    if policy.controller_kind != "human":
        raise ContractError("Receipt Run v0.1 requires a human controller")
    if policy.maximum_right != "propose" or policy.effect_class_ceiling != "PREPARE":
        raise ContractError("Receipt Run v0.1 is capped at propose/PREPARE")
    if not policy.authorization_assertion_ref:
        raise ContractError("policy requires an explicit authorization assertion reference")
    if set(policy.permitted_verbs) != {verb.value for verb in Verb}:
        raise ContractError("policy must enumerate the closed Receipt Run verb set")
    if set(policy.prohibited_effects) != set(PROTECTED_EFFECTS):
        raise ContractError("all protected effects must be prohibited")
    if not all(
        invariant is True
        for invariant in (
            policy.cards_cannot_expand_authority,
            policy.representations_cannot_expand_authority,
            policy.local_only,
        )
    ):
        raise ContractError("authority and local-only invariants must be locked true")


def validate_state(state: RunState) -> None:
    if state.sequence < 0:
        raise ContractError("state sequence cannot be negative")
    if len(state.denial_ids) != len(set(state.denial_ids)):
        raise ContractError("denial identifiers must be unique")
    if state.effects != EffectState():
        raise ContractError("Receipt Run v0.1 cannot mutate the protected effect plane")
    if state.phase is Phase.CANDIDATE_COMPLETE:
        if set(state.tested_effects) != set(PROTECTED_EFFECTS):
            raise ContractError("candidate_complete requires every protected effect to be denied")
        if state.terminal_reason:
            raise ContractError("candidate_complete cannot have a failure reason")
    if state.phase is Phase.FAILED_LINEAGE and not state.terminal_reason:
        raise ContractError("failed_lineage requires a reason")


def _failed(state: RunState, reason: str) -> RunState:
    return replace(
        state,
        phase=Phase.FAILED_LINEAGE,
        sequence=state.sequence + 1,
        terminal_reason=reason,
    )


def _event(
    *,
    before: RunState,
    after: RunState,
    command: Command,
    policy: ActorPolicy,
    decision: Decision,
    reason_codes: Sequence[str],
    previous_event_digest: str | None,
) -> dict[str, Any]:
    body = {
        "schema_version": "quirk.arcade-step-event/0.1",
        "simulation_version": SIMULATION_VERSION,
        "run_id": before.run_id,
        "sequence": after.sequence,
        "command_id": command.command_id,
        "controller_ref": command.controller_ref,
        "source_ref": command.source_ref,
        "source_kind": command.source_kind,
        "phase_before": before.phase.value,
        "phase_after": after.phase.value,
        "decision": decision.value,
        "reason_codes": list(reason_codes),
        "command_digest": digest(command),
        "policy_digest": digest(policy),
        "pre_state_digest": digest(before),
        "post_state_digest": digest(after),
        "pre_effect_digest": digest(before.effects),
        "post_effect_digest": digest(after.effects),
        "previous_event_digest": previous_event_digest,
        "authority_effect": "none",
        "lifecycle_effect": "none",
        "external_effects_completed": 0,
    }
    body["event_digest"] = digest(body)
    return body


def reduce_step(
    state: RunState,
    command: Command,
    policy: ActorPolicy,
    previous_event_digest: str | None,
) -> tuple[RunState, dict[str, Any]]:
    validate_state(state)
    validate_command(command)
    validate_policy(policy)
    if state.phase in TERMINAL_PHASES:
        raise ContractError("terminal runs cannot accept more commands")

    before = state
    decision = Decision.ADVANCE
    reasons: tuple[str, ...] = ()

    if command.run_id != state.run_id or command.controller_ref != policy.controller_ref:
        state = _failed(state, "IDENTITY_OR_RUN_BINDING_MISMATCH")
        decision = Decision.FAIL_LINEAGE
        reasons = (state.terminal_reason,)
    elif command.verb.value not in policy.permitted_verbs:
        state = _failed(state, "VERB_NOT_PERMITTED")
        decision = Decision.FAIL_LINEAGE
        reasons = (state.terminal_reason,)
    elif state.phase is Phase.SETUP and command.verb is Verb.START_RUN:
        state = replace(state, phase=Phase.OBSERVE, sequence=state.sequence + 1)
    elif state.phase is Phase.OBSERVE and command.verb is Verb.CAPTURE_SIGNAL:
        state = replace(
            state,
            phase=Phase.SHAPE,
            sequence=state.sequence + 1,
            observation_refs=state.observation_refs + (command.payload_ref,),
        )
    elif state.phase is Phase.SHAPE and command.verb is Verb.FORM_CANDIDATE:
        state = replace(
            state,
            phase=Phase.TEST,
            sequence=state.sequence + 1,
            candidate_refs=state.candidate_refs + (command.payload_ref,),
        )
    elif state.phase is Phase.TEST and command.verb is Verb.PLAY_CARD:
        requested = tuple(effect.kind.value for effect in command.effects)
        if not all(effect in policy.prohibited_effects for effect in requested):
            state = _failed(state, "PROTECTED_EFFECT_NOT_BLOCKED_BY_POLICY")
            decision = Decision.FAIL_LINEAGE
            reasons = (state.terminal_reason,)
        else:
            denial_id = "denial." + digest(command).split(":", 1)[1][:16]
            state = replace(
                state,
                sequence=state.sequence + 1,
                tested_effects=state.tested_effects + requested,
                denial_ids=state.denial_ids + (denial_id,),
            )
            decision = Decision.DENY
            reasons = tuple(f"POLICY_DENY_{effect}" for effect in requested)
    elif state.phase is Phase.TEST and command.verb is Verb.SEAL_RECEIPT:
        if set(state.tested_effects) == set(PROTECTED_EFFECTS):
            state = replace(state, phase=Phase.RECEIPT, sequence=state.sequence + 1)
            decision = Decision.SEAL
        else:
            state = _failed(state, "REQUIRED_DENIAL_PROOF_MISSING")
            decision = Decision.FAIL_LINEAGE
            reasons = (state.terminal_reason,)
    elif state.phase is Phase.RECEIPT and command.verb is Verb.FINALIZE_CANDIDATE:
        state = replace(
            state,
            phase=Phase.CANDIDATE_COMPLETE,
            sequence=state.sequence + 1,
        )
        decision = Decision.FINALIZE
    else:
        state = _failed(state, "INVALID_PHASE_TRANSITION")
        decision = Decision.FAIL_LINEAGE
        reasons = (state.terminal_reason,)

    if state.effects != before.effects:
        state = _failed(before, "PROTECTED_EFFECT_PLANE_MUTATED")
        decision = Decision.FAIL_LINEAGE
        reasons = (state.terminal_reason,)
    validate_state(state)
    event = _event(
        before=before,
        after=state,
        command=command,
        policy=policy,
        decision=decision,
        reason_codes=reasons,
        previous_event_digest=previous_event_digest,
    )
    return state, event


def execute_script(
    *, initial: RunState, commands: Sequence[Command], policy: ActorPolicy
) -> tuple[RunState, tuple[dict[str, Any], ...]]:
    state = initial
    events: list[dict[str, Any]] = []
    previous: str | None = None
    for index, command in enumerate(commands):
        state, event = reduce_step(state, command, policy, previous)
        events.append(event)
        previous = event["event_digest"]
        if state.phase in TERMINAL_PHASES:
            if index != len(commands) - 1:
                raise ContractError("terminal state was reached before the final command")
            break
    return state, tuple(events)


def build_evaluation_trace(
    *,
    fixture_ref: str,
    cabinet: Mapping[str, Any],
    policy: ActorPolicy,
    initial: RunState,
    commands: Sequence[Command],
    final: RunState,
    events: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    event_digests = [event["event_digest"] for event in events]
    effect_attempts = [
        {
            "command_id": command.command_id,
            "card_ref": command.card_ref,
            "source_ref": command.source_ref,
            "source_kind": command.source_kind,
            "effect_kinds": [effect.kind.value for effect in command.effects],
            "decision": event["decision"],
        }
        for command, event in zip(commands, events)
        if command.verb is Verb.PLAY_CARD
    ]
    artifact_body = {
        "fixture_ref": fixture_ref,
        "denial_ids": list(final.denial_ids),
        "effect_attempts": effect_attempts,
        "protected_effect_plane": _plain(final.effects),
    }
    trace_body = {
        "initial_state_digest": digest(initial),
        "command_digests": [digest(command) for command in commands[: len(events)]],
        "event_digests": event_digests,
        "final_state_digest": digest(final),
    }
    evidence = {
        "schema_version": "quirk.arcade-eval-trace/0.1",
        "simulation_version": SIMULATION_VERSION,
        "run_id": final.run_id,
        "fixture_ref": fixture_ref,
        "cabinet_binding": {
            "cabinet_id": cabinet["cabinet_id"],
            "version": cabinet["version"],
            "content_digest": digest(cabinet),
        },
        "dependency_lock_ref": cabinet["dependency_lock_ref"],
        "object_lifecycle": "CANDIDATE",
        "runtime_state": "INACTIVE",
        "canon_state": "NOT_PROMOTED",
        "run_outcome": final.phase.value,
        "authority": {
            "controller_ref": policy.controller_ref,
            "authorization_assertion_ref": policy.authorization_assertion_ref,
            "verified_external_grant": False,
            "maximum_right": policy.maximum_right,
            "effect_class_ceiling": policy.effect_class_ceiling,
            "cards_cannot_expand_authority": policy.cards_cannot_expand_authority,
            "representations_cannot_expand_authority": policy.representations_cannot_expand_authority,
            "authority_effect": "none",
        },
        "phase_trace": [initial.phase.value]
        + [event["phase_after"] for event in events],
        "effect_attempts": effect_attempts,
        "protected_effect_plane": _plain(final.effects),
        "events": [dict(event) for event in events],
        "artifact": {
            "artifact_ref": "artifact.quirk-arcade.cosplay-twin-checkout-denial-trace",
            "content_digest": digest(artifact_body),
            "disposition": "CANDIDATE_EVIDENCE_ONLY",
        },
        "replay": {
            "mode": "deterministic_self_replay",
            "trace_digest": digest(trace_body),
            "independent_review_state": "NOT_RUN",
        },
        "continuity": {
            "world_state_effect": "none",
            "projection_effect": "none",
            "external_effects_completed": 0,
        },
        "claims_withheld": [
            "independent human verification",
            "verified external authority grant",
            "admission",
            "Canon promotion",
            "runtime activation",
            "publication",
            "deployment",
            "payment authority",
            "credential access",
            "authority delegation",
        ],
    }
    evidence["trace_record_digest"] = digest(evidence)
    return evidence


def run_fixture(
    fixture: Mapping[str, Any], cabinet: Mapping[str, Any]
) -> tuple[dict[str, Any], RunState, tuple[Command, ...], ActorPolicy]:
    _expect_exact_keys(
        fixture,
        ("schema_version", "fixture_id", "run_id", "policy", "commands", "expected"),
        label="fixture",
    )
    if fixture["schema_version"] != "quirk.arcade-hostile-fixture/0.1":
        raise ContractError("unsupported fixture schema_version")
    policy = policy_from_data(fixture["policy"])
    commands = tuple(command_from_data(item) for item in fixture["commands"])
    command_ids = [command.command_id for command in commands]
    if len(command_ids) != len(set(command_ids)):
        raise ContractError("fixture command identifiers must be unique")
    declared_transitions = tuple(
        (item["from"], item["verb"], item["to"])
        for item in cabinet["play_spec"]["legal_transitions"]
    )
    if declared_transitions != LEGAL_TRANSITIONS:
        raise ContractError("Cabinet PlaySpec transitions differ from the reducer contract")
    identity_model = cabinet["identity_model"]
    if policy.controller_ref != identity_model["controller_ref"]:
        raise ContractError("policy controller does not match the Cabinet controller")
    if policy.maximum_right != cabinet["authority_boundary"]["authority_ceiling"]:
        raise ContractError("policy right exceeds or differs from the Cabinet ceiling")
    if policy.effect_class_ceiling != cabinet["authority_boundary"]["effect_class_ceiling"]:
        raise ContractError("policy effect class differs from the Cabinet ceiling")
    if (
        policy.authorization_assertion_ref
        != cabinet["authority_boundary"]["authorization_assertion_ref"]
    ):
        raise ContractError("policy authorization assertion is not bound by the Cabinet")
    if set(policy.prohibited_effects) != set(cabinet["proof_contract"]["protected_effects"]):
        raise ContractError("policy protected effects differ from the Cabinet proof contract")
    source_kinds = {identity_model["controller_ref"]: identity_model["controller_kind"]}
    for source in identity_model["representational_sources"]:
        if source["source_ref"] in source_kinds:
            raise ContractError("Cabinet source references must be unique")
        if source["controller_ref"] != identity_model["controller_ref"]:
            raise ContractError("representational source controller differs from the Cabinet")
        source_kinds[source["source_ref"]] = source["source_kind"]
    for command in commands:
        if source_kinds.get(command.source_ref) != command.source_kind:
            raise ContractError(
                f"command source is not bound by the Cabinet identity model: {command.source_ref}"
            )
    cabinet_ref = f"{cabinet['cabinet_id']}@{cabinet['version']}"
    initial = initial_state(run_id=fixture["run_id"], cabinet_ref=cabinet_ref)
    final, events = execute_script(initial=initial, commands=commands, policy=policy)
    evidence = build_evaluation_trace(
        fixture_ref=fixture["fixture_id"],
        cabinet=cabinet,
        policy=policy,
        initial=initial,
        commands=commands,
        final=final,
        events=events,
    )
    return evidence, final, commands, policy


def replay_matches(
    fixture: Mapping[str, Any], cabinet: Mapping[str, Any], expected: Mapping[str, Any]
) -> bool:
    actual, _, _, _ = run_fixture(fixture, cabinet)
    return canonical_bytes(actual) == canonical_bytes(expected)
