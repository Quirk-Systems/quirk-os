"""Adjacent crossing cases. All GitHub identities/reviews here are synthetic."""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from sync_control_plane.attestation import ApprovalError, GitHubApprovalVerifier, GitHubReader, MAX_GITHUB_REQUESTS
from sync_control_plane.content import ContentError, manifest_content_hash, manifest_preimage, strict_json_loads
from sync_control_plane.policy import validate_manifest_admission
from sync_control_plane.projection import prepare_projection

NOW = datetime(2026, 10, 4, 14, 30, tzinfo=timezone.utc)
HEAD, BASE = 'a' * 40, 'b' * 40
REPO = 'synthetic/contract-tests'
ROOT_API = '/repos/' + REPO
OWNERS = b'* @synthetic-owner\n/.github/CODEOWNERS @synthetic-owner\n'
PR_API = ROOT_API + '/pulls/7'
REVIEW_API = PR_API + '/reviews/81'
CENSUS_API = PR_API + '/reviews?per_page=100&page=1'
MANIFEST_PATH = 'fixtures/candidate.json'
EVAL_PATH = 'fixtures/evaluation.json'


class MemoryReader:
    def __init__(self, data):
        self.data = data
        self.calls = []
        self.change_on_repeat = {}

    def get(self, endpoint):
        self.calls.append(endpoint)
        if endpoint in self.change_on_repeat and self.calls.count(endpoint) > 1:
            return copy.deepcopy(self.change_on_repeat[endpoint])
        if endpoint not in self.data:
            raise ApprovalError('synthetic API unavailable')
        return copy.deepcopy(self.data[endpoint])


class FrozenVerifier(GitHubApprovalVerifier):
    def verify(self, manifest, context, *, now=None):
        return super().verify(manifest, context, now=now or NOW)


def body(subject):
    fence = chr(96) * 3
    return 'Explicit synthetic activation consent.\n' + fence + 'quirk-manifest-approval\n' + json.dumps(subject) + '\n' + fence


def scenario():
    candidate = json.loads((ROOT / 'evals/sync-control-plane/valid-active-manifest.json').read_text())
    candidate.update(status='candidate', requested_status='active', admission=None,
                     manifest_key='agent.synthetic', eval_refs=[EVAL_PATH],
                     metadata={'case': 'synthetic; no runtime authority'})
    candidate['content_hash'] = manifest_content_hash(candidate)
    subject = {
        'schema_version': 'manifest-approval-attestation.v1', 'repository': REPO, 'pr_number': 7,
        'head_sha': HEAD, 'base_sha': BASE, 'manifest_path': MANIFEST_PATH,
        'manifest_key': candidate['manifest_key'], 'manifest_version': candidate['version'],
        'hash_profile': 'runtime-manifest-content.v1', 'content_hash': candidate['content_hash'],
        'requested_by': 'agent.synthetic', 'action': 'activate_manifest', 'from_status': 'candidate',
        'to_status': 'active', 'requested_status': 'active', 'environment': 'test',
        'authority_ceiling': candidate['authority_ceiling'], 'allowed_actions': [], 'object_scope': [],
        'evaluation_ref': EVAL_PATH, 'evidence_refs': [EVAL_PATH],
        'valid_from': '2026-10-04T14:00:00Z', 'expires_at': '2026-10-04T15:00:00Z',
    }
    review = {'id': 81, 'state': 'APPROVED', 'commit_id': HEAD, 'submitted_at': '2026-10-04T14:00:00Z',
              'user': {'id': 999, 'type': 'User', 'login': 'synthetic-owner'}, 'body': body(subject)}
    evaluation = {k: subject[k] for k in ('manifest_key', 'manifest_version', 'hash_profile', 'content_hash')}
    material = b'synthetic evaluator observation\n'
    evaluation.update(schema_version='manifest-evaluation.v1', decision='pass', authority_effect='none',
                      materials=[{'path': 'fixtures/raw.txt', 'sha256': hashlib.sha256(material).hexdigest()}])
    data = {
        PR_API: {'state': 'open', 'draft': False, 'merged': False, 'user': {'id': 998},
                 'head': {'sha': HEAD, 'ref': 'candidate', 'repo': {'full_name': REPO, 'id': 123}},
                 'base': {'sha': BASE, 'ref': 'main', 'repo': {'full_name': REPO, 'id': 123}}},
        REVIEW_API: review, CENSUS_API: [copy.deepcopy(review)],
    }
    def put(path, revision, raw):
        blob_sha = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        tree = data.setdefault(f'{ROOT_API}/git/trees/{revision}?recursive=1', {'truncated': False, 'tree': []})
        tree['tree'].append({'path': path, 'type': 'blob', 'mode': '100644', 'sha': blob_sha})
        data[f'{ROOT_API}/contents/{path}?ref={revision}'] = {
            'type': 'file', 'encoding': 'base64', 'sha': blob_sha, 'content': base64.b64encode(raw).decode()}
    put('.github/CODEOWNERS', BASE, OWNERS)
    put(MANIFEST_PATH, HEAD, json.dumps(candidate).encode())
    put(EVAL_PATH, HEAD, json.dumps(evaluation).encode())
    put('fixtures/raw.txt', HEAD, material)
    policy = {'enabled': True, 'protection_verified': True, 'repository': REPO, 'base_branch': 'main',
              'human_principals': {'999': 'human.synthetic'}, 'human_logins': {'999': 'synthetic-owner'},
              'codeowners_sha256': hashlib.sha256(OWNERS).hexdigest(), 'environments': ['test'],
              'revoked_review_ids': []}
    context = {k: subject[k] for k in ('manifest_path', 'environment', 'requested_by', 'from_status',
                                     'allowed_actions', 'object_scope')}
    context.update(pr_number=7, review_id=81, requester_github_id=998)
    reader = MemoryReader(data)
    return candidate, subject, context, reader, FrozenVerifier(policy, reader)


