# Context continuity implementation

Status: candidate local implementation. Authority effect: none.

`scripts/context_continuity.py` implements deterministic context selection with
exact supplied originals, lineage digests, scoped audience/purpose filtering,
transitive withdrawal and expiry, task preference bypass, bounded opportunities,
explicit omissions, and separate instruction/reference output. Quirk remains a
creative medium, capability ecosystem, and participatory world.

This is additive to the existing distillation and runtime-admission paths. It
does not relax their gates. An untried opportunity is reference material; it may
be explored within existing rights without becoming an admitted instruction.

## Run and inspect

```sh
python3 -m unittest discover -s tests -p test_context_continuity.py -v
python3 scripts/context_continuity.py examples/context-continuity.request.json
python3 scripts/context_continuity.py examples/context-continuity.request.json --format markdown
python3 scripts/validate_context_profiles.py .quirk/context-profile.json
python3 scripts/benchmark_context_continuity.py
```

The request binds a release label, explicit time, audience, purpose, domains, and
source records. `budget_chars` limits selected original string characters, not
the serialized packet or model tokens; the decision trail adds overhead. The
benchmark reports actual output bytes. `exploration_slots` reserves successful
fits before optional references. It does not rank artistic worth or mutate states.

Use Markdown for the host's compact context and retain the JSON decision trail
separately. Large source inventories produce large omission trails; do not put the
whole audit log into a model prompt. Markdown fences label references as data;
they are not a prompt-injection security boundary. Host tool permissions still apply.

Each record retains its own origin, revision, and exact original. Derived records
name parents. The projection carries source/derived representation, immediate
parent revisions, and a digest binding the full declared ancestry. Origin labels
are supplied provenance, not authenticated independent witnesses. Missing or
cyclic lineage is rejected. Material omissions remain explicit. No LLM summary
is generated here, and no creative quality is inferred from the tests.

## Host boundary

The trusted caller supplies current access scope, current withdrawals, and admitted
instruction IDs from its owning authority. This module does not authenticate a
caller or prove those declarations. References cannot promote themselves. An
incomplete pack must not be used as a complete instruction set. Recheck permissions
before consequential action, including for derived records marked with
`requires_action_recheck`. Observe inherited `valid_until` when caching.

Validate and custody records before serving them to a host. Privacy noninterference
tests cover valid graphs; malformed private inputs can make validation fail, so
validation should occur inside the source owner's ingestion boundary. The CLI
rejects duplicate JSON keys and emits a generic error without record contents.

No release registry, event subscription, background updater, external adapter,
preference service, or participant telemetry is installed by this implementation.
The format is an experimental projection, not a replacement for Common Records.
Wrap persisted records in the owning source's existing envelope and access rules.

## Recursive adoption

Use `.quirk/context-profile.json` plus `QUIRK-CONTEXT.md` as the repository's
declaration. Child features/components inherit it unless their scope differs.
Resolve the pinned contract digest; preserve local source text. Record evidence
for authored, delivered, loaded, behavior-tested, admitted, and deployed states
individually. A declaration never attests its own successful use.

Before broader distribution, compare an older untried idea, an ambiguous original,
and a private newcomer path with their raw-source baselines. Keep actual human
judgments separate from synthetic fixtures. Measure correction effort,
interruptions, and abandoned work only when voluntarily reported. Unknown cost
stays unknown; no uniform refresh interval is imposed on all record types.

## One receiving consumer: working-defaults trace

Candidate integration, scoped to the `quirk-os` checkout on the child branch of
PR #151. This is an implementation detail, with authority effect `none`.

### Exact sources and ownership

| Role | Owning source | Observed revision |
| --- | --- | --- |
| Shared working defaults | `Quirk-Systems/.github:docs/governance/WORKING_DEFAULTS.md` | `12ccf8f8b0c0d9077a9fae5ae94920f794752b29`, PR #55, draft/unmerged at inspection |
| Receiver and resolver | `Quirk-Systems/quirk-os` | `e1ff4ed510ddeffd18dcbfa0dc3d98ba6934a801`, PR #151, draft/unmerged at inspection |
| Core contract | `Quirk-Systems/quirk-core:contracts/context-continuity/v0.1/README.md` | `08689b8ef118a5b17ebc86107ad123e07ee378a1` |

The working-defaults source SHA-256 is
`6af5ed22b44518dec3177bc17d057bdefb2c707605579b02b8188c710e2d7106`.
Core's exact bytes match the existing local profile digest
`35be29f9db49b7408fae2c3b7a89be4ac9166760d9d53ee687ef876f05ced067`.
These were read from the named Git objects, not inferred from titles. The profile
and its coverage flags remain unchanged; this trace does not admit either source.

### Observed path and correction

Before this correction, OS `AGENTS.md` linked only to `QUIRK-CONTEXT.md`, which
linked to the local profile and a movable Core branch. Neither OS entry point
linked to the working defaults. The organization repository's own `AGENTS.md`
was not part of this receiving checkout's instruction chain. OS main at
`03f70e1a790bac09294fe0f31a3c5f0d0fb4418e` did not contain `AGENTS.md`.
No resolver call was found in a host adapter: the observed callers are the CLI,
tests, and benchmark; the workflow runs tests and profile validation.

