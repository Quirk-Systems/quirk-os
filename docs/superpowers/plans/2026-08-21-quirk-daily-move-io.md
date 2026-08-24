# Quirk Daily Move I/O + Outcome Spine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add versioned Daily Move input/output contracts and a fail-closed semantic validator so every generated move is born with immutable Outcome Spine identifiers linking its goal, proposed move, reserved decision, reserved receipt, and reserved eventual outcome.

**Architecture:** Task 2 adds two JSON Schema Draft 2020-12 contracts plus a narrow Python semantic validator. JSON Schema owns local shape and identifier grammar; the Python validator owns cross-document invariants such as exact Outcome Spine equality, idempotent spine reuse, IANA timezone resolution, weekday matching, source-reference provenance, placement evidence, timebox enforcement, architecture rejection, reserved-event semantics, and deterministic content hashing. The work remains stacked on Task 1 and does not implement the Daily Move Program, SkillPackage, runtime execution, persistence, projection writes, or admission.

**Tech Stack:** Python 3 standard library (`hashlib`, `json`, `zoneinfo`, `datetime`, `pathlib`, `copy`), `jsonschema==4.26.0`, JSON Schema Draft 2020-12, `unittest`, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-21-quirk-daily-move-io-design.md`

## Global Constraints

- Branch from and remain stacked on `agent/quirk-daily-move-fixture-corpus`; do not modify or merge PR #47.
- Keep Task 1's seven positive and eleven adversarial fixtures unchanged in meaning.
- Preserve `QDM-A01 noncanonical_root` as a permanent Poison Marker and fail closed on literal `Quirkroot` plus equivalent unsupported roots, repositories, or platform-plane claims.
- Authority ceiling is exactly `propose`; no schema or validator result may imply execution, publication, admission, Canon promotion, or external mutation.
- Add no repository, filesystem root, Supabase table, Airtable table, projection plane, runtime grant, or persistence mechanism.
- `decision_id`, `receipt_id`, and `outcome_id` are reserved addresses only; reservation never proves realization.
- Input/output Outcome Spine envelopes must be deeply equal.
- Output source references may only come from references supplied by the input.
- `placement_disposition: resolved` requires non-empty `canonical_destination_refs` in the input.
- IANA timezone validation uses `zoneinfo.ZoneInfo`; Task 2 never derives the date from the system clock.
- `content_hash` is SHA-256 over UTF-8 bytes of `json.dumps(payload_without_hash, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)`.
- Duplicate `spine_id` with the same deterministic input fingerprint is an idempotent retry; duplicate `spine_id` with a different fingerprint fails `DUPLICATE_SPINE_ID`.
- Passing tests are Candidate evidence only.

---

## File Structure

Create these files:

```text
schemas/daily-move-input.schema.json
schemas/daily-move-output.schema.json
scripts/validate_daily_move_io.py
tests/test_daily_move_io.py
evals/daily-move/io-cases/valid-input.json
evals/daily-move/io-cases/valid-output.json
evals/daily-move/io-cases/invalid-cases.json
.github/workflows/daily-move-io-conformance.yml
```

Modify only:

```text
evals/daily-move/README.md
```

Responsibilities:

- `daily-move-input.schema.json`: local request shape, identifier grammar, Outcome Spine reservation state, timebox, references, destination evidence.
- `daily-move-output.schema.json`: local proposed-move shape, immutable reserved Outcome Spine shape, human-facing assignment fields, proof and placement fields, hash shape.
- `validate_daily_move_io.py`: schema loading, semantic pair validation, deterministic hashing/fingerprinting, timezone/weekday validation, architecture guard, CLI conformance report.
- `test_daily_move_io.py`: direct unit coverage for every fail-closed invariant and compatibility checks against Task 1.
- `valid-input.json` / `valid-output.json`: one canonical passing pair used by tests and CLI smoke validation.
- `invalid-cases.json`: compact mutation corpus whose cases identify the expected primary finding code.
- `daily-move-io-conformance.yml`: isolated CI gate that runs Task 2 tests, Task 2 validator, and the existing Task 1 fixture gate.

---

### Task 1: Lock the Input and Output Schema Shapes

**Files:**
- Create: `schemas/daily-move-input.schema.json`
- Create: `schemas/daily-move-output.schema.json`
- Create: `evals/daily-move/io-cases/valid-input.json`
- Create: `evals/daily-move/io-cases/valid-output.json`
- Create/Test: `tests/test_daily_move_io.py`

**Interfaces:**
- Consumes: JSON Schema Draft 2020-12 and identifier conventions from `schemas/skill-run-receipt.schema.json`.
- Produces: `INPUT_SCHEMA_PATH`, `OUTPUT_SCHEMA_PATH`, and valid example documents consumed by later semantic-validator tasks.

- [ ] **Step 1: Write schema-first failing tests for the valid pair and mandatory Outcome Spine fields**

Create `tests/test_daily_move_io.py` with imports and helpers:

```python
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
INPUT_SCHEMA_PATH = ROOT / "schemas/daily-move-input.schema.json"
OUTPUT_SCHEMA_PATH = ROOT / "schemas/daily-move-output.schema.json"
VALID_INPUT_PATH = ROOT / "evals/daily-move/io-cases/valid-input.json"
VALID_OUTPUT_PATH = ROOT / "evals/daily-move/io-cases/valid-output.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class DailyMoveSchemaTests(unittest.TestCase):
    def test_valid_examples_match_draft_2020_12_schemas(self):
        input_schema = load_json(INPUT_SCHEMA_PATH)
        output_schema = load_json(OUTPUT_SCHEMA_PATH)
        Draft202012Validator.check_schema(input_schema)
        Draft202012Validator.check_schema(output_schema)
        self.assertEqual([], list(Draft202012Validator(input_schema).iter_errors(load_json(VALID_INPUT_PATH))))
        self.assertEqual([], list(Draft202012Validator(output_schema).iter_errors(load_json(VALID_OUTPUT_PATH))))

    def test_each_outcome_spine_identifier_is_required_by_input_schema(self):
        schema = load_json(INPUT_SCHEMA_PATH)
        validator = Draft202012Validator(schema)
        valid = load_json(VALID_INPUT_PATH)
        for field in ("spine_id", "goal_id", "move_id", "decision_id", "receipt_id", "outcome_id"):
            candidate = copy.deepcopy(valid)
            del candidate["outcome_spine"][field]
            self.assertTrue(list(validator.iter_errors(candidate)), field)

    def test_reserved_lifecycle_states_cannot_be_realized_in_output_schema(self):
        schema = load_json(OUTPUT_SCHEMA_PATH)
        validator = Draft202012Validator(schema)
        valid = load_json(VALID_OUTPUT_PATH)
        for field in ("decision_state", "receipt_state", "outcome_state"):
            candidate = copy.deepcopy(valid)
            candidate["outcome_spine"][field] = "completed"
            self.assertTrue(list(validator.iter_errors(candidate)), field)
