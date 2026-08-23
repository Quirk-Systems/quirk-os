import { readdir, readFile } from "node:fs/promises";
import { relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { digest, withoutPath } from "../src/canonical-json.mjs";

const repoRoot = fileURLToPath(new URL("../../..", import.meta.url));
const beautyRoot = resolve(repoRoot, "domains/beauty");
const failures = [];
const fail = (code, message) => failures.push({ code, message });

async function exists(path) {
  try { await readFile(path); return true; } catch { return false; }
}
async function walk(directory) {
  const files = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    if (["node_modules", ".git"].includes(entry.name)) continue;
    const path = resolve(directory, entry.name);
    if (entry.isDirectory()) files.push(...await walk(path)); else files.push(path);
  }
  return files;
}

const required = [
  "domains/beauty/PACK.md",
  "domains/beauty/DECISIONS.md",
  "domains/beauty/RELEASE_CRITERIA.md",
  "canon/domains/beauty/domain-boundary.yaml",
  "domains/beauty/manifest.json",
  "domains/beauty/package.json",
  "domains/beauty/src/taste-engine.mjs",
  "domains/beauty/src/proof-verifier.mjs",
  "domains/beauty/tests/taste-engine.test.mjs",
  "domains/beauty/fixtures/proof/synthetic-example.json",
  "domains/beauty/supabase/migrations/0001_quirk_beauty_taste_engine.sql",
  "domains/beauty/airtable/field-authority.json",
  "domains/beauty/cloudflare/wrangler.jsonc",
  "domains/beauty/openai/explanation-output.schema.json",
  ".github/workflows/quirk-beauty-domain-pack.yml",
];
for (const file of required) if (!await exists(resolve(repoRoot, file))) fail("pack.missing_file", file);

const externalControlledPaths = [
  "canon/domains/beauty/domain-boundary.yaml",
  ".github/CODEOWNERS.quirk-beauty-candidate",
  ".github/PULL_REQUEST_TEMPLATE/quirk-beauty-domain-pack.md",
  ".github/workflows/quirk-beauty-domain-pack.yml",
];
const allFiles = [
  ...await walk(beautyRoot),
  ...externalControlledPaths.map((path) => resolve(repoRoot, path)),
];
for (const path of allFiles.filter((path) => path.endsWith(".json"))) {
  try { JSON.parse(await readFile(path, "utf8")); } catch (error) { fail("json.invalid", `${relative(repoRoot, path)}: ${error.message}`); }
}

const canonDirectory = resolve(repoRoot, "canon/domains/beauty");
const canonFiles = await walk(canonDirectory);
if (canonFiles.length !== 1 || relative(repoRoot, canonFiles[0]).replaceAll("\\", "/") !== "canon/domains/beauty/domain-boundary.yaml") {
  fail("canon.ceiling", `Expected exactly one canonical file, found: ${canonFiles.map((path) => relative(repoRoot, path)).join(", ")}`);
}

const boundary = JSON.parse(await readFile(resolve(repoRoot, "canon/domains/beauty/domain-boundary.yaml"), "utf8"));
const boundaryDigest = digest(withoutPath(boundary, "metadata.content_hash"));
if (boundary.metadata.content_hash !== boundaryDigest) fail("canon.hash", `Expected ${boundaryDigest}, found ${boundary.metadata.content_hash}`);
if (boundary.metadata.lifecycle_status !== "approved_pending_git_admission") fail("canon.lifecycle", "Boundary must not claim merge admission before merge.");
if (boundary.spec.required_proof.synthetic_proof_sufficient !== false) fail("canon.synthetic", "Synthetic proof must remain insufficient.");

const manifest = JSON.parse(await readFile(resolve(beautyRoot, "manifest.json"), "utf8"));
if (manifest.status !== "candidate") fail("candidate.status", "Implementation manifest must remain candidate.");
for (const [name, value] of Object.entries(manifest.authorityCeiling)) if (value !== false) fail("candidate.authority", `${name} must be false.`);

function inspectStrictObjects(schema, path = "$") {
  if (schema && typeof schema === "object") {
    if (schema.type === "object") {
      if (schema.additionalProperties !== false) fail("schema.not_strict", `${path} must set additionalProperties=false.`);
      const keys = Object.keys(schema.properties ?? {});
      const required = new Set(schema.required ?? []);
      for (const key of keys) if (!required.has(key)) fail("schema.optional_property", `${path}.${key} must be required for strict output.`);
    }
    for (const [key, value] of Object.entries(schema)) inspectStrictObjects(value, `${path}.${key}`);
  }
}
const openaiSchema = JSON.parse(await readFile(resolve(beautyRoot, "schemas/openai-explanation.schema.json"), "utf8"));
inspectStrictObjects(openaiSchema);

const sql = await readFile(resolve(beautyRoot, "supabase/migrations/0001_quirk_beauty_taste_engine.sql"), "utf8");
for (const requiredSql of [
  "create schema if not exists quirk_beauty_private",
  "revoke all on schema quirk_beauty_private from public, anon, authenticated",
  "force row level security",
  "grant select, insert on quirk_beauty_private.taste_choices to authenticated",
  "grant select, insert on quirk_beauty_private.outcome_observations to authenticated",
]) if (!sql.toLowerCase().includes(requiredSql)) fail("supabase.missing_control", requiredSql);
if (/create\s+table\s+(if\s+not\s+exists\s+)?public\./i.test(sql)) fail("supabase.public_table", "Projection tables must not be created in public.");
if (/grant\s+all[^;]*authenticated/i.test(sql)) fail("supabase.excess_grant", "Authenticated role must not receive ALL.");
if (/grant\s+(update|delete)[^;]*authenticated/i.test(sql)) fail("supabase.mutable_event", "Authenticated role must not update or delete event records.");

const airtable = JSON.parse(await readFile(resolve(beautyRoot, "airtable/field-authority.json"), "utf8"));
const editable = Object.entries(airtable.fields).filter(([, spec]) => spec.editable).map(([name]) => name);
if (editable.join(",") !== "operatorNote") fail("airtable.authority", `Only operatorNote may be editable; found ${editable.join(", ")}`);

const wranglerRaw = await readFile(resolve(beautyRoot, "cloudflare/wrangler.jsonc"), "utf8");
const wrangler = JSON.parse(wranglerRaw.replace(/^\s*\/\/.*$/gm, ""));
if (wrangler.workers_dev !== false) fail("cloudflare.public_preview", "workers_dev must be false.");
if (wrangler.route || wrangler.routes) fail("cloudflare.route", "Candidate Worker must not declare a public route.");
if (wrangler.vars?.QUIRK_RUNTIME_STATE !== "candidate_disabled") fail("cloudflare.runtime", "Worker must default to candidate_disabled.");

const secretPatterns = [
  /OPENAI_API_KEY\s*=/,
  /SUPABASE_SERVICE_ROLE_KEY\s*=/,
  /CLOUDFLARE_API_TOKEN\s*=/,
  /AIRTABLE_(API_)?KEY\s*=/,
  /sk-[A-Za-z0-9_-]{20,}/,
];
for (const path of allFiles) {
  if (path.endsWith("MANIFEST.sha256")) continue;
  const text = await readFile(path, "utf8").catch(() => "");
  for (const pattern of secretPatterns) if (pattern.test(text)) fail("secret.detected", `${relative(repoRoot, path)} matched ${pattern}`);
}

if (failures.length > 0) {
  for (const item of failures) console.error(`${item.code}: ${item.message}`);
  process.exit(1);
}
console.log(`PACK VALID: ${allFiles.length} controlled files; Beauty canon ceiling intact; boundary ${boundaryDigest}`);
