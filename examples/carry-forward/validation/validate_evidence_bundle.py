#!/usr/bin/env python3
"""Candidate repair of the installed Compounder structural validator.

Strict shapes prevent malformed data from masquerading as authority. A passing
result still establishes neither real authorization nor source truth. Unknown
extension fields are preserved and uninterpreted. See candidate-provenance.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_CENSUS_KEYS = {
    'canonical', 'candidates', 'derived_projections', 'superseded',
    'conflicting', 'unresolved', 'missing',
}
PROTECTED_ACTIONS = {
    'canon_write', 'authority_expand', 'irreversible_change',
    'protected_label_change', 'production_release', 'data_product_publish', 'execute_protected',
}
# Fixed compatibility vocabulary. Rights come from references/control-kernel.md;
# local_candidate_build preserves the existing consumer's bounded build receipt.
# Bundle data cannot register additional supported actions or grant permission.
SUPPORTED_ACTIONS = frozenset(PROTECTED_ACTIONS | {
    'observe', 'infer', 'propose', 'execute_reversible', 'local_candidate_build',
})
CHECKED_INVARIANTS = [
    'source_census_shape', 'receipt_lineage', 'protected_action_authority',
    'capability_never_implies_authority', 'proposed_moves_remain_candidate',
    'strict_permission_booleans', 'known_container_shapes',
    'supported_action_vocabulary',
]


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def object_field(parent: dict[str, Any], key: str, path: str,
                 errors: list[str], required: bool = False) -> dict[str, Any] | None:
    if key not in parent and not required:
        return None
    value = parent.get(key)
    if not isinstance(value, dict):
        errors.append(f'{path} must be an object')
        return None
    return value


def list_field(parent: dict[str, Any], key: str, path: str,
               errors: list[str], required: bool = False) -> list[Any] | None:
    if key not in parent and not required:
        return None
    value = parent.get(key)
    if not isinstance(value, list):
        errors.append(f'{path} must be a list')
        return None
    return value


def boolean_field(parent: dict[str, Any], key: str, path: str,
                  errors: list[str], required: bool = False) -> None:
    if key in parent or required:
        require(type(parent.get(key)) is bool, f'{path} must be a boolean', errors)


def validate_census(bundle: dict[str, Any], errors: list[str]) -> None:
    census = object_field(bundle, 'source_census', 'source_census', errors, required=True)
    if census is None:
        return
    for key in sorted(REQUIRED_CENSUS_KEYS):
        entries = list_field(census, key, f'source_census.{key}', errors, required=True)
        if entries is not None:
            for index, entry in enumerate(entries):
                require(isinstance(entry, dict), f'source_census.{key}[{index}] must be an object', errors)
    for key in ['freshness_risks', 'authority_decision_refs']:
        list_field(census, key, f'source_census.{key}', errors)


def validate_receipt(bundle: dict[str, Any], errors: list[str]) -> None:
    receipt = object_field(bundle, 'run_receipt', 'run_receipt', errors, required=True)
    if receipt is None:
        return
    require('run_id' in receipt, 'run_receipt missing run_id', errors)
    sections = {}
    for key in ['inputs', 'execution', 'outputs', 'quality', 'lineage']:
        sections[key] = object_field(receipt, key, f'run_receipt.{key}', errors, required=True)
    for key in ['economics', 'outcome']:
        sections[key] = object_field(receipt, key, f'run_receipt.{key}', errors)
    list_shapes = {
        'inputs': ['source_refs', 'fingerprints'], 'execution': ['tools'],
        'outputs': ['object_refs', 'output_hashes'], 'quality': ['warnings'],
        'lineage': ['parent_run_ids', 'transformation_refs'],
    }
    for section, keys in list_shapes.items():
        value = sections[section]
        if value is None:
            continue
        for key in keys:
            required = (section, key) in [('inputs', 'fingerprints'), ('lineage', 'transformation_refs')]
            items = list_field(value, key, f'run_receipt.{section}.{key}', errors, required)
            if (section, key) == ('inputs', 'fingerprints') and items is not None:
                require(bool(items), 'run_receipt requires input fingerprints', errors)
    if sections['quality'] is not None:
        object_field(sections['quality'], 'eval_scores', 'run_receipt.quality.eval_scores', errors)
        boolean_field(sections['quality'], 'contract_valid', 'run_receipt.quality.contract_valid', errors)
    if sections['outcome'] is not None:
        for key in ['accepted', 'reused']:
            boolean_field(sections['outcome'], key, f'run_receipt.outcome.{key}', errors)


def validate_authority(bundle: dict[str, Any], errors: list[str]) -> None:
    decisions = list_field(bundle, 'authority_decisions', 'authority_decisions', errors, required=True)
    if decisions is None:
        return
    for index, decision in enumerate(decisions):
        path = f'authority_decisions[{index}]'
        if not isinstance(decision, dict):
            errors.append(f'{path} must be an object')
            continue
        action = decision.get('action')
        valid_action = isinstance(action, str) and bool(action) and action == action.strip()
        require(valid_action, f'{path}.action must be a nonempty string without surrounding whitespace', errors)
        if valid_action:
            require(action in SUPPORTED_ACTIONS, f'{path}.action is unsupported: {action}', errors)
        boolean_field(decision, 'allowed', f'{path}.allowed', errors, required=True)
        boolean_field(decision, 'explicit_authority', f'{path}.explicit_authority', errors)
        allowed = decision.get('allowed')
        if valid_action and action in PROTECTED_ACTIONS and allowed is True:
            require(decision.get('explicit_authority') is True,
                    f'protected action {action} allowed without explicit authority', errors)
        if decision.get('authority_basis') == 'capability' and allowed is True:
            errors.append(f'capability treated as authority for action {action}')


def validate_moves(bundle: dict[str, Any], errors: list[str]) -> list[Any] | None:
    moves = list_field(bundle, 'proposed_moves', 'proposed_moves', errors, required=True)
    if moves is None:
        return None
    for index, move in enumerate(moves):
        path = f'proposed_moves[{index}]'
        if not isinstance(move, dict):
            errors.append(f'{path} must be an object')
            continue
        require(move.get('status') == 'candidate', f'{path} must remain candidate', errors)
        evidence = list_field(move, 'evidence_refs', f'{path}.evidence_refs', errors, required=True)
        if evidence is not None:
            require(bool(evidence), f'{path} requires evidence_refs', errors)
        for key in ['target_refs', 'acceptance_criteria', 'blockers']:
            list_field(move, key, f'{path}.{key}', errors)
    return moves


def validate_dividend(bundle: dict[str, Any], errors: list[str]) -> None:
    dividend = object_field(bundle, 'system_dividend', 'system_dividend', errors, required=True)
    if dividend is None:
        return
    object_field(dividend, 'quality_delta', 'system_dividend.quality_delta', errors)
    for key in ['structured_data_updates', 'reusable_move_candidates', 'skill_or_capability_candidates',
                'cleanup_or_mapping_proposals', 'next_proposed_moves']:
        list_field(dividend, key, f'system_dividend.{key}', errors)


def validate(bundle: Any) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(bundle, dict):
        errors.append('bundle root must be an object')
    else:
        require(bundle.get('bundle_version') is not None, 'missing bundle_version', errors)
        validate_census(bundle, errors)
        validate_receipt(bundle, errors)
        validate_authority(bundle, errors)
        moves = validate_moves(bundle, errors)
        validate_dividend(bundle, errors)
        if not errors and not moves:
            warnings.append('bundle is valid but contains no Proposed Moves')
    return {'valid': not errors, 'errors': errors, 'warnings': warnings,
            'checked_invariants': list(CHECKED_INVARIANTS)}


def main() -> int:
    if len(sys.argv) != 2:
        print('usage: validate_evidence_bundle.py BUNDLE.json', file=sys.stderr)
        return 2
    try:
        bundle = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    except (OSError, ValueError, RecursionError) as exc:
        print(json.dumps({'valid': False, 'errors': [str(exc)], 'warnings': []}, indent=2))
        return 1
    result = validate(bundle)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result['valid'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