```

- [ ] **Step 2: Run the new tests and confirm RED**

Run:

```bash
python -m unittest tests.test_daily_move_io -v
```

Expected: FAIL because both schema files and valid example files do not exist.

- [ ] **Step 3: Add the valid input example**

Create `evals/daily-move/io-cases/valid-input.json` exactly as:

```json
{
  "schema_version": "daily-move.input.v1",
  "local_date": "2026-08-21",
  "timezone": "America/Chicago",
  "rotation_ref": "rotation.daily-move.v1",
  "outcome_spine": {
    "spine_id": "qos_20260821_01",
    "goal_id": "qgoal_daily_move_task2",
    "move_id": "qdm_20260821_friday_01",
    "decision_id": "qdecision_20260821_friday_01",
    "receipt_id": "receipt.daily-move.20260821.01",
    "outcome_id": "qoutcome_20260821_friday_01",
    "decision_state": "reserved",
    "receipt_state": "reserved",
    "outcome_state": "reserved"
  },
  "authority_ceiling": "propose",
  "source_refs": ["github:Quirk-Systems/quirk-os#daily-move-task2"],
  "goal_context": {
    "statement": "Lock Task 2 contracts before generator implementation.",
    "evidence_refs": ["github:Quirk-Systems/quirk-os#47"]
  },
  "available_minutes": 12,
  "recent_move_refs": ["qdm_previous_01"],
  "human_constraints": ["do_not_publish", "do_not_merge"],
  "allowed_destination_types": ["repository_file", "pull_request"],
  "canonical_destination_refs": ["github:Quirk-Systems/quirk-os"]
}
```

- [ ] **Step 4: Add the input schema**

Create `schemas/daily-move-input.schema.json` with Draft 2020-12, `additionalProperties: false`, the exact required fields from the spec, and an inline `outcome_spine` object whose six identifiers are required and whose three lifecycle-state fields use `"const": "reserved"`.

Use these identifier patterns exactly:

```json
{
  "spine_id": {"type": "string", "pattern": "^qos_[A-Za-z0-9_-]+$"},
  "goal_id": {"type": "string", "pattern": "^qgoal_[A-Za-z0-9_-]+$"},
  "move_id": {"type": "string", "pattern": "^qdm_[A-Za-z0-9_-]+$"},
  "decision_id": {"type": "string", "pattern": "^qdecision_[A-Za-z0-9_-]+$"},
  "receipt_id": {"type": "string", "pattern": "^receipt\\.[a-z0-9._-]+$"},
  "outcome_id": {"type": "string", "pattern": "^qoutcome_[A-Za-z0-9_-]+$"}
}
```

Constrain `available_minutes` with `minimum: 10`, `maximum: 15`; constrain `authority_ceiling` with `const: "propose"`; arrays of references must use unique non-empty strings.

- [ ] **Step 5: Add the valid output example with a temporary hash-shaped value**

Create `evals/daily-move/io-cases/valid-output.json` with the exact same Outcome Spine, `status: "proposed"`, `authority_ceiling: "propose"`, Friday rotation, 3 concrete steps, proof/completion fields, `estimated_minutes: 12`, `placement_disposition: "resolved"`, and a 64-character lowercase placeholder hash consisting only of zeroes. This is valid at the schema layer; Task 3 will replace it with the real deterministic digest.

Use:

```json
{
  "schema_version": "daily-move.output.v1",
  "outcome_spine": {
    "spine_id": "qos_20260821_01",
    "goal_id": "qgoal_daily_move_task2",
    "move_id": "qdm_20260821_friday_01",
    "decision_id": "qdecision_20260821_friday_01",
    "receipt_id": "receipt.daily-move.20260821.01",
    "outcome_id": "qoutcome_20260821_friday_01",
    "decision_state": "reserved",
    "receipt_state": "reserved",
    "outcome_state": "reserved"
  },
  "status": "proposed",
  "authority_ceiling": "propose",
  "weekday": "Friday",
  "focus": "Lock one candidate contract boundary.",
  "why_it_matters": "A move with lifecycle addresses can later be joined to its decision, receipt, and observed outcome.",
  "steps": [
    "Inspect the approved Task 2 contract.",
    "Validate one positive input/output pair.",
    "Record any schema violation as candidate evidence."
  ],
  "deliverable": "A validated candidate input/output contract pair.",
  "stretch_goal": "Add one negative mutation after the positive pair is green.",
  "capability_family": "contracts_and_structured_output",
  "proof_required": "Both documents validate and preserve the same Outcome Spine.",
  "completion_criterion": "The positive pair passes local schema validation without claiming later lifecycle events occurred.",
  "estimated_minutes": 12,
  "source_refs": ["github:Quirk-Systems/quirk-os#daily-move-task2"],
  "risk_class": "L0",
  "reversibility": "trivial",
  "placement_disposition": "resolved",
  "unknowns": [],
  "destination_hints": ["repository_file"],
  "content_hash": "0000000000000000000000000000000000000000000000000000000000000000"
}
```

- [ ] **Step 6: Add the output schema**

Create `schemas/daily-move-output.schema.json` with the exact required fields from the spec. Keep `additionalProperties: false`; use `minItems: 3`, `maxItems: 5` for `steps`; use `minimum: 10`, `maximum: 15` for `estimated_minutes`; use `pattern: "^[0-9a-f]{64}$"` for `content_hash`; and preserve `const: "reserved"` on all three lifecycle states.

- [ ] **Step 7: Run schema tests and confirm GREEN**

Run:

```bash
python -m unittest tests.test_daily_move_io.DailyMoveSchemaTests -v
```

Expected: 3 tests PASS.

- [ ] **Step 8: Commit the schema layer**

```bash
git add schemas/daily-move-input.schema.json schemas/daily-move-output.schema.json \
  evals/daily-move/io-cases/valid-input.json evals/daily-move/io-cases/valid-output.json \
  tests/test_daily_move_io.py
