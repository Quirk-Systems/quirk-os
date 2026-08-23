import test from "node:test";
import assert from "node:assert/strict";
import {
  applyApprovedGraphUpdate,
  decideGraphUpdate,
  derivePreferenceEvidence,
  proposeGraphUpdate,
  rankRecommendations,
  recordOutcome,
} from "../src/taste-engine.mjs";
import { actorId, purpose, options, choice, candidates, buildChain } from "./fixtures.mjs";

function code(expected) {
  return (error) => error?.code === expected;
}

test("explicit choice produces contrast-bound candidate evidence", () => {
  const evidence = derivePreferenceEvidence({ choice, options });
  assert.equal(evidence.length, 3);
  assert.ok(evidence.every((item) => item.sourceChoiceId === choice.id && item.truthStatus === "candidate"));
});

test("abstention produces no preference evidence", () => {
  const evidence = derivePreferenceEvidence({ choice: { ...choice, abstained: true, selectedOptionId: null }, options });
  assert.deepEqual(evidence, []);
});

test("implicit choice source is rejected", () => {
  assert.throws(() => derivePreferenceEvidence({ choice: { ...choice, sourceType: "clickstream" }, options }), code("choice.implicit_source"));
});

test("unknown selected option is rejected", () => {
  assert.throws(() => derivePreferenceEvidence({ choice: { ...choice, selectedOptionId: "lip:missing" }, options }), code("choice.selection_incoherent"));
});

test("options without an explicit contrast are rejected", () => {
  const same = [
    { id: "a", attributes: { finish: "satin" } },
    { id: "b", attributes: { finish: "satin" } },
  ];
  assert.throws(() => derivePreferenceEvidence({ choice: { ...choice, presentedOptionIds: ["a", "b"], selectedOptionId: "a" }, options: same }), code("evidence.no_contrast"));
});

test("recommendation ranking is deterministic", () => {
  const evidence = derivePreferenceEvidence({ choice, options });
  const input = { actorId, purpose, candidates, evidence, generatedAt: "2026-08-22T14:02:00.000Z" };
  assert.deepEqual(rankRecommendations(input), rankRecommendations(input));
  assert.equal(rankRecommendations(input)[0].optionId, "lip:rosewood-satin");
});

test("evidence cannot leak across purpose partitions", () => {
  const evidence = derivePreferenceEvidence({ choice, options });
  const ranked = rankRecommendations({ actorId, purpose: "campaign_targeting", candidates, evidence, generatedAt: "2026-08-22T14:02:00.000Z" });
  assert.ok(ranked.every((item) => item.insufficientEvidence && item.score === 0));
});

test("inferred outcome is rejected", () => {
  const { recommendation } = buildChain();
  assert.throws(() => recordOutcome({ recommendation, actorId, purpose, optionId: recommendation.optionId, kind: "preferred", explicit: false, testedInRealWorld: true, sourceType: "engagement_signal", observedAt: "2026-08-22T15:00:00.000Z" }), code("outcome.inferred"));
});

test("purchase is not an accepted outcome source", () => {
  const { recommendation } = buildChain();
  assert.throws(() => recordOutcome({ recommendation, actorId, purpose, optionId: recommendation.optionId, kind: "preferred", explicit: true, testedInRealWorld: true, sourceType: "purchase", observedAt: "2026-08-22T15:00:00.000Z" }), code("outcome.invalid_source"));
});

test("not-tested outcome cannot propose a graph update", () => {
  const evidence = derivePreferenceEvidence({ choice, options });
  const recommendation = rankRecommendations({ actorId, purpose, candidates, evidence, generatedAt: "2026-08-22T14:02:00.000Z" })[0];
  const outcome = recordOutcome({ recommendation, actorId, purpose, optionId: recommendation.optionId, kind: "not_tested", explicit: true, testedInRealWorld: false, sourceType: "explicit_human_report", observedAt: "2026-08-22T15:00:00.000Z" });
  assert.throws(() => proposeGraphUpdate({ graph: { actorId, purpose, revision: 0, edges: [] }, recommendation, outcome, proposedAt: "2026-08-22T15:01:00.000Z" }), code("proposal.no_real_world_test"));
});

