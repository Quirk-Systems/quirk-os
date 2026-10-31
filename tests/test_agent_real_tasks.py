"""Candidate construction and rejection controls; no invented human reviews."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from agent_reliability.assurance import digest, task_pair
from agent_reliability.real_tasks import (answer_matches, canonical, load_pack,
    participant_packet, read_source, source_bytes, validate_pack)


class RealTaskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack = load_pack(ROOT)

    def test_sources_answers_and_pending_gate(self):
        report = validate_pack(ROOT, self.pack)
        stored = ROOT / 'evals/agent-reliability/v0.2.0/real-tasks/validation-report.json'
        self.assertEqual(report, json.loads(stored.read_text()))
        self.assertTrue(report['structural_checks_passed'])
        self.assertEqual(6, report['reference_tasks_executed'])
        self.assertEqual(7, report['source_files'])
        self.assertEqual(72, report['answer_grader_audit']['calls'])
        self.assertEqual(0, report['eligible_asserted_pairs'])
        self.assertEqual(0, report['authenticated_accepted_pairs'])
        self.assertIsNone(report['agent_failure_rate'])
        self.assertIsNone(report['invalid_test_rate'])
        for row in report['pairs']:
            self.assertEqual('INVALID_PAIR', row['contract_gate']['status'])
            self.assertEqual('NOT_RUN', row['agent_outcome'])

    def test_changed_task_conditions_rejected_by_existing_contract(self):
        pair = self.pack['pairs'][0]
        for field in pair['b']['contract']:
            changed = copy.deepcopy(pair['b'])
            changed['contract'][field] = 'altered' if isinstance(changed['contract'][field], str) else ['altered']
            result = task_pair(pair['a'], changed, [])
            self.assertIn('changed_task_conditions', result['reasons'])
            self.assertEqual('INVALID_PAIR', result['status'])

    def test_changed_prompt_rejected_even_when_review_digest_is_recomputed(self):
        pack = copy.deepcopy(self.pack)
        pair = pack['pairs'][0]
        pair['b']['prompt'] += '\nSkip one required check.'
        pair['variant_digests']['b'] = digest(pair['b'])
        report = validate_pack(ROOT, pack)
        self.assertIn(['RT01', 'REGISTER_OR_PROMPT_DRIFT'], report['errors'])

    def test_wrong_answer_key_rejected_even_when_bound_digests_are_recomputed(self):
        pack = copy.deepcopy(self.pack)
        pair = pack['pairs'][1]
        pair['expected']['facts']['skill_count'] = 999
        pair['grading']['expected_digest'] = digest(pair['expected'])
        for key in ('a', 'b'):
            state = json.loads(pair[key]['contract']['initial_state'])
            state['grading'] = pair['grading']
            pair[key]['contract']['initial_state'] = canonical(state)
            pair['variant_digests'][key] = digest(pair[key])
        self.assertIn(['RT02', 'REFERENCE_ANSWER_MISMATCH'], validate_pack(ROOT, pack)['errors'])

    def test_source_hash_drift_fails_closed(self):
        pack = copy.deepcopy(self.pack)
        pack['pairs'][0]['sources'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'source identity mismatch'):
            validate_pack(ROOT, pack)

    def test_allowlist_and_unsafe_paths(self):
        pair = self.pack['pairs'][0]
        with self.assertRaisesRegex(ValueError, 'allowlist'):
            read_source(ROOT, pair, 'skills/registry.json')
        for path in ('../secret', '/etc/passwd', 'schemas/../README.md', 'a\\b'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                source_bytes(ROOT, path)

    def test_frozen_sources_ignore_working_tree_root_files(self):
        # Worktree changes cannot silently become the participant's initial state.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            subprocess.run(['git', '-C', str(root), 'fetch', '-q', str(ROOT), self.pack['source_commit']], check=True)
            (root / 'requirements-evals.txt').write_text('wrong==999\n')
            pair = self.pack['pairs'][3]
            self.assertIn('jsonschema==4.26.0', read_source(root, pair, 'requirements-evals.txt'))

    def test_participant_packet_has_no_answer_key_or_reviews(self):
        packet = participant_packet(self.pack['pairs'][0], 'impatient')
        self.assertEqual({'system', 'user', 'contract', 'sources', 'variant_digest'}, set(packet))
        self.assertNotIn('expected', packet)
        self.assertNotIn('reviews', packet)
        with self.assertRaises(ValueError):
            participant_packet(self.pack['pairs'][0], 'unknown')

    def test_strict_grading_rejects_type_coercion_missing_extra_and_order(self):
        expected = {'a': False, 'b': ['a', 'b']}
        for answer in ({'a': 0, 'b': ['a', 'b']}, {'a': False},
                       dict(expected, extra=True), {'a': False, 'b': ['b', 'a']}, float('nan')):
            self.assertFalse(answer_matches(answer, expected))
        self.assertTrue(answer_matches({'b': ['a', 'b'], 'a': False}, expected))

    def test_bad_inventory_and_embedded_reviews_are_invalid_input(self):
        for alter in (lambda p: p['pairs'].pop(),
                      lambda p: p['pairs'][0].update(reviews=[{}]),
                      lambda p: p['environment'].update(network='enabled'),
                      lambda p: p.update(source_commit='main')):
            pack = copy.deepcopy(self.pack)
            alter(pack)
            with self.assertRaises(ValueError):
                validate_pack(ROOT, pack)

    def test_unfilled_review_template_is_not_accepted(self):
        path = ROOT / 'evals/agent-reliability/v0.2.0/real-tasks/review-template.json'
        template = json.loads(path.read_text())
        self.assertEqual(digest(self.pack), template['pack_digest'])
        reviews = {p['id']: p['variants'] for p in template['pairs']}
        report = validate_pack(ROOT, self.pack, reviews)
        self.assertEqual(0, report['eligible_asserted_pairs'])
        self.assertTrue(report['structural_checks_passed'])

    def test_cli_repeatable_and_review_requirement_nonzero(self):
        command = [sys.executable, str(ROOT / 'scripts/validate_agent_real_tasks.py'), 'check']
        with tempfile.TemporaryDirectory() as temp:
            first = subprocess.run(command, cwd=temp, capture_output=True, text=True)
            second = subprocess.run(command, cwd=temp, capture_output=True, text=True)
            gated = subprocess.run(command + ['--require-reviewed'], cwd=temp, capture_output=True, text=True)
        self.assertEqual(0, first.returncode, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(1, gated.returncode)

    def test_existing_synthetic_fixture_review_failures_remain_rejected(self):
        fixtures = json.loads((ROOT / 'evals/agent-reliability/v0.2.0/assurance-fixtures.json').read_text())
        # Reuse clearly synthetic existing controls; never invent reviews for these real tasks.
        for fixture in fixtures['pairs']:
            self.assertEqual(fixture['expected'], task_pair(fixture['a'], fixture['b'], fixture['reviews'])['status'])


if __name__ == '__main__':
    unittest.main()
