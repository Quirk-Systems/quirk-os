# Multimedia Multipliziert

**Technical ID:** `quirk.media_multiplication`  
**Type:** Quirk Creation + Quirk Asset capability family  
**Status:** PROPOSED

## CANON

> Every derivative owes a source receipt and a medium-native reason to exist.

Multimedia Multipliziert is the controlled multiplication of a canonical Quirk object into distinct media forms that each add useful affordance.

It is not:

- resizing;
- copy-paste repurposing;
- transcript confetti;
- one idea repeated at eleven aspect ratios;
- an excuse to fabricate visual authority;
- a content calendar wearing a German coat.

## 1. Transformation contract

Every derivative declares:

```yaml
media_derivative:
  id: media.<slug>
  canonical_source:
    object_ref: ...
    version: ...
    receipt_ref: ...
  medium: ...
  audience: ...
  job: ...
  transformation_type: ...
  medium_native_affordance: ...
  claims:
    preserved: [...]
    added: [...]
    omitted: [...]
  accessibility:
    transcript: ...
    captions: ...
    alt_text: ...
    reading_order: ...
  provenance:
    quirk_receipt_ref: ...
    c2pa_manifest_ref: ...
  rights:
    owner: ...
    licenses: [...]
    source_permissions: [...]
  evaluation_refs: [...]
  release:
    status: draft | review | approved | released | superseded | withdrawn
    receipt_ref: ...
```

## 2. Eleven useful surfaces

1. **Canonical specification** — authoritative definitions and contracts.
2. **Reference README** — fast orientation and implementation path.
3. **Architecture map** — spatial relationships, boundaries, and flows.
4. **Interactive Control surface** — inspect, query, challenge, approve, reverse.
5. **Decision deck** — executive/product narrative and tradeoffs.
6. **Guided walkthrough** — narrated screen or diagram demonstration.
7. **Long-form video essay** — temporal explanation, examples, critique.
8. **Short-form specimens** — one bounded mechanism per clip/card.
9. **Audio briefing** — hands-free narrative with verbal navigation.
10. **Prompt/skill cards** — executable application of the object.
11. **Dataset + executable examples** — machine-usable proof and tests.

A source object does not need all eleven. Select only surfaces with a real audience/job fit.

## 3. Medium-native affordances

A derivative must add at least one:

- interactivity;
- spatial understanding;
- temporal demonstration;
- comparison;
- embodied performance;
- accessibility;
- searchability;
- executable behavior;
- participatory review;
- compression;
- emotional precision;
- distribution-specific context.

If it adds none, it is a duplicate.

## 4. Provenance

### Internal

Every derivative receives a Quirk receipt linking:

```text
canonical object
→ source version
→ transformation
→ human/agent contributors
→ tools/models
→ edits
→ evals
→ rights
→ release
```

### Public media

Use C2PA Content Credentials where the format and toolchain support them. C2PA proves associated provenance and tamper evidence; it does not certify that a claim is true or good.

Keep Quirk claim/evidence evaluation separate from C2PA asset provenance.

## 5. Product-design system

### Core components

```text
<SourceReceipt />
<DerivativeFamily />
<MediaLineage />
<ClaimFidelityDiff />
<NativeAffordanceBadge />
<AccessibilityStatus />
<RightsStatus />
<ContentCredentialStatus />
<ReleaseReceipt />
<WithdrawDerivative />
```

### Killer view: “WHERE DID THIS COME FROM?”

For any asset:

```text
current derivative
↓
canonical source
↓
source version and receipt
↓
transformations and contributors
↓
claims added/omitted
↓
rights and accessibility
↓
evals
↓
siblings and superseding versions
```

## 6. Evaluation suite

### Source fidelity

- canonical claims preserved accurately;
- omissions disclosed;
- new claims separately sourced;
- no stale source version.

### Medium-native value

- derivative adds a real affordance;
- format fits audience and job;
- information architecture is native to the medium;
- repetition is intentional, not lazy.

### Accessibility

- captions and transcript where applicable;
- alt text and reading order;
- meaningful color-independent cues;
- keyboard/navigation support for interactive work;
- audio description when visual action carries meaning.

### Rights

- sources and contributors identified;
- license and usage rights recorded;
- likeness/voice permission where required;
- no unlicensed asset laundering.

### Strange Intact

- distinctiveness survives translation;
- jargon is not used as camouflage;
- humor or edge serves the object;
- the derivative does not impersonate Bryan.

### Integrity

- source receipt exists;
- provenance manifest verifies;
- release status is current;
- withdrawn/superseded assets are not promoted as operative.

## 7. Production procedure

```text
select canonical object
→ identify audience and job
→ choose useful media surfaces
→ write transformation briefs
→ lock claims and source version
→ produce medium-native drafts
→ accessibility and rights pass
→ source-fidelity eval
→ medium-native eval
→ human review
→ C2PA/Quirk provenance package
→ release receipt
→ outcome measurement
→ keep / revise / withdraw / multiply again
```

## 8. Outcome metrics

Do not optimize only for impressions.

Track:

- comprehension gain;
- successful task completion;
- source click-through;
- challenge/correction rate;
- accessibility completion;
- reuse by another system;
- downstream Proposed Moves;
- derivative maintenance burden;
- stale-version exposure;
- conversion to meaningful outcome;
- family-level learning.

## 9. Anti-patterns

- **Aspect-Ratio Industrial Complex:** same message, eleven crops.
- **Transcript Taxidermy:** spoken words dumped into a document without redesign.
- **Diagram Alibi:** beautiful boxes covering undefined interfaces.
- **Synthetic Authority:** polished AI media implying evidence that does not exist.
- **Accessibility Afterthought:** “we'll add captions later.”
- **Source Orphan:** derivative no longer points to canon.
- **Content Credential Theater:** provenance badge treated as truth certification.
- **Infinite Feed Tax:** derivative volume exceeds maintenance and comprehension value.

## 10. Golden release rule

A media family is Golden only when a stranger can:

- find the source;
- distinguish canon from derivative;
- understand what the medium added;
- verify claims and rights;
- use accessible alternatives;
- identify the current version;
- challenge or correct the asset;
- reuse it without Bryan narrating the family tree.
