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
-- Three further repairs to the same function, all of them cases where this
-- trigger was weaker than its Python twin rather than equal to it. Reproduced
-- on PostgreSQL 16.13 against the previous function, each one inserted and
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
-- Deliberately unchanged: the `evaluated_content_hash <> content_hash` test
-- below still compares two columns of the same row, and nothing computes either
-- from the manifest body. That is a missing specification rather than a bug with
-- a patch; see docs/briefs/2026-10-03-manifest-content-hash-preimage.md, which
-- names the two decisions it needs first. That comparison is NULL-safe in
-- practice because both columns are NOT NULL on `manifest_registry`.

-- Checked BEFORE the function is replaced, deliberately. Replacing the function
-- only guards the next write: rows admitted under the old rule stay `active`
-- and usable until something happens to touch them, so installing the guard
-- without looking at the existing data would leave the persisted hole open
-- while reading as closed.
--
-- The order matters because psql autocommits each statement unless the runner
-- wraps the file in a transaction. Verified on PostgreSQL 16.13: with this
-- block placed after the function, the replacement committed and only then did
-- the check raise, leaving the migration half applied. Read-only first means a
-- refusal changes nothing, under either transaction mode.
--
-- It refuses rather than mutating anyone's rows: revoking or re-admitting a
-- live manifest is an authority act, not a migration's to take. It names the
-- count and the keys so an operator can act on them.
do $$
declare
  v_offending bigint;
  v_keys text;
begin
  select count(*), string_agg(manifest_key || '@' || version, ', ' order by manifest_key)
    into v_offending, v_keys
    from quirk_sync.manifest_registry
    where status = 'active'
      and (approved_by is null or approved_by !~ '^human\.[a-z0-9._-]+$');

  if v_offending > 0 then
    raise exception
      'refusing to complete: % active manifest(s) carry an approver that is not an independent human principal (%). Revoke or re-admit each one, then re-apply.',
      v_offending, v_keys;
  end if;
end $$;

create or replace function quirk_sync.guard_manifest_activation() returns trigger
language plpgsql set search_path=pg_catalog,quirk_sync as $$
begin
  if new.status='active' then
    if new.requested_status<>'active' then raise exception 'active manifest requires requested_status=active'; end if;
    if new.admission_decision_ref is null or new.authority_grant_ref is null or new.requested_by is null
      or new.approved_by is null or new.evaluated_content_hash is null or new.transition_evidence_ref is null or new.admitted_at is null
      then raise exception 'active manifest requires independent admission evidence'; end if;
    if new.requested_by !~ '^(human|agent|service|system)\.[a-z0-9._-]+$'
      then raise exception 'manifest requester must be a well-formed principal'; end if;
    if new.requested_by=new.approved_by then raise exception 'manifest requester may not approve its own activation'; end if;
    if new.approved_by !~ '^human\.[a-z0-9._-]+$'
      then raise exception 'activation requires approval by an independent human principal'; end if;
    if new.evaluated_content_hash<>new.content_hash then raise exception 'evaluated content hash does not match manifest content hash'; end if;
    if jsonb_array_length(new.eval_refs)=0 or jsonb_array_length(new.stop_conditions)=0
      then raise exception 'active manifest requires eval evidence and stop conditions'; end if;
    -- `is distinct from`, not `<>`. A missing JSON key makes `->>` return NULL,
    -- and `NULL <> 'block'` is NULL, not true, so an OR chain containing it
    -- evaluates to NULL and `if NULL then` does not fire. Omitting the key
    -- therefore passed the guard that exists to require it, while supplying a
    -- wrong value was correctly refused.
    if new.manifest_kind='orchestrator' and jsonb_array_length(new.skill_refs)>1 and
      (new.trigger_contract is null
       or new.trigger_contract->>'collision_behavior' is distinct from 'block'
       or nullif(new.trigger_contract->>'routing_policy','') is null)
      then raise exception 'multi-skill orchestrator requires fail-closed trigger contract'; end if;
    if new.domains ? 'data_productization' and
      (new.rights_review is null
       or new.rights_review->>'outcome' is distinct from 'approved'
       or coalesce(new.rights_review->>'license_verified','false')::boolean is not true
       or new.rights_review->>'privacy_review' is distinct from 'approved'
       or coalesce(new.rights_review->>'provenance_complete','false')::boolean is not true)
      then raise exception 'data productization requires approved rights, licensing, privacy, and provenance review'; end if;
  end if;
  return new;
end $$;
