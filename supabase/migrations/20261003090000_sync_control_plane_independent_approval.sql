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
-- Deliberately unchanged: the `evaluated_content_hash <> content_hash` test
-- below still compares two columns of the same row, and nothing computes either
-- from the manifest body. That is a missing specification rather than a bug with
-- a patch; see docs/briefs/2026-10-03-manifest-content-hash-preimage.md, which
-- names the two decisions it needs first.

create or replace function quirk_sync.guard_manifest_activation() returns trigger
language plpgsql set search_path=pg_catalog,quirk_sync as $$
begin
  if new.status='active' then
    if new.requested_status<>'active' then raise exception 'active manifest requires requested_status=active'; end if;
    if new.admission_decision_ref is null or new.authority_grant_ref is null or new.requested_by is null
      or new.approved_by is null or new.evaluated_content_hash is null or new.transition_evidence_ref is null or new.admitted_at is null
      then raise exception 'active manifest requires independent admission evidence'; end if;
    if new.requested_by=new.approved_by then raise exception 'manifest requester may not approve its own activation'; end if;
    if new.approved_by !~ '^human\.[a-z0-9._-]+$'
      then raise exception 'activation requires approval by an independent human principal'; end if;
    if new.evaluated_content_hash<>new.content_hash then raise exception 'evaluated content hash does not match manifest content hash'; end if;
    if jsonb_array_length(new.eval_refs)=0 or jsonb_array_length(new.stop_conditions)=0
      then raise exception 'active manifest requires eval evidence and stop conditions'; end if;
    if new.manifest_kind='orchestrator' and jsonb_array_length(new.skill_refs)>1 and
      (new.trigger_contract is null or new.trigger_contract->>'collision_behavior'<>'block'
       or nullif(new.trigger_contract->>'routing_policy','') is null)
      then raise exception 'multi-skill orchestrator requires fail-closed trigger contract'; end if;
    if new.domains ? 'data_productization' and
      (new.rights_review is null or new.rights_review->>'outcome'<>'approved'
       or coalesce(new.rights_review->>'license_verified','false')::boolean is not true
       or new.rights_review->>'privacy_review'<>'approved'
       or coalesce(new.rights_review->>'provenance_complete','false')::boolean is not true)
      then raise exception 'data productization requires approved rights, licensing, privacy, and provenance review'; end if;
  end if;
  return new;
end $$;
