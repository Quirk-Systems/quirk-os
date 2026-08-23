import { verify as verifySignature } from "node:crypto";
import { readFile } from "node:fs/promises";
import { canonicalize, digest } from "./canonical-json.mjs";
import { validateSchema } from "./schema-validator.mjs";

const proofSchemaUrl = new URL("../schemas/proof-bundle.schema.json", import.meta.url);

function issue(code, message, path = "$") {
  return { code, message, path };
}
function same(value, expected, code, message, path) {
  return value === expected ? [] : [issue(code, message, path)];
}
function date(value) {
  return Number.isFinite(Date.parse(value)) ? Date.parse(value) : Number.NaN;
}
function receiptPayload(receipt) {
  return {
    kind: receipt.kind,
    actorId: receipt.actorId,
    purpose: receipt.purpose,
    proposalId: receipt.proposalId,
    decisionId: receipt.decisionId,
    beforeRevision: receipt.beforeRevision,
    afterRevision: receipt.afterRevision,
    appliedAt: receipt.appliedAt,
    evidenceIds: receipt.evidenceIds,
    effect: receipt.effect,
  };
}
export function coreAttestationPayload(bundle) {
  return {
    proofId: bundle.proofId,
    receiptId: bundle.receipt.id,
    actionDigest: bundle.receipt.actionDigest,
    actorId: bundle.receipt.actorId,
    purpose: bundle.receipt.purpose,
    proposalId: bundle.receipt.proposalId,
    decisionId: bundle.receipt.decisionId,
    beforeRevision: bundle.receipt.beforeRevision,
    afterRevision: bundle.receipt.afterRevision,
  };
}

function verifyCoreAttestation(bundle, trustedKeys) {
  const issues = [];
  const attestation = bundle.coreAttestation;
  if (!attestation || typeof attestation !== "object" || Array.isArray(attestation)) {
    return [issue("proof.core_attestation_missing", "Real proof requires a detached Quirk-core receipt attestation.", "$.coreAttestation")];
  }
  const allowedKeys = new Set(["issuer", "keyId", "algorithm", "signature", "issuedAt"]);
  for (const key of Object.keys(attestation)) if (!allowedKeys.has(key)) issues.push(issue("proof.core_attestation_extra_field", `Unexpected attestation field: ${key}.`, `$.coreAttestation.${key}`));
  for (const key of allowedKeys) if (typeof attestation[key] !== "string" || attestation[key].length === 0) issues.push(issue("proof.core_attestation_field", `${key} is required.`, `$.coreAttestation.${key}`));
  if (issues.length > 0) return issues;
  if (attestation.issuer !== "quirk.core.evidence") issues.push(issue("proof.core_issuer", "Receipt attestation issuer must be quirk.core.evidence.", "$.coreAttestation.issuer"));
  if (attestation.algorithm !== "Ed25519") issues.push(issue("proof.core_algorithm", "Receipt attestation must use Ed25519.", "$.coreAttestation.algorithm"));
  if (!Number.isFinite(Date.parse(attestation.issuedAt))) issues.push(issue("proof.core_attestation_time", "Attestation issue time is invalid.", "$.coreAttestation.issuedAt"));
  const publicKey = trustedKeys?.[attestation.keyId];
  if (!publicKey) {
    issues.push(issue("proof.trust_root_missing", `No trusted Quirk-core public key is registered for ${attestation.keyId}.`, "$.coreAttestation.keyId"));
    return issues;
  }
  try {
    const valid = verifySignature(null, Buffer.from(canonicalize(coreAttestationPayload(bundle))), publicKey, Buffer.from(attestation.signature, "base64"));
    if (!valid) issues.push(issue("proof.core_signature_invalid", "Core receipt attestation signature is invalid.", "$.coreAttestation.signature"));
  } catch (error) {
    issues.push(issue("proof.core_signature_error", `Core receipt attestation could not be verified: ${error.message}`, "$.coreAttestation.signature"));
  }
  return issues;
}

