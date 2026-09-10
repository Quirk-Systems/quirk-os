import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {Script} from 'node:vm';
import {buildDecisionContext,verifyUnsignedDecision} from '../src/decision.mjs';
import {assertDecisionContext,buildUnsignedDecision} from '../src/decision-model.mjs';
import {mountDecisionInspector} from '../src/inspector-ui.mjs';
import {buildDecisionInspector} from '../src/inspector.mjs';
const fixture=async name=>JSON.parse(await readFile(new URL(`../fixtures/${name}.json`,import.meta.url),'utf8'));
const before=await fixture('review-request'),after=await fixture('review-next-request');
const copy=value=>JSON.parse(JSON.stringify(value));

// Minimal event-handler harness, not a browser or a DOM conformance test.
function harness(context=buildDecisionContext(before,after),downloadError=false) {
  let focused=null;const downloads=[];
  class Element {
    value='';textContent='';disabled=false;hidden=false;checked=false;readOnly=false;listeners={};
    constructor(id,value=''){this.id=id;this.value=value;}
    addEventListener(type,fn){this.listeners[type]=fn;}
    fire(type){this.listeners[type]?.({preventDefault(){}});}
    focus(){focused=this.id;}
  }
  const ids=['decision-form','status','preview','decision-json','download','decision-fields','prepare','rationale','next-move','finish-condition','chosen-source','move-fields','move-help','preview-heading'];
  const nodes=Object.fromEntries(ids.map(id=>[id,new Element(id)]));
  nodes.preview.hidden=true;nodes.download.disabled=true;nodes['decision-fields'].disabled=true;
  const sources=context.options.map((row,index)=>new Element(`source-${index}`,row.source_ref));
  const responses=['selected','revised','deferred'].map(value=>new Element(value,value));
  const document={getElementById:id=>nodes[id],querySelectorAll:selector=>selector==='input[name="source"]'?sources:responses};
  mountDecisionInspector(document,context,{assertDecisionContext,buildUnsignedDecision,now:()=>after.captured_at,download:value=>{if(downloadError)throw new Error('viewer rejected');downloads.push(value);}});
  const select=(group,value)=>{group.forEach(input=>{input.checked=input.value===value;});group.find(input=>input.checked).fire('change');};
  return {nodes,sources,responses,downloads,context,focus:()=>focused,source:index=>select(sources,sources[index].value),response:value=>select(responses,value),input:(id,value)=>{nodes[id].value=value;nodes[id].fire('input');},submit:()=>nodes['decision-form'].fire('submit'),download:()=>nodes.download.fire('click')};
}
test('Inspector requires source, response and rationale before enabling any export',()=>{
  const h=harness();assert.ok(h.sources.every(x=>!x.checked));assert.ok(h.responses.every(x=>!x.checked));assert.equal(h.nodes.download.disabled,true);
  h.submit();assert.equal(h.focus(),'source-0');h.download();assert.equal(h.downloads.length,0);
  h.source(0);assert.equal(h.nodes['decision-fields'].disabled,false);h.submit();assert.equal(h.focus(),'selected');
  h.response('selected');h.submit();assert.equal(h.focus(),'rationale');assert.match(h.nodes.status.textContent,/rationale/);assert.equal(h.nodes.preview.hidden,true);
  h.input('rationale','Use this discrepancy to decide what evidence to gather.');h.submit();assert.equal(h.nodes.preview.hidden,false);assert.equal(h.downloads.length,0);
  h.download();const result=JSON.parse(h.downloads[0]);verifyUnsignedDecision(before,after,result);assert.equal(result.executed,false);assert.equal(result.observed_benefit,null);
});
test('revision captures an explicit next move and finish and focuses the missing field',()=>{
  const h=harness();h.source(0);h.response('revised');h.input('rationale','Narrow this to one source.');
  assert.equal(h.nodes['next-move'].readOnly,false);
  h.input('next-move','');h.submit();assert.equal(h.focus(),'next-move');
  h.input('next-move','Inspect one source record.');h.input('finish-condition','');h.submit();assert.equal(h.focus(),'finish-condition');
  h.input('finish-condition','A source discrepancy has a linked explanation.');h.submit();h.download();
  const result=JSON.parse(h.downloads[0]);assert.equal(result.response,'revised');assert.equal(result.next_move,'Inspect one source record.');verifyUnsignedDecision(before,after,result);
});
test('deferral retains the reason and holds and exports no planned move or finish',()=>{
  const h=harness();h.source(0);h.response('deferred');h.input('rationale','The source is unavailable.');
  assert.equal(h.nodes['move-fields'].hidden,true);assert.equal(h.nodes['next-move'].disabled,true);
  h.submit();h.download();const result=JSON.parse(h.downloads[0]);assert.equal(result.next_move,null);assert.equal(result.finish_condition,null);assert.deepEqual(result.authority,h.context.authority);verifyUnsignedDecision(before,after,result);
});
test('drafts survive source and response changes while prepared exports are invalidated',()=>{
  const h=harness();h.source(0);h.response('revised');h.input('rationale','Keep a smaller first step.');h.input('next-move','My smaller step');h.input('finish-condition','My explicit finish');h.submit();
  h.response('selected');assert.equal(h.nodes.download.disabled,true);assert.notEqual(h.nodes['next-move'].value,'My smaller step');
  h.response('revised');assert.equal(h.nodes['next-move'].value,'My smaller step');
  h.source(1);assert.ok(h.responses.every(x=>!x.checked));assert.equal(h.nodes.rationale.value,'');h.download();assert.equal(h.downloads.length,0);
  h.source(0);assert.equal(h.nodes.rationale.value,'Keep a smaller first step.');assert.equal(h.nodes['finish-condition'].value,'My explicit finish');h.submit();
  h.input('rationale','Changed reason');h.download();assert.equal(h.downloads.length,0);assert.equal(h.nodes['decision-json'].value,'');assert.equal(h.nodes.preview.hidden,true);
});
test('download failure leaves a copyable verified record and a fresh mount has no saved answer',()=>{
  const h=harness(undefined,true);h.source(0);h.response('selected');h.input('rationale','A synthetic test rationale.');h.submit();h.download();
  assert.match(h.nodes.status.textContent,/Copy the JSON/);verifyUnsignedDecision(before,after,JSON.parse(h.nodes['decision-json'].value));
  const fresh=harness();assert.equal(fresh.nodes.rationale.value,'');assert.ok(fresh.sources.every(x=>!x.checked));
});
test('invalid or empty contexts disable capture, and Unicode input uses contract character limits',()=>{
  const invalid=buildDecisionContext(before,after);invalid.authority.calendar_write_allowed=true;
  const unchanged={...before,entries:before.entries.slice(0,3)};
  for(const context of [invalid,buildDecisionContext(unchanged,copy(unchanged))]){const h=harness(context);assert.equal(h.nodes.prepare.disabled,true);assert.equal(h.nodes['decision-fields'].disabled,true);h.download();assert.equal(h.downloads.length,0);}
  const h=harness();h.source(0);h.response('selected');h.input('rationale','🙂'.repeat(2000));h.submit();assert.equal(h.nodes.preview.hidden,false);
  h.input('rationale','🙂'.repeat(2001));h.submit();assert.equal(h.nodes.preview.hidden,true);assert.equal(h.focus(),'rationale');
});
test('generated Inspector escapes hostile data and binds its sole module with a CSP hash',()=>{
  const old=copy(before),next=copy(after),hostile='source:</script><img src=x onerror=alert(1)>\u2028&"';
  old.entries[0].source_ref=hostile;next.entries[0].source_ref=hostile;
  const html=buildDecisionInspector(old,next),scripts=[...html.matchAll(/<script type="module">([\s\S]*?)<\/script>/g)];
  assert.equal(scripts.length,1);assert.equal((html.match(/<\/script>/g)||[]).length,1);assert.doesNotMatch(html,/<img/);
  assert.match(html,/&lt;\/script&gt;/);assert.match(scripts[0][1],/\\u003c\/script>/);
  const hash=createHash('sha256').update(scripts[0][1]).digest('base64');assert.ok(html.includes(`script-src 'sha256-${hash}'`));
  assert.match(html,/connect-src 'none'/);assert.match(html,/form-action 'none'/);
  assert.doesNotMatch(scripts[0][1],/\b(?:fetch|XMLHttpRequest|WebSocket|localStorage|sessionStorage|indexedDB)\b/);
  assert.doesNotMatch(html,/type="radio"[^>]*\bchecked\b/);assert.doesNotMatch(html,/maxlength=/);
  assert.match(html,/@media\(max-width:760px\)/);assert.match(html,/aria-live="polite"/);
  // Syntax check only, without executing or navigating a browser.
  assert.doesNotThrow(()=>new Script(scripts[0][1].replace(/^export /gm,'')));
});
