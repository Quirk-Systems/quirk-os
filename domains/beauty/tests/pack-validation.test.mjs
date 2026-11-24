import test from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

test("pack validation accepts the current fail-closed Worker contract", () => {
  const result = spawnSync(process.execPath, [fileURLToPath(new URL("../scripts/validate-pack.mjs", import.meta.url))], { encoding: "utf8" });
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /PACK VALID/);
});
