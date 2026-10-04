# HookCandidate Object Contract v0.1

**Status:** Candidate design contract  
**Contract id:** `contract.object.hook-candidate.v0.1`  
**Authority ceiling:** `propose`  
**Executable schema:** none  
**Canon effect:** none

## Purpose

Define the minimum information the workbench must preserve for a versioned hook candidate. `HookCandidate` is a vertical proof object for the operator experience; this document neither promotes it to a canonical Quirk object type nor reserves a runtime name.

## Candidate shape

The notation below is descriptive. It is not JSON Schema, a database model, or a runtime manifest.

```yaml
contract_version: hook-candidate.object.v0.1
contract_posture: documentation_candidate
fixture_role: vertical_test_fixture
authority_ceiling: propose
object_id: hook_candidate.<stable-id>
object_version: <semantic-version>
object_digest: sha256:<candidate-subject-snapshot-digest>
digest_domain: candidate_subject_snapshot
object_type: HookCandidate
fixture_class: synthetic_fixture | human_content | imported_reference | derived_candidate

lifecycle_state:
  value: captured | scoped | composing | review_ready | evaluating | decision_ready | revision_requested | preserved_candidate | rejected | deferred | boneyard | superseded | retired
  changed_by_transition_ref: <transition-id>

last_material_transition_chamber_ref: chamber.<id-or-null>
responsible_human_ref: <actor-ref>

content:
  payload_ref: <content-addressed-ref>
  payload_digest: sha256:<digest>
  language: <bcp-47-tag>
  structural_role: hook | refrain | post_hook | alternate
  visibility: redacted | private | review | release_candidate

intent:
  project_ref: <project-or-song-ref>
  purpose: <bounded-purpose>
  desired_effects: [<effect>]
  prohibited_uses: [<use>]
  constraints: [<constraint-ref>]

origin:
  origin_type: human_supplied | agent_proposed | imported | derived
  creator_actor_refs: [<actor-ref>]
  source_binding_refs: [<source-binding-ref>]
  captured_at: <date-time>
  rights_declaration_ref: <rights-ref>

lineage:
  parent_version_refs: [<object-version-ref>]
  derivation_operation: original_capture | mutation | combination | extraction | translation | restoration
  derivation_actor_refs: [<actor-ref>]
  sibling_version_refs: [<object-version-ref>]
  supersedes_refs: [<object-version-ref>]

evidence:
  active_bundle_refs: [<evidence-bundle-ref>]
  contradiction_refs: [<evidence-ref>]
  evidence_status: missing | partial | sufficient_for_named_decision | stale | disputed

authority:
  applicable_grant_refs: [<grant-ref>]
  authority_status: absent | requested | authorized | denied | expired | revoked
  blocked_powers: [reuse, external_test, release, publication, canon_admission, preference_mutation]

rights:
  status: unknown | fixture_only | claimed | verified | disputed | restricted | expired
  allowed_uses: [<bounded-use>]
  prohibited_uses: [<bounded-use>]
  review_ref: <rights-review-ref-or-null>

risk:
  class: L0 | L1 | L2 | L3 | L4 | L5
  rights_or_safety_impact: <plain-language-impact>
  irreversibility_notes: <notes>

decision:
  status: none | requested | authorized | rejected | deferred | superseded
  decision_ref: <decision-ref-or-null>
  receipt_ref: <receipt-ref-or-null>
  exact_scope: [<scope>]

retention:
  class: ephemeral | working | preserved | boneyard | restricted | scheduled_for_forgetting
  reason: <reason>
  revisit_trigger: <trigger-or-null>
  forgetting_due_at: <date-time-or-null>

created_at: <date-time>
last_material_transition_at: <date-time>
```

## Lifecycle rules

