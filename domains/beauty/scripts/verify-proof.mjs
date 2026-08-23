import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { verifyProofBundle } from "../src/proof-verifier.mjs";

const args = process.argv.slice(2);
const file = args.find((item) => !item.startsWith("--"));
const trustIndex = args.indexOf("--trust-registry");
if (!file) {
  console.error("Usage: npm run proof:verify -- <proof-bundle.json> --trust-registry <trusted-keys.json>");
  process.exit(2);
}
let trustedKeys = {};
if (trustIndex >= 0 && args[trustIndex + 1]) trustedKeys = JSON.parse(await readFile(resolve(process.cwd(), args[trustIndex + 1]), "utf8"));

const bundle = JSON.parse(await readFile(resolve(process.cwd(), file), "utf8"));
const issues = await verifyProofBundle(bundle, { allowSynthetic: false, trustedKeys });
if (issues.length > 0) {
  for (const item of issues) console.error(`${item.code}: ${item.path}: ${item.message}`);
  process.exit(1);
}
console.log(`REAL PROOF VALID: ${bundle.proofId}`);
