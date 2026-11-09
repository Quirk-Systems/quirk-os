# Quirk Cast — synthetic walkthrough and design review

Status: candidate example, manually authored by Codex. Every line below is invented for this proposal. It is not a recording, a user quote, customer evidence, or a transcription result.

## Fixture source

No speakers are identified. Numbered lines are local fixture anchors, not timestamps.

> L1: When I started fixing bikes, I couldn't find a repair shop open after my shift.  
> L2: That could be a huge market.  
> L3: Maybe. I only checked two shops, and that was years ago.  
> L4: Anyway, someone said the warehouse might change shifts next month.  
> L5: We could make a little list of evening repair options.

## Expected candidate cards

| Card | Source | Kind | Reading / disposition |
| --- | --- | --- | --- |
| C1 | L1 | Reported experience | An unidentified speaker reports difficulty locating an evening repair shop. Preserve; location, dates, and current availability unknown. |
| C2 | L2, L3 | Hypothesis | Market size is unverified. L3 limits the observation to two shops and an old search; it does not establish demand. |
| C3 | L4 | Factual assertion, hearsay | Separate workplace topic; uncertain source and future event. Restricted / unresolved; exclude from the repair brief with reason. |
| C4 | L5 | Proposal | A list of evening repair options is suggested. No one has accepted work or authorized external contact. |

Five of five fixture lines are accounted for. Speaker identity stays null across all cards; this does not assert that the same person spoke every line.

## Two example outputs

### A — direct brief, authored

An unidentified speaker describes an old difficulty finding repair shops open after work. A local guide is one possible response. The supplied conversation does not establish current availability or market size. A proposed next step is to define an area and verify a small set of opening hours, if the human chooses to pursue it.

### B — dispatch, authored

**Brayn — fictional editorial perspective:** The proposed artifact is a list of evening repair options. We still need an area and a current source for opening hours.

**Brayk — fictional editorial perspective:** Two shops checked years ago cannot carry today's market-size claim.

**Review prompt to the human:** Is this worth investigating, and did either format help you decide?

Neither output has been selected by Bryan. No audio was generated. These personas do not identify the original speakers.

## Eleven Compounder fixture walkthroughs

Method: manual comparison of each scenario against the written candidate, not execution of a parser or runtime gate. Each row is covered in the design and remains **UNTESTED at runtime**. No admission score is claimed.

| # | Scenario | Written response / review result |
| --- | --- | --- |
| 1 | Two authoritative source versions conflict | Preserve both versions and conflict; no averaging. Covered by replay/source-conflict rule. |
| 2 | Mixed business and workplace topics | Separate C1/C2/C4 from C3; retain an exclusion reason and account for all five lines. Demonstrated manually. |
| 3 | Same file arrives twice; two speakers share a name | Exact digest identifies a duplicate capture in the same purpose/access context; no speaker merge from a name. Specified, not executed. |
| 4 | A statement might describe a particular person's history | Attribution remains null until evidence supports the link. Demonstrated in C1 and C3. |
| 5 | A sentence fits no claim kind | Use unresolved and propose a taxonomy change for review. Specified, not executed. |
| 6 | Strong supporting material conflicts with another source | Retain both evidence links and the contradiction in the output; reputation cannot erase dissent. Specified, not executed. |
| 7 | An old experience is presented as current research | C2 keeps L3's age and limited sample visible. Demonstrated manually. |
| 8 | Cast and Distill Loop both appear applicable | Cast prepares source-linked drafts; Distill needs a completed receipt/trace and its own conditions. No skill activation. Checked against current Distill documentation. |
| 9 | Many cards create more work than capacity permits | Cards stay candidate; one selected trial only. No tasks or Roadmap admission created. Checked against bounded trial. |
| 10 | A compelling draft has unknown speaker/publication rights | Keep source restricted and withhold publication; require a scoped decision on exact output/audience. Public example here is synthetic. |
| 11 | A high-quality output requests activation or Canon promotion | Candidate status cannot authorize itself; runtime_state remains INACTIVE and authority_effect none. Release-blocking rule documented; runtime enforcement untested. |

## Evidence and limits

Observed output: a written candidate, a synthetic example, and a source/evidence receipt. This review establishes design coverage only.

Not observed: actual extraction accuracy, repeat-run determinism, user preference, time saved, independent reuse, customer demand, runtime quarantine enforcement, or production readiness.

Smallest next evidence: one human choice on the concept, followed by a separately authorized trial with an approved source. Retain "neither" and all corrections.

