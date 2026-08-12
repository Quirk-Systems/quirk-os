/**
 * Quirk Sync Control Plane — canonical projection types
 * Mapping version: sync-control-plane.v1.1.0
 * Source: mappings/sync-control-plane.v1.yaml
 *
 * These types represent the canonical (GitHub/Canon) side of the mapping
 * contract.  Supabase runtime rows use the column names described in the
 * mapping YAML; they must never appear in documents that cross the canonical
 * boundary.
 *
 * Vendor IDs are bindings.  They are never Quirk identity.
 */

// ---------------------------------------------------------------------------
// Source Binding  (schema: source-binding.v2)
// ---------------------------------------------------------------------------

export type BindingPlatform =
  | "github"
  | "supabase"
  | "google_drive"
  | "airtable"
  | "notion"
  | "vercel"
  | "cloudflare";

export type AuthorityClass = "canonical" | "runtime" | "work" | "projection";

export type SyncDirection =
  | "pull"
  | "push"
  | "bidirectional_proposal"
  | "projection_only"
  | "none";

export type BindingState =
  | "discovered"
  | "candidate"
  | "active"
  | "deferred"
  | "drifted"
  | "paused"
  | "error"
  | "retired";

export type FreshnessStatus =
  | "unknown"
  | "fresh"
  | "aging"
  | "stale"
  | "expired";

export interface Freshness {
  status: FreshnessStatus;
  last_verified_at?: string | null;
  max_age_days?: number | null;
  evaluated_at?: string | null;
  reason?: string | null;
}

export interface SourceBinding {
  schema_version: "source-binding.v2";
  /** Stable Quirk binding identifier.  Pattern: binding.<platform>.<slug> */
  binding_id: string;
  /** Stable Quirk object key.  Never a runtime UUID. */
  object_key: string;
  platform: BindingPlatform;
  /** Vendor-assigned identifier stored as a binding, not Quirk identity. */
  external_id: string;
  external_url?: string | null;
  authority_class: AuthorityClass;
  sync_direction: SyncDirection;
  state: BindingState;
  canonical_uri?: string | null;
  /** SHA-256 hex digest of the last observed content. */
  content_hash?: string | null;
  last_seen_at?: string | null;
  last_synced_at?: string | null;
  freshness: Freshness;
  cursor?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Sync Run Receipt  (schema: sync-run-receipt.v2)
// ---------------------------------------------------------------------------

export type RunType =
  | "discover"
  | "pull"
  | "push"
  | "reconcile"
  | "project"
  | "validate"
  | "backfill"
  | "rebuild"
  | "compensate";

export type ReceiptStatus =
  | "planned"
  | "running"
  | "succeeded"
  | "failed"
  | "blocked"
  | "cancelled"
  | "superseded";

export interface SyncRunReceipt {
  schema_version: "sync-run-receipt.v2";
  /** Stable Quirk receipt identifier.  Pattern: receipt.<slug> */
  receipt_id: string;
  idempotency_key: string;
  run_type: RunType;
  status: ReceiptStatus;
  /** Always true — receipts are append-only. */
  immutable: true;
  actor_ref?: string | null;
  authority_ref?: string | null;
  agent_ref?: string | null;
  skill_ref?: string | null;
  manifest_version?: string | null;
  trace_id?: string | null;
  started_at: string;
  completed_at?: string | null;
  input_refs: string[];
  output_refs: string[];
  evidence_refs: string[];
  metrics?: Record<string, number | string | boolean | null>;
  error?: Record<string, unknown> | null;
  proposed_move_ref?: string | null;
  content_hashes?: Record<string, string>;
  receipt_hash?: string | null;
  /** Points to the receipt this one supersedes.  Pattern: receipt.<slug> */
  supersedes_receipt_id?: string | null;
  correction_reason?: string | null;
  outcome?: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Projection Envelope  (schema: projection-envelope.v1)
// ---------------------------------------------------------------------------

export interface ProjectionEnvelope {
  schema_version: "projection-envelope.v1";
  /** Stable Quirk object key.  Never a runtime UUID. */
  object_key: string;
  kind: string;
  canonical_uri?: string | null;
  canonical_version?: string | null;
  /** SHA-256 hex digest of the canonical payload. */
  content_hash?: string | null;
  authority_class: "projection";
  projection: Record<string, unknown>;
  source_bindings: SourceBinding[];
  generated_at: string;
  generator_ref: string;
}
