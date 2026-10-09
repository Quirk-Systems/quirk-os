import {createRecord, assertRecord, assertJSON, digestJSON} from '../src/core.mjs';

export const PREFERENCE_SOURCE_HEAD = 'f70a713c097436172760d633ccee9bacb071483b';
const SOURCE = `https://github.com/Quirk-Systems/quirk-preference/blob/${PREFERENCE_SOURCE_HEAD}/candidates/image-evidence-intake-v0.1.0/scripts/inspect.mjs`;
const HEX = /^[a-f0-9]{64}$/;
const unique = values => [...new Set(values)];
const fail = message => { throw new TypeError(`Invalid pinned Preference inspection: ${message}`); };
const requireThat = (condition, message) => { if (!condition) fail(message); };
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
function keys(value, required, label) {
  requireThat(object(value) && Object.keys(value).sort().join(',') === [...required].sort().join(','), `${label} fields`);
}
function strings(value, label) {
  requireThat(Array.isArray(value) && value.every(item => typeof item === 'string' && item.trim().length > 0) && new Set(value).size === value.length, label);
}
function inspectReference(result) {
  keys(result, ['index','disposition','source_authenticity','graph_delivery','replay_ledger_integrity','replay_entry','reference'], 'accepted result');
  requireThat(result.source_authenticity === 'UNVERIFIED' && result.graph_delivery === 'NOT_ATTEMPTED' && result.replay_ledger_integrity === 'CALLER_SUPPLIED_UNVERIFIED', 'row evidence boundary');
  keys(result.replay_entry, ['source_site','event_id','payload_digest'], 'replay entry');
  const entry = result.replay_entry;
  requireThat(typeof entry.source_site === 'string' && entry.source_site.length > 0 && HEX.test(entry.event_id) && HEX.test(entry.payload_digest), 'replay identity');
  const ref = result.reference;
  keys(ref, ['api_version','kind','metadata','authority','provenance','spec','evidence','lifecycle'], 'reference');
  requireThat(ref.api_version === 'quirk.dev/v1alpha1' && ref.kind === 'PreferenceReference', 'reference version');
  keys(ref.metadata, ['id','version','status','created_at','updated_at','owner_ref'], 'metadata');
  requireThat(/^preference-reference:sha256:[a-f0-9]{64}$/.test(ref.metadata.id) && ref.metadata.version === '0.1.0' && ref.metadata.status === 'candidate' && ref.metadata.owner_ref === 'repository:Quirk-Systems/quirk-preference', 'candidate metadata');
  keys(ref.authority, ['source_of_truth','current_authority_ref','maximum_runtime_right'], 'authority');
  requireThat(ref.authority.source_of_truth === 'git_candidate_definition' && ref.authority.current_authority_ref === null && ref.authority.maximum_runtime_right === 'none', 'source authority');
  keys(ref.evidence, ['supporting_refs','contradicting_refs','confidence'], 'native evidence');
  requireThat(JSON.stringify(ref.evidence.supporting_refs) === JSON.stringify([entry.payload_digest]) && Array.isArray(ref.evidence.contradicting_refs) && ref.evidence.contradicting_refs.length === 0 && ref.evidence.confidence === null, 'native evidence limits');
  keys(ref.lifecycle, ['supersedes','superseded_by','valid_from','valid_until'], 'native lifecycle');
  requireThat(Array.isArray(ref.lifecycle.supersedes) && ref.lifecycle.supersedes.length === 0 && ref.lifecycle.superseded_by === null && ref.lifecycle.valid_from === null && ref.lifecycle.valid_until === null, 'native lifecycle limits');
  const spec = ref.spec;
  keys(spec, ['source_site','source_event_id','payload_sha256','identity','human_origin','criterion','context','presentation','assets','choice','rationale','proposed_relation','inferred_feature_preferences','lineage_status','unresolved_parent_ids','applied','model_training_allowed','observed_benefit'], 'spec');
  requireThat(spec.source_site === entry.source_site && spec.source_event_id === entry.event_id && spec.payload_sha256 === entry.payload_digest, 'record identity');
  keys(spec.identity, ['site_scoped_id','cross_system_principal_mapping','source_authentication'], 'identity');
  requireThat(typeof spec.identity.site_scoped_id === 'string' && spec.identity.site_scoped_id.length > 0 && spec.identity.cross_system_principal_mapping === null && spec.identity.source_authentication === 'UNVERIFIED_UNSIGNED_EXPORT' && spec.human_origin === 'CLAIM_ONLY', 'unsigned identity boundary');
  requireThat(spec.applied === false && spec.model_training_allowed === false && spec.observed_benefit === null && Array.isArray(spec.inferred_feature_preferences) && spec.inferred_feature_preferences.length === 0, 'application, training, inference, and benefit boundary');
  requireThat(['A','B','both','neither','skip'].includes(spec.choice) && typeof spec.rationale === 'string' && spec.rationale.trim().length > 0 && typeof spec.criterion === 'string' && spec.criterion.trim().length > 0 && typeof spec.context === 'string' && spec.context.trim().length > 0, 'comparison fields');
  keys(spec.proposed_relation, ['relation','from','to','context','criterion','autoApply'], 'relation proposal');
  requireThat(spec.proposed_relation.autoApply === false, 'relation is proposal only');
  requireThat(Array.isArray(spec.assets) && spec.assets.length === 2 && spec.assets.every(asset => object(asset) && HEX.test(asset.id) && HEX.test(asset.sha256) && (asset.parentId === null || HEX.test(asset.parentId))), 'asset metadata');
  const ids = new Set(spec.assets.map(asset => asset.id));
  requireThat(ids.size === 2, 'distinct assets');
  keys(ref.provenance, ['source_refs','parent_object_refs','transformation_refs','run_refs'], 'native provenance');
  requireThat(Array.isArray(ref.provenance.source_refs) && ref.provenance.source_refs.length === 1 && digestJSON(ref.provenance.source_refs[0]) === digestJSON(entry) && JSON.stringify(ref.provenance.parent_object_refs) === JSON.stringify(spec.assets.map(asset => asset.id)) && JSON.stringify(ref.provenance.transformation_refs) === JSON.stringify(['image-evidence-intake.v0.1.0']) && Array.isArray(ref.provenance.run_refs) && ref.provenance.run_refs.length === 0, 'native provenance limits');
  strings(spec.unresolved_parent_ids, 'unresolved lineage');
  const unresolved = unique(spec.assets.filter(asset => asset.parentId !== null && !ids.has(asset.parentId)).map(asset => asset.parentId)).sort();
  requireThat(JSON.stringify([...spec.unresolved_parent_ids].sort()) === JSON.stringify(unresolved) && spec.lineage_status === (unresolved.length ? 'PARTIAL' : 'INCLUDED_REFERENCES_CONSISTENT'), 'lineage claim');
  const presentation = spec.presentation;
  requireThat(object(presentation) && object(presentation.A) && object(presentation.B) && ids.has(presentation.A.assetId) && ids.has(presentation.B.assetId) && presentation.A.assetId !== presentation.B.assetId, 'presentation options');
  const winner = spec.choice === 'A' ? presentation.A : spec.choice === 'B' ? presentation.B : null;
  const loser = spec.choice === 'A' ? presentation.B : spec.choice === 'B' ? presentation.A : null;
  requireThat(spec.proposed_relation.relation === (winner ? 'PREFERRED_OVER' : null) && spec.proposed_relation.from === (winner?.assetId ?? null) && spec.proposed_relation.to === (loser?.assetId ?? null) && spec.proposed_relation.context === spec.context && spec.proposed_relation.criterion === spec.criterion, 'choice meaning');
  return ref;
}

