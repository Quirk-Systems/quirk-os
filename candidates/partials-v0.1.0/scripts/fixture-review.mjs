import {readFile,writeFile} from 'node:fs/promises';
import {reviewRecords,renderReviewPanel} from '../src/review.mjs';
export async function generateReviewFixtures() {
  const base=new URL('../fixtures/',import.meta.url),entries=[];
  const captured_at='2026-09-10T00:00:00.000Z';
  for(const name of ['os','preference','skills']) {
    const record=JSON.parse(await readFile(new URL(`${name}-partial.json`,base),'utf8'));
    // Explicit synthetic recapture for the consumer fixture, not new source evidence.
    record.provenance={kind:'synthetic',source_refs:[`fixture:${name}-partial`],captured_at};
    entries.push({source_ref:`fixture:review:${name}`,record,max_count:name==='os'?2:null,expectation:{subject:JSON.parse(JSON.stringify(record.subject)),source_ref:`fixture:expected:${name}`,observed_at:captured_at}});
  }
  entries.push({source_ref:'fixture:review:malformed',record:{invalid_fixture:true},max_count:null,expectation:null});
  const request={schema_version:'quirk.partials-review-request/v1alpha1',captured_at,max_age_seconds:3600,entries};
  for(const [name,value] of [['review-request',request],['review-result',reviewRecords(request)]])await writeFile(new URL(`${name}.json`,base),JSON.stringify(value,null,2)+'\n');
  await writeFile(new URL('../docs/Review-Panel.html',import.meta.url),renderReviewPanel(request));
}
