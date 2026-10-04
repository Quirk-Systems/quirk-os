/** Candidate-only attention trial. No adapters, network, notifications, or runtime grants. */
const API = 'quirk.dev/attention-program/v1alpha1';
const DAY = 86_400_000;
const INITIATIVE_PHASES = ['queued', 'doing', 'paused', 'done', 'stopped'];
const TRIAL_PHASES = ['defined', 'observing', 'trying', 'review', 'paused', 'closed'];
const DISPOSITIONS = ['keep', 'revise', 'pause', 'stop'];
const HASH = /^[a-f0-9]{64}$/;
const own = (value, key) => Object.prototype.hasOwnProperty.call(value, key);
const nonempty = value => typeof value === 'string' && value.trim().length > 0;
const finiteMinutes = value => typeof value === 'number' && Number.isFinite(value) && value >= 0;
const integer = value => Number.isSafeInteger(value) && value >= 0;
const problem = (code, message) => ({ code, message });

function fail(code, message) {
  throw Object.assign(new Error(message), { code });
}

function dateDay(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const [year, month, day] = value.split('-').map(Number);
  const date = new Date(0);
  date.setUTCHours(0, 0, 0, 0);
  date.setUTCFullYear(year, month - 1, day);
  if (date.getUTCFullYear() !== year || date.getUTCMonth() !== month - 1 || date.getUTCDate() !== day) return null;
  return date.getTime() / DAY;
}

function clockMinutes(value) {
  if (typeof value !== 'string' || !/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(value)) return null;
  return Number(value.slice(0, 2)) * 60 + Number(value.slice(3));
}

function weekday(day) { return ((day + 4) % 7 + 7) % 7; }
function totalEffort(observation) {
  return observation.minutes.operation + observation.minutes.review + observation.minutes.correction;
}

/** Reject non-JSON values before property validation, hashing, or cloning. */
function inspectJSON(value, path = '$', active = new WeakSet(), depth = 0) {
  if (depth > 80) return [problem('invalid_json', `${path}: excessive nesting`)];
  if (value === null || typeof value === 'string' || typeof value === 'boolean') return [];
  if (typeof value === 'number') return Number.isFinite(value) ? [] : [problem('invalid_json', `${path}: non-finite number`)];
  if (typeof value !== 'object') return [problem('invalid_json', `${path}: JSON value required`)];
  if (active.has(value)) return [problem('invalid_json', `${path}: cyclic data`)];
  const proto = Object.getPrototypeOf(value);
  if (!Array.isArray(value) && proto !== Object.prototype && proto !== null) return [problem('invalid_json', `${path}: plain object required`)];
  if (Object.getOwnPropertySymbols(value).length) return [problem('invalid_json', `${path}: symbol keys are not JSON`)];
  active.add(value);
  const findings = [];
  const keys = Object.getOwnPropertyNames(value).filter(key => !(Array.isArray(value) && key === 'length'));
  for (const key of keys) {
    const descriptor = Object.getOwnPropertyDescriptor(value, key);
    if (!descriptor || !own(descriptor, 'value') || !descriptor.enumerable) {
      findings.push(problem('invalid_json', `${path}.${key}: only enumerable data properties are allowed`));
    } else {
      findings.push(...inspectJSON(descriptor.value, `${path}.${key}`, active, depth + 1));
    }
  }
  if (Array.isArray(value) && (keys.length !== value.length || keys.some(key => !/^(?:0|[1-9]\d*)$/.test(key) || Number(key) >= value.length))) findings.push(problem('invalid_json', `${path}: dense array without extra properties required`));
  active.delete(value);
  return findings;
}

function objectShape(value, keys, path, findings) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    findings.push(problem('invalid_type', `${path}: object required`));
    return false;
  }
  for (const key of Object.keys(value)) if (!keys.includes(key)) findings.push(problem('unknown_key', `${path}.${key}: undeclared field`));
  for (const key of keys) if (!own(value, key)) findings.push(problem('missing_key', `${path}.${key}: required field`));
  return true;
}

function expect(condition, code, message, findings) {
  if (!condition) findings.push(problem(code, message));
}

function strings(value, fields, path, findings) {
  for (const key of fields) expect(nonempty(value[key]), 'invalid_text', `${path}.${key}: nonempty text required`, findings);
}

function validateInitiative(item, path, findings) {
  if (!objectShape(item, ['id', 'title', 'beneficiary', 'done_when', 'next_move', 'phase', 'budget_minutes', 'cluster_ids'], path, findings)) return;
  strings(item, ['id', 'title', 'beneficiary', 'done_when', 'next_move'], path, findings);
  expect(INITIATIVE_PHASES.includes(item.phase), 'invalid_phase', `${path}.phase: unsupported initiative phase`, findings);
  expect(integer(item.budget_minutes) && item.budget_minutes > 0, 'invalid_minutes', `${path}.budget_minutes: positive safe integer required`, findings);
  expect(Array.isArray(item.cluster_ids) && item.cluster_ids.every(id => Number.isInteger(id) && id >= 1 && id <= 111) && new Set(item.cluster_ids).size === item.cluster_ids.length,
    'invalid_clusters', `${path}.cluster_ids: unique optional cluster numbers 1–111 required`, findings);
}

