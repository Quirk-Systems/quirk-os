import { createRecord, assertRecord, assertJSON, digestJSON } from '../src/core.mjs';

// Native compatibility: quirk-skills RED-stage candidate-object.json,
// evals/baseline-scenarios.json and evidence/baseline-results.json at
// 8fbe2e9553ff140a783eaf8bbd7d97d64ec6c47c. This is not a submission validator.
const FALSE_FLAGS = ['operative', 'admitted', 'active', 'canonical', 'published', 'deployed'];
const SHA256 = /^[a-f0-9]{64}$/;
const STATES = ['present', 'missing', 'unverified', 'intentionally_absent'];
const text = (value) => typeof value === 'string' && value.trim().length > 0;
const own = (value, key) => Object.prototype.hasOwnProperty.call(value, key);
const requireThat = (condition, message) => { if (!condition) throw new TypeError(`Skills partial: ${message}`); };

function uniqueRows(rows, key, label) {
  requireThat(Array.isArray(rows), `${label} must be an array`);
  const ids = new Set();
  for (const row of rows) {
    requireThat(row && typeof row === 'object' && !Array.isArray(row), `${label} rows must be objects`);
    requireThat(text(row[key]), `${label}.${key} is required`);
    requireThat(!ids.has(row[key]), `duplicate ${label}.${key}: ${row[key]}`);
    ids.add(row[key]);
  }
  return ids;
}

/** Classify native declarations without executing tests or verifying artifact bytes. */
export function inspectSkillsCases(input) {
  assertJSON(input);
  requireThat(input && typeof input === 'object' && !Array.isArray(input), 'input must be an object');
  const scenarios = own(input, 'scenarios') ? input.scenarios : [];
  const results = own(input, 'results') ? input.results : [];
  const ids = uniqueRows(scenarios, 'id', 'scenarios');
  uniqueRows(results, 'scenario_id', 'results');
  const resultMap = new Map(results.map((result) => [result.scenario_id, result]));
  for (const result of results) requireThat(ids.has(result.scenario_id), `result has no scenario: ${result.scenario_id}`);

  return scenarios.map((scenario) => {
    requireThat(['PROPOSED_NOT_EXECUTED', 'EXECUTED_HISTORICAL'].includes(scenario.execution_status), `unsupported execution_status: ${scenario.execution_status}`);
    const result = resultMap.get(scenario.id);
    if (scenario.execution_status === 'PROPOSED_NOT_EXECUTED') {
      requireThat(!result && !scenario.evidence_ref, `unexecuted scenario claims evidence: ${scenario.id}`);
      return { id: scenario.id, execution: 'unexecuted', result: 'none', current_pass: false };
    }
    if (!result) return { id: scenario.id, execution: 'historical_reported', result: 'missing', current_pass: false };
    requireThat(result.verdict === 'RED_CONFIRMED', `unsupported historical verdict: ${result.verdict}`);
    requireThat(text(result.evidence_ref) && SHA256.test(result.sha256), `historical result needs a reference and SHA-256: ${scenario.id}`);
    requireThat(Array.isArray(result.critical_failures) && result.critical_failures.length > 0 && result.critical_failures.every(text), `RED result must preserve critical failures: ${scenario.id}`);
    requireThat(!scenario.evidence_ref || scenario.evidence_ref === result.evidence_ref, `scenario/result reference mismatch: ${scenario.id}`);
    return { id: scenario.id, execution: 'historical_reported', result: 'expected_negative_reported', current_pass: false };
  });
}

/**
 * Project RED-stage readiness into the shared record. Artifact states must come
 * from a separate explicit acquisition inventory; references are not presence.
 * scenarioInventoryComplete refers only to this declared scenario list.
 */
