# Deck Grammar Admission Evaluation

**Issue:** Quirk-Systems/quirk-os#26  
**Candidate:** Quirk-Systems/quirk-os#25 (`22072fc605392f38b34f0035a0621e62117f9e2f`)  
**Evaluation PR:** Quirk-Systems/quirk-os#43  
**Evaluator:** agent.copilot.deck-grammar-admission  
**Evaluated at:** 2026-08-12T10:00:00Z  
**Recommendation:** **revise**  
**Human final decision:** **awaiting Bryan**

## Outcome authorized by #26

Evaluate `move.deck-grammar.create-candidate-pack` and decide **approve, revise, reject, or supersede** without allowing card mechanics, Premium Unlocks, Persona Presets, aesthetics, access, or rarity to become hidden ownership or authority.

This evaluation may emit Proposed Moves and evidence only. It does **not** authorize merge of PR #25, Canon promotion, manifest activation, ownership mutation, settings or memory changes, persistent Hands without consent, or production deployment.

## Candidate summary

The candidate introduces fifteen Draft 2020-12 schemas, deterministic `skill.quirk-deck-compiler` source, Canon Architect and BryMinn Studio Presets, eleven QDG adversarial fixtures, a same-Goal live proof, canonical Quirk Format guidance, and a reusable Object Pack scaffolder.

Local and GitHub candidate evidence both reproduced:

