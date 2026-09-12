/** Isolated SQL behavior proof. Install @electric-sql/pglite@0.5.8 in a temporary
 * prefix; set PGLITE_MODULE to its dist/index.js when outside node resolution.
 * This stubs only Supabase auth.uid() and its roles, not Auth/PostgREST services.
 */
import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
const specifier = process.env.PGLITE_MODULE
  ? pathToFileURL(process.env.PGLITE_MODULE).href : '@electric-sql/pglite';
const { PGlite } = await import(specifier);
const db = new PGlite();
try {
  await db.exec(`
    create role anon nologin;
    create role authenticated nologin;
    create role service_role nologin bypassrls;
    create schema auth;
    create function auth.uid() returns uuid language sql stable as $$
      select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid
    $$;
    grant usage on schema auth to authenticated;
    grant execute on function auth.uid() to authenticated;
  `);
  const migration = new URL('../migrations/20260910074902_engineering_evidence_candidate.sql', import.meta.url);
  await db.exec(readFileSync(migration, 'utf8'));
  console.log((await db.query('select version() as version')).rows[0].version);
  const results = await db.exec(readFileSync(new URL('./engineering_projection.sql', import.meta.url), 'utf8'));
  for (const result of results) for (const row of result.rows ?? []) if (row.result) console.log(row.result);
  console.log('Candidate migration and rolled-back SQL fixtures passed in PGlite.');
} catch (error) {
  console.error(error.message, error.code ?? "", error.where ?? "", error.position ?? "");
  process.exitCode = 1;
} finally {
  await db.close();
}
