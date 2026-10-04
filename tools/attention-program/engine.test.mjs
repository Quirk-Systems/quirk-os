import test from 'node:test';
import assert from 'node:assert/strict';
import {
  validateProgram, capacityForDate, evaluate, applyCommand, verifyReceipts,
} from './engine.mjs';

// Synthetic acceptance scenarios. Dates, obligations, names, and observations
// below are deliberately invented; none represent a person's actual evidence.
const NOW = '2030-06-03T12:00:00.000Z';
const AFTER_END = '2030-06-15T12:00:00.000Z';
const clone = value => structuredClone(value);
function initiative(id = 'demo-task') {
  return {
    id, title: `Demo ${id}`, beneficiary: 'Demo operator',
    done_when: 'A synthetic report meets its stated completion condition',
    next_move: 'Perform one manually controlled comparison', phase: 'queued',
    budget_minutes: 60, cluster_ids: [],
  };
}
function program() {
  return {
    api_version: 'quirk.dev/attention-program/v1alpha1', kind: 'Program',
    metadata: {
      id: 'demo-attention-program', title: 'Demo attention program',
      version: '0.1.0', status: 'candidate', owner_ref: 'demo/local-operator',
    },
    authority: {maximum_right: 'propose', external_effects: false}, revision: 0,
    goal: {
      id: 'demo-goal', statement: 'Complete a demo commitment with less effort',
      beneficiary: 'Demo operator', done_when: 'Two comparable useful completions',
    },
    trial: {
      start_date: '2030-06-01', end_date: '2030-06-14', phase: 'defined',
      disposition: null, reason: '',
    },
    bounds: {
      wip_limit: 2, external_in_progress: null, inventory_confirmed: false,
      setup_minutes: 0, maintenance_minutes: 0, costs_confirmed: false,
    },
    schedule: {
      timezone: 'America/Chicago', sleep_start: '22:00', sleep_end: '06:00',
      workdays: [1, 2, 3, 4, 5], work_start: '09:00', work_end: '17:00',
      prep_minutes: 15, commute_minutes: 15, weekend_anchor: '2030-06-01',
      weekend_start: '10:00', weekend_end: '14:00',
    },
    initiatives: [initiative()], sessions: [], observations: [], receipts: [],
  };
}
function observation(id, mode, overrides = {}) {
  return {
    id, initiative_id: 'demo-task', date: mode === 'baseline' ? '2030-05-31' : '2030-06-02',
    mode, comparison_key: 'same synthetic report',
    minutes: {operation: mode === 'baseline' ? 40 : 10, review: 5, correction: 5},
    completed: true, useful: true, protected_displaced: false,
    note: 'Synthetic human report for an acceptance test', source: 'human_report',
    ...overrides,
  };
}
function measuredProgram() {
  const p = program();
  p.bounds.costs_confirmed = true;
  p.bounds.inventory_confirmed = true;
  p.bounds.external_in_progress = 0;
  p.observations = [
    observation('baseline-1', 'baseline'),
    observation('trial-1', 'trial'), observation('trial-2', 'trial'),
  ];
  return p;
}
function slot(id = 'session-1', overrides = {}) {
  return {
    id, initiative_id: 'demo-task', date: '2030-06-04', start: '18:00',
    duration_minutes: 30, capacity_confirmed: true, phase: 'planned', ...overrides,
  };
}
async function command(p, cmd, now = NOW) {
  return applyCommand(p, cmd, {expectedRevision: p.revision, now});
}
async function ready(ids = ['demo-task']) {
  let p = program();
  p.initiatives = ids.map(initiative);
  p = await command(p, {type: 'confirm_inventory', external_in_progress: 0});
  p = await command(p, {type: 'set_trial_phase', phase: 'observing'});
  p = await command(p, {type: 'set_trial_phase', phase: 'trying'});
  for (const id of ids.slice(0, 2)) {
    p = await command(p, {type: 'set_initiative_phase', id, phase: 'doing'});
  }
  return p;
}
async function rejected(p, cmd, now = NOW) {
  const before = clone(p);
  await assert.rejects(() => command(p, cmd, now), error => {
    assert.equal(typeof error.code, 'string', 'rejection needs a usable machine code');
    assert.ok(error.code.length > 0);
    return true;
  });
  assert.deepEqual(p, before, 'a denied action must preserve its input');
}
function freezeDeep(value) {
  if (value && typeof value === 'object') {
    Object.values(value).forEach(freezeDeep);
    Object.freeze(value);
  }
  return value;
}
function overlapsReserved(result, start, end) {
  return result.reserved.some(interval => start < interval.end && end > interval.start);
}

