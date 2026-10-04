-- Quirk Sync Control Plane: an activation needs an independent human approver.
--
-- `guard_manifest_activation` refused an activation only when the requester and
-- the approver were the same string. Naming any second agent as approver cleared
-- it, so a capability could activate itself at execute_protected with a
-- sibling's signature. Reproduced on PostgreSQL 16.13 against the migrations in
-- this directory before this file existed.
--
-- The rule mirrors `_is_independent_approver` in
-- scripts/sync_control_plane/policy.py and the principal pattern in
-- schemas/runtime-manifest.schema.json, narrowed to the human namespace:
-- `agent.` can never be independent, because capability never implies
-- authority, and `service.`/`system.` are refused rather than assumed, because
-- no allow-list of authorized service approvers exists. Add one and this
-- predicate and its Python twin are the two places it belongs.
--
-- The whole principal is matched, not its prefix, so a bare 'human.' naming
-- nobody is refused. There is no schema layer in front of the database.
--
-- What this does NOT establish: `approved_by` is still text the inserting
-- caller supplies, so 'human.fabricated' with arbitrary non-null decision and
-- grant references satisfies this predicate. The rule constrains which
-- principal may appear, not whether that principal approved anything. Proving
-- that needs an approval record the caller cannot author, which is a component
-- this repository does not have; see
-- docs/briefs/2026-10-03-approval-attestation.md.
--
-- Three further repairs to the same rules, all of them cases where this trigger
-- was weaker than its Python twin rather than equal to it. Reproduced on
-- PostgreSQL 16.13 against the previous function, each one inserted and
-- observed to land as `active`:
--
--   * `rights_review` with `outcome` and `privacy_review` absent passed the
--     data_productization guard. `agent.rights-bypass` was accepted.
--   * a multi-skill orchestrator whose `trigger_contract` omitted
--     `collision_behavior` passed the fail-closed routing guard.
--     `orchestrator.collision-bypass` was accepted.
--   * `requested_by` had no shape check at all, so `'NOT-A-PRINCIPAL'` was
--     accepted. The JSON schema constrains that field for manifests that
--     arrive as documents; nothing constrained the column.
--
-- The first two are one bug twice: `->>` on a missing key yields NULL, and
-- `NULL <> 'approved'` is NULL rather than true, so the OR chain evaluated to
-- NULL and the guard did not fire. Supplying a wrong value was refused;
-- omitting the key was not. `is distinct from` is NULL-safe and restores the
-- intent. The Python gate was already correct here, because `None ==
-- "approved"` is simply false, which is why only this surface was affected.
--
-- Deliberately unchanged: the `evaluated_content_hash` test below still
-- compares two columns of the same row, and nothing computes either from the
-- manifest body. That is a missing specification rather than a bug with a
-- patch; see docs/briefs/2026-10-03-manifest-content-hash-preimage.md, which
-- names the two decisions it needs first. The comparison is NULL-safe in
-- practice because both columns are NOT NULL on `manifest_registry`.
--
-- Structure: the rules live in ONE function, `manifest_activation_violation`,
-- which returns the refusal message or NULL. The trigger raises whatever it
-- returns, and the pre-install audit selects the rows for which it returns
-- non-NULL. An earlier draft of this migration hand-wrote the audit's predicate
-- separately, and when three more rules were added to the trigger the audit was
-- not extended with them, so a row already `active` with a well-formed human
-- approver but, say, an incomplete rights review passed an audit that claimed
-- to cover the replacement. Two copies of one rule set is the defect this whole
-- change is about; there is now one copy and two callers.

-- This file deliberately carries NO `begin;`/`commit;`. It needs a transaction
-- and it does not open one, because the runner already owns it: `supabase db
-- push` applies each migration inside a transaction, and an in-file `commit`
-- closes the runner's transaction rather than one of our own — which is how a
-- push reports success while leaving the migration unrecorded in the history
-- table. An earlier draft did carry the boundary, and applying it under a
-- wrapper showed exactly that: `WARNING: there is already a transaction in
-- progress`, then `WARNING: there is no transaction in progress` at the end.
--
-- The requirement is not left to documentation. `LOCK TABLE` is rejected
-- outside a transaction block — `ERROR: LOCK TABLE can only be used in
-- transaction blocks`, verified on PostgreSQL 16.13 — so a runner that
-- autocommits each statement fails on the next line instead of quietly
-- splitting the audit from the cutover. The engine enforces the contract this
-- file depends on.
--
-- The audit and the cutover must be atomic, and `EXCLUSIVE` blocks
-- INSERT/UPDATE/DELETE while still allowing plain SELECT. Without it a write
-- landing after the audit's SELECT but before the new function is visible would
-- be admitted by the old guard and then stay `active`, because a trigger never
-- revalidates a row it did not fire on.
--
-- The cost is that writes to manifest_registry block for the duration of one
-- count and two function definitions. That is the intended trade for a cutover
-- with no gap.
lock table quirk_sync.manifest_registry in exclusive mode;