function validateSession(item, path, findings) {
  if (!objectShape(item, ['id', 'initiative_id', 'date', 'start', 'duration_minutes', 'capacity_confirmed', 'phase'], path, findings)) return;
  strings(item, ['id', 'initiative_id'], path, findings);
  expect(dateDay(item.date) !== null, 'invalid_date', `${path}.date: valid calendar date required`, findings);
  const start = clockMinutes(item.start);
  expect(start !== null, 'invalid_time', `${path}.start: HH:MM required`, findings);
  expect(integer(item.duration_minutes) && item.duration_minutes > 0 && item.duration_minutes <= 1440 && start !== null && start + item.duration_minutes <= 1440,
    'invalid_minutes', `${path}: session must fit within one calendar day`, findings);
  expect(item.capacity_confirmed === true, 'capacity_unconfirmed', `${path}: explicit capacity confirmation required`, findings);
  expect(item.phase === 'planned', 'invalid_phase', `${path}.phase: planned required`, findings);
}

function validateObservation(item, path, findings) {
  if (!objectShape(item, ['id', 'initiative_id', 'date', 'mode', 'comparison_key', 'minutes', 'completed', 'useful', 'protected_displaced', 'note', 'source'], path, findings)) return;
  strings(item, ['id', 'initiative_id', 'comparison_key'], path, findings);
  expect(typeof item.note === 'string', 'invalid_text', `${path}.note: text required`, findings);
  expect(dateDay(item.date) !== null, 'invalid_date', `${path}.date: valid calendar date required`, findings);
  expect(['baseline', 'trial'].includes(item.mode), 'invalid_mode', `${path}.mode: baseline or trial required; fixtures are not observations`, findings);
  if (objectShape(item.minutes, ['operation', 'review', 'correction'], `${path}.minutes`, findings)) {
    for (const key of ['operation', 'review', 'correction']) expect(finiteMinutes(item.minutes[key]), 'invalid_minutes', `${path}.minutes.${key}: finite nonnegative number required`, findings);
    expect(Number.isFinite(item.minutes.operation + item.minutes.review + item.minutes.correction), 'invalid_minutes', `${path}.minutes: total must remain finite`, findings);
  }
  for (const key of ['completed', 'useful', 'protected_displaced']) expect(item[key] === null || typeof item[key] === 'boolean', 'invalid_type', `${path}.${key}: boolean or null required`, findings);
  expect(item.source === 'human_report', 'invalid_source', `${path}.source: human_report required`, findings);
}

function validateSchedule(schedule, findings) {
  const path = '$.schedule';
  if (!objectShape(schedule, ['timezone', 'sleep_start', 'sleep_end', 'workdays', 'work_start', 'work_end', 'prep_minutes', 'commute_minutes', 'weekend_anchor', 'weekend_start', 'weekend_end'], path, findings)) return;
  let timezoneValid = typeof schedule.timezone === 'string';
  if (timezoneValid) {
    try { new Intl.DateTimeFormat('en-US', { timeZone: schedule.timezone }); } catch { timezoneValid = false; }
  }
  expect(timezoneValid, 'invalid_timezone', `${path}.timezone: recognized time zone required`, findings);
  for (const key of ['sleep_start', 'sleep_end', 'work_start', 'work_end', 'weekend_start', 'weekend_end']) expect(clockMinutes(schedule[key]) !== null, 'invalid_time', `${path}.${key}: HH:MM required`, findings);
  for (const pair of [['sleep_start', 'sleep_end'], ['work_start', 'work_end'], ['weekend_start', 'weekend_end']]) expect(schedule[pair[0]] !== schedule[pair[1]], 'invalid_time', `${path}: equal start/end is ambiguous`, findings);
  expect(Array.isArray(schedule.workdays) && schedule.workdays.every(day => Number.isInteger(day) && day >= 0 && day <= 6) && new Set(schedule.workdays).size === schedule.workdays.length,
    'invalid_workdays', `${path}.workdays: unique day numbers 0–6 required`, findings);
  for (const key of ['prep_minutes', 'commute_minutes']) expect(integer(schedule[key]) && schedule[key] <= 720, 'invalid_minutes', `${path}.${key}: safe integer 0–720 required`, findings);
  const anchor = dateDay(schedule.weekend_anchor);
  expect(schedule.weekend_anchor === null || (anchor !== null && weekday(anchor) === 6), 'invalid_anchor', `${path}.weekend_anchor: Saturday date or null required`, findings);
  for (const [startKey, endKey] of [['work_start', 'work_end'], ['weekend_start', 'weekend_end']]) {
    const start = clockMinutes(schedule[startKey]); const end = clockMinutes(schedule[endKey]);
    if (start !== null && end !== null && integer(schedule.prep_minutes) && integer(schedule.commute_minutes)) {
      const length = ((end - start + 1440) % 1440) + schedule.prep_minutes + schedule.commute_minutes * 2;
      expect(length <= 1440, 'invalid_schedule', `${path}: work and travel reservation exceeds one day`, findings);
    }
  }
}

