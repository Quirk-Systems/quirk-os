from __future__ import annotations
from datetime import datetime
from typing import Any
import json
from .common import DeckGrammarError, _slug, authority_not_above, content_hash, is_active_entitlement, parse_datetime, wildcard_match


def build_access_pool(collection: dict[str, Any], entitlements: list[dict[str, Any]], *, as_of: datetime) -> list[dict[str, Any]]:
    instances = [json.loads(json.dumps(item)) for item in collection['card_instances']]
    owned_card_ids = {item['card_id'] for item in instances if item['access_kind'] == 'owned' and item['ownership_claim'] == 'owned'}
    for entitlement in entitlements:
        if not is_active_entitlement(entitlement, as_of):
            continue
        if entitlement.get('authority_effect') != 'none':
            raise DeckGrammarError('an entitlement may not alter authority')
        for card_id in entitlement.get('scope', {}).get('card_ids', []):
            if card_id in owned_card_ids:
                continue
            instance_id = 'card-instance.entitled.' + _slug(entitlement['entitlement_id'].removeprefix('entitlement.')) + '.' + _slug(card_id.removeprefix('card.'))
            if any((existing['instance_id'] == instance_id for existing in instances)):
                continue
            instances.append({'instance_id': instance_id, 'card_id': card_id, 'holder_ref': entitlement['grantee_ref'], 'access_kind': entitlement['access_kind'], 'state': 'accessible', 'acquired_at': entitlement['starts_at'], 'expires_at': entitlement.get('ends_at'), 'entitlement_ref': entitlement['entitlement_id'], 'ownership_claim': 'not_owned', 'authority_effect': 'none', 'edition': None, 'provenance_refs': [entitlement['source_ref']], 'metadata': {'entitlement_state': entitlement['state']}})
    return instances

def compile_deck(*, card_definitions: list[dict[str, Any]], collection: dict[str, Any], entitlements: list[dict[str, Any]], area: dict[str, Any], goal: dict[str, Any], intention: dict[str, Any], purpose_partition: str, platform: str, task_class: str, authority_ceiling: str, explicit_exclusions: list[str] | None=None, as_of: datetime, compiler_version: str='0.1.0') -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    cards_by_id = {card['card_id']: card for card in card_definitions}
    access_instances = build_access_pool(collection, entitlements, as_of=as_of)
    instances_by_id = {instance['instance_id']: instance for instance in access_instances}
    exclusions = set(explicit_exclusions or [])
    eligible: list[str] = []
    excluded: list[dict[str, str]] = []
    for instance in access_instances:
        reason: str | None = None
        detail = ''
        card = cards_by_id.get(instance['card_id'])
        if card is None:
            reason = 'unknown_card'
        elif instance['state'] in {'expired', 'revoked', 'transferred'}:
            reason = 'expired_access' if instance['state'] == 'expired' else 'revoked_access'
        elif (expires := parse_datetime(instance.get('expires_at'))) and as_of >= expires:
            reason = 'expired_access'
        elif instance['card_id'] in exclusions:
            reason = 'explicitly_excluded'
        elif not wildcard_match(card['compatibility']['purpose_partitions'], purpose_partition):
            reason = 'purpose_mismatch'
        elif not wildcard_match(card['compatibility'].get('area_refs', []), area['area_id']):
            reason = 'area_mismatch'
        elif not wildcard_match(card['compatibility']['platforms'], platform):
            reason = 'platform_mismatch'
        elif not wildcard_match(card['compatibility']['task_classes'], task_class):
            reason = 'task_mismatch'
        elif not authority_not_above(card['authority_ceiling'], authority_ceiling):
            reason = 'authority_mismatch'
        elif card['compatibility'].get('required_capabilities'):
            reason = 'missing_capability'
            detail = ','.join(card['compatibility']['required_capabilities'])
        if reason:
            excluded.append({'instance_id': instance['instance_id'], 'reason_code': reason, 'detail': detail})
        else:
            eligible.append(instance['instance_id'])
    deck_id = 'deck.' + _slug(goal['goal_id'].removeprefix('goal.')) + '.' + content_hash({'eligible': eligible, 'purpose': purpose_partition, 'platform': platform, 'task': task_class})[:12]
    deck = {'deck_id': deck_id, 'purpose_partition': purpose_partition, 'area_ref': area['area_id'], 'goal_ref': goal['goal_id'], 'intention_ref': intention['intention_id'], 'platform': platform, 'task_class': task_class, 'authority_ceiling': authority_ceiling, 'card_instance_ids': eligible, 'excluded_cards': excluded, 'compiler_version': compiler_version, 'generated_at': as_of.isoformat().replace('+00:00', 'Z'), 'source_hashes': {'card_definitions': content_hash(card_definitions), 'collection': content_hash(collection), 'entitlements': content_hash(entitlements), 'area': content_hash(area), 'goal': content_hash(goal), 'intention': content_hash(intention)}, 'metadata': {'cards_do_not_grant_authority': True}}
    return (deck, cards_by_id, instances_by_id)
