/* Run: node --test usefulness.test.cjs. Every trial is fictional. */
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const Q = require('./usefulness.js');

const clone = value => JSON.parse(JSON.stringify(value));
const trial = () => ({
  task: 'Review a fictional product description against its specification.',
  meaning: { matters: 'yes', reason: 'Avoid publishing unsupported product claims.' },
  real_use: { status: 'performed', description: 'Reviewed one fictional product description and retained a corrected draft.', observed_at: '2026-01-20T14:00:00.000Z' },
  baseline: { setup: 2, work: 20, supervision: 1, cleanup: 3, maintenance: 4, basis: 'observed', note: 'Fictional observed values for behavior testing.' },
  assisted: { setup: 3, work: 8, supervision: 2, cleanup: 2, maintenance: 3, basis: 'observed', note: 'Fictional observed values for behavior testing.' },
  comparison: { comparable: 'yes', baseline_errors: 1, assisted_errors: 0, note: 'Same fictional product and acceptance criteria.' },
  evidence_refs: ['source.trial-observation@0.1.0'],
  carry_forward_refs: ['asset.review-checklist@0.1.0'],
  carry_forward_description: 'A reusable checklist for the next product description.',
  human_disposition: 'undecided'
});

test('complete supplied observations recommend human review and include every overhead cost', () => {
  const spec = trial();
  assert.equal(Q.validate(spec), true);
  const result = Q.evaluate(spec);
  assert.equal(result.baseline_total_minutes, 30);
  assert.equal(result.assisted_total_minutes, 18);
  assert.equal(result.delta_minutes, 12);
  assert.equal(result.evidence_state, 'observed');
  assert.equal(result.recommendation, 'review_keep');
  assert.equal(result.state, 'candidate');
  assert.equal(result.authority, 'propose');
  assert.ok(result.next_action.trim());
  assert.match(result.reasons.join(' '), /not.*verif|not.*authenticat/i);
  assert.match(result.reasons.join(' '), /rights|staleness/i);
});

test('setup and maintenance can turn faster task work into a slower total', () => {
  const spec = trial();
  Object.assign(spec.assisted, { setup: 12, maintenance: 9 });
  const result = Q.evaluate(spec);
  assert.equal(result.assisted_total_minutes, 33);
  assert.equal(result.delta_minutes, -3);
  assert.equal(result.recommendation, 'review_tradeoff');
});

test('unknown maintenance remains null and prevents measured savings', () => {
  const spec = trial(); spec.assisted.maintenance = null;
  const result = Q.evaluate(spec);
  assert.equal(result.assisted_total_minutes, null);
  assert.equal(result.baseline_total_minutes, 30);
  assert.equal(result.delta_minutes, null);
  assert.equal(result.evidence_state, 'incomplete');
  assert.equal(result.recommendation, 'needs_evidence');
  assert.equal(spec.assisted.maintenance, null);
});

test('estimated totals remain estimates and never become observed savings', () => {
  const spec = trial(); spec.baseline.basis = 'estimated';
  const result = Q.evaluate(spec);
  assert.equal(result.baseline_total_minutes, 30);
  assert.equal(result.assisted_total_minutes, 18);
  assert.equal(result.delta_minutes, null);
  assert.equal(result.evidence_state, 'estimated');
  assert.equal(result.recommendation, 'needs_evidence');
});

test('more unsupported claims require a quality tradeoff review despite a positive time delta', () => {
  const spec = trial(); spec.comparison.assisted_errors = 2;
  spec.comparison.note = 'The fictional assisted draft contained two unsupported claims; baseline contained one.';
  const result = Q.evaluate(spec);
  assert.equal(result.delta_minutes, 12);
  assert.equal(result.recommendation, 'review_tradeoff');
  assert.match(result.reasons.join(' '), /error|quality/i);
});

test('equal total time does not earn a keep recommendation', () => {
  const spec = trial(); spec.assisted.work = 20;
  const result = Q.evaluate(spec);
  assert.equal(result.delta_minutes, 0);
  assert.equal(result.recommendation, 'review_tradeoff');
});

test('each missing proof element independently prevents an observed keep recommendation', () => {
  const edits = [
    s => { s.meaning.matters = 'unknown'; },
    s => { s.meaning.reason = '  '; },
    s => { s.real_use.status = 'not_performed'; s.real_use.observed_at = null; },
    s => { s.real_use.description = ''; },
    s => { s.evidence_refs = []; },
    s => { s.carry_forward_refs = []; },
    s => { s.carry_forward_description = ''; },
    s => { s.comparison.comparable = 'no'; },
    s => { s.comparison.baseline_errors = null; },
    s => { s.comparison.assisted_errors = null; },
    s => { s.baseline.basis = 'unknown'; }
  ];
  for (const edit of edits) {
    const spec = trial(); edit(spec);
    const result = Q.evaluate(spec);
    assert.equal(result.recommendation, 'needs_evidence');
    assert.equal(result.evidence_state, 'incomplete');
  }
});

test('a trial that does not matter recommends a human drop review even if it is fast', () => {
  const spec = trial(); spec.meaning.matters = 'no'; spec.human_disposition = 'keep';
  const result = Q.evaluate(spec);
  assert.equal(result.recommendation, 'review_drop');
  assert.equal(result.evidence_state, 'incomplete');
  assert.equal(result.state, 'candidate');
});

test('recorded human choices never grant execution or admission authority', () => {
  for (const disposition of ['keep', 'mutate', 'drop', 'undecided']) {
    const spec = trial(); spec.human_disposition = disposition;
    const result = Q.evaluate(spec);
    assert.equal(result.recommendation, 'review_keep');
    assert.equal(result.state, 'candidate');
    assert.equal(result.authority, 'propose');
    assert.equal(Object.hasOwn(result, 'admitted'), false);
  }
});

