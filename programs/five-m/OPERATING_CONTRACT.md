# Five-M Candidate Operating Contract

**Status:** candidate-only. This is not an executable grant.

## Five lenses

| Lens | Decision | Observable output | Disallowed shortcut |
| --- | --- | --- | --- |
| **Move** | Which cheapest reversible action advances a real outcome? | one owner, one move, stop condition | do every task because a tool can |
| **Money** | Which beneficiary outcome creates legitimate economic value? | payment/verified customer outcome, variable cost, time | count clicks, estimated savings, or interest as revenue |
| **Merge** | Does exact-head code meet technical, review and authority gates? | checks, review, source SHA, merge receipt | stale CI, `mergeable=true`, or agent confidence alone |
| **Monitor** | Which signal would change the next decision? | event, threshold, counter-metric, source revision | noisy polling or silent autonomous action |
| **Machine** | What repetitive reversible action is truly worth automating? | explicit scope, cost cap, failure receipt, rollback | capability implying permission; self-promotion |

## One Move Card

Each card shall declare:

```yaml
object_type: five_m_move_candidate
status: candidate
beneficiary: <person or business>
outcome_metric: <real-world outcome>
baseline: <source reference or UNKNOWN>
move:
  actor: <named owner>
  next_action: <bounded action>
  stop_condition: <observable threshold>
money:
  economic_value: <observed amount or NOT_PROVEN>
  payment_received: <receipt or NOT_RECEIVED>
  human_minutes: <measurement>
  variable_cost: <measurement>
merge:
  source_revision: <exact commit or N/A>
  required_checks: <observed statuses>
  approval: <human receipt or NONE>
monitor:
  signal: <event with measurement>
  window: <delay horizon>
  notify_on: <meaningful state change>
machine:
  automated_now: false
  grant_ref: NONE
  scope: read_only_or_draft_candidate
  rollback: <specific action>
```

## Adversarial invariants

- **VALUE_NOT_PROXY:** claims of revenue require actual transaction/receipt evidence; pipeline, clicks and projected ROI remain separate.
- **CONSENT_BEFORE_CONTACT:** no unsolicited outbound contact or sensitive customer-data processing from an inferred user preference.
- **HEAD_BEFORE_MERGE:** current source SHA and actual executed checks required; no auto-merge implied by green CI.
- **NO_QUIET_ACTION:** monitoring creates observations/notifications, not implicit deployment or payment authority.
- **NO_AUTONOMOUS_PROMOTION:** feedback may propose changes, but human review determines persistent changes.
- **BOUNDED_COST:** no billable infrastructure, spending limit changes or subscriptions as default execution.
- **REAL_FAILURE_RECEIPT:** unsuccessful executions remain failures/unknown, never retrospective success.

## Status ladder

`PROPOSED → REVIEWED → APPROVED_BOUNDED → EXECUTED → OBSERVED → LEARNING_CANDIDATE`

Only an explicit human decision can authorize `APPROVED_BOUNDED`. Successful execution never automatically expands it. Canon and production are outside this candidate ladder.

## Human modes

Bryan defines intent and grants authority; Brayn inspects mechanisms, evidence and contradictions; BryMinn makes the message memorable. They are perspectives, not separate self-authorizing execution identities.
