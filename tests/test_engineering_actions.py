from __future__ import annotations
import copy
import json
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
from scripts.engineering.actions import (ActionExecutor, LocalAdapter, TrustedGrantRegistry,
    digest_json, digest_text, validate_action)
from scripts.engineering.ledger import ActionLedger

NOW = '2026-09-10T12:00:00Z'
ROOT = Path(__file__).resolve().parents[1]


def fixture(operation='read_resource'):
    arguments = {} if operation == 'read_resource' else {'title': 'Next proof', 'body': 'Run fixtures'}
    limits = {'max_resources': 1, 'max_bytes': 65536, 'max_spend': 0}
    action = {'schema_version': 'action-contract/v1', 'action_id': 'action.test',
        'idempotency_key': 'logical-operation-1', 'grant_id': 'grant.test',
        'skill_id': 'quirk-test', 'skill_version': '1.0.0', 'skill_manifest_sha256': 'a'*64,
        'operation': operation, 'target': 'resource.test', 'target_sha256': digest_text('source'),
        'arguments': arguments, 'arguments_sha256': digest_json(arguments),
        'objective': 'Prove the bounded candidate',
        'postcondition': 'content_digest_matches' if operation == 'read_resource' else 'candidate_prepared',
        'effect_limit': limits, 'recovery': {'retry': 'reconcile_only', 'timeout_seconds': 30}}
    grant = {'schema_version': 'action-grant/v1', 'runtime_grant': {
        'grant_id': 'grant.test', 'skill_id': 'quirk-test', 'skill_version': '1.0.0',
        'skill_manifest_sha256': 'a'*64, 'decision': 'approved', 'admission_ref': 'decision.fixture',
        'requested_by': 'fixture.operator', 'approved_by': 'fixture.host',
        'issued_at': '2026-09-10T00:00:00Z', 'expires_at': '2026-09-11T00:00:00Z',
        'authority_ceiling': 'propose', 'allowed_actions': [operation],
        'purpose': 'Local candidate proof only'}, 'target': action['target'],
        'target_sha256': action['target_sha256'], 'arguments_sha256': action['arguments_sha256'],
        'policy_ref': 'policy.local-candidate.v1', 'effect_limit': copy.deepcopy(limits)}
    return action, grant


class ActionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'actions.sqlite'
        self.action, self.grant = fixture()
        self.ledger = ActionLedger(self.path)
        self.addCleanup(self.ledger.close)
        self.adapter = LocalAdapter({'resource.test': 'source'})
        self.registry = TrustedGrantRegistry({'grant.test': self.grant})
        self.executor = ActionExecutor(self.ledger, self.registry, self.adapter)

    def test_exact_action_passes(self):
        self.assertEqual(validate_action(self.action, self.grant, now=NOW,
            current_target_digest=digest_text('source')), [])

    def test_resource_arguments_digest_expiry_revocation_and_ceiling(self):
        changes = [('target', 'resource.other'), ('arguments', {'path':'/etc/passwd'}),
            ('target_sha256', 'b'*64), ('operation', 'delete_resource'),
            ('skill_manifest_sha256', 'b'*64), ('postcondition', 'anything')]
        for key, value in changes:
            action = copy.deepcopy(self.action); action[key] = value
            with self.subTest(field=key):
                self.assertTrue(validate_action(action, self.grant, now=NOW,
                    current_target_digest=digest_text('source')))
        self.assertTrue(validate_action(self.action, self.grant, now='2026-09-12T00:00:00Z',
            current_target_digest=digest_text('source')))
        self.assertTrue(validate_action(self.action, self.grant, now=NOW,
            current_target_digest=digest_text('source'), revoked_grant_ids=['grant.test']))
        self.assertTrue(validate_action(self.action, self.grant, now=NOW,
            current_target_digest='b'*64))

    def test_read_is_observed_and_persisted_and_replayed(self):
        result = self.executor.execute(self.action, now=NOW)
        self.assertEqual(result['status'], 'VERIFIED', result)
        self.assertEqual(result['output']['content'], 'source')
        self.assertTrue(result['no_authority_escalation'])
        self.assertIsNone(result['immutable'])
        self.assertTrue(result['evidence'])
        self.ledger.close()
        with ActionLedger(self.path) as restarted:
            replay = ActionExecutor(restarted, self.registry, self.adapter).execute(self.action, now=NOW)
            self.assertEqual(replay['status'], 'VERIFIED')
            self.assertTrue(replay['replayed'])
            self.assertEqual(len(restarted.events()), 2)

    def test_changed_action_cannot_reuse_idempotency_key(self):
        self.executor.execute(self.action, now=NOW)
        self.action['objective'] = 'A different logical operation'
        result = self.executor.execute(self.action, now=NOW)
        self.assertEqual(result['status'], 'REJECTED')
        self.assertIn('idempotency key is bound to a different action', result['errors'])

    def test_replay_still_checks_revocation_and_source(self):
        self.executor.execute(self.action, now=NOW)
        self.assertEqual(self.executor.execute(self.action, now=NOW,
            revoked_grant_ids=['grant.test'])['status'], 'REJECTED')
        self.adapter.resources['resource.test'] = 'changed'
        self.assertEqual(self.executor.execute(self.action, now=NOW)['status'], 'REJECTED')

    def test_uncertain_intent_is_not_blindly_repeated(self):
        self.ledger.record_intent(self.action)
        self.ledger.close()
        with ActionLedger(self.path) as restarted:
            result = ActionExecutor(restarted, self.registry, self.adapter).execute(self.action, now=NOW)
            self.assertEqual(result['status'], 'UNCERTAIN')
            self.assertIsNone(result['output'])
            self.assertEqual(len(restarted.events()), 2)

    def test_prepare_creates_only_bounded_candidate(self):
        action, grant = fixture('prepare_candidate')
        executor = ActionExecutor(self.ledger, TrustedGrantRegistry({'grant.test': grant}), self.adapter)
        result = executor.execute(action, now=NOW)
        self.assertEqual(result['status'], 'VERIFIED', result)
        self.assertEqual(result['output']['candidate'], action['arguments'])
        self.assertEqual(self.adapter.resources, {'resource.test':'source'})

    def test_untrusted_embedded_grant_and_receipt_flags_do_not_authorize(self):
        action = copy.deepcopy(self.action)
        action['grant'] = self.grant
        action['no_authority_escalation'] = True
        executor = ActionExecutor(self.ledger, TrustedGrantRegistry({}), self.adapter)
        self.assertEqual(executor.execute(action, now=NOW)['status'], 'REJECTED')

    def test_registry_copies_host_grants(self):
        self.grant['target'] = 'resource.other'
        self.assertEqual(self.executor.execute(self.action, now=NOW)['status'], 'VERIFIED')

    def test_ledger_history_rejects_normal_update_and_delete(self):
        self.executor.execute(self.action, now=NOW)
        with sqlite3.connect(self.path) as connection:
            for statement in ['DELETE FROM action_events', "UPDATE action_events SET event_type='fake'"]:
                with self.assertRaises(sqlite3.DatabaseError):
                    connection.execute(statement)

    def test_malformed_inputs_fail_closed(self):
        for action in [None, [], {}, {**self.action, 'arguments': float('nan')},
                       {**self.action, 'effect_limit': None}]:
            with self.subTest(action=action):
                self.assertEqual(self.executor.execute(action, now=NOW)['status'], 'REJECTED')

    def test_contracts_and_receipt_validate(self):
        result = self.executor.execute(self.action, now=NOW)
        for filename, record in [('action-contract.v1.schema.json', self.action),
                ('action-grant.v1.schema.json', self.grant), ('action-receipt.v2.schema.json', result)]:
            schema = json.loads((ROOT/'schemas'/filename).read_text())
            errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(record))
            self.assertEqual(errors, [], errors)

    def test_recomputed_argument_digest_still_cannot_expand_grant(self):
        action, grant = fixture('prepare_candidate')
        action['arguments']['body'] = 'Different task'
        action['arguments_sha256'] = digest_json(action['arguments'])
        self.assertIn('grant arguments_sha256 mismatch', validate_action(action, grant,
            now=NOW, current_target_digest=action['target_sha256']))

    def test_oversized_resource_is_not_reported_as_verified(self):
        self.action['effect_limit']['max_bytes'] = 2
        result = self.executor.execute(self.action, now=NOW)
        self.assertNotEqual(result['status'], 'VERIFIED')
        self.assertIsNone(result['no_authority_escalation'])

    def test_grant_and_target_revalidated_after_intent_persistence(self):
        original = self.ledger.record_intent
        def reserve_then_revoke(action):
            result = original(action)
            self.registry.revoke(action['grant_id'])
            return result
        with patch.object(self.ledger, 'record_intent', side_effect=reserve_then_revoke):
            with patch.object(self.adapter, 'observe') as observe:
                self.assertEqual(self.executor.execute(self.action, now=NOW)['status'], 'REJECTED')
                observe.assert_not_called()

    def test_expiration_during_intent_persistence_prevents_dispatch(self):
        self.grant['runtime_grant']['expires_at'] = '2026-09-10T12:00:01Z'
        executor = ActionExecutor(self.ledger, TrustedGrantRegistry({'grant.test': self.grant}), self.adapter)
        with patch('scripts.engineering.actions.time.monotonic', side_effect=[0, 2, 2, 2]):
            with patch.object(self.adapter, 'observe') as observe:
                self.assertEqual(executor.execute(self.action, now=NOW)['status'], 'REJECTED')
                observe.assert_not_called()

    def test_crash_after_possible_effect_preserves_intent_for_reconciliation(self):
        class ProcessCrash(BaseException):
            pass
        with patch.object(self.adapter, 'observe', side_effect=ProcessCrash):
            with self.assertRaises(ProcessCrash):
                self.executor.execute(self.action, now=NOW)
        self.assertIsNone(self.ledger.get(self.action['idempotency_key'])['outcome'])
        with patch.object(self.adapter, 'observe') as observe:
            result = self.executor.execute(self.action, now=NOW)
            self.assertEqual(result['status'], 'UNCERTAIN')
            observe.assert_not_called()

    def test_verifier_rejects_wrong_observed_output(self):
        with patch.object(self.adapter, 'observe', return_value=({'content':'wrong'}, [])):
            result = self.executor.execute(self.action, now=NOW)
        self.assertEqual(result['status'], 'UNCERTAIN')

    def test_receipt_preserves_action_and_grant_identity(self):
        result = self.executor.execute(self.action, now=NOW)
        self.assertEqual(result['grant_id'], self.action['grant_id'])
        self.assertEqual(result['skill_manifest_sha256'], self.action['skill_manifest_sha256'])
        self.assertEqual(result['action_sha256'], digest_json(self.action))

    def test_forged_observed_flags_fail_receipt_schema(self):
        result = self.executor.execute(self.action, now=NOW)
        result['evidence'] = []
        result['immutable'] = True
        schema = json.loads((ROOT/'schemas'/'action-receipt.v2.schema.json').read_text())
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(result)))

    def test_final_dispatch_check_uses_fresh_clock(self):
        self.grant['runtime_grant']['expires_at'] = '2026-09-10T12:00:01Z'
        executor = ActionExecutor(self.ledger, TrustedGrantRegistry({'grant.test': self.grant}), self.adapter)
        clock = [0]
        calls = []
        original = executor._check
        def check_then_advance(action, now, revoked):
            errors = original(action, now, revoked)
            calls.append(now)
            if len(calls) == 2:
                clock[0] = 2
            return errors
        with patch('scripts.engineering.actions.time.monotonic', side_effect=lambda: clock[0]):
            with patch.object(executor, '_check', side_effect=check_then_advance):
                with patch.object(self.adapter, 'observe') as observe:
                    result = executor.execute(self.action, now=NOW)
                    self.assertEqual(result['status'], 'REJECTED', result)
                    observe.assert_not_called()

    def test_historical_receipt_binds_checked_grant_after_later_revocation(self):
        original = self.adapter.observe
        def observe_then_revoke(action):
            result = original(action)
            self.registry.revoke(action['grant_id'])
            return result
        with patch.object(self.adapter, 'observe', side_effect=observe_then_revoke):
            result = self.executor.execute(self.action, now=NOW)
        self.assertEqual(result['status'], 'VERIFIED', result)
        self.assertEqual(result['evidence'][0]['grant_sha256'], digest_json(self.grant))
        self.assertEqual(self.executor.execute(self.action, now=NOW)['status'], 'REJECTED')

if __name__ == '__main__':
    unittest.main()
