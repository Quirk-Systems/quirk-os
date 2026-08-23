import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { validateSchema } from "../src/schema-validator.mjs";

const schema = JSON.parse(await readFile(new URL("../schemas/choice.schema.json", import.meta.url), "utf8"));
const valid = {
  id: "choice:test",
  actorId: "actor:test",
  context: { id: "context:test", purpose: "personal_beauty_recommendation" },
  presentedOptionIds: ["a", "b"],
  selectedOptionId: "a",
  abstained: false,
  sourceType: "explicit_human_choice",
  capturedAt: "2026-08-22T00:00:00.000Z",
};

test("strict schema accepts a valid explicit choice", () => {
  assert.deepEqual(validateSchema(schema, valid), []);
});

test("strict schema rejects additional properties", () => {
  const errors = validateSchema(schema, { ...valid, inferredSatisfaction: true });
  assert.ok(errors.some((item) => item.keyword === "additionalProperties"));
});

test("strict schema rejects duplicate presented options", () => {
  const errors = validateSchema(schema, { ...valid, presentedOptionIds: ["a", "a"] });
  assert.ok(errors.some((item) => item.keyword === "uniqueItems"));
});