def set_subject(reader, subject):
    reader.data[REVIEW_API]['body'] = body(subject)
    reader.data[CENSUS_API] = [copy.deepcopy(reader.data[REVIEW_API])]


class ContentHashTests(unittest.TestCase):
    def setUp(self):
        self.manifest = scenario()[0]

    def test_committed_golden_vectors(self):
        vectors = strict_json_loads((ROOT / 'evals/sync-control-plane/content-hash-vectors.json').read_bytes())
        for vector in vectors['vectors']:
            with self.subTest(vector=vector['id']):
                self.assertEqual(vector['preimage_utf8'], manifest_preimage(vector['manifest']).decode())
                self.assertEqual(vector['sha256'], manifest_content_hash(vector['manifest']))

    def test_metadata_change_changes_hash(self):
        changed = copy.deepcopy(self.manifest)
        changed['metadata']['new'] = {'purpose': 'another purpose'}
        self.assertNotEqual(manifest_content_hash(self.manifest), manifest_content_hash(changed))

    def test_each_excluded_field_leaves_content_hash_unchanged(self):
        baseline = manifest_content_hash(self.manifest)
        for key, value in [('content_hash', '0' * 64), ('status', 'paused'),
                           ('requested_status', 'paused'), ('admission', None)]:
            with self.subTest(field=key):
                changed = copy.deepcopy(self.manifest)
                changed[key] = value
                self.assertEqual(baseline, manifest_content_hash(changed))
        active = prepare_projection(*self._projection_args())['manifest']
        self.assertEqual(baseline, manifest_content_hash(active))

    def _projection_args(self):
        candidate, _, context, _, verifier = scenario()
        return candidate, context, verifier

    def test_key_order_is_irrelevant_array_order_is_not(self):
        self.manifest['metadata'] = {'z': [1, 2], 'a': '\u00e9'}
        reordered = dict(reversed(list(self.manifest.items())))
        reordered['metadata'] = {'a': '\u00e9', 'z': [1, 2]}
        self.assertEqual(manifest_content_hash(self.manifest), manifest_content_hash(reordered))
        reordered['metadata']['z'].reverse()
        self.assertNotEqual(manifest_content_hash(self.manifest), manifest_content_hash(reordered))

    def test_unicode_not_normalized_and_number_type_preserved(self):
        for first, second in [('\u00e9', 'e\u0301'), (1, 1.0), (0.0, -0.0)]:
            with self.subTest(first=first):
                a, b = copy.deepcopy(self.manifest), copy.deepcopy(self.manifest)
                a['metadata']['value'], b['metadata']['value'] = first, second
                self.assertNotEqual(manifest_content_hash(a), manifest_content_hash(b))

    def test_absent_optional_field_differs_from_empty(self):
        changed = copy.deepcopy(self.manifest)
        changed.pop('tools')
        self.assertNotEqual(manifest_content_hash(self.manifest), manifest_content_hash(changed))

    def test_duplicate_keys_nonfinite_numbers_and_surrogates_refused(self):
        for raw in ['{"a":1,"a":2}', '{"a":{"b":1,"b":2}}', '[NaN]', '[Infinity]',
                    '[-Infinity]', '[1e9999]', '["\\ud800"]']:
            with self.subTest(raw=raw), self.assertRaises(ContentError):
                strict_json_loads(raw)

    def test_non_json_objects_unknown_fields_and_invalid_metadata_refused(self):
        for key, value in [('unknown', 'x'), ('metadata', {1: 'x'}), ('metadata', {'x': float('nan')}),
                           ('metadata', {'x': (1, 2)}), ('metadata', {'x': '\ud800'})]:
            with self.subTest(key=key, value=repr(value)), self.assertRaises(ContentError):
                changed = copy.deepcopy(self.manifest)
                changed[key] = value
                manifest_content_hash(changed)

    def test_fabricated_human_envelope_is_refused_without_live_verifier(self):
        manifest = json.loads((ROOT / 'evals/sync-control-plane/valid-active-manifest.json').read_text())
        self.assertIn('trusted approval verifier and activation context required', validate_manifest_admission(manifest))

    def test_same_declared_hashes_do_not_validate_changed_metadata(self):
        manifest = json.loads((ROOT / 'evals/sync-control-plane/valid-active-manifest.json').read_text())
        manifest['metadata'] = {'new': 'unreviewed'}
        self.assertIn('declared content hash does not match computed content', validate_manifest_admission(manifest))

    def test_malformed_envelopes_return_errors_not_authority(self):
        for value in [[], None, 1, 'approved']:
            with self.subTest(value=value):
                manifest = copy.deepcopy(self.manifest)
                manifest.update(status='active', admission=value)
                self.assertTrue(validate_manifest_admission(manifest))