test('an unclassified captured initiative and an unknown starting state are valid', () => {
  const p = program();
  assert.deepEqual(validateProgram(p), []);
  const result = evaluate(p, '2030-06-03');
  assert.equal(result.outcome, 'inconclusive');
  assert.equal(result.net_minutes, null);
  assert.equal(result.baseline_count, 0);
  assert.equal(result.trial_count, 0);
  assert.equal(typeof result.next_action, 'string');
  assert.ok(result.next_action.length > 0);
  assert.ok(result.findings.length > 0);
});

test('two useful uses without a baseline cannot manufacture savings', () => {
  const p = measuredProgram();
  p.observations = p.observations.filter(o => o.mode === 'trial');
  const result = evaluate(p, '2030-06-03');
  assert.equal(result.outcome, 'inconclusive');
  assert.equal(result.net_minutes, null);
});

test('zero-valued overhead is unknown until the operator confirms it', () => {
  const p = measuredProgram();
  p.bounds.costs_confirmed = false;
  const result = evaluate(p, '2030-06-03');
  assert.equal(result.outcome, 'inconclusive');
  assert.equal(result.net_minutes, null);
});

test('fewer than two useful comparable uses cannot earn a supported result', () => {
  const p = measuredProgram();
  p.observations.pop();
  assert.notEqual(evaluate(p, '2030-06-03').outcome, 'supported');
});

test('confirmed setup, operation, review, correction, and maintenance all affect net benefit', () => {
  const p = measuredProgram();
  p.bounds.setup_minutes = 10;
  p.bounds.maintenance_minutes = 5;
  const result = evaluate(p, '2030-06-03');
  assert.equal(result.outcome, 'supported');
  assert.equal(result.net_minutes, 45); // 2 × 50 - 2 × 20 - 10 - 5.
  assert.equal(result.baseline_count, 1);
  assert.equal(result.trial_count, 2);
  assert.equal(p.metadata.status, 'candidate');
  assert.equal(p.authority.maximum_right, 'propose');
});

test('a loss or break-even result is not described as improvement', () => {
  for (const setup_minutes of [60, 61]) {
    const p = measuredProgram();
    p.bounds.setup_minutes = setup_minutes;
    const result = evaluate(p, '2030-06-03');
    assert.equal(result.outcome, 'not_supported');
    assert.equal(result.net_minutes, 60 - setup_minutes);
  }
});

test('a failed trial incurs its full cost and earns no completed-task baseline credit', () => {
  const p = measuredProgram();
  p.bounds.setup_minutes = 30;
  p.bounds.maintenance_minutes = 10;
  p.observations.push(observation('failed-trial', 'trial', {
    completed: false, useful: false,
    minutes: {operation: 80, review: 5, correction: 5},
  }));
  const result = evaluate(p, '2030-06-03');
  assert.equal(result.outcome, 'not_supported');
  assert.equal(result.net_minutes, -70); // 2 × 50 - (20 + 20 + 90) - 30 - 10.
  assert.equal(result.trial_count, 3);
});

test('displacing a protected obligation defeats an otherwise positive result', () => {
  const p = measuredProgram();
  p.observations[1].protected_displaced = true;
  const result = evaluate(p, '2030-06-03');
  assert.equal(result.outcome, 'not_supported');
  assert.ok(result.net_minutes > 0);
});

