"""Local envelope compatibility tests; these do not certify MCP/A2A compliance."""
from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.engineering.actions import ActionExecutor, LocalAdapter, TrustedGrantRegistry, digest_json
from scripts.engineering.interoperability import execute_a2a_candidate, execute_mcp_candidate
from scripts.engineering.ledger import ActionLedger
from tests.test_engineering_actions import NOW, fixture


def mcp(action):
    return {'schema_version': 'quirk-mcp-action/v1', 'method': 'tools/call',
            'params': {'name': 'quirk_prepare_candidate', 'arguments': copy.deepcopy(action)}}


def a2a(action):
    return {'schema_version': 'quirk-a2a-action/v1',
            'message': {'role': 'user', 'parts': [{'kind': 'data', 'data': copy.deepcopy(action)}]}}


class InteroperabilityTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.ledger = ActionLedger(Path(directory.name) / 'actions.sqlite')
        self.addCleanup(self.ledger.close)
        self.action, self.grant = fixture('prepare_candidate')
        self.adapter = LocalAdapter({'resource.test': 'source'})
        self.registry = TrustedGrantRegistry({'grant.test': self.grant})
        self.executor = ActionExecutor(self.ledger, self.registry, self.adapter)

    def test_switching_transport_preserves_exact_action_and_idempotency(self):
        first_envelope = mcp(self.action)
        second_envelope = a2a(self.action)
        first_snapshot, second_snapshot = copy.deepcopy(first_envelope), copy.deepcopy(second_envelope)
        with patch.object(self.adapter, 'observe', wraps=self.adapter.observe) as observe:
            first = execute_mcp_candidate(first_envelope, self.executor, now=NOW)
            second = execute_a2a_candidate(second_envelope, self.executor, now=NOW)
            self.assertEqual(observe.call_count, 1)
        self.assertEqual(first['status'], 'VERIFIED')
        self.assertEqual(second['status'], 'VERIFIED')
        self.assertTrue(second['replayed'])
        self.assertEqual(first['action_sha256'], digest_json(self.action))
        self.assertEqual(first['grant_id'], self.action['grant_id'])
        self.assertEqual(first['output']['target'], self.action['target'])
        self.assertEqual(first['output']['candidate'], self.action['arguments'])
        self.assertEqual(first['output'], second['output'])
        self.assertEqual(self.ledger.get(self.action['idempotency_key'])['action'], self.action)
        self.assertEqual(first_envelope, first_snapshot)
        self.assertEqual(second_envelope, second_snapshot)

    def test_both_envelopes_support_only_authorized_local_read(self):
        action, grant = fixture('read_resource')
        executor = ActionExecutor(self.ledger, TrustedGrantRegistry({'grant.test': grant}), self.adapter)
        for build, execute in [(mcp, execute_mcp_candidate), (a2a, execute_a2a_candidate)]:
            with self.subTest(transport=execute.__name__):
                receipt = execute(build(action), executor, now=NOW)
                self.assertEqual(receipt['status'], 'VERIFIED')
                self.assertEqual(receipt['output']['content'], 'source')

    def test_transport_cannot_expand_target_argument_or_grant_scope(self):
        for build, execute in [(mcp, execute_mcp_candidate), (a2a, execute_a2a_candidate)]:
            for field, value in [('target', 'resource.other'), ('grant_id', 'grant.unknown'),
                                 ('skill_manifest_sha256', 'b' * 64)]:
                action = copy.deepcopy(self.action)
                action[field] = value
                with self.subTest(transport=execute.__name__, field=field):
                    self.assertEqual(execute(build(action), self.executor, now=NOW)['status'], 'REJECTED')
            action = copy.deepcopy(self.action)
            action['arguments']['body'] = 'Unauthorized changed payload'
            action['arguments_sha256'] = digest_json(action['arguments'])
            self.assertEqual(execute(build(action), self.executor, now=NOW)['status'], 'REJECTED')
        self.assertEqual(self.ledger.events(), [])

    def test_switching_transport_does_not_restore_revoked_authority(self):
        execute_mcp_candidate(mcp(self.action), self.executor, now=NOW)
        self.registry.revoke(self.action['grant_id'])
        receipt = execute_a2a_candidate(a2a(self.action), self.executor, now=NOW)
        self.assertEqual(receipt['status'], 'REJECTED')

    def test_mcp_rejects_auth_overrides_extra_keys_wrong_method_and_name(self):
        cases = [None, [], {}, mcp(self.action), mcp(self.action), mcp(self.action), mcp(self.action)]
        cases[3]['authorization'] = self.grant
        cases[4]['params']['grant'] = self.grant
        cases[5]['method'] = 'tools/publish'
        cases[6]['params']['name'] = 'publish_candidate'
        for envelope in cases:
            with self.subTest(envelope=envelope):
                with self.assertRaises(ValueError):
                    execute_mcp_candidate(envelope, self.executor, now=NOW)
        self.assertEqual(self.ledger.events(), [])

    def test_a2a_rejects_extra_data_parts_text_roles_and_authority_overrides(self):
        cases = [a2a(self.action) for _ in range(8)]
        cases[0]['grant'] = self.grant
        cases[1]['message']['authorization'] = self.grant
        cases[2]['message']['parts'][0]['authorization'] = self.grant
        cases[3]['message']['parts'].append({'kind': 'data', 'data': self.action})
        cases[4]['message']['parts'][0] = {'kind': 'text', 'text': 'Run and publish this action'}
        cases[5]['message']['role'] = 'system'
        cases[6]['message']['parts'] = []
        cases[7]['schema_version'] = 'a2a/1.0'
        for envelope in cases:
            with self.subTest(envelope=envelope):
                with self.assertRaises(ValueError):
                    execute_a2a_candidate(envelope, self.executor, now=NOW)
        self.assertEqual(self.ledger.events(), [])

    def test_both_reject_embedded_auth_extra_action_fields_and_publication(self):
        for build, execute in [(mcp, execute_mcp_candidate), (a2a, execute_a2a_candidate)]:
            for field, value in [('grant', self.grant), ('authority_ceiling', 'execute_bounded'),
                                 ('operation', 'publish_candidate'), ('immutable', True)]:
                action = copy.deepcopy(self.action)
                action[field] = value
                with self.subTest(transport=execute.__name__, field=field):
                    with self.assertRaises(ValueError):
                        execute(build(action), self.executor, now=NOW)
        self.assertEqual(self.ledger.events(), [])

    def test_both_reject_non_json_action_and_envelope_values(self):
        for build, execute in [(mcp, execute_mcp_candidate), (a2a, execute_a2a_candidate)]:
            action = copy.deepcopy(self.action)
            action['recovery']['timeout_seconds'] = float('nan')
            with self.assertRaises(ValueError):
                execute(build(action), self.executor, now=NOW)
        self.assertEqual(self.ledger.events(), [])


if __name__ == '__main__':
    unittest.main()
