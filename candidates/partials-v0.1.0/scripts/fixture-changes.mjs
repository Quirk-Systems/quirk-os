import {readFile,writeFile} from 'node:fs/promises';
import {digestJSON} from '../src/core.mjs';
import {compareReviewRequests,renderReviewChanges} from '../src/changes.mjs';
export async function generateChangeFixtures() {
  const root=new URL('../fixtures/',import.meta.url);
  const before=JSON.parse(await readFile(new URL('review-request.json',root),'utf8'));
  const after=JSON.parse(JSON.stringify(before));
  after.captured_at='2026-09-10T00:30:00.000Z';
  // Synthetic source expectations advance while the OS record remains on its old input.
  after.entries[0].expectation.subject.version='synthetic-next-version';
  after.entries[0].expectation.subject.digest=digestJSON({synthetic:'changed-source'});
  after.entries[0].expectation.observed_at=after.captured_at;
  // Synthetic Preference replacement carries structural check labels, not verified new proof.
  after.entries[1].record.subject.digest=digestJSON({synthetic:'replaced-preference-input'});
  after.entries[1].expectation.subject=JSON.parse(JSON.stringify(after.entries[1].record.subject));
  after.entries[1].expectation.observed_at=after.captured_at;
  // An absent source is an unresolved removal, never a completion.
  after.entries.splice(2,1);
  await writeFile(new URL('review-next-request.json',root),JSON.stringify(after,null,2)+'\n');
  await writeFile(new URL('review-changes.json',root),JSON.stringify(compareReviewRequests(before,after),null,2)+'\n');
  await writeFile(new URL('../docs/Changes-Panel.html',import.meta.url),renderReviewChanges(before,after));
}