function commandFindings(command) {
  const findings = inspectJSON(command);
  if (findings.length) return findings;
  const keys = {
    confirm_inventory: ['type', 'external_in_progress'], add_initiative: ['type', 'initiative'],
    set_initiative_phase: ['type', 'id', 'phase'], plan_session: ['type', 'session'],
    record_observation: ['type', 'observation'], set_costs: ['type', 'setup_minutes', 'maintenance_minutes'],
    set_trial_phase: ['type', 'phase'], close_trial: ['type', 'disposition', 'reason'],
    update_schedule: ['type', 'schedule'], cancel_session: ['type', 'id'], correct_observation: ['type', 'observation'],
  };
  if (!command || typeof command !== 'object' || Array.isArray(command) || !own(keys, command.type)) return [problem('invalid_command', 'Unknown command type')];
  objectShape(command, keys[command.type], 'command', findings);
  switch (command.type) {
    case 'confirm_inventory': expect(integer(command.external_in_progress), 'invalid_inventory', 'external_in_progress: nonnegative safe integer required', findings); break;
    case 'add_initiative': validateInitiative(command.initiative, 'command.initiative', findings); expect(command.initiative?.phase === 'queued', 'invalid_phase', 'New initiatives must be queued', findings); break;
    case 'set_initiative_phase': strings(command, ['id'], 'command', findings); expect(INITIATIVE_PHASES.includes(command.phase), 'invalid_phase', 'Unsupported initiative phase', findings); break;
    case 'plan_session': validateSession(command.session, 'command.session', findings); break;
    case 'record_observation': case 'correct_observation': validateObservation(command.observation, 'command.observation', findings); break;
    case 'update_schedule': validateSchedule(command.schedule, findings); break;
    case 'cancel_session': strings(command, ['id'], 'command', findings); break;
    case 'set_costs': for (const key of ['setup_minutes', 'maintenance_minutes']) expect(finiteMinutes(command[key]), 'invalid_minutes', `${key}: finite nonnegative number required`, findings); break;
    case 'set_trial_phase': expect(['observing', 'trying', 'review', 'paused'].includes(command.phase), 'invalid_phase', 'Unsupported trial phase', findings); break;
    case 'close_trial': expect(DISPOSITIONS.includes(command.disposition), 'invalid_disposition', 'Unsupported trial disposition', findings); strings(command, ['reason'], 'command', findings); break;
  }
  return findings;
}

/** Calendar capacity represents known bounds, never a claim about all obligations. */
export function capacityForDate(program, date) {
  const day = dateDay(date);
  if (day === null) fail('invalid_date', 'Capacity date must be YYYY-MM-DD');
  const findings = [];
  validateSchedule(program?.schedule, findings);
  if (findings.length) fail(findings[0].code, findings[0].message);
  const schedule = program.schedule;
  const intervals = [];
  const add = (start, end, label) => {
    const clippedStart = Math.max(0, start), clippedEnd = Math.min(1440, end);
    if (clippedStart < clippedEnd) intervals.push({ start: clippedStart, end: clippedEnd, label });
  };
  const addCycle = (startText, endText, offset, label, prep = 0, commute = 0) => {
    const start = clockMinutes(startText), rawEnd = clockMinutes(endText);
    const end = rawEnd <= start ? rawEnd + 1440 : rawEnd;
    add(offset * 1440 + start - prep - commute, offset * 1440 + end + commute, label);
  };
  const anchor = dateDay(schedule.weekend_anchor);
  for (const offset of [-1, 0, 1]) {
    const onDay = day + offset;
    addCycle(schedule.sleep_start, schedule.sleep_end, offset, 'Sleep');
    if (schedule.workdays.includes(weekday(onDay))) addCycle(schedule.work_start, schedule.work_end, offset, 'Work, preparation and commute', schedule.prep_minutes, schedule.commute_minutes);
    if (anchor !== null) {
      const sinceAnchor = ((onDay - anchor) % 14 + 14) % 14;
      if (sinceAnchor === 0 || sinceAnchor === 1) addCycle(schedule.weekend_start, schedule.weekend_end, offset, 'Alternating weekend work, preparation and commute', schedule.prep_minutes, schedule.commute_minutes);
    }
  }
  intervals.sort((a, b) => a.start - b.start || a.end - b.end);
  const reserved = [];
  for (const interval of intervals) {
    const last = reserved.at(-1);
    if (last && interval.start <= last.end) {
      last.end = Math.max(last.end, interval.end);
      if (!last.labels.includes(interval.label)) last.labels.push(interval.label);
    } else reserved.push({ start: interval.start, end: interval.end, labels: [interval.label] });
  }
  const free = []; let cursor = 0;
  for (const interval of reserved) {
    if (cursor < interval.start) free.push({ start: cursor, end: interval.start });
    cursor = interval.end;
  }
  if (cursor < 1440) free.push({ start: cursor, end: 1440 });
  return { reserved: reserved.map(({ start, end, labels }) => ({ start, end, label: labels.join('; ') })), free, unallocated_minutes: free.reduce((sum, slot) => sum + slot.end - slot.start, 0) };
}

