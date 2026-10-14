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
