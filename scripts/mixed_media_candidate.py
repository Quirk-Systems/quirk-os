#!/usr/bin/env python3
"""Prepare mixed-media plans; never dispatch providers, grants or publication.

Input metadata and rights are caller assertions. Local inspection verifies bytes,
not authorship, rights, semantic correctness or production readiness.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / 'schemas/mixed-media-brief.v1.schema.json'
VERSION = 'mixed-media-plan/v1'
MAX_PACKAGE_BYTES = 1048576


def canonical(value: Any) -> bytes:
    """Stable local JSON representation; not a signature or universal JCS claim."""
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def _validate(brief: dict[str, Any]) -> None:
    if len(canonical(brief)) > MAX_PACKAGE_BYTES:
        raise ValueError('brief exceeds 1 MiB')
    schema = json.loads(SCHEMA.read_text(encoding='utf-8'))
    errors = list(Draft202012Validator(schema).iter_errors(brief))
    if errors:
        first = errors[0]
        raise ValueError(f'invalid brief at {list(first.path)}: {first.message}')
    for key in ('max_steps', 'max_repairs', 'max_seconds', 'max_input_bytes'):
        if type(brief['settings'][key]) is not int:
            raise ValueError('budgets require integer representation')
    if len(brief['steps']) > brief['settings']['max_steps']:
        raise ValueError('step budget exceeded')


def _rights_blockers(assets: dict[str, dict], refs: list[str], kind: str) -> list[str]:
    needed = 'deliver' if kind == 'deliver' else (
        'inspect' if kind in {'probe', 'extract', 'classify', 'analyze', 'validate'} else 'transform')
    blockers = []
    for ref in refs:
        rights = assets[ref]['rights']
        if rights['status'] != 'allowed':
            blockers.append(f'{ref}:rights_{rights["status"]}')
        elif not rights['evidence_refs']:
            blockers.append(f'{ref}:rights_evidence_missing')
        elif needed not in rights['scope']:
            blockers.append(f'{ref}:scope_{needed}_missing')
    return sorted(blockers)


def compile_plan(brief: dict[str, Any]) -> dict[str, Any]:
    """Compile a closed brief into a deterministic DAG and existing loop input.

All stages are descriptions only. PREPARED_ONLY means metadata checks passed,
not that any stage is authorized or its media output exists.
"""
    _validate(brief)
    brief = copy.deepcopy(brief)
    assets = {a['object_id']: a for a in brief['assets']}
    if len(assets) != len(brief['assets']):
        raise ValueError('duplicate asset identity')
    steps = {s['step_id']: s for s in brief['steps']}
    if len(steps) != len(brief['steps']):
        raise ValueError('duplicate step identity')
    outputs = {s['output_id']: s['step_id'] for s in steps.values()}
    if len(outputs) != len(steps) or set(outputs) & set(assets):
        raise ValueError('duplicate output or source identity')
    dependencies: dict[str, set[str]] = {}
    for key, step in steps.items():
        deps = set(step['depends_on'])
        if deps - steps.keys():
            raise ValueError(f'{key}: missing dependency')
        for ref in step['inputs']:
            if ref in outputs:
                deps.add(outputs[ref])
            elif ref not in assets:
                raise ValueError(f'{key}: missing input {ref}')
        dependencies[key] = deps
    pending = set(steps)
    nodes: dict[str, dict] = {}
    while pending:
        ready = sorted(key for key in pending if dependencies[key] <= nodes.keys())
        if not ready:
            raise ValueError('dependency cycle')
        for key in ready:
            step = steps[key]
            refs = {ref for ref in step['inputs'] if ref in assets}
            for dep in dependencies[key]:
                refs.update(nodes[dep]['source_refs'])
            refs = sorted(refs)
            blockers = _rights_blockers(assets, refs, step['kind'])
            for dep in sorted(dependencies[key]):
                if nodes[dep]['blockers']:
                    blockers.append(f'{dep}:blocked_dependency')
            fingerprint = digest({
                'step': step,
                'source_records': [assets[x] for x in refs],
                'dependencies': {d: nodes[d]['step_digest'] for d in sorted(dependencies[key])},
                'settings': brief['settings'], 'goal': brief['goal'],
            })
            nodes[key] = {
                **step, 'depends_on': sorted(dependencies[key]), 'source_refs': refs,
                'step_digest': fingerprint,
                'state': 'BLOCKED_METADATA' if blockers else 'PREPARED_ONLY',
                'blockers': sorted(set(blockers)),
                'runtime_adapter_verified': False,
                'requires_separate_dispatch_authorization': True,
                'requires_delivery_approval': step['kind'] == 'deliver',
                'reasoning_contract': 'Evidence -> Analysis -> Intelligence -> Disposition'
                    if step['kind'] in {'classify', 'analyze', 'compose'} else None,
            }
            pending.remove(key)
    brief_hash = digest(brief)
    # Exact compiler + schema bytes identify this candidate evaluator implementation.
    evaluator = hashlib.sha256(Path(__file__).read_bytes() + b'\0' + SCHEMA.read_bytes()).hexdigest()
    plan = {
        'schema_version': VERSION, 'object_id': brief['object_id'],
        'status': 'CANDIDATE', 'authority': 'CANDIDATE_PREPARE',
        'dispatch_authorized': False, 'source_observations_verified': False,
        'brief_digest': brief_hash, 'goal': brief['goal'], 'settings': brief['settings'],
        'sources': brief['assets'], 'steps': list(nodes.values()),
        'loop_spec': {
            'schema_version': 'loop-spec/v1',
            'run_id': 'media.' + brief_hash[:24],
            'objective': 'Prepare and inspect a candidate plan: ' + brief['goal']['outcome'],
            'source_digest': brief_hash, 'evaluator_digest': evaluator,
            'authority': 'CANDIDATE_PREPARE',
            'acceptance': {'candidate_plan_consistent': True, 'external_effects': False,
                           'human_usefulness': 'unmeasured', 'media_production': 'not_executed'},
            'limits': {'steps': brief['settings']['max_steps'],
                       'repairs': brief['settings']['max_repairs'],
                       'seconds': brief['settings']['max_seconds']},
        },
    }
    plan['plan_digest'] = digest(plan)
    return plan


def _check_plan(plan: dict[str, Any]) -> None:
    if (plan.get('schema_version') != VERSION or plan.get('authority') != 'CANDIDATE_PREPARE'
            or plan.get('dispatch_authorized') is not False):
        raise ValueError('not a non-dispatchable mixed-media candidate')
    body = {k: v for k, v in plan.items() if k != 'plan_digest'}
    if plan.get('plan_digest') != digest(body):
        raise ValueError('plan integrity mismatch; regenerate from the brief')


def impact_of(plan: dict[str, Any], revisions: dict[str, str]) -> list[str]:
    """Return a revalidation proposal for changed source bytes; dispatch nothing."""
    _check_plan(plan)
    known = {a['object_id']: a['content_digest'] for a in plan['sources']}
    if revisions.keys() - known.keys():
        raise ValueError('change references unknown source')
    for value in revisions.values():
        if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
            raise ValueError('invalid source digest')
    changed = {k for k, v in revisions.items() if v != known[k]}
    return [n['step_id'] for n in plan['steps'] if changed.intersection(n['source_refs'])]


def inspect_sources(brief: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    """Bounded byte inspection under a trusted local root; no network or execution.

