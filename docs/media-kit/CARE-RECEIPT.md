# Quirk Media — care refinement receipt

Status: **CANDIDATE** · Actor: **agent.codex** · Toolkit: **0.2.0**

## Decision and implementation

The existing kit preserves source bytes, alternatives, and an unsigned choice. It did not describe an asset's readable name, maintenance state, sensitivity, or artistic intent, nor inspect included accessibility companions. This pass adds one optional care layer around that same kit: a classification/service registry, a strict care contract, a read-only inspector, a saved review page, and replay/boundary fixtures.

The user's request covered naming and classification, handling, management, maintenance, security, services, artifacts, assets, and artistry. The bounded decision was to make those distinctions usable in one local care inspection. It does not build four editors or introduce a second asset database.

## Sources brought forward

| Source | Inspected state | Treatment |
|---|---|---|
| Draft PR #78, `Quirk-Systems/quirk-os` | Head `f38bc0b9e5bebe5d28196568e8ef3880e05274ce`; open/draft; the three existing CI workflows passed at that head. | Extend the same candidate work. Later head/CI results are reported separately after the new commit. |
| `scripts/media_kit.py`, its tests and project schema | The 0.1.0 implementation at that head. | Preserve source/derivative/selection behavior; add explicit legacy reading and owner-only outer ZIP permissions. |
| `schemas/media-derivative.schema.json` | SHA-256 `d96497a86b90c5f39d44dcd1fc683e5ffb58dcd6c9776a8c0c1993b28edf0076`. | Keep the existing identity and provenance contract unchanged. |
| Original kit ZIP | SHA-256 `a564466df56a5fbfb2287c2dad07573743157cf4dabe17a90da7e09aacc8a514`. | Copy the original bytes to `examples/media-kit/legacy-v0.1.0.zip`; verify rather than regenerate the fixture. |
| Existing source design and two adaptations | Same three byte pins and project input as the prior kit. | Preserve originals; add human titles and care declarations in a separate record. |
| The previous six media labels and present user request | Candidate vocabulary, not implemented production workspaces or a human acceptance record. | Define Visuals, Video, Presentations, Audio, plus Photography, Quick Picks, and Podcasts as modes; retain earlier names as aliases. |

The original [RECEIPT.md](RECEIPT.md) and [EVIDENCE.json](EVIDENCE.json) remain historical evidence and are not rewritten to claim this pass's results. This pass's exact behavior-file hashes and command outputs are in [CARE-EVIDENCE.json](CARE-EVIDENCE.json).

## What became better

| Area | Concrete change | Evidence or limit |
|---|---|---|
| Naming/classification | Separate workspace, family, origin, use role, sensitivity, and care state. Human titles can change without changing IDs or source bytes. | Rename preservation, ambiguous title, and classification mismatch fixtures. |
| Handling/assets/artifacts | Bind care to every exact included asset; keep artifact outputs distinct from reusable assets. Add explicit opaque custody for presentation and additional photo/audio formats. | Missing/duplicate/unknown inventory rejection; PPTX/ODP custody tests use synthetic opaque bytes and prove no rendering claim. |
| Management/maintenance | Expose unassigned ownership, due dates, withdrawal, supersession, primary-source and companion dependencies. | Date, replacement-cycle, withdrawal, and transitive companion-source fixtures. The tool neither assigns a person nor changes/deletes a file. |
| Security | Use owner-only POSIX outer-file permissions; inspect through one open verified archive; reject remote/missing/self companion targets. | Permissive-umask and hostile reference tests. No encryption, malware scan, authenticated identity, or transfer ACL is claimed. |
| Services | Mark package/verify/inspect as implemented local operations; distinguish human craft review and proposed services. | Machine-readable service registry. No provider, background job, or publish integration. |
| Artistry | Record intent, what to preserve/avoid, and questions for the actual medium. Add a readable care review that names the selected piece. | Text/HTML structure and escaping checked; human taste, usefulness, and visual/device review remain unobserved. |

## Result and beneficiaries

The example has **six findings** as of **2026-09-10**: one missing maintenance owner, one unknown source origin, and rights/accessibility reviews for each of the two adaptations. This is an actionable inventory of recorded gaps, not evidence that the underlying work is unsafe or bad. A source origin and a person's acceptance must be established from evidence outside the packer's declarations.

The final focused run has **68 passing tests**: the original 39 plus 29 care/compatibility tests. The Golden candidate gate passes with **all 16 admission holds intact**. The original 0.1.0 ZIP reopens without changing bytes. Toolkit 0.2.0 produces a new, reproducible kit with the same three included assets and unchanged project fingerprint.

**Observed mechanical benefit:** the generated review contains readable names and a dated care inventory with the chosen work. A changed title leaves identity and originals intact. Missing review material is detected, and adding a valid included transcript removes only the missing-material finding; it cannot manufacture accessibility quality or human approval. A selected asset is flagged when a companion's source is withdrawn.

**Intended human beneficiaries:** Bryan comparing and reopening media work, a collaborator receiving it, and the eventual maintenance owner. **Not observed:** their task completion, time saved, acceptance, artistic preference, or independent reuse. No person is claimed to have benefited from passing tests alone.

## Open work, recovery, and next move

- The example is still a repository design and two text adaptations. No source track, production photograph, video, deck, or podcast was supplied. Media decoding and actual production quality remain untested; custody fixtures do not stand in for them.
- Rights, accessibility quality, source authenticity, maintenance-owner acceptance, and human judgment remain open. Classification and sensitivity are self-declared. Unknown provenance is retained explicitly.
- Browser visual/device review remains unverified. The earlier local preview route returned `net::ERR_BLOCKED_BY_CLIENT`; it was not bypassed. The new report is checked structurally and for escaping, with no claim of a rendered visual review.
- Local verification uses the Python standard library. The earlier automatic rejection of third-party dependency installation was respected; no installation was retried. Remote CI results must be checked at the new PR head before claiming them.
- A care record targets a single kit. Wrong bindings and malformed records fail; old records, sources, and kits are preserved. Repair consists of deliberate inspection, corrected declarations/pins, and new outputs. Discard the new candidate outputs or revert this refinement commit to roll back. No source renaming, automatic supersession, scheduling, deletion, publication, training, Preference Graph application, or canon promotion occurred.

**Next Proposed Move:** a person opens the kit and care page, finds the selected version and one review issue, compares the card with the summary, and records what they could finish and what they still had to reconstruct. Keep the direction if the combined view helps them complete that inspection; mutate the names or care view where it causes confusion; drop parts that add handling without a useful outcome. Preserve their words in a new dated receipt bound to the kit and care fingerprints.

## Learning carried forward

**Reusable method candidate:** keep identity stable → distinguish workspaces from classification → bind care to exact bytes → follow declared dependencies → separate presence checks from quality judgment → ask a person what helped → retain the answer with the next version.

The useful implementation lesson is that an accessible companion may carry its own source dependency. Checking only the chosen file's direct source misses that obligation. The transitive companion-source fixture preserves this discovery. Successful inspections still cannot promote their own authority; the self-promotion denial remains executable. No skill, Preference Graph, or canonical instruction was changed.
