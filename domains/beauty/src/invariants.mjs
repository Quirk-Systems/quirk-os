export class InvariantError extends Error {
  constructor(code, message, details = {}) {
    super(message);
    this.name = "InvariantError";
    this.code = code;
    this.details = details;
  }
}

export function requireInvariant(condition, code, message, details = {}) {
  if (!condition) throw new InvariantError(code, message, details);
}

export function isDateTime(value) {
  return typeof value === "string" && Number.isFinite(Date.parse(value));
}

export function assertUnexpired(expiresAt, at = new Date()) {
  requireInvariant(isDateTime(expiresAt), "time.invalid_expiry", "Expiry must be an ISO-compatible timestamp.");
  const atDate = at instanceof Date ? at : new Date(at);
  requireInvariant(Number.isFinite(atDate.getTime()), "time.invalid_reference", "Reference time is invalid.");
  requireInvariant(atDate.getTime() <= Date.parse(expiresAt), "time.expired", "Artifact is expired.", { expiresAt, at: atDate.toISOString() });
}

export function assertChoice(choice, options) {
  requireInvariant(choice && typeof choice === "object", "choice.missing", "Choice is required.");
  requireInvariant(choice.sourceType === "explicit_human_choice", "choice.implicit_source", "Choice must come from an explicit human action.");
  requireInvariant(isDateTime(choice.capturedAt), "choice.invalid_time", "Choice timestamp is invalid.");
  requireInvariant(typeof choice.actorId === "string" && choice.actorId.length > 0, "choice.actor_missing", "Choice actor is required.");
  requireInvariant(choice.context && typeof choice.context.id === "string" && typeof choice.context.purpose === "string", "choice.context_missing", "Choice context and purpose are required.");
  requireInvariant(Array.isArray(choice.presentedOptionIds) && choice.presentedOptionIds.length >= 2, "choice.too_few_options", "At least two presented options are required.");
  requireInvariant(new Set(choice.presentedOptionIds).size === choice.presentedOptionIds.length, "choice.duplicate_options", "Presented options must be unique.");
  const optionIds = new Set(options.map((option) => option.id));
  requireInvariant(choice.presentedOptionIds.every((id) => optionIds.has(id)), "choice.unknown_option", "Every presented option must exist.");
  requireInvariant(
    (choice.abstained === true && choice.selectedOptionId === null) ||
      (choice.abstained === false && typeof choice.selectedOptionId === "string" && choice.presentedOptionIds.includes(choice.selectedOptionId)),
    "choice.selection_incoherent",
    "Choice selection and abstention state are incoherent."
  );
}

export function assertExplicitOutcome(outcome) {
  requireInvariant(outcome && typeof outcome === "object", "outcome.missing", "Outcome is required.");
  requireInvariant(outcome.explicit === true, "outcome.inferred", "Outcome must be explicitly reported by a human.");
  requireInvariant(outcome.sourceType === "explicit_human_report", "outcome.invalid_source", "Outcome source must be an explicit human report.");
  requireInvariant(["preferred", "rejected", "mixed", "not_tested"].includes(outcome.kind), "outcome.invalid_kind", "Outcome kind is invalid.");
  requireInvariant(isDateTime(outcome.observedAt), "outcome.invalid_time", "Outcome timestamp is invalid.");
  const coherent = outcome.kind === "not_tested" ? outcome.testedInRealWorld === false : outcome.testedInRealWorld === true;
  requireInvariant(coherent, "outcome.test_incoherent", "Outcome kind and real-world test state are incoherent.");
}

export function assertHumanDecision(decision) {
  requireInvariant(decision && typeof decision === "object", "gate.decision_missing", "Decision is required.");
  requireInvariant(decision.humanConfirmed === true, "gate.not_human_confirmed", "Graph update decision requires explicit human confirmation.");
  requireInvariant(["approve", "revise", "reject"].includes(decision.decision), "gate.invalid_decision", "Decision must be approve, revise, or reject.");
  requireInvariant(typeof decision.reason === "string" && decision.reason.trim().length > 0, "gate.reason_missing", "Decision reason is required.");
  requireInvariant(isDateTime(decision.decidedAt) && isDateTime(decision.expiresAt), "gate.invalid_time", "Decision timestamps are invalid.");
}
