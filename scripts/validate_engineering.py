"""Validate candidate engineering schemas and their loop input compatibility.

This is structural/contract evidence. It does not run external actions, admit
skills, establish human usefulness, or replace the behavioral test suites.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator, FormatChecker

SCHEMA_NAMES = (
    'action-contract.v1.schema.json',
    'action-grant.v1.schema.json',
    'action-receipt.v2.schema.json',
    'engineering-graph-object.v1.schema.json',
    'engineering-graph-assertion.v1.schema.json',
    'loop-spec.v1.schema.json',
    'skill-run-receipt.v2.schema.json',
)


def _reject_constant(value):
    raise ValueError(f'non-JSON numeric constant: {value}')


def loop_cases():
    base = {
        'schema_version': 'loop-spec/v1', 'run_id': 'run.schema-check',
        'objective': 'Prepare a bounded candidate', 'source_digest': 'a' * 64,
        'evaluator_digest': 'b' * 64, 'acceptance': {'required': ['source_ref']},
        'authority': 'CANDIDATE_PREPARE',
        'limits': {'steps': 3, 'repairs': 2, 'seconds': 30},
    }
    yield 'candidate_prepare', base, True
    for authority in ('EXECUTE', 'REVOKED', 'PREPARE'):
        yield 'authority_pauses_' + authority, {**base, 'authority': authority}, True
    for label, limits in (
        ('minimum_budgets', {'steps': 1, 'repairs': 0, 'seconds': 1}),
        ('maximum_budgets', {'steps': 100, 'repairs': 99, 'seconds': 3600}),
    ):
        yield label, {**base, 'limits': limits}, True
    yield 'frozen_extension_metadata', {**base, 'metadata': {'candidate': True}, 'limits': {**base['limits'], 'reads': 5}}, True
    for key in base:
        missing = deepcopy(base)
        del missing[key]
        yield 'missing_' + key, missing, False
    for key in ('run_id', 'objective', 'authority'):
        yield 'blank_' + key, {**base, key: ' \n\t'}, False
    for key in ('source_digest', 'evaluator_digest'):
        for label, value in (('uppercase', 'A' * 64), ('short', 'a' * 63), ('newline', 'a' * 64 + '\n')):
            yield label + '_' + key, {**base, key: value}, False
    yield 'wrong_version', {**base, 'schema_version': 'loop-spec/v2'}, False
    yield 'empty_acceptance', {**base, 'acceptance': {}}, False
    yield 'array_acceptance', {**base, 'acceptance': []}, False
    for key, low, high in (('steps', 1, 100), ('repairs', 0, 99), ('seconds', 1, 3600)):
        for label, value in (('too_low', low - 1), ('too_high', high + 1), ('boolean', True), ('fractional', 1.5)):
            yield label + '_' + key, {**base, 'limits': {**base['limits'], key: value}}, False


def validate(root):
    findings, schemas, case_results = [], {}, []
    identifiers = set()
    for name in SCHEMA_NAMES:
        try:
            schema = json.loads((root / 'schemas' / name).read_text(encoding='utf-8'), parse_constant=_reject_constant)
            Draft202012Validator.check_schema(schema)
            if schema.get('$schema') != 'https://json-schema.org/draft/2020-12/schema':
                raise ValueError('expected JSON Schema draft 2020-12')
            identity = schema.get('$id')
            if not isinstance(identity, str) or not identity or identity in identifiers:
                raise ValueError('schema must have a unique nonempty $id')
            identifiers.add(identity)
            schemas[name] = schema
        except (OSError, ValueError, TypeError, KeyError) as exc:
            findings.append({'code': 'SCHEMA_INVALID', 'path': 'schemas/' + name, 'message': str(exc)})
        except Exception as exc:  # JSON Schema's SchemaError includes its useful location.
            findings.append({'code': 'SCHEMA_INVALID', 'path': 'schemas/' + name, 'message': str(exc)})

    loop_schema = schemas.get('loop-spec.v1.schema.json')
    if loop_schema is not None:
        sys.path.insert(0, str(root))
        from scripts.engineering.loop import _validate_spec
        validator = Draft202012Validator(loop_schema, format_checker=FormatChecker())
        for name, instance, expected in loop_cases():
            schema_accepts = validator.is_valid(instance)
            try:
                _validate_spec(instance, instance.get('evaluator_digest'))
                runtime_accepts = True
            except (ValueError, TypeError, AttributeError):
                runtime_accepts = False
            passed = schema_accepts == expected and runtime_accepts == expected
            case_results.append({'case': name, 'passed': passed, 'schema_accepts': schema_accepts,
                                 'runtime_accepts': runtime_accepts, 'expected': expected})
            if not passed:
                findings.append({'code': 'LOOP_SCHEMA_RUNTIME_DRIFT', 'path': name,
                                 'message': f'expected {expected}; schema={schema_accepts}, runtime={runtime_accepts}'})

    return {
        'schema_version': 'engineering-validation/v1',
        'status': 'pass' if not findings else 'fail',
        'evaluated_at': datetime.now(timezone.utc).isoformat(),
        'schema_count': len(schemas), 'expected_schema_count': len(SCHEMA_NAMES),
        'schemas': sorted(schemas), 'loop_case_count': len(case_results),
        'passed_loop_case_count': sum(case['passed'] for case in case_results),
        'loop_cases': case_results, 'findings': findings,
        'runtime_only_constraints': [
            'Evaluator identity is compared with the separately supplied evaluator digest.',
            'Runtime rejects nonfinite JSON and Python float budget values even when mathematically integral.',
            'Non-CANDIDATE_PREPARE authority causes a pause before dispatch, not schema rejection.',
        ],
        'authority': {'admission_effect': 'none', 'external_writes': 0, 'human_usefulness': None},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default='.', type=Path)
    parser.add_argument('--output', type=Path, help='Write the JSON validation report.')
    args = parser.parse_args()
    root = args.repo.resolve()
    report = validate(root)
    if args.output:
        output = root / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    for finding in report['findings']:
        print(f"ERROR {finding['code']} {finding['path']}: {finding['message']}", file=sys.stderr)
    print(f"engineering validation {report['status']}: {report['schema_count']}/{report['expected_schema_count']} schemas, "
          f"{report['passed_loop_case_count']}/{report['loop_case_count']} loop compatibility cases")
    return 0 if report['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