for (const field of ['completed', 'useful', 'protected_displaced']) {
  test(`unknown ${field} remains unknown evidence`, () => {
    const p = measuredProgram();
    p.observations[1][field] = null;
    assert.deepEqual(validateProgram(p), []);
    const result = evaluate(p, '2030-06-03');
    assert.equal(result.outcome, 'inconclusive');
    assert.equal(result.net_minutes, null);
  });
}

test('comparisons use each task group baseline instead of a pooled mean', () => {
  const p = measuredProgram();
  p.observations = [
    observation('base-a', 'baseline', {comparison_key: 'small', minutes: {operation: 10, review: 0, correction: 0}}),
    observation('base-b', 'baseline', {comparison_key: 'large', minutes: {operation: 100, review: 0, correction: 0}}),
    observation('trial-a1', 'trial', {comparison_key: 'small', minutes: {operation: 5, review: 0, correction: 0}}),
    observation('trial-a2', 'trial', {comparison_key: 'small', minutes: {operation: 5, review: 0, correction: 0}}),
    observation('trial-b', 'trial', {comparison_key: 'large', minutes: {operation: 90, review: 0, correction: 0}}),
  ];
  const result = evaluate(p, '2030-06-03');
  assert.equal(result.net_minutes, 20);
  assert.equal(result.outcome, 'supported');
  p.observations = p.observations.filter(o => o.id !== 'base-b');
  assert.equal(evaluate(p, '2030-06-03').outcome, 'inconclusive');
  assert.equal(evaluate(p, '2030-06-03').net_minutes, null);
});

test('a similarly named comparison from another initiative cannot supply the baseline', () => {
  const p = measuredProgram();
  p.initiatives.push(initiative('other-task'));
  p.observations[0].initiative_id = 'other-task';
  assert.equal(evaluate(p, '2030-06-03').net_minutes, null);
  assert.equal(evaluate(p, '2030-06-03').outcome, 'inconclusive');
});

test('unknown outside commitments cannot be treated as confirmed global capacity', async () => {
  const p = program();
  await rejected(p, {type: 'set_initiative_phase', id: 'demo-task', phase: 'doing'});
  const result = evaluate(p, '2030-06-03');
  assert.ok(result.findings.length > 0);
});

test('measured savings cannot establish the whole goal while outside WIP is unknown', () => {
  const p = measuredProgram();
  p.bounds.inventory_confirmed = false;
  p.bounds.external_in_progress = null;
  const result = evaluate(p, '2030-06-03');
  assert.equal(result.net_minutes, 60, 'known measured benefit remains visible');
  assert.equal(result.outcome, 'inconclusive', 'aggregate goal still needs confirmed WIP');
});

test('measured savings do not satisfy a goal whose confirmed outside WIP exceeds the limit', () => {
  const p = measuredProgram();
  p.bounds.external_in_progress = 3;
  assert.equal(p.initiatives.filter(item => item.phase === 'doing').length, 0);
  assert.deepEqual(validateProgram(p), [], 'a truthful outside inventory can exceed its desired bound');
  const result = evaluate(p, '2030-06-03');
  assert.equal(result.net_minutes, 60, 'actual effort comparison is separate from conformance');
  assert.equal(result.outcome, 'not_supported');
});

test('a third discretionary initiative can be queued but cannot silently start', async () => {
  const p = await ready(['first', 'second', 'third']);
  await rejected(p, {type: 'set_initiative_phase', id: 'third', phase: 'doing'});
  assert.equal(p.initiatives.find(i => i.id === 'third').phase, 'queued');
  assert.equal(p.initiatives.filter(i => i.phase === 'doing').length, 2);
});

test('outside discretionary commitments consume the same two-initiative allowance', async () => {
  let p = program();
  p.initiatives = [initiative('first'), initiative('second')];
  p = await command(p, {type: 'confirm_inventory', external_in_progress: 1});
  p = await command(p, {type: 'set_initiative_phase', id: 'first', phase: 'doing'});
  await rejected(p, {type: 'set_initiative_phase', id: 'second', phase: 'doing'});
});

