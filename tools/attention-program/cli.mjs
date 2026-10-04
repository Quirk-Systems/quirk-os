#!/usr/bin/env node
// Local candidate tooling. No remote adapters, deployment, or promotion path.
import {readFile, writeFile} from 'node:fs/promises';
import {dirname, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {validateProgram, verifyReceipts, evaluate, applyCommand} from './engine.mjs';

const dir = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const usage = `Usage (Node 24):
  node tools/attention-program/cli.mjs validate PROGRAM.json
  node tools/attention-program/cli.mjs report PROGRAM.json [--as-of YYYY-MM-DD]
  node tools/attention-program/cli.mjs apply PROGRAM.json COMMAND.json --expected-revision N [--at UTC_ISO_WITH_MILLISECONDS] [--out NEW.json]
  node tools/attention-program/cli.mjs build PROGRAM.json --out NEW.html

Outputs never overwrite an existing file. Without --out, apply writes JSON to stdout.
All commands act only on local candidate records. No calendar or service is connected.`;

function option(name) {
  const i = args.indexOf(name);
  if (i === -1) return undefined;
  if (!args[i+1] || args[i+1].startsWith('--')) throw new Error(`Missing value for ${name}`);
  return args[i+1];
}
async function readJSON(path) {
  const raw = await readFile(resolve(path), 'utf8');
  if (Buffer.byteLength(raw) > 2_000_000) throw new Error('Record exceeds 2 MB import limit');
  return JSON.parse(raw);
}
async function checked(path) {
  const p = await readJSON(path);
  const structural = validateProgram(p);
  if (structural.length) throw new Error(JSON.stringify(structural));
  const ledger = await verifyReceipts(p);
  if (ledger.length) throw new Error(JSON.stringify(ledger));
  return p;
}
function localDate(p) {
  const parts = new Intl.DateTimeFormat('en-CA', {timeZone:p.schedule.timezone,year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());
  const get = t => parts.find(x=>x.type===t).value;
  return `${get('year')}-${get('month')}-${get('day')}`;
}
async function output(body, path) {
  if (path) {await writeFile(resolve(path), body, {encoding:'utf8',flag:'wx',mode:0o600}); process.stdout.write(`${resolve(path)}\n`);}
  else process.stdout.write(body);
}
try {
  const [verb, file, commandFile] = args;
  if (verb === '--help' || verb === '-h') {console.log(usage); process.exit(0);}
  if (!file || !['validate','report','apply','build'].includes(verb)) throw new Error(usage);
  const p = await checked(file);
  if (verb === 'validate') console.log(JSON.stringify({valid:true,id:p.metadata.id,revision:p.revision,scope:'local candidate record; no outcome or authority admission'},null,2));
  if (verb === 'report') console.log(JSON.stringify(evaluate(p,option('--as-of') || localDate(p)),null,2));
  if (verb === 'apply') {
    if (!commandFile || commandFile.startsWith('--')) throw new Error('A command JSON file is required');
    const revision = option('--expected-revision');
    if (revision === undefined || !/^\d+$/.test(revision)) throw new Error('--expected-revision must be an explicit nonnegative integer');
    const command = await readJSON(commandFile);
    const options = {expectedRevision:Number(revision)};
    if (option('--at')) options.now = option('--at');
    const next = await applyCommand(p,command,options);
    await output(JSON.stringify(next,null,2)+'\n',option('--out'));
  }
  if (verb === 'build') {
    const path = option('--out');
    if (!path) throw new Error('build requires --out NEW.html');
    const [template, engine] = await Promise.all([readFile(resolve(dir,'view.html'),'utf8'),readFile(resolve(dir,'engine.mjs'),'utf8')]);
    for(const marker of ['/*__ENGINE__*/','/*__PROGRAM__*/']) if(template.split(marker).length!==2) throw new Error(`Template must contain one ${marker}`);
    if (/<\/script/i.test(engine)) throw new Error('Engine source includes an unsafe script terminator');
    const safeJSON = JSON.stringify(p).replace(/</g,'\\u003c').replace(/\u2028/g,'\\u2028').replace(/\u2029/g,'\\u2029');
    const html = template.replace('/*__ENGINE__*/',()=>engine).replace('/*__PROGRAM__*/',()=>safeJSON);
    await output(html,path);
  }
} catch (error) {
  console.error(JSON.stringify({error:error.code || 'INVALID_REQUEST',message:error.message}));
  process.exitCode = 1;
}
