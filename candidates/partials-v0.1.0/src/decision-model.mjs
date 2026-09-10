/** Browser-safe unsigned data capture. No hashing, source authentication, or effects. */
export const DECISION_ACTIONS = Object.freeze(['repair_native_input','account_for_removed_source','review_hold_removal','obtain_source_expectation','reconcile_identity','reinspect_source','review_policy_change','verify_recapture','revalidate_source_claims','review_added_source','review_record_change']);
export const DECISION_CHANGED_FIELDS = Object.freeze(['record','record.id','subject','scope','knowledge','evidence','work','availability','authority','provenance','revision','supersedes_digest','expectation','max_count','review_accounting','max_age_seconds']);
export const DECISION_LIMITS = Object.freeze({text:4000,rationale:2000,options:64,items:1024,criteria:16,bytes:8*1024*1024});
const demand=(ok,message)=>{if(!ok)throw new Error(message);};

/** Inspect property descriptors before reading data, so accessors are never invoked. */
function assertPlainJSON(value,path='$',seen=new WeakSet(),depth=0) {
  demand(depth<=32,`${path}: excessive JSON nesting`);
  if(value===null||['string','boolean'].includes(typeof value))return;
  if(typeof value==='number'){demand(Number.isFinite(value),`${path}: finite JSON number required`);return;}
  demand(typeof value==='object',`${path}: JSON data required`);
  demand(!seen.has(value),`${path}: cyclic JSON`);
  const array=Array.isArray(value),prototype=Object.getPrototypeOf(value);
  demand(array?prototype===Array.prototype:[Object.prototype,null].includes(prototype),`${path}: plain JSON data required`);
  demand(Object.getOwnPropertySymbols(value).length===0,`${path}: symbol properties forbidden`);
  const keys=Object.getOwnPropertyNames(value).filter(key=>!(array&&key==='length'));
  if(array)demand(keys.length===value.length&&keys.every(key=>/^(0|[1-9][0-9]*)$/.test(key)&&Number(key)<value.length),`${path}: dense JSON array required`);
  seen.add(value);
  for(const key of keys){
    const descriptor=Object.getOwnPropertyDescriptor(value,key);
    demand(Object.hasOwn(descriptor,'value')&&descriptor.enumerable,`${path}.${key}: JSON data property required`);
    assertPlainJSON(descriptor.value,`${path}.${key}`,seen,depth+1);
  }
  seen.delete(value);
}
function object(value,keys,path) {
  demand(value!==null&&typeof value==='object'&&!Array.isArray(value),`${path}: object required`);
  demand(Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key)),`${path}: missing or unknown fields`);
}
function text(value,path,max=DECISION_LIMITS.text) {demand(typeof value==='string'&&value.trim().length>0&&[...value].length<=max,`${path}: nonempty text of at most ${max} characters required`);}
function digest(value,path){demand(typeof value==='string'&&/^sha256:[a-f0-9]{64}$/.test(value),`${path}: SHA256 digest required`);}
function dateTime(value,path) {
  demand(typeof value==='string'&&value.length<=64&&/^\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d+)?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$/.test(value),`${path}: explicit date-time required`);
  const date=value.slice(0,10);
  demand(Number.isFinite(Date.parse(value))&&new Date(`${date}T00:00:00Z`).toISOString().slice(0,10)===date,`${path}: valid date-time required`);
}
function strings(value,path,{min=0,max=DECISION_LIMITS.items,allowed=null}={}) {
  demand(Array.isArray(value)&&value.length>=min&&value.length<=max,`${path}: bounded array required`);
  for(const item of value){text(item,path);if(allowed)demand(allowed.includes(item),`${path}: unknown value`);}
  demand(new Set(value).size===value.length,`${path}: duplicate value`);
}
function authority(value,path) {
  object(value,['maximum_right','effect_execution_allowed','calendar_write_allowed','canon_promotion_allowed','graph_application_allowed','training_allowed','human_review_required','upstream_hold_refs'],path);
  demand(value.maximum_right==='propose'&&value.human_review_required===true,`${path}: candidate authority required`);
  for(const key of ['effect_execution_allowed','calendar_write_allowed','canon_promotion_allowed','graph_application_allowed','training_allowed'])demand(value[key]===false,`${path}.${key}: authority escalation forbidden`);
  strings(value.upstream_hold_refs,`${path}.upstream_hold_refs`);
}
function proposal(value,path) {
  object(value,['status','action','target_ref','evidence_refs','acceptance_criteria','maximum_right','effect_execution_allowed','human_review_required'],path);
  demand(value.status==='candidate'&&value.maximum_right==='propose'&&value.effect_execution_allowed===false&&value.human_review_required===true,`${path}: candidate proposal required`);
  demand(DECISION_ACTIONS.includes(value.action),`${path}.action: unknown action`);
  text(value.target_ref,`${path}.target_ref`);
  strings(value.evidence_refs,`${path}.evidence_refs`,{min:1});value.evidence_refs.forEach(ref=>digest(ref,`${path}.evidence_refs`));
  strings(value.acceptance_criteria,`${path}.acceptance_criteria`,{min:1,max:DECISION_LIMITS.criteria});
  text(value.acceptance_criteria.join(' '),`${path}.combined_acceptance_criteria`);
}

