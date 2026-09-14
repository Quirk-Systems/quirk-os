export type Primitive = string | number | boolean;
export type TruthStatus = "candidate" | "canonical";
export type OutcomeKind = "preferred" | "rejected" | "mixed" | "not_tested";
export type GraphDecisionKind = "approve" | "revise" | "reject";
export interface TasteContext { id:string; realm:"beauty"; purpose:string; attributes:Record<string,Primitive>; }
export interface TasteOption { id:string; label:string; attributes:Record<string,Primitive>; truthStatus:"candidate"; }
export interface TasteChoice { id:string; sessionId:string; actorId:string; context:TasteContext; presentedOptionIds:string[]; selectedOptionId:string|null; abstained:boolean; sourceType:"explicit_human_choice"; capturedAt:string; }
export interface PreferenceEvidence { id:string; actorId:string; purpose:string; contextId:string; preferredFeature:string; contrastedFeature:string; sourceChoiceId:string; sourceType:"explicit_human_choice"; weight:number; confidence:number; truthStatus:"candidate"; recordedAt:string; }
export interface RecommendationFactor { feature:string; contribution:number; evidenceIds:string[]; }
export interface Recommendation { id:string; actorId:string; purpose:string; optionId:string; score:number; confidence:number; evidenceIds:string[]; factors:RecommendationFactor[]; insufficientEvidence:boolean; status:"candidate"; generatedAt:string; expiresAt:string; }
export interface OutcomeObservation { id:string; actorId:string; purpose:string; recommendationId:string; optionId:string; kind:OutcomeKind; explicit:true; testedInRealWorld:boolean; sourceType:"explicit_human_report"; note:string; observedAt:string; }
export interface PreferenceEdge { feature:string; strength:number; confidence:number; evidenceIds:string[]; lastUpdatedAt:string; }
export interface PreferenceGraphSnapshot { actorId:string; purpose:string; revision:number; edges:PreferenceEdge[]; }
export interface GraphDelta { feature:string; delta:number; setStrength?:number; evidenceIds:string[]; }
export interface GraphUpdateProposal { id:string; actorId:string; purpose:string; expectedGraphRevision:number; recommendationId:string; outcomeId:string; deltas:GraphDelta[]; autoApply:false; truthStatus:"candidate"; proposedAt:string; expiresAt:string; }
export interface GraphUpdateDecision { id:string; proposalId:string; actorId:string; purpose:string; decision:GraphDecisionKind; humanConfirmed:boolean; reason:string; corrections:GraphDelta[]; decidedAt:string; expiresAt:string; }
