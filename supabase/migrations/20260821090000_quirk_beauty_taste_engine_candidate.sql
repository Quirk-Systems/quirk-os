-- Quirk Beauty Taste Engine v0.1 candidate projection. Canon and authority remain external.
create extension if not exists pgcrypto;
create schema if not exists beauty;
revoke all on schema beauty from public, anon;
grant usage on schema beauty to authenticated;
grant usage on schema beauty to service_role;

create table if not exists beauty.taste_sessions (
 id uuid primary key default gen_random_uuid(), actor_id uuid not null references auth.users(id) on delete cascade,
 purpose text not null check(length(purpose) between 1 and 120), context jsonb not null default '{}'::jsonb check(jsonb_typeof(context)='object'),
 state text not null default 'purpose_declared' check(state in ('purpose_declared','choice_recorded','evidence_reviewed','recommendation_proposed','outcome_recorded','graph_update_proposed','approved','revised','rejected','expired','receipted','abandoned')),
 created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
 constraint taste_sessions_scope_key unique(id,actor_id,purpose)
);
create table if not exists beauty.taste_options (
 id uuid primary key default gen_random_uuid(), session_id uuid not null, actor_id uuid not null references auth.users(id) on delete cascade, purpose text not null,
 option_key text not null check(length(option_key) between 1 and 160), label text not null check(length(label) between 1 and 240),
 attributes jsonb not null check(jsonb_typeof(attributes)='object'), truth_status text not null default 'candidate' check(truth_status='candidate'), created_at timestamptz not null default now(),
 constraint taste_options_session_actor_purpose_fkey foreign key(session_id,actor_id,purpose) references beauty.taste_sessions(id,actor_id,purpose) on delete cascade,
 constraint taste_options_scope_key unique(session_id,actor_id,purpose,option_key)
);
create table if not exists beauty.taste_choices (
 id uuid primary key default gen_random_uuid(), session_id uuid not null, actor_id uuid not null references auth.users(id) on delete cascade, purpose text not null,
 presented_option_keys text[] not null check(cardinality(presented_option_keys)>=2 and array_position(presented_option_keys,null) is null),
 selected_option_key text, abstained boolean not null default false, source_type text not null default 'explicit_human_choice' check(source_type='explicit_human_choice'),
 captured_at timestamptz not null default now(), created_at timestamptz not null default now(),
 constraint taste_choices_session_actor_purpose_fkey foreign key(session_id,actor_id,purpose) references beauty.taste_sessions(id,actor_id,purpose) on delete cascade,
 constraint taste_choices_selection_check check((abstained and selected_option_key is null) or (not abstained and selected_option_key is not null and selected_option_key = any (presented_option_keys))),
 constraint taste_choices_scope_key unique(id,session_id,actor_id,purpose)
);
create or replace function beauty.validate_taste_choice_options() returns trigger language plpgsql set search_path=pg_catalog,beauty as $$
declare v_distinct_count integer; v_owned_count integer;
begin
 select count(distinct presented_key) into v_distinct_count from unnest(new.presented_option_keys) as presented_key;
 if v_distinct_count <> cardinality(new.presented_option_keys) then raise exception using errcode='23514',message='presented option keys must be unique'; end if;
 select count(*) into v_owned_count from beauty.taste_options o where o.session_id=new.session_id and o.actor_id=new.actor_id and o.purpose=new.purpose and o.option_key=any(new.presented_option_keys);
 if v_owned_count <> cardinality(new.presented_option_keys) then raise exception using errcode='23514',message='presented options must share actor, purpose, and session'; end if;
 return new;
end $$;
revoke all on function beauty.validate_taste_choice_options() from public, anon;
grant execute on function beauty.validate_taste_choice_options() to authenticated, service_role;
drop trigger if exists taste_choices_validate_options on beauty.taste_choices;
create trigger taste_choices_validate_options before insert or update of session_id,actor_id,purpose,presented_option_keys,selected_option_key,abstained on beauty.taste_choices for each row execute function beauty.validate_taste_choice_options();

