-- Quirk Beauty Taste Engine v0.1.1 candidate private projection.
-- Git canon remains authoritative. This migration cannot admit canon, grant runtime,
-- issue Human Gate decisions, or mutate the generic Preference Graph.

begin;

create extension if not exists pgcrypto;
create schema if not exists quirk_beauty_private;

revoke all on schema quirk_beauty_private from public, anon, authenticated;
grant usage on schema quirk_beauty_private to authenticated, service_role;

alter default privileges in schema quirk_beauty_private revoke all on tables from public, anon, authenticated;
alter default privileges in schema quirk_beauty_private revoke all on sequences from public, anon, authenticated;
alter default privileges in schema quirk_beauty_private revoke execute on functions from public, anon, authenticated;

create table if not exists quirk_beauty_private.taste_sessions (
  id uuid primary key default gen_random_uuid(),
  actor_id uuid not null references auth.users(id) on delete cascade,
  purpose text not null check (length(purpose) between 1 and 120),
  context jsonb not null default '{}'::jsonb check (jsonb_typeof(context) = 'object'),
  state text not null default 'purpose_declared' check (state in (
    'purpose_declared', 'choice_recorded', 'evidence_reviewed',
    'recommendation_proposed', 'outcome_recorded', 'graph_update_proposed',
    'approved', 'revised', 'rejected', 'expired', 'receipted', 'abandoned'
  )),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (id, actor_id, purpose)
);

create table if not exists quirk_beauty_private.taste_options (
  id text primary key check (length(id) between 1 and 240),
  session_id uuid not null,
  actor_id uuid not null,
  purpose text not null,
  option_key text not null check (length(option_key) between 1 and 240),
  label text not null check (length(label) between 1 and 300),
  attributes jsonb not null check (jsonb_typeof(attributes) = 'object' and attributes <> '{}'::jsonb),
  truth_status text not null default 'candidate' check (truth_status = 'candidate'),
  created_at timestamptz not null default now(),
  unique (session_id, option_key),
  unique (id, session_id, actor_id, purpose, option_key),
  foreign key (session_id, actor_id, purpose)
    references quirk_beauty_private.taste_sessions(id, actor_id, purpose)
    on delete cascade
);

create table if not exists quirk_beauty_private.taste_choices (
  id text primary key check (id ~ '^choice:'),
  session_id uuid not null,
  actor_id uuid not null,
  purpose text not null,
  context_id text not null check (length(context_id) between 1 and 240),
  presented_option_keys text[] not null check (cardinality(presented_option_keys) >= 2),
  selected_option_key text,
  abstained boolean not null default false,
  source_type text not null check (source_type = 'explicit_human_choice'),
  captured_at timestamptz not null,
  created_at timestamptz not null default now(),
  unique (id, session_id, actor_id, purpose),
  foreign key (session_id, actor_id, purpose)
    references quirk_beauty_private.taste_sessions(id, actor_id, purpose)
    on delete cascade,
  check ((abstained and selected_option_key is null) or (not abstained and selected_option_key = any(presented_option_keys)))
);

create table if not exists quirk_beauty_private.preference_evidence (
  id text primary key check (id ~ '^evidence:'),
  session_id uuid not null,
  actor_id uuid not null,
  purpose text not null,
  context_id text not null,
  preferred_feature text not null check (preferred_feature ~ '^[^=]+=.+'),
  contrasted_feature text not null check (contrasted_feature ~ '^[^=]+=.+'),
  source_choice_id text not null,
  source_type text not null check (source_type = 'explicit_human_choice'),
  weight numeric(10,6) not null check (weight > 0 and weight <= 1),
  confidence numeric(4,3) not null check (confidence between 0 and 1),
  truth_status text not null default 'candidate' check (truth_status = 'candidate'),
  recorded_at timestamptz not null,
  created_at timestamptz not null default now(),
  unique (id, session_id, actor_id, purpose),
  foreign key (source_choice_id, session_id, actor_id, purpose)
    references quirk_beauty_private.taste_choices(id, session_id, actor_id, purpose)
    on delete restrict
);

create table if not exists quirk_beauty_private.recommendations (
  id text primary key check (id ~ '^recommendation:'),
  session_id uuid not null,
  actor_id uuid not null,
  purpose text not null,
  option_key text not null,
  score numeric(12,6) not null,
  confidence numeric(4,3) not null check (confidence between 0 and 1),
  evidence_ids text[] not null default '{}',
  factors jsonb not null check (jsonb_typeof(factors) = 'array'),
  insufficient_evidence boolean not null,
  status text not null default 'candidate' check (status = 'candidate'),
  generated_at timestamptz not null,
  expires_at timestamptz not null,
  created_at timestamptz not null default now(),
  unique (id, session_id, actor_id, purpose, option_key),
  foreign key (session_id, actor_id, purpose)
    references quirk_beauty_private.taste_sessions(id, actor_id, purpose)
    on delete cascade,
  check (expires_at > generated_at)
);

