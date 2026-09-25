from __future__ import annotations
from datetime import datetime
from typing import Any
from .common import AUTHORITY_ORDER, DeckGrammarError, _slug, content_hash, wildcard_match
from .access import compile_deck


def _ordered_candidates(*, slot: dict[str, Any], eligible_instances: list[dict[str, Any]], cards_by_id: dict[str, dict[str, Any]], used_instances: set[str]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    selectors = slot['selectors']
    preferred = selectors.get('prefer_card_ids', [])
    required_tags = set(selectors.get('require_tags', []))
    excluded = set(selectors.get('exclude_card_ids', []))
    candidates: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for instance in eligible_instances:
        if instance['instance_id'] in used_instances:
            continue
        card = cards_by_id[instance['card_id']]
        if card['card_kind'] != slot['card_kind'] or card['card_id'] in excluded:
            continue
        tags = set(card.get('metadata', {}).get('tags', []))
        if required_tags and (not required_tags.issubset(tags)):
            continue
        candidates.append((instance, card))
    preference_index = {card_id: index for index, card_id in enumerate(preferred)}
    candidates.sort(key=lambda pair: (preference_index.get(pair[1]['card_id'], len(preferred) + 1), pair[1]['card_id'], pair[0]['instance_id']))
    return candidates

def compile_hand(*, deck: dict[str, Any], preset: dict[str, Any], cards_by_id: dict[str, dict[str, Any]], instances_by_id: dict[str, dict[str, Any]], collection: dict[str, Any], goal: dict[str, Any], intention: dict[str, Any], area: dict[str, Any], authority_grant_ref: str, external_authority_ceiling: str) -> dict[str, Any]:
    applies = preset['applies_when']
    if not wildcard_match(applies['purpose_partitions'], deck['purpose_partition']):
        raise DeckGrammarError('preset purpose does not match')
    if not wildcard_match(applies['task_classes'], deck['task_class']):
        raise DeckGrammarError('preset task class does not match')
    if applies.get('platforms') and (not wildcard_match(applies['platforms'], deck['platform'])):
        raise DeckGrammarError('preset platform does not match')
    if applies.get('area_refs') and (not wildcard_match(applies['area_refs'], deck['area_ref'])):
        raise DeckGrammarError('preset area does not match')
    if preset['personalization']['permanent_persona_assignment'] is not False:
        raise DeckGrammarError('a preset may not permanently assign a persona')
    if preset['personalization']['auto_persist_hand'] is not False:
        raise DeckGrammarError('a preset may not auto-persist a Hand')
    if preset['authority']['cards_cannot_expand_authority'] is not True:
        raise DeckGrammarError('a preset must state that cards cannot expand authority')
    preset_ceiling = preset['authority']['maximum_right']
    effective_ceiling = min((external_authority_ceiling, preset_ceiling), key=lambda value: AUTHORITY_ORDER[value])
    eligible_instances = [instances_by_id[i] for i in deck['card_instance_ids']]
    used: set[str] = set()
    active_cards: list[dict[str, Any]] = []
    for slot in preset['slots']:
        candidates = _ordered_candidates(slot=slot, eligible_instances=eligible_instances, cards_by_id=cards_by_id, used_instances=used)
        selected = candidates[:slot['maximum']]
        if len(selected) < slot['minimum']:
            raise DeckGrammarError(f"slot {slot['slot_id']} requires {slot['minimum']} card(s); only {len(selected)} eligible")
        for instance, card in selected:
            used.add(instance['instance_id'])
            active_cards.append({'instance_id': instance['instance_id'], 'card_id': card['card_id'], 'slot': slot['slot_id'], 'role': slot.get('default_role', slot['slot_id']), 'weight': slot.get('default_weight', 1.0), 'authority_effect': 'none', 'reason': f"selected by {preset['preset_id']} for {deck['purpose_partition']} / {deck['task_class']}"})
    persona_weight = sum((item['weight'] for item in active_cards if cards_by_id[item['card_id']]['card_kind'] == 'persona'))
    if persona_weight > 1.000001:
        raise DeckGrammarError('Persona Hand weights may not exceed 1.0')
    owned_instance_ids = sorted((instance['instance_id'] for instance in collection['card_instances'] if instance['access_kind'] == 'owned' and instance['ownership_claim'] == 'owned'))
    truth_snapshot = {'goal_hash': content_hash({'goal_id': goal['goal_id'], 'desired_state': goal['desired_state'], 'evidence_of_completion': goal['evidence_of_completion'], 'constraints': goal['constraints']}), 'facts_hash': content_hash(goal['facts'])}
    ownership_snapshot = {'collection_hash': content_hash({'collection_id': collection['collection_id'], 'owner_ref': collection['owner_ref'], 'owned_instance_ids': owned_instance_ids}), 'owned_instance_ids': owned_instance_ids}
    hand_id = 'hand.' + _slug(goal['goal_id'].removeprefix('goal.')) + '.' + _slug(preset['preset_id'].removeprefix('preset.')) + '.' + content_hash([item['instance_id'] for item in active_cards])[:10]
    return {'hand_id': hand_id, 'deck_id': deck['deck_id'], 'preset_ref': preset['preset_id'], 'purpose_partition': deck['purpose_partition'], 'area_ref': area['area_id'], 'goal_ref': goal['goal_id'], 'intention_ref': intention['intention_id'], 'active_cards': active_cards, 'authority': {'ceiling': effective_ceiling, 'grant_ref': authority_grant_ref, 'cards_cannot_expand_authority': True}, 'truth_snapshot': truth_snapshot, 'ownership_snapshot': ownership_snapshot, 'state': 'proposed', 'persistence': 'ephemeral', 'expires': {'condition': 'task_resolved', 'at': None}, 'approach': preset['approach'], 'metadata': {'current_instruction_wins': True, 'premium_access_is_not_ownership': True, 'rarity_is_not_quality': True}}

def compile_live_proof(*, card_definitions: list[dict[str, Any]], collection: dict[str, Any], entitlements: list[dict[str, Any]], area: dict[str, Any], goal: dict[str, Any], intention: dict[str, Any], presets: list[dict[str, Any]], purpose_partition: str, platform: str, task_class: str, authority_ceiling: str, authority_grant_ref: str, as_of: datetime) -> dict[str, Any]:
    deck, cards_by_id, instances_by_id = compile_deck(card_definitions=card_definitions, collection=collection, entitlements=entitlements, area=area, goal=goal, intention=intention, purpose_partition=purpose_partition, platform=platform, task_class=task_class, authority_ceiling=authority_ceiling, as_of=as_of)
    hands = [compile_hand(deck=deck, preset=preset, cards_by_id=cards_by_id, instances_by_id=instances_by_id, collection=collection, goal=goal, intention=intention, area=area, authority_grant_ref=authority_grant_ref, external_authority_ceiling=authority_ceiling) for preset in presets]
    if len(hands) != 2:
        raise DeckGrammarError('the first live proof requires exactly two Presets')
    first, second = hands
    invariants = {'same_goal_ref': first['goal_ref'] == second['goal_ref'] == goal['goal_id'], 'same_truth_snapshot': first['truth_snapshot'] == second['truth_snapshot'], 'same_ownership_snapshot': first['ownership_snapshot'] == second['ownership_snapshot'], 'same_authority': first['authority'] == second['authority'], 'different_active_cards': {item['card_id'] for item in first['active_cards']} != {item['card_id'] for item in second['active_cards']}, 'different_approach': first['approach'] != second['approach']}
    verdict = 'PASS' if all(invariants.values()) else 'FAIL'
    return {'proof_id': 'proof.deck-grammar.same-goal-two-presets.v0.1', 'generated_at': as_of.isoformat().replace('+00:00', 'Z'), 'goal': goal, 'intention': intention, 'area': area, 'deck': deck, 'hands': hands, 'invariants': invariants, 'verdict': verdict, 'statement': 'The Hand changes the approach without changing truth, ownership, or authority.' if verdict == 'PASS' else 'One or more Deck Grammar invariants failed.'}
