import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { adaptSkillsReadiness, inspectSkillsCases } from '../adapters/skills.mjs';
import { assertRecord, digestJSON } from '../src/core.mjs';

const read = (relative) => JSON.parse(readFileSync(new URL(relative, import.meta.url), 'utf8'));
const fixture = () => read('../fixtures/skills-red.json');
const opts = { capturedAt: '2026-09-10T00:00:00.000Z', provenanceKind: 'synthetic', sourceRefs: ['fixture:skills-red'] };
const adapt = (input, options = {}) => adaptSkillsReadiness(input, { ...opts, ...options });

test('Skills preserves historical expected-negative, unexecuted, and missing-result cases separately', () => {
  const input = fixture();
  input.scenarios.push({ id: 'SYN-RED-003', execution_status: 'EXECUTED_HISTORICAL' });
  assert.deepEqual(inspectSkillsCases(input), [
    { id: 'SYN-RED-001', execution: 'historical_reported', result: 'expected_negative_reported', current_pass: false },
    { id: 'SYN-RED-002', execution: 'unexecuted', result: 'none', current_pass: false },
    { id: 'SYN-RED-003', execution: 'historical_reported', result: 'missing', current_pass: false },
  ]);
  const record = adapt(input);
  assertRecord(record);
  assert.equal(record.knowledge.lower_bound, 3);
  assert.equal(record.knowledge.exact, null);
  assert.equal(record.evidence.status, 'partial');
  assert.ok(record.evidence.missing.includes('historical_result:SYN-RED-003'));
  assert.ok(record.work.remaining_units.includes('execute_scenario:SYN-RED-002'));
  assert.ok(record.work.remaining_units.includes('recover_historical_result:SYN-RED-003'));
  assert.deepEqual(record.work.failed_units, []);
});

test('Skills intentionally absent artifact remains distinct from unexpected missing and unverified', () => {
  const record = adapt(fixture());
  assert.deepEqual(record.availability.present, ['candidate-object.json']);
  assert.deepEqual(record.availability.missing, ['SKILL.md (intentionally absent)', 'plugin-bundle']);
  assert.deepEqual(record.availability.unverified, ['independent-qa-verdict', 'package_artifact_inventory']);
  assert.equal(record.availability.status, 'partial');
});

test('Skills omitted scenario and artifact inventories stay unknown rather than zero or available', () => {
  const record = adapt({ candidate: fixture().candidate });
  assert.equal(record.knowledge.status, 'unknown');
  assert.equal(record.knowledge.lower_bound, null);
  assert.equal(record.knowledge.exact, null);
  assert.equal(record.availability.status, 'unknown');
  assert.ok(record.availability.unverified.includes('package_artifact_inventory'));
  assert.ok(record.evidence.missing.includes('scenario_inventory'));
  assert.ok(record.evidence.missing.includes('historical_result_inventory'));
});

test('Skills complete scenario enumeration establishes only its count, never complete readiness', () => {
  const record = adapt(fixture(), { scenarioInventoryComplete: true });
  assert.equal(record.knowledge.status, 'complete');
  assert.equal(record.knowledge.exact, 2);
  assert.equal(record.knowledge.lower_bound, 2);
  assert.equal(record.knowledge.upper_bound, 2);
  assert.equal(record.knowledge.completeness_basis, 'source_declared');
  assert.equal(record.evidence.status, 'partial');
  assert.equal(record.work.status, 'partial');
  assert.equal(record.authority.effect_execution_allowed, false);
  assert.ok(record.authority.upstream_hold_refs.includes('skills:no-admission-or-submission-grant'));
});

test('Skills empty supplied list needs explicit completeness to establish exact zero', () => {
  const input = { candidate: fixture().candidate, scenarios: [], results: [] };
  assert.equal(adapt(input).knowledge.exact, null);
  assert.equal(adapt(input, { scenarioInventoryComplete: true }).knowledge.exact, 0);
  assert.throws(() => adapt({ candidate: input.candidate }, { scenarioInventoryComplete: true }), /supplied scenarios/);
  assert.throws(() => adapt(input, { scenarioInventoryComplete: 'true' }), /must be boolean/);
});

test('Skills null inventories cannot become empty, complete, or zero inventories', () => {
  for (const field of ['scenarios', 'results', 'artifacts']) {
    const input = fixture(); input[field] = null;
    assert.throws(() => adapt(input, { scenarioInventoryComplete: true }), /must be an array/);
  }
});

test('Skills some present files do not imply complete availability', () => {
  const input = fixture(); input.artifacts = [{ id: 'candidate-object.json', state: 'present' }];
  assert.equal(adapt(input).availability.status, 'partial');
  assert.equal(adapt(input, { artifactInventoryComplete: true }).availability.status, 'available');
  assert.equal(adapt(input, { artifactInventoryComplete: true }).evidence.status, 'partial');
  assert.throws(() => adapt({ candidate: input.candidate }, { artifactInventoryComplete: true }), /supplied artifacts/);
});

test('Skills RED confirmation cannot be relabeled as current positive or negative pass evidence', () => {
  for (const verdict of ['PASS', 'PASSED', 'NEGATIVE_CASE_PASSED']) {
    const input = fixture(); input.results[0].verdict = verdict;
    assert.throws(() => adapt(input), /unsupported historical verdict/);
  }
  const record = adapt(fixture());
  assert.ok(record.evidence.missing.includes('current_version_passing_positive_cases'));
  assert.ok(record.evidence.missing.includes('current_version_passing_negative_or_boundary_cases'));
  assert.deepEqual(record.evidence.satisfied, ['historical_expected_negative_reported:SYN-RED-001']);
});

