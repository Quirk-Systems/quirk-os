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

function chain() {
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
  const proposal = proposeGraphUpdate({ graph, recommendation, outcome, proposedAt: "2026-08-21T14:01:00.000Z" });
  const decision = decideGraphUpdate({
    proposal,
    actorId: choice.actorId,
    purpose: choice.context.purpose,
    decision: "approve",
    humanConfirmed: true,
    reason: "Confirmed.",
    decidedAt: "2026-08-21T14:02:00.000Z",
  });
  return { proposal, decision };
}

test("stale graph revision fails closed", () => {
  const { proposal, decision } = chain();
  const changedGraph = { ...graph, revision: 1 };
  assert.throws(() => applyApprovedGraphUpdate({ graph: changedGraph, proposal, decision, appliedAt: "2026-08-21T14:03:00.000Z" }), /revision changed/i);
});

test("expired decision fails closed", () => {
  const { proposal, decision } = chain();
  assert.throws(() => applyApprovedGraphUpdate({ graph, proposal, decision, appliedAt: "2026-08-21T17:00:00.000Z" }), /expired/i);
});

test("cross-purpose decision is denied", () => {
  const { proposal } = chain();
  assert.throws(() => decideGraphUpdate({
    proposal,
    actorId: choice.actorId,
    purpose: "campaign_content",
    decision: "approve",
    humanConfirmed: true,
    reason: "Wrong scope.",
    decidedAt: "2026-08-21T14:02:00.000Z",
  }), /purpose does not match/i);
});