export function adaptSkillsReadiness(input, options = {}) {
  assertJSON(options);
  const cases = inspectSkillsCases(input);
  requireThat(text(options.capturedAt), 'explicit capturedAt is required');
  requireThat(Array.isArray(options.sourceRefs) && options.sourceRefs.length > 0 && options.sourceRefs.every(text), 'explicit nonempty sourceRefs are required');
  requireThat(!options.sourceRefs.some((ref) => ref.startsWith('fixture:')) || options.provenanceKind === 'synthetic', 'fixture sources must have synthetic provenance');
  const candidate = input.candidate;
  requireThat(candidate && typeof candidate === 'object' && !Array.isArray(candidate), 'candidate object is required');
  requireThat(text(candidate.name) && text(candidate.version), 'candidate name and version are required');
  requireThat(candidate.status === 'candidate' && candidate.authority_ceiling === 'propose', 'candidate/propose boundary is required');
  for (const flag of FALSE_FLAGS) requireThat(candidate[flag] === false, `${flag} must remain explicitly false`);
  requireThat(candidate.red_stage?.required_verdict === 'RED_CONFIRMED', 'unsupported candidate stage');
  requireThat(candidate.red_stage?.skill_md_required_absent === true, 'RED-stage required-absence boundary is required');
  requireThat(options.scenarioInventoryComplete === undefined || typeof options.scenarioInventoryComplete === 'boolean', 'scenarioInventoryComplete must be boolean');
  requireThat(!options.scenarioInventoryComplete || own(input, 'scenarios'), 'complete inventory requires supplied scenarios');
  requireThat(options.artifactInventoryComplete === undefined || typeof options.artifactInventoryComplete === 'boolean', 'artifactInventoryComplete must be boolean');
  requireThat(!options.artifactInventoryComplete || own(input, 'artifacts'), 'complete artifact inventory requires supplied artifacts');

  const artifacts = own(input, 'artifacts') ? input.artifacts : [];
  uniqueRows(artifacts, 'id', 'artifacts');
  for (const item of artifacts) requireThat(STATES.includes(item.state), `unsupported artifact state: ${item.state}`);
  const present = artifacts.filter((item) => item.state === 'present').map((item) => item.id);
  const missingArtifacts = artifacts.filter((item) => item.state === 'missing' || item.state === 'intentionally_absent').map((item) => item.state === 'intentionally_absent' ? `${item.id} (intentionally absent)` : item.id);
  const unverified = artifacts.filter((item) => item.state === 'unverified').map((item) => item.id);
  if (options.artifactInventoryComplete !== true) unverified.push('package_artifact_inventory');

  const known = cases.map((item) => ({ id: item.id, label: `${item.id}: ${item.result === 'expected_negative_reported' ? 'historical RED result reported' : item.result === 'missing' ? 'historical result missing' : 'not executed'}` }));
  const historical = cases.filter((item) => item.result === 'expected_negative_reported');
  const missingResults = cases.filter((item) => item.result === 'missing');
  const pending = cases.filter((item) => item.execution === 'unexecuted');
  const complete = options.scenarioInventoryComplete === true;
  const evidenceMissing = [
    'current_version_passing_positive_cases',
    'current_version_passing_negative_or_boundary_cases',
    'independent_qa_verdict',
    'immutable_package_digest',
    ...missingResults.map((item) => `historical_result:${item.id}`),
  ];
  if (!own(input, 'scenarios')) evidenceMissing.push('scenario_inventory');
  if (!own(input, 'results')) evidenceMissing.push('historical_result_inventory');
  const remaining = [
    ...pending.map((item) => `execute_scenario:${item.id}`),
    ...missingResults.map((item) => `recover_historical_result:${item.id}`),
    'current_version_comparative_evaluation',
    'independent_qa',
  ];
  const record = createRecord({
    id: options.id ?? `skills:${candidate.name}:readiness`,
    subject: { system: 'Quirk-Systems/quirk-skills', id: candidate.name, version: candidate.version, digest: digestJSON(input) },
    scope: { id: options.scopeId ?? `${candidate.name}:red-readiness`, description: 'Declared RED-stage evaluation scenarios and package readiness; scenario completeness does not mean skill readiness.' },
    provenance: { kind: options.provenanceKind ?? 'source_projection', source_refs: options.sourceRefs, captured_at: options.capturedAt },
    knowledge: {
      status: complete ? 'complete' : known.length ? 'partial' : 'unknown', known_items: known,
      lower_bound: complete || known.length ? known.length : null,
      upper_bound: complete ? known.length : null, exact: complete ? known.length : null,
      completeness_basis: complete ? 'source_declared' : 'unconfirmed',
    },
    evidence: {
      status: historical.length ? 'partial' : 'unknown',
      satisfied: historical.map((item) => `historical_expected_negative_reported:${item.id}`),
      missing: evidenceMissing, conflicts: [],
      limitations: [
        'RED_CONFIRMED is an expected historical failure, never current-version passing evidence.',
        'PROPOSED_NOT_EXECUTED scenarios are not executed negative review cases.',
        'References and recorded SHA-256 values are source declarations; artifact bytes are not verified by this adapter.',
        'The native RED validator is not executed by this projection; internal consistency cannot establish admission or submission readiness.',
      ],
    },
    work: { status: historical.length ? 'partial' : 'not_started', completed_units: historical.map((item) => `historical_result_report:${item.id}`), remaining_units: remaining, failed_units: [] },
    availability: { status: present.length ? missingArtifacts.length || unverified.length ? 'partial' : 'available' : missingArtifacts.length ? 'unavailable' : 'unknown', present, missing: missingArtifacts, unverified },
    authority: {
      maximum_right: 'propose', effect_execution_allowed: false, calendar_write_allowed: false,
      canon_promotion_allowed: false, graph_application_allowed: false, training_allowed: false,
      human_review_required: true,
      upstream_hold_refs: ['skills:candidate-only', 'skills:current-version-evaluation-required', 'skills:independent-qa-required', 'skills:no-admission-or-submission-grant'],
    },
  });
  assertRecord(record);
  return record;
}
