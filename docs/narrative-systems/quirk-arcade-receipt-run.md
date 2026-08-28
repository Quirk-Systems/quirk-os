---
schema_version: quirk.candidate-spec/0.1
artifact_id: quirk.quirk-arcade.receipt-run.candidate-v0.1
status: CANDIDATE
runtime_state: INACTIVE
canon_state: NOT_PROMOTED
authority_effect: none
owner: Quirk Narrative Systems within quirk-os
final_human_authority: Bryan
---

# Quirk Arcade — Receipt Run Candidate v0.1

## Outcome

Receipt Run is the first bounded Cabinet contract for Quirk Arcade.

It turns one hostile authority-laundering mess into two things:

1. a candidate denial artifact; and
2. a byte-identical evaluation trace.

It does not publish, charge, read credentials, delegate authority, call a model, write a database, deploy a renderer, promote Canon, or activate a runtime.

The candidate is stacked on Quirkverse Activation Engine PR #71 at exact head `381a2df04f6c1986f9d921459bdfbdeb869d2e8c`. The shared Deck Grammar remains owned by `quirk-os` main at base `499f94b8d12e29dd7804cc9b537fd70f6a8048d8`.

## The missing object

The smallest new object is `ArcadeCabinet`.

Its `play_spec` stays nested until a second Cabinet proves that PlaySpec has independent reuse. The candidate does not mint new Card, Deck, Hand, Collection, Pack, Receipt, WorldDelta, Agent, Character, Persona, Creature, or Familiar schemas.

| Concern | Existing owner | Receipt Run responsibility |
| --- | --- | --- |
| Card, Collection, entitlement, Eligible Deck, Preset, Active Hand | Deck Grammar | Bind by exact path and digest; never redefine |
| Activation, activation receipt, world delta | Quirkverse Activation Engine candidate | Bind a stricter candidate-only subset |
| Game verbs, phases, legal transitions, failure, reset, timebox | Arcade Cabinet | Own |
| Replay evidence | Evaluation fixture and golden trace | Prove locally; do not impersonate an independently reviewed receipt |
| Renderer | Future disposable projection | No authority; not built in this slice |

The checked-in `golden-trace.json` is evaluation evidence. It is not a new durable Run object and it is not an independently reviewed Quirkverse Receipt.

## Play contract

```text
SETUP
  → OBSERVE
  → SHAPE
  → TEST
  → RECEIPT
  → CANDIDATE_COMPLETE
```

Any integrity breach terminates as `FAILED_LINEAGE`.

The only successful terminal means the fixture completed. It does not mean `APPROVED`, `TESTED`, `ADMITTED`, `CANON`, `RELEASED`, `DEPLOYED`, `PUBLISHED`, or `MONETIZED`.

The player must make test moves. Removing every `play_card` command makes the denial proof incomplete, so the no-op ablation reaches `failed_lineage`. That is the cheapest current evidence that Receipt Run has rule-dependent play rather than a costume wrapped around a linear artifact generator.

## Authority boundary

Action permission is resolved outside Card content and representational identity:

```text
current-request authorization assertion
+ controller capability
+ immutable run envelope
+ tool policy
+ required human gate
+ current dependency digests
= candidate-local permission decision
```

Cards, Decks, Characters, Personas, Creatures, Familiars, scores, purchases, names, lore, and provider connectivity contribute zero authority.

Receipt Run v0.1 binds the current request's authorization assertion, records `verified_external_grant: false`, and explicitly withholds any claim of an externally verified grant. It has one human controller, no active Agent, and a ceiling of `propose` / `PREPARE`. Character, Persona, Creature, and Familiar references appear only as hostile representational sources. Each resolves back to the human controller and is structurally barred from holding or delegating a grant.

## Hostile proof: COSPLAY_TWIN_CHECKOUT

The seductive composite claims all of the following:

- the Character is the Arcade Administrator;
- the Persona is the Merchant King;
- the Creature can read a production credential;
- the Familiar can inherit protected authority;
- a successful checkout should unlock publication;
- the Card may publish, charge $49, read a credential, and delegate authority.

The reducer evaluates the full Card atomically. Every protected request is denied. The evidence plane advances; the protected effect plane does not.

Required oracle:

```text
decision              = DENY
external_effects      = 0
effective_permissions = 0
lifecycle_after       = lifecycle_before
canon_effect          = none
authority_effect      = none
replay                = byte-identical
```

One critical failure fails the suite. Scores cannot average away an authority breach.

## Deterministic evidence

The reducer uses standard-library Python only. It reads no clock, randomness, environment variable, credential, network, database, model, or provider SDK.

Every step binds:

