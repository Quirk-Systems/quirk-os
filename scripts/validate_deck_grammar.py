from __future__ import annotations
import argparse
from datetime import datetime
from pathlib import Path
from typing import Any
import json
import yaml
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from deck_grammar.compiler import compile_live_proof, content_hash, evaluate_adversarial_case, load_json, load_yaml
SCHEMA_FILES = ['active-hand.schema.json', 'aesthetic-contract.schema.json', 'affordance.schema.json', 'area.schema.json', 'art.schema.json', 'artifact.schema.json', 'asset.schema.json', 'card-definition.schema.json', 'card-instance.schema.json', 'collection.schema.json', 'eligible-deck.schema.json', 'entitlement-grant.schema.json', 'goal.schema.json', 'hand-preset.schema.json', 'intention.schema.json']
EXPECTED_OBJECT_TYPES = {'chatbot', 'platform', 'system', 'repository', 'prompt', 'chain', 'workflow', 'sequence', 'tool', 'evaluation', 'harness', 'automation', 'bot', 'content', 'slate', 'argument_set', 'permutation_set', 'plugin', 'capability', 'skill', 'agent', 'product', 'service', 'revenue_stream'}
EXPECTED_TEMPLATE_MODULES = {'MANIFEST.template.yaml', 'README.template.md', 'REPO-MANAGEMENT.template.md', 'SYSTEM-PROMPT.template.md', 'CUSTOM-INSTRUCTIONS.template.md', 'SETTINGS.template.yaml', 'PROJECT-INSTRUCTIONS.template.md', 'REFERENCES.template.md', 'SKILL.template.md', 'EVALS.template.yaml', 'OPERATING-WORKFLOW.template.yaml'}

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Validate the Quirk Deck Grammar candidate pack.')
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--require-pass', action='store_true')
    return parser.parse_args()

def make_registry(schemas: dict[str, dict[str, Any]]) -> Registry:
    registry = Registry()
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)
        registry = registry.with_resource(schema['$id'], Resource.from_contents(schema))
    return registry

def validation_errors(*, instance: Any, schema: dict[str, Any], registry: Registry) -> list[str]:
    validator = Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())
    return [f"{'/'.join((str(item) for item in error.absolute_path)) or '<root>'}: {error.message}" for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path))]

def record_validation(results: list[dict[str, Any]], *, name: str, instance: Any, schema_name: str, schemas: dict[str, dict[str, Any]], registry: Registry) -> bool:
    errors = validation_errors(instance=instance, schema=schemas[schema_name], registry=registry)
    results.append({'name': name, 'schema': schema_name, 'passed': not errors, 'errors': errors})
    return not errors

