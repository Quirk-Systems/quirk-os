# Continuation: verified consumers, local refresh and portable presentation

2026-10-14. CANDIDATE. Extends the existing review branches; merges and deployments
are not part of this continuation.

## Implemented

- OS writes a responsive, printable branch report with CSS generated from Quirk's
  existing semantic tokens. Output receipt includes document and CSS byte hashes.
- A bounded local synchronizer creates immutable snapshots and a locked,
  compare-and-swap current.json pointer. Replaying unchanged content is idempotent.
  Changed meaning requires a new source revision; style release is part of snapshot identity.
- Quirk adds a plain CSS/document exporter, scoped Tailwind/shadcn bridge and a
  browser/Node consumer. The consumer verifies Python producer bytes and domain
  projections before exposing data; unknown extensions remain opaque.
- Music's consumer produces a standalone styled document without overwriting files.
- Town's workshop imports a synthetic pack, shows origin, keeps two demonstration
  viewers' choices separate, retains the prior valid view on bad input, and clears
  tab state on leaving. These are local demonstration viewers, not authenticated users.

## Reproduce

Run tests and producer in OS:

```sh
python -m unittest discover -s experiments/cross_repo -p 'test_*.py' -v
python experiments/cross_repo/compiler.py experiments/cross_repo/source.json /tmp/new-quirk-pack
python experiments/cross_repo/synchronize.py experiments/cross_repo/source.json /tmp/local-quirk-stream
```

For an existing local stream, pass --expected-current with the current snapshot
digest. Reread the pointer after a rejected lease; never retry blindly.
Receipts retain before/after pointer state. Failed pointer delivery records failure.
A stale .sync-lock requires investigating the interrupted writer before manual
recovery. Only one local stream, on a local filesystem, is supported.

Run Music's import-pack.mjs with the emitted pack.json and a new HTML path.
Start Town and visit /workshop; import the same file. Each consumer validates it
independently of the producer. This is cross-runtime reuse, not independent human review.

For style regeneration, run the Quirk monorepo's portable-styles.mjs exporter.
Run --check against managed destination files before --write. Local overrides belong
in a separate file. No automated job changes a brand choice, authority or shared meaning.

## Breadth and limits

The source retains creative medium, capability ecosystem and participatory world.
The local Favor Exchange is a workshop; no real account, public favor, purchase,
private-memory transfer, human preference inference, canon admission or creative grade occurs.

Portable CSS applies to HTML/docs, print and opt-in framework components. tokens.json
can inform native document adapters; native DOCX/slides/sheets adapters and their fidelity
checks remain OPEN. Additional Quirk applications have not been automatically restyled.

Network synchronization, real multi-user authorization, general context resolution,
private-source handling, source authentication, independent reuse, maintenance benefit
and actual human creative judgment remain OPEN.

The local sync receipt follows Core Execution Receipt 005. The synthetic producer
receipt remains a fixture receipt. Production authority is a separate decision.
