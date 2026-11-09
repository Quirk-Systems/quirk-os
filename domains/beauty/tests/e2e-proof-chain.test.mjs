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

test("executes the complete proof chain with a human-confirmed graph update", () => {
  const evidence = derivePreferenceEvidence({ choice, options });
  assert.ok(evidence.length >= 1);
  assert.ok(evidence.every((item) => item.sourceChoiceId === choice.id));

  const recommendations = rankRecommendations({
    actorId: choice.actorId,
    purpose: choice.context.purpose,
    candidates: options.slice(2),
    evidence,
    generatedAt: "2026-08-21T12:05:00.000Z",
  });
  assert.equal(recommendations[0].optionId, "option:satin-mauve");
  assert.deepEqual(recommendations[0].evidenceIds, [...recommendations[0].evidenceIds].sort());

  const outcome = recordOutcome({
    recommendation: recommendations[0],
    actorId: choice.actorId,
    purpose: choice.context.purpose,
    optionId: recommendations[0].optionId,
    kind: "preferred",
    explicit: true,
    testedInRealWorld: true,
    sourceType: "explicit_human_report",
    note: "Comfortable after a full wear test.",
    observedAt: "2026-08-22T18:00:00.000Z",
  });

  const proposal = proposeGraphUpdate({
    graph,
    recommendation: recommendations[0],
    outcome,
    proposedAt: "2026-08-22T18:01:00.000Z",
  });
  assert.equal(proposal.autoApply, false);
  assert.equal(graph.revision, 0, "proposal creation must not mutate the graph");

  const decision = decideGraphUpdate({
    proposal,
    actorId: choice.actorId,
    purpose: choice.context.purpose,
    decision: "approve",
    humanConfirmed: true,
    reason: "The recorded outcome matches my judgment.",
    decidedAt: "2026-08-22T18:02:00.000Z",
  });

  const result = applyApprovedGraphUpdate({
    graph,
    proposal,
    decision,
    appliedAt: "2026-08-22T18:03:00.000Z",
  });
  assert.equal(result.graph.revision, 1);
  assert.ok(result.graph.edges.length >= 1);
  assert.equal(result.receipt.beforeRevision, 0);
  assert.equal(result.receipt.afterRevision, 1);
  assert.match(result.receipt.actionDigest, /^sha256:[a-f0-9]{64}$/);
});
