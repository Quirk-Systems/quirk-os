import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const migrationPath = resolve(process.cwd(), "../../supabase/migrations/20260821090000_quirk_beauty_taste_engine_candidate.sql");
const sql = readFileSync(migrationPath, "utf8");

test("authenticated clients cannot manufacture lifecycle approval", () => {
  assert.doesNotMatch(sql, /grant\s+update\s*\([^)]*state[^)]*\)\s+on\s+beauty\.taste_sessions\s+to\s+authenticated/i);
  assert.doesNotMatch(sql, /create\s+policy\s+taste_sessions_update_own/i);
  assert.doesNotMatch(sql, /grant\s+select\s*,\s*insert\s+on\s+beauty\.taste_sessions\s+to\s+authenticated/i);
  assert.match(sql, /grant\s+insert\s*\(\s*actor_id\s*,\s*purpose\s*,\s*context\s*\)\s+on\s+beauty\.taste_sessions\s+to\s+authenticated/i);
  assert.match(sql, /state\s*=\s*'purpose_declared'/i);
});

test("all semantic references are bound to actor, purpose, and session", () => {
  for (const marker of ["taste_options_session_actor_purpose_fkey","taste_choices_session_actor_purpose_fkey","preference_evidence_choice_scope_fkey","recommendation_options_scope_fkey","recommendation_evidence_recommendation_scope_fkey","recommendation_evidence_evidence_scope_fkey","outcomes_recommendation_scope_fkey","proposals_outcome_scope_fkey","decisions_proposal_scope_fkey","receipts_decision_scope_fkey"]) assert.match(sql, new RegExp(marker));
});

test("choice option keys are database-validated", () => {
  assert.match(sql, /validate_taste_choice_options/i);
  assert.match(sql, /selected_option_key\s*=\s*any\s*\(presented_option_keys\)/i);
  assert.match(sql, /count\s*\(\s*distinct\s+presented_key\s*\)/i);
});

test("recommendation evidence is relational rather than an unenforced uuid array", () => {
  assert.match(sql, /create\s+table\s+if\s+not\s+exists\s+beauty\.recommendation_evidence_links/i);
  assert.doesNotMatch(sql, /evidence_ids\s+uuid\[\]/i);
});

test("server writer access is explicit and anonymous access remains absent", () => {
  assert.match(sql, /grant\s+usage\s+on\s+schema\s+beauty\s+to\s+service_role/i);
  assert.match(sql, /grant\s+select\s*,\s*insert\s+on\s+beauty\.preference_evidence\s+to\s+service_role/i);
  assert.match(sql, /revoke\s+all\s+on\s+all\s+tables\s+in\s+schema\s+beauty\s+from\s+anon/i);
  assert.doesNotMatch(sql, /grant\s+(?:select\s*,\s*)?insert\s+on\s+beauty\.(?:preference_evidence|recommendations|graph_update_proposals|graph_update_decision_mirrors|graph_update_receipt_mirrors)\s+to\s+authenticated/i);
});

test("human decisions expire, receipts require an approved live decision, and updates stay non-automatic", () => {
  assert.match(sql, /check\s*\(expires_at\s*>\s*decided_at\)/i);
  assert.match(sql, /validate_graph_update_receipt/i);
  assert.match(sql, /v_decision\s*<>\s*'approve'/i);
  assert.match(sql, /auto_apply\s+boolean\s+not\s+null\s+default\s+false\s+check\s*\(auto_apply\s*=\s*false\)/i);
});
