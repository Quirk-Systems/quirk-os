"""Prepare a private, unsigned Media Care review projection; never dispatch actions.

Consumes a saved media-care-check.v1 report, not media bytes or executable content.
Its integrity/rights/selection statements remain declarations. Caller-supplied
hash and visibility context bind this local capture; they do not authenticate it.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date, datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from jsonschema import Draft202012Validator, FormatChecker
from scripts.engineering.graph import EvidenceGraph

MAX_SOURCE = 1024 * 1024
MAX_ASSETS, MAX_FINDINGS, MAX_EDGES = 64, 128, 256
MAX_EXPORT_FILE = 8 * 1024 * 1024
AUTHORITY = {'ceiling': 'candidate', 'publish_allowed': False,
             'graph_application_allowed': False, 'training_allowed': False,
             'canon_promotion_allowed': False}
ROOT_KEYS = set('schema_version tool_version as_of kit_id kit_content_sha256 care_sha256 classification_sha256 integrity status authority human_benefit scope maintenance_owner owner_acceptance proposed_by selection assets findings art_direction'.split())
ASSET_KEYS = set('asset_ref title archive_path provenance_role family extension_family origin use_role sensitivity state state_reason review_on replacement_ref selected depends_on alt_text_presence companions'.split())
SELECTION_KEYS = set('asset_ref needs_attention review_refs actor_type signature_status'.split())
METHODS = {
    'owner_needed': ('owner_review', 'Record a nominated owner and their separate acceptance reference.'),
    'origin_unknown': ('provenance_review', 'Inspect exact source evidence; retain unknown origin when evidence is insufficient.'),
    'rights_review_open': ('rights_review', 'Record the intended use, supporting rights evidence, and a human review disposition; do not infer clearance.'),
    'accessibility_review_open': ('accessibility_review', 'Review the actual medium and required companions; record findings and human judgment, not presence alone.'),
}


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _object(value: Any, keys: set[str], label: str) -> dict:
    if type(value) is not dict or set(value) != keys:
        raise ValueError(f'{label}: missing or unsupported fields')
    return value


def _text(value: Any, label: str, maximum: int = 8192) -> str:
    if type(value) is not str or not value.strip() or len(value) > maximum:
        raise ValueError(f'{label}: bounded nonempty text required')
    return value


def _identity(value: Any, label: str) -> str:
    if type(value) is not str or re.fullmatch(r'[A-Za-z0-9._-]{1,120}', value) is None:
        raise ValueError(f'{label}: invalid identity')
    return value


def _hash(value: Any, label: str) -> str:
    if type(value) is not str or re.fullmatch(r'[a-f0-9]{64}', value) is None:
        raise ValueError(f'{label}: lowercase SHA-256 required')
    return value


def _array(value: Any, maximum: int, label: str) -> list:
    if type(value) is not list or len(value) > maximum:
        raise ValueError(f'{label}: bounded array required')
    return value


def _date(value: Any, label: str) -> date:
    if type(value) is not str or re.fullmatch(r'\d{4}-\d{2}-\d{2}', value) is None:
        raise ValueError(f'{label}: ISO date required')
    return date.fromisoformat(value)


def _capture(value: Any) -> datetime:
    _text(value, 'captured_at', 64)
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError('captured_at: timezone required')
    return parsed.astimezone(timezone.utc)


def _parse(raw: bytes) -> dict:
    if type(raw) is not bytes or len(raw) > MAX_SOURCE:
        raise ValueError('source: bytes within 1 MiB required')
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    def nonfinite(_):
        raise ValueError('nonfinite JSON is forbidden')
    try:
        value = json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)
        canonical(value)  # Also rejects overflow floats such as 1e999 and invalid Unicode.
    except (UnicodeError, RecursionError, json.JSONDecodeError) as exc:
        raise ValueError('source: invalid bounded JSON') from exc
    return _object(value, ROOT_KEYS, 'report')


def _validate(report: dict, capture: datetime) -> tuple[dict, set[str], bool]:
    if report['schema_version'] != 'media-care-check.v1' or report['tool_version'] != '0.2.0':
        raise ValueError('unsupported report protocol/version')
    if canonical(report['authority']) != canonical(AUTHORITY):
        raise ValueError('candidate authority restrictions must remain exact')
    if report['integrity'] != 'verified':
        raise ValueError('producer did not declare a successful inspection')
    # This prerequisite is not independent verification of the producer claim.
    for key in ('status', 'scope', 'maintenance_owner', 'owner_acceptance', 'proposed_by', 'human_benefit'):
        _text(report[key], key)
    _identity(report['kit_id'], 'kit_id')
    for key in ('kit_content_sha256', 'care_sha256', 'classification_sha256'):
        _hash(report[key], key)
    as_of = _date(report['as_of'], 'as_of')
    if as_of > capture.date():
        raise ValueError('source inspection date is after capture date')
    assets = {}
    edge_count = 0
    for asset in _array(report['assets'], MAX_ASSETS, 'assets'):
        _object(asset, ASSET_KEYS, 'asset')
        ref = _identity(asset['asset_ref'], 'asset_ref')
        if ref in assets:
            raise ValueError('duplicate asset reference')
        for key in ('title', 'archive_path', 'provenance_role', 'family', 'extension_family', 'origin', 'use_role', 'sensitivity', 'state', 'state_reason', 'alt_text_presence'):
            _text(asset[key], key)
        _date(asset['review_on'], 'review_on')
        if type(asset['selected']) is not bool or type(asset['companions']) is not dict:
            raise ValueError('invalid selected flag or companion mapping')
        if asset['replacement_ref'] is not None:
            _identity(asset['replacement_ref'], 'replacement_ref')
        deps = _array(asset['depends_on'], MAX_ASSETS, 'depends_on')
        for dep in deps:
            _identity(dep, 'dependency')
        if len(deps) != len(set(deps)):
            raise ValueError('duplicate dependency')
        edge_count += len(deps)
        assets[ref] = asset
    if not assets or edge_count > MAX_EDGES:
        raise ValueError('empty asset inventory or dependency budget exceeded')
    for asset in assets.values():
        if any(dep not in assets for dep in asset['depends_on']):
            raise ValueError('unresolved dependency')
    visiting, visited = set(), set()
    def walk(ref):
        if ref in visiting:
            raise ValueError('dependency cycle')
        if ref in visited:
            return
        visiting.add(ref)
        for dep in assets[ref]['depends_on']:
            walk(dep)
        visiting.remove(ref)
        visited.add(ref)
    for ref in assets:
        walk(ref)
    selection = _object(report['selection'], SELECTION_KEYS, 'selection')
    selected = _identity(selection['asset_ref'], 'selected asset')
    if selected not in assets or type(selection['needs_attention']) is not bool:
        raise ValueError('invalid selection')
    if [a['asset_ref'] for a in assets.values() if a['selected']] != [selected]:
        raise ValueError('selection flags do not match exactly one selected asset')
    for key in ('actor_type', 'signature_status'):
        _text(selection[key], key, 120)
    review_refs = _array(selection['review_refs'], MAX_ASSETS, 'review_refs')
    for ref in review_refs:
        _identity(ref, 'review reference')
    if len(review_refs) != len(set(review_refs)) or any(ref not in assets for ref in review_refs):
        raise ValueError('unresolved or duplicate review references')
    closure, pending = set(), [selected]
    while pending:
        ref = pending.pop()
        if ref not in closure:
            closure.add(ref)
            pending.extend(assets[ref]['depends_on'])
    if not closure.issubset(set(review_refs)):
        raise ValueError('selection review omitted a source dependency')
    findings_seen = set()
    for finding in _array(report['findings'], MAX_FINDINGS, 'findings'):
        _object(finding, {'code', 'asset_ref', 'message'}, 'finding')
        _identity(finding['code'], 'finding code')
        _text(finding['message'], 'finding message')
        ref = finding['asset_ref']
        if ref is not None and (type(ref) is not str or ref not in assets):
            raise ValueError('finding refers to an unknown asset')
        identity = (finding['code'], ref)
        if identity in findings_seen:
            raise ValueError('duplicate finding identity')
        findings_seen.add(identity)
    if type(report['art_direction']) is not dict:
        raise ValueError('art_direction must be a data object')
    return assets, set(review_refs), (capture.date() - as_of).days > 7


def prepare_report(raw: bytes, *, expected_sha256: str, tenant_id: str,
                   principal_id: str, captured_at: str) -> dict:
    """Map a bounded saved report to existing projection/graph contracts.

    Host context is explicit, not inferred from instructions in the report.
    Asset-view digests describe captured metadata, never the actual media bytes.
    """
    expected_sha256 = _hash(expected_sha256, 'expected_sha256')
    _identity(tenant_id, 'tenant_id'); _identity(principal_id, 'principal_id')
    capture = _capture(captured_at)
    report = _parse(raw)
    if sha256(raw) != expected_sha256:
        raise ValueError('source bytes differ from caller expectation')
    assets, review_refs, stale = _validate(report, capture)
    captured_at = capture.isoformat()
    prefix = 'media-review.' + expected_sha256
    source_ref = prefix + '.source'
    objects = [{'object_id': source_ref, 'digest': expected_sha256, 'kind': 'evidence',
                'tenant_id': tenant_id, 'visible_to': [principal_id]}]
    assertions, tasks, views = [], [], {}
    def node(oid, value, kind='claim'):
        objects.append({'object_id': oid, 'digest': sha256(canonical(value)), 'kind': kind,
                        'tenant_id': tenant_id, 'visible_to': [principal_id]})
        return oid
    def edge(subject, target, predicate):
        digests = {o['object_id']: o['digest'] for o in objects}
        assertions.append({'assertion_id': prefix+'.edge.'+str(len(assertions)),
            'subject_id': subject, 'subject_digest': digests[subject], 'predicate': predicate,
            'object_id': target, 'object_digest': digests[target],
            'source_ref': source_ref, 'source_digest': expected_sha256,
            'observer': 'media-care-handoff/v1', 'observed_at': captured_at,
            'valid_from': captured_at, 'valid_until': None, 'status': 'declared'})
    for ref, asset in sorted(assets.items()):
        views[ref] = node(prefix+'.metadata.'+ref, asset)
    for ref, asset in sorted(assets.items()):
        edge(views[ref], source_ref, 'supported_by')
        for dep in sorted(asset['depends_on']):
            edge(views[ref], views[dep], 'depends_on')
    ordered = sorted(enumerate(report['findings']), key=lambda pair: (
        0 if pair[1]['asset_ref'] is None else 1 if pair[1]['asset_ref'] in review_refs else 2, pair[0]))
    for _, finding in ordered:
        method, finish = METHODS.get(finding['code'], ('manual_review', 'Inspect the retained finding, record supporting evidence and a human disposition; do not infer completion.'))
        task_id = prefix+'.task.'+sha256(canonical(finding))[:20]
        task = {'task_id': task_id, 'state': 'proposed', 'owner_ref': None,
                'finding': deepcopy(finding), 'review_method': method, 'finish_condition': finish,
                'selection_relevant': finding['asset_ref'] is None or finding['asset_ref'] in review_refs,
                'authorization': 'none'}
        tasks.append(task)
        node(task_id, task, 'artifact')
        edge(task_id, source_ref, 'supported_by')
        if finding['asset_ref'] is not None:
            edge(task_id, views[finding['asset_ref']], 'depends_on')
    graph = EvidenceGraph(objects, assertions, tenant_id=tenant_id, principal_id=principal_id)
    holds = ['SOURCE_DECLARATIONS_UNVERIFIED', 'HUMAN_USEFULNESS_UNOBSERVED', 'NO_EXTERNAL_EXECUTION_AUTHORITY']
    if stale:
        holds.append('SOURCE_REVALIDATION_REQUIRED')
    projection = {'schema_version': 'media-review-handoff.v1', 'state': 'candidate',
        'goal': 'Resume a selected media review without reconstructing its sources, alternatives, or open care findings.',
        'authority': deepcopy(AUTHORITY), 'source_ref': source_ref, 'source_report_sha256': expected_sha256,
        'source_schema': report['schema_version'], 'source_as_of': report['as_of'],
        'kit_id': report['kit_id'], 'kit_content_sha256_declared': report['kit_content_sha256'],
        'producer_integrity_claim': report['integrity'], 'producer_claims_independently_verified': False,
        'selection': deepcopy(report['selection']), 'findings': deepcopy(report['findings']),
        'art_direction': deepcopy(report['art_direction']), 'asset_metadata_views': views,
        'tasks': tasks, 'graph': {'objects': objects, 'assertions': assertions},
        'source_change_impact': graph.impact_of(source_ref, max_depth=8),
        'snapshot_stale': stale, 'freshness': 'not_revalidated', 'holds': holds,
        'intelligence': {'kind': 'candidate_recommendation', 'next_task_id': tasks[0]['task_id'] if tasks else None,
                         'basis': 'Global findings, then selected-version dependency scope, then retained alternatives; not a quality score.'},
        'disposition': {'review': 'human_review_required', 'authorized_actions': [], 'admission_effect': 'none'},
        'suggested_work_in_progress': 1, 'external_writes': 0, 'measured_human_benefit': None}
    result = {'schema_version': 'projection-envelope.v1', 'object_key': prefix, 'kind': 'media_review_handoff',
        'canonical_uri': None, 'canonical_version': None, 'content_hash': sha256(canonical(projection)),
        'authority_class': 'projection', 'projection': projection,
        'source_bindings': [{'object_ref': source_ref, 'digest': expected_sha256, 'digest_kind': 'raw_bytes',
                             'upstream_schema': report['schema_version'], 'upstream_as_of': report['as_of']}],
        'generated_at': captured_at, 'generator_ref': 'scripts/prepare_media_review.py:media-care-handoff/v1'}
    schema = json.loads((ROOT/'schemas/projection-envelope.schema.json').read_text())
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(result)
    return result


def _view(envelope: dict) -> bytes:
    p = envelope['projection']
    lines = ['QUIRK MEDIA REVIEW — CANDIDATE / UNSIGNED', '', p['goal'],
        'Source snapshot: '+p['source_as_of']+'; current freshness is not revalidated.',
        'Selected asset: '+p['selection']['asset_ref'],
        'Selection attribution: '+p['selection']['actor_type']+' / '+p['selection']['signature_status'],
        'Source bytes SHA-256: '+p['source_report_sha256'],
        'Human benefit: unobserved. External execution authority: none.', '', 'REVIEW TASKS']
    for number, task in enumerate(p['tasks'], 1):
        finding = task['finding']
        lines.extend([f"{number}. {finding['code']} — {finding['asset_ref'] or 'whole kit'}",
                      '   Source says: '+json.dumps(finding['message'], ensure_ascii=False),
                      '   Finish: '+task['finish_condition'], '   State: proposed; owner acceptance not recorded.'])
    lines.extend(['', 'ALL HOLDS', *p['holds'], '', 'This handoff does not decode media, verify rights or source authenticity, admit a skill,',
                  'record human preference, dispatch a provider action, or apply a Preference Graph update.',
                  'The source report and every open finding are retained. Reopen checks local consistency only.'])
    return ('\n'.join(lines)+'\n').encode('utf-8')


def _reject_symlinks(path: Path) -> None:
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError('symlinked paths are outside this local handoff boundary')


def _read_file(path: Path, limit: int) -> bytes:
    _reject_symlinks(path)
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    try:
        with os.fdopen(os.open(path, flags), 'rb') as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                raise ValueError('regular file required')
            data = handle.read(limit+1)
    except OSError as exc:
        raise ValueError('required regular file is unavailable') from exc
    if len(data) > limit:
        raise ValueError('file exceeds bounded read budget')
    return data


def _outputs(raw: bytes, host_context: dict) -> dict[str, bytes]:
    envelope = prepare_report(raw, **host_context)
    outputs = {'source.json': raw, 'review.json': canonical(envelope)+b'\n', 'REVIEW.txt': _view(envelope)}
    if any(len(value) > MAX_EXPORT_FILE for value in outputs.values()):
        raise ValueError('export file budget exceeded')
    return outputs


def export_review(raw: bytes, destination: Path, **host_context) -> dict:
    """Write a new private directory. An interrupted package cannot pass replay.

    No overwrite. This local POSIX boundary does not defend a hostile concurrent
    filesystem owner or promise crash durability; verify before relying on output.
    """
    outputs = _outputs(raw, host_context)
    destination = Path(destination).absolute()
    _reject_symlinks(destination)
    destination.mkdir(mode=0o700, parents=False, exist_ok=False)
    written = []
    try:
        for name, data in outputs.items():
            target = destination/name
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
            with os.fdopen(os.open(target, flags, 0o600), 'wb') as handle:
                written.append(target)
                handle.write(data)
    except Exception:
        for target in reversed(written):
            target.unlink(missing_ok=True)
        destination.rmdir()
        raise
    return {'state': 'candidate', 'files': {name: sha256(data) for name, data in outputs.items()}, 'authority_effect': 'none'}


def verify_review(destination: Path, **host_context) -> dict:
    """Replay against caller-supplied source/tenant/principal/capture expectations.

    The capture time is historical metadata, not evidence of current freshness.
    """
    destination = Path(destination).absolute()
    _reject_symlinks(destination)
    if not destination.is_dir() or {p.name for p in destination.iterdir()} != {'source.json', 'review.json', 'REVIEW.txt'}:
        raise ValueError('incomplete or unexpected export inventory')
    raw = _read_file(destination/'source.json', MAX_SOURCE)
    outputs = _outputs(raw, host_context)
    for name, expected in outputs.items():
        if _read_file(destination/name, MAX_EXPORT_FILE) != expected:
            raise ValueError('export differs from exact deterministic replay: '+name)
    return {'replay_verified': True, 'scope': 'historical local consistency only',
            'current_freshness': 'not_revalidated', 'authority_effect': 'none',
            'source_sha256': sha256(raw), 'files': {k: sha256(v) for k,v in outputs.items()}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['prepare','verify'])
    parser.add_argument('--input', type=Path, help='Saved native Media Care report; prepare only')
    parser.add_argument('--directory', required=True, type=Path, help='New output directory or existing replay directory')
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--tenant-id', required=True)
    parser.add_argument('--principal-id', required=True)
    parser.add_argument('--captured-at', required=True, help='Explicit timezone-aware capture timestamp; not a live authorization clock')
    args = parser.parse_args()
    host = {'expected_sha256': args.expected_sha256, 'tenant_id': args.tenant_id,
            'principal_id': args.principal_id, 'captured_at': args.captured_at}
    try:
        if args.operation == 'prepare':
            if args.input is None:
                raise ValueError('--input required for prepare')
            result = export_review(_read_file(args.input, MAX_SOURCE), args.directory, **host)
        else:
            if args.input is not None:
                raise ValueError('--input is not accepted for verify')
            result = verify_review(args.directory, **host)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (ValueError, OSError, RecursionError) as exc:
        print(json.dumps({'status':'rejected', 'reason':str(exc), 'authority_effect':'none'}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
