import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {compareReviewRequests,verifyReviewChanges,renderReviewChanges} from '../src/changes.mjs';
import {digestJSON} from '../src/core.mjs';

const fixture=JSON.parse(await readFile(new URL('../fixtures/review-request.json',import.meta.url),'utf8'));
const copy=value=>JSON.parse(JSON.stringify(value));
const request=()=>({...copy(fixture),entries:copy(fixture.entries.slice(0,3))});
const single=()=>({...request(),entries:[copy(fixture.entries[0])]});
const rowAt=(result,ref='fixture:review:os')=>result.rows.find(row=>row.source_ref===ref);
const assertAuthority=authority=>{
  assert.equal(authority.maximum_right,'propose');
  assert.equal(authority.human_review_required,true);
  for(const key of ['effect_execution_allowed','calendar_write_allowed','canon_promotion_allowed','graph_application_allowed','training_allowed'])assert.equal(authority[key],false);
};

test('unchanged requests reproduce exactly without changing inputs or claiming benefit',()=>{
  const before=request(),after=copy(before),beforeDigest=digestJSON(before),afterDigest=digestJSON(after);
  const result=compareReviewRequests(before,after);
  assert.deepEqual(result.counts,{sources:3,unchanged:3,added:0,removed:0,replaced:0,changed:0,proposed_repairs:0});
  assert.ok(result.rows.every(row=>row.proposed_repair===null));
  assert.deepEqual(verifyReviewChanges(before,after,result),result);
  assert.deepEqual(compareReviewRequests(before,after),result);
  assert.equal(digestJSON(before),beforeDigest);assert.equal(digestJSON(after),afterDigest);
  assert.equal(result.receipt.observed_human_benefit,null);assertAuthority(result.authority);
});

test('changed source binding carries claim labels only as assertions requiring revalidation',()=>{
  const before=single(),after=copy(before),entry=after.entries[0];
  entry.record.subject.version='next-source-version';entry.record.subject.digest=digestJSON('next-source');
  entry.expectation.subject=copy(entry.record.subject);
  entry.record.evidence.satisfied.push('newly_asserted_check');
  const result=compareReviewRequests(before,after),row=rowAt(result);
  assert.equal(row.change,'replaced');assert.equal(row.after.reason,'expectation_matched');
  assert.ok(row.changed_fields.includes('subject'));assert.ok(row.changed_fields.includes('expectation'));
  assert.deepEqual(row.claims_requiring_revalidation,before.entries[0].record.evidence.satisfied);
  assert.ok(!row.claims_requiring_revalidation.includes('newly_asserted_check'));
  assert.equal(row.proposed_repair.action,'revalidate_source_claims');
  assert.equal(row.proposed_repair.effect_execution_allowed,false);assertAuthority(result.authority);
});

test('record identity and complete scope changes are replacements even with unchanged source digest',()=>{
  for(const mutate of [entry=>entry.record.id='replacement-projection',entry=>entry.record.scope.id='new-scope',entry=>entry.record.scope.description='Changed scope meaning']){
    const before=single(),after=copy(before);mutate(after.entries[0]);
    const row=rowAt(compareReviewRequests(before,after));
    assert.equal(row.change,'replaced');assert.equal(row.proposed_repair.action,'revalidate_source_claims');
    assert.deepEqual(row.claims_requiring_revalidation,before.entries[0].record.evidence.satisfied);
  }
});

test('exact-ref rename yields removed and added sources without declaring work completed',()=>{
  const before=single(),after=copy(before);after.entries[0].source_ref='fixture:renamed';
  const result=compareReviewRequests(before,after),removed=rowAt(result),added=rowAt(result,'fixture:renamed');
  assert.equal(result.counts.removed,1);assert.equal(result.counts.added,1);
  assert.equal(removed.after,null);assert.equal(removed.after_count,null);
  assert.equal(removed.proposed_repair.action,'account_for_removed_source');
  assert.equal(added.before,null);assert.equal(added.proposed_repair.action,'review_added_source');
  for(const hold of before.entries[0].record.authority.upstream_hold_refs)assert.ok(result.authority.upstream_hold_refs.includes(hold));
});

test('expectation reference, binding, and absence are explicit even when record bytes do not change',()=>{
  for(const [mutate,reason,action] of [
    [entry=>entry.expectation.source_ref='fixture:another-observer','expectation_matched','verify_recapture'],
    [entry=>entry.expectation.subject.version='unmatched-version','subject_mismatch','reinspect_source'],
    [entry=>entry.expectation=null,'expectation_missing','obtain_source_expectation']
  ]){
    const before=single(),after=copy(before);mutate(after.entries[0]);
    const row=rowAt(compareReviewRequests(before,after));
    assert.equal(row.before.input_digest,row.after.input_digest);assert.ok(row.changed_fields.includes('expectation'));
    assert.equal(row.after.reason,reason);assert.equal(row.proposed_repair.action,action);
  }
});

