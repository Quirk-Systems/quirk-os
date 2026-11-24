import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, mkdir, readFile, writeFile, copyFile, symlink, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

async function fixture(t) {
  const root = await mkdtemp(join(tmpdir(), "beauty-manifest-"));
  t.after(() => rm(root, { recursive: true, force: true }));
  const script = join(root, "domains/beauty/scripts/generate-manifest.mjs");
  await mkdir(join(root, "domains/beauty/scripts"), { recursive: true });
  await copyFile(new URL("../scripts/generate-manifest.mjs", import.meta.url), script);
  for (const path of ["docs/canon/QUIRK-BEAUTY-DOMAIN-BOUNDARY.yaml", "docs/canon/QUIRK-BEAUTY-DOMAIN-BOUNDARY.payload.json", "decisions/ADR-0002-quirk-beauty-domain-boundary.md", "supabase/migrations/20260821090000_quirk_beauty_taste_engine_candidate.sql", "supabase/tests/quirk_beauty_taste_engine_rls.sql", ".github/CODEOWNERS", ".github/workflows/quirk-beauty-domain-pack.yml"]) {
    await mkdir(join(root, path, ".."), { recursive: true });
    await writeFile(join(root, path), "fixture\n");
  }
  return { root, run: (...args) => spawnSync(process.execPath, [script, ...args], { encoding: "utf8" }) };
}

test("manifest ignores unrelated repo files and detects controlled input drift", async (t) => {
  const { root, run } = await fixture(t);
  assert.equal(run().status, 0);
  const manifest = await readFile(join(root, "domains/beauty/MANIFEST.sha256"), "utf8");
  await writeFile(join(root, "unrelated.json"), "not even JSON");
  assert.equal(run("--check").status, 0);
  assert.ok(!manifest.includes("unrelated.json"));
  await writeFile(join(root, ".github/CODEOWNERS"), "changed\n");
  assert.equal(run("--check").status, 1);
});

test("manifest rejects symbolic links rather than reading outside controlled paths", async (t) => {
  const { root, run } = await fixture(t);
  await writeFile(join(root, "outside.txt"), "outside controlled scope\n");
  await symlink(join(root, "outside.txt"), join(root, "domains/beauty/escape.txt"));
  const result = run();
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /symbolic link/i);
});
