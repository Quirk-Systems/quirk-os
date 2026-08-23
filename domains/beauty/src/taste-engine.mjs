import { digest } from "./canonical-json.mjs";
import {
  assertChoice,
  assertExplicitOutcome,
  assertHumanDecision,
  assertUnexpired,
  isDateTime,
  requireInvariant,
} from "./invariants.mjs";

function feature(key, value) {
  return `${key}=${String(value)}`;
}

function parseFeature(encoded) {
  const split = encoded.indexOf("=");
  return [encoded.slice(0, split), encoded.slice(split + 1)];
}

function optionHasFeature(option, encoded) {
  const [key, value] = parseFeature(encoded);
  return Object.prototype.hasOwnProperty.call(option.attributes, key) && String(option.attributes[key]) === value;
}

function unique(values) {
  return [...new Set(values)];
}

function assertOptions(options) {
  requireInvariant(Array.isArray(options) && options.length >= 2, "options.too_few", "At least two options are required.");
  requireInvariant(new Set(options.map((option) => option.id)).size === options.length, "options.duplicate_id", "Option IDs must be unique.");
  for (const option of options) {
    requireInvariant(typeof option.id === "string" && option.id.length > 0, "options.id_missing", "Option ID is required.");
    requireInvariant(option.attributes && typeof option.attributes === "object" && !Array.isArray(option.attributes), "options.attributes_missing", "Option attributes must be an object.");
    requireInvariant(Object.keys(option.attributes).length > 0, "options.attributes_empty", "Option attributes cannot be empty.");
  }
}

function assertPositiveTtl(ttlHours) {
  requireInvariant(typeof ttlHours === "number" && Number.isFinite(ttlHours) && ttlHours > 0, "time.invalid_ttl", "TTL hours must be positive.");
}

export function derivePreferenceEvidence({ choice, options }) {
  assertOptions(options);
  assertChoice(choice, options);
  if (choice.abstained) return [];

  const byId = new Map(options.map((option) => [option.id, option]));
  const selected = byId.get(choice.selectedOptionId);
  const rejected = choice.presentedOptionIds
    .filter((id) => id !== choice.selectedOptionId)
    .map((id) => byId.get(id));

  const comparisons = [];
  for (const other of rejected) {
    const differingKeys = Object.keys(selected.attributes)
      .filter((key) => Object.prototype.hasOwnProperty.call(other.attributes, key))
      .filter((key) => String(selected.attributes[key]) !== String(other.attributes[key]))
      .sort();
    requireInvariant(differingKeys.length > 0, "evidence.no_contrast", `Options ${selected.id} and ${other.id} have no explicit attribute contrast.`);
    for (const key of differingKeys) comparisons.push({ other, key, denominator: differingKeys.length * rejected.length });
  }

  return comparisons.map(({ other, key, denominator }) => ({
    id: `evidence:${choice.id}:${other.id}:${key}`,
    actorId: choice.actorId,
    purpose: choice.context.purpose,
    contextId: choice.context.id,
    preferredFeature: feature(key, selected.attributes[key]),
    contrastedFeature: feature(key, other.attributes[key]),
    sourceChoiceId: choice.id,
    sourceType: "explicit_human_choice",
    weight: Number((1 / denominator).toFixed(6)),
    confidence: 0.7,
    truthStatus: "candidate",
    recordedAt: choice.capturedAt,
  }));
}

