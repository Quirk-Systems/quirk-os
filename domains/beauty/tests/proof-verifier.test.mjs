import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { verifyRealProof } from "../src/index.mjs";

test("synthetic proof is never admissible as the required proof", () => {
  const proof = JSON.parse(readFileSync(new URL("../proof/synthetic-example.json", import.meta.url), "utf8"));
  const verdict = verifyRealProof(proof);
  assert.equal(verdict.passed, false);
  assert.ok(verdict.errors.some((error) => error.code === "proof.synthetic"));
});

test("public real-proof API cannot bypass the CLI attestation hold by relabeling a fixture", () => {
  const proof = JSON.parse(readFileSync(new URL("../proof/synthetic-example.json", import.meta.url), "utf8"));
  proof.synthetic = false;
  proof.participantConsent = true;
  const verdict = verifyRealProof(proof);
  assert.equal(verdict.passed, false);
  assert.ok(verdict.errors.some((error) => error.code === "proof.core_attestation_not_integrated"));
});