create table if not exists quirk_beauty_private.outcome_observations (
  id text primary key check (id ~ '^outcome:'),
  session_id uuid not null,
  actor_id uuid not null,
  purpose text not null,
  recommendation_id text not null,
  option_key text not null,
  outcome_kind text not null check (outcome_kind in ('preferred', 'rejected', 'mixed', 'not_tested')),
  explicit boolean not null check (explicit = true),
  tested_in_real_world boolean not null,
  source_type text not null check (source_type = 'explicit_human_report'),
  note text not null default '',
  observed_at timestamptz not null,
  created_at timestamptz not null default now(),
  unique (id, session_id, actor_id, purpose, recommendation_id),
  foreign key (recommendation_id, session_id, actor_id, purpose, option_key)
    references quirk_beauty_private.recommendations(id, session_id, actor_id, purpose, option_key)
    on delete restrict,
  check ((outcome_kind = 'not_tested' and tested_in_real_world = false) or (outcome_kind <> 'not_tested' and tested_in_real_world = true))
);

create table if not exists quirk_beauty_private.graph_update_proposals (
  id text primary key check (id ~ '^graph-update-proposal:'),
  session_id uuid not null,
  actor_id uuid not null,
  purpose text not null,
  expected_graph_revision bigint not null check (expected_graph_revision >= 0),
  recommendation_id text not null,
  outcome_id text not null,
  deltas jsonb not null check (jsonb_typeof(deltas) = 'array' and jsonb_array_length(deltas) > 0),
  requires_revision boolean not null default false,
  auto_apply boolean not null default false check (auto_apply = false),
  truth_status text not null default 'candidate' check (truth_status = 'candidate'),
  proposed_at timestamptz not null,
  expires_at timestamptz not null,
  created_at timestamptz not null default now(),
  unique (id, session_id, actor_id, purpose),
  foreign key (outcome_id, session_id, actor_id, purpose, recommendation_id)
    references quirk_beauty_private.outcome_observations(id, session_id, actor_id, purpose, recommendation_id)
    on delete restrict,
  check (expires_at > proposed_at)
);

-- Read-only mirrors. Beauty does not issue authority or core receipts.
create table if not exists quirk_beauty_private.graph_update_decision_mirrors (
  core_decision_ref text primary key,
  session_id uuid not null,
  actor_id uuid not null,
  purpose text not null,
  proposal_id text not null,
  decision text not null check (decision in ('approve', 'revise', 'reject')),
  human_confirmed boolean not null check (human_confirmed = true),
  decision_envelope jsonb not null check (jsonb_typeof(decision_envelope) = 'object'),
  decided_at timestamptz not null,
  expires_at timestamptz not null,
  created_at timestamptz not null default now(),
  unique (core_decision_ref, proposal_id, session_id, actor_id, purpose),
  foreign key (proposal_id, session_id, actor_id, purpose)
    references quirk_beauty_private.graph_update_proposals(id, session_id, actor_id, purpose)
    on delete restrict
);

create table if not exists quirk_beauty_private.graph_update_receipt_mirrors (
  core_receipt_ref text primary key,
  session_id uuid not null,
  actor_id uuid not null,
  purpose text not null,
  proposal_id text not null,
  core_decision_ref text not null,
  before_revision bigint not null check (before_revision >= 0),
  after_revision bigint not null check (after_revision = before_revision + 1),
  action_digest text not null check (action_digest ~ '^sha256:[a-f0-9]{64}$'),
  core_key_id text not null,
  core_signature text not null check (length(core_signature) >= 80),
  core_verification_ref text not null unique,
  receipt_envelope jsonb not null check (jsonb_typeof(receipt_envelope) = 'object'),
  applied_at timestamptz not null,
  created_at timestamptz not null default now(),
  foreign key (core_decision_ref, proposal_id, session_id, actor_id, purpose)
    references quirk_beauty_private.graph_update_decision_mirrors(core_decision_ref, proposal_id, session_id, actor_id, purpose)
    on delete restrict
);

