# Quirk Distill Loop

Status: **candidate / non-operative**. Nothing in this pack admits a skill, grants runtime authority, or promotes Canon.

## What it is

The distill loop is the post-run flywheel. When a skill run finishes with an immutable receipt, the trigger extracts the moves that actually worked and writes them as a reusable skill package in the same `SKILL.md` + `manifest.json` format as every other package under `skills/`. The next run can pick that package up as context.

The idea is borrowed from the Hermes Agent distill loop (MIT). Hermes writes the distilled skill straight into the loadable set. Quirk cannot do that, because a skill that writes skills has no authority to make them true. So the loop lands every auto-written skill as an **unreviewed candidate**, and only a **distill promotion receipt** with two distinct actors moves it into the set the next run may see. Promotion is still not admission. Admission, activation, and Canon keep their existing separate receipts.

## Tiers

| Tier | How a package gets there | Visible to next run | Runtime loadable | Registry |
| --- | --- | --- | --- | --- |
| distilled candidate | `post_run_distill` from a `completed` receipt | listed as pending only | no | never |
| reviewed candidate | distill promotion receipt, `decision: promote` | yes, as candidate source context | no | never automatically |
| rejected | distill promotion receipt, `decision: reject` | no | no | never |
| manifested candidate | separate human PR into `skills/registry.json` | n/a | no | yes |
| admitted | external admission record and scoped grant | n/a | yes, under grant | yes |

A distilled candidate lives at `skills/quirk-distilled-<task>-<hash>/`. The namespace prefix is what lets `scripts/validate_skills.py` keep its twelve-skill drift gate while the flywheel adds packages, and what lets the registry check refuse any `quirk-distilled-*` id.

## Sequence

```
run receipt (immutable) + run trace
  -> post_run_distill
       -> abstain (ledger entry)                 when the run was not completed, the receipt does not bind
                                                 the source digest, fewer than three declared moves
                                                 succeeded, a stop condition fired, the observed ceiling
                                                 exceeds the source ceiling, or the receipt was already distilled
       -> distilled candidate (ledger entry)     skills/quirk-distilled-*/SKILL.md, manifest.json,
                                                 evals/skills/distilled/<id>.json (positive + authority only)
  -> reviewer authors adversarial + regression cases
  -> distill promotion receipt (requested_by != approved_by, neither is the trigger)
  -> apply_promotion
       -> refused                                any digest, provenance, actor, or eval failure
       -> promoted (ledger entry)                package bytes untouched, status stays candidate
  -> next_run_context                            only promoted candidates whose on-disk digests still match
```

## What the trigger will not do

- Distill a `blocked`, `abstained`, or `failed` run.
- Distill a move the source skill did not declare. Undeclared moves that succeeded are listed under "Excluded from distillation" and flagged `UNDECLARED_MOVE_EXCLUDED`.
- Raise the ceiling. The distilled ceiling is the lower of the source ceiling and the observed ceiling, and an observed ceiling above the source ceiling aborts distillation.
- Author adversarial or regression eval cases. The starter suite carries the replay itself and the authority boundary, which the loop can state honestly. The missing kinds block promotion until a reviewer writes them.
- Distill a distilled skill. Second-order distillation is refused.
- Distill the same receipt twice.
- Write to disk. `post_run_distill` returns the files and the updated ledger; the caller writes them. The CLI writes only with `--write`.

## What promotion will not do

- Accept a receipt where requester and approver are the same actor, or where either is `agent.distill-loop`.
- Accept a receipt whose digests differ from the candidate on disk or from the ledger's distilled entry.
- Accept a receipt whose body was edited after attestation.
- Accept a receipt without all four eval kinds passing for the exact candidate id and version.
- Edit the candidate package, change its status, add it to the registry, or mark it admitted. The schema pins `promoted_to: reviewed_candidate` and `admission_effect`, `canon_effect`, `runtime_effect` to `none`.
- Promote twice, or promote a rejected digest.

## Ledger

`skills/distill-ledger.json` is append-only and hash-chained. Every trigger decision, including abstention, and every promotion or rejection appends an entry with `prev_entry_sha256` and `entry_sha256`. Tampering with any entry breaks verification, and the ledger module refuses to append to a ledger that fails verification. The committed ledger is a valid genesis until the first live distillation lands.

The ledger is a projection. A candidate's tier is folded from its entries; nothing else is authoritative about it.

## On "signed" governance

This repository has no key infrastructure, so the promotion receipt is not cryptographically signed. What it has instead is what the rest of the skill runtime already uses: digest binding to exact bytes, an attestation digest over the receipt body, distinct requester and approver, provenance that must match the ledger, and fail-closed validation. If signing arrives later, `attestation` is the field that grows a signature. Until then this document says plainly that promotion is accountable, not cryptographic.

## Files

| Path | Role |
| --- | --- |
| `scripts/distill_loop/trigger.py` | `post_run_distill` |
| `scripts/distill_loop/package.py` | candidate manifest, `SKILL.md`, starter eval suite |
| `scripts/distill_loop/ledger.py` | append-only chain, state fold |
| `scripts/distill_loop/promotion.py` | receipt validation, `apply_promotion`, attestation |
| `scripts/distill_loop/context.py` | `next_run_context` |
| `scripts/distill_loop/evaluator.py` | deterministic evaluator for distilled cases |
| `scripts/distill_loop/__main__.py` | CLI: `distill`, `promote`, `attest`, `context` |
| `scripts/validate_distill_loop.py` | conformance report, `--regenerate-example` |
| `schemas/distill-run-trace.schema.json` | trace input |
| `schemas/distill-ledger.schema.json` | ledger |
| `schemas/distill-promotion-receipt.schema.json` | promotion receipt |
| `examples/distill-loop/` | fixture run, expected outputs after distill and after promotion |
| `tests/test_distill_loop.py` | unit and adversarial tests |
| `.github/workflows/distill-loop-conformance.yml` | CI evidence |

## Running it

```
PYTHONPATH=scripts python -m distill_loop distill --receipt <receipt.json> --trace <trace.json>
PYTHONPATH=scripts python -m distill_loop distill --receipt <receipt.json> --trace <trace.json> --write
PYTHONPATH=scripts python -m distill_loop attest --receipt <promotion-body.json> > promotion-receipt.json
PYTHONPATH=scripts python -m distill_loop promote --receipt promotion-receipt.json --eval-suite <reviewed.json> --write
PYTHONPATH=scripts python -m distill_loop context
PYTHONPATH=scripts python scripts/validate_distill_loop.py --repo . --require-pass
```

`--repo` is where schemas and source skills are read; `--root` is the tree holding the ledger and distilled candidates; `--out` redirects writes. All three default to this checkout.

## Worked example

`examples/distill-loop/run-receipt.json` and `run-trace.json` record a completed trial of `quirk-distillation-synthesizer` 0.2.0. Four declared moves succeeded, one undeclared operator move succeeded, and one declared move was skipped. The trigger writes `quirk-distilled-decision-brief-2d699dfa` with exactly the four declared moves, excludes the other two by name, and appends one `distilled` ledger entry. `promotion-receipt.json` and `reviewed-eval-suite.json` then promote it; `expected-after-promotion/next-run-context.json` shows it as the only context source, still `runtime_loadable: false`. The validator regenerates both stages from the fixtures on every run and fails on any byte of drift.

## Decision ceiling

This pack justifies candidate completeness only. It cannot by itself mark a distilled package reviewed, admitted, active, current, chooseable, useable, canonical, or deployed.
