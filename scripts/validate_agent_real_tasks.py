"""Prepare/check frozen real-task candidates; never invoke a model or grant authority."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from agent_reliability.real_tasks import (answer_matches, load_pack,
    participant_packet, read_source, validate_pack)

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    check = sub.add_parser('check', help='check sources, answers, contracts and review state')
    check.add_argument('--reviews', type=Path, help='six-ID map of actual independent review assertions')
    check.add_argument('--require-reviewed', action='store_true', help='exit 1 unless all six assertion gates pass')
    packet = sub.add_parser('packet', help='emit a participant packet without answer keys or review data')
    packet.add_argument('task')
    packet.add_argument('register', choices=['cooperative', 'impatient'])
    source = sub.add_parser('read-source', help='read one allowlisted blob from the frozen commit')
    source.add_argument('task')
    source.add_argument('path')
    grade = sub.add_parser('grade', help='compare an answer file; no agent outcome inferred')
    grade.add_argument('task')
    grade.add_argument('answer', type=Path)
    args = parser.parse_args(argv)
    try:
        pack = load_pack(ROOT)
        if args.command == 'check':
            reviews = json.loads(args.reviews.read_text()) if args.reviews else None
            result = validate_pack(ROOT, pack, reviews)
            code = 0 if result['structural_checks_passed'] else 1
            if args.require_reviewed and result['eligible_asserted_pairs'] != 6:
                code = 1
        else:
            # Never expose a packet or grade a corrupted pack.
            if not validate_pack(ROOT, pack)['structural_checks_passed']:
                raise ValueError('pack validation failed')
            pair = next((p for p in pack['pairs'] if p['id'] == args.task), None)
            if pair is None:
                raise ValueError('unknown task')
            code = 0
            if args.command == 'packet':
                result = participant_packet(pair, args.register)
            elif args.command == 'read-source':
                print(read_source(ROOT, pair, args.path), end='')
                return 0
            else:
                answer = json.loads(args.answer.read_text(encoding='utf-8'))
                matches = answer_matches(answer, pair['expected'])
                result = {'task': pair['id'], 'answer_matches': matches,
                          'scope': 'ANSWER_CHECK_ONLY_NOT_AN_AGENT_OUTCOME', 'authority_effect': False}
                code = 0 if matches else 1
        print(json.dumps(result, indent=2, sort_keys=True))
        return code
    except (OSError, ValueError, TypeError, KeyError, AttributeError, subprocess.CalledProcessError) as error:
        print(f'invalid real-task input: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