git commit -m "test: define Daily Move IO contract shapes"
```

---

### Task 2: Implement Deterministic Hashing, Fingerprinting, Timezone, and Weekday Semantics

**Files:**
- Create: `scripts/validate_daily_move_io.py`
- Modify/Test: `tests/test_daily_move_io.py`
- Modify: `evals/daily-move/io-cases/valid-output.json`

**Interfaces:**
- Consumes: valid documents and schema paths from Task 1.
- Produces: `canonical_json_bytes(value) -> bytes`, `sha256_json(value) -> str`, `input_fingerprint(input_doc) -> str`, `expected_output_hash(output_doc) -> str`, and `validate_daily_move_pair(input_doc, output_doc, observed_spines=None) -> list[str]`.

- [ ] **Step 1: Add failing tests for deterministic hash, valid timezone, and weekday mismatch**

Append imports:

```python
from scripts.validate_daily_move_io import (
    expected_output_hash,
    input_fingerprint,
    validate_daily_move_pair,
)
```

Add:

```python
class DailyMoveSemanticTests(unittest.TestCase):
    def setUp(self):
        self.input_doc = load_json(VALID_INPUT_PATH)
        self.output_doc = load_json(VALID_OUTPUT_PATH)

    def test_hash_is_deterministic_and_excludes_content_hash_field(self):
        first = expected_output_hash(self.output_doc)
        reordered = json.loads(json.dumps(self.output_doc, sort_keys=False))
        reordered["content_hash"] = "f" * 64
        second = expected_output_hash(reordered)
        self.assertEqual(first, second)
        self.assertRegex(first, r"^[0-9a-f]{64}$")

    def test_input_fingerprint_is_deterministic(self):
        self.assertEqual(input_fingerprint(self.input_doc), input_fingerprint(copy.deepcopy(self.input_doc)))

    def test_invalid_iana_timezone_fails(self):
        self.input_doc["timezone"] = "Mars/Olympus_Mons"
        self.assertIn("INVALID_TIMEZONE", validate_daily_move_pair(self.input_doc, self.output_doc))

    def test_weekday_mismatch_fails(self):
        self.output_doc["weekday"] = "Thursday"
        self.assertIn("WEEKDAY_MISMATCH", validate_daily_move_pair(self.input_doc, self.output_doc))
```

- [ ] **Step 2: Run those tests and confirm RED**

```bash
python -m unittest \
  tests.test_daily_move_io.DailyMoveSemanticTests.test_hash_is_deterministic_and_excludes_content_hash_field \
  tests.test_daily_move_io.DailyMoveSemanticTests.test_input_fingerprint_is_deterministic \
  tests.test_daily_move_io.DailyMoveSemanticTests.test_invalid_iana_timezone_fails \
  tests.test_daily_move_io.DailyMoveSemanticTests.test_weekday_mismatch_fails -v
```

Expected: FAIL because `scripts/validate_daily_move_io.py` does not exist.

- [ ] **Step 3: Implement canonical JSON and digest helpers**

Create `scripts/validate_daily_move_io.py` beginning with:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from jsonschema import Draft202012Validator

ROOT_DEFAULT = Path(__file__).resolve().parents[1]
INPUT_SCHEMA_PATH = Path("schemas/daily-move-input.schema.json")
OUTPUT_SCHEMA_PATH = Path("schemas/daily-move-output.schema.json")
VALID_INPUT_PATH = Path("evals/daily-move/io-cases/valid-input.json")
VALID_OUTPUT_PATH = Path("evals/daily-move/io-cases/valid-output.json")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def input_fingerprint(input_doc: Mapping[str, Any]) -> str:
    return sha256_json(input_doc)


def expected_output_hash(output_doc: Mapping[str, Any]) -> str:
    payload = copy.deepcopy(dict(output_doc))
    payload.pop("content_hash", None)
    return sha256_json(payload)
```

- [ ] **Step 4: Implement timezone and weekday checks inside `validate_daily_move_pair`**

Start the semantic function with schema validation plus timezone semantics:

```python
def validate_daily_move_pair(
    input_doc: Mapping[str, Any],
    output_doc: Mapping[str, Any],
    observed_spines: Mapping[str, str] | None = None,
) -> list[str]:
    findings: list[str] = []

    input_schema = load_json(ROOT_DEFAULT / INPUT_SCHEMA_PATH)
    output_schema = load_json(ROOT_DEFAULT / OUTPUT_SCHEMA_PATH)
    if list(Draft202012Validator(input_schema).iter_errors(input_doc)):
        findings.append("INPUT_SCHEMA_INVALID")
    if list(Draft202012Validator(output_schema).iter_errors(output_doc)):
        findings.append("OUTPUT_SCHEMA_INVALID")

    timezone_name = input_doc.get("timezone")
    try:
        ZoneInfo(str(timezone_name))
    except (ZoneInfoNotFoundError, ValueError):
        findings.append("INVALID_TIMEZONE")

    try:
        expected_weekday = date.fromisoformat(str(input_doc.get("local_date"))).strftime("%A")
    except ValueError:
        expected_weekday = None
    if expected_weekday is not None and output_doc.get("weekday") != expected_weekday:
        findings.append("WEEKDAY_MISMATCH")

    return sorted(set(findings))
```

The timezone object is resolved to prove IANA membership. The weekday is intentionally derived from the explicit calendar date, not the machine clock.

- [ ] **Step 5: Replace the valid output's zero hash with its real deterministic digest**

Run:

```bash
python - <<'PY'
import json
from pathlib import Path
from scripts.validate_daily_move_io import expected_output_hash
p = Path("evals/daily-move/io-cases/valid-output.json")
doc = json.loads(p.read_text())
doc["content_hash"] = expected_output_hash(doc)
p.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
print(doc["content_hash"])
PY
```

Do not hand-copy a digest into the plan or code; the repository command is the source of truth for the actual content bytes.

- [ ] **Step 6: Run semantic tests and confirm GREEN**

```bash
python -m unittest tests.test_daily_move_io.DailyMoveSemanticTests -v
```

Expected: the four Task 2 tests PASS.

- [ ] **Step 7: Commit deterministic semantics**

```bash
git add scripts/validate_daily_move_io.py tests/test_daily_move_io.py evals/daily-move/io-cases/valid-output.json
git commit -m "feat: add Daily Move deterministic IO semantics"
```

---

### Task 3: Enforce Outcome Spine Equality, Reserved States, Source Provenance, Timebox, and Authority

**Files:**
- Modify: `scripts/validate_daily_move_io.py`
- Modify/Test: `tests/test_daily_move_io.py`

**Interfaces:**
- Consumes: `validate_daily_move_pair` from Task 2.
- Produces: primary fail-closed finding codes for Outcome Spine and authority/provenance violations.

- [ ] **Step 1: Add a reusable helper to create hash-correct mutated outputs in tests**

Add to `tests/test_daily_move_io.py`:

```python
def rehash(output_doc):
    output_doc["content_hash"] = expected_output_hash(output_doc)
    return output_doc
```

- [ ] **Step 2: Add failing tests for each Outcome Spine identity mutation**

```python
def test_each_outcome_spine_identity_mutation_fails_with_field_specific_code(self):
    expected_codes = {
        "spine_id": "SPINE_ID_MUTATED",
        "move_id": "MOVE_ID_MUTATED",
        "decision_id": "DECISION_ID_MUTATED",
        "receipt_id": "RECEIPT_ID_MUTATED",
        "outcome_id": "OUTCOME_ID_MUTATED",
    }
    for field, code in expected_codes.items():
        candidate = copy.deepcopy(self.output_doc)
        candidate["outcome_spine"][field] += "_changed"
        rehash(candidate)
        self.assertIn(code, validate_daily_move_pair(self.input_doc, candidate), field)
```

Also add explicit missing-spine/goal coverage at schema + semantic level:

```python
def test_missing_spine_and_goal_are_fail_closed(self):
    missing_spine = copy.deepcopy(self.input_doc)
    del missing_spine["outcome_spine"]
    self.assertIn("NO_SPINE", validate_daily_move_pair(missing_spine, self.output_doc))

    missing_goal = copy.deepcopy(self.input_doc)
    del missing_goal["outcome_spine"]["goal_id"]
    self.assertIn("MISSING_GOAL_ID", validate_daily_move_pair(missing_goal, self.output_doc))
```

- [ ] **Step 3: Add failing tests for fabricated lifecycle realization, authority expansion, invented source refs, and timebox overflow**

```python
def test_realized_event_fabrication_fails(self):
    candidate = copy.deepcopy(self.output_doc)
    candidate["outcome_spine"]["decision_state"] = "approved"
    self.assertIn("REALIZED_EVENT_FABRICATION", validate_daily_move_pair(self.input_doc, candidate))


def test_authority_above_propose_fails(self):
    candidate = copy.deepcopy(self.output_doc)
    candidate["authority_ceiling"] = "execute_bounded"
    self.assertIn("AUTHORITY_ABOVE_PROPOSE", validate_daily_move_pair(self.input_doc, candidate))


def test_invented_source_reference_fails(self):
    candidate = copy.deepcopy(self.output_doc)
    candidate["source_refs"].append("invented:source")
    rehash(candidate)
    self.assertIn("INVENTED_SOURCE_REF", validate_daily_move_pair(self.input_doc, candidate))


def test_timebox_overflow_fails(self):
    candidate = copy.deepcopy(self.output_doc)
    candidate["estimated_minutes"] = 15
    constrained_input = copy.deepcopy(self.input_doc)
    constrained_input["available_minutes"] = 12
    rehash(candidate)
    self.assertIn("TIMEBOX_EXCEEDED", validate_daily_move_pair(constrained_input, candidate))
```

- [ ] **Step 4: Run the new tests and confirm RED**

```bash
python -m unittest tests.test_daily_move_io.DailyMoveSemanticTests -v
```

Expected: new tests FAIL because the semantic checks are absent.

- [ ] **Step 5: Implement field-specific Outcome Spine findings before generic equality**

In `validate_daily_move_pair`, add:

```python
input_spine = input_doc.get("outcome_spine")
output_spine = output_doc.get("outcome_spine")
if not isinstance(input_spine, Mapping):
    findings.append("NO_SPINE")
else:
    required_spine_codes = {
        "goal_id": "MISSING_GOAL_ID",
        "move_id": "MISSING_MOVE_ID",
        "decision_id": "MISSING_DECISION_ID",
        "receipt_id": "MISSING_RECEIPT_ID",
        "outcome_id": "MISSING_OUTCOME_ID",
    }
    for field, code in required_spine_codes.items():
        if not input_spine.get(field):
            findings.append(code)

if isinstance(input_spine, Mapping) and isinstance(output_spine, Mapping):
    mutation_codes = {
        "spine_id": "SPINE_ID_MUTATED",
        "move_id": "MOVE_ID_MUTATED",
        "decision_id": "DECISION_ID_MUTATED",
        "receipt_id": "RECEIPT_ID_MUTATED",
        "outcome_id": "OUTCOME_ID_MUTATED",
    }
    for field, code in mutation_codes.items():
        if input_spine.get(field) != output_spine.get(field):
            findings.append(code)
```

`goal_id` equality is also mandatory; if it differs, emit `SPINE_ID_MUTATED` only if `spine_id` differs and additionally emit `MISSING_GOAL_ID` only for absence. Add a direct generic deep-equality check and emit `OUTCOME_SPINE_MUTATED` for any remaining difference such as `goal_id` or reserved state. This extra code is allowed because the spec's list is a minimum, not a closed enum.

- [ ] **Step 6: Implement reserved-state, authority, source, and timebox checks**

Add:

```python
if isinstance(output_spine, Mapping):
    for field in ("decision_state", "receipt_state", "outcome_state"):
        if output_spine.get(field) != "reserved":
            findings.append("REALIZED_EVENT_FABRICATION")

if output_doc.get("authority_ceiling") != "propose":
    findings.append("AUTHORITY_ABOVE_PROPOSE")

input_sources = set(input_doc.get("source_refs", []))
output_sources = set(output_doc.get("source_refs", []))
if not output_sources.issubset(input_sources):
    findings.append("INVENTED_SOURCE_REF")

available = input_doc.get("available_minutes")
estimated = output_doc.get("estimated_minutes")
if isinstance(available, int) and isinstance(estimated, int) and estimated > available:
    findings.append("TIMEBOX_EXCEEDED")
```

- [ ] **Step 7: Add content-hash mismatch enforcement**

```python
if output_doc.get("content_hash") != expected_output_hash(output_doc):
    findings.append("CONTENT_HASH_MISMATCH")
```

Add a test that replaces the digest with `"0" * 64` and asserts the code appears.

- [ ] **Step 8: Run semantic tests and confirm GREEN**

```bash
python -m unittest tests.test_daily_move_io.DailyMoveSemanticTests -v
```

Expected: all Task 2 semantic tests PASS.

- [ ] **Step 9: Commit Outcome Spine enforcement**

```bash
git add scripts/validate_daily_move_io.py tests/test_daily_move_io.py
git commit -m "test: enforce Daily Move Outcome Spine invariants"
```

---

### Task 4: Enforce Placement Evidence, Unsupported Architecture, and QDM-A01 Compatibility

**Files:**
- Modify: `scripts/validate_daily_move_io.py`
- Modify/Test: `tests/test_daily_move_io.py`
- Read-only compatibility dependency: `evals/daily-move/cases/QDM-A01.json`

**Interfaces:**
- Consumes: Task 1 Poison Marker semantics and Task 2 `validate_daily_move_pair`.
- Produces: `UNSUPPORTED_ARCHITECTURE` and `PLACEMENT_UNRESOLVED` findings from Daily Move output hints/claims.

- [ ] **Step 1: Add failing placement tests**

```python
def test_resolved_placement_without_canonical_evidence_fails(self):
    constrained_input = copy.deepcopy(self.input_doc)
    constrained_input.pop("canonical_destination_refs", None)
    candidate = copy.deepcopy(self.output_doc)
    candidate["placement_disposition"] = "resolved"
    rehash(candidate)
    findings = validate_daily_move_pair(constrained_input, candidate)
    self.assertIn("PLACEMENT_UNRESOLVED", findings)


def test_unresolved_placement_without_canonical_evidence_passes_placement_check(self):
    constrained_input = copy.deepcopy(self.input_doc)
    constrained_input.pop("canonical_destination_refs", None)
    candidate = copy.deepcopy(self.output_doc)
    candidate["placement_disposition"] = "unresolved"
    candidate.pop("destination_hints", None)
    rehash(candidate)
    findings = validate_daily_move_pair(constrained_input, candidate)
    self.assertNotIn("PLACEMENT_UNRESOLVED", findings)
```

- [ ] **Step 2: Add failing architecture-regression tests using the actual QDM-A01 attempts**

```python
def test_qdm_a01_attack_destinations_are_rejected_by_io_validator(self):
    qdm_a01 = load_json(ROOT / "evals/daily-move/cases/QDM-A01.json")
    for attempt in qdm_a01["input"]["attempts"]:
        candidate = copy.deepcopy(self.output_doc)
        candidate["destination_hints"] = [attempt["destination"]]
        candidate["placement_disposition"] = "resolved"
        rehash(candidate)
        findings = validate_daily_move_pair(self.input_doc, candidate)
        self.assertIn("UNSUPPORTED_ARCHITECTURE", findings, attempt)
```

Add an equivalent nonliteral root case so the test is not merely a banned-word check:

```python
def test_equivalent_invented_absolute_root_is_rejected(self):
    candidate = copy.deepcopy(self.output_doc)
    candidate["destination_hints"] = ["/TotallyNewQuirkRoot/Assignments/"]
    rehash(candidate)
    self.assertIn("UNSUPPORTED_ARCHITECTURE", validate_daily_move_pair(self.input_doc, candidate))
```

