import copy
import json
import unittest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from scripts.sync_control_plane.github_approval import verified_record, manifest_contract, strict_json, ingest, refresh, PolicyInvalidation, GitHubAPI
from scripts.sync_control_plane.approval import PostgresApprovalRegistry
from scripts.sync_control_plane.policy import validate_manifest_admission
from scripts.sync_control_plane.skill_runtime import load_skill_for_execution
from tests.test_skill_runtime import admitted_copy, valid_grant

ROOT = Path(__file__).resolve().parents[1]
NOW = '2026-10-06T04:00:00Z'
SHA = 'a' * 40


class FixtureAPI:
    def __init__(self):
        self.subject = json.loads((ROOT / 'evals/sync-control-plane/valid-active-manifest.json').read_text())
        self.request = dict(grant_id='grant.manifest.valid',subject_kind='manifest',
            subject_id=self.subject['manifest_key'],subject_version='1.0.0',subject_digest=self.subject['content_hash'],
            subject_path='agents/valid.json',authority_ceiling='propose',allowed_actions=['activate_manifest'],
            requested_by='agent.valid',approved_by='human.bryan',decision_ref='decision.manifest.valid',
            issued_at='2026-10-06T03:00:00Z',expires_at='2026-10-06T05:00:00Z',purpose='bounded activation review')
        self.pr = dict(head=dict(sha=SHA),base=dict(ref='main',sha='c'*40,repo=dict(id=1316249812,full_name='Quirk-Systems/quirk-os')),draft=False,state='open',merged=False)
        self.review = dict(id=1,user=dict(id=207279,login='bryansayler',type='User'),state='APPROVED',commit_id=SHA,submitted_at='2026-10-06T03:30:00Z')
        self.reviews = [self.review]
        self.pr_calls = 0
        self.change_head = False

    def get(self, path):
        if '/reviews?' in path:
            return copy.deepcopy(self.reviews)
        self.pr_calls += 1
        value = copy.deepcopy(self.pr)
        if self.change_head and self.pr_calls > 1:
            value['head']['sha'] = 'b' * 40
        return value

    def document(self, path, commit):
        assert commit == SHA
        return copy.deepcopy(self.request if path.startswith('.quirk/') else self.subject)


