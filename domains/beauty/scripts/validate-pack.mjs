import { createHash } from "node:crypto";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const domainRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = resolve(domainRoot, "../..");
const requiredDomainFiles = ["README.md","candidate/domain-pack.yaml","candidate/object-registry.yaml","candidate/capability-registry.yaml","proof/proof-manifest.yaml","proof/runbook.md","schemas/real-proof.schema.json","tests/supabase-migration-contract.test.mjs"];
const requiredRepoFiles = ["docs/canon/QUIRK-BEAUTY-DOMAIN-BOUNDARY.yaml","docs/canon/QUIRK-BEAUTY-DOMAIN-BOUNDARY.payload.json","decisions/ADR-0002-quirk-beauty-domain-boundary.md","supabase/migrations/20260821090000_quirk_beauty_taste_engine_candidate.sql","supabase/tests/quirk_beauty_taste_engine_rls.sql",".github/workflows/quirk-beauty-domain-pack.yml"];
const failures = [];
function requireFile(base,path){try{if(!statSync(join(base,path)).isFile())failures.push(`required path is not a file: ${path}`);}catch{failures.push(`missing required file: ${path}`);}}
requiredDomainFiles.forEach((path)=>requireFile(domainRoot,path));
requiredRepoFiles.forEach((path)=>requireFile(repoRoot,path));
function walk(directory){return readdirSync(directory,{withFileTypes:true}).flatMap((entry)=>{const path=join(directory,entry.name);return entry.isDirectory()?walk(path):[path];});}
for(const path of walk(domainRoot)){const rel=relative(domainRoot,path);if(!/\.(yaml|json)$/.test(rel))continue;const text=readFileSync(path,"utf8");if(/truth_status:\s*canonical\b/.test(text)||/"truth_status"\s*:\s*"canonical"/.test(text))failures.push(`canonical truth status escaped docs/canon: domains/beauty/${rel}`);if(/lifecycle_status:\s*canonized\b/.test(text)||/"lifecycle_status"\s*:\s*"canonized"/.test(text))failures.push(`canonized lifecycle status escaped docs/canon: domains/beauty/${rel}`);}
const packageJson=JSON.parse(readFileSync(join(domainRoot,"package.json"),"utf8"));
const boundaryPath=resolve(domainRoot,packageJson.quirk.canonicalArtifact);
const payloadPath=resolve(domainRoot,packageJson.quirk.canonicalPayload);
const boundary=readFileSync(boundaryPath,"utf8");
const payload=JSON.parse(readFileSync(payloadPath,"utf8"));
function stable(value){if(value===null||typeof value!=="object")return JSON.stringify(value);if(Array.isArray(value))return `[${value.map(stable).join(",")}]`;return `{${Object.keys(value).sort().map((key)=>`${JSON.stringify(key)}:${stable(value[key])}`).join(",")}}`;}
const expectedHash=`sha256:${createHash("sha256").update(stable(payload)).digest("hex")}`;
if(packageJson.quirk.canonicalContentHash!==expectedHash)failures.push("package canonicalContentHash does not match the admitted payload");
if(!boundary.includes(`content_hash: ${expectedHash}`))failures.push("canonical boundary content hash does not match the admitted payload");
const expectedChain=["choice","preference_evidence","recommendation","real_world_outcome","human_confirmed_graph_update"];
let cursor=-1;for(const stage of expectedChain){const next=boundary.indexOf(`- ${stage}`,cursor+1);if(next<0)failures.push(`canonical proof chain missing stage: ${stage}`);cursor=next;}
if(!boundary.includes("synthetic_proof_sufficient: false"))failures.push("canonical boundary must reject synthetic proof as sufficient");
if(!boundary.includes("only_this_domain_boundary_is_canonical_in_v0_1"))failures.push("canonical ceiling invariant is missing");
const migration=readFileSync(join(repoRoot,"supabase/migrations/20260821090000_quirk_beauty_taste_engine_candidate.sql"),"utf8");
if(/grant\s+update\s*\([^)]*state[^)]*\)\s+on\s+beauty\.taste_sessions\s+to\s+authenticated/i.test(migration))failures.push("authenticated lifecycle-state mutation escaped the migration contract");
if(!/auto_apply\s+boolean\s+not\s+null\s+default\s+false\s+check\s*\(auto_apply\s*=\s*false\)/i.test(migration))failures.push("database projection no longer structurally forbids auto-application");
if(failures.length){console.error("PACK INVALID");failures.forEach((failure)=>console.error(`- ${failure}`));process.exit(1);}
console.log(`PACK VALID: ${requiredDomainFiles.length+requiredRepoFiles.length} required files present; canon ceiling intact; boundary hash ${expectedHash}.`);
