import {
  applyApprovedGraphUpdate,
  decideGraphUpdate,
  derivePreferenceEvidence,
  proposeGraphUpdate,
  rankRecommendations,
  recordOutcome,
} from "../src/taste-engine.mjs";

export const actorId = "participant:test-001";
export const purpose = "personal_beauty_recommendation";
export const options = [
  { id: "lip:soft-satin", attributes: { finish: "satin", chroma: "muted", fragrance: "low" } },
  { id: "lip:vivid-matte", attributes: { finish: "matte", chroma: "vivid", fragrance: "high" } },
];
export const choice = {
  id: "choice:test-001",
  actorId,
  context: { id: "context:everyday-lip", purpose },
  presentedOptionIds: options.map((option) => option.id),
  selectedOptionId: options[0].id,
  abstained: false,
  sourceType: "explicit_human_choice",
  capturedAt: "2026-08-22T14:01:00.000Z",
};
export const candidates = [
  { id: "lip:rosewood-satin", attributes: { finish: "satin", chroma: "muted", fragrance: "low" } },
  { id: "lip:scarlet-matte", attributes: { finish: "matte", chroma: "vivid", fragrance: "high" } },
];

export function buildChain({ outcomeKind = "preferred", decisionKind = "approve", corrections = [], receiptWriter } = {}) {
  const evidence = derivePreferenceEvidence({ choice, options });
  const recommendation = rankRecommendations({ actorId, purpose, candidates, evidence, generatedAt: "2026-08-22T14:02:00.000Z" })[0];
  const outcome = recordOutcome({ recommendation, actorId, purpose, optionId: recommendation.optionId, kind: outcomeKind, explicit: true, testedInRealWorld: true, sourceType: "explicit_human_report", note: "Fixture outcome", observedAt: "2026-08-22T15:00:00.000Z" });
  const graph = { actorId, purpose, revision: 4, edges: [{ feature: "finish=satin", strength: 0.2, confidence: 0.7, evidenceIds: ["evidence:prior"], lastUpdatedAt: "2026-08-20T00:00:00.000Z" }] };
  const proposal = proposeGraphUpdate({ graph, recommendation, outcome, proposedAt: "2026-08-22T15:01:00.000Z" });
  const decision = decideGraphUpdate({ proposal, actorId, purpose, decision: decisionKind, humanConfirmed: true, reason: "Fixture decision", corrections, decidedAt: "2026-08-22T15:02:00.000Z" });
  const applied = decisionKind === "reject" ? null : applyApprovedGraphUpdate({ graph, proposal, decision, appliedAt: "2026-08-22T15:03:00.000Z", receiptWriter });
  return { evidence, recommendation, outcome, graph, proposal, decision, ...applied };
}