test('count and age policy changes remain policy assertions despite improved review disposition',()=>{
  const before=single(),after=copy(before);after.entries[0].max_count=100;
  let result=compareReviewRequests(before,after),row=rowAt(result);
  assert.ok(row.changed_fields.includes('max_count'));assert.equal(row.proposed_repair.action,'review_policy_change');
  assert.equal(row.after_count,'At least 6; total unknown');assertAuthority(result.authority);
  before.max_age_seconds=0;before.captured_at='2026-09-10T00:30:00.000Z';
  const relaxed=copy(before);relaxed.max_age_seconds=3600;
  result=compareReviewRequests(before,relaxed);row=rowAt(result);
  assert.equal(row.before.reason,'stale_capture');assert.equal(row.after.reason,'expectation_matched');
  assert.deepEqual(result.context_changes,['max_age_seconds']);assert.ok(row.changed_fields.includes('max_age_seconds'));
  assert.equal(row.proposed_repair.action,'review_policy_change');assertAuthority(result.authority);
});

test('time passage changes freshness and recapture does not establish newly verified evidence',()=>{
  const before=single(),aged=copy(before);aged.captured_at='2026-09-10T02:00:00.000Z';
  let result=compareReviewRequests(before,aged),row=rowAt(result);
  assert.deepEqual(result.context_changes,['captured_at']);assert.equal(row.before.input_digest,row.after.input_digest);
  assert.equal(row.after.reason,'stale_capture');assert.equal(row.proposed_repair.action,'reinspect_source');
  const recaptured=copy(aged);recaptured.entries[0].record.provenance.captured_at=aged.captured_at;
  recaptured.entries[0].expectation.observed_at=aged.captured_at;
  result=compareReviewRequests(aged,recaptured);row=rowAt(result);
  assert.equal(row.before.reason,'stale_capture');assert.equal(row.after.reason,'expectation_matched');
  assert.ok(row.changed_fields.includes('provenance'));assert.ok(row.changed_fields.includes('expectation'));
  assert.equal(row.proposed_repair.action,'verify_recapture');assert.equal(result.receipt.observed_human_benefit,null);
  assert.ok(result.receipt.limitations.some(text=>text.includes('does not establish refreshed evidence')));
});

test('knowledge evidence work and availability changes are separate and cannot upgrade authority',()=>{
  for(const [field,mutate] of [
    ['knowledge',record=>record.knowledge.lower_bound=7],
    ['evidence',record=>record.evidence.missing.push('additional_unverified_obligation')],
    ['work',record=>record.work.remaining_units.push('additional_work')],
    ['availability',record=>record.availability.unverified.push('additional_input')]
  ]){
    const before=single(),after=copy(before);mutate(after.entries[0].record);
    const result=compareReviewRequests(before,after),row=rowAt(result);
    assert.equal(row.change,'changed');assert.deepEqual(row.changed_fields,[field]);
    assert.equal(row.proposed_repair.action,'review_record_change');assertAuthority(result.authority);
  }
});

test('removed holds stay in aggregate authority and added holds remain visible',()=>{
  const before=single(),after=copy(before),oldHold=after.entries[0].record.authority.upstream_hold_refs.shift();
  after.entries[0].record.authority.upstream_hold_refs.push('fixture:new-hold');
  const result=compareReviewRequests(before,after),row=rowAt(result);
  assert.deepEqual(row.removed_holds,[oldHold]);assert.deepEqual(row.added_holds,['fixture:new-hold']);
  assert.ok(result.authority.upstream_hold_refs.includes(oldHold));assert.ok(result.authority.upstream_hold_refs.includes('fixture:new-hold'));
  assert.equal(row.proposed_repair.action,'review_hold_removal');assertAuthority(result.authority);
});

test('invalid records remain opaque while prior valid holds and unknown obligations remain unresolved',()=>{
  const before=single(),after=copy(before);
  after.entries[0].record={private_note:'untrusted-private-payload',authority:{upstream_hold_refs:['malformed-secret-hold'],effect_execution_allowed:true}};
  const result=compareReviewRequests(before,after),row=rowAt(result),html=renderReviewChanges(before,after);
  assert.equal(row.after.reason,'invalid_record');assert.deepEqual(row.changed_fields,['record','review_accounting']);
  assert.equal(row.after_count,null);assert.equal(row.proposed_repair.action,'repair_native_input');
  assert.ok(result.authority.upstream_hold_refs.includes('changes:invalid_input_unresolved'));
  for(const hold of before.entries[0].record.authority.upstream_hold_refs)assert.ok(result.authority.upstream_hold_refs.includes(hold));
  assert.ok(!JSON.stringify(result).includes('untrusted-private-payload'));assert.ok(!html.includes('malformed-secret-hold'));
  assert.ok(!html.includes('untrusted-private-payload'));assertAuthority(result.authority);
});