test('weekday capacity includes sleep, preparation, work, and both commutes', () => {
  const c = capacityForDate(program(), '2030-06-03');
  assert.equal(c.unallocated_minutes, 435);
  assert.deepEqual(c.free, [{start: 360, end: 510}, {start: 1035, end: 1320}]);
  assert.ok(overlapsReserved(c, 0, 360));
  assert.ok(overlapsReserved(c, 510, 1035));
  assert.ok(overlapsReserved(c, 1320, 1440));
});

test('alternating Saturday and Sunday commitments recur together across the fortnight boundary', () => {
  const p = program();
  for (const date of ['2030-06-01', '2030-06-02', '2030-06-15', '2030-06-16']) {
    const c = capacityForDate(p, date);
    assert.equal(c.unallocated_minutes, 675, date);
    assert.ok(overlapsReserved(c, 570, 855), date);
  }
  for (const date of ['2030-06-08', '2030-06-09']) {
    assert.equal(capacityForDate(p, date).unallocated_minutes, 960, date);
  }
});

test('overnight work blocks the next calendar day and interval union avoids double counting', () => {
  const p = program();
  p.schedule = {
    ...p.schedule, sleep_start: '03:00', sleep_end: '11:00', workdays: [1],
    work_start: '22:00', work_end: '02:00', weekend_anchor: null,
  };
  const tuesday = capacityForDate(p, '2030-06-04');
  assert.ok(overlapsReserved(tuesday, 0, 135));
  assert.equal(tuesday.unallocated_minutes, 825);
  assert.deepEqual(tuesday.free, [{start: 135, end: 180}, {start: 660, end: 1440}]);
  p.schedule.sleep_start = '22:00';
  p.schedule.sleep_end = '06:00';
  assert.equal(capacityForDate(p, '2030-06-04').unallocated_minutes, 960);
});

test('an apparently free slot still needs explicit human capacity confirmation', async () => {
  const p = await ready();
  await rejected(p, {type: 'plan_session', session: slot('unconfirmed', {capacity_confirmed: false})});
});

test('planning respects sleep, work, preparation, commute, and exact free boundaries', async () => {
  const p = await ready();
  for (const start of ['05:45', '08:15', '09:00', '17:00', '21:45']) {
    await rejected(p, {type: 'plan_session', session: slot(`conflict-${start}`, {start})});
  }
  const next = await command(p, {type: 'plan_session', session: slot('at-boundary', {start: '17:15'})});
  assert.equal(next.sessions.length, 1);
  assert.equal(next.sessions[0].start, '17:15');
});

test('sessions cannot overlap across initiatives or exceed an initiative effort budget', async () => {
  let p = await ready(['demo-task', 'other-task']);
  p = await command(p, {type: 'plan_session', session: slot('first', {duration_minutes: 40})});
  await rejected(p, {type: 'plan_session', session: slot('cross-initiative', {initiative_id: 'other-task', start: '18:20'})});
  await rejected(p, {type: 'plan_session', session: slot('over-budget', {start: '19:00', duration_minutes: 30})});
  const next = await command(p, {type: 'plan_session', session: slot('adjacent', {initiative_id: 'other-task', start: '18:40'})});
  assert.equal(next.sessions.length, 2);
});

test('sessions require doing status, valid trial dates, and a same-day duration', async () => {
  await rejected(program(), {type: 'plan_session', session: slot()});
  const p = await ready();
  for (const changes of [
    {date: '2030-05-31'}, {date: '2030-06-15'}, {date: '2030-06-02'},
    {start: '23:45', duration_minutes: 30}, {duration_minutes: 0},
  ]) {
    await rejected(p, {type: 'plan_session', session: slot('invalid-window', changes)});
  }
});