test('missing required fields and arbitrary promotion fields are rejected at every object boundary', () => {
  for (const path of [[], ['meaning'], ['real_use'], ['baseline'], ['assisted'], ['comparison']]) {
    for (const operation of ['missing', 'extra']) {
      const spec = trial(); const target = path.length ? spec[path[0]] : spec;
      if (operation === 'extra') target.authority = 'execute';
      else delete target[Object.keys(target)[0]];
      assert.throws(() => Q.validate(spec));
      assert.throws(() => Q.evaluate(spec));
    }
  }
});

test('negative, nonfinite and nonnumeric costs, fractional error counts and overflowing totals are rejected', () => {
  for (const bad of [-1, NaN, Infinity, -Infinity, '3', undefined, true]) {
    const spec = trial(); spec.assisted.work = bad;
    assert.throws(() => Q.validate(spec));
  }
  for (const bad of [-1, 0.5, NaN, Infinity, '0', undefined]) {
    const spec = trial(); spec.comparison.baseline_errors = bad;
    assert.throws(() => Q.validate(spec));
  }
  const overflow = trial(); overflow.baseline.setup = Number.MAX_VALUE; overflow.baseline.work = Number.MAX_VALUE;
  assert.throws(() => Q.evaluate(overflow));
  const safe = Q.evaluate(trial());
  assert.deepEqual(JSON.parse(JSON.stringify(safe)), safe);
});

test('evidence and carry-forward links require distinct exact version pins within each list', () => {
  for (const key of ['evidence_refs', 'carry_forward_refs']) {
    for (const refs of [['source.example@latest'], ['source.example'], ['source.example@1.0'], ['source.example@1.0.0', 'source.example@1.0.0'], [null]]) {
      const spec = trial(); spec[key] = refs;
      assert.throws(() => Q.validate(spec));
    }
  }
});

test('performed use requires a real ISO timestamp rather than a missing or impossible calendar date', () => {
  for (const date of [null, '', 'yesterday', '2026-02-30T12:00:00Z', '2026-01-20', '2026-01-20T25:00:00Z']) {
    const spec = trial(); spec.real_use.observed_at = date;
    assert.throws(() => Q.validate(spec));
  }
  const offset = trial(); offset.real_use.observed_at = '2026-01-20T08:00:00-06:00';
  assert.equal(Q.validate(offset), true);
});

test('validation and evaluation do not change frozen valid inputs or rejected inputs', () => {
  const freeze = value => { if (value && typeof value === 'object') { Object.values(value).forEach(freeze); Object.freeze(value); } return value; };
  const spec = trial(); const before = clone(spec); freeze(spec);
  assert.equal(Q.validate(spec), true); Q.evaluate(spec);
  assert.deepEqual(spec, before);
  const invalid = trial(); invalid.assisted.cleanup = null; invalid.promote = true;
  const invalidBefore = clone(invalid);
  assert.throws(() => Q.evaluate(invalid));
  assert.deepEqual(invalid, invalidBefore);
});

test('zero costs and zero errors are known observations rather than missing values', () => {
  const spec = trial();
  for (const key of ['setup', 'work', 'supervision', 'cleanup', 'maintenance']) spec.assisted[key] = 0;
  spec.comparison.baseline_errors = 0; spec.comparison.assisted_errors = 0;
  const result = Q.evaluate(spec);
  assert.equal(result.assisted_total_minutes, 0);
  assert.equal(result.delta_minutes, 30);
  assert.equal(result.evidence_state, 'observed');
  assert.equal(result.recommendation, 'review_keep');
});

test('browser global evaluates the same JSON trial without Node or network capabilities', () => {
  const context = vm.createContext({});
  vm.runInContext(fs.readFileSync(require.resolve('./usefulness.js'), 'utf8'), context);
  context.input = JSON.stringify(trial());
  const result = vm.runInContext('JSON.stringify(QuirkUsefulness.evaluate(JSON.parse(input)))', context);
  assert.equal(JSON.parse(result).delta_minutes, 12);
  assert.equal(JSON.parse(result).recommendation, 'review_keep');
  assert.deepEqual(JSON.parse(result), Q.evaluate(trial()));
});

test('unknown use plus an estimated cost remains estimated evidence requiring a real trial', () => {
  const spec = trial();
  spec.real_use.status = 'unknown'; spec.real_use.observed_at = null;
  spec.assisted.basis = 'estimated'; spec.assisted.maintenance = null;
  const result = Q.evaluate(spec);
  assert.equal(result.evidence_state, 'estimated');
  assert.equal(result.recommendation, 'needs_evidence');
  assert.equal(result.delta_minutes, null);
  assert.equal(result.assisted_total_minutes, null);
});

test('complete cost records cannot display measured savings before real use and its supporting proof are complete', () => {
  for (const change of [
    s => { s.real_use.status = 'not_performed'; s.real_use.observed_at = null; },
    s => { s.evidence_refs = []; },
    s => { s.carry_forward_refs = []; },
    s => { s.comparison.comparable = 'unknown'; }
  ]) {
    const spec = trial(); change(spec);
    const result = Q.evaluate(spec);
    assert.equal(result.baseline_total_minutes, 30);
    assert.equal(result.assisted_total_minutes, 18);
    assert.equal(result.delta_minutes, null);
    assert.equal(result.evidence_state, 'incomplete');
    assert.equal(result.recommendation, 'needs_evidence');
  }
});
