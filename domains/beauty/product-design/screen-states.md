# Required Screen States

| State | User-facing behavior | System behavior |
|---|---|---|
| Loading | preserve context; no fake progress | no state transition |
| Abstained | confirm no preference evidence created | append choice with abstention |
| Insufficient evidence | explain why ranking is weak | no invented confidence |
| Conflicting evidence | show competing signals | preserve contradiction |
| Recommendation expired | require regeneration | deny old proposal lineage |
| Outcome not tested | close without graph update | no proposal |
| Proposal stale | explain graph changed | regenerate against new revision |
| Decision expired | request a fresh decision | fail closed |
| Revised | show replacement values | corrections override candidate deltas |
| Rejected | preserve outcome; no mutation | receipt rejection if core supports it |
| Applied | show before/after revision | write effect receipt |
| Error | preserve completed stages | no silent retry with effects |

## Accessibility floor

- entire proof path is keyboard operable;
- choice cards expose names, attributes, and selection state;
- confidence is not conveyed by color alone;
- motion is nonessential and respects reduced-motion settings;
- approval, revision, and rejection are distinguishable without position alone;
- receipt digest is copyable but not the only explanation.
