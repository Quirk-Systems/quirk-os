# Quirk Object Pack Templates

Create eleven consistent candidate source modules from explicit identity, ownership, and a title. The compiler validates the whole pack before writing it. Supported object families may have admitted definitions, but every newly generated pack starts as a candidate.

## Supported object kinds

`chatbot`, `platform`, `system`, `repository`, `prompt`, `chain`, `workflow`, `sequence`, `tool`, `evaluation`, `harness`, `automation`, `bot`, `content`, `slate`, `argument_set`, `permutation_set`, `plugin`, `capability`, `skill`, `agent`, `product`, `service`, and `revenue_stream`.

## Generated modules

Every pack starts with the same inspectable modules:

1. `MANIFEST.yaml`
2. `README.md`
3. `REPO-MANAGEMENT.md`
4. `SYSTEM-PROMPT.md`
5. `CUSTOM-INSTRUCTIONS.md`
6. `SETTINGS.yaml`
7. `PROJECT-INSTRUCTIONS.md`
8. `REFERENCES.md`
9. `SKILL.md`
10. `EVALS.yaml`
11. `OPERATING-WORKFLOW.yaml`

A module may state “not applicable,” but it may not silently disappear. This makes absence deliberate and reviewable.

## Preview, then create

Use Python 3.10 or later and the repository's pinned evaluation dependencies:

```bash
python -m pip install -r requirements-evals.txt
```

From the repository root, preview without creating files or directories:

```bash
python scripts/scaffold_quirk_object_pack.py \
  --kind agent \
  --id agent.example \
  --title "Example Agent" \
  --owner human.bryan \
  --output /tmp/agent-example \
  --dry-run --json
```

The preview reports the resolved kind, explicit owner, candidate ceiling, eleven output hashes, source hashes, and a `content_sha256`. Remove `--dry-run` to write. To bind the write to the preview, add `--expect-content-sha256` with the returned digest; changed inputs, templates, schema, compiler, or named dependencies then require a new preview. This digest binds content, not the output path, authorization, or preview/write action. Keep any saved report outside the destination directory.

`--owner` is required. `--status` accepts only `candidate`; `--authority-ceiling` accepts `observe`, `infer`, or `propose`. These fields are declarations, not grants or verified identities. Namespaced IDs such as `agent.example` and owner refs such as `human.bryan` are required. An alias such as `agents` resolves through the existing registry.

`--dry-run` alone retains the original filename-list output. `--json` provides a machine-readable preview/write report. A successful write produces exactly the eleven modules above; its report goes to stdout. Exit `0` means success, `2` means refused input/source/destination or failed publication, and `4` means compilation/publication completed but stdout reporting failed. Argument syntax errors use argparse's standard text output.

Quotes, line breaks, YAML-looking text, and template-looking text in a title remain data in YAML and Skill front matter. Markdown titles use a single escaped display line. No shell, code, secret retrieval, recursive variable evaluation, or remote schema fetching occurs during compilation. Treat the repository templates and schema as reviewed local source; this is not a hostile-code sandbox.

The destination must be absent or an empty directory, never a symlink or populated directory. Files are staged beside it before a single directory rename. On the supported POSIX path, an existing empty directory is replaced as a directory; the staging directory's private permissions become the pack permissions. Failed staging/finalization is cleaned up and cannot report a completed pack. This is not crash-durable storage or protection against hostile concurrent replacement of parent directories. If stdout fails after publication, inspect the existing output rather than blindly retrying.

The generated pack is an authoring scaffold: purpose, detailed contracts, and real evaluations still need to be authored. `validation: passed` means the creation contract and cross-file bindings passed, not that those future contents exist or are useful. `SKILL.md` is an object-pack module, not proof of host-compatible installation. The generator does not register, activate, deploy, or canonize an object.

For reusable Python/agent use and the decision record, see [Object Pack creation](../../docs/deck-grammar/OBJECT-PACK-CREATION.md). Run the affected checks with:

```bash
python -m unittest discover -s tests -p 'test_object_pack.py' -v
python -m unittest discover -s tests -p 'test_deck_grammar.py' -v
```