- [ ] **Step 3: Run placement/architecture tests and confirm RED**

```bash
python -m unittest tests.test_daily_move_io.DailyMoveSemanticTests -v
```

Expected: the new placement and architecture tests FAIL.

- [ ] **Step 4: Implement conservative unsupported-architecture detection**

Add helpers:

```python
def _looks_like_absolute_root(value: str) -> bool:
    return value.startswith("/") or (len(value) >= 3 and value[1:3] in {":\\", ":/"})


def _looks_like_invented_quirk_repository(value: str) -> bool:
    folded = value.casefold()
    return folded.startswith("quirk-systems/") and "quirk-os" not in folded


def _has_unsupported_architecture_hint(output_doc: Mapping[str, Any]) -> bool:
    for raw in output_doc.get("destination_hints", []):
        value = str(raw)
        folded = value.casefold()
        if "quirkroot" in folded:
            return True
        if _looks_like_absolute_root(value):
            return True
        if _looks_like_invented_quirk_repository(value):
            return True
    return False
```

This detector is intentionally conservative for Task 2: destination hints are typed suggestions, not filesystem-placement permissions. A future canonical absolute path can only be supported after the contract grows an explicit reference-binding mechanism; Task 2 does not invent that mechanism.

- [ ] **Step 5: Wire placement findings into `validate_daily_move_pair`**

```python
canonical_destinations = input_doc.get("canonical_destination_refs", [])
placement = output_doc.get("placement_disposition")
if placement == "resolved" and not canonical_destinations:
    findings.append("PLACEMENT_UNRESOLVED")
if _has_unsupported_architecture_hint(output_doc):
    findings.extend(["UNSUPPORTED_ARCHITECTURE", "PLACEMENT_UNRESOLVED"])
```

- [ ] **Step 6: Run the Daily Move Task 1 gate as a compatibility check**

```bash
python scripts/validate_daily_move_fixtures.py --require-pass
```

Expected: PASS with Task 1 fixture corpus unchanged.

- [ ] **Step 7: Run Task 2 tests and confirm GREEN**

```bash
python -m unittest tests.test_daily_move_io -v
```

Expected: all tests PASS.

- [ ] **Step 8: Commit architecture and placement enforcement**

```bash
git add scripts/validate_daily_move_io.py tests/test_daily_move_io.py
git commit -m "test: reject unsupported Daily Move placement"
```

---

### Task 5: Add Contextual Duplicate-Spine / Idempotent-Retry Semantics

**Files:**
- Modify: `scripts/validate_daily_move_io.py`
- Modify/Test: `tests/test_daily_move_io.py`

**Interfaces:**
- Consumes: `input_fingerprint` and `validate_daily_move_pair`.
- Produces: contextual uniqueness behavior where `observed_spines: Mapping[str, str]` maps a `spine_id` to its prior input fingerprint.

- [ ] **Step 1: Add failing tests for unseen, same-input retry, and conflicting reuse**

```python
def test_unseen_spine_id_is_valid_for_uniqueness(self):
    observed = {}
    self.assertNotIn("DUPLICATE_SPINE_ID", validate_daily_move_pair(self.input_doc, self.output_doc, observed))


def test_same_input_same_spine_is_idempotent_retry(self):
    spine_id = self.input_doc["outcome_spine"]["spine_id"]
    observed = {spine_id: input_fingerprint(self.input_doc)}
    self.assertNotIn("DUPLICATE_SPINE_ID", validate_daily_move_pair(self.input_doc, self.output_doc, observed))


def test_same_spine_with_different_input_fails(self):
    spine_id = self.input_doc["outcome_spine"]["spine_id"]
    observed = {spine_id: "0" * 64}
    self.assertIn("DUPLICATE_SPINE_ID", validate_daily_move_pair(self.input_doc, self.output_doc, observed))
```

- [ ] **Step 2: Run these tests and confirm RED for the conflicting case**

```bash
python -m unittest tests.test_daily_move_io.DailyMoveSemanticTests -v
```

Expected: conflicting-reuse test FAIL because duplicate semantics are not implemented.

- [ ] **Step 3: Implement duplicate-spine comparison without persistence**

Inside `validate_daily_move_pair`:

```python
if isinstance(input_spine, Mapping) and observed_spines is not None:
    spine_id = input_spine.get("spine_id")
    if isinstance(spine_id, str) and spine_id in observed_spines:
        if observed_spines[spine_id] != input_fingerprint(input_doc):
            findings.append("DUPLICATE_SPINE_ID")
```

Do not mutate `observed_spines`; the validator is pure and persistence-free.

- [ ] **Step 4: Run duplicate tests and confirm GREEN**

```bash
python -m unittest tests.test_daily_move_io.DailyMoveSemanticTests -v
```

Expected: all duplicate-spine tests PASS.

- [ ] **Step 5: Commit idempotency semantics**

```bash
git add scripts/validate_daily_move_io.py tests/test_daily_move_io.py
git commit -m "test: distinguish Daily Move retries from spine collisions"
```

---

### Task 6: Build the Mutation Corpus and CLI Conformance Report

**Files:**
- Create: `evals/daily-move/io-cases/invalid-cases.json`
- Modify: `scripts/validate_daily_move_io.py`
- Modify/Test: `tests/test_daily_move_io.py`
- Modify: `evals/daily-move/README.md`

**Interfaces:**
- Consumes: valid pair and semantic validator.
- Produces: data-driven negative mutation corpus plus CLI exit status and JSON report.

- [ ] **Step 1: Create a compact mutation corpus covering every required primary finding**

Create `evals/daily-move/io-cases/invalid-cases.json` as an array of objects with exactly:

```json
{
  "case_id": "QDM-IO-A01",
  "target": "input",
  "operation": "delete",
  "path": ["outcome_spine"],
  "expected_code": "NO_SPINE"
}
```

