import { readFileSync } from "node:fs";
import { resolve } from "node:path";
const file=process.argv[2];
if (!file) { console.error("Usage: npm run proof:verify -- proof/evidence/real-proof.json"); process.exit(2); }
try { JSON.parse(readFileSync(resolve(file), "utf8")); }
catch (error) { console.error("FAIL: unable to read proof: " + error.message); process.exit(2); }
console.error("HOLD: core_attestation_not_integrated: v0.1 repo-native proof verifier is synthetic-only. Detached Ed25519 verification against an independently administered Quirk-core trust registry is required for real admission.");
process.exit(1);
