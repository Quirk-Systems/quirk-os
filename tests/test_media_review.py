"""Synthetic behavior tests; no real user content or measured benefit."""
import copy
import hashlib
import json
from pathlib import Path
import stat
import tempfile
import unittest

from jsonschema import Draft202012Validator, FormatChecker
from scripts.engineering.graph import EvidenceGraph
from scripts.prepare_media_review import prepare_report, export_review, verify_review

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = {'ceiling': 'candidate', 'publish_allowed': False, 'graph_application_allowed': False, 'training_allowed': False, 'canon_promotion_allowed': False}
HOST = {'tenant_id': 'fixture-tenant', 'principal_id': 'fixture-reviewer', 'captured_at': '2026-09-10T12:00:00+00:00'}

def fixture():
    assets = []
    for i, ref in enumerate(['source', 'selected', 'alternative']):
        assets.append({'asset_ref': ref, 'title': 'Synthetic '+ref, 'archive_path': 'assets/'+ref+'.txt',
            'provenance_role': 'source' if i == 0 else 'derivative', 'family': 'document', 'extension_family': 'document',
            'origin': 'unknown' if i == 0 else 'generated', 'use_role': 'reference' if i == 0 else 'working',
            'sensitivity': 'private', 'state': 'candidate', 'state_reason': 'Synthetic test record only',
            'review_on': '2026-09-17', 'replacement_ref': None, 'selected': i == 1,
            'depends_on': [] if i == 0 else ['source'], 'alt_text_presence': 'absent', 'companions': {}})
    return {'schema_version': 'media-care-check.v1', 'tool_version': '0.2.0', 'as_of': '2026-09-10',
        'kit_id': 'qmk_synthetic', 'kit_content_sha256': '1'*64, 'care_sha256': '2'*64, 'classification_sha256': '3'*64,
        'integrity': 'verified', 'status': 'needs_attention', 'authority': copy.deepcopy(AUTHORITY),
        'human_benefit': 'unobserved', 'scope': 'Synthetic unsigned report; not permission.',
        'maintenance_owner': 'unassigned', 'owner_acceptance': 'unverified', 'proposed_by': 'fixture.agent',
        'selection': {'asset_ref': 'selected', 'needs_attention': True, 'review_refs': ['selected','source'], 'actor_type': 'agent', 'signature_status': 'unsigned'},
        'assets': assets, 'findings': [
            {'code':'owner_needed','asset_ref':None,'message':'Record owner acceptance.'},
            {'code':'origin_unknown','asset_ref':'source','message':'Inspect source origin.'},
            {'code':'rights_review_open','asset_ref':'selected','message':'Review rights.'},
            {'code':'accessibility_review_open','asset_ref':'selected','message':'Review accessibility.'},
            {'code':'rights_review_open','asset_ref':'alternative','message':'Review rights.'},
            {'code':'accessibility_review_open','asset_ref':'alternative','message':'Review accessibility.'}],
        'art_direction': {'intent':'Synthetic review.', 'preserve':['The source'], 'avoid':['False approval'], 'craft_questions':['Useful?'], 'human_judgment':'unobserved'}}

def raw(value=None):
    return (json.dumps(fixture() if value is None else value, ensure_ascii=False, indent=2)+'\n').encode()

def context(data):
    return dict(HOST, expected_sha256=hashlib.sha256(data).hexdigest())