class ApprovalCrossingTests(unittest.TestCase):
    def test_exact_scoped_review_prepares_projection_without_mutating_candidate(self):
        candidate, _, context, reader, verifier = scenario()
        before = copy.deepcopy(candidate)
        result = prepare_projection(candidate, context, verifier)
        self.assertEqual(before, candidate)
        self.assertEqual('active', result['manifest']['status'])
        self.assertEqual('projection', result['database_verification'])
        self.assertEqual('none', result['authority_effect'])
        self.assertEqual('human.synthetic', result['manifest']['admission']['approved_by'])
        self.assertEqual([], validate_manifest_admission(result['manifest'], verifier=verifier, context=context))
        self.assertEqual(2, reader.calls.count(CENSUS_API))

    def test_unadmitted_policy_stops_before_any_api_resolution(self):
        for field in ('enabled', 'protection_verified'):
            with self.subTest(field=field):
                candidate, _, context, reader, verifier = scenario()
                verifier.policy[field] = False
                with self.assertRaisesRegex(ApprovalError, 'bootstrap required'):
                    verifier.verify(candidate, context)
                self.assertEqual([], reader.calls)

    def test_old_head_review_refused_adjacent_to_valid_review(self):
        candidate, _, context, reader, verifier = scenario()
        reader.data[REVIEW_API]['commit_id'] = 'c' * 40
        with self.assertRaisesRegex(ApprovalError, 'exact-head'):
            verifier.verify(candidate, context)

    def test_missing_ordinary_dismissed_and_bot_reviews_do_not_confer_authority(self):
        for delta in [('body', 'ordinary PR approval'), ('state', 'DISMISSED'),
                      ('state', 'COMMENTED'), ('user', {'id': 999, 'type': 'Bot', 'login': 'synthetic-owner'}),
                      ('user', {'id': 997, 'type': 'User', 'login': 'synthetic-owner'}),
                      ('user', {'id': 999, 'type': 'User', 'login': 'renamed-owner'})]:
            with self.subTest(delta=delta):
                candidate, _, context, reader, verifier = scenario()
                reader.data[REVIEW_API][delta[0]] = delta[1]
                with self.assertRaises(ApprovalError):
                    verifier.verify(candidate, context)

    def test_scope_expansion_refused_one_axis_at_a_time(self):
        for field, value in [('content_hash', '0' * 64), ('environment', 'production'),
                             ('manifest_key', 'agent.other'), ('manifest_path', 'fixtures/other.json'),
                             ('authority_ceiling', 'execute_protected'), ('from_status', 'paused'),
                             ('requested_by', 'agent.other'), ('allowed_actions', ['delete']),
                             ('object_scope', ['everything']), ('base_sha', 'c' * 40)]:
            with self.subTest(field=field):
                candidate, subject, context, reader, verifier = scenario()
                subject[field] = value
                set_subject(reader, subject)
                with self.assertRaisesRegex(ApprovalError, 'scope mismatch'):
                    verifier.verify(candidate, context)

    def test_matching_caller_and_review_cannot_expand_manifest_tools(self):
        candidate, subject, context, reader, verifier = scenario()
        subject['allowed_actions'] = context['allowed_actions'] = ['delete']
        set_subject(reader, subject)
        with self.assertRaisesRegex(ApprovalError, 'capability scope'):
            verifier.verify(candidate, context)

    def test_self_requester_and_pr_author_refused(self):
        for axis in ('principal', 'context_account', 'pr_author'):
            with self.subTest(axis=axis):
                candidate, subject, context, reader, verifier = scenario()
                if axis == 'principal':
                    subject['requested_by'] = context['requested_by'] = 'human.synthetic'
                    set_subject(reader, subject)
                elif axis == 'context_account':
                    context['requester_github_id'] = 999
                else:
                    reader.data[PR_API]['user']['id'] = 999
                with self.assertRaisesRegex(ApprovalError, 'own activation'):
                    verifier.verify(candidate, context)

    def test_expiry_and_not_yet_valid_approval_refused(self):
        for field, value in [('expires_at', '2026-10-04T14:30:00Z'),
                             ('valid_from', '2026-10-04T14:31:00Z')]:
            with self.subTest(field=field, value=value):
                candidate, subject, context, reader, verifier = scenario()
                subject[field] = value
                set_subject(reader, subject)
                with self.assertRaises(ApprovalError):
                    verifier.verify(candidate, context)

    def test_body_composed_before_submission_does_not_backdate_authority(self):
        candidate, subject, context, reader, verifier = scenario()
        subject['valid_from'] = '2026-10-04T13:59:00Z'
        set_subject(reader, subject)
        record = verifier.verify(candidate, context)
        self.assertEqual('2026-10-04T14:00:00Z', record['decided_at'])

    def test_future_provider_submission_cannot_confer_authority(self):
        candidate, _, context, reader, verifier = scenario()
        reader.data[REVIEW_API]['submitted_at'] = '2026-10-04T14:31:00Z'
        with self.assertRaisesRegex(ApprovalError, 'invalid approval validity interval'):
            verifier.verify(candidate, context)

    def test_revocation_and_changes_requested_invalidate_approval(self):
        for state, marker in [('CHANGES_REQUESTED', ''), ('COMMENTED', 'quirk-manifest-revocation')]:
            with self.subTest(state=state):
                candidate, _, context, reader, verifier = scenario()
                other = copy.deepcopy(reader.data[REVIEW_API])
                other.update(id=82, state=state, body=marker, submitted_at='2026-10-04T14:01:00Z')
                reader.data[CENSUS_API].append(other)
                with self.assertRaisesRegex(ApprovalError, 'superseded or revoked'):
                    verifier.verify(candidate, context)
        candidate, _, context, _, verifier = scenario()
        verifier.policy['revoked_review_ids'] = [81]
        with self.assertRaisesRegex(ApprovalError, 'revoked'):
            verifier.verify(candidate, context)

    def test_ambiguous_scoped_approvals_refused(self):
        candidate, _, context, reader, verifier = scenario()
        other = copy.deepcopy(reader.data[REVIEW_API])
        other['id'] = 82
        reader.data[CENSUS_API].append(other)
        with self.assertRaisesRegex(ApprovalError, 'ambiguous'):
            verifier.verify(candidate, context)

    def test_unavailable_api_census_and_partial_results_fail_closed(self):
        for endpoint in (PR_API, REVIEW_API, CENSUS_API):
            with self.subTest(endpoint=endpoint):
                candidate, _, context, reader, verifier = scenario()
                del reader.data[endpoint]
                with self.assertRaises(ApprovalError):
                    verifier.verify(candidate, context)
        candidate, _, context, reader, verifier = scenario()
        reader.data[CENSUS_API] = []
        with self.assertRaisesRegex(ApprovalError, 'no longer current'):
            verifier.verify(candidate, context)

    def test_head_base_and_review_races_refused(self):
        for axis in ('head', 'base', 'review'):
            with self.subTest(axis=axis):
                candidate, _, context, reader, verifier = scenario()
                endpoint = REVIEW_API if axis == 'review' else PR_API
                final = copy.deepcopy(reader.data[endpoint])
                if axis == 'review':
                    final['state'] = 'DISMISSED'
                else:
                    final[axis]['sha'] = 'c' * 40
                reader.change_on_repeat[endpoint] = final
                with self.assertRaisesRegex(ApprovalError, 'changed during verification'):
                    verifier.verify(candidate, context)

    def test_same_commit_identity_races_refused(self):
        for side in ('base', 'head'):
            for field in ('ref', 'repository_name', 'repository_id', 'missing_repository'):
                with self.subTest(side=side, field=field):
                    candidate, _, context, reader, verifier = scenario()
                    final = copy.deepcopy(reader.data[PR_API])
                    if field == 'ref':
                        final[side]['ref'] = 'unprotected'
                    elif field == 'repository_name':
                        final[side]['repo']['full_name'] = 'untrusted/other'
                    elif field == 'repository_id':
                        final[side]['repo']['id'] = 456
                    else:
                        final[side]['repo'] = None
                    reader.change_on_repeat[PR_API] = final
                    with self.assertRaises(ApprovalError):
                        verifier.verify(candidate, context)

    def test_material_limit_checked_before_any_material_read(self):
        from jsonschema import Draft202012Validator
        schema = json.loads((ROOT / 'schemas/manifest-evaluation.schema.json').read_text())
        for count in (32, 33):
            candidate, _, context, reader, verifier = scenario()
            endpoint = ROOT_API + '/contents/' + EVAL_PATH + '?ref=' + HEAD
            record = json.loads(base64.b64decode(reader.data[endpoint]['content']))
            record['materials'] = [{'path': f'fixtures/material-{i}.txt', 'sha256': 'a' * 64}
                                   for i in range(count)]
            errors = list(Draft202012Validator(schema).iter_errors(record))
            self.assertEqual(bool(errors), count > 32)
            reader.data[endpoint]['content'] = base64.b64encode(json.dumps(record).encode()).decode()
            if count == 32:
                material = b'material at limit'
                digest = hashlib.sha256(material).hexdigest()
                for entry in record['materials']:
                    entry['sha256'] = digest
                    reader.data[f"{ROOT_API}/contents/{entry['path']}?ref={HEAD}"] = {
                        'type': 'file', 'encoding': 'base64', 'sha': 'c' * 40,
                        'content': base64.b64encode(material).decode()}
                    reader.data[f'{ROOT_API}/git/trees/{HEAD}?recursive=1']['tree'].append({
                        'path': entry['path'], 'type': 'blob', 'mode': '100644', 'sha': 'c' * 40})
                reader.data[endpoint]['content'] = base64.b64encode(json.dumps(record).encode()).decode()
                verifier.verify(candidate, context)
                self.assertEqual(sum('/contents/fixtures/material-' in call for call in reader.calls), 32)
                self.assertLessEqual(len(reader.calls), MAX_GITHUB_REQUESTS)
            else:
                with self.assertRaisesRegex(ApprovalError, 'invalid manifest evaluation'):
                    verifier.verify(candidate, context)
                self.assertFalse(any('/contents/fixtures/material-' in call for call in reader.calls))

    def test_aggregate_request_budget_and_fresh_verification(self):
        candidate, _, context, reader, verifier = scenario()
        # A transport-independent proof: the cap refuses the 65th call before
        # it reaches even a synthetic authenticated reader.
        for _ in range(MAX_GITHUB_REQUESTS):
            verifier._get(PR_API)
        with self.assertRaisesRegex(ApprovalError, 'request budget'):
            verifier._get(PR_API)
        self.assertEqual(len(reader.calls), MAX_GITHUB_REQUESTS)
        verifier.verify(candidate, context)
        first = verifier._requests
        verifier.verify(candidate, context)
        self.assertEqual(verifier._requests, first)
        self.assertLessEqual(first, MAX_GITHUB_REQUESTS)

    def test_candidate_branch_cannot_install_its_own_codeowners(self):
        candidate, _, context, reader, verifier = scenario()
        endpoint = ROOT_API + '/contents/.github/CODEOWNERS?ref=' + BASE
        reader.data[endpoint]['content'] = base64.b64encode(b'* @untrusted\n').decode()
        with self.assertRaisesRegex(ApprovalError, 'ownership policy changed'):
            verifier.verify(candidate, context)

    def test_candidate_and_evaluation_material_drift_refused(self):
        for path in (MANIFEST_PATH, EVAL_PATH, 'fixtures/raw.txt'):
            with self.subTest(path=path):
                candidate, _, context, reader, verifier = scenario()
                endpoint = ROOT_API + '/contents/' + path + '?ref=' + HEAD
                if path == MANIFEST_PATH:
                    altered = copy.deepcopy(candidate)
                    altered['metadata']['case'] = 'unreviewed'
                    raw = json.dumps(altered).encode()
                elif path == EVAL_PATH:
                    record = json.loads(base64.b64decode(reader.data[endpoint]['content']))
                    record['content_hash'] = 'c' * 64
                    raw = json.dumps(record).encode()
                else:
                    raw = b'changed material'
                reader.data[endpoint]['content'] = base64.b64encode(raw).decode()
                with self.assertRaises(ApprovalError):
                    verifier.verify(candidate, context)

    def test_evidence_cannot_be_detached_from_manifest(self):
        candidate, subject, context, reader, verifier = scenario()
        subject['evidence_refs'] = ['unrelated']
        set_subject(reader, subject)
        with self.assertRaisesRegex(ApprovalError, 'include the manifest evaluation'):
            verifier.verify(candidate, context)

    def test_symlink_submodule_truncated_tree_and_wrong_blob_refused(self):
        for axis in ('symlink', 'submodule', 'truncated', 'blob'):
            with self.subTest(axis=axis):
                candidate, _, context, reader, verifier = scenario()
                tree = reader.data[f'{ROOT_API}/git/trees/{HEAD}?recursive=1']
                if axis == 'truncated':
                    tree['truncated'] = True
                elif axis in ('symlink', 'submodule'):
                    tree['tree'][0]['mode'] = '120000' if axis == 'symlink' else '160000'
                else:
                    reader.data[f'{ROOT_API}/contents/{MANIFEST_PATH}?ref={HEAD}']['sha'] = 'c' * 40
                with self.assertRaises(ApprovalError):
                    verifier.verify(candidate, context)

    def test_copied_approval_envelope_cannot_expand_scope_or_principal(self):
        for field, value in [('approved_by', 'human.other'), ('authority_grant_ref', 'grant.fake'),
                             ('decision_ref', 'decision.fake'), ('evidence_refs', ['evidence.fake'])]:
            with self.subTest(field=field):
                candidate, _, context, _, verifier = scenario()
                projected = prepare_projection(candidate, context, verifier)['manifest']
                projected['admission'][field] = value
                self.assertIn('admission envelope differs from resolved approval',
                              validate_manifest_admission(projected, verifier=verifier, context=context))

    def test_draft_closed_and_forked_prs_refused(self):
        for axis in ('draft', 'closed', 'fork'):
            with self.subTest(axis=axis):
                candidate, _, context, reader, verifier = scenario()
                if axis == 'draft':
                    reader.data[PR_API]['draft'] = True
                elif axis == 'closed':
                    reader.data[PR_API]['state'] = 'closed'
                else:
                    reader.data[PR_API]['head']['repo']['full_name'] = 'foreign/repo'
                with self.assertRaises(ApprovalError):
                    verifier.verify(candidate, context)

    def test_double_blocks_duplicate_subject_keys_and_bad_paths_refused(self):
        for axis in ('double', 'duplicate', 'path'):
            with self.subTest(axis=axis):
                candidate, subject, context, reader, verifier = scenario()
                if axis == 'double':
                    reader.data[REVIEW_API]['body'] *= 2
                elif axis == 'duplicate':
                    reader.data[REVIEW_API]['body'] = body(subject).replace('"repository":', '"repository":"fake/repo", "repository":')
                else:
                    subject['manifest_path'] = context['manifest_path'] = '../candidate.json'
                    set_subject(reader, subject)
                with self.assertRaises(ApprovalError):
                    verifier.verify(candidate, context)

    def test_reader_never_uses_caller_origin_or_follows_redirects(self):
        reader = GitHubReader('synthetic-token')
        for endpoint in ('https://attacker.test/repos/x', '/repos/x/../y', '/repos/x#secret'):
            with self.subTest(endpoint=endpoint), self.assertRaises(ApprovalError):
                reader.get(endpoint)
        from sync_control_plane.attestation import _NoRedirects
        self.assertIsNone(_NoRedirects().redirect_request(None, None, 302, '', {}, 'https://attacker.test'))


