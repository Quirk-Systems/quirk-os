from __future__ import annotations
from datetime import datetime
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from deck_grammar.compiler import build_access_pool, compile_live_proof, content_hash, evaluate_adversarial_case
from deck_grammar.access import _slug
SCHEMA_FILES = ['active-hand.schema.json', 'aesthetic-contract.schema.json', 'affordance.schema.json', 'area.schema.json', 'art.schema.json', 'artifact.schema.json', 'asset.schema.json', 'card-definition.schema.json', 'card-instance.schema.json', 'collection.schema.json', 'eligible-deck.schema.json', 'entitlement-grant.schema.json', 'goal.schema.json', 'hand-preset.schema.json', 'intention.schema.json']

def load_json(relative: str):
    return json.loads((ROOT / relative).read_text(encoding='utf-8'))

def load_yaml(relative: str):
    return yaml.safe_load((ROOT / relative).read_text(encoding='utf-8'))

class DeckGrammarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schemas = {name: load_json(f'schemas/{name}') for name in SCHEMA_FILES}
        cls.registry = Registry()
        for schema in cls.schemas.values():
            Draft202012Validator.check_schema(schema)
            cls.registry = cls.registry.with_resource(schema['$id'], Resource.from_contents(schema))
        cls.as_of = datetime.fromisoformat('2026-08-12T05:00:00+00:00')
        cls.card_pool = load_json('examples/deck-grammar/card-pool.json')['cards']
        cls.collection = load_json('examples/deck-grammar/collection.json')
        cls.entitlements = load_json('examples/deck-grammar/entitlements.json')['entitlements']
        cls.area = load_json('examples/deck-grammar/area.json')
        cls.goal = load_json('examples/deck-grammar/shared-goal.json')
        cls.intention = load_json('examples/deck-grammar/shared-intention.json')
        cls.presets = [load_yaml('presets/deck-grammar/canon-architect.preset.yaml'), load_yaml('presets/deck-grammar/bryminn-studio.preset.yaml')]
    def compile_proof(self):
        return compile_live_proof(card_definitions=self.card_pool, collection=self.collection, entitlements=self.entitlements, area=self.area, goal=self.goal, intention=self.intention, presets=self.presets, purpose_partition='deck_grammar_live_proof', platform='github', task_class='build_candidate_pack', authority_ceiling='propose', authority_grant_ref='authority.human.deck-grammar-candidate', as_of=self.as_of)
    def test_exactly_fifteen_schemas(self):
        self.assertEqual(len(self.schemas), 15)
    def test_same_goal_two_presets_preserve_invariants(self):
        proof = self.compile_proof()
        self.assertEqual(proof['verdict'], 'PASS')
        self.assertTrue(all(proof['invariants'].values()))
    def test_hands_use_different_cards(self):
        proof = self.compile_proof()
        first = {item['card_id'] for item in proof['hands'][0]['active_cards']}
        second = {item['card_id'] for item in proof['hands'][1]['active_cards']}
        self.assertNotEqual(first, second)
        self.assertIn('card.persona.brayn', first)
        self.assertIn('card.persona.bryminn', second)
    def test_premium_access_is_not_ownership(self):
        pool = build_access_pool(self.collection, self.entitlements, as_of=self.as_of)
        premium = {item['card_id']: item for item in pool if item['entitlement_ref'] == 'entitlement.premium.deck-grammar-proof'}
        self.assertEqual(premium['card.affordance.tribunal-docket']['ownership_claim'], 'not_owned')
        self.assertEqual(premium['card.affordance.vocal-mechanics']['authority_effect'], 'none')
    def test_owned_collection_is_unchanged_by_entitlements(self):
        before = content_hash(self.collection)
        build_access_pool(self.collection, self.entitlements, as_of=self.as_of)
        after = content_hash(self.collection)
        self.assertEqual(before, after)

    def test_build_access_pool_matches_linear_duplicate_check(self):
        collection = {
            'collection_id': 'collection.test.perf',
            'owner_ref': 'human.test',
            'card_instances': [
                {
                    'instance_id': f'card-instance.owned.{index:04d}',
                    'card_id': f'card.affordance.{index:04d}',
                    'holder_ref': 'human.test',
                    'access_kind': 'owned',
                    'state': 'accessible',
                    'acquired_at': '2026-01-01T00:00:00Z',
                    'ownership_claim': 'owned',
                    'authority_effect': 'none',
                    'edition': None,
                    'provenance_refs': ['source.collection.test'],
                    'metadata': {},
                }
                for index in range(400)
            ],
        }
        entitlements = []
        for ent_index in range(40):
            scope = [f'card.affordance.{((ent_index * 5) + offset) % 800:04d}' for offset in range(24)]
            scope.append(scope[0])
            entitlements.append({
                'entitlement_id': f'entitlement.test.{ent_index:04d}',
                'grantee_ref': 'human.test',
                'access_kind': 'premium',
                'state': 'active',
                'authority_effect': 'none',
                'starts_at': '2026-08-01T00:00:00Z',
                'ends_at': None,
                'scope': {'card_ids': scope},
                'source_ref': f'source.entitlement.{ent_index:04d}',
            })

        baseline = [json.loads(json.dumps(item)) for item in collection['card_instances']]
        owned = {item['card_id'] for item in baseline if item['access_kind'] == 'owned' and item['ownership_claim'] == 'owned'}
        for entitlement in entitlements:
            for card_id in entitlement['scope']['card_ids']:
                if card_id in owned:
                    continue
                instance_id = 'card-instance.entitled.' + _slug(entitlement['entitlement_id'].removeprefix('entitlement.')) + '.' + _slug(card_id.removeprefix('card.'))
                if any((existing['instance_id'] == instance_id for existing in baseline)):
                    continue
                baseline.append({'instance_id': instance_id, 'card_id': card_id, 'holder_ref': entitlement['grantee_ref'], 'access_kind': entitlement['access_kind'], 'state': 'accessible', 'acquired_at': entitlement['starts_at'], 'expires_at': entitlement.get('ends_at'), 'entitlement_ref': entitlement['entitlement_id'], 'ownership_claim': 'not_owned', 'authority_effect': 'none', 'edition': None, 'provenance_refs': [entitlement['source_ref']], 'metadata': {'entitlement_state': entitlement['state']}})

        actual = build_access_pool(collection, entitlements, as_of=self.as_of)
        self.assertEqual(len(actual), len({item['instance_id'] for item in actual}))
        self.assertEqual(baseline, actual)

    def test_build_access_pool_deduplicates_repeated_scope_ids(self):
        collection = {'collection_id': 'collection.test.scope', 'owner_ref': 'human.test', 'card_instances': []}
        entitlements = [{
            'entitlement_id': 'entitlement.test.dup',
            'grantee_ref': 'human.test',
            'access_kind': 'premium',
            'state': 'active',
            'authority_effect': 'none',
            'starts_at': '2026-08-01T00:00:00Z',
            'ends_at': None,
            'scope': {'card_ids': ['card.affordance.alpha', 'card.affordance.alpha', 'card.affordance.alpha']},
            'source_ref': 'source.entitlement.dup',
        }]
        actual = build_access_pool(collection, entitlements, as_of=self.as_of)
        self.assertEqual(1, len(actual))
        self.assertEqual('card.affordance.alpha', actual[0]['card_id'])
    def test_all_adversarial_cases_pass(self):
        manifest = load_json('evals/deck-grammar/fixtures.json')
        results = [evaluate_adversarial_case(load_json(ref['path']), as_of=self.as_of) for ref in manifest['cases']]
        self.assertEqual(len(results), 11)
        self.assertTrue(all((result['passed'] for result in results)), results)
    def test_non_ephemeral_hand_requires_consent(self):
        invalid = json.loads(json.dumps(self.compile_proof()['hands'][0]))
        invalid['persistence'] = 'saved_with_consent'
        invalid['metadata'].pop('consent_ref', None)
        validator = Draft202012Validator(self.schemas['active-hand.schema.json'], registry=self.registry)
        self.assertTrue(list(validator.iter_errors(invalid)))
    def test_asset_requires_clear_rights(self):
        invalid = load_json('examples/deck-grammar/asset.evidence-pack.json')
        invalid['rights']['status'] = 'unclear'
        validator = Draft202012Validator(self.schemas['asset.schema.json'], registry=self.registry)
        self.assertTrue(list(validator.iter_errors(invalid)))
    def test_scaffolder_generates_full_pack(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'example'
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/scaffold_quirk_object_pack.py'), '--repo', str(ROOT), '--kind', 'agent', '--id', 'agent.example', '--title', 'Example Agent', '--output', str(output)], check=False, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            generated = {path.name for path in output.iterdir()}
            self.assertEqual(generated, {'MANIFEST.yaml', 'README.md', 'REPO-MANAGEMENT.md', 'SYSTEM-PROMPT.md', 'CUSTOM-INSTRUCTIONS.md', 'SETTINGS.yaml', 'PROJECT-INSTRUCTIONS.md', 'REFERENCES.md', 'SKILL.md', 'EVALS.yaml', 'OPERATING-WORKFLOW.yaml'})
            for path in output.iterdir():
                self.assertNotIn('{{', path.read_text(encoding='utf-8'))
            workflow = yaml.safe_load((output / 'OPERATING-WORKFLOW.yaml').read_text(encoding='utf-8'))
            self.assertEqual(workflow['metadata']['id'], 'agent.example')

    def test_aesthetic_guard_rejects_price_or_accessibility_hiding(self):
        for field in ('price', 'accessibility'):
            result = evaluate_adversarial_case({'case_id': f'local-{field}', 'attack': 'aesthetic_hides_evidence', 'input': {'must_hide': [field]}, 'expected': 'reject'}, as_of=self.as_of)
            self.assertTrue(result['passed'], result)

    def test_scaffolder_supports_non_agent_object_families(self):
        registry = load_yaml('templates/quirk-object-pack/object-types.registry.yaml')
        kinds = [entry['kind'] for entry in registry['object_types']]
        self.assertIn('workflow', kinds)
        self.assertIn('revenue_stream', kinds)
        with tempfile.TemporaryDirectory() as temporary:
            for kind in ('workflow', 'content', 'revenue_stream'):
                output = Path(temporary) / kind
                result = subprocess.run([sys.executable, str(ROOT / 'scripts/scaffold_quirk_object_pack.py'), '--repo', str(ROOT), '--kind', kind, '--id', f'{kind}.sample', '--title', f'Sample {kind}', '--output', str(output)], check=False, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                manifest = yaml.safe_load((output / 'MANIFEST.yaml').read_text(encoding='utf-8'))
                self.assertEqual(manifest['kind'], kind)
                self.assertEqual(manifest['authority']['ceiling'], 'propose')
    def test_persisted_live_proof_is_reproducible(self):
        self.assertEqual(self.compile_proof(), load_json('examples/deck-grammar/live-proof.json'))
if __name__ == '__main__':
    unittest.main()
