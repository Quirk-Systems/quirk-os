-- Expected FAILURE, exit 3. The open transaction discards every synthetic row.
\set ON_ERROR_STOP on
begin;
\ir manifest_activation_guard.cases.sql
\ir ../migrations/20261004140000_sync_control_plane_verified_projection.sql
-- Reaching this is a bug: legacy human.* strings are not historical consent.
rollback;
