import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdtemp,rm,stat} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
test('decision CLI captures and replays a choice, rejects drift and overwrites, and builds a private Inspector',async()=>{
  const root=new URL('../',import.meta.url),dir=await mkdtemp(join(tmpdir(),'quirk-decision-'));
  try {
    const before='fixtures/review-request.json',after='fixtures/review-next-request.json',answer='fixtures/decision-answer.json',json=join(dir,'decision.json'),html=join(dir,'inspector.html');
    const run=(...args)=>spawnSync(process.execPath,['scripts/cli.mjs',...args],{cwd:root,encoding:'utf8'});
    let result=run('decide',before,after,answer,json);assert.equal(result.status,0,result.stderr);
    result=run('verify-decision',before,after,json);assert.equal(result.status,0,result.stderr);assert.match(result.stdout,/remain unverified/);
    result=run('inspector',before,after,html);assert.equal(result.status,0,result.stderr);assert.match(await readFile(html,'utf8'),/Choose one next move/);
    for(const path of [json,html])assert.equal((await stat(path)).mode&0o777,0o600);
    const original=await readFile(json,'utf8');assert.equal(run('decide',before,after,answer,json).status,1);assert.equal(await readFile(json,'utf8'),original);
    assert.equal(run('inspector',before,after,html).status,1);assert.equal(run('inspector',after,before,join(dir,'reversed.html')).status,1);
    const changed=JSON.parse(original);changed.context.options[0].after_count='0 confirmed';const forged=join(dir,'forged.json');await writeFile(forged,JSON.stringify(changed));assert.equal(run('verify-decision',before,after,forged).status,1);
    const oversized=join(dir,'oversized.json');await writeFile(oversized,' '.repeat(8*1024*1024+1));result=run('verify-decision',before,after,oversized);assert.equal(result.status,1);assert.match(result.stderr,/exceeds 8 MiB/);
  } finally {await rm(dir,{recursive:true,force:true});}
});