export function validateProgram(program) {
  const findings = inspectJSON(program);
  if (findings.length) return findings;
  if (!objectShape(program, ['api_version', 'kind', 'metadata', 'authority', 'revision', 'goal', 'trial', 'bounds', 'schedule', 'initiatives', 'sessions', 'observations', 'receipts'], '$', findings)) return findings;
  expect(program.api_version === API && program.kind === 'Program', 'invalid_program', 'Program API and kind must match the candidate contract', findings);
  if (objectShape(program.metadata, ['id', 'title', 'version', 'status', 'owner_ref'], '$.metadata', findings)) {
    strings(program.metadata, ['id', 'title', 'owner_ref'], '$.metadata', findings);
    expect(program.metadata.version === '0.1.0' && program.metadata.status === 'candidate', 'authority_violation', 'Metadata must remain version 0.1.0 / candidate', findings);
  }
  if (objectShape(program.authority, ['maximum_right', 'external_effects'], '$.authority', findings)) expect(program.authority.maximum_right === 'propose' && program.authority.external_effects === false, 'authority_violation', 'Only propose authority with no external effects is admitted', findings);
  expect(integer(program.revision), 'invalid_revision', 'revision must be a nonnegative safe integer', findings);
  if (objectShape(program.goal, ['id', 'statement', 'beneficiary', 'done_when'], '$.goal', findings)) strings(program.goal, ['id', 'statement', 'beneficiary', 'done_when'], '$.goal', findings);
  if (objectShape(program.trial, ['start_date', 'end_date', 'phase', 'disposition', 'reason'], '$.trial', findings)) {
    const start = dateDay(program.trial.start_date), end = dateDay(program.trial.end_date);
    expect(start !== null && end !== null && end >= start && end - start < 31, 'invalid_trial_dates', 'Trial must span 1–31 inclusive valid calendar dates', findings);
    expect(TRIAL_PHASES.includes(program.trial.phase), 'invalid_phase', 'Unsupported trial phase', findings);
    expect(typeof program.trial.reason === 'string', 'invalid_text', 'Trial reason must be text', findings);
    if (program.trial.phase === 'closed') expect(DISPOSITIONS.includes(program.trial.disposition) && nonempty(program.trial.reason), 'invalid_disposition', 'Closed trial requires disposition and reason', findings);
    else expect(program.trial.disposition === null && program.trial.reason === '', 'invalid_disposition', 'Open trial cannot carry a closing decision', findings);
  }
  if (objectShape(program.bounds, ['wip_limit', 'external_in_progress', 'inventory_confirmed', 'setup_minutes', 'maintenance_minutes', 'costs_confirmed'], '$.bounds', findings)) {
    expect(integer(program.bounds.wip_limit) && program.bounds.wip_limit >= 1 && program.bounds.wip_limit <= 2, 'invalid_wip_limit', 'Trial WIP limit must be 1 or 2', findings);
    expect(program.bounds.external_in_progress === null || integer(program.bounds.external_in_progress), 'invalid_inventory', 'Outside WIP must be unknown or a nonnegative safe integer', findings);
    expect(typeof program.bounds.inventory_confirmed === 'boolean', 'invalid_type', 'inventory_confirmed must be boolean', findings);
    expect(program.bounds.inventory_confirmed ? integer(program.bounds.external_in_progress) : program.bounds.external_in_progress === null, 'invalid_inventory', 'Inventory confirmation and known count must agree', findings);
    expect(typeof program.bounds.costs_confirmed === 'boolean', 'invalid_type', 'costs_confirmed must be boolean', findings);
    for (const key of ['setup_minutes', 'maintenance_minutes']) expect(finiteMinutes(program.bounds[key]), 'invalid_minutes', `${key}: finite nonnegative number required`, findings);
    expect(Number.isFinite(program.bounds.setup_minutes + program.bounds.maintenance_minutes), 'invalid_minutes', 'Combined costs must remain finite', findings);
  }
  validateSchedule(program.schedule, findings);
  for (const [key, validator] of [['initiatives', validateInitiative], ['sessions', validateSession], ['observations', validateObservation]]) {
    if (!Array.isArray(program[key])) findings.push(problem('invalid_type', `${key}: array required`));
    else program[key].forEach((item, index) => validator(item, `$.${key}[${index}]`, findings));
  }
  if (!Array.isArray(program.receipts)) findings.push(problem('invalid_type', 'receipts: array required'));
  else program.receipts.forEach((receipt, index) => {
    const path = `$.receipts[${index}]`;
    if (!objectShape(receipt, ['command', 'before_hash', 'after_hash', 'previous_receipt_hash', 'receipt_hash', 'revision', 'recorded_at', 'actor', 'previous_value'], path, findings)) return;
    findings.push(...commandFindings(receipt.command).map(finding => ({ ...finding, message: `${path}: ${finding.message}` })));
    switch (receipt.command?.type) {
      case 'update_schedule': validateSchedule(receipt.previous_value, findings); break;
      case 'cancel_session':
        validateSession(receipt.previous_value, `${path}.previous_value`, findings);
        expect(receipt.previous_value?.id === receipt.command.id, 'invalid_previous_value', `${path}: canceled session ID must match its prior value`, findings);
        break;
      case 'correct_observation':
        validateObservation(receipt.previous_value, `${path}.previous_value`, findings);
        expect(receipt.previous_value?.id === receipt.command.observation?.id, 'invalid_previous_value', `${path}: corrected observation ID must match its prior value`, findings);
        break;
      default: expect(receipt.previous_value === null, 'invalid_previous_value', `${path}: previous_value must be null for this command`, findings);
    }
    for (const key of ['before_hash', 'after_hash', 'receipt_hash']) expect(typeof receipt[key] === 'string' && HASH.test(receipt[key]), 'invalid_hash', `${path}.${key}: SHA-256 hex required`, findings);
    expect(receipt.previous_receipt_hash === null || (typeof receipt.previous_receipt_hash === 'string' && HASH.test(receipt.previous_receipt_hash)), 'invalid_hash', `${path}.previous_receipt_hash: hash or null required`, findings);
    expect(integer(receipt.revision) && receipt.revision === index + 1, 'invalid_revision', `${path}: contiguous receipt revision required`, findings);
    expect(validInstant(receipt.recorded_at), 'invalid_timestamp', `${path}.recorded_at: UTC ISO timestamp required`, findings);
    expect(receipt.actor === 'local_operator_self_report', 'invalid_actor', `${path}: local self-report actor required`, findings);
  });
  if (Array.isArray(program.receipts)) expect(program.revision === program.receipts.length, 'invalid_revision', 'Revision must match receipt count', findings);
  if (findings.length) return findings;

  const ids = new Set([program.metadata.id, program.goal.id]);
  expect(ids.size === 2, 'duplicate_id', 'Program and goal IDs must be unique', findings);
  for (const record of [...program.initiatives, ...program.sessions, ...program.observations]) {
    expect(!ids.has(record.id), 'duplicate_id', `Duplicate record ID: ${record.id}`, findings); ids.add(record.id);
  }
  const initiatives = new Map(program.initiatives.map(item => [item.id, item]));
  const doing = program.initiatives.filter(item => item.phase === 'doing').length;
  if (doing) {
    expect(program.bounds.inventory_confirmed, 'inventory_unknown', 'Starting discretionary work requires confirmed outside inventory', findings);
    expect(doing + (program.bounds.external_in_progress ?? 0) <= program.bounds.wip_limit, 'wip_exceeded', 'Doing initiatives plus confirmed outside WIP exceed the limit', findings);
  }
  const trialStart = dateDay(program.trial.start_date), trialEnd = dateDay(program.trial.end_date);
  const sessionTotals = new Map();
  for (const session of program.sessions) {
    const item = initiatives.get(session.initiative_id), date = dateDay(session.date);
    expect(Boolean(item), 'missing_initiative', `Session ${session.id} references an unknown initiative`, findings);
    expect(date >= trialStart && date <= trialEnd, 'outside_trial', `Session ${session.id} is outside trial dates`, findings);
    const start = clockMinutes(session.start), end = start + session.duration_minutes;
    const capacity = capacityForDate(program, session.date);
    expect(!capacity.reserved.some(slot => start < slot.end && end > slot.start), 'reserved_overlap', `Session ${session.id} overlaps known protected time`, findings);
    sessionTotals.set(session.initiative_id, (sessionTotals.get(session.initiative_id) ?? 0) + session.duration_minutes);
  }
  const ordered = [...program.sessions].sort((a, b) => a.date.localeCompare(b.date) || clockMinutes(a.start) - clockMinutes(b.start));
  for (let index = 1; index < ordered.length; index++) {
    const prior = ordered[index - 1], current = ordered[index];
    expect(prior.date !== current.date || clockMinutes(current.start) >= clockMinutes(prior.start) + prior.duration_minutes,
      'session_overlap', `Sessions ${prior.id} and ${current.id} overlap`, findings);
  }
  for (const [id, total] of sessionTotals) if (initiatives.has(id)) expect(total <= initiatives.get(id).budget_minutes, 'budget_exceeded', `Sessions exceed initiative ${id} effort budget`, findings);
  for (const observation of program.observations) {
    expect(initiatives.has(observation.initiative_id), 'missing_initiative', `Observation ${observation.id} references an unknown initiative`, findings);
    const day = dateDay(observation.date);
    const earliest = observation.mode === 'baseline' ? trialStart - 31 : trialStart;
    expect(day >= earliest && day <= trialEnd, 'outside_trial', `Observation ${observation.id} is outside its permitted date range`, findings);
  }
  return findings;
}

