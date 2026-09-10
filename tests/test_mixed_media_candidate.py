"""Candidate behavior, not proof of production media adapters."""
import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
SPEC = importlib.util.find_spec('mixed_media_candidate')
if SPEC:
    import mixed_media_candidate as m

class MixedMediaTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(SPEC, 'mixed-media compiler must exist')
        self.brief = json.loads((ROOT/'examples/mixed-media/synthetic-review.json').read_text())
    def test_stable_compile(self):
        self.assertEqual(m.compile_plan(self.brief), m.compile_plan(self.brief))
    def test_original_not_mutated(self):
        before=copy.deepcopy(self.brief);m.compile_plan(self.brief);self.assertEqual(before,self.brief)
    def test_topological_order(self):
        self.brief['steps'].reverse()
        p=m.compile_plan(self.brief)
        self.assertEqual(p['steps'][-1]['step_id'],'step.review')
    def test_unknown_input(self):
        self.brief['steps'][0]['inputs']=['asset.absent']
        with self.assertRaises(ValueError):m.compile_plan(self.brief)
    def test_cycle(self):
        self.brief['steps'][0]['depends_on']=['step.review']
        with self.assertRaises(ValueError):m.compile_plan(self.brief)
    def test_duplicate_output(self):
        self.brief['steps'][1]['output_id']='output.caption'
        with self.assertRaises(ValueError):m.compile_plan(self.brief)
    def test_duplicate_asset(self):
        self.brief['assets'].append(copy.deepcopy(self.brief['assets'][0]))
        with self.assertRaises(ValueError):m.compile_plan(self.brief)
    def test_unknown_dependency(self):
        self.brief['steps'][0]['depends_on']=['step.missing']
        with self.assertRaises(ValueError):m.compile_plan(self.brief)
    def test_step_budget(self):
        self.brief['settings']['max_steps']=1
        with self.assertRaises(ValueError):m.compile_plan(self.brief)
    def test_boolean_budget(self):
        self.brief['settings']['max_steps']=True
        with self.assertRaises(ValueError):m.compile_plan(self.brief)
    def test_non_finite(self):
        self.brief['settings']['max_seconds']=float('nan')
        with self.assertRaises(ValueError):m.compile_plan(self.brief)
    def test_unknown_nested_key(self):
        self.brief['assets'][0]['rights']['auto_approve']=True
        with self.assertRaises(ValueError):m.compile_plan(self.brief)
    def test_no_external_effects(self):
        self.brief['settings']['external_effects']=True
        with self.assertRaises(ValueError):m.compile_plan(self.brief)
    def test_no_promote_kind(self):
        self.brief['steps'][0]['kind']='promote_canon'
        with self.assertRaises(ValueError):m.compile_plan(self.brief)
    def test_no_grant_or_dispatch(self):
        p=m.compile_plan(self.brief)
        self.assertFalse(p['dispatch_authorized']);self.assertEqual(p['loop_spec']['authority'],'CANDIDATE_PREPARE')
        self.assertNotIn('grant_id',p)
    def test_rights_unknown_gates_descendants(self):
        self.brief['assets'][0]['rights']['status']='unknown'
        p=m.compile_plan(self.brief); nodes={x['step_id']:x for x in p['steps']}
        self.assertTrue(nodes['step.caption']['blockers']);self.assertTrue(nodes['step.review']['blockers'])
        self.assertEqual(nodes['step.stats']['blockers'],[])
    def test_allowed_rights_need_evidence(self):
        self.brief['assets'][0]['rights']['evidence_refs']=[]
        self.assertTrue(m.compile_plan(self.brief)['steps'][0]['blockers'])
    def test_rights_scope(self):
        self.brief['assets'][0]['rights']['scope']=['inspect']
        p=m.compile_plan(self.brief)
        self.assertTrue(next(x for x in p['steps'] if x['step_id']=='step.review')['blockers'])
    def test_local_invalidation(self):
        p=m.compile_plan(self.brief)
        self.assertEqual(m.impact_of(p,{'asset.caption':'f'*64}),['step.caption','step.review'])
    def test_same_digest_no_invalidation(self):
        p=m.compile_plan(self.brief);a=self.brief['assets'][0]
        self.assertEqual(m.impact_of(p,{a['object_id']:a['content_digest']}),[])
    def test_unknown_change_rejected(self):
        with self.assertRaises(ValueError):m.impact_of(m.compile_plan(self.brief),{'asset.absent':'a'*64})
    def test_branch_identity_preserved(self):
        p=m.compile_plan(self.brief);self.brief['assets'][0]['content_digest']='f'*64;q=m.compile_plan(self.brief)
        get=lambda z:{x['step_id']:x['step_digest'] for x in z['steps']}
        self.assertEqual(get(p)['step.stats'],get(q)['step.stats']);self.assertNotEqual(get(p)['step.review'],get(q)['step.review'])
    def test_exact_local_bytes(self):
        x=m.inspect_sources(self.brief,ROOT/'examples/mixed-media/sources')
        self.assertTrue(all(i['status']=='digest_match' for i in x));self.assertTrue(all(i['rights_verified'] is False for i in x))
    def test_mismatch_not_zero(self):
        self.brief['assets'][0]['content_digest']='f'*64
        self.assertEqual(m.inspect_sources(self.brief,ROOT/'examples/mixed-media/sources')[0]['status'],'digest_mismatch')
    def test_missing_file_unknown(self):
        self.brief['assets'][0]['locator']='missing.txt'
        self.assertEqual(m.inspect_sources(self.brief,ROOT/'examples/mixed-media/sources')[0]['status'],'unavailable')
    def test_path_escape(self):
        self.brief['assets'][0]['locator']='../synthetic-review.json'
        self.assertEqual(m.inspect_sources(self.brief,ROOT/'examples/mixed-media/sources')[0]['status'],'path_rejected')
    def test_remote_locator_never_fetched(self):
        self.brief['assets'][0]['locator']='https://example.invalid/secret'
        self.assertEqual(m.inspect_sources(self.brief,ROOT/'examples/mixed-media/sources')[0]['status'],'path_rejected')
    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/'caption.txt').symlink_to(ROOT/'examples/mixed-media/sources/caption.txt')
            self.assertEqual(m.inspect_sources(self.brief,Path(tmp))[0]['status'],'path_rejected')
    def test_input_byte_limit(self):
        self.brief['settings']['max_input_bytes']=1
        self.assertEqual(m.inspect_sources(self.brief,ROOT/'examples/mixed-media/sources')[0]['status'],'size_limit')
    def test_denied_rights_no_local_read(self):
        self.brief['assets'][0]['rights']['status']='denied'
        row=m.inspect_sources(self.brief,ROOT/'examples/mixed-media/sources')[0]
        self.assertEqual(row['status'],'rights_blocked');self.assertIsNone(row['observed_digest'])
    def test_integer_like_float_rejected(self):
        self.brief['settings']['max_steps']=12.0
        with self.assertRaises(ValueError):m.compile_plan(self.brief)
    def test_prepare_arguments_only(self):
        args=m.prepare_arguments(m.compile_plan(self.brief))
        self.assertEqual(set(args),{'title','body'});self.assertLessEqual(len(args['body']),65536)
    def test_tampered_plan_rejected(self):
        p=m.compile_plan(self.brief);p['dispatch_authorized']=True
        with self.assertRaises(ValueError):m.prepare_arguments(p)
    def test_tampered_impact_rejected(self):
        p=m.compile_plan(self.brief);p['steps'][0]['source_refs']=[]
        with self.assertRaises(ValueError):m.impact_of(p,{'asset.caption':'f'*64})
    def test_loop_output_matches_parent_schema(self):
        schema=ROOT/'schemas/loop-spec.v1.schema.json'
        if not schema.exists():self.skipTest('parent schema supplied by stacked PR')
        from jsonschema import Draft202012Validator
        Draft202012Validator(json.loads(schema.read_text())).validate(m.compile_plan(self.brief)['loop_spec'])
    def test_prepare_output_matches_parent_action_arguments(self):
        schema=ROOT/'schemas/action-contract.v1.schema.json'
        if not schema.exists():self.skipTest('parent schema supplied by stacked PR')
        from jsonschema import Draft202012Validator
        parent=json.loads(schema.read_text())['allOf'][0]['else']['properties']['arguments']
        Draft202012Validator(parent).validate(m.prepare_arguments(m.compile_plan(self.brief)))

if __name__=='__main__':unittest.main()
