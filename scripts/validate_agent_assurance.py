"""Audit existing graders and run synthetic disclosure/task-integrity fixtures."""
import argparse
import json
import sys
from pathlib import Path
from agent_reliability.assurance import run_assurance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        result = run_assurance(Path(__file__).resolve().parents[1])
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(f'invalid assurance input: {error}', file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
