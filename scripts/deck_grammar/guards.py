from __future__ import annotations
from datetime import datetime
from typing import Any
from .common import DeckGrammarError, parse_datetime


def evaluate_adversarial_case(case: dict[str, Any], *, as_of: datetime) -> dict[str, Any]:
    attack = case['attack']
    payload = case['input']
    decision: str
    reason: str
    if attack == 'premium_authority_escalation':
        decision = 'reject' if payload.get('authority_effect') != 'none' else 'allow'
        reason = 'entitlements may alter access, never authority'
    elif attack == 'borrowed_claimed_owned':
        decision = 'reject' if payload.get('access_kind') == 'borrowed' and payload.get('ownership_claim') == 'owned' else 'allow'
        reason = 'borrowed access cannot be represented as ownership'
    elif attack == 'expired_entitlement_in_deck':
        ends = parse_datetime(payload.get('ends_at'))
        decision = 'exclude' if ends and as_of >= ends and payload.get('included') else 'allow'
        reason = 'expired access is removed from the eligible Deck'
    elif attack == 'persona_permanent_identity':
        decision = 'reject' if payload.get('permanent_assignment') else 'allow'
        reason = 'a Persona card is a temporary functional lens'
    elif attack == 'aesthetic_hides_evidence':
        hidden = set(payload.get('must_hide', []))
        protected = {'evidence', 'uncertainty', 'authority', 'risk', 'price', 'accessibility'}
        decision = 'reject' if hidden & protected else 'allow'
        reason = 'aesthetic may not hide evidence, uncertainty, authority, risk, price, or accessibility'
    elif attack == 'area_preference_leak':
        decision = 'exclude' if payload.get('card_area_ref') != payload.get('current_area_ref') and payload.get('included') else 'allow'
        reason = 'purpose and Area partitions prevent preference leakage'
    elif attack == 'artifact_promoted_without_rights':
        decision = 'reject' if payload.get('promotion_requested') and (not (payload.get('rights_status') == 'clear' and payload.get('provenance_complete') is True)) else 'allow'
        reason = 'Asset promotion requires clear rights and provenance'
    elif attack == 'owned_card_removed_with_subscription':
        decision = 'preserve_owned' if payload.get('access_kind') == 'owned' and payload.get('subscription_cancelled') and payload.get('remove_requested') else 'allow'
        reason = 'subscription cancellation cannot remove independently owned cards'
    elif attack == 'rarity_used_as_quality':
        decision = 'reject' if payload.get('quality_claim_source') == 'rarity' else 'allow'
        reason = 'rarity and quality are independent dimensions'
    elif attack == 'discard_deletes_history':
        decision = 'reject' if payload.get('discard') and payload.get('delete_underlying') else 'allow'
        reason = 'discard removes a card from the Hand, not from history'
    elif attack == 'hand_persists_without_consent':
        decision = 'require_consent' if payload.get('persistence') != 'ephemeral' and (not payload.get('consent_ref')) else 'allow'
        reason = 'non-ephemeral Hands require explicit consent'
    else:
        raise DeckGrammarError(f'unknown attack: {attack}')
    return {'case_id': case['case_id'], 'attack': attack, 'decision': decision, 'reason': reason, 'expected': case['expected'], 'passed': decision == case['expected']}
