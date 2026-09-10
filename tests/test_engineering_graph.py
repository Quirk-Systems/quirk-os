"""Adversarial behavior checks for a scoped, non-authoritative evidence graph."""
import copy
import json
from pathlib import Path
import unittest

from scripts.engineering.graph import EvidenceGraph

NOW = '2026-09-10T12:00:00Z'


def obj(name, **changes):
    return dict(object_id=name, digest='sha256:' + name, kind='artifact', tenant_id='t1', **changes)


def edge(name='a1', subject='candidate', target='proof', predicate='supported_by', **changes):
    record = dict(assertion_id=name, subject_id=subject, subject_digest='sha256:' + subject,
                  predicate=predicate, object_id=target, object_digest='sha256:' + target,
                  source_ref=target, source_digest='sha256:' + target, observer='test-host',
                  observed_at='2026-09-10T10:00:00Z', valid_from='2026-09-10T10:00:00Z',
                  valid_until=None, status='observed')
    record.update(changes)
    return record


class GraphTests(unittest.TestCase):
    def graph(self, edges=None, objects=None, **scope):
        return EvidenceGraph(objects or [obj('candidate'), obj('proof')], edges or [edge()], **scope)

    def test_exact_digest_support(self):
        result = self.graph().support_for('candidate', 'sha256:candidate', now=NOW)
        self.assertEqual([x['assertion_id'] for x in result['supports']], ['a1'])
        self.assertEqual(result['authorization'], 'not_evaluated')
        json.dumps(result)

    def test_changed_subject_digest_invalidates_proof(self):
        result = self.graph().support_for('candidate', 'sha256:new', now=NOW)
        self.assertEqual(result['supports'], [])
        self.assertIn('subject_digest_mismatch', result['excluded'][0]['reasons'])

    def test_changed_source_digest_invalidates_proof(self):
        result = self.graph(edges=[edge(source_digest='sha256:old')]).support_for('candidate', 'sha256:candidate', now=NOW)
        self.assertEqual(result['supports'], [])
        self.assertIn('source_digest_mismatch', result['excluded'][0]['reasons'])

    def test_changed_object_digest_invalidates_proof(self):
        result = self.graph(edges=[edge(object_digest='sha256:old')]).support_for('candidate', 'sha256:candidate', now=NOW)
        self.assertEqual(result['supports'], [])
        self.assertIn('object_digest_mismatch', result['excluded'][0]['reasons'])

    def test_expired_and_future_evidence_excluded(self):
        for changes in ({'valid_until': NOW}, {'observed_at': '2026-09-11T10:00:00Z'}, {'valid_from': '2026-09-11T10:00:00Z'}):
            with self.subTest(changes=changes):
                self.assertEqual(self.graph(edges=[edge(**changes)]).support_for('candidate', 'sha256:candidate', now=NOW)['supports'], [])

    def test_contradictions_are_preserved(self):
        graph = self.graph(edges=[edge(), edge('a2', predicate='contradicted_by')])
        result = graph.support_for('candidate', 'sha256:candidate', now=NOW)
        self.assertEqual(len(result['supports']), 1)
        self.assertEqual(len(result['contradictions']), 1)
        self.assertEqual(len(graph.context_for('candidate', 'sha256:candidate', now=NOW)['items']), 2)

    def test_declared_and_retracted_records_cannot_support(self):
        for status in ('declared', 'retracted'):
            self.assertEqual(self.graph(edges=[edge(status=status)]).support_for('candidate', 'sha256:candidate', now=NOW)['supports'], [])

    def test_supersession_preserves_history_and_cannot_cross_claims(self):
        graph = self.graph(edges=[edge(), edge('a2', supersedes='a1')])
        self.assertEqual([x['assertion_id'] for x in graph.support_for('candidate', 'sha256:candidate', now=NOW)['supports']], ['a2'])
        self.assertEqual(len(graph.context_for('candidate', 'sha256:candidate', now=NOW)['items']), 2)
        with self.assertRaises(ValueError):
            self.graph(edges=[edge(), edge('a2', subject='proof', target='candidate', supersedes='a1')])

    def test_future_supersession_does_not_erase_current_support(self):
        graph = self.graph(edges=[edge(), edge('a2', supersedes='a1', observed_at='2026-09-11T00:00:00Z')])
        self.assertEqual([x['assertion_id'] for x in graph.support_for('candidate', 'sha256:candidate', now=NOW)['supports']], ['a1'])

    def test_future_effective_supersession_preserves_current_support(self):
        graph = self.graph(edges=[edge(), edge('a2', supersedes='a1', valid_from='2026-09-11T00:00:00Z')])
        result = graph.support_for('candidate', 'sha256:candidate', now=NOW)
        self.assertEqual([x['assertion_id'] for x in result['supports']], ['a1'])

    def test_bounded_cycle_traversal(self):
        graph = self.graph(objects=[obj(x) for x in ['a','b','c','d']], edges=[edge(str(i), subject=s, target=t, predicate='depends_on') for i,(s,t) in enumerate([('b','a'),('c','b'),('a','c'),('d','c')])])
        result = graph.impact_of('a', max_depth=2)
        self.assertEqual([(x['object_id'],x['depth']) for x in result['affected']], [('b',1),('c',2)])
        self.assertTrue(result['truncated'])
        full = graph.impact_of('a')
        self.assertEqual(len(full['affected']), 3)
        self.assertFalse(full['truncated'])

    def test_preference_cannot_grant_authority(self):
        with self.assertRaises(ValueError):
            self.graph(edges=[edge(predicate='may_perform')])
        objects = [dict(obj('candidate'), kind='judgment'), obj('proof')]
        graph = self.graph(objects=objects, edges=[edge(predicate='prefers')])
        self.assertEqual(graph.support_for('candidate','sha256:candidate',now=NOW)['supports'], [])
        self.assertEqual(graph.context_for('candidate','sha256:candidate',now=NOW)['authorization'],'not_evaluated')

    def test_relationship_types_are_checked(self):
        with self.assertRaises(ValueError):
            self.graph(edges=[edge(predicate='produced')])
        with self.assertRaises(ValueError):
            self.graph(edges=[edge(predicate='unknown')])

    def test_tenant_and_source_visibility(self):
        objects = [obj('candidate'), obj('proof'), dict(obj('secret'), visible_to=['bob'])]
        graph = self.graph(objects=objects, edges=[edge(source_ref='secret', source_digest='sha256:secret')], tenant_id='t1', principal_id='alice')
        self.assertEqual(graph.context_for('candidate','sha256:candidate',now=NOW)['items'], [])
        self.assertEqual(graph.impact_of('proof')['affected'], [])
        graph = self.graph(tenant_id='other')
        self.assertEqual(graph.support_for('candidate','sha256:candidate',now=NOW)['supports'], [])
        with self.assertRaises(ValueError):
            self.graph(objects=[obj('candidate'),dict(obj('proof'),tenant_id='other')])

    def test_mixed_tenants_require_explicit_scope(self):
        with self.assertRaises(ValueError):
            self.graph(objects=[obj('candidate'),obj('proof'),dict(obj('other'),tenant_id='t2')])

    def test_context_budget_is_strict_and_keeps_provenance(self):
        result = self.graph(edges=[edge('a1'),edge('a2',predicate='contradicted_by')]).context_for('candidate','sha256:candidate',now=NOW,max_items=1)
        self.assertEqual(len(result['items']),1)
        self.assertTrue(result['truncated'])
        self.assertIn('source_digest', result['items'][0]['assertion'])
        self.assertEqual(self.graph().context_for('candidate','sha256:candidate',now=NOW,max_items=0)['items'],[])

    def test_input_and_output_copies_protect_snapshot(self):
        objects, edges = [obj('candidate'),obj('proof')], [edge()]
        graph = EvidenceGraph(objects,edges)
        edges[0]['status']='declared'
        result=graph.support_for('candidate','sha256:candidate',now=NOW)
        result['supports'][0]['status']='declared'
        self.assertEqual(graph.support_for('candidate','sha256:candidate',now=NOW)['supports'][0]['status'],'observed')

    def test_rejects_missing_source_duplicate_ids_and_naive_times(self):
        for edges in ([edge(source_ref='missing')],[edge(),edge()],[edge(observed_at='2026-09-10T10:00:00')]):
            with self.subTest(edges=edges), self.assertRaises(ValueError):
                self.graph(edges=edges)

    def test_runtime_rejects_schema_extras_and_non_json_input(self):
        for bad in ({'extra': {1}}, {'extra': 'authority'}, {'observed_at': 123}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.graph(edges=[edge(**bad)])
        with self.assertRaises(ValueError):
            self.graph(objects=[dict(obj('candidate'), metadata={'unscoped': True}), obj('proof')])
        with self.assertRaises(ValueError):
            self.graph(objects=[dict(obj('candidate'), visible_to=['alice','alice']), obj('proof')])

    def test_schema_accepts_fixture(self):
        from jsonschema import Draft202012Validator, FormatChecker
        root=Path(__file__).resolve().parents[1]
        for name, record in [('engineering-graph-object.v1',obj('candidate')),('engineering-graph-assertion.v1',edge())]:
            schema=json.loads((root/'schemas'/f'{name}.schema.json').read_text())
            Draft202012Validator(schema,format_checker=FormatChecker()).validate(record)


if __name__ == '__main__':
    unittest.main()
