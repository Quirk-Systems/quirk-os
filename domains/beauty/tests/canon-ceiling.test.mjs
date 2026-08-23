import test from "node:test";
import assert from "node:assert/strict";
import { readdir, readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { digest, withoutPath } from "../src/canonical-json.mjs";

const repoRoot = fileURLToPath(new URL("../../..", import.meta.url));

test("only the Quirk Beauty boundary occupies the canonical surface", async () => {
  const directory = resolve(repoRoot, "canon/domains/beauty");
  assert.deepEqual(await readdir(directory), ["domain-boundary.yaml"]);
});

test("canonical boundary digest matches exact content", async () => {
  const boundary = JSON.parse(await readFile(resolve(repoRoot, "canon/domains/beauty/domain-boundary.yaml"), "utf8"));
  assert.equal(boundary.metadata.content_hash, digest(withoutPath(boundary, "metadata.content_hash")));
});

test("boundary does not claim Git admission before merge", async () => {
  const boundary = JSON.parse(await readFile(resolve(repoRoot, "canon/domains/beauty/domain-boundary.yaml"), "utf8"));
  assert.equal(boundary.metadata.lifecycle_status, "approved_pending_git_admission");
  assert.equal(boundary.spec.required_proof.synthetic_proof_sufficient, false);
});

test("candidate manifest has zero implicit effect authority", async () => {
  const manifest = JSON.parse(await readFile(resolve(repoRoot, "domains/beauty/manifest.json"), "utf8"));
  assert.equal(manifest.status, "candidate");
  assert.ok(Object.values(manifest.authorityCeiling).every((value) => value === false));
});
