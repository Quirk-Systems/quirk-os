import test from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
test("the repo-native real-proof CLI denies even a syntactically valid proof until core attestation integration", () => {
  const result = spawnSync(process.execPath, [fileURLToPath(new URL("../scripts/verify-real-proof.mjs", import.meta.url)), fileURLToPath(new URL("../proof/synthetic-example.json", import.meta.url))], { encoding: "utf8" });
  assert.equal(result.status, 1);
  assert.match(result.stderr, /core_attestation_not_integrated/);
});
