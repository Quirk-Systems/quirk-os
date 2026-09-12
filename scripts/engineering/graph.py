"""Bounded candidate evidence queries. Graph content never grants action authority.

The host supplies a current object/digest registry and authenticated visibility scope.
Records are observations supplied by that host, not verified external facts. This
snapshot checks binding and time applicability; it cannot authenticate an observer.
"""
from collections import deque
from copy import deepcopy
from datetime import datetime, timezone
from functools import lru_cache
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

KINDS = frozenset({'artifact', 'claim', 'evidence', 'run', 'action', 'judgment', 'principal', 'policy'})
PREDICATES = frozenset({'supported_by', 'contradicted_by', 'depends_on', 'blocked_by', 'produced', 'prefers'})
DEPENDENCIES = frozenset({'supported_by', 'contradicted_by', 'depends_on', 'blocked_by'})
MAX_RESULTS = 1000
MAX_DEPTH = 32


@lru_cache(maxsize=2)
def _validator(record_type):
    path = Path(__file__).resolve().parents[2] / 'schemas' / f'engineering-graph-{record_type}.v1.schema.json'
    return Draft202012Validator(json.loads(path.read_text()), format_checker=FormatChecker())


def _validate_record(record, record_type):
    try:
        json.dumps(record, allow_nan=False)
        _validator(record_type).validate(record)
    except (TypeError, ValueError, ValidationError) as exc:
        raise ValueError(f'invalid graph {record_type} record: {exc}') from exc


def _time(value):
    try:
        parsed = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace('Z', '+00:00'))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError('timezone required')
        return parsed.astimezone(timezone.utc)
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError('expected timezone-aware ISO8601 timestamp') from exc


def _nonempty(record, fields):
    for field in fields:
        if not isinstance(record.get(field), str) or not record[field].strip():
            raise ValueError(f'{field} must be a nonempty string')