export function rankRecommendations({ actorId, purpose, candidates, evidence, generatedAt, ttlHours = 168 }) {
  assertOptions(candidates);
  requireInvariant(typeof actorId === "string" && actorId.length > 0, "recommendation.actor_missing", "Actor is required.");
  requireInvariant(typeof purpose === "string" && purpose.length > 0, "recommendation.purpose_missing", "Purpose is required.");
  requireInvariant(isDateTime(generatedAt), "recommendation.invalid_time", "Generation timestamp is invalid.");
  assertPositiveTtl(ttlHours);

  const scopedEvidence = evidence.filter((item) => item.actorId === actorId && item.purpose === purpose);
  const expiresAt = new Date(Date.parse(generatedAt) + ttlHours * 60 * 60 * 1000).toISOString();

  const ranked = candidates.map((option) => {
    const factorMap = new Map();
    for (const item of scopedEvidence) {
      if (optionHasFeature(option, item.preferredFeature)) {
        const factor = factorMap.get(item.preferredFeature) ?? { feature: item.preferredFeature, contribution: 0, evidenceIds: [] };
        factor.contribution += item.weight;
        factor.evidenceIds.push(item.id);
        factorMap.set(item.preferredFeature, factor);
      }
      if (optionHasFeature(option, item.contrastedFeature)) {
        const factor = factorMap.get(item.contrastedFeature) ?? { feature: item.contrastedFeature, contribution: 0, evidenceIds: [] };
        factor.contribution -= item.weight * 0.5;
        factor.evidenceIds.push(item.id);
        factorMap.set(item.contrastedFeature, factor);
      }
    }

    const factors = [...factorMap.values()]
      .map((factor) => ({
        ...factor,
        contribution: Number(factor.contribution.toFixed(6)),
        evidenceIds: unique(factor.evidenceIds).sort(),
      }))
      .sort((left, right) => Math.abs(right.contribution) - Math.abs(left.contribution) || left.feature.localeCompare(right.feature));
    const score = Number(factors.reduce((sum, factor) => sum + factor.contribution, 0).toFixed(6));
    const evidenceIds = unique(factors.flatMap((factor) => factor.evidenceIds)).sort();
    const insufficientEvidence = evidenceIds.length === 0;
    const confidence = insufficientEvidence ? 0 : Number(Math.min(0.95, 0.5 + evidenceIds.length * 0.05).toFixed(2));
    const idSeed = { actorId, purpose, optionId: option.id, evidenceIds, generatedAt };

    return {
      id: `recommendation:${digest(idSeed).slice(7, 23)}`,
      actorId,
      purpose,
      optionId: option.id,
      score,
      confidence,
      evidenceIds,
      factors,
      insufficientEvidence,
      status: "candidate",
      generatedAt,
      expiresAt,
    };
  });

  return ranked.sort((left, right) => right.score - left.score || left.optionId.localeCompare(right.optionId));
}

export function recordOutcome({ recommendation, actorId, purpose, optionId, kind, explicit, testedInRealWorld, sourceType, note = "", observedAt }) {
  requireInvariant(isDateTime(observedAt), "outcome.invalid_time", "Outcome timestamp is invalid.");
  const outcome = {
    id: `outcome:${digest({ recommendationId: recommendation.id, actorId, purpose, kind, observedAt }).slice(7, 23)}`,
    actorId,
    purpose,
    recommendationId: recommendation.id,
    optionId,
    kind,
    explicit,
    testedInRealWorld,
    sourceType,
    note,
    observedAt,
  };
  assertExplicitOutcome(outcome);
  requireInvariant(recommendation.actorId === actorId, "outcome.actor_mismatch", "Outcome actor does not match recommendation actor.");
  requireInvariant(recommendation.purpose === purpose, "outcome.purpose_mismatch", "Outcome purpose does not match recommendation purpose.");
  requireInvariant(recommendation.optionId === optionId, "outcome.option_mismatch", "Outcome option does not match recommendation option.");
  requireInvariant(Date.parse(observedAt) >= Date.parse(recommendation.generatedAt), "outcome.before_recommendation", "Outcome cannot precede the recommendation.");
  return outcome;
}

