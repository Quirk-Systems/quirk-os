"""Read an evaluation case and emit proposed repair routes; no effects."""

import argparse
import json
import sys
from pathlib import Path

from agent_reliability.repair_routes import evaluate_with_routes
from agent_reliability.repair_loop import plan_loop

MAX_INPUT_BYTES = 1024 * 1024


def reject_constant(value):
    raise ValueError("nonfinite JSON number")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON object with kind and case")
    parser.add_argument("--loop", action="store_true", help="Evaluate bounded loop observations and decompose routes into steps")
    args = parser.parse_args()
    try:
        with args.input.open("rb") as handle:
            raw = handle.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise ValueError("input exceeds byte budget")
        payload = json.loads(raw, parse_constant=reject_constant, object_pairs_hook=unique_object)
        report = plan_loop(payload) if args.loop else evaluate_with_routes(payload)
    except (OSError, ValueError, TypeError, RecursionError):
        # Do not expose input fragments, sensitive path text or parser messages.
        print(json.dumps({"status": "INVALID_INPUT", "authority_effect": False, "effects_executed": 0}), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.loop:
        return 0 if report["stop_reason"] == "CANDIDATE_REVIEW" else 1
    return 1 if report["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())

