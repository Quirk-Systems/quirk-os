import {openSync,fstatSync,readSync,closeSync} from 'node:fs';
import {IntakeError,prepareImageReference} from '../src/intake.mjs';
import {parseUniqueJson} from '../src/json.mjs';
const MAX_BYTES=8*1024*1024;
const fail=(code,message)=>{throw new IntakeError(code,message);};
function readBounded(path){
  let fd;
  try{
    fd=openSync(path,'r');const stat=fstatSync(fd);
    if(!stat.isFile())fail('INPUT_TYPE','Input must be a regular JSON file.');
    if(stat.size>MAX_BYTES)fail('INPUT_BOUND','Input exceeds 8 MiB.');
    const buffer=Buffer.alloc(MAX_BYTES+1);let total=0,n;
    while(total<buffer.length && (n=readSync(fd,buffer,total,buffer.length-total,null))>0)total+=n;
    if(total>MAX_BYTES)fail('INPUT_BOUND','Input exceeds 8 MiB.');
    let text;
    try{text=new TextDecoder('utf-8',{fatal:true}).decode(buffer.subarray(0,total));}
    catch{fail('INVALID_JSON','Input must contain valid UTF-8 JSON.');}
    return parseUniqueJson(text);
  }finally{if(fd!==undefined)closeSync(fd);}
}
function inspect(input){
  let rows=[input],page=null,hasMore=null,uninspected=[];
  if(input && typeof input==='object' && 'schemaVersion' in input){
    const allowed=['schemaVersion','status','signature','page','limit','image_preference_events','image_assets','image_pairs','image_observations','image_jobs','graph','generation'];
    const events=input.image_preference_events;
    if(input.schemaVersion!=='quirk.image-workspace-export.v0.1'||input.status!=='unsigned_candidate'||input.signature!==null||
       !Number.isSafeInteger(input.page)||input.page<0||input.limit!==100||!events||
       Object.keys(events).sort().join(',')!=='hasMore,rows'||!Array.isArray(events.rows)||events.rows.length>100||typeof events.hasMore!=='boolean'||
       input.graph?.state!=='AWAITING_INTEGRATION'||input.graph?.accepted!==0||Object.keys(input).some(key=>!allowed.includes(key))){
      fail('EXPORT_ENVELOPE_MISMATCH','Expected a bounded unsigned Site export page with no claimed graph delivery.');
    }
    rows=events.rows;page=input.page;hasMore=events.hasMore;
    uninspected=['image_assets','image_pairs','image_observations','image_jobs','generation'].filter(key=>key in input);
  }
  const seen=[],results=[],counts={new_candidates:0,exact_replays:0,rejected:0};
  for(const [index,row] of rows.entries()){
    try{
      const result=prepareImageReference(row,{seen});
      if(result.disposition==='NEW_CANDIDATE'){seen.push(result.replay_entry);counts.new_candidates++;}else counts.exact_replays++;
      results.push({index,...result});
    }catch(error){
      if(!(error instanceof IntakeError))throw error;
      results.push({index,disposition:'REJECTED',error:{code:error.code,message:error.message}});counts.rejected++;
    }
  }
  return {schema_version:'quirk.image-intake-inspection.v0.1',status:'candidate_inspection',graph_delivery:'NOT_ATTEMPTED',
    source_authenticity:'UNVERIFIED',replay_scope:'THIS_DOCUMENT_ONLY',complete_export_verified:false,
    page,has_more_events:hasMore,uninspected_sections:uninspected,counts,results};
}
try{
  if(process.argv.length!==3)fail('USAGE','Usage: node scripts/inspect.mjs INPUT.json');
  const result=inspect(readBounded(process.argv[2]));process.stdout.write(JSON.stringify(result,null,2)+'\n');
  if(result.counts.rejected)process.exitCode=2;
}catch(error){
  const known=error instanceof IntakeError;
  process.stdout.write(JSON.stringify({status:'rejected',graph_delivery:'NOT_ATTEMPTED',error:{code:known?error.code:'READ_OR_INTERNAL_ERROR',message:known?error.message:'Could not inspect this file.'}},null,2)+'\n');
  process.exitCode=2;
}
