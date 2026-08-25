import test from "node:test";
import assert from "node:assert/strict";
import { derivePreferenceEvidence, rankRecommendations } from "../src/index.mjs";
import { choice, options } from "../fixtures/taste-fixture.mjs";

test("same inputs produce the same ranked recommendation", () => {
  const evidence = derivePreferenceEvidence({ choice, options });
  const args = {
    actorId: choice.actorId,
    purpose: choice.context.purpose,
    candidates: options.slice(2),
    evidence,
    generatedAt: "2026-08-21T12:05:00.000Z",
  };
  assert.deepEqual(rankRecommendations(args), rankRecommendations(args));
});

test("evidence from another purpose partition is ignored", () => {
  const evidence = derivePreferenceEvidence({ choice, options }).map((item) => ({ ...item, purpose: "campaign_content" }));
  const ranked = rankRecommendations({
    actorId: choice.actorId,
    purpose: choice.context.purpose,
    candidates: options.slice(2),
    evidence,
    generatedAt: "2026-08-21T12:05:00.000Z",
  });
  assert.ok(ranked.every((item) => item.insufficientEvidence));
  assert.ok(ranked.every((item) => item.score === 0));
});
