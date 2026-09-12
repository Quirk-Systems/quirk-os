"""Strict local envelopes around the existing candidate action boundary.

These are MCP-like and A2A-like input adapters, not network servers or claims of
protocol compliance. Their explicit Quirk versions prevent ordinary protocol
messages from being mistaken for a supported authority-bearing contract. Only
host code supplies the ActionExecutor and its trusted registry; envelope data can
neither install a grant nor replace the executor's resource/argument checks.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .actions import ActionExecutor, digest_json


@lru_cache(maxsize=1)
def _action_validator() -> Draft202012Validator:
    path = Path(__file__).resolve().parents[2] / 'schemas' / 'action-contract.v1.schema.json'
    return Draft202012Validator(json.loads(path.read_text(encoding='utf-8')), format_checker=FormatChecker())


def _object(value: Any, keys: set[str], label: str) -> dict:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f'{label} must be an object with exactly these keys: {sorted(keys)}')
    return value


def _json_envelope(envelope: Any) -> None:
    try:
        digest_json(envelope)
    except (TypeError, ValueError, RecursionError) as exc:
        raise ValueError('local envelope must contain finite JSON values') from exc


def _dispatch(action: Any, executor: ActionExecutor, *, now: str) -> dict:
    if type(executor) is not ActionExecutor:
        raise ValueError('local envelope requires the host-provided ActionExecutor')
    errors = list(_action_validator().iter_errors(action))
    if errors:
        # The canonical closed schema forbids embedded grants/auth overrides,
        # live publication verbs, and any implicit target/argument defaults.
        raise ValueError(f'invalid local action contract: {errors[0].message}')
    return executor.execute(action, now=now)


def execute_mcp_candidate(envelope: Any, executor: ActionExecutor, *, now: str) -> dict:
    """Execute a quirk-mcp-action/v1 tools/call envelope or raise ValueError.

    Exact shape: {schema_version, method: "tools/call", params: {
        name: "quirk_prepare_candidate", arguments: <action-contract/v1>}}.
    The named local tool supports the contract's two candidate operations.
    Authorization rejection remains an ordinary ActionExecutor receipt.
    """
    _json_envelope(envelope)
    envelope = _object(envelope, {'schema_version', 'method', 'params'}, 'MCP-like envelope')
    if envelope['schema_version'] != 'quirk-mcp-action/v1' or envelope['method'] != 'tools/call':
        raise ValueError('unsupported local MCP-like envelope version or method')
    params = _object(envelope['params'], {'name', 'arguments'}, 'MCP-like params')
    if params['name'] != 'quirk_prepare_candidate':
        raise ValueError('unsupported local MCP-like tool name')
    return _dispatch(params['arguments'], executor, now=now)


def execute_a2a_candidate(envelope: Any, executor: ActionExecutor, *, now: str) -> dict:
    """Execute a quirk-a2a-action/v1 single-data-part envelope or raise ValueError.

    Exact shape: {schema_version, message: {role: "user", parts: [
        {kind: "data", data: <action-contract/v1>}]}}.
    Message roles are transport labels and convey no grant authority.
    """
    _json_envelope(envelope)
    envelope = _object(envelope, {'schema_version', 'message'}, 'A2A-like envelope')
    if envelope['schema_version'] != 'quirk-a2a-action/v1':
        raise ValueError('unsupported local A2A-like envelope version')
    message = _object(envelope['message'], {'role', 'parts'}, 'A2A-like message')
    if message['role'] != 'user':
        raise ValueError('unsupported local A2A-like message role')
    parts = message['parts']
    if not isinstance(parts, list) or len(parts) != 1:
        raise ValueError('local A2A-like message requires exactly one data part')
    part = _object(parts[0], {'kind', 'data'}, 'A2A-like data part')
    if part['kind'] != 'data':
        raise ValueError('local A2A-like message requires a data part')
    return _dispatch(part['data'], executor, now=now)