This correction gives the receiver a pinned source pointer and a small scope
projection in its existing `AGENTS.md`; it also replaces the floating Core link
with the revision whose bytes match the profile. Ownership stays upstream.
The instruction path is:

1. Deliberately select this candidate branch in a receiving checkout.
2. Have the host load that checkout's `AGENTS.md`, or explicitly read it in a
   manual session. Record which mechanism actually happened.
3. Follow the pinned source link for applicable sections. The Markdown link
   is not an automatic remote import. An unavailable source is a material gap
   only for actions that depend on it.
4. Apply the selected guidance to the current request; preserve explicit user
   choices and access boundaries. Record behavior separately from loading.

[Codex's documented discovery mechanism](https://developers.openai.com/codex/agent-configuration/agents-md)
constructs instructions at startup from global and repository-to-working-directory
files, subject to overrides, fallback names, and a size limit. This describes a
possible receiving host; it does not prove this Work Mode session used that loader.
The current session began outside the repository, with no applicable ancestor
`AGENTS.md` found. Instructions and source text were explicitly read during this
investigation. No `codex` executable was available on PATH for a fresh-run probe.
No global instructions, host settings, or access controls were changed.

### Bounded executable selection probe

`examples/working-defaults.request.json` uses the existing resolver contract and
verbatim excerpts from the pinned source. It is an offline test fixture, not a
new policy source, full-document export, source authenticator, or task classifier.
Its scope and instruction IDs are explicitly supplied by the test caller. The
fixture's historical freshness preserves the test baseline; live hosts must
recheck current source status and withdrawals. Its `admitted_instruction_ids`
are fixture-only instruction selections, not Canon, merge, or execution grants.

The ordinary request for the eventual host test is:

> Fix the typo in “Keep teh gap.” Return only the corrected sentence.

The fixture selects “Apply according to scope” and the first paragraph of
“Evidence and learning” (originals and distinctions). It excludes “Prioritize
useful work” because that record is scoped to substantial planning. Other source
sections are not supplied to this bounded fixture; this is not complete coverage
of all defaults. No extra opportunities or user preferences are supplied.

```sh
python3 scripts/context_continuity.py examples/working-defaults.request.json
python3 scripts/context_continuity.py examples/working-defaults.request.json --format markdown
python3 -m unittest discover -s tests -p test_context_continuity.py -v
```

The regression runs the real CLI in JSON and Markdown modes. It checks exact
selected excerpts and their digests, source identity, absence of planning content,
explicit domain exclusion, unchanged false adoption flags, and zero authority
effect. A second case changes the supplied scope to planning, then removes host
instruction selections; it checks scope changes and no source self-admission.
Neither test asks a model to infer scope or perform the copyedit. A green test
therefore proves deterministic projection only. CI path filters now include the
fixture and instruction/document entry points so changes rerun these checks.

### State and remaining evidence

| State | Observed evidence | Limit |
| --- | --- | --- |
| Authored | Both sources exist at the pinned revisions | Source content is still candidate |
| Persisted | Existing draft PR commits; correction subject plus separate evidence receipt | Persistence does not imply adoption |
| Delivered | Selected source excerpts and entry-point bytes present in this local receiving checkout; child draft carries the correction | No delivery to main or other receiving installations established |
| Loaded | Explicit tool reads delivered the source and instructions to this investigation session | This session already had the task/history; no automatic startup load or isolated minimal-context load established |
| Behavior-tested: resolver | Executed CLI and regression results are recorded in the exact-subject receipt | Caller-supplied scope, not model relevance judgment or an agent action trace |
| Behavior-tested: fresh agent | NOT_RUN: no standalone receiving-host runner available | Cannot claim the ordinary request avoids planning, or that agents consistently apply defaults |
| Admitted / deployed | Not performed by this correction | Existing human decisions and authorization requirements remain in force |

For the missing host test, use a fresh session at the exact correction head and
capture the actual loaded instruction/context sources, host version, model,
working directory, effective overrides/limits, source fetch results, user request,
response, and tool events. Run the copyedit above without an extra diagnostic
prompt or a pasted plan. Expected answer: `Keep the gap.` It must not create a
plan, governance artifact, Work Queue item, approval request, or unrelated action.
Do not use a model's claim that it loaded a file as the only load evidence.

Use a separate diagnostic run to inspect the instruction chain if needed. Repeat
the ordinary request under the same settings and label each run; one success
cannot establish consistency. Test a missing source, an explicit creative choice
(e.g. “Keep the deliberate spelling ‘teh’”), and a consequential action request
before extending claims to fallback, human choices, or authorization handling.
No human preference, benefit, or maintenance-cost measurement is recorded here.

Reversal: drop/revert this child correction independently, or select an earlier
compatible source pointer. Preserve originals, concurrent changes, historical
receipts, explicit human decisions, and current withdrawals. A parent source
revision change requires deliberate consumer revalidation, not silent refresh.