class PreparationCliTests(unittest.TestCase):
    def test_hash_only_is_useful_without_granting_admission(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/manifest_admission.py'),
                                 str(ROOT / 'evals/sync-control-plane/valid-active-manifest.json')],
                                capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        record = json.loads(result.stdout)
        self.assertFalse(record['admission_verified'])
        self.assertEqual('none', record['authority_effect'])

    def test_failed_run_replaces_old_projection_with_blocked_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / 'bad.json', Path(directory) / 'result.json'
            source.write_text('{}')
            output.write_text('{"status":"pass"}')
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/manifest_admission.py'),
                                     str(source), '--output', str(output)], capture_output=True)
            self.assertEqual(1, result.returncode)
            self.assertEqual('blocked', json.loads(output.read_text())['status'])

    def test_output_alias_does_not_destroy_source(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.json'
            source.write_text('{}')
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/manifest_admission.py'),
                                     str(source), '--output', str(source)], capture_output=True)
            self.assertEqual(1, result.returncode)
            self.assertEqual('{}', source.read_text())


class ProjectionWorkflowTests(unittest.TestCase):
    def test_candidate_policy_cannot_admit_itself(self):
        policy = strict_json_loads((ROOT / 'policies/manifest-verifier-policy.candidate.json').read_bytes())
        self.assertIs(policy['enabled'], False)
        self.assertIs(policy['protection_verified'], False)

    def test_projection_proof_removal_and_cutover_collapse_fail_conformance(self):
        import yaml
        from validate_sync_control_plane import projection_job_checks
        live = yaml.safe_load((ROOT / '.github/workflows/sync-control-plane-conformance.yml').read_text())
        self.assertTrue(all(projection_job_checks(ROOT / '.github/workflows/sync-control-plane-conformance.yml').values()))
        for marker, check in [
            ('-f supabase/tests/manifest_verified_projection.sql', 'ci_runs_verified_projection_cases'),
            ('manifest_verified_projection.cutover.sql', 'ci_proves_legacy_projection_cutover_refusal'),
            (' > "20261004140000"', 'ci_stages_projection_cutover'),
        ]:
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as directory:
                workflow = copy.deepcopy(live)
                for step in workflow['jobs']['database-guard']['steps']:
                    step['run'] = str(step.get('run', '')).replace(marker, 'removed')
                path = Path(directory) / 'workflow.yml'
                path.write_text(yaml.safe_dump(workflow))
                self.assertFalse(projection_job_checks(path)[check])

    def test_new_paths_are_reachable_by_the_workflow(self):
        import yaml
        from validate_sync_control_plane import projection_job_checks
        workflow = yaml.safe_load((ROOT / '.github/workflows/sync-control-plane-conformance.yml').read_text())
        trigger = workflow.get(True) or workflow['on']
        trigger['pull_request']['paths'].remove('tests/test_manifest_admission.py')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'workflow.yml'
            path.write_text(yaml.safe_dump(workflow))
            self.assertFalse(projection_job_checks(path)['ci_paths_cover_projection_inputs'])


if __name__ == '__main__':
    unittest.main()
