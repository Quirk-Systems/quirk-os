"""Compile eleven candidate source modules with typed inputs and no runtime authority."""

from __future__ import annotations

import argparse
from hashlib import sha256
import html
from importlib.metadata import version
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile

import yaml
from jsonschema import Draft202012Validator, SchemaError

TEMPLATE_MAP = {
    'MANIFEST.yaml': 'MANIFEST.template.yaml',
    'README.md': 'README.template.md',
    'REPO-MANAGEMENT.md': 'REPO-MANAGEMENT.template.md',
    'SYSTEM-PROMPT.md': 'SYSTEM-PROMPT.template.md',
    'CUSTOM-INSTRUCTIONS.md': 'CUSTOM-INSTRUCTIONS.template.md',
    'SETTINGS.yaml': 'SETTINGS.template.yaml',
    'PROJECT-INSTRUCTIONS.md': 'PROJECT-INSTRUCTIONS.template.md',
    'REFERENCES.md': 'REFERENCES.template.md',
    'SKILL.md': 'SKILL.template.md',
    'EVALS.yaml': 'EVALS.template.yaml',
    'OPERATING-WORKFLOW.yaml': 'OPERATING-WORKFLOW.template.yaml',
}
SCHEMA_PATH = 'schemas/object-pack-creation.schema.json'
SLOT = re.compile(r'\{\{([^{}]+)\}\}')
MARKER_PREFIX = 'QUIRKPACKSLOT_'
MARKER = re.compile(MARKER_PREFIX + r'([A-Z_]+)_END')


class PackError(ValueError):
    """A rejected input, template, or destination. No pack was published."""


class StrictLoader(yaml.SafeLoader):
    """Data-only YAML with string keys, no aliases, and no duplicate keys."""

    def compose_node(self, parent, index):
        if self.check_event(yaml.AliasEvent):
            raise PackError('YAML aliases are unsupported in object-pack source')
        return super().compose_node(parent, index)

    def construct_mapping(self, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str) or key in result:
                raise PackError('YAML keys must be unique strings')
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def load_yaml(text: str) -> dict:
    data = yaml.load(text, Loader=StrictLoader)
    if not isinstance(data, dict):
        raise PackError('expected a YAML object')
    return data


def substitute(template: str, values: dict[str, str]) -> str:
    """Bind source slots once; input containing slot syntax stays literal."""
    def replacement(match):
        key = match.group(1)
        if key not in values:
            raise PackError(f'unknown template placeholder: {key}')
        return values[key]

    residue = SLOT.sub('', template)
    if '{{' in residue or '}}' in residue:
        raise PackError('malformed template placeholder')
    return SLOT.sub(replacement, template)


def structured_template(template: str, values: dict[str, str]) -> dict:
    # Neutral scalar markers let existing unquoted YAML slots parse. User data
    # enters parsed string values, never YAML syntax or mapping keys.
    if MARKER_PREFIX in template:
        raise PackError('reserved marker in template source')
    source = load_yaml(substitute(template, {key: f'{MARKER_PREFIX}{key}_END' for key in values}))

    def bind(node):
        if isinstance(node, str):
            return MARKER.sub(lambda match: values[match.group(1)], node)
        if isinstance(node, list):
            return [bind(item) for item in node]
        if isinstance(node, dict):
            if any(MARKER_PREFIX in key for key in node):
                raise PackError('template slots cannot define YAML keys')
            return {key: bind(value) for key, value in node.items()}
        return node

    return bind(source)


def markdown_title(title: str) -> str:
    # Display titles stay on one line and cannot add headings, links, HTML, or
    # code fences. Manifest and front matter retain the exact original string.
    display = html.escape(' '.join(title.splitlines()).replace('\t', ' '), quote=False)
    return re.sub(r'([\\`*_{}\[\]()#+.!|\-])', r'\\\1', display)


def render(template: str, values: dict[str, str]) -> str:
    return substitute(template, dict(values, OBJECT_TITLE=markdown_title(values['OBJECT_TITLE'])))


