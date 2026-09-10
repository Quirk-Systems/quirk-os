import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {buildDecisionContext,buildUnsignedDecision,verifyUnsignedDecision} from '../src/decision.mjs';
import {assertDecisionContext,buildUnsignedDecision as browserBuild,DECISION_LIMITS} from '../src/decision-model.mjs';
import {compareReviewRequests} from '../src/changes.mjs';
import {digestJSON} from '../src/core.mjs';

const fixture=JSON.parse(await readFile(new URL('../fixtures/review-request.json',import.meta.url),'utf8'));
const copy=value=>JSON.parse(JSON.stringify(value));
function requests(){const before={...copy(fixture),entries:copy(fixture.entries.slice(0,3))},after=copy(before);after.entries[0].record.knowledge.lower_bound=7;return {before,after};}
function setup(){const {before,after}=requests();return {before,after,context:buildDecisionContext(before,after)};}
function answer(context,response='selected'){
  const option=context.options[0];return {source_ref:option.source_ref,response,rationale:'This existing discrepancy is the smallest useful thing to resolve.',next_move:response==='deferred'?null:option.proposed_repair.acceptance_criteria[0],finish_condition:response==='deferred'?null:option.proposed_repair.acceptance_criteria.join(' '),captured_at:context.after_captured_at};
}
function fixedAuthority(authority){
  assert.equal(authority.maximum_right,'propose');assert.equal(authority.human_review_required,true);
  for(const field of ['effect_execution_allowed','calendar_write_allowed','canon_promotion_allowed','graph_application_allowed','training_allowed'])assert.equal(authority[field],false);
}

test('context reproduces only proposed repairs and binds the complete comparison and retained requests',()=>{
  const {before,after,context}=setup(),comparison=compareReviewRequests(before,after);
  assert.equal(context.options.length,1);assert.equal(context.options[0].source_ref,after.entries[0].source_ref);
  assert.equal(context.comparison_digest,digestJSON(comparison));
  assert.equal(context.before_request_digest,digestJSON(before));assert.equal(context.after_request_digest,digestJSON(after));
  const body=copy(context);delete body.context_digest;assert.equal(context.context_digest,digestJSON(body));
  assert.deepEqual(buildDecisionContext(before,after),context);
  assert.equal(context.options[0].before_count,'At least 6; total unknown');assert.equal(context.options[0].after_count,'At least 7; total unknown');fixedAuthority(context.authority);
});

test('selected response retains its proposal and complete context without changing inputs or claiming completion',()=>{
  const {before,after,context}=setup(),input=answer(context),initial=digestJSON({before,after,context,input});
  const decision=buildUnsignedDecision(context,input);
  assert.deepEqual(decision.context,context);assert.deepEqual(decision.proposed_repair,context.options[0].proposed_repair);
  assert.equal(decision.context_digest,context.context_digest);assert.equal(decision.signature,null);
  assert.equal(decision.human_origin,'claim_only');assert.equal(decision.executed,false);assert.equal(decision.observed_benefit,null);fixedAuthority(decision.authority);
  assert.deepEqual(verifyUnsignedDecision(before,after,decision),decision);
  assert.equal(digestJSON({before,after,context,input}),initial);
  decision.context.options[0].after_count='forged';assert.notEqual(context.options[0].after_count,'forged');
});

test('revised response preserves original proposal while recording the explicit custom move and finish condition',()=>{
  const {before,after,context}=setup(),input={...answer(context,'revised'),next_move:'Inspect one retained source.',finish_condition:'One source discrepancy is documented with its original evidence.'};
  const decision=buildUnsignedDecision(context,input);
  assert.equal(decision.response,'revised');assert.equal(decision.next_move,input.next_move);
  assert.notEqual(decision.next_move,decision.proposed_repair.acceptance_criteria[0]);
  verifyUnsignedDecision(before,after,decision);fixedAuthority(decision.authority);
});

test('deferral is an explicit reason with no scheduled move and no completion claim',()=>{
  const {before,after,context}=setup(),decision=buildUnsignedDecision(context,answer(context,'deferred'));
  assert.equal(decision.response,'deferred');assert.equal(decision.next_move,null);assert.equal(decision.finish_condition,null);
  verifyUnsignedDecision(before,after,decision);assert.equal(decision.observed_benefit,null);fixedAuthority(decision.authority);
  assert.throws(()=>buildUnsignedDecision(context,{...answer(context,'deferred'),next_move:'Do it later'}),/deferred response/);
});

