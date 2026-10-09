import {DECISION_ACTIONS,DECISION_CHANGED_FIELDS,DECISION_LIMITS} from './decision-model.mjs';
const object=properties=>({type:'object',additionalProperties:false,required:Object.keys(properties),properties});
const text={type:'string',minLength:1,maxLength:DECISION_LIMITS.text,pattern:'\\S'};
const strings={type:'array',maxItems:DECISION_LIMITS.items,uniqueItems:true,items:text};
const digest={type:'string',pattern:'^sha256:[a-f0-9]{64}$'};
const dateTime={type:'string',format:'date-time',maxLength:64};
const nullableText={anyOf:[text,{type:'null'}]};
const authority=object({maximum_right:{const:'propose'},effect_execution_allowed:{const:false},calendar_write_allowed:{const:false},canon_promotion_allowed:{const:false},graph_application_allowed:{const:false},training_allowed:{const:false},human_review_required:{const:true},upstream_hold_refs:strings});
const proposal=object({status:{const:'candidate'},action:{enum:DECISION_ACTIONS},target_ref:text,evidence_refs:{...strings,minItems:1,items:digest},acceptance_criteria:{...strings,minItems:1,maxItems:DECISION_LIMITS.criteria},maximum_right:{const:'propose'},effect_execution_allowed:{const:false},human_review_required:{const:true}});
const contextShape=object({
  schema_version:{const:'quirk.partials-decision-context/v1alpha1'},context_digest:digest,comparison_digest:digest,before_request_digest:digest,after_request_digest:digest,after_captured_at:dateTime,authority,
  options:{type:'array',maxItems:DECISION_LIMITS.options,items:object({source_ref:text,change:{enum:['unchanged','added','removed','replaced','changed']},before_count:nullableText,after_count:nullableText,changed_fields:{...strings,items:{enum:DECISION_CHANGED_FIELDS}},claims_requiring_revalidation:strings,removed_holds:strings,added_holds:strings,proposed_repair:proposal})}
});
export const contextSchema={$schema:'https://json-schema.org/draft/2020-12/schema',$id:'urn:quirk:partials-decision-context:v1alpha1',...contextShape};
export const decisionSchema={
  $schema:contextSchema.$schema,$id:'urn:quirk:partials-unsigned-decision:v1alpha1',
  ...object({schema_version:{const:'quirk.partials-unsigned-decision/v1alpha1'},status:{const:'candidate'},context_digest:digest,comparison_digest:digest,before_request_digest:digest,after_request_digest:digest,context:contextShape,source_ref:text,proposed_repair:proposal,response:{enum:['selected','revised','deferred']},rationale:{...text,maxLength:DECISION_LIMITS.rationale},next_move:nullableText,finish_condition:nullableText,captured_at:dateTime,signature:{type:'null'},human_origin:{const:'claim_only'},executed:{const:false},observed_benefit:{type:'null'},authority}),
  allOf:[{if:{properties:{response:{const:'deferred'}}},then:{properties:{next_move:{type:'null'},finish_condition:{type:'null'}}},else:{properties:{next_move:text,finish_condition:text}}}]
};
