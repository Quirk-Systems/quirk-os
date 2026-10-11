"""Bounded observation loop and step decomposition; no repair executor."""

import hashlib
import json

from .repair_routes import evaluate_with_routes

VERSION = "verification-repair-loop.v0.1.0"


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def decompose(report):
    """Make dependency-ordered investigation, mutation and verification proposals."""
    steps = []
    previous = None
    for route in report["routes"]:
        for phase, action, proof in (
            ("inspect", route["question"], "Source-bound observation identifying this blocker."),
            ("propose", route["proposed_action"], "Exact bounded change, affected dependencies and recovery path."),
            ("verify", "Collect the required proof, then reevaluate the original goal.", route["resume_proof"]),
        ):
            step_id = route["id"] + "." + phase
            steps.append({"id": step_id, "route": route["id"], "phase": phase,
                          "action": action, "requires": [previous] if previous else [],
                          "completion_proof": proof, "state": "PROPOSED",
                          "executable": False, "next_gate": route["next_gate"]})
            previous = step_id
    return steps


def _binding(payload):
    """Freeze task obligations and requested authority across the loop."""
    case = payload["case"]
    if payload["kind"] == "completion":
        required = case.get("required_ids")
        if not isinstance(required, list) or not required or any(not isinstance(v, str) or not v for v in required) or len(set(required)) != len(required):
            raise ValueError("invalid goal obligations")
        return {"kind": "completion", "required_ids": sorted(required)}
    request = case.get("request")
    if not isinstance(request, dict) or set(request) != {"principal", "verb", "object_id", "scope"} or any(not isinstance(v, str) or not v for v in request.values()):
        raise ValueError("invalid requested authority")
    return {"kind": "authority", "request": request}


def plan_loop(payload):
    """Evaluate supplied observations, preserving regressions and stop reasons.

    Callers collect observations separately. Structural blocker reduction is
    explicitly distinct from measured user benefit and authenticated proof.
    """
    if not isinstance(payload, dict) or set(payload) != {"goal_id", "round_limit", "observations"}:
        raise ValueError("invalid loop contract")
    if not isinstance(payload["goal_id"], str) or not payload["goal_id"].strip():
        raise ValueError("invalid goal id")
    limit = payload["round_limit"]
    observations = payload["observations"]
    if type(limit) is not int or not 1 <= limit <= 3 or not isinstance(observations, list) or not 1 <= len(observations) <= limit:
        raise ValueError("invalid round budget")
    frames, binding, prior, plateau = [], None, None, 0
    stop = None
    for observation in observations:
        if stop is not None:
            raise ValueError("observations continue beyond stop condition")
        if not isinstance(observation, dict) or set(observation) != {"evaluation", "mutation_id"}:
            raise ValueError("invalid observation")
        mutation = observation["mutation_id"]
        if not isinstance(mutation, str) or not mutation.strip() or len(mutation) > 128:
            raise ValueError("invalid mutation id")
        if any(frame["mutation_digest"] == _digest(mutation) for frame in frames):
            raise ValueError("repeated mutation")
        report = evaluate_with_routes(observation["evaluation"])
        current_binding = _binding(observation["evaluation"])
        if binding is not None and current_binding != binding:
            raise ValueError("goal or requested authority changed")
        binding = current_binding
        reasons = {reason for route in report["routes"] for reason in route.get("reasons", [])}
        removed, added = (prior - reasons, reasons - prior) if prior is not None else (set(), set())
        comparison = "BASELINE" if prior is None else "TRADEOFF" if removed and added else "REGRESSED" if added else "BLOCKERS_REDUCED" if removed else "NO_CHANGE"
        plateau = plateau + 1 if comparison == "NO_CHANGE" else 0
        route_ids = {route["id"] for route in report["routes"]}
        if "authority" in route_ids:
            stop = "AUTHORITY_RECONCILIATION"
        elif "input_contract" in route_ids or "unmapped_failure" in route_ids:
            stop = "CONTRACT_REPAIR"
        elif report["status"] == "CANDIDATE_ONLY":
            stop = "CANDIDATE_REVIEW"
        elif comparison in {"REGRESSED", "TRADEOFF"}:
            stop = "REGRESSION_REVIEW"
        elif plateau >= 2:
            stop = "NO_PROGRESS"
        frames.append({"index": len(frames), "observation_digest": _digest(observation),
                       "mutation_digest": _digest(mutation), "status": report["status"],
                       "comparison": comparison, "resolved_reasons": sorted(removed),
                       "new_reasons": sorted(added), "remaining_reasons": sorted(reasons),
                       "routes": report["routes"], "steps": decompose(report)})
        prior = reasons
    if stop is None:
        stop = "BUDGET_STOP" if len(frames) == limit else "AWAIT_OBSERVATION"
    return {"version": VERSION, "goal_digest": _digest(payload["goal_id"]),
            "binding_digest": _digest(binding), "frames": frames, "stop_reason": stop,
            "rounds_used": len(frames), "rounds_remaining": limit - len(frames),
            "authority_effect": False, "effects_executed": 0,
            "benefit_status": "NOT_MEASURED",
            "limits": ["Supplied observations and mutations are not authenticated.",
                       "Blocker reduction is structural evidence, not user benefit or causal proof.",
                       "This planner proposes steps; it does not execute repairs or grant authority."]}