test('pausing blocks new planned work without destroying already recorded evidence', async () => {
  let p = await ready();
  p = await command(p, {type: 'set_trial_phase', phase: 'paused'});
  await rejected(p, {type: 'plan_session', session: slot()});
  const next = await command(p, {type: 'record_observation', observation: observation('late-report', 'trial')});
  assert.equal(next.observations.length, 1);
});

test('closing is a decision, preserves historical reporting, and cannot promote authority', async () => {
  let p = await ready();
  p = await command(p, {type: 'close_trial', disposition: 'keep', reason: 'Demo operator elects to retain the idea'});
  assert.equal(p.trial.phase, 'closed');
  assert.equal(evaluate(p, '2030-06-03').outcome, 'inconclusive');
  assert.equal(p.metadata.status, 'candidate');
  assert.deepEqual(p.authority, {maximum_right: 'propose', external_effects: false});
  await rejected(p, {type: 'plan_session', session: slot()});
  await rejected(p, {type: 'set_trial_phase', phase: 'trying'});
  const next = await command(p, {type: 'record_observation', observation: observation('historical', 'trial')});
  assert.equal(next.observations.length, 1);
  assert.equal(next.trial.phase, 'closed');
});

test('an expired trial does not renew itself and still accepts historical evidence and closure', async () => {
  let p = await ready();
  assert.equal(evaluate(p, '2030-06-15').trial_expired, true);
  await rejected(p, {type: 'set_trial_phase', phase: 'trying'}, AFTER_END);
  await rejected(p, {type: 'add_initiative', initiative: initiative('late-expansion')}, AFTER_END);
  p = await command(p, {type: 'record_observation', observation: observation('historical-after-expiry', 'trial')}, AFTER_END);
  p = await command(p, {type: 'close_trial', disposition: 'stop', reason: 'The finite demo trial ended'}, AFTER_END);
  assert.equal(p.trial.phase, 'closed');
  assert.equal(p.trial.end_date, '2030-06-14');
});

test('trial expiry and future-evidence checks use the program date across UTC midnight', async () => {
  const p = program();
  // 03:00 UTC on June 15 is still June 14 in this synthetic Chicago schedule.
  const next = await command(p, {
    type: 'add_initiative', initiative: initiative('last-local-day'),
  }, '2030-06-15T03:00:00.000Z');
  assert.equal(next.initiatives.length, 2);
  await rejected(p, {
    type: 'add_initiative', initiative: initiative('after-local-midnight'),
  }, '2030-06-15T06:00:00.000Z');
  // A June 3 observation is future evidence while the program date is June 2.
  await rejected(p, {
    type: 'record_observation', observation: observation('future-local-date', 'trial', {date: '2030-06-03'}),
  }, '2030-06-03T02:00:00.000Z');
});

test('observations cannot claim future work, fabricated fixture sources, or unbounded baseline history', async () => {
  const p = program();
  for (const changes of [
    {date: '2030-06-04'}, {mode: 'fixture'}, {source: 'tool_success'},
    {mode: 'baseline', date: '2030-04-30'}, {initiative_id: 'missing-task'},
  ]) {
    await rejected(p, {type: 'record_observation', observation: observation('bad-evidence', 'trial', changes)});
  }
});

test('valid baseline observations may precede the trial within its comparison window', async () => {
  const next = await command(program(), {type: 'record_observation', observation: observation('pre-trial-baseline', 'baseline')});
  assert.equal(next.observations.length, 1);
  assert.equal(next.observations[0].date, '2030-05-31');
});

test('cost correction is explicit, confirmed, and leaves earlier commands in its ledger', async () => {
  let p = await command(program(), {type: 'set_costs', setup_minutes: 12, maintenance_minutes: 3});
  assert.equal(p.bounds.costs_confirmed, true);
  p = await command(p, {type: 'set_costs', setup_minutes: 15, maintenance_minutes: 4});
  assert.equal(p.bounds.setup_minutes, 15);
  assert.equal(p.receipts.length, 2);
  assert.equal(p.receipts[0].command.setup_minutes, 12);
  assert.equal(p.receipts[1].command.setup_minutes, 15);
});