test('empty comparison has no selectable repair and unknown or unchanged source references reject',()=>{
  const {before}=requests(),context=buildDecisionContext(before,copy(before));assert.deepEqual(context.options,[]);assertDecisionContext(context);
  const valid=setup().context,input=answer(valid);
  assert.throws(()=>buildUnsignedDecision(context,input),/existing proposed repair/);
  assert.throws(()=>buildUnsignedDecision(valid,{...input,source_ref:before.entries[1].source_ref}),/existing proposed repair/);
  assert.throws(()=>buildUnsignedDecision(valid,{...input,source_ref:'__proto__'}),/existing proposed repair/);
});

test('edited selected moves must be called revised and all answers require explicit meaningful fields',()=>{
  const {context}=setup(),valid=answer(context);
  for(const mutation of [input=>input.next_move='Edited move',input=>input.finish_condition='Edited finish']){
    const input=copy(valid);mutation(input);assert.throws(()=>buildUnsignedDecision(context,input),/use revised/);
  }
  for(const mutation of [input=>delete input.response,input=>input.response='approved',input=>input.rationale=' \n ',input=>input.extra=true,input=>input.next_move=null,input=>input.finish_condition='']){
    const input=copy(valid);mutation(input);assert.throws(()=>buildUnsignedDecision(context,input));
  }
});

test('answer capture rejects temporal regression and nonexistent dates while accepting equivalent offsets',()=>{
  const {context}=setup(),input=answer(context);
  for(const captured_at of ['2020-01-01T00:00:00Z','2026-02-30T00:00:00Z','2026-09-10','today','2026-09-10T24:00:00Z'])assert.throws(()=>buildUnsignedDecision(context,{...input,captured_at}));
  const captured_at='2026-09-10T01:00:00+01:00';assert.equal(buildUnsignedDecision(context,{...input,captured_at}).captured_at,captured_at);
});

test('text limits count Unicode characters consistently and reject oversized input',()=>{
  const {context}=setup(),input=answer(context,'revised');
  const valid={...input,rationale:'🙂'.repeat(2000),next_move:'x'.repeat(4000),finish_condition:'y'.repeat(4000)};
  assert.deepEqual(browserBuild(context,valid),buildUnsignedDecision(context,valid));
  for(const [key,value] of [['rationale','x'.repeat(2001)],['next_move','x'.repeat(4001)],['finish_condition','x'.repeat(4001)]])assert.throws(()=>buildUnsignedDecision(context,{...valid,[key]:value}),/at most/);
});

test('browser and Node capture produce the same decisions for all response paths',()=>{
  const {context}=setup();
  for(const response of ['selected','revised','deferred'])assert.deepEqual(browserBuild(context,answer(context,response)),buildUnsignedDecision(context,answer(context,response)));
});

test('context shape enforces bounded distinct options, digests, targets, request bindings and retained holds',()=>{
  const {context}=setup();
  for(const mutate of [
    value=>value.extra=true,
    value=>value.comparison_digest='sha256:not-a-digest',
    value=>value.options.push(copy(value.options[0])),
    value=>value.options=Array.from({length:65},(_,i)=>({...copy(value.options[0]),source_ref:`source:${i}`})),
    value=>value.options[0].proposed_repair.target_ref='different-source',
    value=>value.options[0].proposed_repair.evidence_refs=[digestJSON('unrelated')],
    value=>value.options[0].removed_holds.push('hidden:prior-obligation'),
    value=>value.authority.upstream_hold_refs=value.authority.upstream_hold_refs.filter(hold=>hold!=='changes:no_automatic_repair'),
    value=>value.options[0].proposed_repair=null,
    value=>value.options[0].changed_fields.push('unknown_field')
  ]){const value=copy(context);mutate(value);assert.throws(()=>assertDecisionContext(value));}
});

test('plain JSON capture rejects accessors without invocation, class instances, cycles, symbols, and sparse arrays',()=>{
  const {context}=setup();let invoked=0;
  const input=answer(context);Object.defineProperty(input,'rationale',{enumerable:true,get(){invoked++;return 'forged';}});
  assert.throws(()=>browserBuild(context,input),/JSON data property/);assert.equal(invoked,0);
  const source=copy(context);Object.defineProperty(source.options[0],'after_count',{enumerable:true,get(){invoked++;return 'forged';}});
  assert.throws(()=>assertDecisionContext(source),/JSON data property/);assert.equal(invoked,0);
  for(const mutate of [
    value=>Object.setPrototypeOf(value,{inherited:true}),
    value=>value.cycle=value,
    value=>value[Symbol('hidden')]=true,
    value=>delete value.options[0],
    value=>Object.defineProperty(value,'hidden',{value:true,enumerable:false}),
    value=>Object.setPrototypeOf(value.options,{})
  ]){const value=copy(context);mutate(value);assert.throws(()=>assertDecisionContext(value));}
});