create or replace function quirk_sync.manifest_activation_violation(m quirk_sync.manifest_registry)
returns text
language plpgsql
immutable
set search_path=pg_catalog,quirk_sync as $$
begin
  if m.status <> 'active' then return null; end if;
  if m.requested_status <> 'active' then return 'active manifest requires requested_status=active'; end if;
  if m.admission_decision_ref is null or m.authority_grant_ref is null or m.requested_by is null
    or m.approved_by is null or m.evaluated_content_hash is null or m.transition_evidence_ref is null or m.admitted_at is null
    then return 'active manifest requires independent admission evidence'; end if;
  if m.requested_by !~ '^(human|agent|service|system)\.[a-z0-9._-]+$'
    then return 'manifest requester must be a well-formed principal'; end if;
  if m.requested_by = m.approved_by then return 'manifest requester may not approve its own activation'; end if;
  if m.approved_by !~ '^human\.[a-z0-9._-]+$'
    then return 'activation requires approval by an independent human principal'; end if;
  if m.evaluated_content_hash <> m.content_hash then return 'evaluated content hash does not match manifest content hash'; end if;
  if jsonb_array_length(m.eval_refs) = 0 or jsonb_array_length(m.stop_conditions) = 0
    then return 'active manifest requires eval evidence and stop conditions'; end if;
  -- `is distinct from`, not `<>`: see the header. A missing JSON key yields
  -- NULL, and a NULL comparison would make the condition NULL rather than true.
  if m.manifest_kind = 'orchestrator' and jsonb_array_length(m.skill_refs) > 1 and
    (m.trigger_contract is null
     or m.trigger_contract->>'collision_behavior' is distinct from 'block'
     or nullif(m.trigger_contract->>'routing_policy','') is null)
    then return 'multi-skill orchestrator requires fail-closed trigger contract'; end if;
  if m.domains ? 'data_productization' and
    (m.rights_review is null
     or m.rights_review->>'outcome' is distinct from 'approved'
     or coalesce(m.rights_review->>'license_verified','false')::boolean is not true
     or m.rights_review->>'privacy_review' is distinct from 'approved'
     or coalesce(m.rights_review->>'provenance_complete','false')::boolean is not true)
    then return 'data productization requires approved rights, licensing, privacy, and provenance review'; end if;
  return null;
end $$;

-- Audited BEFORE the guard is replaced. Replacing the function only guards the
-- next write: rows admitted under the old rules stay `active` and usable until
-- something happens to touch them, so installing the guard without looking at
-- the existing data would leave the persisted hole open while reading as
-- closed.
--
-- It refuses rather than mutating anyone's rows: revoking or re-admitting a
-- live manifest is an authority act, not a migration's to take. It names the
-- count, the keys, and the reason so an operator can act on them.
do $$
declare
  v_offending bigint;
  v_detail text;
begin
  select count(*),
         string_agg(m.manifest_key || '@' || m.version || ' (' || quirk_sync.manifest_activation_violation(m) || ')',
                    ', ' order by m.manifest_key)
    into v_offending, v_detail
    from quirk_sync.manifest_registry m
    where quirk_sync.manifest_activation_violation(m) is not null;

  if v_offending > 0 then
    raise exception
      'refusing to complete: % active manifest(s) would be refused by the replacement guard (%). Revoke or re-admit each one, then re-apply.',
      v_offending, v_detail;
  end if;
end $$;

create or replace function quirk_sync.guard_manifest_activation() returns trigger
language plpgsql set search_path=pg_catalog,quirk_sync as $$
declare
  v_violation text := quirk_sync.manifest_activation_violation(new);
begin
  if v_violation is not null then raise exception '%', v_violation; end if;
  return new;
end $$;

-- Every other function in this schema is revoked from the browser roles and
-- granted to `service_role` explicitly; this one was created after that
-- lockdown and so inherited PostgreSQL's default of EXECUTE to PUBLIC. It
-- therefore worked in production by omission, and the next time the delivery
-- migration's `revoke execute on all functions in schema quirk_sync from
-- public,anon,authenticated` is re-run, every write to manifest_registry
-- starts failing with `permission denied for function
-- manifest_activation_violation` — raised inside the trigger, so a valid
-- candidate cannot be written either.
--
-- Verified both halves on PostgreSQL 16.13: with the default ACL a
-- `service_role` insert of a well-formed active manifest succeeds, and with
-- EXECUTE revoked from PUBLIC and no grant it fails with that exact message at
-- `guard_manifest_activation() line 3`. The grant is to `service_role` alone;
-- the trigger function itself needs none, because EXECUTE on a trigger
-- function is checked when the trigger is created, not when it fires.
--
-- SECURITY DEFINER would also work and is not used: the predicate reads only
-- the row passed to it, so a definer context would add reach it has no use for.
revoke execute on function
  quirk_sync.manifest_activation_violation(quirk_sync.manifest_registry)
  from public, anon, authenticated;
grant execute on function
  quirk_sync.manifest_activation_violation(quirk_sync.manifest_registry)
  to service_role;