def dump_yaml(data: dict) -> str:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=88)


def validate(data: dict, schema: dict, definition: str) -> None:
    validator = Draft202012Validator(dict(schema, **{'$ref': f'#/$defs/{definition}'}))
    error = next(validator.iter_errors(data), None)
    if error:
        location = '.'.join(str(part) for part in error.absolute_path) or definition
        raise PackError(f'{location}: {error.message}')


def canonical_bytes(data: dict) -> bytes:
    """Local JSON digest convention, not a signature or RFC 8785 claim."""
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode('utf-8')


def compile_pack(repo: Path, inputs: dict[str, str]) -> tuple[dict[str, str], dict]:
    """Compile and validate completely in memory; never writes output."""
    source_hashes = {}

    def read(relative: str) -> str:
        raw = (repo / relative).read_bytes()
        source_hashes[relative] = sha256(raw).hexdigest()
        return raw.decode('utf-8')

    schema = json.loads(read(SCHEMA_PATH))
    Draft202012Validator.check_schema(schema)

    def check_refs(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ('$ref', '$dynamicRef') and not value.startswith('#'):
                    raise PackError('only local schema references are supported')
                check_refs(value)
        elif isinstance(node, list):
            for value in node:
                check_refs(value)
    check_refs(schema)
    validate(inputs, schema, 'inputs')
    template_dir = 'templates/quirk-object-pack/'
    registry = load_yaml(read(template_dir + 'object-types.registry.yaml'))
    validate(registry, schema, 'registry')
    kind = registry['aliases'].get(inputs['kind'], inputs['kind'])
    supported = {entry['kind'] for entry in registry['object_types']}
    if kind not in supported:
        raise PackError(f'unsupported object kind: {inputs["kind"]}')
    if registry['modules'] != list(TEMPLATE_MAP):
        raise PackError('registry modules do not match the eleven-file emitter contract')
    resolved = dict(inputs, kind=kind)
    values = {
        'OBJECT_ID': inputs['object_id'], 'OBJECT_TITLE': inputs['title'],
        'OBJECT_KIND': kind, 'OWNER_REF': inputs['owner'],
        'AUTHORITY_CEILING': inputs['authority_ceiling'], 'STATUS': inputs['status'],
    }
    files, structured = {}, {}
    for destination, template_name in TEMPLATE_MAP.items():
        source = read(template_dir + template_name)
        if destination.endswith('.yaml'):
            data = structured_template(source, values)
            files[destination] = dump_yaml(data)
            structured[destination] = load_yaml(files[destination])
            if structured[destination] != data:
                raise PackError(f'{destination}: YAML round trip changed the data')
        elif destination == 'SKILL.md':
            if not source.startswith('---\n') or '\n---\n' not in source[4:]:
                raise PackError('SKILL template requires YAML front matter')
            front, body = source[4:].split('\n---\n', 1)
            data = structured_template(front, values)
            front_text = dump_yaml(data)
            structured['skill_front_matter'] = load_yaml(front_text)
            if structured['skill_front_matter'] != data:
                raise PackError('SKILL front matter did not round trip')
            files[destination] = '---\n' + front_text + '---\n' + render(body, values)
        else:
            files[destination] = render(source, values)
    validate(structured, schema, 'generated')
    manifest = structured['MANIFEST.yaml']
    expected = {'id': inputs['object_id'], 'title': inputs['title'],
                'version': '0.1.0', 'status': 'candidate', 'owner_ref': inputs['owner']}
    if manifest['metadata'] != expected or manifest['kind'] != kind:
        raise PackError('manifest does not match the supplied identity')
    for name, prefix in (('SETTINGS.yaml', 'settings.'), ('EVALS.yaml', 'eval.'),
                         ('OPERATING-WORKFLOW.yaml', '')):
        if structured[name]['metadata']['id'] != prefix + inputs['object_id']:
            raise PackError(f'{name}: object identity is detached from the manifest')
    if (structured['SETTINGS.yaml']['metadata']['owner_ref'] != inputs['owner']
            or structured['EVALS.yaml']['subject_ref'] != inputs['object_id']
            or structured['skill_front_matter']['name'] != inputs['object_id']):
        raise PackError('generated owner or subject is detached from the manifest')
    ceilings = [manifest['authority']['ceiling'],
                structured['SETTINGS.yaml']['authority']['ceiling'],
                structured['OPERATING-WORKFLOW.yaml']['authority_ceiling']]
    if any(ceiling != inputs['authority_ceiling'] for ceiling in ceilings):
        raise PackError('generated ceiling differs from the requested candidate ceiling')
    payload = {
        'inputs': resolved,
        'compiler_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
        'dependencies': {name: version(name) for name in ('PyYAML', 'jsonschema')},
        'source_sha256': dict(sorted(source_hashes.items())),
        'files': [{'path': name, 'bytes': len(content.encode('utf-8')),
                   'sha256': sha256(content.encode('utf-8')).hexdigest()}
                  for name, content in sorted(files.items())],
    }
    report = {
        'schema_version': 'object-pack-creation-report.v1', 'status': 'candidate',
        'authority_effect': 'none', 'signature_status': 'unsigned',
        'validation': 'passed', 'file_count': len(files),
        'content_sha256': sha256(canonical_bytes(payload)).hexdigest(), **payload,
    }
    return files, report


def check_destination(output: Path) -> None:
    if output.is_symlink():
        raise PackError('output must not be a symlink')
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise PackError('output must be absent or an empty directory')


def publish_pack(output: Path, files: dict[str, str]) -> None:
    """Stage beside output, then rename once; never replace a populated pack."""
    if set(files) != set(TEMPLATE_MAP):
        raise PackError('publication requires all eleven compiled modules')
    check_destination(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.quirk-pack-', dir=output.parent))
    try:
        for name, content in files.items():
            if name not in TEMPLATE_MAP:
                raise PackError('unexpected output module')
            (stage / name).write_bytes(content.encode('utf-8'))
        check_destination(output)
        stage.rename(output)
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind', required=True)
    parser.add_argument('--id', required=True, dest='object_id')
    parser.add_argument('--title', required=True)
    parser.add_argument('--owner', required=True, help='explicit owner ref, e.g. human.bryan')
    parser.add_argument('--authority-ceiling', default='propose', choices=('observe', 'infer', 'propose'))
    parser.add_argument('--status', default='candidate', choices=('candidate',))
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--dry-run', action='store_true', help='validate and preview without writing')
    parser.add_argument('--json', action='store_true', help='emit an unsigned JSON preview or write report')
    parser.add_argument('--expect-content-sha256', help='refuse if inputs or sources changed since preview')
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        check_destination(args.output)
        files, report = compile_pack(args.repo, {key: getattr(args, key) for key in
                                               ('kind', 'object_id', 'title', 'owner', 'authority_ceiling', 'status')})
        if args.expect_content_sha256 and args.expect_content_sha256 != report['content_sha256']:
            raise PackError('preview is stale: content digest changed; inspect a fresh --dry-run --json')
        if args.json:
            message = json.dumps(dict(report, action='preview' if args.dry_run else 'written',
                                      output=str(args.output)), ensure_ascii=False, indent=2)
        elif args.dry_run:
            message = '\n'.join(sorted(files))
        else:
            message = f'created {len(files)} candidate files in {args.output}'
        if not args.dry_run:
            publish_pack(args.output, files)
    except (PackError, OSError, UnicodeError, yaml.YAMLError, json.JSONDecodeError, SchemaError) as error:
        if args.json:
            print(json.dumps({'status': 'rejected', 'action': 'not_published',
                              'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        else:
            print(f'object pack not created: {error}', file=sys.stderr)
        return 2
    # Output failure after publication must not be reported as a failed write.
    try:
        print(message)
    except OSError:
        state = 'preview complete' if args.dry_run else f'pack written to {args.output}'
        print(f'{state}; could not emit stdout report', file=sys.stderr)
        return 4
    return 0