test('prior removed holds survive selection and cannot be removed from the context or output',()=>{
  const {before,after}=requests(),hold=after.entries[0].record.authority.upstream_hold_refs.shift();
  const context=buildDecisionContext(before,after),decision=buildUnsignedDecision(context,answer(context));
  assert.ok(context.options[0].removed_holds.includes(hold));assert.ok(decision.authority.upstream_hold_refs.includes(hold));
  const forged=copy(decision);forged.authority.upstream_hold_refs=forged.authority.upstream_hold_refs.filter(x=>x!==hold);
  assert.throws(()=>verifyUnsignedDecision(before,after,forged),/does not reproduce/);
});

test('full replay detects edited displayed context even when copied digest strings are unchanged',()=>{
  const {before,after}=requests();after.entries[1].max_count=100;
  const context=buildDecisionContext(before,after);assert.equal(context.options.length,2);
  for(const mutate of [
    value=>value.options[0].after_count='0 confirmed within this scope',
    value=>value.options[1].before_count='0 confirmed within this scope',
    value=>value.authority.upstream_hold_refs.push('fabricated:hold'),
    value=>value.options.reverse()
  ]){const changed=copy(context);mutate(changed);assert.throws(()=>buildUnsignedDecision(changed,answer(changed)),/context digest mismatch/);const forged=browserBuild(changed,answer(changed));assert.throws(()=>verifyUnsignedDecision(before,after,forged),/does not reproduce/);}
});

test('replay rejects changed retained sources, proposal data, digests, and authority or benefit escalation',()=>{
  const {before,after,context}=setup(),decision=buildUnsignedDecision(context,answer(context));
  const drift=copy(after);drift.entries[0].record.knowledge.lower_bound=8;
  assert.throws(()=>verifyUnsignedDecision(before,drift,decision),/does not reproduce/);
  for(const mutate of [
    value=>value.context_digest=digestJSON('changed'),
    value=>value.comparison_digest=digestJSON('changed'),
    value=>value.proposed_repair.action='reinspect_source',
    value=>value.authority.effect_execution_allowed=true,
    value=>value.authority.calendar_write_allowed=true,
    value=>value.authority.canon_promotion_allowed=true,
    value=>value.authority.graph_application_allowed=true,
    value=>value.authority.training_allowed=true,
    value=>value.authority.human_review_required=false,
    value=>value.signature='signed',
    value=>value.human_origin='verified',
    value=>value.executed=true,
    value=>value.observed_benefit='helpful',
    value=>value.approved=true
  ]){const forged=copy(decision);mutate(forged);assert.throws(()=>verifyUnsignedDecision(before,after,forged));}
});

test('unsigned reproduction does not authenticate an author or turn a changed rationale into execution evidence',()=>{
  const {before,after,context}=setup(),decision=buildUnsignedDecision(context,answer(context));
  decision.rationale='Another supplied rationale can reproduce because this record is unsigned.';
  verifyUnsignedDecision(before,after,decision);assert.equal(decision.human_origin,'claim_only');assert.equal(decision.executed,false);fixedAuthority(decision.authority);
});

test('whole-export UTF-8 byte budget rejects oversized decisions even when every field fits its schema bound',()=>{
  const {context}=setup(),input=answer(context),small=buildUnsignedDecision(context,input);
  assert.ok(new TextEncoder().encode(JSON.stringify(small,null,2)+'\n').byteLength<DECISION_LIMITS.bytes);
  context.options[0].claims_requiring_revalidation=Array.from({length:1024},(_,index)=>'€'.repeat(3000)+`:${index}`);
  const {context_digest,...body}=context;context.context_digest=digestJSON(body);
  assertDecisionContext(context);
  // The compact context has fewer than 8 Mi UTF-16 code units, but over 8 MiB in UTF-8.
  assert.ok(JSON.stringify(context).length<DECISION_LIMITS.bytes);
  assert.throws(()=>browserBuild(context,input),/serialized export exceeds the 8 MiB byte limit/);
  assert.throws(()=>buildUnsignedDecision(context,input),/serialized export exceeds the 8 MiB byte limit/);
});