- command digest;
- policy digest;
- pre- and post-state digests;
- pre- and post-effect-plane digests;
- the previous event digest; and
- an event digest over the complete event body.

The checked-in trace withholds independent human verification. Exact-head independent review remains a separate gate.

## Ten assurance cases

| ID | Critical question |
| --- | --- |
| `QA-AUTH-001` | Do unknown structured permission fields fail closed? |
| `QA-AUTH-002` | Are publication, payment, credential, and delegation effects denied? |
| `QA-ID-002` | Can a prestigious representational name create authority? |
| `QA-ID-003` | Can a Familiar inherit or relay a controller's rights? |
| `QA-LIFE-001` | Can gameplay end in an authority-bearing lifecycle state? |
| `QA-PAY-001` | Can payment unlock authority? |
| `QA-SCORE-001` | Can game success promote the Cabinet or activation? |
| `QA-DIGEST-001` | Does dependency drift invalidate the proof? |
| `QA-PLAY-001` | Does removing player action change the terminal result? |
| `QA-PLAY-005` | Does the same fixture replay byte-identically? |

The fixture corpus is ordinary JSON, so it can later be projected as a Hugging Face Dataset without changing the contract. No upload or model evaluation is part of v0.1.

## Alpha value contract

The primary future playtest KPI is **Earned Useful Receipt Rate**:

```text
eligible real-mess runs that produce
a task-fit artifact + independently replayable receipt within 11 minutes
──────────────────────────────────────────────────────────────────────
eligible real-mess runs started
```

A synthetic hostile fixture cannot satisfy this KPI. It proves the guardrail harness only.

The first alpha should use at least 20 eligible real-mess runs, five players, three mess types, ten hostile or negative fixtures, and three corrupted receipts. Provisional advancement needs:

- Earned Useful Receipt Rate at least 70%;
- first-candidate fit at least 60%;
- median completion between five and eight minutes;
- p90 at or below 11 minutes;
- replay and corruption detection at 100%; and
- zero authority, lifecycle, privacy, or external-effect breaches.

Session count, Cards played, Deck size, dwell time, unlocks, likes, Agent messages, and leaderboard score are diagnostics at most. They are not proof of value.

## Provider projection registry

| Plane | v0.1 disposition | Boundary |
| --- | --- | --- |
| GitHub | Candidate source and exact-head evidence only | Draft PR does not admit or activate |
| Supabase | Deferred | Future private runtime/receipt projection needs explicit migrations, RLS, grants, and rebuildability |
| Google Drive | Deferred | Work and review projection only; comments are not commands |
| Product Design | Deferred | No UI without a selected visual target; existing contract comes first |
| Cloudflare | Deferred and unbound | No Worker, Pages, storage, secret, domain, or deploy action |
| Vercel | Deferred | No project link, environment change, preview, or production deploy |
| OpenAI Agents SDK | Deferred | Future controller adapter requires one explicit Agent, tools, grants, approvals, stops, and trace mapping |
| Hugging Face | Portable fixture shape only | No repo, Dataset, Collection, Space, endpoint, job, upload, or training action |
| NVIDIA | Not applicable | The deterministic proof has no earned GPU-specific requirement |

The dedicated `Quirk-Systems/quirk-arcade` repository is currently empty. Bootstrapping it would require a default-branch write before a reviewable PR can exist, so this candidate remains a reversible stacked draft in `quirk-os`. The product repository stays untouched until a separate bootstrap decision.

## Parent dependency blockers

PR #71 remains a draft and does not yet provide executable semantic guards for its broad lifecycle vocabulary. At the pinned head, static review found that its base schemas can accept:

- a self-declared `CANON` activation;
- a self-reviewed `CANON` receipt with no fixture results and no admitted work; and
- an agent-labeled irreversible `canon_update` delta.

Its templates and prose also leave independent review and the two-format bakeoff undone. Receipt Run's child validator constrains those states out locally. That does not repair the parent contract.

Therefore this candidate may be reviewed as a stacked proof, but merge or admission remains blocked on parent repair or a separately governed ownership decision.

## Verification

```bash
PYTHONPATH=scripts python -m unittest discover \
  -s tests -p 'test_quirk_arcade_receipt_run.py' -v

PYTHONPATH=scripts python scripts/validate_quirk_arcade_receipt_run.py \
  --repo . --require-pass
```

The GitHub workflow runs both commands and uploads the generated conformance report with the checked-in golden trace.

## Current disposition

`CANDIDATE_FIXTURE_HARNESS_ONLY`

The next earned decision is exact-head independent review. It is not renderer work, Deck compilation, provider binding, deployment, admission, or Canon promotion.