/** Project one pinned CLI inspection document. This does not authenticate it or import image bytes. */
export function fromPreferenceInspection(inspection, options = {}) {
  assertJSON(inspection);
  assertJSON(options);
  const {capturedAt, sourceRefs = []} = options;
  keys(inspection, ['schema_version','status','graph_delivery','source_authenticity','replay_scope','complete_export_verified','page','has_more_events','uninspected_sections','counts','results'], 'inspection');
  requireThat(inspection.schema_version === 'quirk.image-intake-inspection.v0.1' && inspection.status === 'candidate_inspection', 'inspection version');
  requireThat(inspection.graph_delivery === 'NOT_ATTEMPTED' && inspection.source_authenticity === 'UNVERIFIED' && inspection.replay_scope === 'THIS_DOCUMENT_ONLY' && inspection.complete_export_verified === false, 'document evidence boundary');
  requireThat((inspection.page === null && inspection.has_more_events === null) || (Number.isSafeInteger(inspection.page) && inspection.page >= 0 && typeof inspection.has_more_events === 'boolean'), 'pagination fields');
  strings(inspection.uninspected_sections, 'uninspected sections');
  requireThat(inspection.uninspected_sections.every(section => ['image_assets','image_pairs','image_observations','image_jobs','generation'].includes(section)), 'unsupported uninspected section');
  keys(inspection.counts, ['new_candidates','exact_replays','rejected'], 'counts');
  requireThat(Object.values(inspection.counts).every(n => Number.isSafeInteger(n) && n >= 0), 'nonnegative counts');
  requireThat(Array.isArray(inspection.results) && inspection.results.length <= 100, 'bounded results');
  strings(sourceRefs, 'sourceRefs');
  requireThat(typeof capturedAt === 'string' && Number.isFinite(Date.parse(capturedAt)) && new Date(capturedAt).toISOString() === capturedAt, 'capturedAt must be an explicit UTC timestamp');
  const observed = {new_candidates:0, exact_replays:0, rejected:0};
  const references = new Map(), identities = new Map(), completed = [], failed = [], unresolved = [], assets = [];
  for (const [index, result] of inspection.results.entries()) {
    requireThat(object(result) && result.index === index, 'row index');
    if (result.disposition === 'REJECTED') {
      keys(result, ['index','disposition','error'], 'rejected result');
      keys(result.error, ['code','message'], 'rejection');
      requireThat(typeof result.error.code === 'string' && result.error.code.length > 0 && typeof result.error.message === 'string' && result.error.message.length > 0, 'rejection detail');
      observed.rejected++;
      failed.push(`row:${index}:${result.error.code}`);
      continue;
    }
    requireThat(['NEW_CANDIDATE','EXACT_REPLAY'].includes(result.disposition), 'row disposition');
    const ref = inspectReference(result), entry = result.replay_entry;
    const identity = JSON.stringify([entry.source_site, entry.event_id]);
    const prior = identities.get(identity);
    if (result.disposition === 'EXACT_REPLAY') {
      requireThat(prior && prior.payload_digest === entry.payload_digest && prior.reference_digest === digestJSON(ref), 'replay must match an earlier row in this document');
      observed.exact_replays++;
    } else {
      requireThat(!prior && !references.has(ref.metadata.id), 'new event must not duplicate document identity');
      identities.set(identity, {payload_digest:entry.payload_digest, reference_digest:digestJSON(ref)});
      references.set(ref.metadata.id, ref);
      observed.new_candidates++;
    }
    completed.push(`row:${index}:${result.disposition}`);
    unresolved.push(...ref.spec.unresolved_parent_ids);
    assets.push(...ref.spec.assets.map(asset => asset.id));
  }
  requireThat(Object.keys(observed).every(key => observed[key] === inspection.counts[key]), 'counts contradict rows');
  const known = [...references.values()].map((ref, index) => ({id:ref.metadata.id, label:`Candidate comparison ${index + 1}`}));
  const record = createRecord({
    id:`preference-inspection:${digestJSON(inspection).slice(7)}`,
    subject:{system:'Quirk-Systems/quirk-preference', id:'image-intake-inspection', version:PREFERENCE_SOURCE_HEAD, digest:digestJSON(inspection)},
    scope:{id:'preference:document-inspection', description:'Distinct candidate events observed in this one inspection document; full export size, image bytes, identity, and benefit remain unverified.'},
    provenance:{kind:'source_projection',source_refs:unique([SOURCE,...sourceRefs]),captured_at:capturedAt},
    knowledge:{status:known.length ? 'partial' : 'unknown',known_items:known,lower_bound:known.length || null,upper_bound:null,exact:null,completeness_basis:'unconfirmed'},
    evidence:{status:'partial',satisfied:['inspection_shape_and_counts_consistent'],missing:['source_authentication','verified_human_origin','independent_evaluation','observed_human_benefit',...failed.map(unit => `usable_evidence:${unit}`)],conflicts:[],limitations:['Structural projection does not authenticate the inspection or rerun original payload validation.','Unsigned export; human origin is a claim.','Replay checking covers this document only.','A last-page flag does not establish a complete export.','Included lineage metadata does not establish image byte availability or globally complete lineage.']},
    work:{status:failed.length && completed.length === 0 ? 'failed' : 'partial',completed_units:['inspection_document_projected',...completed],remaining_units:['verify_complete_export',...(inspection.has_more_events === true ? ['inspect_remaining_event_pages'] : []),...inspection.uninspected_sections.map(section => `inspect_section:${section}`)],failed_units:failed},
    availability:{status:'partial',present:['inspection_envelope',...unique(assets).map(id => `asset_metadata:${id}`)],missing:unique(unresolved).map(id => `lineage_parent:${id}`),unverified:['complete_export',...unique(assets).map(id => `image_bytes:${id}`),...inspection.uninspected_sections.map(section => `section:${section}`)]},
    authority:{maximum_right:'propose',effect_execution_allowed:false,calendar_write_allowed:false,canon_promotion_allowed:false,graph_application_allowed:false,training_allowed:false,human_review_required:true,upstream_hold_refs:['preference:no_graph_application','preference:no_model_training','preference:unsigned_source','preference:human_review_open']},
  });
  assertRecord(record);
  return record;
}
