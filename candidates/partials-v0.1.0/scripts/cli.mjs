#!/usr/bin/env node
import {open,readFile,writeFile} from 'node:fs/promises';
import {assertRecord,evaluate,reviseRecord} from '../src/core.mjs';
import {renderPanel} from '../src/projection.mjs';
import {fromOSProgram} from '../adapters/os.mjs';
import {fromPreferenceInspection} from '../adapters/preference.mjs';
import {adaptSkillsReadiness} from '../adapters/skills.mjs';
import {reviewRecords,renderReviewPanel} from '../src/review.mjs';
import {compareReviewRequests,renderReviewChanges} from '../src/changes.mjs';
import {buildDecisionContext,buildUnsignedDecision,verifyUnsignedDecision} from '../src/decision.mjs';
import {buildDecisionInspector} from '../src/inspector.mjs';
import {DECISION_LIMITS} from '../src/decision-model.mjs';
const readReview=async(path,limit=1048576)=>{
  const handle=await open(path,'r');
  try {
    if(!(await handle.stat()).isFile())throw new Error('Review request must be a regular file');
    const buffer=Buffer.alloc(limit+1);let size=0;
    while(size<buffer.length){const {bytesRead}=await handle.read(buffer,size,buffer.length-size,null);if(!bytesRead)break;size+=bytesRead;}
    if(size>limit)throw new Error(`JSON input exceeds ${limit/1048576} MiB`);
    return JSON.parse(buffer.subarray(0,size).toString('utf8'));
  } finally {await handle.close();}
};
const read=async p=>JSON.parse(await readFile(p,'utf8'));
const out=async(p,data)=>{if(!p)throw new Error('Explicit new output path required');await writeFile(p,typeof data==='string'?data:JSON.stringify(data,null,2)+'\n',{flag:'wx',mode:0o600});};
try {
  const [command,...args]=process.argv.slice(2);
  if(command==='validate'&&args.length===1) {assertRecord(await read(args[0]));console.log('Valid structural and semantic record; authority remains propose only.');}
  else if(['review','review-panel'].includes(command)&&args.length===2) {
    const request=await readReview(args[0]);await out(args[1],command==='review'?reviewRecords(request):renderReviewPanel(request));
  }
  else if(['compare','compare-panel'].includes(command)&&args.length===3) {
    const before=await readReview(args[0]),after=await readReview(args[1]);
    await out(args[2],command==='compare'?compareReviewRequests(before,after):renderReviewChanges(before,after));
  }
  else if(command==='inspector'&&args.length===3) {
    await out(args[2],buildDecisionInspector(await readReview(args[0]),await readReview(args[1])));
  }
  else if(command==='decide'&&args.length===4) {
    const context=buildDecisionContext(await readReview(args[0]),await readReview(args[1]));
    await out(args[3],buildUnsignedDecision(context,await readReview(args[2])));
  }
  else if(command==='verify-decision'&&args.length===3) {
    verifyUnsignedDecision(await readReview(args[0]),await readReview(args[1]),await readReview(args[2],DECISION_LIMITS.bytes));
    console.log('Unsigned decision reproduces from the retained requests. Human origin, execution, and benefit remain unverified.');
  }
  else if(command==='report'&&(args.length===1||args.length===2)) console.log(JSON.stringify(evaluate(await read(args[0]),{maxCount:args[1]===undefined?null:Number(args[1])}),null,2));
  else if(command==='panel'&&args.length>=2) await out(args.at(-1),renderPanel(await Promise.all(args.slice(0,-1).map(read))));
  else if(command==='adapt'&&args.length===4) {
    const [system,inputPath,optionsPath,outputPath]=args,input=await read(inputPath),options=await read(optionsPath);
    const adapters={os:fromOSProgram,preference:fromPreferenceInspection,skills:adaptSkillsReadiness};
    if(!Object.hasOwn(adapters,system))throw new Error('Adapter must be os, preference, or skills');
    const record=await adapters[system](input,options);assertRecord(record);await out(outputPath,record);
  } else if(command==='revise'&&args.length===6) {
    const [priorPath,replacementPath,expectedDigest,reason,recordPath,receiptPath]=args;
    const result=reviseRecord(await read(priorPath),await read(replacementPath),{expectedDigest,reason});
    // A two-file write is deliberately not offered as an atomic transaction: one bundle is the receipt.
    if(receiptPath!=='bundle')throw new Error('Use literal bundle as final argument; record and receipt stay together');
    await out(recordPath,result);
  } else throw new Error('Usage: inspector before.json after.json new.html | decide before.json after.json answer.json new.json | verify-decision before.json after.json decision.json | compare before.json after.json new.json | compare-panel before.json after.json new.html | review request.json new.json | review-panel request.json new.html | validate record.json | report record.json [maxCount] | panel record.json [...] new.html | adapt os|preference|skills input.json options.json new.json | revise prior.json replacement.json expectedDigest reason new.json bundle');
} catch(error) {console.error(error.message);process.exitCode=1;}
