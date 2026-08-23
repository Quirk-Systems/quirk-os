import { createHash } from "node:crypto";
import { readdir, readFile, writeFile } from "node:fs/promises";
import { relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = fileURLToPath(new URL("../../..", import.meta.url));
const beautyRoot = resolve(repoRoot, "domains/beauty");
const output = resolve(beautyRoot, "MANIFEST.sha256");
const externalControlledPaths = [
  "canon/domains/beauty/domain-boundary.yaml",
  ".github/CODEOWNERS.quirk-beauty-candidate",
  ".github/PULL_REQUEST_TEMPLATE/quirk-beauty-domain-pack.md",
  ".github/workflows/quirk-beauty-domain-pack.yml",
];

async function walk(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    if ([".git", "node_modules"].includes(entry.name)) continue;
    const path = resolve(directory, entry.name);
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
  .sort((left, right) => left.relative.localeCompare(right.relative));

const lines = [];
for (const entry of controlledFiles) {
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
