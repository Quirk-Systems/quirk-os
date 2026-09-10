"""Host-scoped local candidate actions with observed, versioned receipts.

This reference boundary does not load or admit skills and has no live mutation
adapter. TrustedGrantRegistry is supplied by the host, never by proposal content.
Grant approval fields are references asserted by that trusted host; their presence
alone is not authentication and cannot turn a candidate skill into an admitted one.
"""
from __future__ import annotations
import copy
import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping
from jsonschema import Draft202012Validator, FormatChecker
from .ledger import ActionLedger


def digest_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest()


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


@lru_cache(maxsize=4)
def _validator(name: str):
    schema = json.loads((Path(__file__).resolve().parents[2] / 'schemas' / name).read_text())
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _schema_errors(value: Any, schema: str) -> list[str]:
    try:
        digest_json(value)  # Reject non-JSON values and NaN before doing anything.
        return [f'{schema}: {e.message}' for e in _validator(schema).iter_errors(value)]
    except (TypeError, ValueError, RecursionError) as exc:
        return [f'invalid JSON contract: {exc}']


def _instant(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('timestamp must include timezone')
    return result.astimezone(timezone.utc)


def validate_action(action, grant, *, now: str, current_target_digest: str | None,
                    revoked_grant_ids=()) -> list[str]:
    errors = _schema_errors(action, 'action-contract.v1.schema.json')
    errors += _schema_errors(grant, 'action-grant.v1.schema.json')
    if errors:
        return errors
    runtime = grant['runtime_grant']
    for field in ('grant_id', 'skill_id', 'skill_version', 'skill_manifest_sha256'):
        if action[field] != runtime[field]:
            errors.append(f'grant {field} mismatch')
    if runtime['requested_by'] == runtime['approved_by']:
        errors.append('runtime grant requester and approver must be distinct')
    if action['grant_id'] in revoked_grant_ids:
        errors.append('grant is revoked')
    if action['operation'] not in runtime['allowed_actions']:
        errors.append('operation is outside grant scope')
    if action['operation'] == 'prepare_candidate' and runtime['authority_ceiling'] not in ('propose', 'execute_bounded'):
        errors.append('prepare_candidate requires at least propose ceiling')
    for field in ('target', 'target_sha256', 'arguments_sha256'):
        if action[field] != grant[field]:
            errors.append(f'grant {field} mismatch')
    if action['arguments_sha256'] != digest_json(action['arguments']):
        errors.append('canonical arguments digest mismatch')
    if action['target_sha256'] != current_target_digest:
        errors.append('current target digest mismatch')
    for field, limit in action['effect_limit'].items():
        if limit > grant['effect_limit'][field]:
            errors.append(f'effect limit {field} exceeds grant')
    try:
        instant, issued, expires = _instant(now), _instant(runtime['issued_at']), _instant(runtime['expires_at'])
        if not issued <= instant < expires:
            errors.append('grant is expired or not yet valid')
    except (ValueError, TypeError, AttributeError):
        errors.append('invalid current time')
    return errors


class TrustedGrantRegistry:
    """Host configuration, not an authorization parser for untrusted content."""
    def __init__(self, grants: Mapping[str, dict]):
        self._grants = copy.deepcopy(dict(grants))
        for key, grant in self._grants.items():
            errors = _schema_errors(grant, 'action-grant.v1.schema.json')
            if errors or key != grant['runtime_grant']['grant_id']:
                raise ValueError(f'invalid trusted grant {key}: {errors}')

    def get(self, grant_id: str) -> dict | None:
        return copy.deepcopy(self._grants.get(grant_id))

    def revoke(self, grant_id: str) -> None:
        self._grants.pop(grant_id, None)


class LocalAdapter:
    """Only bounded reads and returned candidate data; no filesystem/network writes."""
    def __init__(self, resources: Mapping[str, str]):
        if not all(isinstance(k, str) and isinstance(v, str) for k, v in resources.items()):
            raise ValueError('local resources must map names to text')
        self.resources = dict(resources)

    def current_digest(self, target: str) -> str | None:
        text = self.resources.get(target)
        return digest_text(text) if text is not None else None

    def observe(self, action: dict) -> tuple[dict, list[dict]]:
        content = self.resources[action['target']]
        before = digest_text(content)
        if before != action['target_sha256']:
            raise ValueError('target changed at dispatch')
        if len(content.encode('utf-8')) > action['effect_limit']['max_bytes']:
            raise ValueError('resource exceeds byte limit')
        if action['operation'] == 'read_resource':
            output = {'target': action['target'], 'content': content, 'content_sha256': before}
        elif action['operation'] == 'prepare_candidate':
            output = {'target': action['target'], 'source_sha256': before,
                      'candidate': copy.deepcopy(action['arguments'])}
        else:
            raise ValueError('unsupported operation')
        if len(json.dumps(output, ensure_ascii=False).encode('utf-8')) > action['effect_limit']['max_bytes']:
            raise ValueError('output exceeds byte limit')
        after = self.current_digest(action['target'])
        if before != after:
            raise ValueError('target changed during observation')
        return output, [{'observer': 'local-adapter/v1', 'target': action['target'],
            'before_sha256': before, 'after_sha256': after,
            'output_sha256': digest_json(output), 'operation': action['operation'],
            'resources_observed': 1, 'external_writes': 0, 'spend': 0}]

    def reconcile(self, action: dict) -> None:
        # Source state cannot prove whether a prior read/prepare completed. Never
        # rerun an uncertain operation or turn deterministic reconstruction into proof.
        return None


class ActionExecutor:
    def __init__(self, ledger: ActionLedger, registry: TrustedGrantRegistry, adapter: LocalAdapter):
        if type(adapter) is not LocalAdapter or type(registry) is not TrustedGrantRegistry:
            raise TypeError('only the trusted registry and built-in local adapter are supported')
        self.ledger, self.registry, self.adapter = ledger, registry, adapter

    def _result(self, action, status, *, errors=(), output=None, evidence=(), replayed=False):
        action = action if isinstance(action, dict) else {}
        try:
            action_sha256 = digest_json(action)
        except (ValueError, TypeError, RecursionError):
            action_sha256 = None
        identity = {field: action.get(field) if isinstance(action.get(field), str) else None
            for field in ('grant_id', 'skill_id', 'skill_version', 'skill_manifest_sha256')}
        return {'schema_version': 'action-receipt/v2',
            **identity, 'action_sha256': action_sha256,
            'action_id': action.get('action_id') if isinstance(action.get('action_id'), str) else None,
            'idempotency_key': action.get('idempotency_key') if isinstance(action.get('idempotency_key'), str) else None,
            'status': status, 'errors': list(errors), 'output': output, 'evidence': list(evidence),
            'replayed': replayed, 'no_authority_escalation': True if status == 'VERIFIED' else None,
            'immutable': None, 'limitations': [
                'Local candidate boundary only; no skill admission or live authority established.',
                'SQLite append-only triggers do not enforce immutability against its owner.',
                'Human usefulness is unmeasured.']}

    def _check(self, action, now, revoked):
        errors, _ = self._checked_grant(action, now, revoked)
        return errors

    def _checked_grant(self, action, now, revoked):
        """Return the exact host snapshot validated by this decision."""
        errors = _schema_errors(action, 'action-contract.v1.schema.json')
        if errors:
            return errors, None
        grant = self.registry.get(action['grant_id'])
        if grant is None:
            return ['grant is absent from trusted host registry'], None
        errors = validate_action(action, grant, now=now,
            current_target_digest=self.adapter.current_digest(action['target']), revoked_grant_ids=revoked)
        return errors, grant

    def execute(self, action, *, now: str, revoked_grant_ids=()) -> dict:
        entered_at = time.monotonic()
        # Snapshot proposal data so caller mutation cannot change a checked action.
        action = copy.deepcopy(action)
        errors = self._check(action, now, revoked_grant_ids)
        if errors:
            return self._result(action, 'REJECTED', errors=errors)
        created, previous = self.ledger.record_intent(action)
        if previous['action_digest'] != digest_json(action):
            return self._result(action, 'REJECTED', errors=['idempotency key is bound to a different action'])
        dispatch_at = (_instant(now) + timedelta(seconds=max(0, time.monotonic() - entered_at))).isoformat()
        errors = self._check(action, dispatch_at, revoked_grant_ids)
        if errors:
            result = self._result(action, 'REJECTED', errors=errors)
            if created:
                return self.ledger.record_outcome(action['idempotency_key'], result)
            return result
        if not created:
            if previous['outcome'] is not None:
                return {**previous['outcome'], 'replayed': True}
            self.adapter.reconcile(action)
            result = self._result(action, 'UNCERTAIN', errors=[
                'prior intent has no durable outcome; reconciliation cannot establish completion'], replayed=True)
            return self.ledger.record_outcome(action['idempotency_key'], result)
        # Re-read trusted grant and source immediately before the bounded operation.
        dispatch_at = (_instant(now) + timedelta(seconds=max(0, time.monotonic() - entered_at))).isoformat()
        errors, dispatch_grant = self._checked_grant(action, dispatch_at, revoked_grant_ids)
        if errors:
            result = self._result(action, 'REJECTED', errors=errors)
        else:
            start = time.monotonic()
            try:
                output, evidence = self.adapter.observe(action)
                self._verify(action, output, evidence)
                if time.monotonic() - start > action['recovery']['timeout_seconds']:
                    raise TimeoutError('local action exceeded observation timeout')
                for observation in evidence:
                    observation['observed_at'] = dispatch_at
                    observation['verifier'] = 'local-postcondition/v1'
                    observation['grant_sha256'] = digest_json(dispatch_grant)
                result = self._result(action, 'VERIFIED', output=output, evidence=evidence)
            except Exception as exc:
                result = self._result(action, 'UNCERTAIN', errors=[f'no verified outcome: {type(exc).__name__}: {exc}'])
        return self.ledger.record_outcome(action['idempotency_key'], result)

    def _verify(self, action: dict, output: dict, evidence: list[dict]) -> None:
        """Check the concrete postcondition instead of accepting a success flag."""
        expected = action['target_sha256']
        if self.adapter.current_digest(action['target']) != expected or output.get('target') != action['target']:
            raise ValueError('postcondition target mismatch')
        if action['operation'] == 'read_resource':
            if digest_text(output['content']) != expected or output.get('content_sha256') != expected:
                raise ValueError('read postcondition digest mismatch')
        elif output.get('source_sha256') != expected or output.get('candidate') != action['arguments']:
            raise ValueError('prepared candidate postcondition mismatch')
        if len(evidence) != 1:
            raise ValueError('missing bounded observation evidence')
        observation = evidence[0]
        required = {'observer': 'local-adapter/v1', 'target': action['target'],
            'before_sha256': expected, 'after_sha256': expected, 'output_sha256': digest_json(output),
            'operation': action['operation'], 'resources_observed': 1, 'external_writes': 0, 'spend': 0}
        if observation != required:
            raise ValueError('observation does not match verified local effects')
