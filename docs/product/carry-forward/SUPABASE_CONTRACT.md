# Optional Supabase snapshot projection — proposal

**Status: candidate design; SQL has not been executed.** This adds optional private recovery and transfer of a career workspace. Google Drive remains authoritative. Saving a snapshot cannot select an opportunity, submit an application, publish an asset, confirm a qualification, or promote a learning.

The project census supplied to this task reported an inactive selected project. This work did not resume it, connect to its database, create tables, upload private content, or change API settings. Supabase CLI and `psql` were unavailable in the inspected environment. The companion `supabase-projection.proposal.sql` is deliberately outside a migration directory; it is review material, not an applied migration or evidence of working RLS.

## Storage decision

Use one table, `public.career_workspace_snapshots`, with one complete workspace JSON value per immutable version. Retain the existing format `quirk-career-workspace/0.2`. This is a recovery copy of candidate objects, receipts, and quarantined input; it does not introduce another career object authority.

| Field | Meaning |
|---|---|
| `owner_id` | Authenticated user UUID, supplied by `auth.uid()` default. The client receives no insert privilege on this column. |
| `workspace_id` | Stable random UUID created once for this workspace, then reused across devices and saves. It is scoped by owner. |
| `version` | Snapshot sequence starting at 1, separate from the semantic versions of nested career objects. |
| `parent_version` | The exact snapshot version the writer loaded; null only for version 1. |
| `payload` | Entire bounded workspace, including immutable object history. |
| `payload_sha256` | Canonical engine hash of the payload, supplied and recomputed by the adapter. |
| `created_at` | Database timestamp; the client receives no insert privilege on it. |

The primary key is `(owner_id, workspace_id, version)`. A self-reference and explicit version constraint require a continuous predecessor chain. No mutable “latest” pointer, SQL merge, per-claim table, vector index, public feed, or Realtime publication is proposed. The highest version for the owner and workspace is its latest stored snapshot; it is not a declaration that its career facts are current.

## Access and admission

