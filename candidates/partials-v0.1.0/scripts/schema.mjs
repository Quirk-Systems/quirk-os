import {readFile,writeFile} from 'node:fs/promises';
import {recordSchema,reviewRequestSchema,reviewResultSchema} from '../src/schema.mjs';
for(const [name,schema] of [['partial-record',recordSchema],['review-request',reviewRequestSchema],['review-result',reviewResultSchema]]) {
const path=new URL(`../schemas/${name}.schema.json`,import.meta.url);
const content=JSON.stringify(schema,null,2)+'\n';
if(process.argv.includes('--check')) {
  if(await readFile(path,'utf8')!==content) throw new Error('Schema projection drift: run npm run schema');
} else await writeFile(path,content);
}
