import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {verifyReviewChanges} from '../src/changes.mjs';
test('comparison CLI replays retained requests, renders, refuses overwrite and reversed time',async()=>{
  const root=new URL('../',import.meta.url),dir=await mkdtemp(join(tmpdir(),'quirk-changes-'));
  try {
    const before='fixtures/review-request.json',after='fixtures/review-next-request.json',json=join(dir,'changes.json'),html=join(dir,'changes.html');
    const run=(...args)=>spawnSync(process.execPath,['scripts/cli.mjs',...args],{cwd:root,encoding:'utf8'});
    const result=run('compare',before,after,json);assert.equal(result.status,0,result.stderr);
    verifyReviewChanges(JSON.parse(await readFile(new URL(before,root),'utf8')),JSON.parse(await readFile(new URL(after,root),'utf8')),JSON.parse(await readFile(json,'utf8')));
    assert.equal(run('compare-panel',before,after,html).status,0);
    const panel=await readFile(html,'utf8');assert.match(panel,/What changed\?/);assert.match(panel,/No repair has been performed/);
    assert.equal(run('compare',before,after,json).status,1);
    assert.equal(run('compare',after,before,join(dir,'reversed.json')).status,1);
  } finally {await rm(dir,{recursive:true,force:true});}
});