/** Report only observed benefit; evidence quality and program authority are separate. */
export function evaluate(program, asOfDate) {
  const findings = validateProgram(program);
  const asOf = dateDay(asOfDate);
  if (asOf === null) findings.push(problem('invalid_date', 'Evaluation date must be YYYY-MM-DD'));
  if (findings.length) return { outcome: 'inconclusive', net_minutes: null, baseline_count: 0, trial_count: 0, findings, next_action: 'Repair invalid input before evaluating.', trial_expired: false };
  const expired = asOf > dateDay(program.trial.end_date);
  const observations = program.observations.filter(item => dateDay(item.date) <= asOf);
  const baseline = observations.filter(item => item.mode === 'baseline');
  const trial = observations.filter(item => item.mode === 'trial');
  if (observations.length !== program.observations.length) findings.push(problem('future_evidence', 'Observations after the evaluation date are excluded.'));
  const inventoryKnown = program.bounds.inventory_confirmed;
  const wipExceeded = inventoryKnown && program.initiatives.filter(item => item.phase === 'doing').length + program.bounds.external_in_progress > program.bounds.wip_limit;
  if (!inventoryKnown) findings.push(problem('inventory_unknown', 'Outside discretionary WIP is unknown; global WIP conformance is unproven.'));
  else if (wipExceeded) findings.push(problem('wip_exceeded', 'Confirmed outside commitments exceed the trial WIP bound; reduce commitments before new work.'));
  if (!program.bounds.costs_confirmed) findings.push(problem('costs_unknown', 'Confirm setup and maintenance costs, including explicit zeros, before claiming net benefit.'));
  if (expired) findings.push(problem('trial_expired', 'Trial dates have ended; record remaining historical evidence and close without automatic renewal.'));
  const unknown = [...baseline, ...trial].some(item => item.completed === null || item.useful === null || item.protected_displaced === null);
  if (unknown) findings.push(problem('evidence_unknown', 'Completion, usefulness, or protected-obligation effects remain unknown.'));
  const keyFor = item => JSON.stringify([item.initiative_id, item.comparison_key]);
  const baselines = new Map();
  for (const item of baseline.filter(item => item.completed === true && item.useful === true)) {
    const key = keyFor(item); const group = baselines.get(key) ?? [];
    group.push(totalEffort(item)); baselines.set(key, group);
  }
  const missing = trial.some(item => !baselines.has(keyFor(item)));
  if (missing) findings.push(problem('baseline_missing', 'Every trial comparison needs a completed, useful baseline with the same initiative and task specification.'));
  const usefulTrials = trial.filter(item => item.completed === true && item.useful === true);
  if (usefulTrials.length < 2) findings.push(problem('insufficient_uses', 'At least two completed, useful comparable trial uses are needed to support benefit.'));
  const displaced = trial.some(item => item.protected_displaced === true);
  const failed = trial.some(item => item.completed === false || item.useful === false);
  if (displaced) findings.push(problem('protected_displaced', 'A trial use reportedly displaced a protected obligation.'));
  if (failed) findings.push(problem('use_failed', 'A trial use was incomplete or not useful; its full effort still counts as cost.'));
  let net = null;
  if (trial.length && !missing && !unknown && program.bounds.costs_confirmed) {
    const counterfactual = usefulTrials.reduce((sum, item) => {
      const values = baselines.get(keyFor(item));
      return sum + values.reduce((subtotal, minutes) => subtotal + minutes / values.length, 0);
    }, 0);
    const cost = trial.reduce((sum, item) => sum + totalEffort(item), 0) + program.bounds.setup_minutes + program.bounds.maintenance_minutes;
    if (Number.isFinite(counterfactual) && Number.isFinite(cost)) net = counterfactual - cost;
    else findings.push(problem('arithmetic_overflow', 'Recorded costs exceed finite arithmetic; no benefit claim is available.'));
  }
  let outcome = 'inconclusive';
  if (net !== null && (displaced || failed || net <= 0 || wipExceeded)) outcome = 'not_supported';
  else if (net !== null && usefulTrials.length >= 2 && inventoryKnown) outcome = 'supported';
  if (net !== null && net <= 0) findings.push(problem('no_net_benefit', 'Recorded trial benefit does not exceed all recorded human effort costs.'));
  findings.push(problem('self_report_only', 'This is a local self-report comparison; it does not independently verify outcomes, authorize scaling, or confer Canon status.'));
  const next = program.trial.phase === 'closed' ? 'Read the recorded disposition; closed trials do not reopen automatically.'
    : expired ? 'Record any remaining historical evidence and close with keep, revise, pause, or stop.'
    : !inventoryKnown ? 'Confirm the number of outside discretionary commitments before starting program work or claiming overall conformance.'
    : wipExceeded ? 'Reduce or pause discretionary commitments before starting additional program work.'
    : !program.bounds.costs_confirmed ? 'Confirm setup and maintenance minutes, including explicit zeros.'
    : !trial.length || missing ? 'Record a comparable baseline and the next actual use; leave benefit unproven until evidence exists.'
    : unknown ? 'Resolve unknown evidence with the person who performed the work.'
    : outcome === 'not_supported' ? 'Review the measured burden or displaced obligation and choose revise, pause, or stop.'
    : outcome === 'supported' ? 'Choose and record a trial disposition; any expansion remains a separate decision.'
    : 'Observe another comparable real use within the existing trial and capacity bounds.';
  return { outcome, net_minutes: net, baseline_count: baseline.length, trial_count: trial.length, findings, next_action: next, trial_expired: expired };
}

