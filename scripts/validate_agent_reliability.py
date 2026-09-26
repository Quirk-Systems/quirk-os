"""Print a reproducible candidate-only report for the agent reliability pack."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agent_reliability.runner import run_pack


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=Path("evals/agent-reliability/v0.1.0/fixtures.json"))
    parser.add_argument("--observations", type=Path, help="Optional separately recorded traces; never treated as authenticated deployment evidence")
    args = parser.parse_args()
    pack = json.loads(args.fixtures.read_text(encoding="utf-8"))
    observations = json.loads(args.observations.read_text(encoding="utf-8")) if args.observations else None
    try:
        result = run_pack(pack, observations)
    except (KeyError, TypeError, ValueError) as error:
        print(f"invalid observations or fixture version: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, indent=2))
    return 1 if result["failed_fixture_ids"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
