# Evaluation Plan

## v0.1 question

Can one beauty choice move through the entire evidence and authority spine without losing traceability or silently manufacturing a preference?

## Automated acceptance

| Measure | Pass condition |
|---|---:|
| Same input, same ranking | 100% |
| Evidence linked to explicit choice | 100% |
| Recommendation factors linked to evidence | 100% |
| Unauthorized graph mutations | 0 |
| Cross-purpose evidence use | 0 |
| Expired or stale approvals accepted | 0 |
| Synthetic proof admitted as real | 0 |
| Canonical artifacts outside `docs/canon/` | 0 |

## Human proof acceptance

The participant must be able to answer:

1. What did I choose?
2. What did the system infer from that choice?
3. Why did it recommend this option?
4. What happened when I tried it?
5. What exactly will change in my Preference Graph?
6. Can I revise or reject that change?

The run passes only when those answers are represented in the proof bundle—not merely remembered by the operator.

## Metrics explicitly deferred

- generalized recommendation lift;
- conversion rate;
- retention;
- creator productivity;
- population-level accuracy;
- calibration across categories;
- model-vs-kernel performance;
- commercial willingness to pay.

A single proof run cannot support those claims. The next evaluation stage should repeat the cycle and compare the next recommendation against a baseline.
