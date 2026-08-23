export const context = {
  id: "context:everyday-lip:daylight",
  realm: "beauty",
  purpose: "personal_beauty_recommendation",
  attributes: {
    occasion: "everyday",
    lighting: "daylight",
    budget_ceiling_usd: 25,
  },
};

export const options = [
  {
    id: "option:soft-satin-rose",
    label: "Soft Satin Rose",
    attributes: { finish: "satin", chroma: "muted", effort_minutes: 5, fragrance: "low" },
    truthStatus: "candidate",
  },
  {
    id: "option:flat-matte-cherry",
    label: "Flat Matte Cherry",
    attributes: { finish: "matte", chroma: "vivid", effort_minutes: 10, fragrance: "high" },
    truthStatus: "candidate",
  },
  {
    id: "option:satin-mauve",
    label: "Satin Mauve",
    attributes: { finish: "satin", chroma: "muted", effort_minutes: 4, fragrance: "low" },
    truthStatus: "candidate",
  },
  {
    id: "option:matte-coral",
    label: "Matte Coral",
    attributes: { finish: "matte", chroma: "vivid", effort_minutes: 9, fragrance: "high" },
    truthStatus: "candidate",
  },
];

export const choice = {
  id: "choice:001",
  sessionId: "session:001",
  actorId: "human:proof-participant",
  context,
  presentedOptionIds: ["option:soft-satin-rose", "option:flat-matte-cherry"],
  selectedOptionId: "option:soft-satin-rose",
  abstained: false,
  sourceType: "explicit_human_choice",
  capturedAt: "2026-08-21T12:00:00.000Z",
};

export const graph = {
  actorId: "human:proof-participant",
  purpose: "personal_beauty_recommendation",
  revision: 0,
  edges: [],
};
