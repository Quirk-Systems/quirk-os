import {createRecord,assertJSON,digestJSON} from '../src/core.mjs';
import {validateProgram,verifyReceipts,evaluate as nativeEvaluate} from './native/os-engine.mjs';
export const OS_SOURCE_HEAD='138039afad0826130505eb13230c5a0844c0f572';
const SOURCE=`https://github.com/Quirk-Systems/quirk-os/tree/${OS_SOURCE_HEAD}`;
const demand=(ok,message)=>{if(!ok)throw new Error(`OS adapter: ${message}`);};
const closed=(o,keys)=>o&&typeof o==='object'&&!Array.isArray(o)&&Object.keys(o).every(k=>keys.includes(k))&&keys.every(k=>Object.hasOwn(o,k));

/** Read-only sidecar. Never invokes native applyCommand or confirms an inventory. */
export async function fromOSProgram(program,options={}) {
  assertJSON(options);
  const {capturedAt,asOfDate,inventory:providedInventory=null,useReport:providedReport=null}=options;
  let inventory=providedInventory,useReport=providedReport;
  assertJSON({program,capturedAt,asOfDate,inventory,useReport});
  program=JSON.parse(JSON.stringify(program));
  inventory=JSON.parse(JSON.stringify(inventory));useReport=JSON.parse(JSON.stringify(useReport));
  const findings=validateProgram(program);demand(!findings.length,JSON.stringify(findings));
  const integrity=await verifyReceipts(program);demand(!integrity.length,JSON.stringify(integrity));
  const native=nativeEvaluate(program,asOfDate);
  demand(!native.findings.some(x=>x.code==='invalid_date'),'explicit valid asOfDate required');
  const sourceRefs=[SOURCE,`program:${digestJSON(program)}`];
  let externalItems=[],externalLower=null;
  if(inventory!==null) {
    demand(closed(inventory,['program_digest','known_items','lower_bound','source_refs']),'inventory sidecar fields');
    demand(inventory.program_digest===digestJSON(program),'inventory sidecar belongs to a different program version');
    demand(Array.isArray(inventory.known_items)&&inventory.known_items.every(x=>closed(x,['id','label'])),'known item shape');
    demand(Number.isSafeInteger(inventory.lower_bound)&&inventory.lower_bound>=inventory.known_items.length,'inventory lower bound');
    demand(Array.isArray(inventory.source_refs)&&inventory.source_refs.length>0,'inventory provenance required');
    demand(inventory.known_items.every(x=>!program.initiatives.some(i=>i.id===x.id)),'outside inventory overlaps program initiatives');
    externalItems=inventory.known_items;externalLower=inventory.lower_bound;sourceRefs.push(...inventory.source_refs);
  }
  if(useReport!==null) {
    demand(closed(useReport,['report','source_ref'])&&typeof useReport.report==='string'&&useReport.report.trim(),'use report must be explicit text with source');
    sourceRefs.push(useReport.source_ref);
  }
  const active=program.initiatives.filter(x=>x.phase==='doing');
  const known=[...externalItems,...active.map(x=>({id:x.id,label:x.title}))];
  const confirmed=program.bounds.inventory_confirmed;
  if(confirmed&&externalLower!==null) demand(program.bounds.external_in_progress>=externalLower,'confirmed count contradicts sidecar lower bound');
  const exact=confirmed?program.bounds.external_in_progress+active.length:null;
  const lower=confirmed?exact:externalLower!==null?externalLower+active.length:active.length||null;
  const completed=program.initiatives.filter(x=>x.phase==='done').map(x=>x.id);
  const remaining=program.initiatives.filter(x=>!['done','stopped'].includes(x.phase)).map(x=>x.id);
  const failed=program.observations.filter(x=>x.completed===false&&x.date<=asOfDate).map(x=>`observation:${x.id}`);
  const finished=completed.length>0&&!remaining.length&&!failed.length;
  const conflicts=native.outcome==='not_supported'?['native_benefit_not_supported']:[];
  return createRecord({
    id:`os-partials:${program.metadata.id}`,
    subject:{system:'Quirk-Systems/quirk-os',id:program.metadata.id,version:`${OS_SOURCE_HEAD}/r${program.revision}`,digest:digestJSON({program,inventory,useReport,asOfDate})},
    scope:{id:'os:active-optional-work',description:'Active discretionary initiatives in this program plus outside discretionary inventory; employment and essential care are excluded.'},
    provenance:{kind:'source_projection',source_refs:[...new Set(sourceRefs)],captured_at:capturedAt},
    knowledge:{status:confirmed?'complete':lower!==null?'partial':'unknown',known_items:known,lower_bound:lower,upper_bound:exact,exact,completeness_basis:confirmed?'source_declared':'unconfirmed'},
    evidence:{status:conflicts.length?'contradicted':'partial',satisfied:['native_shape_valid','native_receipts_consistent',...(useReport?['human_use_report_present']:[]),...(native.outcome==='supported'?['native_self_report_comparison_supported']:[])],missing:['independent_human_benefit_verification',...(native.outcome==='inconclusive'?['native_comparable_benefit_evidence']:[]),...native.findings.filter(x=>x.code!=='self_report_only').map(x=>`native:${x.code}`)],conflicts,limitations:['Native receipts establish local integrity, not authenticated human truth.','A use report is subjective feedback and supplies no elapsed minutes or completed commitment.','Native benefit result is a self-report comparison only.']},
    work:{status:finished?'completed':failed.length&&!completed.length&&!active.length?'failed':completed.length||active.length||failed.length?'partial':'not_started',completed_units:completed,remaining_units:remaining,failed_units:failed},
    availability:{status:'partial',present:['program_record','declared_protected_schedule'],missing:[],unverified:['current_real_world_capacity','protected_obligation_fit']},
    authority:{upstream_hold_refs:[...(!confirmed?['os:inventory_unknown']:[]),...(['paused','closed'].includes(program.trial.phase)?[`os:trial_${program.trial.phase}`]:[]),...(native.trial_expired?['os:trial_expired']:[]),'os:protected_schedule','os:no_runtime_or_calendar_authority']}
  });
}
