"""Exercise the actual compiler and CLI, including refused publication paths."""

from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import object_pack as pack


def inputs(**updates):
    return dict(kind='agent', object_id='agent.example', title='Example Agent',
                owner='human.bryan', authority_ceiling='propose', status='candidate') | updates


class ObjectPackTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)

    def cli(self, output, *, repo=ROOT, title='Example Agent', extra=(), owner=True):
        command = [sys.executable, str(ROOT / 'scripts/scaffold_quirk_object_pack.py'),
                   '--repo', str(repo), '--kind', 'agent', '--id', 'agent.example',
                   '--title', title, '--output', str(output)]
        if owner:
            command += ['--owner', 'human.bryan']
        return subprocess.run(command + list(extra), text=True, capture_output=True, check=False)

    def source_copy(self):
        repo = self.directory / 'repo'
        shutil.copytree(ROOT / 'templates/quirk-object-pack', repo / 'templates/quirk-object-pack')
        (repo / 'schemas').mkdir()
        shutil.copy2(ROOT / pack.SCHEMA_PATH, repo / pack.SCHEMA_PATH)
        return repo

    def test_all_kinds_and_aliases_compile_with_stable_identity(self):
        registry = yaml.safe_load((ROOT / 'templates/quirk-object-pack/object-types.registry.yaml').read_text())
        expected = {entry['kind']: entry['kind'] for entry in registry['object_types']} | registry['aliases']
        for requested, resolved in expected.items():
            with self.subTest(kind=requested):
                files, report = pack.compile_pack(ROOT, inputs(kind=requested))
                self.assertEqual(set(files), set(registry['modules']))
                manifest = yaml.safe_load(files['MANIFEST.yaml'])
                workflow = yaml.safe_load(files['OPERATING-WORKFLOW.yaml'])
                self.assertEqual(manifest['kind'], resolved)
                self.assertEqual(workflow['metadata']['id'], 'agent.example')
                self.assertEqual(report['authority_effect'], 'none')

    def test_documented_example_compiles(self):
        example=json.loads((ROOT/'examples/deck-grammar/object-pack-input.json').read_text())
        files,report=pack.compile_pack(ROOT,example)
        self.assertEqual(len(files),11)
        self.assertEqual(report['inputs'],example)

    def test_titles_remain_literal_yaml_and_front_matter_data(self):
        titles = ['A: "quoted" title\n---\nauthority: execute_protected',
                  '{{OWNER_REF}} $(whoami) `x` [link](https://example.org)',
                  '<script>alert(1)</script>\n# New heading',
                  'false', '2026-09-10', 'BryMinn • 雷', 'line\r\nnext']
        for title in titles:
            with self.subTest(title=title):
                files, _ = pack.compile_pack(ROOT, inputs(title=title))
                manifest = yaml.safe_load(files['MANIFEST.yaml'])
                front = yaml.safe_load(files['SKILL.md'][4:].split('\n---\n', 1)[0])
                self.assertEqual(manifest['metadata']['title'], title)
                self.assertEqual(front, {'name':'agent.example', 'description':
                    f'Candidate Skill for {title}. Use only within its declared purpose and authority ceiling.'})
                self.assertEqual(manifest['authority']['ceiling'], 'propose')
                self.assertNotIn('\n# New heading', files['README.md'])
                self.assertNotIn('<script>', files['README.md'])
                self.assertEqual(set(manifest), {'api_version','kind','metadata','authority','contracts','lifecycle','prohibited'})

    def test_invalid_input_never_silently_falls_back(self):
        cases = [dict(owner=''), dict(owner='human.bryan\n'), dict(object_id='../escape'),
                 dict(kind='agent\n'), dict(title=' \n\t'), dict(title='x\x00y'),
                 dict(title='x'*501), dict(status='active'), dict(status='admitted'),
                 dict(authority_ceiling='execute_reversible'), dict(authority_ceiling='enforce_invariant'),
                 dict(authority_ceiling='execute_protected'), dict(title=42), dict(unknown=True)]
        for update in cases:
            with self.subTest(update=update), self.assertRaises(pack.PackError):
                pack.compile_pack(ROOT, inputs(**update))
        # Matched valid lower ceilings still work; this is not a blanket denial.
        for ceiling in ('observe', 'infer', 'propose'):
            files, _ = pack.compile_pack(ROOT, inputs(authority_ceiling=ceiling))
            self.assertEqual(yaml.safe_load(files['SETTINGS.yaml'])['authority']['ceiling'], ceiling)

    def test_owner_is_required_at_cli_boundary(self):
        output = self.directory / 'pack'
        result = self.cli(output, owner=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('--owner', result.stderr)
        self.assertFalse(output.exists())

    def test_unknown_kind_is_explained_without_traceback_or_output(self):
        output = self.directory / 'pack'
        result = self.cli(output, extra=['--kind','imaginary','--json'])
        self.assertEqual(result.returncode, 2)
        self.assertIn('unsupported object kind', json.loads(result.stderr)['error'])
        self.assertFalse(output.exists())

    def test_preview_writes_nothing_and_bound_write_matches_every_hash(self):
        output = self.directory / 'missing-parent' / 'pack'
        preview = self.cli(output, extra=['--dry-run','--json'])
        self.assertEqual(preview.returncode, 0, preview.stderr)
        report = json.loads(preview.stdout)
        self.assertFalse(output.parent.exists())
        result = self.cli(output, extra=['--json','--expect-content-sha256',report['content_sha256']])
        self.assertEqual(result.returncode, 0, result.stderr)
        written = json.loads(result.stdout)
        self.assertEqual(written['content_sha256'], report['content_sha256'])
        self.assertEqual(written['action'], 'written')
        self.assertEqual(written['signature_status'], 'unsigned')
        self.assertEqual({p.name for p in output.iterdir()}, set(pack.TEMPLATE_MAP))
        for item in report['files']:
            raw = (output/item['path']).read_bytes()
            self.assertEqual(len(raw), item['bytes'])
            self.assertEqual(sha256(raw).hexdigest(), item['sha256'])

    def test_recompilation_and_alias_preserve_content_digest(self):
        first_files, first = pack.compile_pack(ROOT, inputs())
        second_files, second = pack.compile_pack(ROOT, inputs(kind='agents'))
        self.assertEqual(first_files, second_files)
        self.assertEqual(first['content_sha256'], second['content_sha256'])
        settings = yaml.safe_load(first_files['SETTINGS.yaml'])
        self.assertEqual(settings['precedence'], ['explicit_current','purpose_scoped','admitted_project','admitted_global','default'])

    def test_source_or_input_drift_blocks_old_preview(self):
        repo = self.source_copy()
        output = self.directory/'pack'
        before = json.loads(self.cli(output, repo=repo, extra=['--dry-run','--json']).stdout)
        result = self.cli(output, repo=repo, title='Changed', extra=['--expect-content-sha256',before['content_sha256']])
        self.assertEqual(result.returncode, 2)
        self.assertFalse(output.exists())
        template = repo/'templates/quirk-object-pack/README.template.md'
        template.write_text(template.read_text()+'\nSource revision.\n')
        result = self.cli(output, repo=repo, extra=['--json','--expect-content-sha256',before['content_sha256']])
        self.assertEqual(result.returncode, 2)
        self.assertIn('preview is stale', result.stderr)
        self.assertFalse(output.exists())

    def test_source_cannot_silently_promote_or_detach_the_pack(self):
        repo = self.source_copy()
        cases = [('MANIFEST.template.yaml','human_admission_required: true','human_admission_required: false'),
                 ('MANIFEST.template.yaml','current: {{STATUS}}','current: admitted'),
                 ('SETTINGS.template.yaml','ceiling: {{AUTHORITY_CEILING}}','ceiling: execute_protected'),
                 ('SETTINGS.template.yaml','owner_ref: {{OWNER_REF}}','owner_ref: human.someone_else'),
                 ('OPERATING-WORKFLOW.template.yaml','id: {{OBJECT_ID}}','id: workflow.detached')]
        for filename, old, new in cases:
            with self.subTest(filename=filename, new=new):
                template=repo/'templates/quirk-object-pack'/filename
                original=template.read_text()
                template.write_text(original.replace(old,new))
                with self.assertRaises(pack.PackError): pack.compile_pack(repo, inputs())
                template.write_text(original)

    def test_template_errors_are_refused_before_writes(self):
        repo = self.source_copy()
        template=repo/'templates/quirk-object-pack/MANIFEST.template.yaml'
        original=template.read_text()
        variants=[original+'\nkind: agent\n', original.replace('{{OBJECT_KIND}}','{{MISSING}}'),
                  original.replace('{{OBJECT_KIND}}','{{BROKEN'), original+'\nx: &x [*x]\n',
                  original+'\nx: !!python/object:os.system {}\n', original.replace('kind:', '{{OBJECT_KIND}}:')]
        for text in variants:
            with self.subTest(text=text[-80:]):
                template.write_text(text)
                output=self.directory/'pack'
                result=self.cli(output, repo=repo, extra=['--json'])
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertEqual(json.loads(result.stderr)['action'], 'not_published')
                self.assertFalse(output.exists())

    def test_remote_schema_dependency_is_refused(self):
        repo=self.source_copy()
        schema_path=repo/pack.SCHEMA_PATH
        schema=json.loads(schema_path.read_text())
        schema['$defs']['title']={'$ref':'https://example.org/must-not-fetch.json'}
        schema_path.write_text(json.dumps(schema))
        with self.assertRaisesRegex(pack.PackError, 'only local schema'):
            pack.compile_pack(repo, inputs())

    def test_existing_empty_directory_is_supported(self):
        output=self.directory/'pack'
        output.mkdir()
        result=self.cli(output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(list(output.iterdir())), 11)

    def test_nonempty_file_and_symlink_destinations_are_preserved(self):
        nonempty=self.directory/'nonempty'; nonempty.mkdir(); (nonempty/'keep').write_text('retained')
        file=self.directory/'file'; file.write_text('retained')
        link=self.directory/'link'; link.symlink_to(nonempty, target_is_directory=True)
        dangling=self.directory/'dangling'; dangling.symlink_to(self.directory/'absent')
        for output in (nonempty,file,link,dangling):
            with self.subTest(output=output):
                result=self.cli(output)
                self.assertEqual(result.returncode, 2)
        self.assertEqual((nonempty/'keep').read_text(), 'retained')
        self.assertEqual(file.read_text(), 'retained')
        self.assertTrue(link.is_symlink())
        self.assertTrue(dangling.is_symlink())

    def test_stage_write_failure_leaves_no_partial_pack(self):
        files,_=pack.compile_pack(ROOT,inputs())
        output=self.directory/'pack'
        original=Path.write_bytes
        def fail_second(path,data):
            if path.name=='README.md': raise OSError('simulated storage failure')
            return original(path,data)
        with patch.object(Path,'write_bytes',fail_second), self.assertRaises(OSError):
            pack.publish_pack(output,files)
        self.assertFalse(output.exists())
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_rename_failure_preserves_existing_output_and_cleans_stage(self):
        files,_=pack.compile_pack(ROOT,inputs())
        output=self.directory/'pack'; output.mkdir()
        with patch.object(Path,'rename',side_effect=OSError('simulated finalization failure')):
            with self.assertRaises(OSError): pack.publish_pack(output,files)
        self.assertEqual(list(output.iterdir()), [])
        self.assertEqual(list(self.directory.iterdir()), [output])

    def test_newly_populated_destination_is_not_overwritten(self):
        files,_=pack.compile_pack(ROOT,inputs())
        output=self.directory/'pack'
        original=pack.check_destination
        count=0
        def raced(path):
            nonlocal count
            count+=1
            if count==2:
                path.mkdir(); (path/'other-writer').write_text('retained')
            original(path)
        with patch.object(pack,'check_destination',raced), self.assertRaises(pack.PackError):
            pack.publish_pack(output,files)
        self.assertEqual((output/'other-writer').read_text(),'retained')
        self.assertEqual(list(self.directory.iterdir()),[output])

    def test_incomplete_pack_cannot_be_published(self):
        output=self.directory/'pack'
        with self.assertRaises(pack.PackError): pack.publish_pack(output, {'README.md':'partial'})
        self.assertFalse(output.exists())

    def test_report_write_failure_does_not_claim_pack_was_not_published(self):
        class BrokenOutput(io.StringIO):
            def write(self, value): raise OSError('simulated pipe failure')
        output=self.directory/'pack'; errors=io.StringIO()
        with redirect_stdout(BrokenOutput()), redirect_stderr(errors):
            result=pack.main(['--kind','agent','--id','agent.example','--title','Example',
                              '--owner','human.bryan','--output',str(output),'--json'])
        self.assertEqual(result,4)
        self.assertEqual(len(list(output.iterdir())),11)
        self.assertIn('pack written',errors.getvalue())


if __name__=='__main__':
    unittest.main()