export async function verifyProofBundle(bundle, { allowSynthetic = false, trustedKeys = {} } = {}) {
  const schema = JSON.parse(await readFile(proofSchemaUrl, "utf8"));
  const issues = validateSchema(schema, bundle).map((entry) => issue(`schema.${entry.keyword}`, entry.message, entry.path));
  if (issues.length > 0) return issues;

  const { choice, evidence, recommendation, outcome, proposal, decision, receipt, participantConsent } = bundle;
  const actorId = choice.actorId;
  const purpose = choice.context.purpose;

  if (!allowSynthetic && bundle.synthetic) issues.push(issue("proof.synthetic", "Synthetic execution cannot satisfy the real-world proof.", "$.synthetic"));
  if (!allowSynthetic && participantConsent.granted !== true) issues.push(issue("proof.consent", "Participant consent is required.", "$.participantConsent.granted"));
  if (participantConsent.purpose !== purpose) issues.push(issue("proof.consent_purpose", "Consent purpose must match the proof purpose.", "$.participantConsent.purpose"));

  for (const [path, value] of [
    ["$.recommendation.actorId", recommendation.actorId], ["$.outcome.actorId", outcome.actorId],
    ["$.proposal.actorId", proposal.actorId], ["$.decision.actorId", decision.actorId], ["$.receipt.actorId", receipt.actorId],
  ]) issues.push(...same(value, actorId, "proof.actor_mismatch", "All proof stages must use the same actor.", path));
  for (const [path, value] of [
    ["$.recommendation.purpose", recommendation.purpose], ["$.outcome.purpose", outcome.purpose],
    ["$.proposal.purpose", proposal.purpose], ["$.decision.purpose", decision.purpose], ["$.receipt.purpose", receipt.purpose],
  ]) issues.push(...same(value, purpose, "proof.purpose_mismatch", "All proof stages must use the same purpose partition.", path));

  const evidenceIds = new Set(evidence.map((item) => item.id));
  for (const [index, item] of evidence.entries()) {
    if (item.actorId !== actorId || item.purpose !== purpose || item.sourceChoiceId !== choice.id || item.contextId !== choice.context.id) {
      issues.push(issue("proof.evidence_lineage", "Evidence must derive from this choice, actor, purpose, and context.", `$.evidence[${index}]`));
    }
  }
  if (recommendation.insufficientEvidence) issues.push(issue("proof.insufficient_evidence", "A proof-completing recommendation cannot be marked insufficient.", "$.recommendation.insufficientEvidence"));
  for (const id of recommendation.evidenceIds) if (!evidenceIds.has(id)) issues.push(issue("proof.unknown_evidence", `Recommendation references unknown evidence ${id}.`, "$.recommendation.evidenceIds"));

  if (outcome.recommendationId !== recommendation.id || outcome.optionId !== recommendation.optionId) issues.push(issue("proof.outcome_lineage", "Outcome must reference the tested recommendation and option.", "$.outcome"));
  if (!outcome.explicit || outcome.sourceType !== "explicit_human_report") issues.push(issue("proof.inferred_outcome", "Outcome must be an explicit human report.", "$.outcome"));
  if (!outcome.testedInRealWorld || outcome.kind === "not_tested") issues.push(issue("proof.no_real_world_outcome", "A proof-completing outcome must come from a real-world test.", "$.outcome"));

  if (proposal.recommendationId !== recommendation.id || proposal.outcomeId !== outcome.id) issues.push(issue("proof.proposal_lineage", "Graph proposal must reference this recommendation and outcome.", "$.proposal"));
  if (proposal.autoApply !== false) issues.push(issue("proof.auto_apply", "Graph proposal must disable auto-apply.", "$.proposal.autoApply"));
  if (decision.proposalId !== proposal.id || !decision.humanConfirmed) issues.push(issue("proof.decision_lineage", "Decision must be an explicit human decision for this proposal.", "$.decision"));
  if (!new Set(["approve", "revise"]).has(decision.decision)) issues.push(issue("proof.non_applying_decision", "A rejected decision cannot complete an applied proof.", "$.decision.decision"));
  if (proposal.requiresRevision && decision.decision !== "revise") issues.push(issue("proof.mixed_not_revised", "A mixed outcome requires an explicit revised decision.", "$.decision.decision"));

  if (receipt.proposalId !== proposal.id || receipt.decisionId !== decision.id) issues.push(issue("proof.receipt_lineage", "Receipt must reference this proposal and decision.", "$.receipt"));
  if (receipt.beforeRevision !== proposal.expectedGraphRevision || receipt.afterRevision !== receipt.beforeRevision + 1) issues.push(issue("proof.revision_mismatch", "Receipt revisions must match the proposal and advance exactly once.", "$.receipt"));
  if (receipt.actionDigest !== digest(receiptPayload(receipt))) issues.push(issue("proof.receipt_digest", "Receipt action digest does not match its canonical payload.", "$.receipt.actionDigest"));
  if (!allowSynthetic) issues.push(...verifyCoreAttestation(bundle, trustedKeys));

  const times = [
    ["consent", participantConsent.recordedAt], ["choice", choice.capturedAt], ["recommendation", recommendation.generatedAt],
    ["outcome", outcome.observedAt], ["proposal", proposal.proposedAt], ["decision", decision.decidedAt],
    ["receipt", receipt.appliedAt], ["verification", bundle.verifiedAt],
  ];
  for (let index = 1; index < times.length; index += 1) {
    if (date(times[index][1]) < date(times[index - 1][1])) issues.push(issue("proof.time_order", `${times[index][0]} cannot precede ${times[index - 1][0]}.`, `$${times[index][0]}`));
  }
  if (date(decision.decidedAt) > date(proposal.expiresAt)) issues.push(issue("proof.proposal_expired", "Decision occurred after proposal expiry.", "$.decision.decidedAt"));
  if (date(receipt.appliedAt) > date(decision.expiresAt)) issues.push(issue("proof.decision_expired", "Effect occurred after decision expiry.", "$.receipt.appliedAt"));
  if (bundle.coreAttestation && date(bundle.coreAttestation.issuedAt) < date(receipt.appliedAt)) issues.push(issue("proof.attestation_before_effect", "Core attestation cannot precede the effect receipt.", "$.coreAttestation.issuedAt"));
  if (bundle.coreAttestation && date(bundle.verifiedAt) < date(bundle.coreAttestation.issuedAt)) issues.push(issue("proof.verification_before_attestation", "Proof verification cannot precede core attestation.", "$.verifiedAt"));

  return issues;
}

export async function assertValidProofBundle(bundle, options = {}) {
  const issues = await verifyProofBundle(bundle, options);
  if (issues.length > 0) {
    const error = new Error(issues.map((item) => `${item.code}: ${item.message}`).join("\n"));
    error.name = "ProofVerificationError";
    error.issues = issues;
    throw error;
  }
  return bundle;
}
