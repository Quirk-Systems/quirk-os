import test from "node:test";
import assert from "node:assert/strict";
import {
  applyApprovedGraphUpdate,
  decideGraphUpdate,
  derivePreferenceEvidence,
  proposeGraphUpdate,
  rankRecommendations,
  recordOutcome,
} from "../src/index.mjs";
import { choice, graph, options } from "../fixtures/taste-fixture.mjs";

function buildProposal() {
  const evidence = derivePreferenceEvidence({ choice, options });
  const recommendation = rankRecommendations({
    actorId: choice.actorId,
    purpose: choice.context.purpose,
    candidates: options.slice(2),
    evidence,
    generatedAt: "2026-08-21T12:05:00.000Z",
  })[0];
  const outcome = recordOutcome({
    recommendation,
    actorId: choice.actorId,
    purpose: choice.context.purpose,
    optionId: recommendation.optionId,
    kind: "preferred",
    explicit: true,
    testedInRealWorld: true,
    sourceType: "explicit_human_report",
    observedAt: "2026-08-21T14:00:00.000Z",
  });
  return proposeGraphUpdate({ graph, recommendation, outcome, proposedAt: "2026-08-21T14:01:00.000Z" });
}

test("silence cannot become approval", () => {
  const proposal = buildProposal();
  assert.throws(() => decideGraphUpdate({
    proposal,
    actorId: choice.actorId,
    purpose: choice.context.purpose,
    decision: "approve",
    humanConfirmed: false,
    reason: "No response received.",
    decidedAt: "2026-08-21T14:02:00.000Z",
  }), /explicit human confirmation/i);
});

test("rejection cannot mutate the graph", () => {
  const proposal = buildProposal();
  const decision = decideGraphUpdate({
    proposal,
    actorId: choice.actorId,
    purpose: choice.context.purpose,
    decision: "reject",
    humanConfirmed: true,
    reason: "The system misunderstood the result.",
    decidedAt: "2026-08-21T14:02:00.000Z",
  });
  assert.throws(() => applyApprovedGraphUpdate({ graph, proposal, decision, appliedAt: "2026-08-21T14:03:00.000Z" }), /Rejected proposal/i);
});

test("revisions replace candidate deltas rather than silently averaging them", () => {
  const proposal = buildProposal();
  const decision = decideGraphUpdate({
    proposal,
    actorId: choice.actorId,
    purpose: choice.context.purpose,
    decision: "revise",
    humanConfirmed: true,
    reason: "Finish mattered; fragrance did not.",
    corrections: [{ feature: "finish=satin", delta: 0, setStrength: 0.8, evidenceIds: [proposal.outcomeId] }],
    decidedAt: "2026-08-21T14:02:00.000Z",
  });
  const result = applyApprovedGraphUpdate({ graph, proposal, decision, appliedAt: "2026-08-21T14:03:00.000Z" });
  assert.deepEqual(result.graph.edges.map((edge) => edge.feature), ["finish=satin"]);
  assert.equal(result.graph.edges[0].strength, 0.8);
});
