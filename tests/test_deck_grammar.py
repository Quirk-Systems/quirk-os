from __future__ import annotations
from datetime import datetime
from pathlib import Path
import json
import re
import subprocess
import sys
import tempfile
import unittest
import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from deck_grammar.compiler import build_access_pool, compile_deck, compile_live_proof, content_hash, evaluate_adversarial_case, wildcard_match
from deck_grammar.access import _slug
SCHEMA_FILES = ['active-hand.schema.json', 'aesthetic-contract.schema.json', 'affordance.schema.json', 'area.schema.json', 'art.schema.json', 'artifact.schema.json', 'asset.schema.json', 'card-definition.schema.json', 'card-instance.schema.json', 'collection.schema.json', 'eligible-deck.schema.json', 'entitlement-grant.schema.json', 'goal.schema.json', 'hand-preset.schema.json', 'intention.schema.json']

def committed_json(relative: str):
    """Parse a path as it exists in the current commit, not the working tree.

    The conformance workflows delete the tracked evidence artifact before
    running anything, so that an `always()` upload cannot ship a committed
    passing result as a failed run's evidence. A test that read the working
    tree would therefore fail in CI for a reason that has nothing to do with
    what it asserts — which is exactly what happened on `33769ba`. Reading the
    commit is also the more faithful reading: the claim is that the committed
    documents quote the committed artifact's digest.
    """
    return json.loads(
        subprocess.run(
            ["git", "show", f"HEAD:{relative}"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    )

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
    def compile_pool(self, pool):
        return compile_deck(card_definitions=pool, collection=self.collection, entitlements=self.entitlements, area=self.area, goal=self.goal, intention=self.intention, purpose_partition='deck_grammar_live_proof', platform='github', task_class='build_candidate_pack', authority_ceiling='propose', as_of=self.as_of)
    def retire_one_card(self, status: str):
        pool = json.loads(json.dumps(self.card_pool))
        target = pool[0]
        target['status'] = status
        return (pool, target['card_id'])
    def test_retired_and_deprecated_cards_leave_the_deck(self):
        """Retiring a card has to remove it. The compiler used to never read `status`."""
        for status in ('retired', 'deprecated'):
            with self.subTest(status=status):
                pool, card_id = self.retire_one_card(status)
                deck, _, instances_by_id = self.compile_pool(pool)
                live = {instances_by_id[i]['card_id'] for i in deck['card_instance_ids']}
                self.assertNotIn(card_id, live)
                excluded = [item for item in deck['excluded_cards'] if instances_by_id[item['instance_id']]['card_id'] == card_id]
                self.assertEqual([('card_status_ineligible', status)], [(item['reason_code'], item['detail']) for item in excluded])
    def test_a_card_in_a_live_status_stays_in_the_deck(self):
        """The guard excludes the two terminal statuses only, never a candidate."""
        for status in ('candidate', 'evaluated', 'admitted'):
            with self.subTest(status=status):
                pool, card_id = self.retire_one_card(status)
                deck, _, instances_by_id = self.compile_pool(pool)
                live = {instances_by_id[i]['card_id'] for i in deck['card_instance_ids']}
                self.assertIn(card_id, live)
    def test_deck_with_a_retired_card_still_validates(self):
        pool, _ = self.retire_one_card('retired')
        deck, _, _ = self.compile_pool(pool)
        validator = Draft202012Validator(self.schemas['eligible-deck.schema.json'], registry=self.registry)
        self.assertEqual([], list(validator.iter_errors(deck)))
    def test_persisted_live_proof_records_the_current_compiler_version(self):
        """A Deck's provenance has to name the semantics that produced it.

        Paired with test_persisted_live_proof_is_reproducible, this means an
        eligibility change cannot land without both a version bump and a
        regenerated proof: otherwise two compilers emit different Decks under
        identical source hashes and an identical compiler version.
        """
        from deck_grammar.access import COMPILER_VERSION
        persisted = load_json('examples/deck-grammar/live-proof.json')
        self.assertEqual(COMPILER_VERSION, persisted['deck']['compiler_version'])
        self.assertEqual(COMPILER_VERSION, self.compile_pool(self.card_pool)[0]['compiler_version'])
    def test_wildcard_match_separates_an_absent_list_from_an_empty_one(self):
        """An empty allow-list used to permit everything, so the check could not fail."""
        self.assertTrue(wildcard_match(None, 'github'))
        self.assertFalse(wildcard_match([], 'github'))
        self.assertTrue(wildcard_match(['*'], 'github'))
        self.assertTrue(wildcard_match(['github'], 'github'))
        self.assertFalse(wildcard_match(['gitlab'], 'github'))
    def test_a_card_declaring_no_platforms_is_not_universally_eligible(self):
        for dimension, reason in (('platforms', 'platform_mismatch'), ('purpose_partitions', 'purpose_mismatch'), ('task_classes', 'task_mismatch')):
            with self.subTest(dimension=dimension):
                pool = json.loads(json.dumps(self.card_pool))
                pool[0]['compatibility'][dimension] = []
                card_id = pool[0]['card_id']
                deck, _, instances_by_id = self.compile_pool(pool)
                live = {instances_by_id[i]['card_id'] for i in deck['card_instance_ids']}
                self.assertNotIn(card_id, live)
                excluded = [item['reason_code'] for item in deck['excluded_cards'] if instances_by_id[item['instance_id']]['card_id'] == card_id]
                self.assertEqual([reason], excluded)
    def test_a_card_omitting_the_optional_area_key_stays_unconstrained_by_area(self):
        """`area_refs` is optional in the card schema, so leaving it out must still match."""
        pool = json.loads(json.dumps(self.card_pool))
        pool[0]['compatibility'].pop('area_refs')
        card_id = pool[0]['card_id']
        deck, _, instances_by_id = self.compile_pool(pool)
        live = {instances_by_id[i]['card_id'] for i in deck['card_instance_ids']}
        self.assertIn(card_id, live)
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


class ContentHashBindingTests(unittest.TestCase):
    """An artifact manifest's `content_hash` must match the bytes it names.

    Nothing checked this, so bumping `compiler_version` in the live proof
    silently invalidated the accepted evaluation report: the report kept
    recording the pre-bump `828dc88d...` while the proof hashed to
    `9f633bea...`. A reference whose digest no longer matches the bytes reads
    as a verification that happened, which is worse than no reference.
    """

    def test_the_live_proof_report_binds_to_the_proof_it_names(self):
        report = load_json('examples/deck-grammar/artifact.live-proof-report.json')
        self.assertEqual(report['content_hash'], content_hash(load_json(report['content_ref'])))

    def test_the_evidence_deletion_precedes_every_failable_step(self):
        """The upload runs on `always()`, so the deletion must be unskippable.

        Checkout restores the committed `conformance-results.json`, which
        records a pass. Any post-checkout failure skips the later steps by the
        default success condition while the upload still fires, publishing that
        committed file as the failed run's evidence. `if-no-files-found: error`
        cannot catch it, because the upload also names `live-proof.json` and
        that path still exists.

        When this deletion was added it sat after `setup-python` and the
        dependency install, leaving exactly that window open for the two steps
        most likely to fail for reasons unrelated to the change.
        """
        workflow = load_yaml('.github/workflows/deck-grammar-conformance.yml')
        steps = [
            step.get('name')
            for step in workflow['jobs']['candidate-deck-conformance']['steps']
        ]
        deletion = next(i for i, name in enumerate(steps) if 'Discard' in (name or ''))
        self.assertEqual(
            ['Checkout'],
            steps[:deletion],
            'a step that can fail precedes the deletion of the tracked evidence',
        )

    def test_the_workflow_rejects_committed_evidence_it_cannot_reproduce(self):
        # `test_the_admission_docs_quote_the_tracked_conformance_digest` below
        # compares the committed documents to the committed artifact. A change
        # that alters the payload while leaving both untouched therefore
        # compares stale to stale and passes, and the validator rewrites the
        # artifact without comparing it to what is committed. The workflow has
        # to diff the regenerated file against the committed blob, or green CI
        # can merge an evidence of record the tree no longer produces.
        workflow = load_yaml('.github/workflows/deck-grammar-conformance.yml')
        runs = '\n'.join(
            str(step.get('run', ''))
            for step in workflow['jobs']['candidate-deck-conformance']['steps']
        )
        self.assertIn(
            'git diff --exit-code -- evals/deck-grammar/conformance-results.json', runs
        )

    def test_the_admission_docs_quote_the_tracked_conformance_digest(self):
        # The stale digest that prompted the `content-hash-binds` check was not
        # the only dangling one: two documents quoted the Deck Grammar
        # conformance hash and nothing compared them to the artifact, so the
        # suite could gain a check while the docs described the suite without
        # it. Superseded hashes may still appear — the documents record them
        # deliberately — so this asserts the current one is present, not that
        # no other is.
        tracked = committed_json('evals/deck-grammar/conformance-results.json')['content_hash']
        # Compare the NAMED current-hash field in each document, not "appears
        # somewhere": both also quote the superseded hash on purpose, so a
        # containment check would pass with the current and superseded values
        # swapped, or with the current one only in a prose aside.
        named = {
            'docs/deck-grammar/ADMISSION-EVALUATION.md': r'^\| Revised evaluation conformance hash \| `([0-9a-f]{64})` \|',
            'docs/deck-grammar/README.md': r'Revised evaluation conformance content hash.*?`([0-9a-f]{64})`',
        }
        for doc, pattern in named.items():
            with self.subTest(doc=doc):
                found = re.search(pattern, (ROOT / doc).read_text(encoding='utf-8'), re.M | re.S)
                self.assertIsNotNone(found, f'{doc} has no current-hash field')
                self.assertEqual(tracked, found.group(1))

    def test_the_binding_notices_a_changed_proof(self):
        # The check is only worth recording if a change to the referenced file
        # moves the hash.
        referenced = load_json(
            load_json('examples/deck-grammar/artifact.live-proof-report.json')['content_ref']
        )
        mutated = {**referenced, 'verdict': 'NOT_THE_REAL_VERDICT'}
        self.assertNotEqual(content_hash(referenced), content_hash(mutated))


if __name__ == '__main__':
    unittest.main()