test("mixed outcome cannot be approved without explicit revision", () => {
  const evidence = derivePreferenceEvidence({ choice, options });
  const recommendation = rankRecommendations({ actorId, purpose, candidates, evidence, generatedAt: "2026-08-22T14:02:00.000Z" })[0];
  const outcome = recordOutcome({ recommendation, actorId, purpose, optionId: recommendation.optionId, kind: "mixed", explicit: true, testedInRealWorld: true, sourceType: "explicit_human_report", observedAt: "2026-08-22T15:00:00.000Z" });
  const proposal = proposeGraphUpdate({ graph: { actorId, purpose, revision: 0, edges: [] }, recommendation, outcome, proposedAt: "2026-08-22T15:01:00.000Z" });
  assert.equal(proposal.requiresRevision, true);
  assert.throws(() => decideGraphUpdate({ proposal, actorId, purpose, decision: "approve", humanConfirmed: true, reason: "No", decidedAt: "2026-08-22T15:02:00.000Z" }), code("gate.mixed_requires_revision"));
});

test("silence cannot become a Human Gate decision", () => {
  const { proposal } = buildChain();
  assert.throws(() => decideGraphUpdate({ proposal, actorId, purpose, decision: "approve", humanConfirmed: false, reason: "Timed out", decidedAt: "2026-08-22T15:02:00.000Z" }), code("gate.not_human_confirmed"));
});

test("decision cannot cross purpose partition", () => {
  const { proposal } = buildChain();
  assert.throws(() => decideGraphUpdate({ proposal, actorId, purpose: "campaign_targeting", decision: "approve", humanConfirmed: true, reason: "Wrong scope", decidedAt: "2026-08-22T15:02:00.000Z" }), code("gate.purpose_mismatch"));
});

test("expired proposal fails closed", () => {
  const { proposal } = buildChain();
  assert.throws(() => decideGraphUpdate({ proposal: { ...proposal, expiresAt: "2026-08-22T15:01:30.000Z" }, actorId, purpose, decision: "approve", humanConfirmed: true, reason: "Late", decidedAt: "2026-08-22T15:02:00.000Z" }), code("time.expired"));
});

test("stale graph revision fails closed", () => {
  const { graph, proposal, decision } = buildChain();
  assert.throws(() => applyApprovedGraphUpdate({ graph: { ...graph, revision: graph.revision + 1 }, proposal, decision, appliedAt: "2026-08-22T15:03:00.000Z" }), code("gate.stale_revision"));
});

test("rejected proposal cannot mutate the graph", () => {
  const evidence = derivePreferenceEvidence({ choice, options });
  const recommendation = rankRecommendations({ actorId, purpose, candidates, evidence, generatedAt: "2026-08-22T14:02:00.000Z" })[0];
  const outcome = recordOutcome({ recommendation, actorId, purpose, optionId: recommendation.optionId, kind: "preferred", explicit: true, testedInRealWorld: true, sourceType: "explicit_human_report", observedAt: "2026-08-22T15:00:00.000Z" });
  const graph = { actorId, purpose, revision: 0, edges: [] };
  const proposal = proposeGraphUpdate({ graph, recommendation, outcome, proposedAt: "2026-08-22T15:01:00.000Z" });
  const decision = decideGraphUpdate({ proposal, actorId, purpose, decision: "reject", humanConfirmed: true, reason: "Human rejects update", decidedAt: "2026-08-22T15:02:00.000Z" });
  assert.throws(() => applyApprovedGraphUpdate({ graph, proposal, decision, appliedAt: "2026-08-22T15:03:00.000Z" }), code("gate.rejected"));
});

test("explicit correction replaces strength instead of averaging", () => {
  const corrections = [{ feature: "finish=satin", setStrength: -0.4, evidenceIds: ["evidence:human-correction"] }];
  const { graph } = buildChain({ decisionKind: "revise", corrections });
  assert.equal(graph.edges.find((edge) => edge.feature === "finish=satin").strength, -0.4);
});

test("identical approved inputs produce identical receipt digest", () => {
  const first = buildChain().receipt;
  const second = buildChain().receipt;
  assert.equal(first.actionDigest, second.actionDigest);
});
