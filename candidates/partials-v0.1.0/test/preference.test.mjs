import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync, writeFileSync, mkdtempSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {fromPreferenceInspection, PREFERENCE_SOURCE_HEAD} from '../adapters/preference.mjs';
import {prepareImageReference} from './upstream/preference/src/intake.mjs';

const fixture = JSON.parse(readFileSync(new URL('./upstream/preference/fixtures/producer-event.json',import.meta.url)));
const capturedAt = '2026-09-10T00:00:00.000Z';
const canonical = v => v === null || typeof v !== 'object' ? JSON.stringify(v) : Array.isArray(v) ? '['+v.map(canonical).join(',')+']' : '{'+Object.keys(v).sort().map(k => JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';
const hash = v => createHash('sha256').update(v).digest('hex');
function modifiedRecord(mutate) {
  const row = structuredClone(fixture), payload = JSON.parse(row.payload_json);
  mutate(payload);
  row.outcome = payload.judgment.outcome;
  row.rationale = payload.judgment.rationale;
  row.payload_json = canonical(payload);
  row.payload_digest = hash(row.payload_json);
  return row;
}
function inspectRows(rows, {page=0,hasMore=false,sections={}}={}) {
  const input = {schemaVersion:'quirk.image-workspace-export.v0.1',status:'unsigned_candidate',signature:null,page,limit:100,image_preference_events:{hasMore,rows},graph:{state:'AWAITING_INTEGRATION',accepted:0},...sections};
  const directory = mkdtempSync(join(tmpdir(),'quirk-preference-inspection-'));
  try {
    const path = join(directory,'input.json');
    writeFileSync(path,JSON.stringify(input));
    let output;
    try { output = execFileSync(process.execPath,[fileURLToPath(new URL('./upstream/preference/scripts/inspect.mjs',import.meta.url)),path],{encoding:'utf8'}); }
    catch (error) { if(error.status !== 2 || !error.stdout) throw error; output = error.stdout; }
    return JSON.parse(output);
  } finally { rmSync(directory,{recursive:true,force:true}); }
}
const project = input => fromPreferenceInspection(input,{capturedAt});

test('upstream snapshots are byte-identical to GitHub blob identities at pinned head', () => {
  assert.equal(PREFERENCE_SOURCE_HEAD,'f70a713c097436172760d633ccee9bacb071483b');
  const sources = {
    'src/intake.mjs':'10004fc5b063f8d822cc12a9140ca2af443e27c0',
    'src/json.mjs':'c8e1effb9e87be87f5aa3da1a8f2416bfe79ae0d',
    'scripts/inspect.mjs':'38c0c31af15e69413372ef5dbe74f168737ebd9f',
    'schemas/image-event-record.schema.json':'35f68fba149f9f4f9e410e0b708f22a2d39a0fcf',
    'fixtures/producer-event.json':'6bea1fb045e7869cfd570ca4411538456dcc4ec0',
  };
  for (const [path, expected] of Object.entries(sources)) {
    const bytes = readFileSync(new URL('./upstream/preference/'+path,import.meta.url));
    const actual = createHash('sha1').update(`blob ${bytes.length}\0`).update(bytes).digest('hex');
    assert.equal(actual,expected,path);
  }
});

test('real pinned producer and CLI output project with explicit limited evidence', () => {
  const source = prepareImageReference(fixture);
  assert.equal(source.reference.spec.lineage_status,'INCLUDED_REFERENCES_CONSISTENT');
  const input = inspectRows([fixture]);
  const before = structuredClone(input), result = project(input);
  assert.deepEqual(input,before,'adapter must not change native evidence');
  assert.equal(result.knowledge.lower_bound,1);
  assert.equal(result.knowledge.exact,null);
  assert.equal(result.knowledge.status,'partial');
  assert.equal(result.authority.graph_application_allowed,false);
  assert.equal(result.authority.training_allowed,false);
  assert.equal(result.authority.effect_execution_allowed,false);
  assert.equal(result.authority.human_review_required,true);
  assert.equal(result.availability.missing.length,0);
  assert.equal(result.availability.unverified.filter(x=>x.startsWith('image_bytes:')).length,2);
  assert.ok(result.evidence.missing.includes('verified_human_origin'));
  assert.ok(result.evidence.missing.includes('observed_human_benefit'));
});

test('unresolved parent remains explicit even when event metadata is valid', () => {
  const parentId = 'c'.repeat(64);
  const row = modifiedRecord(payload => { payload.assets[0].parentId = parentId; });
  assert.equal(prepareImageReference(row).reference.spec.lineage_status,'PARTIAL');
  const result = project(inspectRows([row]));
  assert.deepEqual(result.availability.missing,[`lineage_parent:${parentId}`]);
  assert.equal(result.knowledge.exact,null);
});

test('last page does not establish a full export or exact total', () => {
  const result = project(inspectRows([fixture],{page:4,hasMore:false}));
  assert.equal(result.knowledge.exact,null);
  assert.equal(result.knowledge.upper_bound,null);
  assert.ok(result.work.remaining_units.includes('verify_complete_export'));
});

test('empty page preserves unknown full count rather than inventing zero preferences', () => {
  const result = project(inspectRows([]));
  assert.equal(result.knowledge.exact,null);
  assert.equal(result.knowledge.status,'unknown');
  assert.equal(result.knowledge.lower_bound,null);
});

test('exact replay is counted once and keeps document-local replay limitation', () => {
  const input = inspectRows([fixture,fixture]);
  assert.equal(input.counts.exact_replays,1);
  const result = project(input);
  assert.equal(result.knowledge.lower_bound,1);
  assert.equal(result.knowledge.known_items.length,1);
  assert.ok(result.work.completed_units.some(x=>x.endsWith('EXACT_REPLAY')));
  assert.ok(result.evidence.limitations.some(x=>x.includes('this document only')));
});

test('rejected rows remain visible without discarding valid rows', () => {
  const invalid = structuredClone(fixture); invalid.payload_digest = '0'.repeat(64);
  const result = project(inspectRows([fixture,invalid]));
  assert.equal(result.knowledge.lower_bound,1);
  assert.equal(result.work.status,'partial');
  assert.deepEqual(result.work.failed_units,['row:1:PAYLOAD_DIGEST_MISMATCH']);
});

test('all rejected rows do not claim successful preference evidence', () => {
  const invalid = structuredClone(fixture); invalid.payload_digest = '0'.repeat(64);
  const result = project(inspectRows([invalid]));
  assert.equal(result.work.status,'failed');
  assert.equal(result.knowledge.exact,null);
  assert.deepEqual(result.knowledge.known_items,[]);
});

test('uninspected sections and further pages are preserved separately', () => {
  const result = project(inspectRows([fixture],{hasMore:true,sections:{image_jobs:{hasMore:false,rows:[]}}}));
  assert.ok(result.availability.unverified.includes('section:image_jobs'));
  assert.ok(result.work.remaining_units.includes('inspect_remaining_event_pages'));
});

test('both, neither and skip retain null relation proposals', () => {
  for (const outcome of ['both','neither','skip']) {
    const row = modifiedRecord(payload => { payload.judgment.outcome = outcome; Object.assign(payload.graphProposal,{relation:null,from:null,to:null}); });
    const result = project(inspectRows([row]));
    assert.equal(result.authority.graph_application_allowed,false);
    assert.equal(result.knowledge.lower_bound,1);
  }
});

test('missing and contradictory native fields are rejected instead of defaulted', () => {
  const input = inspectRows([fixture]);
  for (const mutate of [
    x=>{delete x.counts;},x=>{x.counts.new_candidates=0;},x=>{x.results[0].index=1;},
    x=>{x.has_more_events=null;},x=>{x.results[0].disposition='EXACT_REPLAY';x.counts={new_candidates:0,exact_replays:1,rejected:0};},
    x=>{x.results[0].reference.spec.unresolved_parent_ids=['c'.repeat(64)];},
  ]) { const bad=structuredClone(input); mutate(bad); assert.throws(()=>project(bad),/Invalid pinned Preference inspection/); }
});

test('completion and authority escalation cannot enter through native claims', () => {
  const input = inspectRows([fixture]);
  for (const mutate of [
    x=>{x.complete_export_verified=true;},x=>{x.graph_delivery='APPLIED';},x=>{x.source_authenticity='VERIFIED';},
    x=>{x.replay_scope='GLOBAL';},x=>{x.results[0].reference.spec.applied=true;},
    x=>{x.results[0].reference.spec.model_training_allowed=true;},x=>{x.results[0].reference.spec.human_origin='VERIFIED';},
    x=>{x.results[0].reference.spec.observed_benefit={helpful:true};},x=>{x.results[0].reference.spec.proposed_relation.autoApply=true;},
    x=>{x.results[0].reference.authority.maximum_runtime_right='execute';},
  ]) { const bad=structuredClone(input); mutate(bad); assert.throws(()=>project(bad),/Invalid pinned Preference inspection/); }
});

test('a provenance capture timestamp is required and never fabricated', () => {
  const input=inspectRows([fixture]);
  assert.throws(()=>fromPreferenceInspection(input),/capturedAt/);
  assert.throws(()=>fromPreferenceInspection(input,{capturedAt:'not-a-date'}),/capturedAt/);
});

test('non-JSON inputs are rejected before evaluating accessor code', () => {
  let accessed = false;
  const getterInput = {};
  Object.defineProperty(getterInput,'schema_version',{enumerable:true,get(){accessed=true;return 'quirk.image-intake-inspection.v0.1';}});
  assert.throws(()=>project(getterInput),/JSON data property/);
  assert.equal(accessed,false);
  assert.throws(()=>project(Object.create({schema_version:'quirk.image-intake-inspection.v0.1'})),/plain JSON object/);
  assert.throws(()=>project({[Symbol('hidden')]:true}),/symbol properties/);
  const input=inspectRows([fixture]),options={};
  Object.defineProperty(options,'capturedAt',{enumerable:true,get(){accessed=true;return capturedAt;}});
  assert.throws(()=>fromPreferenceInspection(input,options),/JSON data property/);
  assert.equal(accessed,false);
});
