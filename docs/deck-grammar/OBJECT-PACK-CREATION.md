# Object Pack creation: typed source, inspectable preview

Status: **candidate implementation**. Owner: `Quirk-Systems/quirk-os`. Base inspected: `499f94b8d12e29dd7804cc9b537fd70f6a8048d8`, 10 September 2026. Quality decision: **Constrain** to local candidate-pack creation. This does not admit an object, install a skill, or authorize runtime effects.

## Decision and purpose

The original emitter inserted arbitrary strings into YAML source, silently assigned `human.bryan` when owner was omitted, and accepted unrestricted status/ceiling strings. These behaviors made ordinary titles capable of corrupting the manifest and made scaffolding look more authoritative than its evidence justified.

Preserve the eleven-module interface and existing registry. Move compilation into the reusable `scripts/object_pack.py`; retain `scripts/scaffold_quirk_object_pack.py` as the CLI. Build structured YAML/front matter from parsed string slots, validate the emitted documents, and publish the compiled files only after all checks pass.

The alternative of escaping only YAML quotes was rejected: it would not cover front matter, multiline strings, duplicate keys, identity drift, or status/ceiling claims. A general variable engine is deliberately deferred. This slice has six typed inputs and no external observations, derivations, stored preferences, or secrets.

## Contract and compatibility

- Input: kind or registry alias, namespaced object ID, title, explicit owner ref, candidate status, and one of `observe`, `infer`, `propose`.
- Output: exactly eleven UTF-8 modules. The four YAML modules and Skill front matter validate against `schemas/object-pack-creation.schema.json`; the compiler additionally checks identity, owner, subject, and equal-ceiling bindings.
- YAML source uses the existing `{{NAME}}` notation. The compiler substitutes neutral markers before parsing, then binds supplied strings into scalar values once. Values do not become keys, syntax, or another template expansion stage. The data-only parser rejects duplicates, aliases, unsupported tags, and malformed sources.
- Markdown body titles are escaped and collapsed to one display line. Exact supplied text remains in the manifest and description front matter. Escaping is syntax containment, not a claim that arbitrary natural-language text cannot influence an agent.
- Ordinary SETTINGS precedence stays `explicit_current > purpose_scoped > admitted_project > admitted_global > default`. This generator does not implement preference resolution or effect authorization.
- Breaking changes: owner omission is refused; non-candidate status and executable ceilings are refused; YAML formatting is normalized; malformed inputs/templates now return a controlled failure. Existing content is never migrated or overwritten.
- Caller contract: `--repo` points to reviewed local source. Schemas/templates are not authenticated by the compiler. Hashes bind inspected bytes and versions; they are unsigned, do not prove truth/admission, and use a local JSON convention rather than RFC 8785.

## Agent and Python use

Use explicit arguments or call the pure compiler. Never build shell source by interpolating a title. The checked-in example is consumed in the focused test suite:

```python
import json
from pathlib import Path
import sys

repo = Path.cwd()  # Run from the repository root.
sys.path.insert(0, str(repo / "scripts"))
from object_pack import compile_pack

inputs = json.loads((repo / "examples/deck-grammar/object-pack-input.json").read_text())
files, preview = compile_pack(repo, inputs)
print(preview["content_sha256"])
print(preview["files"])
```

`compile_pack` performs no writes. For publication, use the CLI with an explicit destination and the preview digest; the CLI validates again and then stages the complete pack. A future runtime consumer can reuse this function without importing CLI argument parsing. It must supply its own actual scope/identity checks before consequential downstream actions.

## Failure and recovery

Invalid input, template/schema mismatch, source drift relative to an expected preview, a symlink destination, or a populated destination blocks publication. A staged write failure or failed final rename cleans the temporary stage. A destination populated by another writer during staging is retained. The supported publication proof is POSIX same-filesystem directory rename; network filesystems, Windows replacement of an empty directory, power loss, and hostile parent-directory races remain unproved.

Preview changes no directories. Publication may create missing parent directories, and those empty parents can remain after failure. The final pack receives the private staging directory's permissions. A stdout-reporting failure after a successful rename returns a distinct status and says the pack was written. Inspect it before retrying. To revise a pack, choose a new destination and preserve the previous version; do not treat this creator as an in-place editor.

Rollback of this code change is a normal revert on its candidate branch. Generated artifacts already created remain user-owned source and are not deleted by that revert. No database migration or existing-file regeneration is required.

## Proof and compounding value

The focused suite exercises real compiler/CLI paths: all registry kinds and aliases; quoted/multiline/template-looking titles; explicit ownership; typed input refusal; lower-ceiling positive controls; self-promotion refusals; source/identity drift; duplicate/alias/tag refusal; preview-to-write hashes; destination preservation; staged-write and finalization failures; and report failure after successful publication. The existing Deck Grammar tests and conformance command remain regression checks.

These observations establish the scoped creation behavior, not independent human usefulness or runtime safety. The reusable deposit is `compile_pack(repo, inputs)`, the creation schema, and a preview/write digest contract consumed by the existing CLI. The next useful move is a thin Quirk Now caller that supplies a real user's chosen object inputs, exports the candidate pack, reopens it, and asks whether it reduced their reconstruction effort.

The implementation evidence and exact validation commands are recorded in [Object Pack creation evidence](../../evals/deck-grammar/object-pack-creation-evidence.json).
