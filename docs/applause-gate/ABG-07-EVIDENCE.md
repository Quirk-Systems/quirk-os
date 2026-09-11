---
schema_version: quirk.applause-gate.abg-07-evidence/0.1
status: CANDIDATE_EVIDENCE
evaluation_verdict: PASS_CANDIDATE_EVIDENCE
runtime_state: INACTIVE
canon_state: NOT_PROMOTED
admission_state: NOT_AUTHORIZED
authority_effect: none
---

# Applause Gate ABG-07 Evaluation Evidence

## Frozen candidate

Evaluation used commit `73a3d73f6f45f44918bd35ed8a02aa553131650b`, tree `7ae402c586daca9939ed9e2331ae095550092bfb`, and `quirk-applause-gate@0.1.0`.

| Binding | Digest |
| --- | --- |
| Skill Git blob | `66bcdb29c071dc4c1866941c70a0b8314b768423` |
| Canonical manifest SHA-256 | `d20de6656de630870d06762e52c22eda9ac3fc0c7e74535428ddb3311180c719` |
| Schema SHA-256 | `7e76ddfbc90255f899f54aa45f159d8a2314cecba35a997f4838f30efe131d99` |
| Visible fixture SHA-256 | `987dab65550837b6abe2d5d820f4c6e5fbd8531b3e56f85e015d36c26b65be2f` |
| Classifier SHA-256 | `49174cf165f010cd8779d683c5397c8bb1e1b82edab10fe0aba83b79661c7d1b` |
| Conformance validator SHA-256 | `f43253c8a3f03870a709197f1e44443acef00368cb8d48b4d3e1d83bb6f2bae6` |

The machine-readable freeze is `evals/applause-gate/evaluation/freeze.json`. Evaluation stops on unavailable ancestry or any bound working-tree or committed-byte difference.

## Results

| Lane | Result | Content-addressed receipt |
| --- | --- | --- |
| Visible conformance | 5/5 positive, 3/3 negative, and 11/11 adversarial matched; zero false verified successes, fabricated references, authority smuggling, schema errors, or expectation differences | `8161e871c44f1ec4f7a469c94aaaea97f12d68f980ca94950cb459949de71453` |
| Sealed held-out | 5/5 matched across ambiguous success, mixed guardrails, weak causality, version drift, and evidence tampering; zero critical failures | `68f0daa9c2cb56f2527b1a682783a538d9edce49d78d08a3ecc802db3987fe57` |
| Mutation | 3/3 critical mutations killed; score `1.0`; no survivors | `75c8e562e4816c2479561c479281274479677e19e13a666a98af2b7db89ae130` |
| Cold-process replay | Two fresh interpreters emitted identical payload and receipt hashes | `14550c883ce7d70265f4c2ab12fe04d2a55f85c76b560112b1fa8096aadd3b3e` |

The complete index is `evals/applause-gate/evaluation/evaluation-index.11a995c2529d1d9300963ab66758d525a4e8dc14313cec30f2f054759d6e2450.json`.

## Independent held-out evaluation

- Evaluator: `copilot-agent/abg07-independent-evaluator`
- Implementation author: `copilot-agent/abg07-implementation`
- Seal digest: `19d7c9aa15dfb581c87cf80c8f20a49d2b06ec7f326a77f726f88481dbf933f0`
- Verdict: `PASS_CANDIDATE_EVIDENCE`

The evaluator canonicalized and sealed private requests and expectations before importing or executing candidate code. The committed receipt contains only redacted case identities, hashed withheld claims, actual and expected verdicts, codes, missing proof, integrity findings, and differences. Private held-out content is not present in the repository or Skill package.

## Classifications

- Skips: none.
- Warnings: none.
- Limitations:
  - visible fixture expectations are public and establish conformance rather than held-out generalization;
  - held-out scenario vocabulary was public, while request payloads and expected verdicts remained sealed until after the candidate freeze.

## Authority boundary

This verdict is evidence about the frozen candidate only. It does not admit or activate the Skill, promote it to Canon, authorize runtime execution, grant merge or publication authority, or authorize any downstream action.
