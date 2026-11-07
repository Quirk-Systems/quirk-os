-- Expected FAILURE, exit 3; all synthetic roles/grants roll back on disconnect.
\set ON_ERROR_STOP on
begin;
create role quirk_manifest_verifier nologin noinherit nobypassrls;
create role synthetic_projection_parent nologin;
create role synthetic_projection_member nologin;
\if :reverse_browser
  grant service_role to quirk_manifest_verifier;
\elif :reverse_neutral
  grant synthetic_projection_parent to quirk_manifest_verifier;
\elif :reverse_transitive
  grant service_role to synthetic_projection_parent;
  grant synthetic_projection_parent to quirk_manifest_verifier;
\else
  grant quirk_manifest_verifier to synthetic_projection_member;
\endif
\ir ../migrations/20261004140000_sync_control_plane_verified_projection.sql
-- Reaching this is a defect: NOINHERIT does not prevent SET ROLE.
rollback;
