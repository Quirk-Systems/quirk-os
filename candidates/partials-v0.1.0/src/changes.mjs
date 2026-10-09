import {assertRecord,contractCheck,digestJSON,summarize} from './core.mjs';
import {reviewRecords} from './review.mjs';
import {reviewChangesSchema} from './schema.mjs';
import {escapeHTML,renderPanelShell} from './projection.mjs';
const check=contractCheck(reviewChangesSchema);
const equal=(a,b)=>digestJSON(a)===digestJSON(b);
const valid=record=>{try{assertRecord(record);return record;}catch{return null;}};
const difference=(a,b)=>a.filter(x=>!b.includes(x));
const recordFields=['id','subject','scope','knowledge','evidence','work','availability','authority','provenance','revision','supersedes_digest'];

function indexRequest(request,review) {
  return new Map(request.entries.map((entry,index)=>{
    const row=review.rows[index];
    return [entry.source_ref,{entry,record:valid(entry.record),state:{input_digest:row.input_digest,disposition:row.disposition,reason:row.reason,duplicate_source_ref:row.duplicate_of===null?null:request.entries[row.duplicate_of].source_ref}}];
  }));
}

const criteria={
  repair_native_input:'Repair the owning input and rerun its adapter; retain the malformed source for inspection.',
  account_for_removed_source:'Explain where the source went; do not treat absence as completed work or released obligations.',
  review_hold_removal:'Resolve the prior hold through its owning decision path; removal from a record is not permission.',
  obtain_source_expectation:'Obtain an attributable expected subject and actual observation time from the owning source.',
  reconcile_identity:'Resolve conflicting identity, expectations, or policy explicitly without hiding any original row.',
  reinspect_source:'Inspect the owning source and rerun its adapter; do not edit timestamps solely to pass freshness checks.',
  review_policy_change:'Explain the policy change and compare its effect on eligibility before relying on the new view.',
  verify_recapture:'Substantiate the new capture or provenance; a new timestamp alone is not new evidence.',
  revalidate_source_claims:'Recheck source-bound claims against the new subject and scope; carried labels are unverified assertions.',
  review_added_source:'Inspect the added source, its scope and holds before relying on its assertions.',
  review_record_change:'Inspect the changed facts and evidence; record any correction separately from human benefit.'
};

function chooseRepair(row) {
  if(row.after?.reason==='invalid_record')return 'repair_native_input';
  if(row.change==='removed')return 'account_for_removed_source';
  if(row.removed_holds.length)return 'review_hold_removal';
  if(row.after?.reason==='expectation_missing')return 'obtain_source_expectation';
  if(row.after?.reason==='identity_conflict')return 'reconcile_identity';
  if(['subject_mismatch','stale_capture','future_capture'].includes(row.after?.reason))return 'reinspect_source';
  if(row.changed_fields.some(x=>['max_count','max_age_seconds'].includes(x)))return 'review_policy_change';
  if(row.change==='replaced')return 'revalidate_source_claims';
  if(row.changed_fields.some(x=>['provenance','expectation'].includes(x)))return 'verify_recapture';
  if(row.change==='added')return 'review_added_source';
  if(row.change!=='unchanged')return 'review_record_change';
  return null;
}