create table if not exists beauty.preference_evidence (
 id uuid primary key default gen_random_uuid(), session_id uuid not null, actor_id uuid not null references auth.users(id) on delete cascade, purpose text not null,
 context_id text not null, preferred_feature text not null, contrasted_feature text not null, source_choice_id uuid not null,
 source_type text not null default 'explicit_human_choice' check(source_type='explicit_human_choice'), weight numeric(10,6) not null check(weight between 0 and 1), confidence numeric(4,3) not null check(confidence between 0 and 1),
 truth_status text not null default 'candidate' check(truth_status='candidate'), recorded_at timestamptz not null default now(), created_at timestamptz not null default now(),
 constraint preference_evidence_session_scope_fkey foreign key(session_id,actor_id,purpose) references beauty.taste_sessions(id,actor_id,purpose) on delete cascade,
 constraint preference_evidence_choice_scope_fkey foreign key(source_choice_id,session_id,actor_id,purpose) references beauty.taste_choices(id,session_id,actor_id,purpose) on delete restrict,
 constraint preference_evidence_scope_key unique(id,session_id,actor_id,purpose)
);
create table if not exists beauty.recommendations (
 id uuid primary key default gen_random_uuid(), session_id uuid not null, actor_id uuid not null references auth.users(id) on delete cascade, purpose text not null, option_key text not null,
 score numeric(12,6) not null, confidence numeric(4,3) not null check(confidence between 0 and 1), factors jsonb not null check(jsonb_typeof(factors)='array'), insufficient_evidence boolean not null,
 status text not null default 'candidate' check(status='candidate'), generated_at timestamptz not null default now(), expires_at timestamptz not null, created_at timestamptz not null default now(),
 constraint recommendation_session_scope_fkey foreign key(session_id,actor_id,purpose) references beauty.taste_sessions(id,actor_id,purpose) on delete cascade,
 constraint recommendation_options_scope_fkey foreign key(session_id,actor_id,purpose,option_key) references beauty.taste_options(session_id,actor_id,purpose,option_key) on delete restrict,
 constraint recommendations_expiry_check check(expires_at>generated_at), constraint recommendations_scope_key unique(id,session_id,actor_id,purpose),
 constraint recommendations_option_scope_key unique(id,session_id,actor_id,purpose,option_key)
);
create table if not exists beauty.recommendation_evidence_links (
 recommendation_id uuid not null, evidence_id uuid not null, session_id uuid not null, actor_id uuid not null references auth.users(id) on delete cascade, purpose text not null, created_at timestamptz not null default now(),
 primary key(recommendation_id,evidence_id),
 constraint recommendation_evidence_recommendation_scope_fkey foreign key(recommendation_id,session_id,actor_id,purpose) references beauty.recommendations(id,session_id,actor_id,purpose) on delete cascade,
 constraint recommendation_evidence_evidence_scope_fkey foreign key(evidence_id,session_id,actor_id,purpose) references beauty.preference_evidence(id,session_id,actor_id,purpose) on delete restrict
);
create table if not exists beauty.outcome_observations (
 id uuid primary key default gen_random_uuid(), session_id uuid not null, actor_id uuid not null references auth.users(id) on delete cascade, purpose text not null,
 recommendation_id uuid not null, option_key text not null, outcome_kind text not null check(outcome_kind in ('preferred','rejected','mixed','not_tested')),
 explicit boolean not null default true check(explicit=true), tested_in_real_world boolean not null, source_type text not null default 'explicit_human_report' check(source_type='explicit_human_report'), note text not null default '',
 observed_at timestamptz not null default now(), created_at timestamptz not null default now(),
 constraint outcomes_session_scope_fkey foreign key(session_id,actor_id,purpose) references beauty.taste_sessions(id,actor_id,purpose) on delete cascade,
 constraint outcomes_recommendation_scope_fkey foreign key(recommendation_id,session_id,actor_id,purpose,option_key) references beauty.recommendations(id,session_id,actor_id,purpose,option_key) on delete restrict,
 constraint outcomes_test_check check((outcome_kind='not_tested' and tested_in_real_world=false) or (outcome_kind<>'not_tested' and tested_in_real_world=true)),
 constraint outcomes_scope_key unique(id,session_id,actor_id,purpose)
);
create table if not exists beauty.graph_update_proposals (
 id uuid primary key default gen_random_uuid(), session_id uuid not null, actor_id uuid not null references auth.users(id) on delete cascade, purpose text not null,
 recommendation_id uuid not null, outcome_id uuid not null, expected_graph_revision bigint not null check(expected_graph_revision>=0), deltas jsonb not null check(jsonb_typeof(deltas)='array' and jsonb_array_length(deltas)>0),
 auto_apply boolean not null default false check (auto_apply = false), truth_status text not null default 'candidate' check(truth_status='candidate'), proposed_at timestamptz not null default now(), expires_at timestamptz not null, created_at timestamptz not null default now(),
 constraint proposals_session_scope_fkey foreign key(session_id,actor_id,purpose) references beauty.taste_sessions(id,actor_id,purpose) on delete cascade,
 constraint proposals_recommendation_scope_fkey foreign key(recommendation_id,session_id,actor_id,purpose) references beauty.recommendations(id,session_id,actor_id,purpose) on delete restrict,
 constraint proposals_outcome_scope_fkey foreign key(outcome_id,session_id,actor_id,purpose) references beauty.outcome_observations(id,session_id,actor_id,purpose) on delete restrict,
 constraint proposals_expiry_check check(expires_at>proposed_at), constraint proposals_scope_key unique(id,session_id,actor_id,purpose)
);
create table if not exists beauty.graph_update_decision_mirrors (
 id uuid primary key default gen_random_uuid(), session_id uuid not null, actor_id uuid not null references auth.users(id) on delete cascade, purpose text not null, proposal_id uuid not null,
 decision text not null check(decision in ('approve','revise','reject')), human_confirmed boolean not null check(human_confirmed=true), reason text not null, corrections jsonb not null default '[]'::jsonb check(jsonb_typeof(corrections)='array'),
 core_decision_ref text not null unique, decided_at timestamptz not null, expires_at timestamptz not null check (expires_at > decided_at), created_at timestamptz not null default now(),
 constraint decisions_session_scope_fkey foreign key(session_id,actor_id,purpose) references beauty.taste_sessions(id,actor_id,purpose) on delete cascade,
 constraint decisions_proposal_scope_fkey foreign key(proposal_id,session_id,actor_id,purpose) references beauty.graph_update_proposals(id,session_id,actor_id,purpose) on delete restrict,
 constraint decisions_scope_key unique(id,proposal_id,session_id,actor_id,purpose)
);
create table if not exists beauty.graph_update_receipt_mirrors (
 id uuid primary key default gen_random_uuid(), session_id uuid not null, actor_id uuid not null references auth.users(id) on delete cascade, purpose text not null, proposal_id uuid not null, decision_mirror_id uuid not null,
 core_receipt_ref text not null unique, before_revision bigint not null check(before_revision>=0), after_revision bigint not null check(after_revision=before_revision+1), action_digest text not null check(action_digest ~ '^sha256:[a-f0-9]{64}$'),
 receipt_envelope jsonb not null check(jsonb_typeof(receipt_envelope)='object'), applied_at timestamptz not null, created_at timestamptz not null default now(),
 constraint receipts_session_scope_fkey foreign key(session_id,actor_id,purpose) references beauty.taste_sessions(id,actor_id,purpose) on delete cascade,
 constraint receipts_proposal_scope_fkey foreign key(proposal_id,session_id,actor_id,purpose) references beauty.graph_update_proposals(id,session_id,actor_id,purpose) on delete restrict,
 constraint receipts_decision_scope_fkey foreign key(decision_mirror_id,proposal_id,session_id,actor_id,purpose) references beauty.graph_update_decision_mirrors(id,proposal_id,session_id,actor_id,purpose) on delete restrict,
 constraint receipts_one_per_proposal_key unique(proposal_id)
);
create or replace function beauty.validate_graph_update_receipt() returns trigger language plpgsql set search_path=pg_catalog,beauty as $$
declare v_decision text; v_human_confirmed boolean; v_expires_at timestamptz;
begin
 select decision,human_confirmed,expires_at into v_decision,v_human_confirmed,v_expires_at from beauty.graph_update_decision_mirrors where id=new.decision_mirror_id and proposal_id=new.proposal_id and session_id=new.session_id and actor_id=new.actor_id and purpose=new.purpose;
 if not found then raise exception using errcode='23503',message='receipt decision scope does not exist'; end if;
 if v_decision <> 'approve' or v_human_confirmed is not true then raise exception using errcode='23514',message='receipt requires a human-confirmed approve decision'; end if;
 if new.applied_at>v_expires_at then raise exception using errcode='23514',message='receipt cannot apply an expired decision'; end if;
 return new;