1. The active chamber is workbench/session context, not part of the `HookCandidate` snapshot. `last_material_transition_chamber_ref` records where the last governed material transition was proposed or decided. Navigating to Gallery changes neither lifecycle state, object version, nor digest.
2. `contract_posture`, `fixture_role`, and `authority_ceiling` remain `documentation_candidate`, `vertical_test_fixture`, and `propose`. No lifecycle state upgrades this object into an executable schema, runtime registration, or canonical object type.
3. `object_version` and `object_digest` identify one immutable candidate-subject snapshot: content reference/digest, intent, origin, lineage, rights declaration, and risk declaration. Any material change to those object-owned fields creates a new version and digest.
4. A derived candidate must identify at least one parent version and a derivation operation.
5. `content.payload_digest` identifies the payload bytes; `object_digest` identifies the broader candidate-subject snapshot that refers to that payload. A payload may be redacted from the UI, but both digests and the visibility reason remain inspectable.
6. Lifecycle, evidence, authority, decision/receipt, and retention are versioned governance projections. They are excluded from `object_digest` so external grants and receipts can bind the exact subject tuple without circular self-reference. Their own transition, bundle, grant, decision, and receipt refs/digests provide integrity.
7. `evidence_status: sufficient_for_named_decision` must name that decision in the associated bundle. It is not globally sufficient.
8. Rights status does not inherit silently. Each derivation records whether rights are inherited, narrowed, disputed, or re-reviewed.
9. An agent-origin candidate records provenance and capability use; origin supplies no authority, ownership, approval, or release permission.
10. `preserved_candidate` means a receipt-backed decision was retained. It does not mean selected for use, reusable, releaseable, published, canonical, preferred, or successful.
11. Rejection, deferral, boneyard, supersession, and retirement preserve reason and salvage where retention policy permits.
12. Preference state changes only through a separately authorized, human-confirmed graph update after real outcome evidence. Candidate selection is not preference evidence.
13. Canon admission, external execution, publication, release, provider-resource access, and rights transfer are outside this object's authority surface.

## Identity and lineage invariants

- `object_id` is stable across versions; `object_version` and `object_digest` identify immutable candidate-subject state, while ledger state digests identify governance state.
- A receipt binds `object_id`, exact `object_version`, `object_digest`, payload digest, and the relevant prior/proposed ledger state digests.
- Parent, sibling, supersession, and dependency edges are typed. A visual connection without an edge type is not lineage.
- Deleting a UI card cannot erase the transition or receipt history.
- A later decision may supersede an earlier one, but may not rewrite the earlier evidence snapshot.
- A fork preserves its parent and begins with no inherited decision authority.

## Workbench projections

| Object field | Primary surface |
| --- | --- |
| id, version, object digest, lifecycle, rights, authority | context bar |
| active chamber | workbench/session context; not a HookCandidate field |
| origin and lineage | lineage rail |
| content, intent, constraints | work surface |
| applicable grants and blocked powers | move inspector and authority drawer |
| evidence, contradictions, decision, receipts | evidence/transition drawer |
| retention, salvage, revisit trigger | Gallery work surface |

No workbench projection becomes the semantic authority merely because it is easier to edit.

## Compatibility notes

- `source_binding_refs` is designed to reference, not replace, `source-binding.v2` records.
- Candidate movement is expressed through `proposed-move.v1` and `ledger.transition.v1` vocabulary where compatible.
- The existing `artifact`, `asset`, `media-derivative`, and other object schemas remain separate. No subtype relationship is asserted here.
- Any future schema nomination must compare this design with current repository contracts, record collisions, and choose migration or adaptation explicitly.

## Failure states

| Failure | Required behavior |
| --- | --- |
| version mismatch | block move; show expected and observed versions |
| missing origin | keep object captured and mark evidence gap |
| unbound rights | prohibit external test, reuse, release, and publication |
| broken lineage | quarantine derived version; preserve raw record |
| stale evidence | remain inspectable; block decisions that require freshness |
| disputed evidence | preserve both sides; require named resolution or deferral |
| expired or revoked grant | remove usability, retain inspectability and reason |
| receipt/digest mismatch | mark integrity failure; prohibit further consequential transitions |
| unknown retention basis | default to bounded working retention, not Forever |

## Review test

Remove every chamber name and brand label. If the object can no longer preserve exact identity, state, lineage, evidence, authority, rights, decision, and retention truth, the contract is still decorative rather than operational.
