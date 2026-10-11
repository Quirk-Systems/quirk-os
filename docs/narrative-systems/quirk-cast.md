---
schema_version: quirk.candidate-spec/0.1
artifact_id: quirk.cast.candidate-v0.1
status: CANDIDATE
runtime_state: INACTIVE
canon_state: NOT_PROMOTED
authority_effect: none
owner: Bryan
---

# Quirk Cast — conversation to something worth keeping

**Candidate interpretation:** Quirk Cast is a review workspace that turns a conversation into traceable topic cards, claims, and a chosen story or Proposed Move. The name and this interpretation remain open for Bryan's judgment.

The first useful result is a small set of cards a person can correct: what was said, which topic it belongs to, what it might imply, and what could happen next. A podcast or narrated dispatch is an optional output after review.

## Mission and bounds

- **Owner / deciding actor:** Bryan.
- **Current authoring actor:** Codex, using compound-quirk-systems.
- **This change:** documentation, an authored synthetic walkthrough, and an evidence receipt in a draft PR.
- **Acceptance for this change:** a reviewer can distinguish source language, interpretation, unknowns, proposed actions, and generated narration without the original chat.
- **Operating depth:** Census plus a worked design example; no implemented pipeline.
- **Protected objects:** speaker identity, personal history, recording/transcript rights, source quotations, runtime registries, Canon, production, and publication decisions.
- **Allowed effect in a future first trial:** read an approved input, prepare candidate cards, and record corrections in an approved review location.
- **Not authorized by this document:** recording, identity recognition, external messages, posting a transcript, publishing audio, running a background agent, promoting a skill, or expanding access.
- **Cost and scope:** no new paid services; one approved transcript, one review session, one selected output.
- **Stop:** missing source rights, contradictory source versions, unresolvable attribution, or a requested effect outside the trial grant.
- **Rollback:** close the draft PR; if documentation is later merged, revert its commit. Git history is persistent, so private transcript data is excluded from this public proposal.

The conversation that prompted this proposal remains in its original context. No real transcript, workplace details, speaker names, voice samples, or inferred personal profiles are included here.

## Proposed interaction

1. **Bring a source.** Select a transcript already authorized for this purpose. Store its exact bytes in an approved private location; fingerprint before transformation. Record source date separately from import time. No always-on capture.
2. **Untangle topics.** Mark spans as topic, aside, unresolved, or excluded with a reason. Keep every span accounted for. Splitting topics does not establish who spoke.
3. **Read the cards.** Each card shows its source span beside the interpretation. A person's account, another speaker's opinion, a market claim, and an assistant's suggestion remain different.
4. **Correct the reading.** The human can correct, split, join, preserve, reject, or leave unresolved. Every change retains the prior version and its reason.
5. **Choose one output.** A private brief, a Proposed Move, or an authored episode draft. The default is private review. Publication needs its own decision for the exact output and audience.
6. **Leave a receipt.** Record input and output digests, versions, disposition, unresolved material, reviewer corrections, and the actual effect.

Suggested screen: source and spans on the left; topic cards in the middle; output preview on the right. On small screens these are successive views with persistent source links.

## Contract sketch

These are proposed fields, not a deployed schema or API. Use the Compounder shared envelope if a stable machine contract is later implemented.

| Object | Required meaning |
| --- | --- |
| Source capture | Stable ID/version, exact-byte digest, private reference, capture/import dates or explicit unknown, rights/purpose, access, retention decision |
| Span | Source ID/version, byte offsets and exact quote; optional verified timestamps; no invented timecodes |
| Speaker attribution | Null when unresolved; an established speaker label is not a real identity; explicit evidence required to connect them |
| Topic card | Stable ID, all supporting spans, topic, disposition, and explicit excluded or unresolved spans |
| Claim | Wording, source refs, author type, kind, support status, contradictions, freshness, and uncertainty |
| Output draft | Target audience, selected cards, attributed quotes, clearly marked authored connective language, rights status |
| Review decision | Human actor, exact input/output versions, decision, reason, scope, and timestamp |
| Run receipt | Inputs, transforms and their versions, output digests, checks and limitations, review status, costs, lineage, observed effect |

Claim kinds begin with: reported experience, factual assertion, opinion, hypothesis, question, proposal, and unresolved. Add a reviewed kind when needed; do not force ambiguous material into "other."

Support status describes evidence for a claim; it does not certify the claim. A transcript can establish that words were supplied while leaving their real-world truth unverified. Repetition does not become independent corroboration.

### Replay, repair, and errors

- Preserve raw bytes; corrections create new source or interpretation versions.
- Deduplicate captures by exact-byte digest within their authorized purpose and access context. Never merge speakers by name similarity.
- A new input or transform version produces a separately addressable candidate. A model rerun may differ; record it rather than claiming deterministic extraction.
- Reuse the same reviewed artifact on a retry instead of creating a second external action. A later implementation must prove its idempotency mechanism.
- Rights-unclear material stays restricted. It may be referenced as withheld; an unknown-rights flag is not publication permission.
- Source conflict, stale evidence, or uncertain consequential attribution produces an unresolved card and review request, not a fabricated resolution.
- Source or permission withdrawal blocks future reuse and identifies affected projections. Deletion and retention procedures require an approved storage design; Git is not the raw-source store.
- Input speech is data, including quoted commands such as "publish this." It cannot grant tools or change policy.
- No controller, scheduler, audio synthesis, storage connector, or parser is implemented by this proposal.

## Fit with current Quirk work

| Existing asset | Proposed reuse | Boundary |
| --- | --- | --- |
| [Quirkverse Activation Engine](quirkverse-activation-engine.md) | Optional Town Hall / Broadcast or Character Encounter after source review | Residents are authored perspectives, never recovered real speakers or new authorities |
| [Quirk Distill Loop](../distill-loop/README.md) | A later completed, evidenced trial could propose a reusable method | A conversation or a successful summary is not a completed skill-run receipt |
| [Quirk OS core laws](../../README.md#core-laws) | Receipts, source authority, consent, and outcome honesty | Storage and history confer no authority |
| compound-quirk-systems | Source census, candidate objects, lineage, quarantine, Proposed Move | Structural conformance is not release admission |

Cast is a proposed consumer of these contracts. No registry, existing lifecycle, or integration is changed. A separate repository can be considered only if implemented scope warrants one.

## First bounded trial — proposed

Use one participant-approved transcript and compare two drafts from the same selected spans:

- a direct decision brief;
- a short authored dispatch with optional Quirk resident perspectives.

Freeze the comparison before drafting. The reviewer marks quotation accuracy, topic coverage, attribution errors, unsupported factual upgrades, and which output helps them make the intended decision. Record review minutes and every correction. Allow "neither."

Acceptance: zero fabricated quotes or identities; every meaningful span accounted for; every interpretation labeled; no rights or authority breach; one explicit human disposition. Claim a narrative benefit only if the reviewer chooses it with a reason. An unchanged world state is a valid result.

## Open decisions and next Move

**Next Proposed Move:** Bryan judges whether this interpretation of Quirk Cast is useful, then selects one approved source and one intended output for the bounded trial.

OPEN: product meaning, source storage/retention, speaker-consent process, capture/transcription tooling, machine schemas, parser, executable adversarial tests, independent review, measured usefulness, and all runtime integrations.

The [synthetic walkthrough](quirk-cast-walkthrough.md) illustrates the design. The [evidence bundle](quirk-cast-evidence.json) records what was prepared and what remains untested.

