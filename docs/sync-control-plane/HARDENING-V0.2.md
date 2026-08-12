# Sync Control Plane Hardening v0.2

This candidate implements QH-001 through QH-010 from the blocked admission gauntlet.

| Move | Applied repair | Proof |
| --- | --- | --- |
| QH-001 | Independent manifest admission and legal transition guard | JSON Schema, Python policy, PostgreSQL trigger |
| QH-002 | Append-only receipts and transition ledger | mutation-blocking trigger and supersession fields |
| QH-003 | Executable SCP-001…011 suite | case fixtures, policy runner, unit tests, CI |
| QH-004 | Drift/conflict proposal mechanics | `proposed_moves` table and `observe_binding` |
| QH-005 | Atomic outbox worker mechanics | lease token, owner, `SKIP LOCKED`, retry and dead letter functions |
| QH-006 | Canonical/runtime projection mappers | versioned mapping YAML and Python round-trip tests |
| QH-007 | Consequential decision contracts | `sync-decision.v1` and manifest rights/trigger contracts |
| QH-008 | Cloudflare boundary | ADR and deferred platform manifest |
| QH-009 | Separate candidate conformance CI | `sync-control-plane-conformance.yml` |
| QH-010 | Migration and compensation proof | transactional Supabase proof suite |

## Remaining external gates

Implementation does not equal admission. The following remain external:

- GitHub Actions must execute on the pushed candidate commit.
- The hardening migration and SQL proof must run in Supabase.
- GitHub Discussions must be enabled before the RFC seed becomes a native Discussion.
- The stacked PR #3 governance failures remain a separate merge signal.
- Bryan must record the human admission decision.