export function proposeGraphUpdate({ graph, recommendation, outcome, proposedAt, ttlHours = 24 }) {
  assertExplicitOutcome(outcome);
  requireInvariant(isDateTime(proposedAt), "proposal.invalid_time", "Proposal timestamp is invalid.");
  assertPositiveTtl(ttlHours);
  requireInvariant(outcome.recommendationId === recommendation.id, "proposal.lineage_mismatch", "Outcome and recommendation lineage do not match.");
  requireInvariant(outcome.actorId === graph.actorId && recommendation.actorId === graph.actorId, "proposal.actor_mismatch", "Graph, outcome, and recommendation actors must match.");
  requireInvariant(outcome.purpose === graph.purpose && recommendation.purpose === graph.purpose, "proposal.purpose_mismatch", "Graph, outcome, and recommendation purpose must match.");
  requireInvariant(outcome.testedInRealWorld === true, "proposal.no_real_world_test", "A graph update requires a real-world test.");
  requireInvariant(outcome.kind !== "not_tested", "proposal.not_tested", "A not-tested outcome cannot propose a graph update.");
  requireInvariant(Date.parse(proposedAt) >= Date.parse(outcome.observedAt), "proposal.before_outcome", "Proposal cannot precede the outcome.");

  const multiplier = outcome.kind === "preferred" ? 0.15 : outcome.kind === "rejected" ? -0.15 : 0;
  const positiveFactors = recommendation.factors.filter((factor) => factor.contribution > 0);
  requireInvariant(positiveFactors.length > 0, "proposal.no_supported_features", "Recommendation has no positively supported features to update.");

  const deltas = positiveFactors.map((factor) => ({
    feature: factor.feature,
    delta: multiplier,
    evidenceIds: unique([...factor.evidenceIds, outcome.id]).sort(),
  }));
  const expiresAt = new Date(Date.parse(proposedAt) + ttlHours * 60 * 60 * 1000).toISOString();
  const requiresRevision = outcome.kind === "mixed";
  const seed = { actorId: graph.actorId, purpose: graph.purpose, recommendationId: recommendation.id, outcomeId: outcome.id, expectedGraphRevision: graph.revision, deltas, requiresRevision };

  return {
    id: `graph-update-proposal:${digest(seed).slice(7, 23)}`,
    actorId: graph.actorId,
    purpose: graph.purpose,
    expectedGraphRevision: graph.revision,
    recommendationId: recommendation.id,
    outcomeId: outcome.id,
    deltas,
    requiresRevision,
    autoApply: false,
    truthStatus: "candidate",
    proposedAt,
    expiresAt,
  };
}

export function decideGraphUpdate({ proposal, actorId, purpose, decision, humanConfirmed, reason, corrections = [], decidedAt, ttlHours = 2 }) {
  requireInvariant(isDateTime(decidedAt), "gate.invalid_time", "Decision timestamp is invalid.");
  assertPositiveTtl(ttlHours);
  assertUnexpired(proposal.expiresAt, new Date(decidedAt));
  const result = {
    id: `graph-update-decision:${digest({ proposalId: proposal.id, actorId, purpose, decision, decidedAt }).slice(7, 23)}`,
    proposalId: proposal.id,
    actorId,
    purpose,
    decision,
    humanConfirmed,
    reason,
    corrections,
    decidedAt,
    expiresAt: new Date(Date.parse(decidedAt) + ttlHours * 60 * 60 * 1000).toISOString(),
  };
  assertHumanDecision(result);
  requireInvariant(actorId === proposal.actorId, "gate.actor_mismatch", "Decision actor does not match proposal actor.");
  requireInvariant(purpose === proposal.purpose, "gate.purpose_mismatch", "Decision purpose does not match proposal purpose.");
  requireInvariant(Date.parse(decidedAt) >= Date.parse(proposal.proposedAt), "gate.before_proposal", "Decision cannot precede the proposal.");
  if (decision === "revise") requireInvariant(corrections.length > 0, "gate.revision_without_correction", "A revised decision requires explicit corrected deltas.");
  if (decision !== "revise") requireInvariant(corrections.length === 0, "gate.unexpected_corrections", "Corrections are allowed only for a revised decision.");
  if (proposal.requiresRevision) requireInvariant(decision === "revise" || decision === "reject", "gate.mixed_requires_revision", "A mixed outcome cannot be approved without explicit revisions.");
  return result;
}

