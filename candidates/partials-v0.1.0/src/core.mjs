import {createHash} from 'node:crypto';
import Ajv2020 from 'ajv/dist/2020.js';
import {recordSchema} from './schema.mjs';

export function assertJSON(value, path='$', seen=new WeakSet(), depth=0) {
  if (depth>80) throw new Error(`${path}: excessive JSON nesting`);
  if (value===null || ['string','boolean'].includes(typeof value)) return;
  if (typeof value==='number' && Number.isFinite(value)) return;
  if (typeof value!=='object') throw new Error(`${path}: JSON data required`);
  if (seen.has(value)) throw new Error(`${path}: cyclic JSON`);
  if (!Array.isArray(value) && ![Object.prototype,null].includes(Object.getPrototypeOf(value))) throw new Error(`${path}: plain JSON object required`);
  if (Object.getOwnPropertySymbols(value).length) throw new Error(`${path}: symbol properties forbidden`);
  seen.add(value);
  const keys=Object.getOwnPropertyNames(value).filter(k=>!(Array.isArray(value)&&k==='length'));
  if (Array.isArray(value) && (keys.length!==value.length || keys.some(k=>! /^(0|[1-9][0-9]*)$/.test(k)||Number(k)>=value.length))) throw new Error(`${path}: dense JSON array required`);
  for (const k of keys) {
    const d=Object.getOwnPropertyDescriptor(value,k);
    if (!Object.hasOwn(d,'value')||!d.enumerable) throw new Error(`${path}.${k}: JSON data property required`);
    assertJSON(d.value,`${path}.${k}`,seen,depth+1);
  }
  seen.delete(value);
}
const canonical = v => v===null||typeof v!=='object' ? JSON.stringify(v) : Array.isArray(v) ? `[${v.map(canonical).join(',')}]` : `{${Object.keys(v).sort().map(k=>`${JSON.stringify(k)}:${canonical(v[k])}`).join(',')}}`;
export function digestJSON(value) { assertJSON(value); return `sha256:${createHash('sha256').update(canonical(value)).digest('hex')}`; }
const ajv=new Ajv2020({strict:true,allErrors:true,ownProperties:true});
ajv.addFormat('date-time', {type:'string',validate:value=>{
  if (!/^\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d+)?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$/.test(value)) return false;
  const date=value.slice(0,10); return Number.isFinite(Date.parse(value))&&new Date(`${date}T00:00:00Z`).toISOString().slice(0,10)===date;
}});
const validateShape=ajv.compile(recordSchema);
const demand=(ok,message)=>{if(!ok)throw new Error(message);};
const disjoint=(a,b)=>a.every(x=>!b.includes(x));

export function assertRecord(record) {
  assertJSON(record);
  demand(validateShape(record),`Invalid partial record: ${ajv.errorsText(validateShape.errors)}`);
  const {knowledge:k,evidence:e,work:w,availability:a}=record;
  demand(new Set(k.known_items.map(x=>x.id)).size===k.known_items.length,'Duplicate known item identity');
  demand(k.lower_bound===null||k.lower_bound>=k.known_items.length,'Lower bound excludes known items');
  demand(k.upper_bound===null||k.upper_bound>=Math.max(k.lower_bound??0,k.known_items.length),'Inconsistent count bounds');
  if(k.status==='unknown') demand(k.known_items.length===0&&k.lower_bound===null&&k.upper_bound===null&&k.exact===null&&k.completeness_basis==='unconfirmed','Unknown knowledge cannot assert a count');
  if(k.status==='partial') demand(k.exact===null&&k.completeness_basis==='unconfirmed'&&(k.known_items.length>0||k.lower_bound!==null||k.upper_bound!==null),'Partial knowledge needs a bound or known item, never exact');
  if(k.status==='complete') demand(k.exact!==null&&k.lower_bound===k.exact&&k.upper_bound===k.exact&&k.completeness_basis!=='unconfirmed','Complete knowledge needs explicit exact bounds and basis');
  demand(e.status!=='supported'||(e.satisfied.length>0&&!e.missing.length&&!e.conflicts.length),'Supported evidence cannot hide missing or conflicting evidence');
  demand(e.status==='contradicted'?e.conflicts.length>0:e.conflicts.length===0,'Evidence conflicts require contradicted status');
  demand(e.status!=='unknown'||e.satisfied.length===0,'Unknown evidence cannot claim satisfied checks');
  demand(disjoint(e.satisfied,e.missing),'Evidence requirement both satisfied and missing');
  demand(e.status!=='partial'||e.satisfied.length+e.missing.length>0,'Partial evidence needs a concrete check');
  demand(disjoint(w.completed_units,w.remaining_units)&&disjoint(w.completed_units,w.failed_units)&&disjoint(w.remaining_units,w.failed_units),'Work unit in conflicting states');
  demand(w.status!=='completed'||(w.completed_units.length>0&&!w.remaining_units.length&&!w.failed_units.length),'Completed work requires completed units with no remaining or failed units');
  demand(w.status!=='failed'||w.failed_units.length>0,'Failed work requires failed units');
  demand(!['unknown','not_started'].includes(w.status)||(!w.completed_units.length&&!w.failed_units.length),'Unstarted work cannot claim completed/failed units');
  demand(w.status!=='partial'||w.completed_units.length+w.remaining_units.length+w.failed_units.length>0,'Partial work needs a concrete unit');
  demand(disjoint(a.present,a.missing)&&disjoint(a.present,a.unverified)&&disjoint(a.missing,a.unverified),'Availability item in conflicting states');
  demand(a.status!=='available'||(a.present.length>0&&!a.missing.length&&!a.unverified.length),'Available inputs require present items without unresolved inputs');
  demand(a.status!=='unavailable'||(a.missing.length>0&&!a.present.length),'Unavailable inputs require absence');
  demand(a.status!=='unknown'||a.present.length===0,'Unknown availability cannot assert present inputs');
  demand(a.status!=='partial'||a.present.length+a.missing.length+a.unverified.length>0,'Partial availability needs a concrete input');
  demand((record.revision===0)===(record.supersedes_digest===null),'Revision requires predecessor digest');
  return record;
}