end $$;
revoke all on function beauty.validate_graph_update_receipt() from public, anon;
grant execute on function beauty.validate_graph_update_receipt() to service_role;
drop trigger if exists graph_update_receipts_validate_decision on beauty.graph_update_receipt_mirrors;
create trigger graph_update_receipts_validate_decision before insert or update of session_id,actor_id,purpose,proposal_id,decision_mirror_id,applied_at on beauty.graph_update_receipt_mirrors for each row execute function beauty.validate_graph_update_receipt();

alter table beauty.taste_sessions enable row level security; alter table beauty.taste_options enable row level security; alter table beauty.taste_choices enable row level security;
alter table beauty.preference_evidence enable row level security; alter table beauty.recommendations enable row level security; alter table beauty.recommendation_evidence_links enable row level security;
alter table beauty.outcome_observations enable row level security; alter table beauty.graph_update_proposals enable row level security; alter table beauty.graph_update_decision_mirrors enable row level security; alter table beauty.graph_update_receipt_mirrors enable row level security;
revoke all on all tables in schema beauty from public; revoke all on all tables in schema beauty from anon; revoke all on all tables in schema beauty from authenticated; revoke all on all tables in schema beauty from service_role;

grant select on beauty.taste_sessions to authenticated;
grant insert (actor_id, purpose, context) on beauty.taste_sessions to authenticated;
grant select on beauty.taste_options,beauty.taste_choices,beauty.preference_evidence,beauty.recommendations,beauty.recommendation_evidence_links,beauty.outcome_observations,beauty.graph_update_proposals,beauty.graph_update_decision_mirrors,beauty.graph_update_receipt_mirrors to authenticated;
grant insert (session_id,actor_id,purpose,presented_option_keys,selected_option_key,abstained) on beauty.taste_choices to authenticated;
grant insert (session_id,actor_id,purpose,recommendation_id,option_key,outcome_kind,tested_in_real_world,note) on beauty.outcome_observations to authenticated;

