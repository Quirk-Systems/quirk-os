(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.QuirkUsefulness = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  // Pure candidate assessment. Supplied observations and references are not authenticated here.
  const COST_FIELDS = ['setup', 'work', 'supervision', 'cleanup', 'maintenance'];
  const REF = /^[A-Za-z0-9][A-Za-z0-9._:-]*@\d+\.\d+\.\d+$/;
  const DATE = /^(\d{4})-(\d{2})-(\d{2})T([01]\d|2[0-3]):([0-5]\d):([0-5]\d)(?:\.\d+)?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$/;

  function assert(condition, message) {
    if (!condition) throw new Error(message);
  }
  function shape(value, fields, path) {
    assert(value !== null && typeof value === 'object' && !Array.isArray(value), path + ' must be an object.');
    const actual = Reflect.ownKeys(value);
    assert(actual.length === fields.length && actual.every(key => fields.includes(key)), path + ' must contain exactly the required fields.');
  }
  function string(value, path) {
    assert(typeof value === 'string', path + ' must be a string.');
  }
  function text(value) { return value.trim().length > 0; }
  function one(value, choices, path) {
    assert(choices.includes(value), path + ' has an unsupported value.');
  }
  function timestamp(value) {
    if (typeof value !== 'string') return false;
    const parts = DATE.exec(value);
    if (!parts || !Number.isFinite(Date.parse(value))) return false;
    const year = Number(parts[1]), month = Number(parts[2]), day = Number(parts[3]);
    const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
    const days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    return month >= 1 && month <= 12 && day >= 1 && day <= days[month - 1];
  }
  function refs(value, path) {
    assert(Array.isArray(value), path + ' must be an array.');
    for (const item of value) assert(typeof item === 'string' && REF.test(item), path + ' requires exact id@major.minor.patch references.');
    assert(new Set(value).size === value.length, path + ' must not contain duplicate references.');
  }
  function cost(value, path) {
    shape(value, COST_FIELDS.concat(['basis', 'note']), path);
    let subtotal = 0;
    for (const field of COST_FIELDS) {
      const amount = value[field];
      assert(amount === null || (typeof amount === 'number' && Number.isFinite(amount) && amount >= 0), path + '.' + field + ' must be a finite nonnegative number or null.');
      if (amount !== null) subtotal += amount;
    }
    assert(Number.isFinite(subtotal), path + ' cost total must remain finite.');
    one(value.basis, ['observed', 'estimated', 'unknown'], path + '.basis');
    string(value.note, path + '.note');
  }
  function total(value) {
    return COST_FIELDS.every(field => value[field] !== null)
      ? COST_FIELDS.reduce((sum, field) => sum + value[field], 0) : null;
  }
  function validate(spec) {
    shape(spec, ['task', 'meaning', 'real_use', 'baseline', 'assisted', 'comparison', 'evidence_refs', 'carry_forward_refs', 'carry_forward_description', 'human_disposition'], 'trial');
    string(spec.task, 'task');
    assert(text(spec.task), 'task must describe a task.');
    shape(spec.meaning, ['matters', 'reason'], 'meaning');
    one(spec.meaning.matters, ['yes', 'no', 'unknown'], 'meaning.matters');
    string(spec.meaning.reason, 'meaning.reason');
    shape(spec.real_use, ['status', 'description', 'observed_at'], 'real_use');
    one(spec.real_use.status, ['performed', 'not_performed', 'unknown'], 'real_use.status');
    string(spec.real_use.description, 'real_use.description');
    assert(spec.real_use.observed_at === null || timestamp(spec.real_use.observed_at), 'real_use.observed_at must be a valid ISO timestamp or null.');
    assert(spec.real_use.status !== 'performed' || timestamp(spec.real_use.observed_at), 'Performed real use requires an ISO observed_at timestamp.');
    cost(spec.baseline, 'baseline');
    cost(spec.assisted, 'assisted');
    shape(spec.comparison, ['comparable', 'baseline_errors', 'assisted_errors', 'note'], 'comparison');
    one(spec.comparison.comparable, ['yes', 'no', 'unknown'], 'comparison.comparable');
    for (const field of ['baseline_errors', 'assisted_errors']) {
      const count = spec.comparison[field];
      assert(count === null || (Number.isInteger(count) && count >= 0), 'comparison.' + field + ' must be a nonnegative integer or null.');
    }
    string(spec.comparison.note, 'comparison.note');
    refs(spec.evidence_refs, 'evidence_refs');
    refs(spec.carry_forward_refs, 'carry_forward_refs');
    string(spec.carry_forward_description, 'carry_forward_description');
    one(spec.human_disposition, ['keep', 'mutate', 'drop', 'undecided'], 'human_disposition');
    return true;
  }

  function evaluate(spec) {
    validate(spec);
    const baselineTotal = total(spec.baseline), assistedTotal = total(spec.assisted);
    const missing = [];
    if (spec.meaning.matters !== 'yes') missing.push('Record whether this task matters to the person doing it.');
    if (!text(spec.meaning.reason)) missing.push('Explain why the benefit matters.');
    if (spec.real_use.status !== 'performed') missing.push('Perform one real use before judging benefit.');
    if (!text(spec.real_use.description)) missing.push('Describe what happened in the real use.');
    if (!spec.evidence_refs.length) missing.push('Attach at least one exact evidence reference.');
    if (!spec.carry_forward_refs.length) missing.push('Attach at least one exact reference to what carries forward.');
    if (!text(spec.carry_forward_description)) missing.push('Describe how the retained piece makes the next attempt easier.');
    if (spec.comparison.comparable !== 'yes') missing.push('Establish a comparable task and acceptance criteria.');
    if (spec.comparison.baseline_errors === null || spec.comparison.assisted_errors === null) missing.push('Record error counts for both attempts.');
    for (const side of ['baseline', 'assisted']) {
      const absent = COST_FIELDS.filter(field => spec[side][field] === null);
      if (absent.length) missing.push('Measure ' + side + ' minutes for: ' + absent.join(', ') + '. Unknown costs are not zero.');
      if (spec[side].basis !== 'observed') missing.push('Observe the ' + side + ' costs; estimates and unknown bases cannot establish measured savings.');
    }
    const complete = missing.length === 0;
    const reasons = missing.slice();
    let recommendation = 'needs_evidence';
    let nextAction = missing[0] || 'Review this trial and decide whether its benefit matters enough to keep.';
    if (spec.meaning.matters === 'no') {
      recommendation = 'review_drop';
      reasons.push('The recorded judgment says this task does not matter; speed alone does not justify keeping it.');
      nextAction = 'Review whether to drop this approach or choose a task whose benefit matters.';
    } else if (complete) {
      const moreErrors = spec.comparison.assisted_errors > spec.comparison.baseline_errors;
      const noTimeSaving = assistedTotal >= baselineTotal;
      if (moreErrors || noTimeSaving) {
        recommendation = 'review_tradeoff';
        if (moreErrors) reasons.push('The assisted attempt has more recorded errors; a positive time delta does not resolve the quality tradeoff.');
        if (noTimeSaving) reasons.push('The assisted total is at least the baseline total after setup, supervision, cleanup, and maintenance.');
        nextAction = 'Review the time and quality tradeoff; choose whether to mutate, keep, or drop this approach.';
      } else {
        recommendation = 'review_keep';
        reasons.push('Supplied observations show a lower assisted total without more recorded errors, plus a retained piece for reuse.');
      }
    }
    reasons.push('Supplied observations are not independently verified. The caller must resolve exact references, rights, and staleness before relying on this assessment.');
    reasons.push('A time delta and recorded human disposition do not grant admission or execution authority; this assessment remains a candidate proposal.');
    return {
      baseline_total_minutes: baselineTotal,
      assisted_total_minutes: assistedTotal,
      delta_minutes: complete ? baselineTotal - assistedTotal : null,
      evidence_state: complete ? 'observed' : (spec.baseline.basis === 'estimated' || spec.assisted.basis === 'estimated' ? 'estimated' : 'incomplete'),
      recommendation,
      reasons,
      next_action: nextAction,
      state: 'candidate',
      authority: 'propose'
    };
  }
  return Object.freeze({ validate, evaluate });
});