class EvidenceGraph:
    """Immutable in-memory snapshot scoped by host-supplied tenant and principal.

    Each object_id has exactly one current digest. Historical assertion bindings
    stay in the snapshot and become stale when that current digest changes.
    Missing visible_to means tenant-visible; a restricted object needs a matching
    principal_id. Mixed-tenant snapshots require an explicit tenant_id.
    """
    def __init__(self, objects, assertions, *, tenant_id=None, principal_id=None):
        self._objects = {}
        for raw in objects:
            _validate_record(raw, 'object')
            item = deepcopy(raw)
            _nonempty(item, ('object_id', 'digest', 'kind', 'tenant_id'))
            if item['kind'] not in KINDS:
                raise ValueError('unknown object kind')
            if 'visible_to' in item and (not isinstance(item['visible_to'], list) or any(not isinstance(p, str) or not p for p in item['visible_to'])):
                raise ValueError('visible_to must be a list of principal IDs')
            if item['object_id'] in self._objects:
                raise ValueError('duplicate object identity')
            self._objects[item['object_id']] = item
        tenants = {o['tenant_id'] for o in self._objects.values()}
        if tenant_id is None and len(tenants) > 1:
            raise ValueError('mixed tenants require explicit tenant_id')
        self._tenant_id = tenant_id if tenant_id is not None else next(iter(tenants), None)
        self._principal_id = principal_id
        self._assertions = {}
        required = ('assertion_id', 'subject_id', 'subject_digest', 'predicate', 'object_id', 'object_digest', 'source_ref', 'source_digest', 'observer', 'observed_at', 'valid_from', 'status')
        for raw in assertions:
            _validate_record(raw, 'assertion')
            item = deepcopy(raw)
            _nonempty(item, required)
            if 'valid_until' not in item:
                raise ValueError('valid_until is required (null means no expiry)')
            if item['assertion_id'] in self._assertions:
                raise ValueError('duplicate assertion identity')
            if item['predicate'] not in PREDICATES:
                raise ValueError('unknown relationship; graph cannot grant authority')
            if item['status'] not in {'observed', 'declared', 'retracted'}:
                raise ValueError('unknown assertion status')
            ids = [item[k] for k in ('subject_id', 'object_id', 'source_ref')]
            if any(key not in self._objects for key in ids):
                raise ValueError('all endpoints and source_ref must be registered objects')
            if len({self._objects[key]['tenant_id'] for key in ids}) != 1:
                raise ValueError('cross-tenant assertions are forbidden')
            subject = self._objects[item['subject_id']]
            if item['predicate'] == 'produced' and subject['kind'] not in {'run', 'action'}:
                raise ValueError('produced requires run or action subject')
            if item['predicate'] == 'prefers' and subject['kind'] not in {'judgment', 'principal'}:
                raise ValueError('prefers requires judgment or principal subject')
            observed = _time(item['observed_at'])
            valid = _time(item['valid_from'])
            if item['valid_until'] is not None and _time(item['valid_until']) <= valid:
                raise ValueError('valid_until must be after valid_from')
            if 'recorded_at' in item and _time(item['recorded_at']) < observed:
                raise ValueError('recorded_at cannot precede observed_at')
            self._assertions[item['assertion_id']] = item
        self._superseding = {}
        for item in self._assertions.values():
            previous = item.get('supersedes')
            if previous is None:
                continue
            if previous not in self._assertions or previous == item['assertion_id']:
                raise ValueError('supersedes must reference a different known assertion')
            prior = self._assertions[previous]
            if any(prior[k] != item[k] for k in ('subject_id', 'predicate', 'object_id', 'observer')):
                raise ValueError('supersession must keep endpoints, predicate and observer')
            if _time(item['observed_at']) < _time(prior['observed_at']):
                raise ValueError('supersession cannot precede prior observation')
            self._superseding.setdefault(previous, []).append(item)
        for item in self._assertions.values():
            seen = set()
            while item.get('supersedes') is not None:
                if item['assertion_id'] in seen:
                    raise ValueError('supersession cycle')
                seen.add(item['assertion_id'])
                item = self._assertions[item['supersedes']]

    def _visible_object(self, object_id):
        item = self._objects.get(object_id)
        return bool(item and item['tenant_id'] == self._tenant_id and ('visible_to' not in item or self._principal_id in item['visible_to']))

    def _visible(self, assertion):
        return all(self._visible_object(assertion[key]) for key in ('subject_id', 'object_id', 'source_ref'))

    def _reasons(self, item, digest, now):
        reasons = []
        if item['subject_digest'] != digest or item['subject_digest'] != self._objects[item['subject_id']]['digest']:
            reasons.append('subject_digest_mismatch')
        if item['object_digest'] != self._objects[item['object_id']]['digest']:
            reasons.append('object_digest_mismatch')
        if item['source_digest'] != self._objects[item['source_ref']]['digest']:
            reasons.append('source_digest_mismatch')
        if item['status'] != 'observed':
            reasons.append('status_' + item['status'])
        if _time(item['observed_at']) > now:
            reasons.append('not_yet_observed')
        if _time(item.get('recorded_at', item['observed_at'])) > now:
            reasons.append('not_yet_recorded')
        if _time(item['valid_from']) > now:
            reasons.append('not_yet_valid')
        if item['valid_until'] is not None and _time(item['valid_until']) <= now:
            reasons.append('expired')
        # Supersession is historical and permanent once a visible, host-observed
        # replacement is learned and effective. It does not resurrect expired old evidence.
        if any(self._visible(new) and new['status'] in {'observed', 'retracted'} and _time(new['observed_at']) <= now and _time(new['valid_from']) <= now and _time(new.get('recorded_at', new['observed_at'])) <= now for new in self._superseding.get(item['assertion_id'], [])):
            reasons.append('superseded')
        return reasons

    def support_for(self, object_id, digest, *, now):
        now = _time(now)
        result = dict(object_id=object_id, digest=digest, supports=[], contradictions=[], excluded=[], truncated=False, authorization='not_evaluated')
        count = 0
        for item in sorted(self._assertions.values(), key=lambda a: a['assertion_id']):
            if item['subject_id'] != object_id or item['predicate'] not in {'supported_by', 'contradicted_by'} or not self._visible(item):
                continue
            if count == MAX_RESULTS:
                result['truncated'] = True
                break
            count += 1
            reasons = self._reasons(item, digest, now)
            if reasons:
                result['excluded'].append(dict(assertion_id=item['assertion_id'], reasons=reasons))
            else:
                key = 'supports' if item['predicate'] == 'supported_by' else 'contradictions'
                result[key].append(deepcopy(item))
        return result

    def impact_of(self, object_id, *, max_depth=8):
        if type(max_depth) is not int or not 0 <= max_depth <= MAX_DEPTH:
            raise ValueError(f'max_depth must be between 0 and {MAX_DEPTH}')
        result = dict(object_id=object_id, affected=[], truncated=False, authorization='not_evaluated')
        if not self._visible_object(object_id):
            return result
        reverse = {}
        for item in sorted(self._assertions.values(), key=lambda a: a['assertion_id']):
            if item['predicate'] not in DEPENDENCIES or not self._visible(item):
                continue
            # A change to the cited source can invalidate a conclusion even when
            # the relationship's object is a separate evidence object.
            for dependency in {item['object_id'], item['source_ref']}:
                reverse.setdefault(dependency, []).append(item)
        queue, seen = deque([(object_id, 0)]), {object_id}
        while queue:
            current, depth = queue.popleft()
            for item in reverse.get(current, []):
                dependent = item['subject_id']
                if dependent in seen:
                    continue
                if depth >= max_depth or len(result['affected']) >= MAX_RESULTS:
                    result['truncated'] = True
                    continue
                seen.add(dependent)
                result['affected'].append(dict(object_id=dependent, digest=self._objects[dependent]['digest'], depth=depth+1, via_assertion_id=item['assertion_id']))
                queue.append((dependent, depth+1))
        return result

    def context_for(self, object_id, digest, *, now, max_items=20):
        if type(max_items) is not int or not 0 <= max_items <= MAX_RESULTS:
            raise ValueError(f'max_items must be between 0 and {MAX_RESULTS}')
        now = _time(now)
        result = dict(object_id=object_id, digest=digest, items=[], truncated=False, authorization='not_evaluated')
        # Contradictions and blockers precede convenient support in a tight budget.
        priority = {'contradicted_by': 0, 'blocked_by': 1, 'supported_by': 2, 'depends_on': 3, 'produced': 4, 'prefers': 5}
        for item in sorted(self._assertions.values(), key=lambda a: (priority[a['predicate']], a['assertion_id'])):
            if item['subject_id'] != object_id or not self._visible(item):
                continue
            if len(result['items']) == max_items:
                result['truncated'] = True
                break
            reasons = self._reasons(item, digest, now)
            result['items'].append(dict(assertion=deepcopy(item), applicable=not reasons, reasons=reasons))
        return result