def main() -> int:
    args = parse_args()
    repo = args.repo.resolve()
    schemas = {filename: load_json(repo / 'schemas' / filename) for filename in SCHEMA_FILES}
    registry = make_registry(schemas)
    checks: list[dict[str, Any]] = []
    passed = True
    card_pool = load_json(repo / 'examples/deck-grammar/card-pool.json')['cards']
    collection = load_json(repo / 'examples/deck-grammar/collection.json')
    entitlements = load_json(repo / 'examples/deck-grammar/entitlements.json')['entitlements']
    area = load_json(repo / 'examples/deck-grammar/area.json')
    goal = load_json(repo / 'examples/deck-grammar/shared-goal.json')
    intention = load_json(repo / 'examples/deck-grammar/shared-intention.json')
    presets = [load_yaml(repo / 'presets/deck-grammar/canon-architect.preset.yaml'), load_yaml(repo / 'presets/deck-grammar/bryminn-studio.preset.yaml')]
    for card in card_pool:
        passed &= record_validation(checks, name=card['card_id'], instance=card, schema_name='card-definition.schema.json', schemas=schemas, registry=registry)
    passed &= record_validation(checks, name=collection['collection_id'], instance=collection, schema_name='collection.schema.json', schemas=schemas, registry=registry)
    for entitlement in entitlements:
        passed &= record_validation(checks, name=entitlement['entitlement_id'], instance=entitlement, schema_name='entitlement-grant.schema.json', schemas=schemas, registry=registry)
    for name, instance, schema_name in [(area['area_id'], area, 'area.schema.json'), (goal['goal_id'], goal, 'goal.schema.json'), (intention['intention_id'], intention, 'intention.schema.json')]:
        passed &= record_validation(checks, name=name, instance=instance, schema_name=schema_name, schemas=schemas, registry=registry)
    for preset in presets:
        passed &= record_validation(checks, name=preset['preset_id'], instance=preset, schema_name='hand-preset.schema.json', schemas=schemas, registry=registry)
    examples = {'affordance.contract-diff.json': 'affordance.schema.json', 'artifact.live-proof-report.json': 'artifact.schema.json', 'asset.evidence-pack.json': 'asset.schema.json', 'art.two-hands.json': 'art.schema.json', 'aesthetic.premium-chaos.json': 'aesthetic-contract.schema.json'}
    for filename, schema_name in examples.items():
        passed &= record_validation(checks, name=filename, instance=load_json(repo / 'examples/deck-grammar' / filename), schema_name=schema_name, schemas=schemas, registry=registry)
    fixture_manifest = load_json(repo / 'evals/deck-grammar/fixtures.json')
    as_of_text = fixture_manifest['as_of']
    as_of = datetime.fromisoformat(as_of_text.replace('Z', '+00:00'))
    proof = compile_live_proof(card_definitions=card_pool, collection=collection, entitlements=entitlements, area=area, goal=goal, intention=intention, presets=presets, purpose_partition='deck_grammar_live_proof', platform='github', task_class='build_candidate_pack', authority_ceiling='propose', authority_grant_ref='authority.human.deck-grammar-candidate', as_of=as_of)
    proof_matches = proof == load_json(repo / 'examples/deck-grammar/live-proof.json')
    checks.append({'name': 'same-goal-live-proof-reproducible', 'passed': proof_matches, 'errors': [] if proof_matches else ['generated live proof differs from persisted proof']})
    passed &= proof_matches
    passed &= record_validation(checks, name='live-proof-deck', instance=proof['deck'], schema_name='eligible-deck.schema.json', schemas=schemas, registry=registry)
    for hand in proof['hands']:
        passed &= record_validation(checks, name=hand['hand_id'], instance=hand, schema_name='active-hand.schema.json', schemas=schemas, registry=registry)
    invariant_pass = proof['verdict'] == 'PASS' and all(proof['invariants'].values())
    checks.append({'name': 'same-goal-two-presets-invariants', 'passed': invariant_pass, 'errors': [] if invariant_pass else [str(proof['invariants'])]})
    passed &= invariant_pass
    adversarial_results = []
    for fixture_ref in fixture_manifest['cases']:
        result = evaluate_adversarial_case(load_json(repo / fixture_ref['path']), as_of=as_of)
        adversarial_results.append(result)
        passed &= result['passed']
    registry_data = yaml.safe_load((repo / 'templates/quirk-object-pack/object-types.registry.yaml').read_text(encoding='utf-8'))
    actual_types = {entry['kind'] for entry in registry_data['object_types']}
    types_pass = actual_types == EXPECTED_OBJECT_TYPES
    checks.append({'name': 'quirk-object-type-registry-complete', 'passed': types_pass, 'errors': [] if types_pass else [f'missing={sorted(EXPECTED_OBJECT_TYPES - actual_types)} extra={sorted(actual_types - EXPECTED_OBJECT_TYPES)}']})
    passed &= types_pass
    actual_templates = {path.name for path in (repo / 'templates/quirk-object-pack').glob('*.template.*')}
    template_pass = actual_templates == EXPECTED_TEMPLATE_MODULES
    checks.append({'name': 'canonical-template-module-set', 'passed': template_pass, 'errors': [] if template_pass else [f'missing={sorted(EXPECTED_TEMPLATE_MODULES - actual_templates)} extra={sorted(actual_templates - EXPECTED_TEMPLATE_MODULES)}']})
    passed &= template_pass
    output = {'suite_id': 'eval.deck-grammar.v0.1', 'generated_at': as_of_text, 'status': 'passed' if passed else 'failed', 'schema_count': len(SCHEMA_FILES), 'schema_checks': checks, 'adversarial_cases': adversarial_results, 'live_proof': {'proof_id': proof['proof_id'], 'verdict': proof['verdict'], 'invariants': proof['invariants'], 'preset_refs': [hand['preset_ref'] for hand in proof['hands']], 'truth_snapshot': proof['hands'][0]['truth_snapshot'], 'ownership_snapshot': proof['hands'][0]['ownership_snapshot'], 'authority_snapshot': proof['hands'][0]['authority']}, 'protected_actions': {'manifest_activation': 0, 'canon_promotions': 0, 'ownership_mutations': 0, 'authority_expansions': 0, 'production_deployments': 0, 'persistent_hands_without_consent': 0}}
    output['content_hash'] = content_hash(output)
    serialized = json.dumps(output, indent=2, ensure_ascii=False) + '\n'
    if args.output:
        target = args.output if args.output.is_absolute() else repo / args.output
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(serialized, encoding='utf-8')
    print(serialized, end='')
    return 0 if passed else 1
if __name__ == '__main__':
    raise SystemExit(main())