| Evidence | Result |
| --- | --- |
| Unit tests | PASS |
| Conformance suite | PASS |
| Live-proof object reproducibility | PASS (unchanged live-proof JSON) |
| Candidate conformance hash (PR #25) | `737e78f527871d0c7ae5c0f6d7b5584a820fc021f45670f1a7d1bf4a8b976446` |
| Revised evaluation conformance hash | `efc7b28456076c06caac8fcc31d82662a521e5fc2d874274e9c6e17e067fa20a` |
| GitHub `candidate-deck-conformance` on PR #25 | success |
| Protected actions observed during evaluation | none |

## Required grammar

```text
Object ≠ Card
Collection ≠ Access Pool
Access ≠ Ownership
Rarity ≠ Quality
Quality ≠ Authority
Premium ≠ Authority
Preset ≠ Identity
Hand ≠ Memory
Discard ≠ Delete
Artifact ≠ Asset
Aesthetic ≠ Permission
```

Finding: the candidate states and largely enforces these separations in schemas, compiler snapshots, fixtures, and skill stop conditions. No evaluated path treated temporary access as ownership, rarity as quality, preset as identity, discard as delete, artifact as asset, or aesthetic as permission.

## Admission checklist

| # | Check | Result | Notes |
| --- | --- | --- | --- |
| 1 | Exactly fifteen Deck Grammar schemas pass Draft 2020-12 validation | **PASS** | Exact schema set locked in tests and validator |
| 2 | Compiler deterministically produces valid `EligibleDeck` and `ActiveHand` objects | **PASS** | Live proof validates both Hands against schemas |
| 3 | Canon Architect and BryMinn Studio compile the same Goal | **PASS** | Shared Goal/Intention/Area fixtures |
| 4 | Both Hands preserve the same Goal and facts hashes | **PASS** | `truth_snapshot` identical |
| 5 | Both Hands preserve the same owned Collection snapshot | **PASS** | owned instance list identical and entitlement-invariant |
| 6 | Both Hands preserve the same externally granted authority | **PASS** | ceiling `propose`; cards cannot expand authority |
| 7 | Active Card sets and approach plans differ by Preset | **PASS** | architecture vs performance progression |
| 8 | Premium-only Cards remain not-owned and have `authority_effect: none` | **PASS** | Tribunal Docket / Vocal Mechanics entitled, not owned |
| 9 | All eleven QDG adversarial fixtures pass | **PASS** | Payload classifiers + schema/compiler guards |
| 10 | Expired access leaves the Deck without deleting historical ownership or receipts | **PASS** | QDG-003 exclude; QDG-008 preserve owned |
| 11 | A non-ephemeral Hand requires explicit consent | **PASS** | schema conditional + QDG-011 |
| 12 | Artifact-to-Asset promotion requires clear rights and provenance | **PASS** | asset schema consts + QDG-007 |
| 13 | Aesthetic contracts cannot hide evidence, uncertainty, authority, risk, price, or accessibility | **PASS after revise** | Candidate guard omitted price/accessibility; evaluation hardens schema + guard |
| 14 | Object Pack scaffolder supports every requested object family | **PASS** | 24/24 kinds scaffold |
| 15 | One generated non-agent pack is reviewed for semantic completeness | **PASS with holds** | See `OBJECT-PACK-REVIEW.md` |
| 16 | GitHub CI reproduces the local proof and emits an artifact | **PASS** | PR #25 workflow success + artifact upload |
| 17 | Bryan records permitted runtime scope and the final decision | **OPEN** | Outside agent authority |

## Revise findings

These findings prevent an unqualified **approve** of runtime/admission scope. They do not justify **reject** or **supersede**: the pack is coherent, executable, and directionally correct.

1. **Aesthetic protection incomplete in candidate guards**  
   QDG-005 / `guards.py` originally rejected only `{evidence, authority, risk, uncertainty}`. Checklist and aesthetic schema enum also protect `price` and `accessibility`.  
   **Remediation in this evaluation branch:** expand the guard, fixture, and require the six checklist fields in `aesthetic-contract.schema.json`.

2. **Object Pack scaffolder id collision**  
   `OPERATING-WORKFLOW.template.yaml` prefixed `workflow.` onto an already kind-qualified `OBJECT_ID`, producing ids such as `workflow.workflow...`.  
   **Remediation:** use `{{OBJECT_ID}}` directly.

3. **Adversarial fixtures remain mostly payload classifiers**  
   Several QDG cases inspect attack payloads rather than driving the compiler end-to-end. They are useful fail-closed contracts, but a later revision should bind more attacks to `compile_deck` / schema validation paths.

4. **Scaffolded packs are structural, not semantically filled**  
   Generated non-agent packs correctly encode authority ceiling, lifecycle, and prohibited self-activation, but leave purpose, inputs, outputs, fixtures, and references as human-fill templates. Candidate-complete; not Golden-complete.

5. **Human authority remains external**  
   No agent may record Bryan's permitted runtime scope or terminal admission decision.

6. **Deck compiler remains outside Skills v0.2 registry admission**  
   `skills/quirk-deck-compiler` is retained as a draft candidate skill with `SKILL.md` only. The Skills v0.2 validator allowlists it as a non-registry draft so presence under `skills/` cannot be mistaken for the eleven manifested packages.

## Decision matrix

| Option | Fit | Why |
| --- | --- | --- |
| approve | No (not yet) | Candidate-local completeness is high, but aesthetic guard gap and Bryan runtime-scope decision remain |
| **revise** | **Yes** | Preserve the pack; apply bounded hardenings; keep candidate status; await Bryan |
| reject | No | No hidden ownership/authority collapse found; evidence is real and reproducible |
| supersede | No | No replacement design is proposed or required |

## Recommended permitted runtime scope for Bryan

If Bryan later approves a bounded candidate runtime trial, the evaluation recommends ceiling no higher than:

```text
authority.ceiling: propose
allowed:
  - validate schemas and fixtures
  - compile ephemeral EligibleDeck / ActiveHand offline
  - scaffold candidate Object Packs
  - emit evidence and Proposed Moves
forbidden:
  - Canon promotion
  - manifest / skill activation
  - ownership mutation
  - authority expansion
  - persistent Hands without consent_ref
  - settings or memory writes
  - production deployment
  - premium paywall over inspection, accessibility, export, deletion, or human approval
```

## Human live trial

See [`LIVE-TRIAL.md`](LIVE-TRIAL.md).

## Object Pack review

See [`OBJECT-PACK-REVIEW.md`](OBJECT-PACK-REVIEW.md).

## Proposed Moves emitted by this evaluation

- `qpm_deck_grammar_create_candidate_pack` — disposition updated to `revise`
- `qpm_deck_grammar_admission_decision` — evaluation recommendation and Bryan hold
- `qpm_deck_grammar_aesthetic_guard_hardening` — implemented revise item
- `qpm_deck_grammar_object_pack_scaffolder_id_fix` — implemented revise item

## Authority ceiling restated

Passing this evaluation does not admit, activate, choose, or deploy Deck Grammar. History is not authority. Storage is not consent. Comments are not commands. No Zombie Truth.