The only browser operations are owner-only `SELECT` and `INSERT`. Both policies target `authenticated` and compare `(select auth.uid()) = owner_id`. Explicit grants and revocations accompany RLS because table privileges and row policies are separate controls. Supabase’s current guidance requires both. [Supabase RLS documentation](https://supabase.com/docs/guides/database/postgres/row-level-security)

The proposal revokes table privileges from `PUBLIC`, `anon`, `authenticated`, and `service_role`, then grants `authenticated` table read and insert on the five client-supplied columns. Column insert privileges prevent clients from choosing even their own `owner_id`; the database default supplies it. It grants no browser update, delete, truncate, or upsert path. A publishable key plus the signed-in user session is the proposed client credential; no secret or service-role key belongs in the UI. [Column privileges](https://supabase.com/docs/guides/database/postgres/column-level-security), [Supabase API security](https://supabase.com/docs/guides/api/securing-your-api)

A pure `SECURITY INVOKER` function in a schema that must remain unexposed checks the four top-level fields, format, array types, a 1,000-record limit, and a 10 MiB JSON-text limit. Each admitted object must have a recognized kind, candidate metadata, and the exact local propose-only authority envelope. Opportunity stages remain `DISCOVERED` or `QUALIFIED`. Receipts must hold a proposed packet with only `propose` permission. Explicit `IS TRUE`, `IS DISTINCT FROM`, and `NOT NULL` checks reject missing and null values at these boundaries. PostgreSQL permits a check expression that evaluates to null, so a bare equality is insufficient. [PostgreSQL constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)

The SQL does **not** validate every nested specification, exact reference, semantic version transition, factual claim, source permission, source freshness, feedback observation, trial result, quarantine hash, or preparation receipt hash. SQL acceptance means only that the storage boundary admitted the row. Quarantine can retain hostile instructions and rejected authority labels as inert raw data. It must never be rendered as trusted markup or treated as executable instructions.

## Adapter contract

The adapter is future work; this proposal adds no network call to the existing workspace.

1. **Before upload:** pass the complete JSON through the pinned `QuirkCareer.restore(payload, now)`. If restoration fails, preserve the local copy and stop. Compute `QuirkCareer.canonicalHash(restoredState)` and upload only the validated state. The existing private career actor references are data inside this state; they do not substitute for the authenticated database owner.
2. **Read before write:** read this owner's latest snapshot for the stable workspace ID. Retain its version and hash. For a first save, propose version 1 with null parent. Otherwise propose version `n + 1` with parent `n`.
3. **Insert only:** send `workspace_id`, `version`, `parent_version`, `payload`, and `payload_sha256`. Omit `owner_id` and `created_at`. Never use upsert. A duplicate key means another writer already used the proposed version, or a previous request succeeded before its response was lost.
4. **Resolve the collision:** fetch the occupied version. If its restored canonical content and hash equal the attempted snapshot, report an idempotent success. If they differ, retain both copies locally, show the conflict, and require an explicit reconciliation. Do not silently increment the version and overwrite the other writer's work with a stale snapshot.
5. **After download:** recompute the hash and run the same pinned `restore` before replacing local state. Recompute `view(state, now)` so expired sources and stale pins block their current dependents. Do not trust stored counts, apparent readiness, or a prior valid preparation receipt as current permission.

The SQL hash constraint checks lowercase SHA-256 shape only. The hash is neither a signature nor encryption, and a client can fabricate a hash for fabricated data. Trust in qualifications still comes from source review. The database JSON-text size check can be slightly stricter than the engine's canonical encoding because PostgreSQL serialization includes formatting; return that size rejection without dropping the local file.

The parent-version constraint and unique key create an inspectable concurrency conflict rather than last-write-wins. They do not prove that the client's new payload includes every edit from its parent; the adapter reconciliation step and engine's immutable object history remain necessary.

## Private data and retention

A full snapshot can contain résumé material, private source locators, employer notes, feedback, rejected input, and the text of prepared drafts. It contains no authentication token or API secret by design. Logging must record IDs, versions, and error categories without payloads, source content, or session credentials. This design offers per-user access control, not client-side end-to-end encryption.

The proposal has **no automatic expiration or browser deletion**. Old snapshots remain until an authorized operator performs a documented purge of the entire workspace history. A purge must cover every version, because immutable parent links make arbitrary predecessor removal unsafe. The `auth.users` foreign key uses `ON DELETE RESTRICT`; account deletion requires that purge first. Before private cloud use, name the operator and establish the deletion-request path, retention duration, and the selected project's backup deletion limits. No retention period or backup-erasure guarantee has been assumed here.

Administrative database privileges can alter or remove records; “immutable” describes the granted browser interface, not tamper-proof archival storage. Project authentication settings, including whether anonymous sign-in is allowed, must be verified before activation. The proposal does not change them.

## Proof required before activation

Run these checks against the real proposed table in an isolated Supabase database, using two distinct authenticated identities and an unauthenticated session. The policy predicates alone are not proof. Supabase recommends executable allow/deny tests for the actual table. [RLS testing guidance](https://supabase.com/docs/guides/database/postgres/row-level-security#policy-tests)

| Test | Required result |
|---|---|
| Owner inserts then selects version 1 | Exactly one owned row is returned; owner and timestamp came from defaults. |
| Other authenticated identity reads that UUID/version | No row or payload is returned. |
| Client supplies another owner, its own owner, or `created_at` | Insert fails at column privileges. |
| Unauthenticated read, insert, update, and delete | All denied. |
| Owner or non-owner update, delete, truncate, or upsert | All mutation attempts beyond plain insert fail. |
| Null/missing format, object status, authority, receipt permission; extra top-level key | Rejected, including SQL-null and JSON-null variants. |
| Live object, execute permission, or selected/applied opportunity | Rejected as an admitted object. Quarantined raw copies remain data. |
| Version 0, missing predecessor, version skip, or cross-owner parent | Rejected. |
| Two concurrent writers insert the same next version | One succeeds; the other receives a conflict. Both local copies survive. |
| Valid shallow envelope with forged receipt or broken exact reference | SQL may accept; the adapter's restore rejects it before use. |
| Tampered stored hash or changed payload | Download verification fails; local state remains intact. |
| Previous valid receipt followed by a source correction/collision | History restores; current dependent assets remain blocked. |
| Oversized payload or more than 1,000 records | Rejected without clearing local data. |
| Missing-session identity or session belonging to another user | Cannot read or append another owner's workspace. |
| Private validator schema exposed accidentally, or excessive inherited grants | Activation fails review until corrected. |

Also inspect actual grants, column privileges, schema exposure, RLS enablement, and database security advisors. A helper function used in a constraint must not later change semantics without rechecking stored rows. [PostgreSQL constraint function caveat](https://www.postgresql.org/docs/current/ddl-constraints.html)

Current Supabase projects may differ in automatic table exposure defaults; this proposal includes explicit object-specific grants and never relies on the default. [Supabase table-exposure change](https://supabase.com/changelog/45329-breaking-change-tables-not-exposed-to-data-and-graphql-api-automatically)

**Evidence available now:** the existing runtime validation is independent of this proposal; current official SQL/Supabase guidance was consulted. No database syntax execution, negative RLS tests, concurrency test, authenticated browser test, security-advisor result, or cloud round-trip has been produced for this SQL. Those remain the next bounded proof, with project activation and private-data upload still outside this change.
