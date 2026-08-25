import test from "node:test";
import assert from "node:assert/strict";
import { derivePreferenceEvidence } from "../src/index.mjs";
import { choice, options } from "../fixtures/taste-fixture.mjs";

test("abstention is valid evidence of no choice and creates no preference edge", () => {
  const abstention = { ...choice, selectedOptionId: null, abstained: true };
  assert.deepEqual(derivePreferenceEvidence({ choice: abstention, options }), []);
});
