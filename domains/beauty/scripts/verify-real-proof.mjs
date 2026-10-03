import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { verifyRealProof } from "../src/index.mjs";
const file=process.argv[2];
if(!file){console.error("Usage: npm run proof:verify -- proof/evidence/real-proof.json");process.exit(2);}
let proof;try{proof=JSON.parse(readFileSync(resolve(file),"utf8"));}catch(error){console.error(`FAIL: unable to read proof: ${error.message}`);process.exit(2);}
const verdict=verifyRealProof(proof);if(!verdict.passed){console.error("FAIL: real-world Taste Engine proof is not admissible.");for(const error of verdict.errors)console.error(`- ${error.code}: ${error.message}`);process.exit(1);}console.log("PASS: real-world Taste Engine proof is complete and traceable.");