test('Skills rejects fabricated evidence attached to an unexecuted scenario', () => {
  const referenced = fixture(); referenced.scenarios[1].evidence_ref = 'fake-output.txt';
  assert.throws(() => adapt(referenced), /unexecuted scenario claims evidence/);
  const reported = fixture(); reported.results.push({ ...reported.results[0], scenario_id: 'SYN-RED-002' });
  assert.throws(() => adapt(reported), /unexecuted scenario claims evidence/);
});

test('Skills rejects duplicate or orphaned case reports', () => {
  const duplicateCase = fixture(); duplicateCase.scenarios.push(duplicateCase.scenarios[0]);
  assert.throws(() => adapt(duplicateCase), /duplicate scenarios/);
  const duplicateResult = fixture(); duplicateResult.results.push(duplicateResult.results[0]);
  assert.throws(() => adapt(duplicateResult), /duplicate results/);
  const orphan = fixture(); orphan.results[0].scenario_id = 'unknown';
  assert.throws(() => adapt(orphan), /result has no scenario/);
});

test('Skills rejects erased failures and malformed or mismatched evidence declarations', () => {
  for (const mutation of [
    (input) => { input.results[0].critical_failures = []; },
    (input) => { input.results[0].sha256 = 'not-a-digest'; },
    (input) => { input.results[0].evidence_ref = 'different-output.txt'; },
  ]) {
    const input = fixture(); mutation(input);
    assert.throws(() => adapt(input), /Skills partial/);
  }
});

test('Skills rejects operative or admission claims rather than laundering them into a safe projection', () => {
  for (const flag of ['operative', 'admitted', 'active', 'canonical', 'published', 'deployed']) {
    const input = fixture(); input.candidate[flag] = true;
    assert.throws(() => adapt(input), new RegExp(`${flag} must remain explicitly false`));
  }
  const unknown = fixture(); delete unknown.candidate.admitted;
  assert.throws(() => adapt(unknown), /admitted must remain explicitly false/);
  const promoted = fixture(); promoted.candidate.status = 'active';
  assert.throws(() => adapt(promoted), /candidate\/propose boundary/);
});

test('Skills source digest binds the entire supplied input and projection does not mutate it', () => {
  const input = fixture(); const before = structuredClone(input);
  const record = adapt(input);
  assert.deepEqual(input, before);
  assert.equal(record.subject.digest, digestJSON(input));
  input.scenarios[1].name = 'changed scenario description';
  assert.notEqual(adapt(input).subject.digest, record.subject.digest);
});

test('Skills rejects unsupported source stage/status and invalid artifact observations', () => {
  const stage = fixture(); stage.candidate.red_stage.required_verdict = 'GREEN';
  assert.throws(() => adapt(stage), /unsupported candidate stage/);
  const status = fixture(); status.scenarios[1].execution_status = 'EXECUTED_CURRENT';
  assert.throws(() => adapt(status), /unsupported execution_status/);
  const artifact = fixture(); artifact.artifacts[0].state = 'probably-present';
  assert.throws(() => adapt(artifact), /unsupported artifact state/);
});

test('Skills accepts actual pinned native JSON shapes without treating historical RED reports as pass evidence', () => {
  const manifest = read('./upstream/skills/source-manifest.json');
  const input = {
    candidate: read('./upstream/skills/candidate-object.json'),
    scenarios: read('./upstream/skills/baseline-scenarios.json'),
    results: read('./upstream/skills/baseline-results.json'),
  };
  const record = adaptSkillsReadiness(input, {
    capturedAt: opts.capturedAt, scenarioInventoryComplete: true,
    sourceRefs: manifest.files.filter((file) => file.fixture.endsWith('.json')).map((file) => file.source_url),
  });
  assertRecord(record);
  assert.equal(record.provenance.kind, 'source_projection');
  assert.equal(record.subject.id, 'writing-cuntsnickery');
  assert.equal(record.knowledge.exact, 11);
  assert.equal(record.evidence.satisfied.length, 3);
  assert.equal(inspectSkillsCases(input).filter((item) => item.execution === 'unexecuted').length, 8);
  assert.ok(inspectSkillsCases(input).every((item) => item.current_pass === false));
  assert.equal(record.availability.status, 'unknown');
  assert.equal(record.authority.maximum_right, 'propose');
  assert.equal(record.authority.human_review_required, true);
});

test('Skills compatibility snapshots retain exact Git blob bytes', () => {
  const manifest = read('./upstream/skills/source-manifest.json');
  for (const file of manifest.files) {
    const bytes = readFileSync(new URL(`./upstream/skills/${file.fixture}`, import.meta.url));
    const sha = createHash('sha1').update(`blob ${bytes.length}\0`).update(bytes).digest('hex');
    assert.equal(sha, file.blob_sha, file.fixture);
    assert.ok(file.source_url.includes(manifest.commit));
  }
});

test('Skills projection requires explicit time and attributable provenance without a wallclock default', () => {
  assert.throws(() => adaptSkillsReadiness(fixture()), /capturedAt is required/);
  assert.throws(() => adaptSkillsReadiness(fixture(), { capturedAt: opts.capturedAt }), /sourceRefs are required/);
  assert.throws(() => adaptSkillsReadiness(fixture(), { capturedAt: opts.capturedAt, sourceRefs: ['fixture:skills-red'] }), /synthetic provenance/);
  assert.equal(adapt(fixture()).provenance.captured_at, opts.capturedAt);
});

test('Skills rejects non-JSON accessors before reading them', () => {
  let calls = 0;
  const input = fixture();
  Object.defineProperty(input, 'scenarios', { enumerable: true, get() { calls += 1; return []; } });
  assert.throws(() => adapt(input), /JSON data property required/);
  assert.equal(calls, 0);
});
