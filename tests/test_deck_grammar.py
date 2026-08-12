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
    def test_persisted_live_proof_is_reproducible(self):
        self.assertEqual(self.compile_proof(), load_json('examples/deck-grammar/live-proof.json'))
if __name__ == '__main__':
    unittest.main()