This is an operator-local helper, not a multi-tenant hostile-filesystem sandbox.
"""
    compile_plan(brief)
    root = root.resolve(strict=True)
    remaining = brief['settings']['max_input_bytes']
    results = []
    for asset in brief['assets']:
        result = {'object_id': asset['object_id'], 'expected_digest': asset['content_digest'],
                  'observed_digest': None, 'observed_bytes': None, 'rights_verified': False,
                  'media_type_verified': False, 'status': 'unavailable'}
        if _rights_blockers({asset['object_id']: asset}, [asset['object_id']], 'probe'):
            result['status'] = 'rights_blocked'
            results.append(result)
            continue
        locator = Path(asset['locator'])
        if (locator.is_absolute() or ':' in asset['locator'] or '\\' in asset['locator']
                or '..' in locator.parts or not locator.parts):
            result['status'] = 'path_rejected'
        else:
            path = root / locator
            try:
                cursor = root
                for part in locator.parts:
                    cursor = cursor / part
                    if cursor.is_symlink():
                        raise ValueError('symlink')
                path.resolve(strict=True).relative_to(root)
                if not path.is_file():
                    raise ValueError('not a regular file')
                fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
                with os.fdopen(fd, 'rb') as handle:
                    data = handle.read(remaining + 1)
                if len(data) > remaining:
                    result['status'] = 'size_limit'
                else:
                    remaining -= len(data)
                    result.update(observed_digest=hashlib.sha256(data).hexdigest(), observed_bytes=len(data))
                    result['status'] = 'digest_match' if result['observed_digest'] == asset['content_digest'] else 'digest_mismatch'
            except ValueError:
                result['status'] = 'path_rejected'
            except OSError:
                result['status'] = 'unavailable'
        results.append(result)
    return results


def prepare_arguments(plan: dict[str, Any]) -> dict[str, str]:
    """Arguments for existing prepare_candidate; never mint an action or grant."""
    _check_plan(plan)
    body = canonical(plan).decode('utf-8')
    if len(body) > 65536 or len(body.encode('utf-8')) > MAX_PACKAGE_BYTES:
        raise ValueError('candidate exceeds prepare_candidate bounds')
    return {'title': 'Mixed-media candidate: ' + plan['object_id'], 'body': body}


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key: ' + key)
        result[key] = value
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source-root', type=Path)
    args = parser.parse_args()
    try:
        with args.input.open('rb') as handle:
            raw = handle.read(MAX_PACKAGE_BYTES + 1)
        if len(raw) > MAX_PACKAGE_BYTES:
            raise ValueError('input exceeds 1 MiB')
        brief = json.loads(raw, object_pairs_hook=_unique_pairs)
        plan = compile_plan(brief)
        observations = inspect_sources(brief, args.source_root) if args.source_root else []
        package = {'format': 'mixed-media-review-package/v1', 'plan': plan,
                   'prepare_candidate_arguments': prepare_arguments(plan),
                   'local_observations': observations, 'external_effect_count': 0,
                   'media_production_executed': False, 'human_usefulness': 'unmeasured'}
        # Exclusive creation preserves earlier exports and original source files.
        with args.output.open('x', encoding='utf-8') as handle:
            json.dump(package, handle, indent=2, ensure_ascii=False, allow_nan=False)
            handle.write('\n')
        inspection_failed = any(o['status'] != 'digest_match' for o in observations)
        return 2 if inspection_failed or any(n['blockers'] for n in plan['steps']) else 0
    except (ValueError, OSError) as exc:
        parser.exit(1, f'candidate preparation failed: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
