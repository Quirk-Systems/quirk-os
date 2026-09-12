import { readFile, writeFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import { adaptSkillsReadiness } from '../adapters/skills.mjs';

/** Reproduce the shared Skills example from synthetic native-shape input. */
export async function generateSkillsFixtures() {
  const input = JSON.parse(await readFile(new URL('../fixtures/skills-red.json', import.meta.url), 'utf8'));
  const record = adaptSkillsReadiness(input, {
    capturedAt: '2026-09-10T00:00:00.000Z',
    provenanceKind: 'synthetic',
    sourceRefs: ['fixture:skills-red.json'],
  });
  await writeFile(new URL('../fixtures/skills-partial.json', import.meta.url), `${JSON.stringify(record, null, 2)}\n`);
  return record;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  await generateSkillsFixtures();
}
