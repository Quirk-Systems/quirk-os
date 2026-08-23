import { assertSchema } from "./schema-validator.mjs";

const AUTHORITY_STATEMENT = "Recommendation only. No action or Preference Graph update is authorized.";

export function buildExplanationRequest({ model, recommendation, evidence, outputSchema }) {
  if (typeof model !== "string" || model.length === 0) throw new Error("Runtime must inject an explicit model identifier.");
  if (recommendation.insufficientEvidence || recommendation.evidenceIds.length === 0) throw new Error("Insufficient evidence cannot be rendered as a supported explanation.");
  const byId = new Map(evidence.map((item) => [item.id, item]));
  const lockedEvidence = recommendation.evidenceIds.map((id) => {
    const item = byId.get(id);
    if (!item) throw new Error(`Recommendation references unavailable evidence: ${id}`);
    return item;
  });

  return {
    model,
    input: [
      {
        role: "system",
        content: [
          {
            type: "input_text",
            text: [
              "Render a concise Quirk Beauty recommendation explanation from the supplied locked envelope.",
              "Do not change ranking, score, confidence, option, evidence IDs, purpose, or authority.",
              "Do not infer skin condition, health, race, ethnicity, age, gender identity, or any sensitive attribute.",
              "Do not add product claims, medical guidance, purchase instructions, or unstated observations.",
              `The authorityStatement must be exactly: ${AUTHORITY_STATEMENT}`,
            ].join("\n"),
          },
        ],
      },
      {
        role: "user",
        content: [{ type: "input_text", text: JSON.stringify({ recommendation, evidence: lockedEvidence }) }],
      },
    ],
    text: {
      format: {
        type: "json_schema",
        name: "quirk_beauty_recommendation_explanation",
        strict: true,
        schema: outputSchema,
      },
    },
    store: false,
  };
}

export function validateExplanation({ explanation, recommendation, outputSchema }) {
  assertSchema(outputSchema, explanation, "OpenAI explanation");
  if (explanation.recommendationId !== recommendation.id) throw new Error("Explanation recommendation ID changed.");
  if (explanation.authorityStatement !== AUTHORITY_STATEMENT) throw new Error("Explanation authority statement changed.");
  const allowed = new Set(recommendation.evidenceIds);
  for (const id of explanation.evidenceIds) if (!allowed.has(id)) throw new Error(`Explanation invented evidence: ${id}`);
  for (const reason of explanation.reasons) for (const id of reason.evidenceIds) if (!allowed.has(id)) throw new Error(`Explanation reason invented evidence: ${id}`);
  return explanation;
}

export { AUTHORITY_STATEMENT };
