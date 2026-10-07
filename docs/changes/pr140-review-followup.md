# PR #140 review follow-up

- Expand migration and decision audit directories into explicit file evidence; reject directory targets instead of silently reporting them missing. File hashes retain byte-level evidence binding.
- Reject missing or unsupported queue/audit schema versions before interpreting their contents.
- Correct Distill requester fixtures to agent.probe and isolate candidate rejection with exact errors and a paired synthetic admitted control, including the registry boundary introduced by #141. A malformed requester must fail conformance.

All admission work remains inspect-only: 16 holds, zero verified moves, no authority or admission effect. Synthetic admission and registry fixtures exist only in memory; they do not establish real approval or runtime authority.