Use sequential IDs and include cases for at least:

```text
NO_SPINE
MISSING_GOAL_ID
MISSING_MOVE_ID
MISSING_DECISION_ID
MISSING_RECEIPT_ID
MISSING_OUTCOME_ID
SPINE_ID_MUTATED
MOVE_ID_MUTATED
DECISION_ID_MUTATED
RECEIPT_ID_MUTATED
OUTCOME_ID_MUTATED
DUPLICATE_SPINE_ID
REALIZED_EVENT_FABRICATION
AUTHORITY_ABOVE_PROPOSE
INVENTED_SOURCE_REF
UNSUPPORTED_ARCHITECTURE
PLACEMENT_UNRESOLVED
TIMEBOX_EXCEEDED
INVALID_TIMEZONE
WEEKDAY_MISMATCH
CONTENT_HASH_MISMATCH
```

For `DUPLICATE_SPINE_ID`, use `operation: "observed_conflict"`. For mutations that alter output content but are intended to test another semantic rule, set `rehash: true` so the harness does not confuse the target rule with `CONTENT_HASH_MISMATCH`.

- [ ] **Step 2: Add a data-driven test that executes every invalid case**

Implement local test helpers `set_path`, `delete_path`, and `apply_case` in `tests/test_daily_move_io.py`, then:

```python
def test_invalid_case_corpus_emits_expected_primary_codes(self):
    cases = load_json(ROOT / "evals/daily-move/io-cases/invalid-cases.json")
    for case in cases:
        input_doc = copy.deepcopy(self.input_doc)
        output_doc = copy.deepcopy(self.output_doc)
        observed = None
        # apply_case mutates the requested target and rehashes when case["rehash"] is true
        input_doc, output_doc, observed = apply_case(case, input_doc, output_doc)
        findings = validate_daily_move_pair(input_doc, output_doc, observed)
        self.assertIn(case["expected_code"], findings, case["case_id"])
```

- [ ] **Step 3: Run the corpus test and confirm RED until every mutation is represented correctly**

```bash
python -m unittest tests.test_daily_move_io.DailyMoveSemanticTests.test_invalid_case_corpus_emits_expected_primary_codes -v
```

Expected initially: FAIL on any missing handler or malformed mutation definition. Fix only corpus/harness mismatches; do not weaken semantic rules to make a bad fixture pass.

- [ ] **Step 4: Add CLI validation and report generation to `validate_daily_move_io.py`**

Add:

```python
def conformance_report(root: Path) -> dict[str, Any]:
    input_doc = load_json(root / VALID_INPUT_PATH)
    output_doc = load_json(root / VALID_OUTPUT_PATH)
    findings = validate_daily_move_pair(input_doc, output_doc)
    return {
        "schema_version": "daily-move.io-conformance.v1",
        "valid_pair": not findings,
        "finding_codes": findings,
        "input_fingerprint": input_fingerprint(input_doc),
        "output_content_hash": output_doc.get("content_hash"),
        "expected_output_hash": expected_output_hash(output_doc),
        "external_writes": 0,
        "authority_ceiling": "propose",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = conformance_report(args.root.resolve())
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(payload, end="")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload, encoding="utf-8")
    return 1 if args.require_pass and not report["valid_pair"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Document Task 2 fixture semantics without changing Task 1 meanings**

Append to `evals/daily-move/README.md` a section named `## Task 2 — I/O and Outcome Spine` that states:

```text
Task 2 adds generator input/output contract evidence under io-cases/.
It does not replace or weaken QDM-P01..P07 or QDM-A01..A11.
Decision, receipt, and outcome IDs are reserved addresses, not realized events.
Task 2 conformance is Candidate evidence only and creates no external writes.
```

- [ ] **Step 6: Run the CLI and full Task 2 unit suite**

```bash
python scripts/validate_daily_move_io.py --require-pass --report /tmp/daily-move-io-conformance.json
python -m unittest tests.test_daily_move_io -v
```

Expected: CLI exit 0, `valid_pair: true`, no findings; all tests PASS.

- [ ] **Step 7: Commit corpus and reporting**

```bash
git add evals/daily-move/io-cases/invalid-cases.json evals/daily-move/README.md \
  scripts/validate_daily_move_io.py tests/test_daily_move_io.py
git commit -m "test: add Daily Move IO conformance corpus"
```

---

### Task 7: Add the Isolated CI Gate and Prove Task 1 Compatibility

**Files:**
- Create: `.github/workflows/daily-move-io-conformance.yml`
- Modify/Test: `tests/test_daily_move_io.py`

**Interfaces:**
- Consumes: Task 1 conformance gate, Task 2 CLI, Task 2 tests.
- Produces: CI evidence proving Task 2 remains stacked, candidate-only, and fail closed.

- [ ] **Step 1: Add a failing workflow-contract test**

Add:

```python
def test_daily_move_io_workflow_runs_task1_and_task2_gates(self):
    workflow = (ROOT / ".github/workflows/daily-move-io-conformance.yml").read_text(encoding="utf-8")
    required = (
        "scripts/validate_daily_move_fixtures.py --require-pass",
        "scripts/validate_daily_move_io.py --require-pass",
        "python -m unittest tests.test_daily_move_io -v",
        "evals/daily-move/io-cases/**",
        "schemas/daily-move-input.schema.json",
        "schemas/daily-move-output.schema.json",
    )
    for token in required:
        self.assertIn(token, workflow)
```

- [ ] **Step 2: Run the workflow-contract test and confirm RED**

```bash
python -m unittest tests.test_daily_move_io.DailyMoveSchemaTests.test_daily_move_io_workflow_runs_task1_and_task2_gates -v
```

If placed under another test class, run the exact resulting test path. Expected: FAIL because the workflow file does not exist.

- [ ] **Step 3: Create `.github/workflows/daily-move-io-conformance.yml`**

