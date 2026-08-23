# Supabase Projection — Candidate

The migration creates `quirk_beauty_private`, which must **not** be added to the Supabase Data API exposed-schema list for v0.1.1.

## Access posture

- `anon`: no schema or table privileges;
- `authenticated`: append explicit sessions, choices, and outcomes; inspect only own rows;
- `service_role`: writes options, derived evidence, recommendations, proposals, and read-only core mirrors;
- no user update/delete grants;
- all child rows bind to the same session, actor, and purpose through composite foreign keys;
- RLS is enabled and forced on every table;
- canonical definitions and actual Preference Graph storage remain elsewhere.

## Isolated validation order

1. Apply migration to a non-production Supabase project.
2. Confirm `quirk_beauty_private` is absent from exposed schemas.
3. Run `tests/rls.sql` as an administrative connection.
4. Run Supabase security and performance advisors.
5. Record migration digest, project reference, advisor output, and rollback evidence.
6. Do not apply to production or admit runtime without a fresh grant.
