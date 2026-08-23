import { mkdir, writeFile } from "node:fs/promises";
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
import {
  applyApprovedGraphUpdate,
  decideGraphUpdate,
  derivePreferenceEvidence,
  proposeGraphUpdate,
  rankRecommendations,
  recordOutcome,
} from "../src/taste-engine.mjs";
import { assertValidProofBundle, verifyProofBundle } from "../src/proof-verifier.mjs";

const actorId = "participant:synthetic-001";
const purpose = "personal_beauty_recommendation";
const options = [
  { id: "lip:soft-satin", attributes: { finish: "satin", chroma: "muted", fragrance: "low" } },
  { id: "lip:vivid-matte", attributes: { finish: "matte", chroma: "vivid", fragrance: "high" } },
];
const choice = {
  id: "choice:synthetic-001",
  actorId,
  context: { id: "context:everyday-lip", purpose },
  presentedOptionIds: options.map((item) => item.id),
  selectedOptionId: options[0].id,
  abstained: false,
  sourceType: "explicit_human_choice",
  capturedAt: "2026-08-22T14:01:00.000Z",
};
const evidence = derivePreferenceEvidence({ choice, options });
const candidates = [
  { id: "lip:rosewood-satin", attributes: { finish: "satin", chroma: "muted", fragrance: "low" } },
  { id: "lip:scarlet-matte", attributes: { finish: "matte", chroma: "vivid", fragrance: "high" } },
];
const recommendation = rankRecommendations({ actorId, purpose, candidates, evidence, generatedAt: "2026-08-22T14:02:00.000Z" })[0];
const outcome = recordOutcome({
  recommendation,
  actorId,
  purpose,
  optionId: recommendation.optionId,
  kind: "preferred",
  explicit: true,
  testedInRealWorld: true,
  sourceType: "explicit_human_report",
  note: "Synthetic fixture: comfortable finish and appropriate chroma.",
  observedAt: "2026-08-22T15:00:00.000Z",
});
const graph = { actorId, purpose, revision: 4, edges: [] };
const proposal = proposeGraphUpdate({ graph, recommendation, outcome, proposedAt: "2026-08-22T15:01:00.000Z" });
const decision = decideGraphUpdate({
  proposal,
  actorId,
  purpose,
  decision: "approve",
  humanConfirmed: true,
  reason: "Synthetic fixture approves exact proposed deltas.",
  decidedAt: "2026-08-22T15:02:00.000Z",
});
const { receipt } = applyApprovedGraphUpdate({ graph, proposal, decision, appliedAt: "2026-08-22T15:03:00.000Z" });
const bundle = {
  proofId: "qb-taste-proof-synthetic-001",
  synthetic: true,
  participantConsent: { granted: false, recordedAt: "2026-08-22T14:00:00.000Z", purpose },
  choice,
  evidence,
  recommendation,
  outcome,
  proposal,
  decision,
  receipt,
  coreAttestation: null,
  verifiedAt: "2026-08-22T15:04:00.000Z",
};

await assertValidProofBundle(bundle, { allowSynthetic: true });
const realIssues = await verifyProofBundle(bundle, { allowSynthetic: false });
const expected = new Set(["proof.synthetic", "proof.consent", "proof.core_attestation_missing"]);
for (const code of expected) {
  if (!realIssues.some((item) => item.code === code)) throw new Error(`Synthetic fixture failed to trigger ${code}`);
}

const output = fileURLToPath(new URL("../fixtures/proof/synthetic-example.json", import.meta.url));
await mkdir(dirname(output), { recursive: true });
await writeFile(output, `${JSON.stringify(bundle, null, 2)}\n`);
console.log(`SYNTHETIC MACHINERY VALID: ${bundle.proofId}`);
console.log(`REAL ADMISSION DENIED: ${[...expected].join(", ")}`);
