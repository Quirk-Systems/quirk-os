import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {readFileSync,writeFileSync,mkdirSync,mkdtempSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {fromPreferenceInspection} from '../adapters/preference.mjs';

const ROOT = fileURLToPath(new URL('../', import.meta.url));
const canonical = value => value === null || typeof value !== 'object' ? JSON.stringify(value)
  : Array.isArray(value) ? '['+value.map(canonical).join(',')+']'
  : '{'+Object.keys(value).sort().map(key => JSON.stringify(key)+':'+canonical(value[key])).join(',')+'}';

/** Reproduce synthetic shared-record fixtures through the unmodified pinned inspection CLI. */
export async function generatePreferenceFixtures() {
  const base = JSON.parse(readFileSync(join(ROOT,'test/upstream/preference/fixtures/producer-event.json'),'utf8'));
  const broken = structuredClone(base);
  broken.payload_digest = '0'.repeat(64);
  const lineage = structuredClone(base), payload = JSON.parse(lineage.payload_json);
  payload.assets[0].parentId = 'c'.repeat(64);
  lineage.payload_json = canonical(payload);
  lineage.payload_digest = createHash('sha256').update(lineage.payload_json).digest('hex');
  const variants = {partial:[base],empty:[],mixed:[base,broken],lineage:[lineage]};
  const directory = mkdtempSync(join(tmpdir(),'quirk-preference-fixtures-'));
  const written = [];
  mkdirSync(join(ROOT,'fixtures'),{recursive:true});
  try {
    for (const [name,rows] of Object.entries(variants)) {
      const input = {schemaVersion:'quirk.image-workspace-export.v0.1',status:'unsigned_candidate',signature:null,
        page:0,limit:100,image_preference_events:{hasMore:false,rows},graph:{state:'AWAITING_INTEGRATION',accepted:0}};
      const path = join(directory,'input.json');
      writeFileSync(path,JSON.stringify(input));
      let output;
      try {
        output = execFileSync(process.execPath,[join(ROOT,'test/upstream/preference/scripts/inspect.mjs'),path],{encoding:'utf8'});
      } catch (error) {
        if (error.status !== 2 || !error.stdout) throw error;
        output = error.stdout;
      }
      const record = fromPreferenceInspection(JSON.parse(output),{capturedAt:'2026-09-10T00:00:00.000Z'});
      const destination = join(ROOT,`fixtures/preference-${name}.json`);
      writeFileSync(destination,JSON.stringify(record,null,2)+'\n');
      written.push(destination);
    }
  } finally {
    rmSync(directory,{recursive:true,force:true});
  }
  return written;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  for (const path of await generatePreferenceFixtures()) process.stdout.write(path+'\n');
}
