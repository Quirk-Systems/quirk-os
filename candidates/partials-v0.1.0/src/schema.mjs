/** Single schema source. Run npm run schema to update its portable JSON projection. */
const text = {type:'string', minLength:1, pattern:'\\S'};
const strings = {type:'array', items:text, uniqueItems:true};
const count = {type:['integer','null'], minimum:0, maximum:Number.MAX_SAFE_INTEGER};
const digest = {type:'string', pattern:'^sha256:[a-f0-9]{64}$'};
const choice = (...values) => ({enum:values});
const object = properties => ({type:'object', additionalProperties:false, required:Object.keys(properties), properties});
export const recordSchema = {
  $schema:'https://json-schema.org/draft/2020-12/schema',
  $id:'urn:quirk:partials:v1alpha1',
  title:'Quirk partial information record — candidate, inspect only',
  ...object({
    schema_version:{const:'quirk.partials/v1alpha1'}, id:text,
    revision:{type:'integer', minimum:0, maximum:Number.MAX_SAFE_INTEGER},
    supersedes_digest:{anyOf:[digest,{type:'null'}]}, status:{const:'candidate'},
    subject:object({system:text,id:text,version:text,digest}),
    scope:object({id:text,description:text}),
    provenance:object({kind:choice('source_projection','synthetic','human_report'),source_refs:{...strings,minItems:1},captured_at:{type:'string',format:'date-time'}}),
    knowledge:object({status:choice('unknown','partial','complete'),known_items:{type:'array',items:object({id:text,label:text}),uniqueItems:true},lower_bound:count,upper_bound:count,exact:count,completeness_basis:choice('unconfirmed','source_declared','human_confirmed')}),
    evidence:object({status:choice('unknown','partial','supported','contradicted'),satisfied:strings,missing:strings,conflicts:strings,limitations:strings}),
    work:object({status:choice('unknown','not_started','partial','completed','failed'),completed_units:strings,remaining_units:strings,failed_units:strings}),
    availability:object({status:choice('unknown','partial','available','unavailable'),present:strings,missing:strings,unverified:strings}),
    authority:object({maximum_right:{const:'propose'},effect_execution_allowed:{const:false},calendar_write_allowed:{const:false},canon_promotion_allowed:{const:false},graph_application_allowed:{const:false},training_allowed:{const:false},human_review_required:{const:true},upstream_hold_refs:strings})
  })
};

export const reviewRequestSchema = {
  $schema:recordSchema.$schema,$id:'urn:quirk:partials-review-request:v1alpha1',
  ...object({
    schema_version:{const:'quirk.partials-review-request/v1alpha1'},
    captured_at:{type:'string',format:'date-time'},
    max_age_seconds:{type:'integer',minimum:0,maximum:604800},
    entries:{type:'array',minItems:1,maxItems:32,items:object({
      source_ref:text,record:{},max_count:count,
      expectation:{anyOf:[{type:'null'},object({subject:recordSchema.properties.subject,source_ref:text,observed_at:{type:'string',format:'date-time'}})]}
    })}
  })
};
export const reviewResultSchema = {
  $schema:recordSchema.$schema,$id:'urn:quirk:partials-review-result:v1alpha1',
  ...object({
    schema_version:{const:'quirk.partials-review-result/v1alpha1'},status:{const:'candidate'},
    captured_at:{type:'string',format:'date-time'},request_digest:digest,
    rows:{type:'array',minItems:1,maxItems:32,items:object({index:{type:'integer',minimum:0},source_ref:text,input_digest:digest,disposition:choice('matched','quarantined','duplicate'),reason:choice('expectation_matched','invalid_record','expectation_missing','subject_mismatch','stale_capture','future_capture','identity_conflict','exact_replay'),duplicate_of:{type:['integer','null'],minimum:0}})},
    records:{type:'array',items:object({index:{type:'integer',minimum:0},record:{$ref:recordSchema.$id},max_count:count})},
    counts:object({inputs:{type:'integer',minimum:1},matched:{type:'integer',minimum:0},quarantined:{type:'integer',minimum:0},duplicates:{type:'integer',minimum:0}}),
    authority:recordSchema.properties.authority,
    receipt:object({capability_ref:{const:'capability.partials-source-review/v0.1.0'},transform_version:{const:'0.1.0'},output_digest:digest,observed_human_benefit:{type:'null'},human_review_minutes:{type:'null'},compute_cost:{type:'null'},limitations:strings})
  })
};
