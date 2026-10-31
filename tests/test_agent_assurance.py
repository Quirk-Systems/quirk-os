"""Regression and deliberately defective grader controls; synthetic only."""
import copy
import json
import sys
import subprocess
import tempfile
from unittest.mock import patch
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from agent_reliability.assurance import audit_grader, disclosure, task_pair, digest, run_assurance


class AssuranceTests(unittest.TestCase):
    def test_malformed_nested_contract_fails_closed(self):
        for value in (None, [], 1, 'text', True):
            with self.subTest(value=value):
                self.assertEqual('INVALID_PAIR', task_pair({'contract': value}, {'contract': value}, [])['status'])

    def test_fixture_expectations_cannot_be_relabelled(self):
        original = Path.read_text
        def changed(path, *args, **kwargs):
            text = original(path, *args, **kwargs)
            if path.name == 'assurance-fixtures.json':
                data = json.loads(text)
                data['pairs'][0]['expected'] = 'INVALID_PAIR'
                return json.dumps(data)
            return text
        with patch.object(Path, 'read_text', changed), self.assertRaises(ValueError):
            run_assurance(ROOT)

    def test_malformed_inventory_is_value_error(self):
        original = Path.read_text
        for value in (None, [], {'version': 'agent-assurance.v0.2.0', 'disclosure': None}):
            def changed(path, *args, **kwargs):
                if path.name == 'assurance-fixtures.json':
                    return json.dumps(value)
                return original(path, *args, **kwargs)
            with patch.object(Path, 'read_text', changed), self.assertRaises(ValueError):
                run_assurance(ROOT)
    def setUp(self):
        self.controls = [{'id': str(i), 'case': {'value': i}, 'expected': i % 2 == 0} for i in range(6)]

    def test_honest_grader(self):
        before = copy.deepcopy(self.controls)
        self.assertTrue(audit_grader(lambda c: c['value'] % 2 == 0, self.controls)['passed'])
        self.assertEqual(before, self.controls)

    def test_four_defects_detected(self):
        def mutator(c):
            answer = c['value'] % 2 == 0
            c['value'] = 999
            return answer
        count = [0]
        def order_dependent(c):
            count[0] += 1
            return count[0] % 2 == 1
        def throwing(c):
            raise RuntimeError('not a pass')
        for grader in (mutator, order_dependent, lambda c: True, throwing):
            with self.subTest(grader=grader):
                self.assertFalse(audit_grader(grader, self.controls)['passed'])

    def test_invalid_controls(self):
        for controls in ([], self.controls + [self.controls[0]], [{'id': 'x', 'case': {}, 'expected': 1}]):
            with self.assertRaises(ValueError):
                audit_grader(lambda c: True, controls)

    def test_non_boolean_result_is_not_pass(self):
        self.assertFalse(audit_grader(lambda c: 1, self.controls)['passed'])

    def test_disclosure_bindings(self):
        c = {'object_id': 'update:1', 'destination': 'public:review', 'purpose': 'status', 'payload': 'ready'}
        p = dict(c, payload_digest=digest(c['payload']), classification='public', allowed_classifications=['public'])
        p.pop('payload')
        self.assertTrue(disclosure(c, p)['eligible_candidate'])
        for field, value in [('payload', 'private password'), ('object_id', 'other'), ('destination', 'elsewhere'), ('purpose', 'advertising')]:
            changed = dict(c, **{field: value})
            self.assertFalse(disclosure(changed, p)['eligible_candidate'])
        p['classification'] = 'secret'
        self.assertFalse(disclosure(c, p)['eligible_candidate'])

    def test_bad_disclosure_shapes(self):
        for value in (None, [], {}, {'payload': 'text'}):
            self.assertFalse(disclosure(value, {})['eligible_candidate'])

    def test_task_pair(self):
        contract = {'goal': 'answer', 'tools': ['read'], 'permissions': ['read'], 'constraints': ['no writes'], 'initial_state': 'state:1'}
        a = {'contract': contract, 'register': 'cooperative'}
        b = {'contract': copy.deepcopy(contract), 'register': 'impatient'}
        reviews = [{'subject_digest': digest(x), 'valid': True, 'reviewer': 'human:reviewer', 'producer': 'model:builder'} for x in (a, b)]
        self.assertEqual('ELIGIBLE_ASSERTED_PAIR', task_pair(a, b, reviews)['status'])
        for field in contract:
            changed = copy.deepcopy(b)
            changed['contract'][field] = 'changed'
            self.assertEqual('INVALID_PAIR', task_pair(a, changed, reviews)['status'])
        reviews[1]['reviewer'] = 'model:builder'
        self.assertEqual('INVALID_PAIR', task_pair(a, b, reviews)['status'])

    def test_missing_invalid_or_stale_review(self):
        a = {'contract': {}, 'register': 'cooperative'}
        for reviews in ([], None, [{'valid': True}]):
            self.assertEqual('INVALID_PAIR', task_pair(a, a, reviews)['status'])

    def test_integrated_report(self):
        report = run_assurance(ROOT)
        self.assertTrue(report['passed'])
        self.assertFalse(report['authority_effect'])
        self.assertEqual('NO_LIVE_MODEL_OBSERVATIONS', report['observation_status'])

    def test_cli_repeatable_outside_repository_cwd(self):
        command = [sys.executable, str(ROOT / 'scripts/validate_agent_assurance.py')]
        with tempfile.TemporaryDirectory() as directory:
            first = subprocess.run(command, cwd=directory, capture_output=True, text=True)
            second = subprocess.run(command, cwd=directory, capture_output=True, text=True)
        self.assertEqual(0, first.returncode, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        self.assertTrue(json.loads(first.stdout)['passed'])

    def test_synthetic_negative_pairs_do_not_count_as_agent_errors(self):
        fixtures = json.loads((ROOT / 'evals/agent-reliability/v0.2.0/assurance-fixtures.json').read_text())
        results = [task_pair(f['a'], f['b'], f['reviews'])['status'] for f in fixtures['pairs']]
        self.assertEqual(3, results.count('INVALID_PAIR'))
        self.assertEqual(3, results.count('ELIGIBLE_ASSERTED_PAIR'))

if __name__ == '__main__':
    unittest.main()
