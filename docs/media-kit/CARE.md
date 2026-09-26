# Quirk Media — names, care, and craft

Status: **CANDIDATE** · Toolkit: **0.2.0** · Existing owner: **Quirk Media within Quirk Creation + Quirk Asset**

Keep one identity for each source or derivative. Describe its purpose clearly, inspect what it depends on, and carry forward the questions a person still needs to answer. The implemented addition is a care record and a local inspector for the existing portable kit.

## Names that describe different things

| Earlier label | Workspace | Focused mode | Meaning |
|---|---|---|---|
| Quirk Images | **Quirk Visuals** | General visual work | Images are a media family; visuals is the work surface. |
| Quirk Pics | **Quirk Visuals** | **Quick Picks** | Collect, compare, and choose; no second image collection. |
| Quirk Photos | **Quirk Visuals** | **Photography** | Capture and photographic edits; origin is declared, never inferred from a filename. |
| Quirk Videos | **Quirk Video** | — | Moving-image work. |
| Quirk Presentations | **Quirk Presentations** | — | Slides and sequences that help an audience understand or decide. |
| Quirk Podcasts | **Quirk Audio** | **Podcasts** | Episodes and segments within audio work. |

**Quirk Media** remains the umbrella. Earlier labels are retained as aliases in [classification.v1.json](classification.v1.json). These are candidate vocabulary and routing definitions; four production applications have not been built. Quirk Music retains its craft/domain ownership; Audio does not rename or take over that domain.

Workspace, media family, origin, use, sensitivity, and current care state are independent. A generated image can be a reference in a presentation; a photograph can be an accessibility source; an audio file need not be a podcast. PDF is classified by its document container even when it is an exported presentation. The derivative's existing `medium` still describes its expression or purpose.

## Name the work without breaking its history

| Field or object | Rule | Example |
|---|---|---|
| Asset identity | Reuse the existing `src_…` or `qmd_…` ID across labels and workspaces. | `qmd_source_first_card` |
| Human title | State the subject and job. Add a distinguishing version or purpose if another asset has the same title. | `Find the source — inspection card` |
| Source or derivative path | Preserve the original path and bytes in the kit's manifest; a new care title does not rename either. | `examples/media-kit/source-first-card.md` |
| File/media family | Declare image, video, audio, presentation, document, data, or unknown. Compare it with extension evidence. | `document` |
| Origin | Declare captured, authored, generated, mixed, or unknown; retain provenance separately. | `generated` for the two agent-written adaptations |
| Use role | Reference, master, working, delivery candidate, or accessibility companion; independent of source/derivative provenance role. | `working` |
| Asset | An included reusable source or derivative, with stable identity and a byte pin. | The inspection card |
| Artifact | An operation's output: kit, manifest, readable view, inspection report, or review bundle. | `Quirk-Media-Care-v0.2.0.zip` |
| Artifact filename | Use the project/purpose and an explicit version; add a date when useful. This is a convention, not an enforced renamer. | `Quirk-Media-Kit-v0.2.0.zip` |

An artifact may later become a source asset when deliberately collected for a new purpose. That requires a source record and provenance; merely displaying it in another workspace creates no new identity. No separate asset database or global deduplication service is introduced here.

## Inspect care against the exact kit

From the repository, after packaging the example using toolkit 0.2.0:

```bash
python3 scripts/media_care.py inspect /tmp/quirk-media-kit-demo.zip \
  --care examples/media-kit/care.json \
  --as-of 2026-09-10 \
  --html /tmp/quirk-media-care-2026-09-10.html
```

Use a new report filename on another run. `--as-of` is mandatory so the same inputs have the same result. Set it to the date you actually want to inspect. A review date is a declaration for a manual check; this command schedules nothing.

The [care schema](../../schemas/media-care.schema.json) covers every included asset exactly once. Its fingerprint binding must match the kit. Changing a source, selection, or toolkit-produced kit requires deliberate inspection and rebinding; care is never silently moved to different bytes. The output binds the exact kit, canonical care record, and classification registry by SHA-256. Registry meaning changes require a new version and replay evidence.

The inspector returns JSON with findings and, optionally, a static HTML report. Exit 0 means inspection completed, including when `status` is `needs_attention`; exit 1 means invalid input, failed verification, or failed output. `prepared_for_human_review` means the mechanical care checks found no issue. It does not approve a release. Any caller must inspect `status`, findings, and scope; exit status is not authorization.

## Handling, management, and maintenance

1. **Collect deliberately.** Name only intended local files in the existing project. Keep originals and source pins. The tool does not scan folders, rename originals, or execute included files.
2. **Describe the assets.** Give each a readable title, declared family, origin, use role, and sensitivity. Duplicate titles and disagreements with file extensions become findings.
3. **Name a caretaker.** Use `maintenance_owner: "unassigned"` until someone is nominated. A different name remains a declaration; acceptance evidence belongs in a separate human receipt.
4. **Review use over time.** Record `review_on` and a reason for the current state. Dates on or before the inspection date are due. No expiry causes deletion, reclassification, or automatic replacement.
5. **Follow dependencies.** A source needing care flags its derivatives. The selection's review scope follows primary sources and accessibility companions, including a companion's source. It does not discover undeclared or remote dependencies.
6. **Keep history.** Superseded assets require an included replacement, with no missing links, self-links, or cycles. The inspector retains the original selection and flags it; it never switches to the replacement. Withdrawn assets remain in the archive for traceability and receive a finding.
7. **Carry learning.** Preserve the previous kit and care record. Capture a person's exact response, any assistance needed, and a keep/mutate/drop choice in a new dated receipt tied to the fingerprints.

