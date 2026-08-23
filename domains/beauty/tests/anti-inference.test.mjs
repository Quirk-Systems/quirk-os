import test from "node:test";
import assert from "node:assert/strict";
import { recordOutcome } from "../src/index.mjs";

const recommendation = {
  id: "recommendation:test",
  actorId: "human:test",
  purpose: "personal_beauty_recommendation",
  optionId: "option:test",
};

test("a purchase event is not accepted as satisfaction", () => {
  assert.throws(() => recordOutcome({
    recommendation,
    actorId: "human:test",
    purpose: "personal_beauty_recommendation",
    optionId: "option:test",
    kind: "preferred",
    explicit: true,
    testedInRealWorld: true,
    sourceType: "purchase_event",
    observedAt: "2026-08-21T12:00:00.000Z",
  }), /Clicks, purchases, silence, and engagement/i);
});

test("an inferred outcome is denied even when confidence is high", () => {
  assert.throws(() => recordOutcome({
    recommendation,
    actorId: "human:test",
    purpose: "personal_beauty_recommendation",
    optionId: "option:test",
    kind: "preferred",
    explicit: false,
    testedInRealWorld: true,
    sourceType: "explicit_human_report",
    observedAt: "2026-08-21T12:00:00.000Z",
  }), /explicitly reported/i);
});
