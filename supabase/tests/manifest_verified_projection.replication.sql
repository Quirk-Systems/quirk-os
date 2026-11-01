-- Expected FAILURE, exit 3; the synthetic privileged role rolls back.
\set ON_ERROR_STOP on
begin;
create role quirk_manifest_verifier nologin noinherit nobypassrls replication;
\ir ../migrations/20261004140000_sync_control_plane_verified_projection.sql
rollback;
