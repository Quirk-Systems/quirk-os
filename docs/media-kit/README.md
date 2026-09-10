# Quirk Media Kit

Status: **CANDIDATE** · Owner: **Quirk Media, within Quirk Creation + Quirk Asset** · Repository: **Quirk-Systems/quirk-os**

Carry a source, its candidate derivatives, and one unsigned version choice in a single offline ZIP. A readable `index.html` answers “Where did this come from?”; the verifier detects missing files, changed bytes, stale source bindings, and a view that disagrees with the manifest.

This is one implementation slice of [Multimedia Multipliziert](../golden-project-pack/MULTIMEDIA-MULTIPLIZIERT.md). It uses the existing `media-derivative.v1` shape. The kit adds file custody and a portable choice; it does not implement rendering, release authorization, or provider integrations.

## Try the included example

Python 3.10+ and its standard library are sufficient. Run from this repository:

```bash
python3 scripts/media_kit.py pack \
  --project examples/media-kit/project.json \
  --root . \
  --output /tmp/quirk-media-kit-demo.zip

python3 scripts/media_kit.py verify /tmp/quirk-media-kit-demo.zip
```

Use a new output filename for subsequent runs. Existing output files are preserved. The output directory must support hard links, used to place a fully verified ZIP without an overwrite race.

Extract the ZIP into one folder and open `index.html`. Keep `assets/`, `kit-manifest.json`, and the page together. No server, account, scripts, or network connection is needed to read it. Run `verify` on the ZIP after transport; the HTML page is a readable view, not a live integrity check.

The example contains the repository’s existing multimedia design and two new agent-written adaptations: an inspection card and a short summary. The agent selected the card for a private trial. **Bryan has not accepted the choice or reported a benefit.** It is not a completed BryMinn release kit; no source track was supplied in this conversation.

## Make a kit from your own files

Copy `examples/media-kit/project.json` into a new project file and replace its project details, sources, derivatives, and selection. The [project schema](../../schemas/media-kit-project.schema.json) is the complete field contract.

1. Set an explicit `--root` containing the intended files. The tool reads only declared paths and performs no directory scan.
2. Record every source’s identity, version, capture reference, current SHA-256, declared status, and rights note. A capture reference records where bytes came from; it is not approval evidence.
3. Record each derivative’s path, SHA-256, `source_id`, and existing `media-derivative.v1` metadata. Its source object, version, and receipt must match the included source exactly.
4. Choose one included derivative. Record the rationale, a completion condition, and whether the person entering the record is a human or agent. Actor identity remains self-declared and unsigned.
5. Pack, transport, reopen, and verify. If a file changes, inspect it, deliberately update its version/pin and affected bindings, then produce a new kit. Keep the prior kit as history.

Compute a file fingerprint without installing anything:

```bash
python3 -c 'import hashlib,pathlib; p=pathlib.Path("PATH_TO_FILE"); print(hashlib.file_digest(p.open("rb"), "sha256").hexdigest())'
```

That convenience command requires Python 3.11+; on Python 3.10 use `hashlib.sha256(p.read_bytes()).hexdigest()` instead.

Use relative paths with letters, numbers, spaces, dots, underscores, hyphens, and `/`. The packer rejects traversal, symlinks, URLs, drive paths, active HTML/SVG/script files, duplicate IDs, and repeated paths. It accepts common image/audio/video formats, text, Markdown, JSON, captions, and PDF. It does not inspect the semantic contents or safety of the included media.

## Contract and lifecycle

| Object | Meaning and boundary |
|---|---|
| `media-kit-project.v1` | Local candidate input: sources, derivatives, pins, and unsigned selection. Its schema strictly limits authority to candidate and all protected-effect flags to false. |
| `media-derivative.v1` | Existing repository contract, retained without changes. The kit accepts only `draft` or `review`, and rejects a `release_receipt_ref`. |
| `media-kit.v1` | ZIP manifest containing the complete input and exact included-file inventory, with project and content fingerprints. |
| `media-kit-check.v1` | A local pack/verify result. Success means package consistency only. It records open rights/accessibility reviews and leaves human benefit unobserved. |

The inherited field name `canonical_source` is preserved for compatibility. **It does not make the source canonical.** `source_status` is an explicit declaration, and neither it nor `source_permissions_verified` authenticates authority or rights. Source version references are checked for internal agreement, not against a remote repository’s latest head. No external URLs are fetched.

Opaque receipt, license, evaluation, and accessibility references are retained in the metadata; their targets are not automatically bundled or resolved. Included source bytes and their pins can be inspected offline. Full transitive receipt/rights verification remains a separate obligation.

Each derivative has one primary source in v1. Multi-source derivatives, source revocation monitoring, distributed signatures, render jobs, caption verification, and integration with Quirk Now or a custody service remain open. Unknown kit/tool versions are rejected; future format or meaning changes need explicit migration and replay fixtures. Existing kits are never silently rewritten.

The local shape checker enforces only the audited JSON Schema subset used by the two bundled schemas. It resolves their known local reference and rejects unsupported encountered keywords/references. It is deliberately not offered as a general JSON Schema validator. The media-kit profile additionally bounds strings and arrays and requires nonblank required text. No package installation or remote schema resolution is involved.

## Integrity and limits

- A kit accepts at most 32 sources and 32 derivatives, 64 MiB per file and 128 MiB of files in total. Project and manifest JSON and the generated page are bounded to 1 MiB each.
- JSON duplicate keys, non-finite numbers, malformed manifests, ZIP duplicate names, special files, unexpected members, and excessive sizes are rejected.
- The verifier never extracts or executes archive contents. It checks the inventory, byte pins, source bindings, selected derivative, and regenerated HTML before returning success.
- Identical inputs produce byte-identical ZIPs. Fingerprints bind the choice and files together, but an unsigned kit can be coherently rewritten and rehashed by another party. **Integrity is not authenticated authorship.**
- The local file guard prevents ordinary path escapes and symlink capture. It is not a sandbox against another process actively replacing filesystem components during a run.
- Errors return a nonzero status and an actionable message. Failed pack attempts leave no final ZIP; existing kits are never replaced. Retry with corrected inputs and a new output name. Rollback is discarding the new local candidate ZIP or reverting the candidate implementation commit.
- Runtime authority remains candidate-only: no publishing, Preference Graph application, training permission, or canon promotion. Successful tests do not resolve the Golden Pack’s admission holds.

## Smallest human-use proof

Give the example kit to the operator without narrating its family tree. Ask them to find the source, identify the selected version, explain the recorded reason, and identify one open review. Then ask: **“Did this help you finish the inspection? What did you still have to reconstruct?”**

Record their actual words, completion/failure, assistance required, and keep/mutate/drop choice in a new dated receipt bound to the kit fingerprint. Do not overwrite the agent’s proposal or infer an acceptance, time saving, release approval, or Preference Graph update.

The first intended beneficiary is Bryan assembling and reopening media work; the second is a collaborator receiving the kit. File recovery and rejection behavior can be demonstrated mechanically. Their task success and saved effort require observation.

## Verification and learning

```bash
python3 -m unittest discover -s tests -p 'test_media_kit.py' -v
python3 scripts/validate_golden_pack.py
```

The focused CI workflow runs the kit tests and packs/reopens the repository example. The existing Golden gate remains separate. See [the receipt](RECEIPT.md) for inspected sources, evidence, unresolved work, and the reusable method.