class ApprovalTests(unittest.TestCase):
    def verify(self, api):
        return verified_record(api, 141, '.quirk/approval-requests/grant.manifest.valid.json', now=NOW)

    def test_review_binds_exact_subject_and_inline_contract(self):
        api=FixtureAPI();record=self.verify(api)
        self.assertEqual(record['subject_contract'],manifest_contract(api.subject))
        self.assertEqual((record['reviewer_id'],record['request_commit'],record['review_id']),(207279,SHA,1))

    def test_old_forged_bot_dismissed_and_future_review_deny(self):
        changes=[{'commit_id':'b'*40},{'state':'DISMISSED'},{'state':'CHANGES_REQUESTED'},
                 {'user':{'id':999,'login':'bryansayler','type':'User'}},
                 {'user':{'id':207279,'login':'bryansayler','type':'Bot'}},
                 {'submitted_at':'2026-10-06T04:01:00Z'}]
        for change in changes:
            with self.subTest(change=change):
                api=FixtureAPI();api.review.update(change)
                with self.assertRaises(ValueError):self.verify(api)

    def test_later_review_supersedes_earlier_approval(self):
        api=FixtureAPI();api.reviews.append({**api.review,'id':2,'state':'CHANGES_REQUESTED','submitted_at':'2026-10-06T03:40:00Z'})
        with self.assertRaises(ValueError):self.verify(api)

    def test_head_change_during_verification_denies(self):
        api=FixtureAPI();api.change_head=True
        with self.assertRaises(ValueError):self.verify(api)

    def test_wrong_subject_scope_expiry_requester_or_extra_field_deny(self):
        changes=[{'subject_digest':'e'*64},{'subject_version':'2.0.0'}, {'allowed_actions':['delete_all']},
                 {'authority_ceiling':'execute_protected'}, {'expires_at':NOW},
                 {'requested_by':'human.bryan'},{'approved_by':'human.fabricated'},{'trusted':True}]
        for change in changes:
            with self.subTest(change=change):
                api=FixtureAPI();api.request.update(change)
                with self.assertRaises(ValueError):self.verify(api)

    def test_closed_unmerged_draft_or_stale_base_deny(self):
        for field,value in [('draft',True),('state','closed')]:
            api=FixtureAPI();api.pr[field]=value
            with self.assertRaises(ValueError):self.verify(api)
        api=FixtureAPI();api.pr['base']['ref']='copilot/old'
        with self.assertRaises(ValueError):self.verify(api)

    def test_duplicate_json_keys_deny(self):
        with self.assertRaises(ValueError):strict_json(b'{"approved_by":"human.bryan","approved_by":"agent.self"}')

    def test_unconfigured_registry_and_database_failure_deny_skill_and_manifest(self):
        manifest,source=admitted_copy();grant=valid_grant(manifest)
        for registry in [None,Mock(allows=Mock(return_value=False)),Mock(allows=Mock(side_effect=RuntimeError('secret')))]:
            result=load_skill_for_execution(manifest,source,grant,now='2026-08-12T05:00:00Z',approval_registry=registry)
            self.assertFalse(result['loaded']);self.assertNotIn('secret',str(result))
            self.assertTrue(validate_manifest_admission(FixtureAPI().subject,approval_registry=registry))

    def test_protected_binding_cannot_be_reused_with_changed_subject_or_scope(self):
        api=FixtureAPI()
        protected=dict(grant_id=api.request['grant_id'],subject_kind='manifest',
            subject_id=api.request['subject_id'],subject_version='1.0.0',subject_digest=api.request['subject_digest'],
            authority_ceiling='propose',allowed_actions=['activate_manifest'],requested_by='agent.valid',
            approved_by='human.bryan',decision_ref='decision.manifest.valid',subject_contract=manifest_contract(api.subject))
        registry=Mock(allows=Mock(side_effect=lambda **binding: binding==protected))
        self.assertEqual(validate_manifest_admission(api.subject,approval_registry=registry),[])
        for field,value in [('tools',[{'ref':'tool.delete','allowed_actions':['delete_all']}]),('version','2.0.0'),('authority_ceiling','execute_protected')]:
            manifest=copy.deepcopy(api.subject);manifest[field]=value
            self.assertTrue(validate_manifest_admission(manifest,approval_registry=registry))
        manifest,source=admitted_copy();grant=valid_grant(manifest)
        from scripts.sync_control_plane.skill_runtime import manifest_digest
        protected=dict(grant_id=grant['grant_id'],subject_kind='skill',subject_id=manifest['id'],
            subject_version=manifest['version'],subject_digest=manifest_digest(manifest),
            authority_ceiling=grant['authority_ceiling'],allowed_actions=grant['allowed_actions'],
            requested_by=grant['requested_by'],approved_by=grant['approved_by'],decision_ref=grant['admission_ref'],subject_contract={})
        self.assertTrue(load_skill_for_execution(manifest,source,grant,now='2026-08-12T05:00:00Z',approval_registry=registry)['loaded'])
        changed=copy.deepcopy(manifest);changed['purpose']+=' changed';changed['integrity']['manifest_sha256']=manifest_digest(changed)
        changed_grant=valid_grant(changed)
        self.assertFalse(load_skill_for_execution(changed,source,changed_grant,now='2026-08-12T05:00:00Z',approval_registry=registry)['loaded'])

    def test_runtime_database_lookup_is_parameterized_and_never_cached(self):
        connection=MagicMock();cursor=connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.side_effect=[(True,),(False,)]
        registry=PostgresApprovalRegistry(connection)
        binding=dict(grant_id="grant.x';drop table x",subject_kind='manifest',subject_id='agent.x',subject_version='1',subject_digest='d'*64,authority_ceiling='propose',allowed_actions=['activate_manifest'],requested_by='agent.x',approved_by='human.bryan',decision_ref='decision.x',subject_contract={})
        self.assertTrue(registry.allows(**binding));self.assertFalse(registry.allows(**binding))
        sql,params=cursor.execute.call_args.args
        self.assertNotIn('drop table',sql);self.assertEqual(params[0],binding['grant_id'])

    def test_runtime_identity_cannot_ingest(self):
        connection=MagicMock();cursor=connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value=('service_role',)
        with self.assertRaises(ValueError):ingest(connection,FixtureAPI(),141,'.quirk/approval-requests/grant.manifest.valid.json',now=NOW)
        self.assertEqual(cursor.execute.call_count,1)

    def test_observed_review_revocation_is_sticky_write(self):
        connection=MagicMock();cursor=connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.side_effect=[('quirk_approval_ingestor',),(141,'.quirk/approval-requests/grant.manifest.valid.json',SHA,1,None)]
        api=FixtureAPI();api.review['state']='DISMISSED'
        self.assertFalse(refresh(connection,api,'grant.manifest.valid',now=NOW))
        self.assertIn('revoked_at',cursor.execute.call_args.args[0])

    def test_outage_cannot_refresh_freshness(self):
        connection=MagicMock();cursor=connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.side_effect=[('quirk_approval_ingestor',),(141,'.quirk/approval-requests/grant.manifest.valid.json',SHA,1,None)]
        api=Mock();api.get.side_effect=OSError('unavailable')
        with self.assertRaises(OSError):refresh(connection,api,'grant.manifest.valid',now=NOW)
        self.assertEqual(cursor.execute.call_count,2)

    def refresh_fixture(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.side_effect = [('quirk_approval_ingestor',),
            (141, '.quirk/approval-requests/grant.manifest.valid.json', SHA, 1, None)]
        return connection, cursor

    def test_mutable_repository_metadata_does_not_revoke_or_deny(self):
        api = FixtureAPI()
        initial, final = copy.deepcopy(api.pr), copy.deepcopy(api.pr)
        initial['base']['repo'].update(stargazers_count=10, updated_at='2026-10-06T03:00:00Z')
        final['base']['repo'].update(stargazers_count=11, updated_at=NOW, description='new description')
        final['base']['label'] = 'unrelated label'
        api.get = Mock(side_effect=[initial, api.reviews, final])
        connection, cursor = self.refresh_fixture()
        self.assertTrue(refresh(connection, api, 'grant.manifest.valid', now=NOW))
        self.assertIn('set verified_at=', cursor.execute.call_args.args[0])

    def test_security_relevant_base_drift_revokes(self):
        for field, value in [('id', 999), ('full_name', 'other/repository'),
                             ('ref', 'other-branch'), ('sha', 'd' * 40)]:
            with self.subTest(field=field):
                api = FixtureAPI()
                final = copy.deepcopy(api.pr)
                target = final['base']['repo'] if field in {'id', 'full_name'} else final['base']
                target[field] = value
                api.get = Mock(side_effect=[api.pr, api.reviews, final])
                connection, cursor = self.refresh_fixture()
                self.assertFalse(refresh(connection, api, 'grant.manifest.valid', now=NOW))
                self.assertIn('set revoked_at=', cursor.execute.call_args.args[0])

    def test_malformed_responses_never_write_and_can_recover(self):
        malformed_prs = [None, [], {}, {'head': None}]
        for path in [('head', 'sha'), ('base', 'sha'), ('base', 'repo'),
                     ('base', 'repo', 'id'), ('base', 'repo', 'full_name'),
                     ('draft',), ('state',), ('merged',)]:
            value = copy.deepcopy(FixtureAPI().pr)
            target = value
            for key in path[:-1]:
                target = target[key]
            del target[path[-1]]
            malformed_prs.append(value)
        for field, value in [('draft', None), ('merged', None), ('state', 'unknown')]:
            pr = copy.deepcopy(FixtureAPI().pr); pr[field] = value
            malformed_prs.append(pr)
        responses = []
        for pr in malformed_prs:
            responses.extend([[pr], [FixtureAPI().pr, FixtureAPI().reviews, pr]])
        responses.extend([[FixtureAPI().pr, value] for value in [None, {}, [None], [{}]]])
        for field in ['id', 'state', 'commit_id', 'submitted_at', 'user']:
            review = copy.deepcopy(FixtureAPI().review); del review[field]
            responses.append([FixtureAPI().pr, [review]])
        for field, value in [('state', 'unknown'), ('submitted_at', None),
                             ('submitted_at', 'bad timestamp'), ('commit_id', None), ('user', None)]:
            review = copy.deepcopy(FixtureAPI().review); review[field] = value
            responses.append([FixtureAPI().pr, [review]])
        for sequence in responses:
            with self.subTest(sequence=sequence):
                api = FixtureAPI(); api.get = Mock(side_effect=sequence)
                connection, cursor = self.refresh_fixture()
                with self.assertRaises((ValueError, KeyError, TypeError, AttributeError)) as error:
                    refresh(connection, api, 'grant.manifest.valid', now=NOW)
                self.assertNotIsInstance(error.exception, PolicyInvalidation)
                self.assertEqual(cursor.execute.call_count, 2)
                # Same unrevoked row is eligible for a later complete verification.
                cursor.fetchone.side_effect = [('quirk_approval_ingestor',),
                    (141, '.quirk/approval-requests/grant.manifest.valid.json', SHA, 1, None)]
                self.assertTrue(refresh(connection, FixtureAPI(), 'grant.manifest.valid', now=NOW))
                self.assertIn('set verified_at=', cursor.execute.call_args.args[0])

    def test_truncated_200_json_is_protocol_failure_without_revocation(self):
        import io
        response = MagicMock()
        response.__enter__.return_value = response
        response.geturl.return_value = 'https://api.github.com/repos/Quirk-Systems/quirk-os/pulls/141'
        response.read = io.BytesIO(b'{"head":').read
        with patch('scripts.sync_control_plane.github_approval.build_opener') as opener:
            opener.return_value.open.return_value = response
            connection, cursor = self.refresh_fixture()
            with self.assertRaises(json.JSONDecodeError):
                refresh(connection, GitHubAPI('fixture-token'), 'grant.manifest.valid', now=NOW)
            self.assertEqual(cursor.execute.call_count, 2)

    def test_protocol_failure_at_document_or_later_page_never_revokes(self):
        for stage in ['request', 'subject', 'missing_subject', 'later_page']:
            with self.subTest(stage=stage):
                api = FixtureAPI()
                if stage == 'request':
                    api.document = Mock(side_effect=ValueError('malformed inline document'))
                elif stage == 'subject':
                    api.document = Mock(side_effect=[api.request, json.JSONDecodeError('truncated', '{', 1)])
                elif stage == 'missing_subject':
                    api.document = Mock(side_effect=[api.request, {}])
                else:
                    api.get = Mock(side_effect=[api.pr, [api.review] * 100, {}])
                connection, cursor = self.refresh_fixture()
                with self.assertRaises((ValueError, KeyError)) as error:
                    refresh(connection, api, 'grant.manifest.valid', now=NOW)
                self.assertNotIsInstance(error.exception, PolicyInvalidation)
                self.assertEqual(cursor.execute.call_count, 2)

    def test_verified_policy_failures_and_original_binding_changes_revoke(self):
        for change in ['head', 'draft', 'closed', 'empty_reviews', 'review_identity', 'expiry']:
            with self.subTest(change=change):
                api = FixtureAPI()
                if change == 'head': api.change_head = True
                elif change == 'draft': api.pr['draft'] = True
                elif change == 'closed': api.pr['state'] = 'closed'
                elif change == 'empty_reviews': api.reviews = []
                elif change == 'review_identity': api.review['id'] = 2
                elif change == 'expiry': api.request['expires_at'] = NOW
                connection, cursor = self.refresh_fixture()
                self.assertFalse(refresh(connection, api, 'grant.manifest.valid', now=NOW))
                self.assertIn('set revoked_at=', cursor.execute.call_args.args[0])

    def test_existing_revocation_is_sticky_without_api_call(self):
        connection, cursor = self.refresh_fixture()
        cursor.fetchone.side_effect = [('quirk_approval_ingestor',),
            (141, '.quirk/approval-requests/grant.manifest.valid.json', SHA, 1, NOW)]
        api = Mock()
        self.assertFalse(refresh(connection, api, 'grant.manifest.valid', now=NOW))
        api.get.assert_not_called()
        self.assertEqual(cursor.execute.call_count, 2)

    def test_malformed_request_values_never_revoke_and_can_recover(self):
        fixture = FixtureAPI().request
        cases = [(key, value) for key in fixture for value in (None, 42, True, {}, [])
                 if not (key == 'allowed_actions' and value == [])]
        cases += [('allowed_actions', value) for value in ([], [None], [42], [{}],
                  ['activate_manifest', 'activate_manifest'], ['bad action'])]
        cases += [('issued_at', 'bad timestamp'), ('expires_at', '2026-10-06T05:00:00'),
                  ('subject_digest', 'bad digest'), ('subject_path', '../bad.json'),
                  ('approved_by', 'bad principal'), ('requested_by', 'bad principal'),
                  ('grant_id', 'bad identity')]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                api = FixtureAPI(); api.request[key] = value
                connection, cursor = self.refresh_fixture()
                with self.assertRaises(ValueError) as error:
                    refresh(connection, api, 'grant.manifest.valid', now=NOW)
                self.assertNotIsInstance(error.exception, PolicyInvalidation)
                self.assertEqual(cursor.execute.call_count, 2)
                cursor.fetchone.side_effect = [('quirk_approval_ingestor',),
                    (141, '.quirk/approval-requests/grant.manifest.valid.json', SHA, 1, None)]
                self.assertTrue(refresh(connection, FixtureAPI(), 'grant.manifest.valid', now=NOW))
                self.assertIn('set verified_at=', cursor.execute.call_args.args[0])

    def test_complete_request_shape_precedes_policy_interpretation(self):
        for key in FixtureAPI().request:
            with self.subTest(key=key):
                api = FixtureAPI()
                api.request['approved_by'] = 'human.other'
                api.request[key] = None
                with self.assertRaises(ValueError) as error:
                    self.verify(api)
                self.assertNotIsInstance(error.exception, PolicyInvalidation)

    def test_well_formed_request_policy_failures_remain_sticky(self):
        for key, value in [('approved_by', 'human.other'), ('purpose', 'too short'),
                           ('allowed_actions', ['delete_all']), ('subject_kind', 'other'),
                           ('subject_digest', 'e' * 64)]:
            with self.subTest(key=key):
                api = FixtureAPI(); api.request[key] = value
                connection, cursor = self.refresh_fixture()
                self.assertFalse(refresh(connection, api, 'grant.manifest.valid', now=NOW))
                self.assertIn('set revoked_at=', cursor.execute.call_args.args[0])
