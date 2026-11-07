import test from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
test("the repo-native real-proof CLI denies even a syntactically valid proof until core attestation integration", () => {
  const result = spawnSync(process.execPath, ["scripts/verify-real-proof.mjs", "proof/synthetic-example.json"], { encoding: "utf8" });
  assert.equal(result.status, 1);
  assert.match(result.stderr, /core_attestation_not_integrated/);
});
