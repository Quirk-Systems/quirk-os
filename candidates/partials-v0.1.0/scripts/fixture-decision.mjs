import {readFile,writeFile} from 'node:fs/promises';
import {buildDecisionContext,buildUnsignedDecision} from '../src/decision.mjs';
import {buildDecisionInspector} from '../src/inspector.mjs';
export async function generateDecisionFixtures() {
  const root=new URL('../fixtures/',import.meta.url);
  const read=async name=>JSON.parse(await readFile(new URL(name,root),'utf8'));
  const save=(name,value)=>writeFile(new URL(name,root),JSON.stringify(value,null,2)+'\n');
  const before=await read('review-request.json'),after=await read('review-next-request.json');
  const context=buildDecisionContext(before,after),option=context.options[0];
  // Synthetic capture for reproducibility. This is not a user's choice or work result.
  const answer={source_ref:option.source_ref,response:'selected',rationale:'Synthetic fixture: inspect the stale source before using its carried claims.',next_move:option.proposed_repair.acceptance_criteria[0],finish_condition:option.proposed_repair.acceptance_criteria.join(' '),captured_at:'2026-09-10T00:31:00.000Z'};
  await save('decision-context.json',context);
  await save('decision-answer.json',answer);
  await save('unsigned-decision.json',buildUnsignedDecision(context,answer));
  await writeFile(new URL('../docs/Decision-Inspector.html',import.meta.url),buildDecisionInspector(before,after));
}
