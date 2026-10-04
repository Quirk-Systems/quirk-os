# Quirk Media Kit — improvement receipt

Status: **CANDIDATE** · Actor: **agent.codex** · Owner: **Quirk Media / Quirk Creation + Quirk Asset**

## What changed and why

The inspected Quirk OS media contract records source references and derivative metadata. It does not carry the referenced files or an unsigned version choice. This pass adds a local ZIP packer/verifier, a readable origin view, a candidate project contract, an example, focused tests, and CI. The existing `media-derivative.v1` schema and Golden admission policy are unchanged.

The intended outcome is that Bryan or a collaborator can reopen a media family and recover its source, alternatives, selected version, rationale, and completion condition without reconstructing the relationship from scattered files.

## Mission and source census

The user asked to bring existing work forward, make one worthwhile change, show who benefited, and carry the learning forward. Scope for this pass: read existing sources; make a reversible candidate implementation; produce a private example; verify packaging and failure behavior. Stop after a reproducible local proof and a reviewable candidate change. Publishing media, applying preferences, training, modifying source material, resolving admission holds, or asserting human acceptance is outside this pass.

| Source | Inspection and classification | Use |
|---|---|---|
| `docs/golden-project-pack/MULTIMEDIA-MULTIPLIZIERT.md` | Inspected at `499f94b8d12e29dd7804cc9b537fd70f6a8048d8`; SHA-256 `1de3f133e2405bdd32d34d611ed225dd584d4b6b7e234d84656d654b10598686`; candidate design, marked PROPOSED. | Source preservation, added affordance, origin inspection, and explicit rights/accessibility reviews. Original bytes are included in the example. |
| `schemas/media-derivative.schema.json` | Same commit; SHA-256 `d96497a86b90c5f39d44dcd1fc683e5ffb58dcd6c9776a8c0c1993b28edf0076`; existing repository input contract. | Retained unchanged and consumed by the candidate kit profile. |
| `docs/golden-project-pack/ADMISSION.md` | Same commit; inspected governing distinction between candidate preservation and Golden admission. | Preserve all admission holds; successful packing grants no rights. |
| Prior Quirk Media proposal in this conversation | Candidate concept, not an implementation or acceptance record. | The source shelf, version choice, and release-kit portability problem. |
| July master document inspected earlier in this conversation | Historical candidate design; current repository implementation is checked independently. | Establishes that Quirk Media was already named; does not prove a deployed product. |

The `Quirk-Systems/quirk-media` lookup returned 404 through the available connector. That establishes neither repository absence nor a reason to create another repository. The working media contract and relevant design were found in `Quirk-Systems/quirk-os` and used there. No canonical status was inferred from a document heading or a repository name.

## Evidence and result

Machine-readable results, measured check durations, exact behavior-file hashes, limitations, and the kit verification receipt are in [EVIDENCE.json](EVIDENCE.json). The base commit above plus those hashes identify the evaluated implementation before commit; the receipt does not claim an independent reviewer.

| Check | Observed result | Practical limit |
|---|---|---|
| Pack and reopen | Original design and two adaptations survived byte-for-byte; the selection and rationale were preserved. | A repository example, not a real music release. |
| Matched source-byte control | The existing metadata shape parses while the kit rejects a stale source SHA-256. | Demonstrates an added packaging check, not source truth or rights. |
| Reproducibility | Identical inputs produced identical ZIP bytes. | Fingerprints are unsigned; a coherent rewrite can be rehashed. |
| Focused tests | 39 passed, including source/version/receipt mismatch, missing files, tampered choice/index, malformed archives, limits, unsafe paths, and rehashed self-promotion. | Bounded fixture evidence; no runtime safety claim. |
| Golden candidate gate | Passed with all 16 Golden-admission holds intact. | No admission, publication, graph application, training, or promotion. |
| Readable view structure | Eight links resolve, no script elements, language and viewport metadata present. | Browser navigation was blocked with `net::ERR_BLOCKED_BY_CLIENT`; visual and device review remain open. |

Example kit content fingerprint: `f76d536e6f46ba3b75672c3411e49a1cb04050dc81957e1fa4f699c7c39a8e0d`.

### Who benefited?

**Observed mechanical benefit:** the package now preserves a reconstructable source-to-derivative relationship and detects the tested loss/change cases on reopen. The operator receives all three files and the exact choice together.

**Intended human beneficiaries:** Bryan preparing media work, and a collaborator receiving it.

**Not observed:** human task completion, time saved, usefulness, acceptance, or independent reuse. The example choice is explicitly agent-authored. No human benefit is inferred from the 39 passing tests.

## Limits, quarantine, and recovery

- Rights and accessibility for the example remain open and are exposed in the kit/check receipt. The kit is for private candidate inspection and is not a release specimen satisfying the existing multimedia admission move.
- The shared schema uses the field name `canonical_source`; the kit does not promote that source. Declared actor, status, rights, and capture references remain unauthenticated.
- Malformed or inconsistent input is rejected before a final output is placed. Existing files are preserved. Unknown versions are rejected. There is no implicit migration or auto-repinning.
- Runtime reads only declared local files. It does not fetch URLs, contact providers, extract untrusted ZIPs, render media, or execute included content.
- Automatic approval review rejected dependency installation. The completed slice and focused verification use Python’s standard library. Broader suites needing external packages were not run locally; the focused CI was added, with remote status reported separately when observed.
- No source track was provided. The BryMinn cover/teaser/release-copy pilot remains open. Source capture/rights receipts, evaluations, and accessibility references are retained as metadata; transitive target verification remains open.
- Rollback: discard the newly produced local candidate kit or revert the candidate code commit. Original sources, prior outputs, admission history, and authority remain preserved.

## Carry the learning forward

**Reusable method candidate:** preserve source bytes → bind metadata to source identity/version/capture → include alternatives → record an unsigned choice with a finish condition → verify after transport → ask the receiving human what still needed reconstruction.

The useful distinction is now executable: a valid metadata reference does not prove the referenced file traveled with the decision. The matched control and the existing schema’s const-only version field are retained as regression evidence rather than lessons requiring oral explanation.

**Next Proposed Move:** run the human-use procedure in [README.md](README.md) on this exact kit, then record the person’s words and a keep/mutate/drop decision. Continue if the operator completes the inspection without source reconstruction; mutate if missing context still requires assistance; drop this packaging direction if it adds handling without helping complete the task. Reuse of the method is a candidate proposal; no skill installation or Preference Graph update was made.
