"""Regression tests for the isolated candidate; fixtures are synthetic."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
TARGET = Path(os.environ.get('VALIDATOR_UNDER_TEST', str(Path(__file__).with_name('validate_evidence_bundle.py'))))
spec = importlib.util.spec_from_file_location('validator_under_test', TARGET)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture():
    return {
        'bundle_version': 'synthetic-fixture-1',
        'source_census': {key: [] for key in module.REQUIRED_CENSUS_KEYS},
        'run_receipt': {'run_id': 'synthetic', 'inputs': {'fingerprints': ['fixture-only']},
                        'execution': {}, 'outputs': {}, 'quality': {},
                        'lineage': {'transformation_refs': []}},
        'authority_decisions': [], 'proposed_moves': [], 'system_dividend': {},
    }


def authority(allowed=True, explicit=False, action='canon_write'):
    data = fixture()
    data['authority_decisions'] = [{'action': action, 'allowed': allowed, 'explicit_authority': explicit}]
    return data


class ValidatorRegression(unittest.TestCase):
    def invalid(self, data):
        result = module.validate(data)
        self.assertIs(result['valid'], False)
        self.assertIsInstance(result['errors'], list)
        self.assertTrue(result['errors'])

    def test_valid_minimal_bundle_preserved(self):
        result = module.validate(fixture())
        self.assertIs(result['valid'], True)
        self.assertTrue(result['warnings'])

    def test_valid_full_shapes_and_extensions_preserved(self):
        data = fixture()
        data['authority_decisions'] = authority(True, True)['authority_decisions']
        data['proposed_moves'] = [{'status': 'candidate', 'evidence_refs': ['synthetic'], 'extra': {'future': 1}}]
        data['run_receipt'].update({'economics': {'compute_cost': None}, 'outcome': {'accepted': False}})
        data['future_extension'] = {'opaque': [1, None, {'a': 'b'}]}
        before = copy.deepcopy(data)
        self.assertIs(module.validate(data)['valid'], True)
        self.assertEqual(data, before)

    def test_protected_action_boolean_false_rejected(self):
        self.invalid(authority(True, False))

    def test_protected_explicit_true_is_structurally_valid(self):
        self.assertIs(module.validate(authority(True, True))['valid'], True)

    def test_truthy_string_explicit_authority_rejected(self):
        self.invalid(authority(True, 'false'))

    def test_nonboolean_explicit_authority_values_rejected(self):
        for value in [1, 0, None, '', [], {}]:
            with self.subTest(value=value):
                self.invalid(authority(True, value))

    def test_numeric_allowed_rejected(self):
        self.invalid(authority(1, False))

    def test_other_nonboolean_allowed_values_rejected(self):
        for value in [0, None, 'true', 'false', [], {}]:
            with self.subTest(value=value):
                self.invalid(authority(value, False))

    def test_nonprotected_numeric_permission_also_rejected(self):
        self.invalid(authority(1, False, 'observe'))

    def test_missing_permission_rejected(self):
        data = authority()
        del data['authority_decisions'][0]['allowed']
        self.invalid(data)

    def test_explicit_not_required_for_denied_action(self):
        data = authority(False, False)
        del data['authority_decisions'][0]['explicit_authority']
        self.assertIs(module.validate(data)['valid'], True)

    def test_capability_never_grants_authority(self):
        data = authority(True, True, 'observe')
        data['authority_decisions'][0]['authority_basis'] = 'capability'
        self.invalid(data)

    def test_malformed_action_and_collection_entries(self):
        for value in [None, [], {}, 1, '']:
            with self.subTest(action=value):
                data = authority()
                data['authority_decisions'][0]['action'] = value
                self.invalid(data)
        for key in ['authority_decisions', 'proposed_moves']:
            with self.subTest(collection=key):
                data = fixture()
                data[key] = [None]
                self.invalid(data)

    def test_padded_action_names_cannot_evade_protection(self):
        for action in ['canon_write ', ' canon_write', '\tcanon_write', 'canon_write\n']:
            with self.subTest(action=action):
                self.invalid(authority(True, False, action))

    def test_unknown_actions_are_unsupported_even_with_explicit_flag(self):
        for allowed in [True, False]:
            with self.subTest(allowed=allowed):
                self.invalid(authority(allowed, True, 'future_production_release'))

    def test_known_control_rights_and_compatibility_action(self):
        for action in ['observe', 'infer', 'propose', 'execute_reversible', 'local_candidate_build']:
            with self.subTest(action=action):
                self.assertIs(module.validate(authority(True, True, action))['valid'], True)

    def test_execute_protected_requires_explicit_boolean_authority(self):
        self.invalid(authority(True, False, 'execute_protected'))
        self.assertIs(module.validate(authority(True, True, 'execute_protected'))['valid'], True)

    def test_candidate_cannot_self_promote(self):
        data = fixture()
        data['proposed_moves'] = [{'status': 'live', 'evidence_refs': ['synthetic']}]
        self.invalid(data)

    def test_null_inputs_returns_structured_invalid(self):
        data = fixture()
        data['run_receipt']['inputs'] = None
        self.invalid(data)

    def test_known_receipt_objects_reject_nonobjects(self):
        for key in ['inputs', 'execution', 'outputs', 'quality', 'lineage', 'economics', 'outcome']:
            for value in [None, [], 'bad', 0, True]:
                with self.subTest(key=key, value=value):
                    data = fixture()
                    data['run_receipt'][key] = value
                    self.invalid(data)

    def test_known_receipt_lists_reject_nonlists(self):
        for section, key in [('inputs', 'fingerprints'), ('inputs', 'source_refs'), ('execution', 'tools'),
                             ('outputs', 'object_refs'), ('outputs', 'output_hashes'),
                             ('quality', 'warnings'), ('lineage', 'transformation_refs'),
                             ('lineage', 'parent_run_ids')]:
            for value in [None, {}, 'bad', 0, True]:
                with self.subTest(section=section, key=key, value=value):
                    data = fixture()
                    data['run_receipt'][section][key] = value
                    self.invalid(data)

    def test_empty_fingerprints_rejected(self):
        data = fixture()
        data['run_receipt']['inputs']['fingerprints'] = []
        self.invalid(data)

    def test_eval_scores_requires_object(self):
        data = fixture()
        data['run_receipt']['quality']['eval_scores'] = []
        self.invalid(data)

    def test_census_lists_and_entries(self):
        for key in module.REQUIRED_CENSUS_KEYS:
            for value in [None, {}, 'bad', [None], ['bad']]:
                with self.subTest(key=key, value=value):
                    data = fixture()
                    data['source_census'][key] = value
                    self.invalid(data)

    def test_proposed_move_evidence_must_be_nonempty_list(self):
        for value in [None, {}, 'synthetic', 1, [], True]:
            with self.subTest(value=value):
                data = fixture()
                data['proposed_moves'] = [{'status': 'candidate', 'evidence_refs': value}]
                self.invalid(data)

    def test_system_dividend_known_containers(self):
        for key in ['structured_data_updates', 'reusable_move_candidates', 'skill_or_capability_candidates',
                    'cleanup_or_mapping_proposals', 'next_proposed_moves']:
            with self.subTest(key=key):
                data = fixture()
                data['system_dividend'][key] = 'bad'
                self.invalid(data)
        data = fixture()
        data['system_dividend']['quality_delta'] = []
        self.invalid(data)

    def test_root_and_top_level_wrong_types(self):
        for data in [None, [], '', 1, True]:
            with self.subTest(root=data):
                self.invalid(data)
        for key in ['source_census', 'run_receipt', 'system_dividend', 'authority_decisions', 'proposed_moves']:
            with self.subTest(key=key):
                data = fixture()
                data[key] = None
                self.invalid(data)

    def test_malformed_nested_objects_dont_crash_cli(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'malformed.json'
            data = fixture()
            data['run_receipt']['inputs'] = None
            path.write_text(json.dumps(data))
            proc = subprocess.run([sys.executable, str(TARGET), str(path)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIs(json.loads(proc.stdout)['valid'], False)
        self.assertNotIn('Traceback', proc.stderr)

    def test_oversized_json_integer_returns_structured_invalid(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'oversized-number.json'
            path.write_text('{"number":' + ('9' * 5000) + '}')
            proc = subprocess.run([sys.executable, '-X', 'int_max_str_digits=4300', str(TARGET), str(path)],
                                  capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIs(json.loads(proc.stdout)['valid'], False)
        self.assertNotIn('Traceback', proc.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
