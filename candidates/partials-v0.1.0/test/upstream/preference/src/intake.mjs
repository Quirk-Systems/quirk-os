import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import Ajv2020 from 'ajv/dist/2020.js';

const schema = JSON.parse(readFileSync(new URL('../schemas/image-event-record.schema.json', import.meta.url)));
const ajv = new Ajv2020({strict:true,allErrors:false});
ajv.addFormat('date-time', value => /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(value) && Number.isFinite(Date.parse(value)) && new Date(value).toISOString() === value);
ajv.addKeyword({keyword:'producerText',type:'string',schemaType:'object',validate:(bounds,value)=>value===value.trim() && value.length>=bounds.min && value.length<=bounds.max});
const validateRecord = ajv.compile(schema);
const validatePayload = ajv.compile({$ref:schema.$id+'#/$defs/payload'});
const sha256 = text => createHash('sha256').update(text,'utf8').digest('hex');

export class IntakeError extends Error {
  constructor(code,message){super(message);this.name='IntakeError';this.code=code;}
}
function requireThat(condition,code,message){if(!condition)throw new IntakeError(code,message);}

// Matches the pinned producer's JSON-key-sort profile for bounded JSON values.
// This profile is named explicitly; it is not asserted to implement RFC 8785.
function canonical(value,depth=0){
  requireThat(depth<=30,'INPUT_BOUND','JSON nesting exceeds the supported depth.');
  if(value===null)return 'null';
  if(typeof value==='string'||typeof value==='boolean')return JSON.stringify(value);
  if(typeof value==='number'){requireThat(Number.isFinite(value),'INVALID_JSON_VALUE','Numbers must be finite.');return JSON.stringify(value);}
  if(Array.isArray(value))return '['+value.map(item=>canonical(item,depth+1)).join(',')+']';
  requireThat(typeof value==='object' && (Object.getPrototypeOf(value)===Object.prototype||Object.getPrototypeOf(value)===null),'INVALID_JSON_VALUE','Only JSON objects are supported.');
  requireThat(Reflect.ownKeys(value).every(key=>typeof key==='string'),'INVALID_JSON_VALUE','Symbol keys are not JSON.');
  return '{'+Object.keys(value).sort().map(key=>JSON.stringify(key)+':'+canonical(value[key],depth+1)).join(',')+'}';
}

function readPayload(record){
  requireThat(validateRecord(record),'SCHEMA_MISMATCH','Record does not match the pinned candidate schema.');
  requireThat(sha256(record.payload_json)===record.payload_digest,'PAYLOAD_DIGEST_MISMATCH','Payload bytes do not match their recorded digest.');
  let payload;
  try{payload=JSON.parse(record.payload_json);}catch{throw new IntakeError('INVALID_JSON','Payload JSON could not be parsed.');}
  requireThat(canonical(payload)===record.payload_json,'NONCANONICAL_PAYLOAD','Payload must retain the producer canonical encoding; duplicate keys and reformatting are not repaired.');
  requireThat(validatePayload(payload),'SCHEMA_MISMATCH','Payload does not match the pinned candidate schema.');
  requireThat(payload.actor.siteScopedId===record.owner,'ACTOR_MISMATCH','Actor claim does not match the Site record owner.');
  requireThat(payload.eventId===record.id && payload.presentation.id===record.pair_id && payload.judgment.outcome===record.outcome && payload.judgment.rationale===record.rationale && payload.judgment.createdAt===record.created_at,'RECORD_PAYLOAD_MISMATCH','Record columns contradict their payload.');
  const eventId=sha256(canonical({site:payload.sourceSite,owner:record.owner,pairId:record.pair_id}));
  requireThat(eventId===record.id,'EVENT_ID_MISMATCH','Event identity does not match the producer identity profile.');
  requireThat(Date.parse(payload.presentation.createdAt)<=Date.parse(payload.judgment.createdAt),'TEMPORAL_ORDER','Judgment precedes presentation.');
  return payload;
}

