# ADR-0003 — manifest content-hash preimage

**Repository path:** `decisions/ADR-0003-manifest-content-hash-preimage.md`  
**Status:** Approved design; implementation remains candidate  
**Owner:** Bryan Sayler  
**Date:** 2026-10-04  
**Authority effect:** design decision only; no runtime admission  
**Scope:** `runtime-manifest.v2` manifest `content_hash` only; pair with ADR-0002  
**Basis:** PR #113 at `d9443d713bb532e00d0d16e692509c2519457d3e`

## Decision

Define hash profile `runtime-manifest-content.v1`: SHA-256 of UTF-8 canonical JSON for the following explicitly allowed top-level fields **when present**. Validate the manifest shape before extraction; reject unknown fields rather than silently excluding them.

| Covered fields | Treatment |
| --- | --- |
| `schema_version`, `manifest_key`, `manifest_kind`, `version`, `canonical_uri` | Identity and source binding |
| `authority_ceiling`, `domains`, `tools` | Capability and scope, including every nested tool field |
| `inputs_schema_ref`, `outputs_schema_ref` | Input/output contract references |
| `eval_refs`, `skill_refs`, `stop_conditions` | Evaluation references, composition and stops |
| `rights_review`, `trigger_contract` | Every supplied review/routing field and nested evidence reference |
| `metadata` | Entire recursive value; no key allow-list or mutable annotation exception |

| Excluded fields | Reason / separate enforcement |
| --- | --- |
| `content_hash` | Self-reference; require declared value to equal computed digest |
| `admission` | Approval/evaluation envelope; externally resolve and verify under ADR-0002 |
| `status` | Current lifecycle state; compare actual state and legal transition, not merely manifest text |
| `requested_status` | Requested lifecycle operation; must match the explicitly approved transition |

The schema presently has no remaining top-level fields. Changing the covered field set is a new hash-profile decision, even if the manifest shape does not change. A new schema field must not silently become unhashed.

Changing either status alone leaves the content digest unchanged **and grants no transition permission**. For example, editing `candidate` to `active` cannot reuse approval for a different action, prior state, requester, environment or transition. Preserve current requirements that an active manifest requests active status and passes the structural admission guard. Changing any metadata value changes content identity; runtime display annotations belong in a separate projection envelope until a separately approved schema says otherwise.

## Canonicalization and digest

Use the existing Deck Grammar idiom as a **Python-specific versioned profile**, not a claim of RFC 8785/JCS or PostgreSQL equivalence:

`json.dumps(preimage, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')`, then SHA-256 and lowercase hexadecimal output.

Normative initial serializer: CPython 3.13 standard-library JSON. Strict input ingestion rejects duplicate object keys recursively, NaN/Infinity, invalid Unicode scalars and non-JSON values before dictionary construction/serialization. Do not silently coerce strings to numbers or insert schema defaults. Keep omitted optional fields omitted; omitted, `null`, and an empty collection remain distinct where the schema permits them. Sort object keys recursively, preserve array order, and perform no Unicode normalization. Whitespace in the source document does not affect the digest. Numeric spelling is normalized by this parser/serializer profile; `1` and `1.0` remain distinct Python serialization outcomes. Require committed vectors for Unicode, nested metadata/numbers, absence/null/empty, escaping and array order before another runtime is accepted.

The manifest field remains **bare 64-character lowercase hex**. Do not change or converge the separate `sha256:`-prefixed contracts elsewhere in the repository. Name the profile in the external attestation and verifier configuration, not in untrusted metadata. The profile hashes reference strings, not recursively the bytes of every referenced schema, skill, URL or evaluation artifact. Exact-commit approval and separately validated evidence must bind referenced materials; immutable reference/digest requirements beyond that are separate work. A mutable URI remains a limitation, not proof of immutable content.

## Verification semantics

The trusted Python path computes `H`, requires `manifest.content_hash == H`, requires `admission.evaluated_content_hash == H`, and requires the externally resolved approval subject digest/profile to equal `H`/this profile. Evaluation evidence must actually bind the evaluated subject, not just repeat the author's digest. A computed hash plus a fabricated approval record is still insufficient. Editing a covered field and recomputing both manifest hashes cannot reuse the old authentic approval.

Use one `manifest_content_hash()` implementation across admission, fixture generation and evidence production. The generator is reviewable and committed; tests must independently mutate inputs rather than certify only matching constants. Existing code/fixtures are unchanged by this draft.

## Database and schema consequences

Adopt ADR-0002's single database-boundary decision: **PostgreSQL projects the verified content digest and authentic approval; it does not recompute this Python canonicalization or independently verify approval.** Keep its local structural checks. The protected exact-payload write path, ACL proof and active-update checks are mandatory; the projection cannot become trustworthy merely by writing the same computed digest into two columns.

Keep `runtime-manifest.v2`: selecting a preimage does not add or remove manifest fields. Version the profile as `runtime-manifest-content.v1`, with attestation `manifest-approval-attestation.v1` and admission-policy revision coordinated under ADR-0002. Old v2 fixtures/documents can remain readable as historical data; their placeholder/declaration hashes are not valid admission evidence under the new policy. If a required profile/attestation field is later added to the manifest, introduce v3 rather than smuggling it into metadata.

Regenerate future fixtures through the shared generator after separately authorized implementation. Inventory other repositories and live consumers before migration; compatibility beyond inspected quirk-os files is unknown. Preserve all historical hashes/ledgers. Do not rehash old receipts in place; record corrections and human dispositions separately. Existing active rows without the required content/evaluation/approval binding block cutover pending disposition.

## Later acceptance evidence — not executed by this draft

| Adversarial change | Expected observation |
| --- | --- |
| Change tool actions/scope, authority ceiling, nested metadata, rights/routing contract or any other covered field; retain hashes | Computed-hash failure |
| Change covered content and update both declared hashes | Authentic evaluation/approval subject mismatch |
| Change only `status` or `requested_status` | Digest unchanged; transition still refused unless independently authorized |
| Reorder object keys/change source whitespace | Digest unchanged |
| Reorder an array | Digest changes |
| Add unknown field, duplicate JSON key or nonfinite number | Input refused before hashing |
| Substitute profile or bypass Python through direct SQL/RPC | Trusted-policy or write-boundary refusal |

Require vectors over the current valid fixture and representative metadata before claiming reproducibility. No Python/PostgreSQL digest-parity claim is made under this choice. Choosing an independent database later requires a new shared serialization/body-binding decision and parity/bypass tests; that is not an implementation detail of these ADRs.

## Approval record

**Design approval:** Bryan explicitly approved the recommended pair in this conversation on 2026-10-04: “Approved and Continue Additional Improvements Implemented via Iteratively Integrated and Enhanced Loop Engineering”. The approval also authorizes continued candidate implementation. The transcript supplies no GitHub review ID; this record is not a runtime activation attestation. No merge, deployment, credential provisioning, or live admission is recorded.


