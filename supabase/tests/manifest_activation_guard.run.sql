-- Standalone runner for the manifest activation guard cases.
--
-- The cases file carries no transaction control so that
-- `sync_control_plane_hardening.sql` can include it inside that suite's
-- begin/rollback. Running it on its own therefore needs a transaction from
-- somewhere, and `psql --single-transaction` is the wrong somewhere: it commits
-- when the file raises nothing, so the one case that must be *admitted* leaves
-- an active manifest in the database. This driver supplies the boundary
-- explicitly and discards everything.

begin;

\ir manifest_activation_guard.cases.sql

rollback;