create index if not exists taste_sessions_actor_purpose_idx on quirk_beauty_private.taste_sessions(actor_id, purpose, created_at desc);
create index if not exists choices_session_time_idx on quirk_beauty_private.taste_choices(session_id, captured_at);
create index if not exists evidence_actor_purpose_idx on quirk_beauty_private.preference_evidence(actor_id, purpose, recorded_at);
create index if not exists recommendations_actor_purpose_idx on quirk_beauty_private.recommendations(actor_id, purpose, generated_at desc);
create index if not exists outcomes_actor_purpose_idx on quirk_beauty_private.outcome_observations(actor_id, purpose, observed_at desc);
create index if not exists proposals_actor_purpose_idx on quirk_beauty_private.graph_update_proposals(actor_id, purpose, proposed_at desc);

alter table quirk_beauty_private.taste_sessions enable row level security;
alter table quirk_beauty_private.taste_options enable row level security;
alter table quirk_beauty_private.taste_choices enable row level security;
alter table quirk_beauty_private.preference_evidence enable row level security;
alter table quirk_beauty_private.recommendations enable row level security;
alter table quirk_beauty_private.outcome_observations enable row level security;
alter table quirk_beauty_private.graph_update_proposals enable row level security;
alter table quirk_beauty_private.graph_update_decision_mirrors enable row level security;
alter table quirk_beauty_private.graph_update_receipt_mirrors enable row level security;

alter table quirk_beauty_private.taste_sessions force row level security;
alter table quirk_beauty_private.taste_options force row level security;
alter table quirk_beauty_private.taste_choices force row level security;
alter table quirk_beauty_private.preference_evidence force row level security;
alter table quirk_beauty_private.recommendations force row level security;
alter table quirk_beauty_private.outcome_observations force row level security;
alter table quirk_beauty_private.graph_update_proposals force row level security;
alter table quirk_beauty_private.graph_update_decision_mirrors force row level security;
alter table quirk_beauty_private.graph_update_receipt_mirrors force row level security;

revoke all on all tables in schema quirk_beauty_private from public, anon, authenticated;
grant select, insert on quirk_beauty_private.taste_sessions to authenticated;
grant select on quirk_beauty_private.taste_options to authenticated;
grant select, insert on quirk_beauty_private.taste_choices to authenticated;
grant select on quirk_beauty_private.preference_evidence to authenticated;
grant select on quirk_beauty_private.recommendations to authenticated;
grant select, insert on quirk_beauty_private.outcome_observations to authenticated;
grant select on quirk_beauty_private.graph_update_proposals to authenticated;
grant select on quirk_beauty_private.graph_update_decision_mirrors to authenticated;
grant select on quirk_beauty_private.graph_update_receipt_mirrors to authenticated;
grant all on all tables in schema quirk_beauty_private to service_role;

create policy taste_sessions_select_own on quirk_beauty_private.taste_sessions for select to authenticated using ((select auth.uid()) = actor_id);
create policy taste_sessions_insert_own on quirk_beauty_private.taste_sessions for insert to authenticated with check ((select auth.uid()) = actor_id and state = 'purpose_declared');
create policy taste_options_select_own on quirk_beauty_private.taste_options for select to authenticated using ((select auth.uid()) = actor_id);
create policy taste_choices_select_own on quirk_beauty_private.taste_choices for select to authenticated using ((select auth.uid()) = actor_id);
create policy taste_choices_insert_own on quirk_beauty_private.taste_choices for insert to authenticated with check ((select auth.uid()) = actor_id);
create policy preference_evidence_select_own on quirk_beauty_private.preference_evidence for select to authenticated using ((select auth.uid()) = actor_id);
create policy recommendations_select_own on quirk_beauty_private.recommendations for select to authenticated using ((select auth.uid()) = actor_id);
create policy outcomes_select_own on quirk_beauty_private.outcome_observations for select to authenticated using ((select auth.uid()) = actor_id);
create policy outcomes_insert_own on quirk_beauty_private.outcome_observations for insert to authenticated with check ((select auth.uid()) = actor_id);
create policy proposals_select_own on quirk_beauty_private.graph_update_proposals for select to authenticated using ((select auth.uid()) = actor_id);
create policy decisions_select_own on quirk_beauty_private.graph_update_decision_mirrors for select to authenticated using ((select auth.uid()) = actor_id);
create policy receipts_select_own on quirk_beauty_private.graph_update_receipt_mirrors for select to authenticated using ((select auth.uid()) = actor_id);

comment on schema quirk_beauty_private is 'Candidate private projection for Quirk Beauty Taste Engine v0.1.1; not canonical and not exposed by default.';
comment on table quirk_beauty_private.graph_update_decision_mirrors is 'Read-only mirror of Human Gate decisions issued by Quirk core.';
comment on table quirk_beauty_private.graph_update_receipt_mirrors is 'Read-only mirror of immutable effect receipts issued by Quirk core.';

commit;
