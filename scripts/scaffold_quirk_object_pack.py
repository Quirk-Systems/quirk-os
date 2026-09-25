from __future__ import annotations
import argparse
from pathlib import Path
import sys
import yaml
TEMPLATE_MAP = {'MANIFEST.yaml': 'MANIFEST.template.yaml', 'README.md': 'README.template.md', 'REPO-MANAGEMENT.md': 'REPO-MANAGEMENT.template.md', 'SYSTEM-PROMPT.md': 'SYSTEM-PROMPT.template.md', 'CUSTOM-INSTRUCTIONS.md': 'CUSTOM-INSTRUCTIONS.template.md', 'SETTINGS.yaml': 'SETTINGS.template.yaml', 'PROJECT-INSTRUCTIONS.md': 'PROJECT-INSTRUCTIONS.template.md', 'REFERENCES.md': 'REFERENCES.template.md', 'SKILL.md': 'SKILL.template.md', 'EVALS.yaml': 'EVALS.template.yaml', 'OPERATING-WORKFLOW.yaml': 'OPERATING-WORKFLOW.template.yaml'}

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind', required=True)
    parser.add_argument('--id', required=True, dest='object_id')
    parser.add_argument('--title', required=True)
    parser.add_argument('--owner', default='human.bryan')
    parser.add_argument('--authority-ceiling', default='propose')
    parser.add_argument('--status', default='candidate')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--dry-run', action='store_true')
    return parser.parse_args()

def render(template: str, values: dict[str, str]) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace('{{' + key + '}}', value)
    unresolved = sorted((token for token in set((part.split('}}', 1)[0] for part in rendered.split('{{')[1:])) if token))
    if unresolved:
        raise ValueError(f'unresolved template placeholders: {unresolved}')
    return rendered

def load_registry(template_root: Path) -> dict:
    path = template_root / 'object-types.registry.yaml'
    registry = yaml.safe_load(path.read_text(encoding='utf-8'))
    if not isinstance(registry, dict):
        raise ValueError('object type registry must be an object')
    return registry

def main() -> int:
    args = parse_args()
    template_root = args.repo / 'templates' / 'quirk-object-pack'
    registry = load_registry(template_root)
    kind = registry.get('aliases', {}).get(args.kind, args.kind)
    supported = {entry['kind'] for entry in registry['object_types']}
    if kind not in supported:
        print(f'unsupported object kind: {args.kind}', file=sys.stderr)
        return 2
    if args.output.exists() and any(args.output.iterdir()):
        print(f'output directory is not empty: {args.output}', file=sys.stderr)
        return 3
    values = {'OBJECT_ID': args.object_id, 'OBJECT_TITLE': args.title, 'OBJECT_KIND': kind, 'OWNER_REF': args.owner, 'AUTHORITY_CEILING': args.authority_ceiling, 'STATUS': args.status}
    generated: dict[str, str] = {}
    for destination, template_name in TEMPLATE_MAP.items():
        template = (template_root / template_name).read_text(encoding='utf-8')
        generated[destination] = render(template, values)
    if args.dry_run:
        for path in sorted(generated):
            print(path)
        return 0
    args.output.mkdir(parents=True, exist_ok=True)
    for destination, content in generated.items():
        target = args.output / destination
        target.write_text(content, encoding='utf-8')
    print(f'created {len(generated)} files in {args.output}')
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