test('disjoint maximum-size requests preserve all 64 source rows without summing domain counts',()=>{
  const before=single(),after=single(),entry=copy(before.entries[0]);
  before.entries=Array.from({length:32},(_,i)=>({...copy(entry),source_ref:`fixture:before:${i}`}));
  after.entries=Array.from({length:32},(_,i)=>({...copy(entry),source_ref:`fixture:after:${i}`}));
  const result=compareReviewRequests(before,after);
  assert.equal(result.rows.length,64);assert.equal(result.counts.sources,64);
  assert.equal(result.counts.removed,32);assert.equal(result.counts.added,32);
  assert.equal(result.counts.proposed_repairs,64);assert.ok(!Object.hasOwn(result.counts,'exact'));
  assert.ok(result.rows.every(row=>(row.before_count??row.after_count)==='At least 6; total unknown'));
  verifyReviewChanges(before,after,result);
});

test('temporal regression rejects comparison and future capture remains quarantined',()=>{
  const before=single(),after=copy(before);after.captured_at='2026-09-09T23:59:59.000Z';
  assert.throws(()=>compareReviewRequests(before,after),/After capture precedes/);
  after.captured_at=before.captured_at;after.entries[0].expectation.observed_at='2026-09-11T00:00:00.000Z';
  const row=rowAt(compareReviewRequests(before,after));
  assert.equal(row.after.reason,'future_capture');assert.equal(row.proposed_repair.action,'reinspect_source');
});

test('prototype-like refs stay literal, HTML is escaped, and accessor data is rejected without invocation',()=>{
  const before=request();['__proto__','constructor','<img src=x onerror=alert(1)>'].forEach((ref,i)=>before.entries[i].source_ref=ref);
  const after=copy(before);after.entries[0].record.knowledge.lower_bound=7;
  const result=compareReviewRequests(before,after),html=renderReviewChanges(before,after);
  assert.equal(result.rows.length,3);assert.ok(rowAt(result,'__proto__'));assert.ok(rowAt(result,'constructor'));
  assert.ok(html.includes('&lt;img src=x onerror=alert(1)&gt;'));assert.ok(!/<img|<script|<form|<iframe/i.test(html));
  const hostile=single();let invoked=0;Object.defineProperty(hostile.entries[0].record,'knowledge',{enumerable:true,get(){invoked++;return {};}});
  assert.throws(()=>compareReviewRequests(single(),hostile),/JSON data property required/);assert.equal(invoked,0);
});

test('receipt row authority and repair tampering fails full request replay',()=>{
  const before=single(),after=copy(before);after.entries[0].record.knowledge.lower_bound=7;
  for(const mutate of [
    result=>result.receipt.output_digest=digestJSON('forged'),
    result=>result.rows[0].after_count='7 confirmed within this scope',
    result=>result.authority.effect_execution_allowed=true,
    result=>result.rows[0].proposed_repair.effect_execution_allowed=true,
    result=>result.rows[0].proposed_repair.action='reinspect_source'
  ]){
    const result=compareReviewRequests(before,after);mutate(result);
    assert.throws(()=>verifyReviewChanges(before,after,result));
  }
  const result=compareReviewRequests(before,after),different=copy(after);different.entries[0].record.knowledge.lower_bound=8;
  assert.throws(()=>verifyReviewChanges(before,different,result),/does not reproduce/);
});

test('duplicate reordering compares representative refs rather than positional indices',()=>{
  const before=single();before.entries.push({...copy(before.entries[0]),source_ref:'fixture:duplicate'});
  const after=copy(before);after.entries.reverse();
  const result=compareReviewRequests(before,after),original=rowAt(result),duplicate=rowAt(result,'fixture:duplicate');
  assert.equal(original.before.disposition,'matched');assert.equal(original.after.disposition,'duplicate');
  assert.equal(original.after.duplicate_source_ref,'fixture:duplicate');
  assert.equal(duplicate.before.duplicate_source_ref,'fixture:review:os');assert.equal(duplicate.after.disposition,'matched');
  for(const row of result.rows){assert.deepEqual(row.changed_fields,['review_accounting']);assert.equal(row.before.input_digest,row.after.input_digest);assert.equal(row.change,'changed');}
  const stable=request();stable.entries.reverse();
  assert.ok(compareReviewRequests(request(),stable).rows.every(row=>row.change==='unchanged'));
});

test('conflicting duplicates remain quarantined and disappearance does not approve the survivor',()=>{
  const before=single(),conflict={...copy(before.entries[0]),source_ref:'fixture:conflict'};
  conflict.record.knowledge.lower_bound=7;conflict.record.authority.upstream_hold_refs.push('fixture:conflict-hold');
  before.entries.push(conflict);const after=single();
  const result=compareReviewRequests(before,after),survivor=rowAt(result),removed=rowAt(result,'fixture:conflict');
  assert.equal(survivor.before.reason,'identity_conflict');assert.equal(survivor.after.reason,'expectation_matched');
  assert.equal(removed.before.reason,'identity_conflict');assert.equal(removed.change,'removed');
  assert.equal(removed.proposed_repair.action,'account_for_removed_source');
  assert.ok(result.authority.upstream_hold_refs.includes('fixture:conflict-hold'));
  assert.equal(survivor.proposed_repair.effect_execution_allowed,false);assertAuthority(result.authority);
});
