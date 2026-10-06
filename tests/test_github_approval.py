import copy
import json
import unittest
from pathlib import Path
from unittest.mock import Mock, MagicMock

from scripts.sync_control_plane.github_approval import verified_record, manifest_contract, strict_json, ingest, refresh
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
        self.pr = dict(head=dict(sha=SHA),base=dict(ref='main',repo=dict(full_name='Quirk-Systems/quirk-os')),draft=False,state='open',merged=False)
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
            authority_ceiling='propose',allowed_actions=['activate_manifest'],requested_by=api.subject['admission']['requested_by'],
            approved_by=api.subject['admission']['approved_by'],decision_ref='decision.manifest.valid',subject_contract=manifest_contract(api.subject))
        registry=Mock(allows=Mock(side_effect=lambda **binding: binding==protected))
        self.assertIn('trusted approval verifier and activation context required',
                      validate_manifest_admission(api.subject,approval_registry=registry))
        registry.allows.assert_called_with(**protected)
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
