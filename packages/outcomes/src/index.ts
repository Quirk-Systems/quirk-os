export const outcomeClasses = [
  "epistemic",
  "decisional",
  "structural",
  "capability",
  "interoperability",
  "operational",
  "governance",
  "behavioral",
  "experiential",
  "material",
  "continuity",
] as const;

export type OutcomeClass = (typeof outcomeClasses)[number];

export type OutcomeStatus =
  | "proposed"
  | "bounded"
  | "instrumented"
  | "pursued"
  | "observed"
  | "verified"
  | "retained"
  | "rejected"
  | "superseded"
  | "abandoned"
  | "decayed"
  | "invalidated";

export type EvidenceLevel =
  | "asserted"
  | "observed"
  | "measured"
  | "verified"
  | "reproduced"
  | "retained";

export interface OutcomeIndicator {
  id: string;
  description: string;
  baseline?: string | number;
  target: string | number;
  actual?: string | number;
  evidenceRefs: string[];
}

export interface OutcomeContract {
  id: `out_${string}`;
  version: string;
  title: string;
  primaryClass: OutcomeClass;
  secondaryClasses: OutcomeClass[];
  beneficiary: {
    kind: "person" | "group" | "agent" | "system" | "organization" | "market";
    id: string;
  };
  scope: {
    systems: string[];
    objectIds?: string[];
    exclusions?: string[];
  };
  baseline: string;
  targetState: string;
  mechanism?: string;
  assumptions: string[];
  indicators: OutcomeIndicator[];
  guardrails: Array<{
    description: string;
    breachEvidenceRefs?: string[];
  }>;
  owner: string;
  targetBy?: string;
  retentionWindow?: string;
  evidenceLevel: EvidenceLevel;
  confidence: {
    score: number;
    rationale: string;
  };
  reversibility: "easy" | "moderate" | "hard";
  status: OutcomeStatus;
}

export const outcomeLinkRelationships = [
  "depends_on",
  "enables",
  "contributes_to",
  "conflicts_with",
  "degrades",
  "proves",
  "supersedes",
  "retains",
] as const;

export type OutcomeLinkRelationship = (typeof outcomeLinkRelationships)[number];
