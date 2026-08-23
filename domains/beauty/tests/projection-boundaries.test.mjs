import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { toAirtableProjection, applyOperatorPatch } from "../src/airtable-projection.mjs";
import { buildExplanationRequest, validateExplanation, AUTHORITY_STATEMENT } from "../src/openai-explanation-adapter.mjs";

const bundle = JSON.parse(await readFile(new URL("../fixtures/proof/synthetic-example.json", import.meta.url), "utf8"));
const outputSchema = JSON.parse(await readFile(new URL("../schemas/openai-explanation.schema.json", import.meta.url), "utf8"));

test("Airtable projection does not treat candidate receipt as core receipt", () => {
  const record = toAirtableProjection(bundle, { participantAlias: "synthetic" });
  assert.equal(record.coreReceiptRef, null);
  assert.notEqual(record.state, "receipted");
});

test("Airtable operator can edit only operatorNote", () => {
  const record = toAirtableProjection(bundle, { participantAlias: "synthetic" });
  assert.equal(applyOperatorPatch(record, { operatorNote: "Reviewed" }).operatorNote, "Reviewed");
  assert.throws(() => applyOperatorPatch(record, { decision: "approve" }), /not operator-editable/);
});

test("OpenAI request is strict, non-storing, and evidence locked", () => {
  const request = buildExplanationRequest({ model: "runtime-injected-model", recommendation: bundle.recommendation, evidence: bundle.evidence, outputSchema });
  assert.equal(request.store, false);
  assert.equal(request.text.format.strict, true);
  assert.equal(request.text.format.type, "json_schema");
});

test("OpenAI adapter refuses invented evidence", () => {
  const explanation = {
    recommendationId: bundle.recommendation.id,
    summary: "Candidate match.",
    reasons: [{ text: "Invented reason", evidenceIds: ["evidence:invented"] }],
    uncertainties: [],
    authorityStatement: AUTHORITY_STATEMENT,
    evidenceIds: ["evidence:invented"],
  };
  assert.throws(() => validateExplanation({ explanation, recommendation: bundle.recommendation, outputSchema }), /invented evidence/);
});

test("OpenAI adapter refuses insufficient-evidence recommendation before provider", () => {
  assert.throws(() => buildExplanationRequest({ model: "runtime-injected-model", recommendation: { ...bundle.recommendation, insufficientEvidence: true }, evidence: bundle.evidence, outputSchema }), /Insufficient evidence/);
});
