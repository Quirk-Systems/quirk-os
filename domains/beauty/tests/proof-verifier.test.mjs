import test from "node:test";
import assert from "node:assert/strict";
import { generateKeyPairSync, sign } from "node:crypto";
import { readFile } from "node:fs/promises";
import { canonicalize } from "../src/canonical-json.mjs";
import { coreAttestationPayload, verifyProofBundle } from "../src/proof-verifier.mjs";

const synthetic = JSON.parse(await readFile(new URL("../fixtures/proof/synthetic-example.json", import.meta.url), "utf8"));

test("synthetic fixture validates machinery", async () => {
  assert.deepEqual(await verifyProofBundle(synthetic, { allowSynthetic: true }), []);
});

test("synthetic fixture cannot satisfy real proof", async () => {
  const codes = new Set((await verifyProofBundle(synthetic)).map((item) => item.code));
  assert.ok(codes.has("proof.synthetic"));
  assert.ok(codes.has("proof.consent"));
  assert.ok(codes.has("proof.core_attestation_missing"));
});

test("tampered receipt digest is detected", async () => {
  const bundle = structuredClone(synthetic);
  bundle.receipt.afterRevision += 1;
  const codes = new Set((await verifyProofBundle(bundle, { allowSynthetic: true })).map((item) => item.code));
  assert.ok(codes.has("proof.receipt_digest"));
  assert.ok(codes.has("proof.revision_mismatch"));
});

test("unknown recommendation evidence is detected", async () => {
  const bundle = structuredClone(synthetic);
  bundle.recommendation.evidenceIds.push("evidence:invented");
  const codes = new Set((await verifyProofBundle(bundle, { allowSynthetic: true })).map((item) => item.code));
  assert.ok(codes.has("proof.unknown_evidence"));
});

test("core-looking metadata cannot fake a real receipt", async () => {
  const bundle = structuredClone(synthetic);
  bundle.synthetic = false;
  bundle.participantConsent.granted = true;
  bundle.receipt.receiptWriter = "quirk.core.evidence/v1";
  const codes = new Set((await verifyProofBundle(bundle)).map((item) => item.code));
  assert.ok(codes.has("proof.core_attestation_missing"));
});

test("valid Ed25519 core attestation satisfies the cryptographic receipt gate", async () => {
  const { publicKey, privateKey } = generateKeyPairSync("ed25519");
  const keyId = "test-core-key";
  const bundle = structuredClone(synthetic);
  bundle.synthetic = false;
  bundle.participantConsent.granted = true;
  bundle.receipt.receiptWriter = "quirk.core.evidence/v1";
  bundle.coreAttestation = {
    issuer: "quirk.core.evidence",
    keyId,
    algorithm: "Ed25519",
    signature: "pending",
    issuedAt: "2026-08-22T15:03:30.000Z",
  };
  bundle.coreAttestation.signature = sign(null, Buffer.from(canonicalize(coreAttestationPayload(bundle))), privateKey).toString("base64");
  const trustedKeys = { [keyId]: publicKey.export({ type: "spki", format: "pem" }) };
  assert.deepEqual(await verifyProofBundle(bundle, { trustedKeys }), []);
});
