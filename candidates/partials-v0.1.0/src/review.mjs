import {assertRecord,contractCheck,digestJSON} from './core.mjs';
import {reviewRequestSchema,reviewResultSchema} from './schema.mjs';
import {escapeHTML,renderPanelShell,renderPartialCard} from './projection.mjs';
const checkRequest=contractCheck(reviewRequestSchema),checkResult=contractCheck(reviewResultSchema);
const authority={maximum_right:'propose',effect_execution_allowed:false,calendar_write_allowed:false,canon_promotion_allowed:false,graph_application_allowed:false,training_allowed:false,human_review_required:true,upstream_hold_refs:[]};

/** Pure bounded consumer. Expectations are caller assertions, not authenticated freshness. */
export function reviewRecords(request) {
  checkRequest(request);
  if(Buffer.byteLength(JSON.stringify(request),'utf8')>1048576)throw new Error('Review request exceeds 1 MiB');
  if(new Set(request.entries.map(e=>e.source_ref)).size!==request.entries.length)throw new Error('Each input needs a unique source_ref');
  request=JSON.parse(JSON.stringify(request));
  const now=Date.parse(request.captured_at),groups=new Map();
  const rows=request.entries.map((entry,index)=>{
    const row={index,source_ref:entry.source_ref,input_digest:digestJSON(entry.record),disposition:'quarantined',reason:'invalid_record',duplicate_of:null};
    try{assertRecord(entry.record);}catch{return row;}
    const identity=JSON.stringify([entry.record.subject.system,entry.record.subject.id,entry.record.scope.id]);
    if(!groups.has(identity))groups.set(identity,[]);groups.get(identity).push(index);
    if(entry.expectation===null){row.reason='expectation_missing';return row;}
    if(digestJSON(entry.record.subject)!==digestJSON(entry.expectation.subject)){row.reason='subject_mismatch';return row;}
    const ages=[entry.record.provenance.captured_at,entry.expectation.observed_at].map(t=>now-Date.parse(t));
    if(ages.some(x=>x<0)){row.reason='future_capture';return row;}
    if(ages.some(x=>x>request.max_age_seconds*1000)){row.reason='stale_capture';return row;}
    row.disposition='matched';row.reason='expectation_matched';return row;
  });
  for(const indices of groups.values()) {
    if(indices.length<2)continue;
    const identities=indices.map(i=>digestJSON({record:request.entries[i].record,expectation:request.entries[i].expectation,max_count:request.entries[i].max_count}));
    if(new Set(identities).size>1) {
      for(const i of indices)Object.assign(rows[i],{disposition:'quarantined',reason:'identity_conflict',duplicate_of:null});
    } else if(rows[indices[0]].disposition==='matched') {
      for(const i of indices.slice(1))Object.assign(rows[i],{disposition:'duplicate',reason:'exact_replay',duplicate_of:indices[0]});
    }
  }
  const records=rows.filter(r=>r.disposition==='matched').map(r=>({index:r.index,record:request.entries[r.index].record,max_count:request.entries[r.index].max_count}));
  // Include holds from every structurally/semantically valid input, including quarantined ones.
  const holds=new Set(['review:human_review_open','review:expectations_are_caller_supplied']);
  for(const indices of groups.values())for(const i of indices)for(const hold of request.entries[i].record.authority.upstream_hold_refs)holds.add(hold);
  const result={schema_version:'quirk.partials-review-result/v1alpha1',status:'candidate',captured_at:request.captured_at,request_digest:digestJSON(request),rows,records,
    counts:{inputs:rows.length,matched:records.length,quarantined:rows.filter(r=>r.disposition==='quarantined').length,duplicates:rows.filter(r=>r.disposition==='duplicate').length},authority:{...authority,upstream_hold_refs:[...holds].sort()}};
  result.receipt={capability_ref:'capability.partials-source-review/v0.1.0',transform_version:'0.1.0',output_digest:digestJSON(result),observed_human_benefit:null,human_review_minutes:null,compute_cost:null,limitations:['Matched means only agreement with explicit caller expectations within the supplied age limit.','No remote freshness, source authentication, admission, capacity or effect authority is established.','Counts describe input dispositions only; domain counts are never added across records.','Original request must be retained for replay; this output is not an authenticated ledger.']};
  checkResult(result);return result;
}

/** Require the retained request; never trust a hand-edited result or hash alone. */
export function verifyReview(request,result) {
  checkResult(result);
  if(digestJSON(reviewRecords(request))!==digestJSON(result))throw new Error('Review result does not reproduce from its request');
  return result;
}

export function renderReviewPanel(request) {
  const result=reviewRecords(request);
  const cards=result.records.map(x=>renderPartialCard(x.record,{maxCount:x.max_count})).join('');
  const summary=`<article><h2>Source review</h2><p>${result.counts.matched} matched · ${result.counts.quarantined} held for review · ${result.counts.duplicates} exact duplicates</p><p>Matched records agree with supplied expectations. They remain candidates requiring human review.</p><ul>${result.rows.map(row=>`<li>${escapeHTML(row.source_ref)}: ${escapeHTML(row.reason)}</li>`).join('')}</ul><details><summary>Review receipt</summary><pre style="white-space:pre-wrap;overflow-wrap:anywhere">${escapeHTML(JSON.stringify({...result,records:result.records.map(x=>({index:x.index,record_digest:digestJSON(x.record)}))},null,2))}</pre></details></article>`;
  return renderPanelShell(summary+cards);
}
