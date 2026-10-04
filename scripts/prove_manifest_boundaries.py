#!/usr/bin/env python3
"""Focused, synthetic executable crossing proof; never admission or live approval."""
from __future__ import annotations
import copy
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from test_manifest_admission import scenario, REVIEW_API
from sync_control_plane.attestation import ApprovalError
from sync_control_plane.projection import prepare_projection


def main():
    output = ROOT / 'evals/sync-control-plane'
    files = ['scripts/sync_control_plane/attestation.py', 'scripts/sync_control_plane/content.py',
             'scripts/sync_control_plane/policy.py', 'scripts/sync_control_plane/projection.py',
             'schemas/manifest-approval-attestation.schema.json', 'schemas/manifest-evaluation.schema.json',
             'schemas/runtime-manifest.schema.json', 'tests/test_manifest_admission.py',
             'scripts/prove_manifest_boundaries.py']
    versions = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files}
    implementation = 'sha256:' + hashlib.sha256(json.dumps(versions, sort_keys=True).encode()).hexdigest()
    executed = datetime.now(timezone.utc).isoformat()
    receipts, cases = [], []
    fields = ['boundary_id', 'contract_version', 'decision', 'reason_codes', 'subject', 'object_hash',
              'purpose', 'authority_source_ids', 'decided_at', 'enforcement_point', 'side_effects']
    axes = {'subject': 'agent.synthetic', 'object_ref': 'filled below', 'source_state': 'candidate',
            'target_state_or_surface': 'in-memory proposed active projection', 'direction': 'candidate_to_proposal',
            'purpose': 'test the approved candidate predicate', 'capability': 'prepare_projection',
            'authority': 'synthetic scoped review at current head', 'evidence': 'synthetic evaluation and raw material',
            'environment': 'unit-test MemoryReader; no network or database', 'time': 'frozen 2026-10-04T14:30:00Z',
            'representation': 'Python API result with authority_effect none'}
    for name, role, outcome in [('exact-review','just_inside','ALLOW'), ('old-review','just_outside','DENY')]:
        candidate, _, context, reader, verifier = scenario()
        before = copy.deepcopy(candidate)
        if role == 'just_outside':
            reader.data[REVIEW_API]['commit_id'] = 'c' * 40
        observed, reason = 'ALLOW', 'BOUNDARY_ALLOW_EXACT'
        try:
            result = prepare_projection(candidate, context, verifier)
            assert result['authority_effect'] == 'none'
            assert result['database_verification'] == 'projection'
        except ApprovalError as error:
            assert 'exact-head' in str(error), str(error)
            observed, reason = 'DENY', 'APPROVAL_HASH_MISMATCH'
        assert observed == outcome
        assert candidate == before
        frozen = dict(axes, object_ref=candidate['manifest_key']+'@sha256:'+candidate['content_hash'])
        if role == 'just_outside':
            frozen['authority'] = 'synthetic scoped review at old head'
        receipt_id = 'receipt.' + name
        receipts.append({'receipt_id':receipt_id,'boundary_id':'boundary.manifest-review-proposal','contract_version':'0.1.0',
                         'decision':observed,'reason_codes':[reason],'subject':frozen['subject'],
                         'object_hash':candidate['content_hash'],'purpose':frozen['purpose'],
                         'authority_source_ids':['authority.approved-design'], 'decided_at':executed,
                         'enforcement_point':'prepare_projection / GitHubApprovalVerifier with MemoryReader',
                         'side_effects':['in_memory_projection_returned'] if outcome == 'ALLOW' else [], 'candidate_unchanged':True,'database_calls':0,'network_calls':0})
        cases.append({'case_id':name,'boundary_id':'boundary.manifest-review-proposal','test_role':role,
                      'pair_id':'pair.exact-head','title':name,'axes':frozen,'varied_axes':['authority'],
                      'expected':{'outcome':outcome,'reason_codes':[reason],'permitted_side_effects':['in_memory_projection_returned'] if outcome == 'ALLOW' else [],
                                  'forbidden_side_effects':['database_write','live_admission','candidate_mutation'],
                                  'required_receipt_fields':fields,'fallback':'hash-only inspection remains available'},
                      'generic_control_false_positive':'APPROVED plus a human role would accept the stale commit binding',
                      'observed':{'outcome':observed,'receipt_id':receipt_id,'evidence_refs':['filled below'],'side_effects':['in_memory_projection_returned'] if outcome == 'ALLOW' else []}})
    receipt_path = output / 'manifest-boundary-crossings.json'
    receipt_path.write_text(json.dumps({'authority_effect':'none','clock':'synthetic frozen clock',
                                      'implementation_ref':implementation,'file_sha256':versions,'receipts':receipts},indent=2)+'\n')
    evidence_ref = 'evals/sync-control-plane/manifest-boundary-crossings.json@sha256:' + hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    for case in cases:
        case['observed']['evidence_refs'] = [evidence_ref]
    boundary = {'boundary_id':'boundary.manifest-review-proposal','name':'Exact reviewed content to proposed runtime envelope',
                'protected_interest':'human activation authority and truthful evidence','costly_default':'human-shaped strings accepted as consent',
                'authority_source_ids':['authority.approved-design'],'dimensions':['delegation_approval','claim_evidence'],
                'source_domain':'candidate','target_domain':'in-memory proposal','direction':'candidate_to_proposal',
                'predicate':{'expression':'Resolve exact-head scoped independent human review, compute content and bind evidence; prepare only',
                             'enforcement':'fail_closed'},
                'behaviors':{'inside':'return an in-memory envelope with authority_effect none','outside':'refuse with no mutation',
                             'ambiguous':'refuse and route a bounded decision to the host owner','degraded':'return only computed content identity'},
                'override':{'authority':'Bryan for design; admitted independent human for activation',
                            'binding_axes':['object_ref','purpose','environment','time','representation'],
                            'resume_behavior':'re-evaluate after a new exact scoped approval; no bypass'},
                'revocation':{'invalidates_receipts':True,'derivative_behavior':'deny'},'receipt_fields':fields,
                'enforcement_surfaces':['prepare_projection','GitHubApprovalVerifier'],
                'non_goals':['live GitHub authenticity demonstration','database independence','admission','consumer expiry enforcement'],
                'invalidators':['implementation/profile/ownership/subject/environment/approval/evidence changes']}
    bundle = {'bundle_id':'boundary-bundle.manifest-review-proposal','version':'0.1.0','status':'candidate',
              'proof_profile':'demonstration','coverage_profile':'focused','authority_basis':'declared',
              'authority_ceiling':{'may':['inspect','test','propose'],'may_not':['self_admit','activate','merge','deploy','grant_authority','canonize','infer_consent']},
              'authority_sources':[{'source_id':'authority.approved-design','kind':'human_rule','owner':'Bryan',
                                    'version':'approved-design-2026-10-04','locator':'decisions/ADR-0002-manifest-approval-trust-root.md approval record',
                                    'scope':['candidate implementation and synthetic testing'],'status':'declared','precedence':100}],
              'boundaries':[boundary],'cases':cases,
              'proof':{'verdict':'demonstrated','implementation_ref':implementation,'executed_at':executed,'evidence':[evidence_ref],
                       'replay_method':'CPython 3.13: python scripts/prove_manifest_boundaries.py; validate with demonstrate-quirk-boundaries validator',
                       'limitations':['focused synthetic predicate proof only','no actual human consent or protected host installed',
                                      'PostgreSQL proof is separately run in CI; this proof has no DB connection',
                                      'full eight-role and representation conservation proof is not claimed'],
                       'invalidators':['any listed implementation digest changes','policy/subject/approval/environment/evidence drift']}}
    path = output / 'manifest-boundary-proof.json'
    path.write_text(json.dumps(bundle,indent=2)+'\n')
    print(json.dumps({'verdict':'demonstrated','coverage':'focused synthetic','implementation_ref':implementation,'authority_effect':'none'}))


if __name__ == '__main__':
    main()