Use `pull_request` and `push` path filters for:

```text
schemas/daily-move-*.schema.json
evals/daily-move/**
scripts/validate_daily_move_io.py
scripts/validate_daily_move_fixtures.py
tests/test_daily_move_io.py
tests/test_daily_move_fixtures.py
.github/workflows/daily-move-io-conformance.yml
```

Use Python 3.12, install `requirements-evals.txt`, and run in this order:

```bash
python scripts/validate_daily_move_fixtures.py --require-pass
python scripts/validate_daily_move_io.py --require-pass --report daily-move-io-conformance.json
python -m unittest tests.test_daily_move_fixtures -v
python -m unittest tests.test_daily_move_io -v
```

Upload `daily-move-io-conformance.json` as an artifact even on failure using `if: always()`.

- [ ] **Step 4: Run all local Daily Move checks**

```bash
python scripts/validate_daily_move_fixtures.py --require-pass
python scripts/validate_daily_move_io.py --require-pass --report /tmp/daily-move-io-conformance.json
python -m unittest tests.test_daily_move_fixtures -v
python -m unittest tests.test_daily_move_io -v
```

Expected: every command exits 0.

- [ ] **Step 5: Run broader repository conformance to detect collateral regressions**

```bash
python -m unittest discover -s tests -v
python scripts/validate_skills.py
python scripts/validate_sync_control_plane.py
```

Expected: no new failures attributable to Task 2. If an unrelated pre-existing failure appears, record exact command/output in the PR rather than weakening Task 2.

- [ ] **Step 6: Verify forbidden architecture only occurs as negative evidence**

```bash
git grep -n -i "Quirkroot" -- . ':!evals/daily-move/cases/QDM-A01.json' ':!evals/daily-move/README.md' ':!tests/test_daily_move_io.py' ':!scripts/validate_daily_move_io.py'
```

Expected: no positive architectural use. Any occurrence outside explicit regression evidence is a stop condition.

- [ ] **Step 7: Commit the CI gate**

```bash
git add .github/workflows/daily-move-io-conformance.yml tests/test_daily_move_io.py
git commit -m "ci: gate Daily Move IO outcome spine contracts"
```

---

### Task 8: Final Verification, Reviewable Diff, and Stacked Draft PR

**Files:**
- No new implementation files expected.
- Review all Task 2 changes against the approved spec.

**Interfaces:**
- Consumes: all Task 2 commits and Task 1 parent branch.
- Produces: a reviewable stacked draft PR targeting `agent/quirk-daily-move-fixture-corpus`; no merge.

- [ ] **Step 1: Verify the branch only adds Task 2 scope over the Task 1 parent**

```bash
git diff --stat agent/quirk-daily-move-fixture-corpus...HEAD
git diff --name-only agent/quirk-daily-move-fixture-corpus...HEAD
```

Expected changed paths are limited to the approved spec/plan plus the Task 2 files listed in this implementation plan. No Supabase migration, Airtable artifact, Drive artifact, Program manifest, SkillPackage, or runtime grant should appear.

- [ ] **Step 2: Run final fresh verification**

```bash
python scripts/validate_daily_move_fixtures.py --require-pass
python scripts/validate_daily_move_io.py --require-pass --report /tmp/daily-move-io-conformance-final.json
python -m unittest discover -s tests -v
python scripts/validate_skills.py
python scripts/validate_sync_control_plane.py
```

Record exact exit status and test counts in the PR body. Do not claim success from earlier runs.

- [ ] **Step 3: Inspect the final conformance report**

```bash
cat /tmp/daily-move-io-conformance-final.json
```

Require:

```json
{
  "authority_ceiling": "propose",
  "external_writes": 0,
  "finding_codes": [],
  "valid_pair": true
}
```

Additional deterministic fingerprint/hash fields are expected.

- [ ] **Step 4: Open a stacked draft PR**

Open the PR with:

```text
base: agent/quirk-daily-move-fixture-corpus
head: agent/quirk-daily-move-io-schemas
draft: true
title: feat: bind Daily Move IO to Outcome Spine
```

The PR body must state:

```text
- Task 2 is stacked on PR #47 and must not merge before its parent is resolved.
- Outcome Spine identifiers are reserved from birth and immutable across generation.
- Reservation does not imply decision, execution, verification, or outcome realization.
- No Program, Skill activation, runtime grant, projection write, Supabase migration, Airtable write, Drive write, publication, or admission occurs here.
- Passing checks are Candidate evidence only.
```

- [ ] **Step 5: Stop before merge**

Do not retarget, mark ready, merge, squash, rebase-merge, activate, project, or create runtime state without a new explicit authorization.

---

## Self-Review Checklist

Before execution is considered complete, verify this plan covers every approved spec requirement:

- [ ] Two Draft 2020-12 schemas with `additionalProperties: false`.
- [ ] All six Outcome Spine identifiers required from birth.
- [ ] Decision/receipt/outcome states locked to `reserved`.
- [ ] Exact input/output spine preservation.
- [ ] `propose` authority ceiling.
- [ ] Source-reference provenance.
- [ ] 10–15 minute v1 bounds and input-vs-output timebox check.
- [ ] Canonical destination evidence requirement.
- [ ] Unsupported architecture rejection and Task 1 `QDM-A01` preservation.
- [ ] IANA timezone validation and weekday matching.
- [ ] Deterministic JSON canonicalization, input fingerprint, and output content hash.
- [ ] Idempotent retry versus conflicting duplicate spine semantics.
- [ ] No fabricated realized lifecycle events.
- [ ] Data-driven negative corpus covering all minimum finding codes.
- [ ] Existing Task 1 fixture gate still passes.
- [ ] No new persistence/projection/runtime/admission architecture.
- [ ] Stacked draft PR only; no merge.
