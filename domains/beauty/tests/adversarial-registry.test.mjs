import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const registry = JSON.parse(await readFile(new URL("../fixtures/adversarial/index.json", import.meta.url), "utf8"));

test("release-killing fixture registry contains eleven distinct attacks", () => {
  assert.equal(registry.fixtures.length, 11);
  assert.equal(new Set(registry.fixtures.map((item) => item.id)).size, 11);
  assert.ok(registry.fixtures.every((item) => item.attack && item.expected));
});