/** Shape and internal consistency only; the supplied context is still unauthenticated. */
export function assertDecisionContext(context) {
  assertPlainJSON(context);
  object(context,['schema_version','context_digest','comparison_digest','before_request_digest','after_request_digest','after_captured_at','authority','options'],'context');
  demand(context.schema_version==='quirk.partials-decision-context/v1alpha1','context: unknown schema version');
  for(const field of ['context_digest','comparison_digest','before_request_digest','after_request_digest'])digest(context[field],`context.${field}`);
  dateTime(context.after_captured_at,'context.after_captured_at');authority(context.authority,'context.authority');
  for(const hold of ['changes:human_review_open','changes:no_automatic_repair'])demand(context.authority.upstream_hold_refs.includes(hold),'context: required review obligation missing');
  demand(Array.isArray(context.options)&&context.options.length<=DECISION_LIMITS.options,'context.options: at most 64 options required');
  const refs=new Set();
  for(const option of context.options){
    object(option,['source_ref','change','before_count','after_count','changed_fields','claims_requiring_revalidation','removed_holds','added_holds','proposed_repair'],'context.option');
    text(option.source_ref,'context.option.source_ref');
    demand(!refs.has(option.source_ref),'context.options: duplicate source reference');refs.add(option.source_ref);
    demand(['unchanged','added','removed','replaced','changed'].includes(option.change),'context.option.change: unknown change');
    for(const key of ['before_count','after_count'])if(option[key]!==null)text(option[key],`context.option.${key}`);
    strings(option.changed_fields,'context.option.changed_fields',{allowed:DECISION_CHANGED_FIELDS});
    for(const key of ['claims_requiring_revalidation','removed_holds','added_holds'])strings(option[key],`context.option.${key}`);
    proposal(option.proposed_repair,'context.option.proposed_repair');
    demand(option.proposed_repair.target_ref===option.source_ref,'context.option: proposal target mismatch');
    demand([context.before_request_digest,context.after_request_digest].every(ref=>option.proposed_repair.evidence_refs.includes(ref)),'context.option: proposal request binding missing');
    demand([...option.removed_holds,...option.added_holds].every(hold=>context.authority.upstream_hold_refs.includes(hold)),'context.option: authority obligations omitted');
  }
  return context;
}

/** Explicit capture only. Selecting or revising a proposal never executes its action. */
export function buildUnsignedDecision(context,answer) {
  assertDecisionContext(context);assertPlainJSON(answer);
  object(answer,['source_ref','response','rationale','next_move','finish_condition','captured_at'],'answer');
  text(answer.source_ref,'answer.source_ref');
  const chosen=context.options.find(option=>option.source_ref===answer.source_ref);
  demand(chosen!==undefined,'answer.source_ref: choose an existing proposed repair');
  demand(['selected','revised','deferred'].includes(answer.response),'answer.response: explicit selected, revised, or deferred response required');
  text(answer.rationale,'answer.rationale',DECISION_LIMITS.rationale);dateTime(answer.captured_at,'answer.captured_at');
  demand(Date.parse(answer.captured_at)>=Date.parse(context.after_captured_at),'answer.captured_at: capture precedes reviewed source');
  if(answer.response==='deferred')demand(answer.next_move===null&&answer.finish_condition===null,'answer: deferred response must have no next move or finish condition');
  else {
    text(answer.next_move,'answer.next_move');text(answer.finish_condition,'answer.finish_condition');
    if(answer.response==='selected')demand(answer.next_move===chosen.proposed_repair.acceptance_criteria[0]&&answer.finish_condition===chosen.proposed_repair.acceptance_criteria.join(' '),'answer: selected response must retain the proposed move and finish condition; use revised for edits');
  }
  const decision={schema_version:'quirk.partials-unsigned-decision/v1alpha1',status:'candidate',
    context_digest:context.context_digest,comparison_digest:context.comparison_digest,before_request_digest:context.before_request_digest,after_request_digest:context.after_request_digest,
    context,source_ref:answer.source_ref,proposed_repair:chosen.proposed_repair,response:answer.response,rationale:answer.rationale,next_move:answer.next_move,finish_condition:answer.finish_condition,captured_at:answer.captured_at,
    signature:null,human_origin:'claim_only',executed:false,observed_benefit:null,authority:context.authority};
  // The portable schema bounds fields; this semantic check bounds the whole UTF-8
  // export, including the two-space formatting and newline used by the UI/CLI.
  const serialized=JSON.stringify(decision,null,2)+'\n';
  demand(new TextEncoder().encode(serialized).byteLength<=DECISION_LIMITS.bytes,'decision: serialized export exceeds the 8 MiB byte limit');
  return JSON.parse(serialized);
}
