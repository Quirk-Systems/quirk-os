import {readFile,writeFile} from 'node:fs/promises';
import {recordSchema,reviewRequestSchema,reviewResultSchema,reviewChangesSchema} from '../src/schema.mjs';
import {contextSchema,decisionSchema} from '../src/decision-schema.mjs';
for(const [name,schema] of [['partial-record',recordSchema],['review-request',reviewRequestSchema],['review-result',reviewResultSchema],['review-changes',reviewChangesSchema],['decision-context',contextSchema],['unsigned-decision',decisionSchema]]) {
const path=new URL(`../schemas/${name}.schema.json`,import.meta.url);
const content=JSON.stringify(schema,null,2)+'\n';
if(process.argv.includes('--check')) {
  if(await readFile(path,'utf8')!==content) throw new Error('Schema projection drift: run npm run schema');
} else await writeFile(path,content);
}
