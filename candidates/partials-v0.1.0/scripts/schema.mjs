import {readFile,writeFile} from 'node:fs/promises';
import {recordSchema} from '../src/schema.mjs';
const path=new URL('../schemas/partial-record.schema.json',import.meta.url);
const content=JSON.stringify(recordSchema,null,2)+'\n';
if(process.argv.includes('--check')) {
  if(await readFile(path,'utf8')!==content) throw new Error('Schema projection drift: run npm run schema');
} else await writeFile(path,content);
