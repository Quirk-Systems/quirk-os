const EDITABLE_FIELDS = new Set(["operatorNote"]);

export function toAirtableProjection(bundle, { participantAlias, realProofVerified = false }) {
  if (typeof participantAlias !== "string" || participantAlias.length === 0) throw new Error("A non-identifying participant alias is required.");
  return {
    recordKey: `qb:${bundle.proofId}`,
    proofId: bundle.proofId,
    participantAlias,
    purpose: bundle.choice.context.purpose,
    state: realProofVerified && bundle.receipt ? "receipted" : bundle.decision?.decision === "reject" ? "rejected" : bundle.proposal ? "awaiting_human_gate" : bundle.recommendation ? "awaiting_real_world_test" : "candidate",
    recommendationOption: bundle.recommendation?.optionId ?? null,
    outcome: bundle.outcome?.kind ?? null,
    decision: bundle.decision?.decision ?? null,
    coreReceiptRef: realProofVerified ? bundle.receipt?.id ?? null : null,
    operatorNote: "",
    updatedAt: bundle.verifiedAt,
  };
}

export function applyOperatorPatch(record, patch) {
  for (const key of Object.keys(patch)) if (!EDITABLE_FIELDS.has(key)) throw new Error(`Airtable field is not operator-editable: ${key}`);
  return { ...record, ...patch };
}

export const AIRTABLE_OPERATOR_EDITABLE_FIELDS = [...EDITABLE_FIELDS];