export function applyApprovedGraphUpdate({ graph, proposal, decision, appliedAt, receiptWriter = "candidate-local-adapter; replace with quirk.core.evidence" }) {
  assertHumanDecision(decision);
  requireInvariant(isDateTime(appliedAt), "gate.invalid_apply_time", "Apply timestamp is invalid.");
  assertUnexpired(proposal.expiresAt, new Date(appliedAt));
  assertUnexpired(decision.expiresAt, new Date(appliedAt));
  requireInvariant(proposal.autoApply === false, "gate.auto_apply_enabled", "Proposal must explicitly disable auto-apply.");
  requireInvariant(decision.proposalId === proposal.id, "gate.proposal_mismatch", "Decision does not authorize this proposal.");
  requireInvariant(graph.actorId === proposal.actorId && graph.actorId === decision.actorId, "gate.actor_mismatch", "Graph, proposal, and decision actors must match.");
  requireInvariant(graph.purpose === proposal.purpose && graph.purpose === decision.purpose, "gate.purpose_mismatch", "Graph, proposal, and decision purposes must match.");
  requireInvariant(graph.revision === proposal.expectedGraphRevision, "gate.stale_revision", "Graph revision changed after proposal creation.");
  requireInvariant(decision.decision !== "reject", "gate.rejected", "Rejected proposal cannot mutate the graph.");
  requireInvariant(Date.parse(appliedAt) >= Date.parse(decision.decidedAt), "gate.apply_before_decision", "Apply cannot precede the decision.");

  const deltas = decision.decision === "revise" ? decision.corrections : proposal.deltas;
  const edgeMap = new Map(graph.edges.map((edge) => [edge.feature, { ...edge, evidenceIds: [...edge.evidenceIds] }]));

  for (const change of deltas) {
    requireInvariant(typeof change.feature === "string" && change.feature.includes("="), "gate.invalid_feature", "Every graph change requires an encoded feature.");
    requireInvariant(Array.isArray(change.evidenceIds) && change.evidenceIds.length > 0, "gate.evidence_missing", "Every graph change requires evidence references.");
    const current = edgeMap.get(change.feature) ?? { feature: change.feature, strength: 0, confidence: 0.5, evidenceIds: [], lastUpdatedAt: appliedAt };
    const nextStrength = typeof change.setStrength === "number" ? change.setStrength : current.strength + change.delta;
    requireInvariant(Number.isFinite(nextStrength), "gate.invalid_strength", "Graph strength must be numeric.");
    edgeMap.set(change.feature, {
      ...current,
      strength: Number(Math.max(-1, Math.min(1, nextStrength)).toFixed(6)),
      confidence: Number(Math.min(0.99, current.confidence + 0.05).toFixed(2)),
      evidenceIds: unique([...current.evidenceIds, ...change.evidenceIds]).sort(),
      lastUpdatedAt: appliedAt,
    });
  }

  const nextGraph = { actorId: graph.actorId, purpose: graph.purpose, revision: graph.revision + 1, edges: [...edgeMap.values()].sort((left, right) => left.feature.localeCompare(right.feature)) };
  const receiptPayload = {
    kind: "PreferenceGraphUpdateReceipt",
    actorId: graph.actorId,
    purpose: graph.purpose,
    proposalId: proposal.id,
    decisionId: decision.id,
    beforeRevision: graph.revision,
    afterRevision: nextGraph.revision,
    appliedAt,
    evidenceIds: unique(deltas.flatMap((delta) => delta.evidenceIds)).sort(),
    effect: "bounded_preference_graph_update",
  };
  return {
    graph: nextGraph,
    receipt: {
      ...receiptPayload,
      id: `receipt:${digest(receiptPayload).slice(7, 23)}`,
      actionDigest: digest(receiptPayload),
      receiptWriter,
    },
  };
}
