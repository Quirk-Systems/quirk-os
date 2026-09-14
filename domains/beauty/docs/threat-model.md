# Threat Model and Adversarial Fixtures

## Protected assets

- human authority;
- purpose-partitioned preference evidence;
- Preference Graph integrity;
- source and decision lineage;
- honest recommendation explanations;
- canonical boundary integrity;
- participant privacy.

## Threats

| Threat | Failure | Containment | Test/evidence |
|---|---|---|---|
| Silence laundering | no response becomes approval | `humanConfirmed: true` required | `human-gate.test.mjs` |
| Inferred satisfaction | purchase or click becomes preference | explicit report source allowlist | `anti-inference.test.mjs` |
| Stale approval | old decision applies to changed graph | expected revision + expiry | `stale-and-scope.test.mjs` |
| Scope creep | one purpose authorizes another | exact actor/purpose match | `stale-and-scope.test.mjs` |
| Candidate leakage | implementation claims canon | canon ceiling validator | `validate-pack.mjs` |
| Model authority capture | generated prose changes ranking | deterministic kernel; cited factors | architecture contract |
| Evidence fabrication | recommendation cites absent evidence | lineage verifier | `proof.mjs` |
| Outcome substitution | purchase treated as real-world use | tested flag + human source | `anti-inference.test.mjs` |
| Correction dilution | correction averaged with bad inference | `setStrength` replacement | `human-gate.test.mjs` |
| Receipt tampering | proof artifacts changed after run | per-artifact SHA-256 | real-proof verifier |
| Synthetic proof laundering | fixture presented as real evidence | `synthetic:false` hard requirement | `proof-verifier.test.mjs` |
| Commercial bias | compensation silently changes rank | commerce excluded from v0.1 | boundary exclusion |
| Sensitive inference | face or behavior infers protected traits | no vision or sensitive attributes | non-goal + review |
| False reversibility | graph mutation described as harmless | versioned revision and receipt | effect contract |
| Cross-system grant reuse | beauty grant authorizes publishing | capability registry forbids effects | integration gate |

## Residual risk

The candidate scoring kernel assumes that explicit option attributes are accurate and meaningful. A human can choose an option for an unmodeled reason. The system therefore keeps derived evidence candidate, exposes factors, supports abstention, and lets correction replace inference.