/** Partial overrides are convenient at construction only. Persisted records must be full and closed. */
export function createRecord(overrides) {
  assertJSON(overrides);
  const defaults={schema_version:'quirk.partials/v1alpha1',revision:0,supersedes_digest:null,status:'candidate',
    knowledge:{status:'unknown',known_items:[],lower_bound:null,upper_bound:null,exact:null,completeness_basis:'unconfirmed'},
    evidence:{status:'unknown',satisfied:[],missing:[],conflicts:[],limitations:[]},
    work:{status:'unknown',completed_units:[],remaining_units:[],failed_units:[]},
    availability:{status:'unknown',present:[],missing:[],unverified:[]},
    authority:{maximum_right:'propose',effect_execution_allowed:false,calendar_write_allowed:false,canon_promotion_allowed:false,graph_application_allowed:false,training_allowed:false,human_review_required:true,upstream_hold_refs:[]}};
  const result={...defaults,...overrides};
  for(const key of ['knowledge','evidence','work','availability','authority']) if(Object.hasOwn(overrides,key)&&overrides[key]!==null&&typeof overrides[key]==='object'&&!Array.isArray(overrides[key])) result[key]={...defaults[key],...overrides[key]};
  assertRecord(result);
  return JSON.parse(JSON.stringify(result));
}

export function evaluate(record,{maxCount=null}={}) {
  assertRecord(record);
  demand(maxCount===null||(Number.isSafeInteger(maxCount)&&maxCount>=0),'maxCount must be null or a nonnegative safe integer');
  const k=record.knowledge;
  const lower=k.lower_bound??(k.known_items.length||null);
  const limit=maxCount===null?'not_assessed':lower!==null&&lower>maxCount?'exceeded':k.status==='complete'?'within':'unknown';
  const holds=[...record.authority.upstream_hold_refs];
  if(k.status!=='complete') holds.push('inventory_incomplete');
  if(limit==='exceeded') holds.push('count_limit_exceeded');
  if(record.evidence.status!=='supported') holds.push('evidence_not_supported');
  if(record.work.status!=='completed') holds.push('work_not_completed');
  if(record.availability.status!=='available') holds.push('inputs_not_available');
  holds.push('human_review_required','candidate_has_no_execution_authority');
  return {schema_version:record.schema_version,record_digest:digestJSON(record),knowledge_status:k.status,lower_bound:lower,exact:k.exact,count_limit:limit,holds:[...new Set(holds)],effectExecutionAllowed:false};
}
export function summarize(record) {
  assertRecord(record);const k=record.knowledge;
  const lower=k.lower_bound??(k.known_items.length||null);
  const count=k.status==='complete'?`${k.exact} confirmed within this scope`:lower!==null?`At least ${lower}; total unknown`:k.upper_bound!==null?`At most ${k.upper_bound}; total unknown`:'Total unknown';
  return {count,knowledge:k.status,evidence:record.evidence.status,work:record.work.status,availability:record.availability.status,authority:'Candidate · propose only · human review required'};
}

/** Explicit full replacement, bound to the expected prior digest. No implicit merge or completion. */
export function reviseRecord(previous,replacement,{expectedDigest,reason}) {
  assertRecord(previous);assertRecord(replacement);
  demand(expectedDigest===digestJSON(previous),'Stale predecessor digest');
  demand(typeof reason==='string'&&reason.trim().length>0,'Correction reason required');
  demand(previous.id===replacement.id&&digestJSON(previous.subject)===digestJSON(replacement.subject)&&digestJSON(previous.scope)===digestJSON(replacement.scope),'Revision source identity/version/scope mismatch; create a new record');
  demand(previous.authority.upstream_hold_refs.every(x=>replacement.authority.upstream_hold_refs.includes(x)),'Revision cannot remove an upstream hold');
  const next=createRecord({...replacement,revision:previous.revision+1,supersedes_digest:expectedDigest});
  return {record:next,receipt:{operation:'replace_projection',reason,previous_digest:expectedDigest,next_digest:digestJSON(next),effect_execution_allowed:false}};
}
