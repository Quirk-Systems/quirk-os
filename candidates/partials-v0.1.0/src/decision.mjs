import {contractCheck,digestJSON} from './core.mjs';
import {compareReviewRequests} from './changes.mjs';
import {assertDecisionContext,buildUnsignedDecision as captureDecision} from './decision-model.mjs';
import {contextSchema,decisionSchema} from './decision-schema.mjs';
const checkContext=contractCheck(contextSchema),checkDecision=contractCheck(decisionSchema);
export {assertDecisionContext} from './decision-model.mjs';

/** Produce a presentation context from retained requests, never precomputed claims. */
export function buildDecisionContext(before,after) {
  const comparison=compareReviewRequests(before,after);
  const context={schema_version:'quirk.partials-decision-context/v1alpha1',comparison_digest:digestJSON(comparison),before_request_digest:comparison.before_request_digest,after_request_digest:comparison.after_request_digest,after_captured_at:comparison.after_captured_at,
    authority:comparison.authority,options:comparison.rows.filter(row=>row.proposed_repair!==null).map(({source_ref,change,before_count,after_count,changed_fields,claims_requiring_revalidation,removed_holds,added_holds,proposed_repair})=>({source_ref,change,before_count,after_count,changed_fields,claims_requiring_revalidation,removed_holds,added_holds,proposed_repair}))};
  context.context_digest=digestJSON(context);
  checkContext(context);assertDecisionContext(context);return context;
}
export function buildUnsignedDecision(context,answer) {
  checkContext(context);
  const {context_digest,...body}=context;
  if(context_digest!==digestJSON(body))throw new Error('Decision context digest mismatch');
  const decision=captureDecision(context,answer);checkDecision(decision);return decision;
}
/** Reproduction binds data to requests. It does not authenticate the claimed human origin. */
export function verifyUnsignedDecision(before,after,decision) {
  checkDecision(decision);
  const context=buildDecisionContext(before,after);
  const answer=Object.fromEntries(['source_ref','response','rationale','next_move','finish_condition','captured_at'].map(key=>[key,decision[key]]));
  const expected=buildUnsignedDecision(context,answer);
  if(digestJSON(expected)!==digestJSON(decision))throw new Error('Unsigned decision does not reproduce from retained requests and answer');
  return decision;
}