function canonical(value) {
  if (value === null || typeof value !== 'object') return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  return `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}`;
}

async function digest(value) {
  if (!globalThis.crypto?.subtle) fail('crypto_unavailable', 'SHA-256 is unavailable in this browser context; use the Node CLI or a secure browser context.');
  const bytes = new TextEncoder().encode(canonical(value));
  return [...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256', bytes))].map(byte => byte.toString(16).padStart(2, '0')).join('');
}

function body(program) {
  const { receipts: _receipts, ...record } = program;
  return record;
}

function validInstant(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(value)) return false;
  const timestamp = new Date(value);
  return Number.isFinite(timestamp.getTime()) && timestamp.toISOString() === value;
}

function instantAndDate(now, timezone) {
  const instant = now === undefined ? new Date() : now instanceof Date ? new Date(now.getTime()) : typeof now === 'string' && validInstant(now) ? new Date(now) : null;
  if (!instant || !Number.isFinite(instant.getTime())) fail('invalid_timestamp', 'now must be a valid Date or UTC ISO timestamp with milliseconds');
  const parts = new Intl.DateTimeFormat('en-US', { timeZone: timezone, year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(instant);
  const date = ['year', 'month', 'day'].map(type => parts.find(part => part.type === type).value).join('-');
  return { recordedAt: instant.toISOString(), date, day: dateDay(date) };
}

/** Hashes detect accidental/tampered local history, not authenticity or independent approval. */
export async function verifyReceipts(program) {
  const findings = validateProgram(program);
  if (findings.length) return findings;
  program = JSON.parse(JSON.stringify(program));
  let previous = null;
  for (const receipt of program.receipts) {
    const { receipt_hash: expected, ...unsigned } = receipt;
    if (await digest(unsigned) !== expected) findings.push(problem('receipt_hash_mismatch', `Receipt ${receipt.revision} content hash does not match`));
    if (receipt.previous_receipt_hash !== (previous?.receipt_hash ?? null)) findings.push(problem('receipt_chain_mismatch', `Receipt ${receipt.revision} is not linked to its predecessor`));
    if (previous && receipt.before_hash !== previous.after_hash) findings.push(problem('state_chain_mismatch', `Receipt ${receipt.revision} prior state does not match its predecessor`));
    if (previous && receipt.recorded_at < previous.recorded_at) findings.push(problem('receipt_clock_regression', `Receipt ${receipt.revision} timestamp precedes its predecessor`));
    previous = receipt;
  }
  if (previous && previous.after_hash !== await digest(body(program))) findings.push(problem('current_state_mismatch', 'Current program does not match the final receipt'));
  return findings;
}

/** Pure copy-on-write commands. Success records only a local record change. */
export async function applyCommand(program, command, { expectedRevision, now } = {}) {
  const inputFindings = validateProgram(program);
  if (inputFindings.length) fail(inputFindings[0].code, inputFindings[0].message);
  if (expectedRevision !== undefined && expectedRevision !== program.revision) fail('stale_revision', 'The program changed; reload and review before applying the command.');
  const commandErrors = commandFindings(command);
  if (commandErrors.length) fail(commandErrors[0].code, commandErrors[0].message);
  // Freeze inputs before the first await so callers cannot change the checked data mid-command.
  program = JSON.parse(JSON.stringify(program));
  command = JSON.parse(JSON.stringify(command));
  const time = instantAndDate(now, program.schedule.timezone);
  const integrity = await verifyReceipts(program);
  if (integrity.length) fail(integrity[0].code, integrity[0].message);
  const lastReceipt = program.receipts.at(-1);
  if (lastReceipt && time.recordedAt < lastReceipt.recorded_at) fail('clock_regression', 'Command timestamp precedes the latest receipt; correct the clock before continuing.');
  const closed = program.trial.phase === 'closed', expired = time.day > dateDay(program.trial.end_date);
  const evidenceCommand = ['record_observation', 'correct_observation', 'set_costs', 'close_trial'].includes(command.type);
  if ((closed || expired) && !evidenceCommand) fail(closed ? 'trial_closed' : 'trial_expired', 'This trial accepts historical evidence, cost corrections and closure only.');
  if (closed && command.type === 'close_trial') fail('trial_closed', 'The trial already has a closing disposition.');
  const startsWork = command.type === 'plan_session' || (command.type === 'set_initiative_phase' && command.phase === 'doing');
  if (program.trial.phase === 'paused' && startsWork) fail('trial_paused', 'Resume the trial explicitly before starting or planning work.');
  const next = JSON.parse(JSON.stringify(program));
  const copiedCommand = JSON.parse(JSON.stringify(command));
  let previousValue = null;
  switch (copiedCommand.type) {
    case 'confirm_inventory': next.bounds.external_in_progress = copiedCommand.external_in_progress; next.bounds.inventory_confirmed = true; break;
    case 'add_initiative': next.initiatives.push(copiedCommand.initiative); break;
    case 'set_initiative_phase': {
      const item = next.initiatives.find(item => item.id === copiedCommand.id);
      if (!item) fail('missing_initiative', 'Initiative not found.');
      if (['done', 'stopped'].includes(item.phase) && copiedCommand.phase !== item.phase) fail('initiative_terminal', 'A finished or stopped initiative cannot reopen in this trial.');
      if (copiedCommand.phase === 'doing' && !next.bounds.inventory_confirmed) fail('inventory_unknown', 'Confirm outside discretionary commitments before starting work.');
      item.phase = copiedCommand.phase;
      break;
    }
    case 'plan_session': {
      const session = copiedCommand.session;
      const item = next.initiatives.find(item => item.id === session.initiative_id);
      if (!item || item.phase !== 'doing') fail('initiative_not_doing', 'Sessions require a doing initiative.');
      if (dateDay(session.date) < time.day) fail('historical_session', 'New sessions must be planned for today or a later trial date.');
      next.sessions.push(session);
      break;
    }
    case 'record_observation':
      if (dateDay(copiedCommand.observation.date) > time.day) fail('future_observation', 'Observations can describe only today or earlier work.');
      next.observations.push(copiedCommand.observation);
      break;
    case 'correct_observation': {
      const index = next.observations.findIndex(item => item.id === copiedCommand.observation.id);
      if (index < 0) fail('missing_observation', 'Correction must identify an existing observation.');
      if (dateDay(copiedCommand.observation.date) > time.day) fail('future_observation', 'Corrections can describe only today or earlier work.');
      previousValue = next.observations[index];
      next.observations[index] = copiedCommand.observation;
      break;
    }
    case 'update_schedule': previousValue = next.schedule; next.schedule = copiedCommand.schedule; break;
    case 'cancel_session': {
      const index = next.sessions.findIndex(item => item.id === copiedCommand.id);
      if (index < 0) fail('missing_session', 'Session not found.');
      previousValue = next.sessions[index];
      next.sessions.splice(index, 1);
      break;
    }
    case 'set_costs': next.bounds.setup_minutes = copiedCommand.setup_minutes; next.bounds.maintenance_minutes = copiedCommand.maintenance_minutes; next.bounds.costs_confirmed = true; break;
    case 'set_trial_phase': {
      const allowed = {
        defined: ['observing', 'trying', 'review', 'paused'], observing: ['trying', 'review', 'paused'],
        trying: ['review', 'paused'], review: ['observing', 'trying', 'paused'], paused: ['observing', 'trying', 'review'],
      };
      if (copiedCommand.phase !== next.trial.phase && !allowed[next.trial.phase]?.includes(copiedCommand.phase)) fail('invalid_transition', 'Unsupported trial phase transition.');
      next.trial.phase = copiedCommand.phase;
      break;
    }
    case 'close_trial': next.trial.phase = 'closed'; next.trial.disposition = copiedCommand.disposition; next.trial.reason = copiedCommand.reason; break;
  }
  const resultingFindings = validateProgram(next);
  if (resultingFindings.length) fail(resultingFindings[0].code, resultingFindings[0].message);
  if (next.revision === Number.MAX_SAFE_INTEGER) fail('revision_overflow', 'Revision limit reached.');
  next.revision += 1;
  const unsigned = {
    command: copiedCommand, before_hash: await digest(body(program)), after_hash: await digest(body(next)),
    previous_receipt_hash: lastReceipt?.receipt_hash ?? null, revision: next.revision,
    recorded_at: time.recordedAt, actor: 'local_operator_self_report', previous_value: previousValue,
  };
  next.receipts.push({ ...unsigned, receipt_hash: await digest(unsigned) });
  return next;
}
