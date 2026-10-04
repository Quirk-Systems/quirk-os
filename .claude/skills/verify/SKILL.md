---
name: verify
description: Build and drive the Quirk Sync Control Plane surfaces — the two conformance CLIs and a real PostgreSQL cluster — to observe a change executing rather than to re-run CI.
---

# Verifying a change in quirk-os

There is no app to launch here. The surfaces are two Python CLIs and a
PostgreSQL database, and the database is the one that takes the real work to
reach. This file records what it took, so the next session does not cold-start
it again.

## Python surfaces

CI runs Python 3.13 with the pinned evaluation dependencies; the system Python
may be older and has no `jsonschema` or `PyYAML`. Build a matching environment
once:

```sh
python3 -m venv /tmp/qos-venv
/tmp/qos-venv/bin/pip install -q -r requirements-evals.txt
```

Then drive the CLIs:

```sh
/tmp/qos-venv/bin/python scripts/validate_sync_control_plane.py --repo . \
  --output evals/sync-control-plane/conformance-results.json --require-admit
PYTHONPATH=scripts /tmp/qos-venv/bin/python scripts/validate_deck_grammar.py \
  --repo . --require-pass
```

`--require-admit` exits 1 when any check fails, so the exit code is the
observation. Both CLIs rewrite their evidence artifact in place: regenerate it,
never hand-edit it, because `content_hash_sha256` covers every other field.

## PostgreSQL surface

The migration guards are the thing most changes here touch, and a static read
of the SQL proves only that a predicate is spelled in the file. To watch one
refuse something, stand up a throwaway cluster. PostgreSQL 16 is installed but
not running, and the details below are all load-bearing:

```sh
# Binaries are not on PATH.
PGBIN=/usr/lib/postgresql/16/bin
# initdb refuses to run as root, and the data directory must be somewhere the
# postgres user can traverse — a scratchpad under /tmp/claude-* is not.
install -d -o postgres -g postgres /var/lib/postgresql/scratch
su postgres -c "$PGBIN/initdb -D /var/lib/postgresql/scratch/data"
# -k /tmp puts the socket where a non-postgres user can reach it.
su postgres -c "$PGBIN/pg_ctl -D /var/lib/postgresql/scratch/data \
  -o '-p 5437 -k /tmp' -l /var/lib/postgresql/scratch/log start"
export PGHOST=/tmp PGPORT=5437 PGUSER=postgres
```

The migrations `revoke ... from anon` and `from authenticated`, which a managed
Supabase project supplies and a bare cluster does not. Create them before
applying anything, or the first migration fails on a missing role:

```sh
psql -d postgres -v ON_ERROR_STOP=1 \
  -c "create role anon nologin;" \
  -c "create role authenticated nologin;" \
  -c "create role service_role nologin bypassrls;"
```

`service_role` needs BYPASSRLS, which Supabase gives it. Without it the
production-role cases below fail on row-level security before reaching any
trigger, and pass for the wrong reason.

Apply the migrations in plain filename order — all of them apply cleanly that
way, including the two `20260811_` files that sort after `20260811113009_`:

```sh
for m in $(ls supabase/migrations/*.sql | sort); do
  psql -v ON_ERROR_STOP=1 --single-transaction -f "$m"
done
```

`--single-transaction` is required, not optional. No migration here opens a
transaction of its own — `supabase db push` applies each file inside one, and
an in-file `commit` would close the runner's — so
`20261003090000_sync_control_plane_independent_approval.sql` needs the runner
to supply the transaction its `lock table` lives in. Drop the flag and it
aborts:

```
ERROR:  LOCK TABLE can only be used in transaction blocks
```

That refusal is deliberate. It is what keeps the audit and the guard cutover
from silently splitting under a runner that autocommits each statement.

## Driving the guards

```sh
# The nine manifest-activation cases, in a transaction that is discarded.
psql -v ON_ERROR_STOP=1 -f supabase/tests/manifest_activation_guard.run.sql
# The two cases that run as the role which writes in production. A SEPARATE
# psql invocation — see below; this is not a style choice.
psql -v ON_ERROR_STOP=1 -f supabase/tests/manifest_activation_guard.service_role.sql
# What is actually installed, which no static check can tell you.
psql -t -A -c "select pg_get_functiondef('quirk_sync.guard_manifest_activation()'::regprocedure)"
# And who may execute it. An empty acl means PostgreSQL's default of EXECUTE to
# PUBLIC, which is how a missing grant hides.
psql -t -A -c "select proname, coalesce(proacl::text,'DEFAULT (public can execute)')
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='quirk_sync' and proname like '%manifest_activation%'"
```

**Run the `service_role` file in its own psql session, before anything else in
that session fires the trigger.** `guard_manifest_activation` calls
`quirk_sync.manifest_activation_violation`, PL/pgSQL caches that call's plan per
session, and EXECUTE on a function is checked when the plan is *built* — so the
privilege check is session-order dependent. Observed on PostgreSQL 16.13 with
the grant revoked:

```
fresh session, service_role writes first                       -> ERROR: permission denied
                                                                  for function manifest_activation_violation
fresh session, postgres writes first, then set role and write  -> INSERT 0 1, INSERT 0 1
```

Append those cases to `manifest_activation_guard.cases.sql` and nine superuser
writes prime the plan ahead of them, so they pass with no grant at all. That
happened; it is why the file is separate. The same trap catches you by hand:
driving the superuser cases first in one `psql` session and then `set role
service_role` proves nothing about privileges.

`--single-transaction` on `manifest_activation_guard.cases.sql` looks
equivalent and is not: it rolls back on an error but **commits when nothing
raises**, and one case there is supposed to raise nothing. Run that way it
leaves an active manifest behind. Use the `.run.sql` driver, which supplies
`begin`/`rollback` itself.

`sync_control_plane_hardening.sql` does not pass end to end on a clean
database. Its last case calls `rebuild_projection_snapshot` for
`program.quirk-sync-control-plane`, a row no migration seeds. Reaching only
that failure is the expected result; anything earlier is a real one.

## Make the check fail before believing it

Every guard here exists because a previous one passed on cooperating data. The
probe that matters is the one that proves the check can return false. Each of
these has caught something real in this repository:

```sh
# Does the guard actually run?  Expect exit 3 on the first case.
psql -c "create or replace function quirk_sync.guard_manifest_activation()
  returns trigger language plpgsql as \$\$ begin return new; end \$\$;"
psql -v ON_ERROR_STOP=1 -f supabase/tests/manifest_activation_guard.run.sql

# Does the production role actually have what it needs?  Expect exit 3 with
# `service_role cannot write a valid manifest: permission denied ...`.
psql -c "revoke execute on function
  quirk_sync.manifest_activation_violation(quirk_sync.manifest_registry)
  from service_role;"
psql -v ON_ERROR_STOP=1 -f supabase/tests/manifest_activation_guard.service_role.sql
```

Also: delete a workflow job from a copy of the tree and re-run the validator,
and drop the migration under test and watch which static checks go false. A
green run on its own establishes nothing — and a recipe that cannot go red is
the same defect as a guard that cannot refuse.

## Teardown

```sh
su postgres -c "/usr/lib/postgresql/16/bin/pg_ctl -D /var/lib/postgresql/scratch/data -m immediate stop"
rm -rf /var/lib/postgresql/scratch
```