/** Compare two retained requests; never accepts precomputed review results as truth. */
export function compareReviewRequests(before,after) {
  const previous=reviewRecords(before),next=reviewRecords(after);
  if(Date.parse(after.captured_at)<Date.parse(before.captured_at))throw new Error('After capture precedes before capture');
  const context_changes=['captured_at','max_age_seconds'].filter(key=>before[key]!==after[key]);
  const prior=indexRequest(before,previous),current=indexRequest(after,next);
  const refs=[...new Set([...prior.keys(),...current.keys()])].sort();
  const rows=refs.map(source_ref=>{
    const a=prior.get(source_ref),b=current.get(source_ref),changed_fields=[];
    if(a&&b) {
      if(a.record&&b.record) {
        for(const field of recordFields)if(!equal(a.record[field],b.record[field]))changed_fields.push(field==='id'?'record.id':field);
      } else if(a.state.input_digest!==b.state.input_digest)changed_fields.push('record');
      for(const key of ['expectation','max_count'])if(!equal(a.entry[key],b.entry[key]))changed_fields.push(key);
      if(!equal({...a.state,input_digest:null},{...b.state,input_digest:null}))changed_fields.push('review_accounting');
      if(context_changes.includes('max_age_seconds'))changed_fields.push('max_age_seconds');
    }
    const replaced=a?.record&&b?.record&&['record.id','subject','scope'].some(x=>changed_fields.includes(x));
    const change=!a?'added':!b?'removed':replaced?'replaced':changed_fields.length?'changed':'unchanged';
    const oldHolds=a?.record?.authority.upstream_hold_refs??[],newHolds=b?.record?.authority.upstream_hold_refs??[];
    const claims=replaced?a.record.evidence.satisfied.filter(x=>b.record.evidence.satisfied.includes(x)):[];
    const row={source_ref,change,before:a?.state??null,after:b?.state??null,changed_fields,
      before_count:a?.record?summarize(a.record).count:null,after_count:b?.record?summarize(b.record).count:null,
      claims_requiring_revalidation:claims,removed_holds:b&&!b.record?[]:difference(oldHolds,newHolds),added_holds:a&&!a.record?[]:difference(newHolds,oldHolds),proposed_repair:null};
    const action=chooseRepair(row);
    if(action)row.proposed_repair={status:'candidate',action,target_ref:source_ref,evidence_refs:[...new Set([previous.request_digest,next.request_digest,a?.state.input_digest,b?.state.input_digest].filter(Boolean))],acceptance_criteria:[criteria[action],'Preserve uncertainty and all existing authority obligations.'],maximum_right:'propose',effect_execution_allowed:false,human_review_required:true};
    return row;
  });
  const holds=new Set([...previous.authority.upstream_hold_refs,...next.authority.upstream_hold_refs,'changes:human_review_open','changes:no_automatic_repair']);
  if([...prior.values(),...current.values()].some(x=>!x.record))holds.add('changes:invalid_input_unresolved');
  const counts={sources:rows.length,...Object.fromEntries(['unchanged','added','removed','replaced','changed'].map(x=>[x,rows.filter(r=>r.change===x).length])),proposed_repairs:rows.filter(r=>r.proposed_repair!==null).length};
  const result={schema_version:'quirk.partials-review-changes/v1alpha1',status:'candidate',before_request_digest:previous.request_digest,after_request_digest:next.request_digest,before_captured_at:before.captured_at,after_captured_at:after.captured_at,context_changes,rows,counts,authority:{...previous.authority,upstream_hold_refs:[...holds].sort()}};
  result.receipt={capability_ref:'capability.partials-change-review/v0.1.0',transform_version:'0.1.0',output_digest:digestJSON(result),observed_human_benefit:null,human_review_minutes:null,compute_cost:null,limitations:['Comparison is between retained caller-supplied requests, not authenticated current upstream state.','A changed capture time or matched result does not establish refreshed evidence.','Carried satisfied labels across changed bindings require revalidation; added labels remain source assertions.','Removed sources or holds do not establish completion or release authority obligations.','Invalid records remain opaque; their hidden obligations are unknown, not discharged.','Proposed repairs are candidates only; none are executed.']};
  check(result);return result;
}

export function verifyReviewChanges(before,after,result) {
  check(result);
  if(!equal(compareReviewRequests(before,after),result))throw new Error('Change review does not reproduce from retained requests');
  return result;
}

export function renderReviewChanges(before,after) {
  const result=compareReviewRequests(before,after);
  const items=values=>values.length?`<ul>${values.map(x=>`<li>${escapeHTML(x)}</li>`).join('')}</ul>`:'<p class="quiet">None recorded.</p>';
  return renderPanelShell(`<article><h2>What changed?</h2><p>${result.counts.sources} sources compared · ${result.counts.proposed_repairs} proposed repairs</p><p>Before: ${escapeHTML(result.before_captured_at)}<br>After: ${escapeHTML(result.after_captured_at)}</p><p>Review-context changes: ${escapeHTML(result.context_changes.join(', ')||'none')}.</p><p>Source claims and proposed repairs require human review. No repair has been performed.</p></article>${result.rows.map(row=>`<article><p class="eyebrow">${escapeHTML(row.change)}</p><h2>${escapeHTML(row.source_ref)}</h2><p>Before: ${escapeHTML(row.before?.reason??'not supplied')}<br>After: ${escapeHTML(row.after?.reason??'not supplied')}</p><p>Count before: ${escapeHTML(row.before_count??'unknown or invalid')}<br>Count after: ${escapeHTML(row.after_count??'unknown or invalid')}</p><h3>Changed fields</h3>${items(row.changed_fields)}${row.claims_requiring_revalidation.length?`<h3>Carried claims to recheck</h3>${items(row.claims_requiring_revalidation)}`:''}${row.removed_holds.length?`<h3>Removed from record; obligations remain unresolved</h3>${items(row.removed_holds)}`:''}${row.added_holds.length?`<h3>Added holds</h3>${items(row.added_holds)}`:''}${row.proposed_repair?`<h3>Proposed next move</h3><p>${escapeHTML(criteria[row.proposed_repair.action])}</p>`:'<p>No new repair proposed for this source.</p>'}</article>`).join('')}<article><details><summary>Comparison receipt and retained holds</summary>${items(result.authority.upstream_hold_refs)}${items(result.receipt.limitations)}<p class="digest">${escapeHTML(result.receipt.output_digest)}</p></details></article>`);
}