grant select, insert, update on beauty.taste_sessions to service_role;
grant select, insert on beauty.taste_options to service_role; grant select, insert on beauty.taste_choices to service_role;
grant select, insert on beauty.preference_evidence to service_role; grant select, insert on beauty.recommendations to service_role;
grant select, insert on beauty.recommendation_evidence_links to service_role; grant select, insert on beauty.outcome_observations to service_role;
grant select, insert on beauty.graph_update_proposals to service_role; grant select, insert on beauty.graph_update_decision_mirrors to service_role; grant select, insert on beauty.graph_update_receipt_mirrors to service_role;

create policy taste_sessions_select_own on beauty.taste_sessions for select to authenticated using((select auth.uid())=actor_id);
create policy taste_sessions_insert_own on beauty.taste_sessions for insert to authenticated with check((select auth.uid())=actor_id and state = 'purpose_declared');
create policy taste_options_select_own on beauty.taste_options for select to authenticated using((select auth.uid())=actor_id);
create policy taste_choices_select_own on beauty.taste_choices for select to authenticated using((select auth.uid())=actor_id);
create policy taste_choices_insert_own on beauty.taste_choices for insert to authenticated with check((select auth.uid())=actor_id);
create policy preference_evidence_select_own on beauty.preference_evidence for select to authenticated using((select auth.uid())=actor_id);
create policy recommendations_select_own on beauty.recommendations for select to authenticated using((select auth.uid())=actor_id);
create policy recommendation_evidence_select_own on beauty.recommendation_evidence_links for select to authenticated using((select auth.uid())=actor_id);
create policy outcome_observations_select_own on beauty.outcome_observations for select to authenticated using((select auth.uid())=actor_id);
create policy outcome_observations_insert_own on beauty.outcome_observations for insert to authenticated with check((select auth.uid())=actor_id);
create policy graph_update_proposals_select_own on beauty.graph_update_proposals for select to authenticated using((select auth.uid())=actor_id);
create policy graph_update_decisions_select_own on beauty.graph_update_decision_mirrors for select to authenticated using((select auth.uid())=actor_id);
create policy graph_update_receipts_select_own on beauty.graph_update_receipt_mirrors for select to authenticated using((select auth.uid())=actor_id);

comment on schema beauty is 'Candidate Quirk Beauty Taste Engine projection; not canon and not automatically exposed through the Data API.';
