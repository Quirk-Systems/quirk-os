import { createHash } from "node:crypto";
import { lstat, readdir, readFile, writeFile } from "node:fs/promises";
import { relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = fileURLToPath(new URL("../../..", import.meta.url));
const beautyRoot = resolve(repoRoot, "domains/beauty");
const output = resolve(beautyRoot, "MANIFEST.sha256");
const externalControlledPaths = [
  "docs/canon/QUIRK-BEAUTY-DOMAIN-BOUNDARY.yaml",
  "docs/canon/QUIRK-BEAUTY-DOMAIN-BOUNDARY.payload.json",
  "decisions/ADR-0002-quirk-beauty-domain-boundary.md",
  "supabase/migrations/20260821090000_quirk_beauty_taste_engine_candidate.sql",
  "supabase/tests/quirk_beauty_taste_engine_rls.sql",
  ".github/CODEOWNERS",
  ".github/workflows/quirk-beauty-domain-pack.yml",
];

async function walk(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    if ([".git", "node_modules"].includes(entry.name)) continue;
    const path = resolve(directory, entry.name);
    if (entry.isSymbolicLink()) throw new Error(`Manifest rejects symbolic link: ${path}`);
    if (entry.isDirectory()) files.push(...await walk(path));
    else files.push(path);
  }
  return files;
}

const beautyFiles = (await walk(beautyRoot))
  .filter((path) => path !== output);
const controlledFiles = [
  ...beautyFiles,
  ...externalControlledPaths.map((path) => resolve(repoRoot, path)),
]
  .map((path) => ({ path, relative: relative(repoRoot, path).replaceAll("\\", "/") }))
  .sort((left, right) => left.relative < right.relative ? -1 : left.relative > right.relative ? 1 : 0);

const lines = [];
for (const entry of controlledFiles) {
  if ((await lstat(entry.path)).isSymbolicLink()) throw new Error(`Manifest rejects symbolic link: ${entry.relative}`);
  const hash = createHash("sha256").update(await readFile(entry.path)).digest("hex");
  lines.push(`${hash}  ${entry.relative}`);
}
const content = `${lines.join("\n")}\n`;

if (process.argv.includes("--check")) {
  let current = "";
  try { current = await readFile(output, "utf8"); } catch {}
  if (current !== content) {
    console.error("domains/beauty/MANIFEST.sha256 is stale. Run npm run manifest.");
    process.exit(1);
  }
  console.log(`MANIFEST VALID: ${lines.length} controlled files`);
} else {
  await writeFile(output, content);
  console.log(`MANIFEST WRITTEN: ${lines.length} controlled files`);
}