test('editing known obligations cannot silently invalidate an existing planned session', async () => {
  let p = await ready();
  p = await command(p, {type: 'plan_session', session: slot('existing-plan')});
  await rejected(p, {
    type: 'update_schedule', schedule: {...p.schedule, work_end: '19:00'},
  });
  assert.equal(p.schedule.work_end, '17:00');
  assert.equal(p.sessions[0].id, 'existing-plan');
});

test('a compatible schedule correction updates capacity and records the actual replacement', async () => {
  let p = await ready();
  p = await command(p, {type: 'plan_session', session: slot('preserved-plan')});
  const prior = clone(p);
  const schedule = {...p.schedule, work_end: '16:00'};
  const next = await command(p, {type: 'update_schedule', schedule});
  assert.deepEqual(p, prior);
  assert.equal(next.schedule.work_end, '16:00');
  assert.equal(next.sessions[0].id, 'preserved-plan');
  assert.equal(capacityForDate(next, '2030-06-04').unallocated_minutes, 495);
  assert.equal(next.receipts.at(-1).command.type, 'update_schedule');
  assert.deepEqual(next.receipts.at(-1).command.schedule, schedule);
  assert.deepEqual(next.receipts.at(-1).previous_value, prior.schedule);
  assert.deepEqual(await verifyReceipts(next), []);
});

test('cancelling a plan frees its full budget while preserving the original plan in receipts', async () => {
  // A seeded record has no earlier plan command to recover the original from.
  let p = program();
  p.bounds.inventory_confirmed = true;
  p.bounds.external_in_progress = 0;
  p.trial.phase = 'trying';
  p.initiatives[0].phase = 'doing';
  p.sessions = [slot('cancel-this', {duration_minutes: 60})];
  const originalPlan = clone(p.sessions[0]);
  assert.equal(p.revision, 0);
  assert.equal(p.receipts.length, 0);
  assert.deepEqual(validateProgram(p), []);
  p = await command(p, {type: 'cancel_session', id: 'cancel-this'});
  assert.equal(p.sessions.length, 0);
  assert.equal(p.receipts.at(-1).command.type, 'cancel_session');
  assert.deepEqual(p.receipts.at(-1).previous_value, originalPlan);
  p = await command(p, {
    type: 'plan_session', session: slot('replacement-plan', {duration_minutes: 60}),
  });
  assert.equal(p.sessions.length, 1);
  assert.equal(p.sessions[0].id, 'replacement-plan');
  assert.equal(p.sessions[0].duration_minutes, 60);
  assert.deepEqual(await verifyReceipts(p), []);
});

test('historical correction after closure and expiry changes arithmetic once and preserves the prior report', async () => {
  let p = await command(program(), {type: 'confirm_inventory', external_in_progress: 0});
  p = await command(p, {type: 'set_costs', setup_minutes: 0, maintenance_minutes: 0});
  for (const obs of [
    observation('original-baseline', 'baseline'),
    observation('correct-this', 'trial'), observation('unchanged-trial', 'trial'),
  ]) {
    p = await command(p, {type: 'record_observation', observation: obs});
  }
  const originalReportReceipt = clone(p.receipts.find(r => r.command.type === 'record_observation' && r.command.observation.id === 'correct-this'));
  assert.equal(evaluate(p, '2030-06-03').net_minutes, 60);
  p = await command(p, {type: 'close_trial', disposition: 'keep', reason: 'Demo trial disposition before a later correction'});
  const replacement = {
    ...p.observations.find(obs => obs.id === 'correct-this'),
    minutes: {operation: 15, review: 5, correction: 5},
    note: 'Synthetic operator corrects an earlier effort report',
  };
  const previousObservation = clone(p.observations.find(obs => obs.id === 'correct-this'));
  const next = await command(p, {type: 'correct_observation', observation: replacement}, AFTER_END);
  assert.equal(next.trial.phase, 'closed');
  assert.equal(next.observations.length, 3);
  assert.equal(next.observations.filter(obs => obs.id === 'correct-this').length, 1);
  assert.equal(evaluate(next, '2030-06-15').net_minutes, 55);
  assert.equal(evaluate(next, '2030-06-15').trial_count, 2);
  assert.deepEqual(next.receipts.find(r => r.receipt_hash === originalReportReceipt.receipt_hash), originalReportReceipt);
  assert.equal(originalReportReceipt.command.observation.minutes.operation, 10);
  assert.equal(next.receipts.at(-1).command.observation.minutes.operation, 15);
  assert.deepEqual(next.receipts.at(-1).previous_value, previousObservation);
  assert.deepEqual(await verifyReceipts(next), []);
});