Care states are `candidate`, `review_needed`, `superseded`, and `withdrawn`. They annotate handling; they do not alter the underlying derivative's admission status. There is no automatic deletion, retention enforcement, background monitoring, provider job, or repair operation.

## Security and accessible review

New outer ZIPs and HTML reports use owner-only POSIX permissions, even under a permissive umask. Existing outputs are preserved through exclusive creation. This does not encrypt a kit, establish access control after transfer, or change the permissions a viewer uses when extracting files. Sensitivity is a declaration; anything other than public is flagged for a storage/sharing decision. Public sensitivity does not establish redistribution rights.

The existing bounds remain: 64 MiB per included file, 128 MiB total, at most 64 assets, and 1 MiB for JSON and generated pages. New custody support includes PPTX/ODP, TIFF, HEIC/HEIF/AVIF, AAC, and AIFF. Like the earlier media support, these bytes are carried opaquely. A recognized extension does not prove file type, decoding, renderability, safety, or provenance. Macro-enabled presentation extensions and general active HTML/SVG/script sources remain outside the allowlist; allowed containers are not inspected for embedded code, objects, or external links.

The inspector verifies the ZIP and reads companions through the same open archive handle. It never extracts files, fetches a reference, decodes media, or runs embedded code. The local file guards are not a sandbox against hostile concurrent filesystem mutation. The HTML report escapes user text, has no scripts, and permits no external resource loading. Its recorded fingerprints and claims are unsigned, as is the kit.

| Family | Material requested for review | What remains a person's task |
|---|---|---|
| Image | Declared alt text | Relevance, accuracy, visual meaning, and whether description is appropriate. |
| Video | Included captions and transcript | Timing, speaker identification, sound cues, readability, and need for audio description. |
| Audio | Included transcript | Fidelity, speaker identification, useful structure, and access to meaningful sound. |
| Presentation | Included speaker notes | Reading order, visual descriptions, pacing, contrast, and audience understanding. |
| Document/data | No blanket companion requirement | Structure and applicability in context; PDF still receives a viewer review finding. |

Captions must reference an included SRT/VTT asset. Transcripts, speaker notes, and optional audio-description scripts must reference included TXT/Markdown assets. The inspector checks nonempty UTF-8 text, allowed extension, and a 1 MiB limit; it does not parse caption timing or establish content fidelity. Absent, unusable, withdrawn, or overdue companions remain findings. A misleading family declaration cannot hide extension-based material requirements. Applicability exceptions belong in a separate human review; this candidate inspector cannot approve a waiver.

## Services with honest boundaries

The machine-readable service inventory is in [classification.v1.json](classification.v1.json). Its entrypoint strings are documentation, never commands executed from registry data.

| Service | Current implementation |
|---|---|
| Package | Local deterministic candidate ZIP creation. |
| Verify | Local inventory, binding, byte, and readable-view consistency checks. |
| Inspect care | Local classification, dependency, maintenance, sharing, and companion findings. |
| Craft review | Human task; a machine cannot award acceptance or taste. |
| Create/edit/render, transcribe/caption, catalog/schedule, publish/deliver | Proposed services; no integrations or production workspaces implemented here. |

## Artistry has its own evidence

Each care record includes an intent, what to preserve, what to avoid, and specific craft questions. Keep an alternative that makes a meaningful difference. Preserve the source's distinctive expression where it serves the work. Review the actual piece in its medium before judging it.

| Surface | Useful craft question |
|---|---|
| Visuals / Photography | What does the crop, light, color, texture, or moment make us notice or miss? |
| Quick Picks | Which selection serves this purpose, and what useful alternative would disappear? |
| Video | Where do sequence, pacing, motion, and sound clarify or weaken the intended experience? |
| Presentations | Can the audience follow the argument and know what to do next? |
| Audio / Podcasts | Do voice, silence, sound, and structure make the story or explanation worth hearing? |

The example care record adds a concrete intent and three questions to the existing inspection-card/summary comparison. It does not invent a human preference. `human_judgment` and `human_benefit` remain unobserved in machine output, even when every mechanical finding is resolved.

## Compatibility and next proof

Toolkit 0.2.0 writes the existing `media-kit.v1` format and reads both 0.1.0 and 0.2.0 tool versions. The original 0.1.0 ZIP is preserved as [a replay fixture](../../examples/media-kit/legacy-v0.1.0.zip); its bytes and content fingerprint remain unchanged. A new care record is optional and external to the verified kit. Older tools can still verify their old kits; they will reject new tool versions explicitly.

Observed mechanical improvement: readable names no longer require identity changes; invalid care bindings and dependencies are detected; the example exposes six care findings. Intended beneficiaries are Bryan choosing/reopening work, a collaborator receiving it, and the person maintaining it. Human usefulness, time saved, craft quality, and visual/device usability have not been observed.

Next proof: let a person open the kit and care report, identify the selected version and one care issue, compare the two adaptations, and explain what helped or still needed reconstruction. Record their words and decision without replacing this agent proposal. See [CARE-RECEIPT.md](CARE-RECEIPT.md) for this pass's evidence and unresolved work.