function inspectReferences(payload){
  const {A,B}=payload.presentation;
  requireThat(A.assetId!==B.assetId && A.sha256!==B.sha256,'IDENTICAL_OPTIONS','A and B must have different IDs and bytes.');
  const assets=new Map(payload.assets.map(asset=>[asset.id,asset]));
  requireThat(assets.size===2 && assets.has(A.assetId) && assets.has(B.assetId),'ASSET_REFERENCE_MISMATCH','Asset records do not close over the two presented options.');
  for(const side of [A,B])requireThat(assets.get(side.assetId).sha256===side.sha256,'ASSET_DIGEST_MISMATCH','A presented image digest contradicts its asset record.');
  const unresolved=[];
  for(const asset of payload.assets){
    if(asset.origin==='recovered_original')requireThat(asset.lineage.sourceSha256===asset.sha256,'SOURCE_DIGEST_MISMATCH','Recovered bytes contradict their source identity.');
    if(!asset.parentId)continue;
    requireThat(asset.parentId!==asset.id,'LINEAGE_CYCLE','An image cannot be its own parent.');
    const parent=assets.get(asset.parentId);
    if(!parent){unresolved.push(asset.parentId);continue;}
    requireThat(parent.sha256===asset.lineage.parentSha256,'PARENT_DIGEST_MISMATCH','Derivative parent digest contradicts the included parent.');
    requireThat(parent.parentId!==asset.id,'LINEAGE_CYCLE','Image lineage contains a cycle.');
  }
  const outcome=payload.judgment.outcome;
  const winner=outcome==='A'?A:outcome==='B'?B:null;
  const loser=outcome==='A'?B:outcome==='B'?A:null;
  requireThat(payload.graphProposal.relation===(winner?'PREFERRED_OVER':null) && payload.graphProposal.from===(winner?.assetId??null) && payload.graphProposal.to===(loser?.assetId??null),'CHOICE_RELATION_MISMATCH','Proposed relation contradicts the recorded A/B meaning.');
  requireThat(payload.graphProposal.context===payload.presentation.context && payload.graphProposal.criterion===payload.presentation.question,'CONTEXT_MISMATCH','Proposed relation changes the comparison purpose.');
  return [...new Set(unresolved)].sort();
}

export function prepareImageReference(record,{seen=[]}={}){
  // Bound and detach caller input before schema traversal. No caller state is written.
  const encoded=canonical(record);
  requireThat(Buffer.byteLength(encoded,'utf8')<=100000,'INPUT_BOUND','Record exceeds 100000 UTF-8 bytes.');
  record=JSON.parse(encoded);
  const payload=readPayload(record);
  const unresolved=inspectReferences(payload);
  requireThat(Array.isArray(seen)&&seen.length<=10000,'INVALID_REPLAY_LEDGER','Replay history must be a bounded array.');
  const identity={source_site:payload.sourceSite,event_id:record.id};
  const referenceId='preference-reference:sha256:'+sha256(canonical({...identity,payload_digest:record.payload_digest}));
  let replay=false;
  for(const prior of seen){
    requireThat(prior && typeof prior==='object' && Object.keys(prior).sort().join(',')==='event_id,payload_digest,source_site' && typeof prior.source_site==='string' && typeof prior.event_id==='string' && typeof prior.payload_digest==='string' && /^[a-f0-9]{64}$/.test(prior.event_id) && /^[a-f0-9]{64}$/.test(prior.payload_digest),'INVALID_REPLAY_LEDGER','Replay entries must contain exact event identity and digest fields.');
    if(prior.source_site!==identity.source_site || prior.event_id!==identity.event_id)continue;
    requireThat(prior.payload_digest===record.payload_digest,'REPLAY_CONFLICT','Existing event identity has different payload bytes.');replay=true;
  }
  const reference={
    api_version:'quirk.dev/v1alpha1',kind:'PreferenceReference',
    metadata:{id:referenceId,version:'0.1.0',status:'candidate',created_at:payload.judgment.createdAt,updated_at:payload.judgment.createdAt,owner_ref:'repository:Quirk-Systems/quirk-preference'},
    authority:{source_of_truth:'git_candidate_definition',current_authority_ref:null,maximum_runtime_right:'none'},
    provenance:{source_refs:[{...identity,payload_digest:record.payload_digest}],parent_object_refs:payload.assets.map(asset=>asset.id),transformation_refs:['image-evidence-intake.v0.1.0'],run_refs:[]},
    spec:{
      source_site:payload.sourceSite,source_event_id:record.id,payload_sha256:record.payload_digest,
      identity:{site_scoped_id:record.owner,cross_system_principal_mapping:null,source_authentication:'UNVERIFIED_UNSIGNED_EXPORT'},
      human_origin:'CLAIM_ONLY',criterion:payload.presentation.question,context:payload.presentation.context,
      presentation:payload.presentation,assets:payload.assets,choice:payload.judgment.outcome,rationale:payload.judgment.rationale,
      proposed_relation:payload.graphProposal,inferred_feature_preferences:[],
      lineage_status:unresolved.length?'PARTIAL':'INCLUDED_REFERENCES_CONSISTENT',unresolved_parent_ids:unresolved,
      applied:false,model_training_allowed:false,observed_benefit:null,
    },
    evidence:{supporting_refs:[record.payload_digest],contradicting_refs:[],confidence:null},
    lifecycle:{supersedes:[],superseded_by:null,valid_from:null,valid_until:null},
  };
  return {disposition:replay?'EXACT_REPLAY':'NEW_CANDIDATE',source_authenticity:'UNVERIFIED',graph_delivery:'NOT_ATTEMPTED',
    replay_ledger_integrity:'CALLER_SUPPLIED_UNVERIFIED',replay_entry:{...identity,payload_digest:record.payload_digest},reference};
}