test('a correction must identify an existing observation instead of silently creating evidence', async () => {
  const p = program();
  await rejected(p, {
    type: 'correct_observation', observation: observation('never-recorded', 'trial'),
  });
  assert.equal(p.observations.length, 0);
  assert.equal(p.receipts.length, 0);
});

test('successful and failed commands never mutate frozen input or command objects', async () => {
  const p = freezeDeep(program());
  const cmd = freezeDeep({type: 'confirm_inventory', external_in_progress: 0});
  const before = clone(p);
  const next = await command(p, cmd);
  assert.notEqual(next, p);
  assert.deepEqual(p, before);
  assert.equal(next.revision, p.revision + 1);
  assert.equal(next.bounds.inventory_confirmed, true);
  next.goal.statement = 'Change only the returned value';
  assert.equal(p.goal.statement, before.goal.statement);
  await rejected(p, {type: 'set_costs', setup_minutes: -1, maintenance_minutes: 0});
});

test('stale revisions reject a concurrent overwrite even if its proposed change is valid', async () => {
  const p = await command(program(), {type: 'confirm_inventory', external_in_progress: 0});
  await assert.rejects(
    () => applyCommand(p, {type: 'set_costs', setup_minutes: 1, maintenance_minutes: 0}, {expectedRevision: 0, now: NOW}),
    error => typeof error.code === 'string' && error.code.length > 0,
  );
  assert.equal(p.bounds.setup_minutes, 0);
  assert.equal(p.revision, 1);
});

test('valid receipt chains bind revisions and changed data without claiming independent authority', async () => {
  let p = await command(program(), {type: 'confirm_inventory', external_in_progress: 0});
  p = await command(p, {type: 'set_costs', setup_minutes: 4, maintenance_minutes: 1});
  assert.deepEqual(await verifyReceipts(p), []);
  const [first, last] = p.receipts;
  assert.equal(last.previous_receipt_hash, first.receipt_hash);
  assert.equal(last.revision, p.revision);
  assert.equal(last.actor, 'local_operator_self_report');
  assert.equal(last.recorded_at, NOW);
  for (const key of ['before_hash', 'after_hash', 'receipt_hash']) {
    assert.match(last[key], /^[a-f0-9]{64}$/i);
  }
  assert.notEqual(last.before_hash, last.after_hash);
  assert.equal(first.after_hash, last.before_hash);
});

test('receipt verification catches changed state, rewritten history, missing history, and broken hashes', async () => {
  let original = await command(program(), {type: 'confirm_inventory', external_in_progress: 0});
  original = await command(original, {type: 'set_costs', setup_minutes: 4, maintenance_minutes: 1});
  for (const mutate of [
    p => { p.bounds.setup_minutes = 0; },
    p => { p.receipts[0].command.external_in_progress = 1; },
    p => { p.receipts[1].previous_receipt_hash = '0'.repeat(64); },
    p => { p.receipts[1].receipt_hash = '0'.repeat(64); },
    p => { p.receipts.shift(); },
    p => { p.receipts = []; },
  ]) {
    const p = clone(original);
    mutate(p);
    assert.ok((await verifyReceipts(p)).length > 0, 'tampering must not verify cleanly');
  }
  assert.deepEqual(await verifyReceipts(original), []);
});

