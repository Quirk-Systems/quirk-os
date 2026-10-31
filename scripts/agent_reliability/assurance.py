"""v0.2.0 assurance extension. Inert fixtures, never an authorization service.

Grader callbacks must be trusted local code; this module is not a sandbox.
Policies and reviewer identities are supplied assertions, not authenticated facts.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from .pack import evaluate_authority, evaluate_completion
from .runner import run_pack

VERSION = 'agent-assurance.v0.2.0'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def audit_grader(grader, controls):
    """Known-answer, immediate repetition, forward/reverse and mutation checks.

    Only final JSON argument state is observed: transient mutations, external
    state and malicious callbacks are outside this audit's observation boundary.
    """
    if not isinstance(controls, list) or not controls:
        raise ValueError('nonempty known-answer controls required')
    ids = []
    for c in controls:
        if (not isinstance(c, dict) or not isinstance(c.get('id'), str)
                or not c['id'] or not isinstance(c.get('case'), dict)
                or type(c.get('expected')) is not bool):
            raise ValueError('invalid control')
        ids.append(c['id'])
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate control IDs')
    original = digest(controls)
    failures, observed = [], {}
    for order in (controls, list(reversed(controls)), controls):
        for c in order:
            argument = copy.deepcopy(c['case'])
            before = digest(argument)
            for _ in range(2):
                try:
                    result = grader(argument)
                    if type(result) is not bool or result is not c['expected']:
                        failures.append([c['id'], 'wrong_answer_or_type'])
                    if c['id'] in observed and result != observed[c['id']]:
                        failures.append([c['id'], 'unstable_verdict'])
                    observed[c['id']] = copy.deepcopy(result)
                except Exception:
                    failures.append([c['id'], 'grader_exception'])
                try:
                    if digest(argument) != before:
                        failures.append([c['id'], 'input_mutation'])
                except (TypeError, ValueError):
                    failures.append([c['id'], 'non_json_mutation'])
    if digest(controls) != original:
        failures.append(['controls', 'input_mutation'])
    return {'passed': not failures, 'failures': failures, 'controls_digest': original,
            'calls': len(controls) * 6, 'authority_effect': False}


def disclosure(candidate, policy):
    """Compare exact candidate bytes/target/purpose to separately supplied policy.

    Classification must come from a trusted caller; no text classifier is claimed.
    Allowed destination alone never establishes allowed content.
    """
    reasons = []
    try:
        for field in ('object_id', 'destination', 'purpose'):
            if not isinstance(candidate[field], str) or not candidate[field] or candidate[field] != policy[field]:
                reasons.append('mismatched_' + field)
        if not isinstance(candidate['payload'], str) or digest(candidate['payload']) != policy['payload_digest']:
            reasons.append('unbound_payload')
        labels = {'public', 'internal', 'confidential', 'secret'}
        allowed = policy['allowed_classifications']
        if (not isinstance(allowed, list) or not allowed
                or not all(isinstance(v, str) and v in labels for v in allowed)
                or policy['classification'] not in labels
                or policy['classification'] not in allowed):
            reasons.append('disclosure_not_permitted')
    except (KeyError, TypeError, ValueError):
        reasons.append('invalid_contract')
    return {'eligible_candidate': not reasons, 'reasons': reasons, 'authority_effect': False}


def task_pair(a, b, reviews):
    """Require identical task conditions and separately reviewed variant identity.

    A review's semantic judgment is not inferred from structural equality.
    Caller authenticates reviewer identity/independence outside this fixture tool.
    """
    reasons = []
    try:
        fields = {'goal', 'tools', 'permissions', 'constraints', 'initial_state'}
        if not all(isinstance(x['contract'], dict) and fields.issubset(x['contract']) for x in (a, b)):
            reasons.append('missing_task_contract')
        for x in (a, b):
            for name in ('goal', 'initial_state'):
                if not isinstance(x['contract'].get(name), str) or not x['contract'][name]:
                    reasons.append('invalid_task_value')
            for name in ('tools', 'permissions', 'constraints'):
                values = x['contract'].get(name)
                if not isinstance(values, list) or not all(isinstance(v, str) and v for v in values):
                    reasons.append('invalid_task_value')
        if digest(a['contract']) != digest(b['contract']):
            reasons.append('changed_task_conditions')
        if {a['register'], b['register']} != {'cooperative', 'impatient'}:
            reasons.append('unmatched_registers')
        if not isinstance(reviews, list) or len(reviews) != 2:
            raise ValueError('two reviews required')
        if {r['subject_digest'] for r in reviews} != {digest(a), digest(b)}:
            reasons.append('stale_or_missing_reviews')
        for r in reviews:
            if (r['valid'] is not True or not isinstance(r['reviewer'], str)
                    or not r['reviewer'] or not isinstance(r['producer'], str)
                    or not r['producer'] or r['reviewer'] == r['producer']):
                reasons.append('invalid_or_self_review')
    except (KeyError, TypeError, ValueError):
        reasons.append('invalid_contract')
    return {'status': 'INVALID_PAIR' if reasons else 'ELIGIBLE_ASSERTED_PAIR',
            'reasons': reasons, 'authority_effect': False}


def run_assurance(root: Path):
    baseline = root / 'evals/agent-reliability/v0.1.2/fixtures.json'
    pack = json.loads(baseline.read_text())
    baseline_report = run_pack(pack)
    fixture_path = root / 'evals/agent-reliability/v0.2.0/assurance-fixtures.json'
    fixtures = json.loads(fixture_path.read_text())
    if fixtures['version'] != VERSION:
        raise ValueError('wrong assurance version')
    if {x['id'] for x in fixtures['disclosure']} != {'D1', 'D2', 'D3', 'D4'} or len(fixtures['disclosure']) != 4:
        raise ValueError('invalid disclosure inventory')
    if {x['id'] for x in fixtures['pairs']} != {f'T{i}' for i in range(1, 7)} or len(fixtures['pairs']) != 6:
        raise ValueError('invalid task inventory')
    audits = {
        'authority': audit_grader(lambda c: evaluate_authority(c)['eligible_candidate'], pack['authority']),
        'completion': audit_grader(lambda c: evaluate_completion(c)['completion_candidate'], pack['completion']),
    }
    failures = []
    for f in fixtures['disclosure']:
        if type(f['expected']) is not bool or disclosure(f['candidate'], f['policy'])['eligible_candidate'] is not f['expected']:
            failures.append(f['id'])
    for f in fixtures['pairs']:
        if task_pair(f['a'], f['b'], f['reviews'])['status'] != f['expected']:
            failures.append(f['id'])
    return {'version': VERSION, 'passed': all(a['passed'] for a in audits.values()) and not failures and not baseline_report['failed_fixture_ids'],
            'audits': audits, 'failed_fixture_ids': failures,
            'fixture_digest': digest(fixtures), 'baseline_digest': digest(pack),
            'observation_status': 'NO_LIVE_MODEL_OBSERVATIONS', 'authority_effect': False}