class MediaReviewTests(unittest.TestCase):
    def prepare(self, value=None):
        data = raw(value)
        return prepare_report(data, **context(data))

    def test_existing_projection_and_native_graph(self):
        out = self.prepare()
        self.assertIsInstance(out, dict)
        schema = json.loads((ROOT/'schemas/projection-envelope.schema.json').read_text())
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(out)
        p = out['projection']
        graph = EvidenceGraph(p['graph']['objects'],p['graph']['assertions'],tenant_id=HOST['tenant_id'],principal_id=HOST['principal_id'])
        result = graph.impact_of(p['source_ref'])
        self.assertGreaterEqual(len(result['affected']), 9)
        self.assertEqual(result['authorization'],'not_evaluated')

    def test_all_findings_survive_and_no_permission_is_created(self):
        p = self.prepare()['projection']
        self.assertEqual(p['findings'],fixture()['findings'])
        self.assertEqual(len(p['tasks']),6)
        self.assertEqual(p['disposition']['authorized_actions'],[])
        self.assertEqual(p['authority'],AUTHORITY)
        self.assertIsNone(p['measured_human_benefit'])
        self.assertTrue(all(t['state']=='proposed' for t in p['tasks']))

    def test_agent_selection_stays_unsigned_not_a_human_preference(self):
        p = self.prepare()['projection']
        self.assertEqual(p['selection'],fixture()['selection'])
        self.assertFalse(any(e['predicate']=='prefers' for e in p['graph']['assertions']))
        self.assertTrue(all(e['status']=='declared' for e in p['graph']['assertions']))

    def test_principal_restriction_survives_all_graph_objects(self):
        p = self.prepare()['projection']
        self.assertTrue(all(o['visible_to']==[HOST['principal_id']] for o in p['graph']['objects']))
        graph = EvidenceGraph(p['graph']['objects'],p['graph']['assertions'],tenant_id=HOST['tenant_id'],principal_id='other-person')
        self.assertEqual(graph.impact_of(p['source_ref'])['affected'],[])

    def test_declared_evidence_does_not_become_observed_support(self):
        p = self.prepare()['projection']; task=p['tasks'][0]
        graph=EvidenceGraph(p['graph']['objects'],p['graph']['assertions'],tenant_id=HOST['tenant_id'],principal_id=HOST['principal_id'])
        obj=next(o for o in p['graph']['objects'] if o['object_id']==task['task_id'])
        support=graph.support_for(obj['object_id'],obj['digest'],now=HOST['captured_at'])
        self.assertEqual(support['supports'],[])
        self.assertTrue(any('status_declared' in e['reasons'] for e in support['excluded']))

    def test_deterministic_repeated_preparation(self):
        self.assertEqual(self.prepare(),self.prepare())

    def test_report_byte_change_creates_new_binding(self):
        a=raw(); b=a+b' '
        pa=prepare_report(a,**context(a)); pb=prepare_report(b,**context(b))
        self.assertNotEqual(pa['object_key'],pb['object_key'])
        self.assertEqual(pa['projection']['findings'],pb['projection']['findings'])

    def test_bad_caller_digest_rejected(self):
        with self.assertRaises(ValueError): prepare_report(raw(),**dict(HOST,expected_sha256='0'*64))

    def test_duplicate_json_key_rejected(self):
        data=raw().replace(b'"schema_version":',b'"schema_version":"media-care-check.v1", "schema_version":',1)
        with self.assertRaises(ValueError): prepare_report(data,**context(data))

    def test_nonfinite_json_rejected(self):
        for x in [b'NaN',b'Infinity',b'1e999']:
            data=raw().replace(b'"unobserved"',x,1)
            with self.subTest(x=x),self.assertRaises(ValueError): prepare_report(data,**context(data))

    def test_oversized_input_rejected(self):
        data=b' '* (1024*1024+1)
        with self.assertRaises(ValueError): prepare_report(data,**context(data))

    def test_future_source_date_rejected(self):
        f=fixture();f['as_of']='2026-09-11'
        with self.assertRaises(ValueError): self.prepare(f)

    def test_old_source_remains_visible_as_stale(self):
        f=fixture();f['as_of']='2026-08-01'; p=self.prepare(f)['projection']
        self.assertTrue(p['snapshot_stale'])
        self.assertEqual(len(p['findings']),6)
        self.assertIn('SOURCE_REVALIDATION_REQUIRED',p['holds'])

    def test_timezone_required(self):
        with self.assertRaises(ValueError):prepare_report(raw(),**dict(context(raw()),captured_at='2026-09-10T12:00:00'))

    def test_authority_expansion_rejected(self):
        for key in AUTHORITY:
            f=fixture();f['authority'][key]='live' if key=='ceiling' else True
            with self.subTest(key=key),self.assertRaises(ValueError):self.prepare(f)

    def test_false_is_not_numeric_zero(self):
        f=fixture();f['authority']['publish_allowed']=0
        with self.assertRaises(ValueError):self.prepare(f)

    def test_unknown_protocol_fields_rejected(self):
        f=fixture();f['activate']=True
        with self.assertRaises(ValueError):self.prepare(f)

    def test_unsupported_version_rejected(self):
        f=fixture();f['schema_version']='media-care-check.v2'
        with self.assertRaises(ValueError):self.prepare(f)

    def test_missing_and_duplicate_assets_rejected(self):
        for mutation in ['missing','duplicate']:
            f=fixture()
            if mutation=='missing': f['assets'].pop(0)
            else:f['assets'].append(copy.deepcopy(f['assets'][0]))
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):self.prepare(f)

    def test_dependency_cycle_rejected(self):
        f=fixture();f['assets'][0]['depends_on']=['selected']
        with self.assertRaises(ValueError):self.prepare(f)

    def test_missing_selection_dependency_rejected(self):
        f=fixture();f['selection']['review_refs']=['selected']
        with self.assertRaises(ValueError):self.prepare(f)

    def test_selection_flag_mismatch_rejected(self):
        f=fixture();f['assets'][2]['selected']=True
        with self.assertRaises(ValueError):self.prepare(f)

    def test_unknown_finding_preserved_not_executed(self):
        f=fixture();f['findings'][0]['code']='new_warning';p=self.prepare(f)['projection']
        task=next(t for t in p['tasks'] if t['finding']['code']=='new_warning')
        self.assertEqual(task['review_method'],'manual_review')
        self.assertEqual(p['disposition']['authorized_actions'],[])

    def test_finding_target_and_duplicates_rejected(self):
        for mutation in ['bad_ref','duplicate']:
            f=fixture()
            if mutation=='bad_ref':f['findings'][0]['asset_ref']='absent'
            else:f['findings'].append(copy.deepcopy(f['findings'][0]))
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):self.prepare(f)

    def test_malformed_structures_fail_as_value_errors(self):
        for value in [None,[],42,'hello']:
            data=json.dumps(value).encode()
            with self.subTest(value=value),self.assertRaises(ValueError):prepare_report(data,**context(data))

    def test_export_and_reopen_are_byte_exact(self):
        data=raw()
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'review'
            export_review(data,dest,**context(data))
            self.assertTrue(dest.is_dir())
            self.assertEqual((dest/'source.json').read_bytes(),data)
            result=verify_review(dest,**context(data))
            self.assertTrue(result['replay_verified'])
            self.assertEqual(result['authority_effect'],'none')
            self.assertEqual(stat.S_IMODE(dest.stat().st_mode),0o700)
            self.assertEqual(stat.S_IMODE((dest/'source.json').stat().st_mode),0o600)

    def test_existing_destination_not_overwritten(self):
        data=raw()
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'review'; dest.mkdir();keep=dest/'keep';keep.write_text('unchanged')
            with self.assertRaises((ValueError,FileExistsError)):export_review(data,dest,**context(data))
            self.assertEqual(keep.read_text(),'unchanged')

    def test_tampered_view_and_projection_and_source_rejected(self):
        for name in ['REVIEW.txt','review.json','source.json']:
            data=raw()
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                dest=Path(tmp)/'review';export_review(data,dest,**context(data))
                with (dest/name).open('ab') as f:f.write(b' ')
                with self.assertRaises(ValueError):verify_review(dest,**context(data))

    def test_changed_principal_cannot_reopen_as_same_context(self):
        data=raw()
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'review';export_review(data,dest,**context(data))
            with self.assertRaises(ValueError):verify_review(dest,**dict(context(data),principal_id='other-person'))

    def test_symlinked_export_and_source_rejected(self):
        data=raw()
        with tempfile.TemporaryDirectory() as tmp:
            real=Path(tmp)/'real';real.mkdir();link=Path(tmp)/'link';link.symlink_to(real,target_is_directory=True)
            with self.assertRaises(ValueError):export_review(data,link/'review',**context(data))
            dest=Path(tmp)/'review';export_review(data,dest,**context(data))
            source=dest/'source.json';source.unlink();source.symlink_to(real/'missing')
            with self.assertRaises(ValueError):verify_review(dest,**context(data))

if __name__=='__main__':unittest.main()