test('receipt hashing is stable across harmless JSON object key reordering', async () => {
  const p = await command(program(), {type: 'confirm_inventory', external_in_progress: 0});
  function reorder(value) {
    if (Array.isArray(value)) return value.map(reorder);
    if (value && typeof value === 'object') {
      return Object.fromEntries(Object.keys(value).reverse().map(key => [key, reorder(value[key])]));
    }
    return value;
  }
  assert.deepEqual(await verifyReceipts(reorder(p)), []);
});

test('appending a legitimate command cannot launder tampered prior evidence', async () => {
  const p = await command(program(), {
    type: 'record_observation', observation: observation('original-report', 'trial'),
  });
  p.observations[0].minutes.operation = 0;
  await rejected(p, {type: 'set_costs', setup_minutes: 1, maintenance_minutes: 0});
  assert.equal(p.receipts.length, 1);
});

test('untrusted imports reject authority, shape, identity, date, time, and numeric corruption', () => {
  const mutations = [
    ['live metadata', p => { p.metadata.status = 'live'; }],
    ['self-promoted authority', p => { p.authority.maximum_right = 'execute'; }],
    ['external effects', p => { p.authority.external_effects = true; }],
    ['undeclared top-level authority', p => { p.canon = true; }],
    ['undeclared nested key', p => { p.goal.approved = true; }],
    ['duplicate initiative IDs', p => { p.initiatives.push(clone(p.initiatives[0])); }],
    ['invalid calendar date', p => { p.trial.end_date = '2030-06-31'; }],
    ['oversized trial window', p => { p.trial.end_date = '2030-07-02'; }],
    ['reversed trial dates', p => { p.trial.end_date = '2030-05-31'; }],
    ['invalid clock', p => { p.schedule.sleep_start = '24:00'; }],
    ['invalid timezone', p => { p.schedule.timezone = 'Nowhere/Invalid'; }],
    ['negative budget', p => { p.initiatives[0].budget_minutes = -1; }],
    ['string budget', p => { p.initiatives[0].budget_minutes = '60'; }],
    ['negative cost', p => { p.bounds.setup_minutes = -1; }],
    ['nonfinite cost', p => { p.bounds.setup_minutes = Infinity; }],
    ['NaN cost', p => { p.bounds.setup_minutes = NaN; }],
    ['WIP authority expansion', p => { p.bounds.wip_limit = 3; }],
    ['fixture observation', p => { p.observations = [observation('fixture', 'fixture')]; }],
    ['unknown evidence field', p => { p.observations = [{...observation('unknown', 'trial'), independently_verified: true}]; }],
    ['duplicate observation IDs', p => { p.observations = [observation('same', 'trial'), observation('same', 'trial')]; }],
  ];
  for (const [label, mutate] of mutations) {
    const p = program();
    mutate(p);
    assert.ok(validateProgram(p).length > 0, label);
  }
  for (const malformed of [null, [], 'program', 42]) {
    assert.ok(validateProgram(malformed).length > 0);
  }
});

test('import validation detects schedule conflicts and over-budget sessions', async () => {
  const original = await ready();
  for (const sessions of [
    [slot('inside-work', {start: '10:00'})],
    [slot('a'), slot('b', {start: '18:15'})],
    [slot('a', {duration_minutes: 40}), slot('b', {start: '19:00', duration_minutes: 30})],
  ]) {
    const p = clone(original);
    p.sessions = sessions;
    assert.ok(validateProgram(p).length > 0);
  }
});

test('commands cannot smuggle authority changes or reserved phases through extra fields', async () => {
  const p = program();
  for (const cmd of [
    {type: 'promote', status: 'CANON'},
    {type: 'confirm_inventory', external_in_progress: 0, authority: {maximum_right: 'execute'}},
    {type: 'set_initiative_phase', id: 'demo-task', phase: 'active'},
    {type: 'add_initiative', initiative: {...initiative('canon-task'), phase: 'CANON'}},
  ]) {
    await rejected(p, cmd);
  }
});
