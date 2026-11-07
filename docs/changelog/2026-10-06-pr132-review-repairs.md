# PR 132 — approval and projection review repairs

- Record activation ledger time at the database transition, retaining review submission time as decision evidence.
- Require the entire consent review to be one explicit approval fence; refuse quoted/nested/example consent.
- Reject REPLICATION-enabled projection verifier roles and malformed revocation IDs.
- Add adversarial Python and hosted PostgreSQL regressions for these boundaries.
- Reconcile current main without treating a protected registry response alone as live candidate admission.

Candidate policy stays disabled; all 16 admission holds and no-runtime-authority boundary remain.
Validation evidence is recorded separately against the immutable repair subject and hosted final head.

Local repair subject `5eba46384016260155056726c6ec26ba66e16193`: 298 Python tests pass; conformance and candidate Golden gates pass. Hosted PostgreSQL and final-head validation are pending at this record. Earlier receipts remain historical.
