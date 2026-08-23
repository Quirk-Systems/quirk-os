from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.validate_daily_move_io import (
    conformance_report,
    expected_output_hash,
    input_fingerprint,
    validate_daily_move_pair,
)

ROOT = Path(__file__).resolve().parents[1]
INPUT_SCHEMA_PATH = ROOT / "schemas/daily-move-input.schema.json"
OUTPUT_SCHEMA_PATH = ROOT / "schemas/daily-move-output.schema.json"
VALID_INPUT_PATH = ROOT / "evals/daily-move/io-cases/valid-input.json"
VALID_OUTPUT_PATH = ROOT / "evals/daily-move/io-cases/valid-output.json"
INVALID_CASES_PATH = ROOT / "evals/daily-move/io-cases/invalid-cases.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def rehash(output_doc):
    output_doc["content_hash"] = expected_output_hash(output_doc)
    return output_doc


def _resolve_parent(document, path):
    current = document
    for segment in path[:-1]:
        current = current[segment]
    return current, path[-1]


def set_path(document, path, value):
    parent, leaf = _resolve_parent(document, path)
    parent[leaf] = value


def delete_path(document, path):
    parent, leaf = _resolve_parent(document, path)
    del parent[leaf]


def apply_case(case, input_doc, output_doc):
    observed = None
    operation = case["operation"]
    target = case["target"]
    if operation == "observed_conflict":
        spine_id = input_doc["outcome_spine"]["spine_id"]
        observed = {spine_id: "0" * 64}
    else:
        document = input_doc if target == "input" else output_doc
        path = case["path"]
        if operation == "delete":
            delete_path(document, path)
        elif operation == "set":
            set_path(document, path, copy.deepcopy(case["value"]))
        elif operation == "append":
            parent, leaf = _resolve_parent(document, path)
            parent[leaf].append(copy.deepcopy(case["value"]))
        else:
            raise AssertionError(f"unsupported mutation operation: {operation}")
    if case.get("rehash"):
        rehash(output_doc)
    return input_doc, output_doc, observed


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

    def test_missing_spine_and_goal_are_fail_closed(self):
        missing_spine = copy.deepcopy(self.input_doc)
        del missing_spine["outcome_spine"]
        self.assertIn("NO_SPINE", validate_daily_move_pair(missing_spine, self.output_doc))

        missing_goal = copy.deepcopy(self.input_doc)
        del missing_goal["outcome_spine"]["goal_id"]
        self.assertIn("MISSING_GOAL_ID", validate_daily_move_pair(missing_goal, self.output_doc))

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

    def test_content_hash_mismatch_fails(self):
        candidate = copy.deepcopy(self.output_doc)
        candidate["content_hash"] = "0" * 64
        self.assertIn("CONTENT_HASH_MISMATCH", validate_daily_move_pair(self.input_doc, candidate))

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

    def test_qdm_a01_attack_destinations_are_rejected_by_io_validator(self):
        qdm_a01 = load_json(ROOT / "evals/daily-move/cases/QDM-A01.json")
        for attempt in qdm_a01["input"]["attempts"]:
            candidate = copy.deepcopy(self.output_doc)
            candidate["destination_hints"] = [attempt["destination"]]
            candidate["placement_disposition"] = "resolved"
            rehash(candidate)
            findings = validate_daily_move_pair(self.input_doc, candidate)
            self.assertIn("UNSUPPORTED_ARCHITECTURE", findings, attempt)

    def test_equivalent_invented_absolute_root_is_rejected(self):
        candidate = copy.deepcopy(self.output_doc)
        candidate["destination_hints"] = ["/TotallyNewQuirkRoot/Assignments/"]
        rehash(candidate)
        self.assertIn("UNSUPPORTED_ARCHITECTURE", validate_daily_move_pair(self.input_doc, candidate))


    def test_unseen_spine_id_is_valid_for_uniqueness(self):
        self.assertNotIn(
            "DUPLICATE_SPINE_ID",
            validate_daily_move_pair(self.input_doc, self.output_doc, {}),
        )

    def test_same_input_same_spine_is_idempotent_retry(self):
        spine_id = self.input_doc["outcome_spine"]["spine_id"]
        observed = {spine_id: input_fingerprint(self.input_doc)}
        self.assertNotIn(
            "DUPLICATE_SPINE_ID",
            validate_daily_move_pair(self.input_doc, self.output_doc, observed),
        )

    def test_same_spine_with_different_input_fails(self):
        spine_id = self.input_doc["outcome_spine"]["spine_id"]
        observed = {spine_id: "0" * 64}
        self.assertIn(
            "DUPLICATE_SPINE_ID",
            validate_daily_move_pair(self.input_doc, self.output_doc, observed),
        )


    def test_duplicate_validation_does_not_mutate_observed_spines(self):
        spine_id = self.input_doc["outcome_spine"]["spine_id"]
        observed = {spine_id: "0" * 64}
        before = copy.deepcopy(observed)
        validate_daily_move_pair(self.input_doc, self.output_doc, observed)
        self.assertEqual(before, observed)


    def test_invalid_case_corpus_contract_is_unique_and_complete(self):
        cases = load_json(INVALID_CASES_PATH)
        self.assertEqual(22, len(cases))
        self.assertEqual(len(cases), len({case["case_id"] for case in cases}))
        self.assertEqual(
            [f"QDM-IO-A{index:02d}" for index in range(1, 23)],
            [case["case_id"] for case in cases],
        )
        for case in cases:
            self.assertEqual(
                {"case_id", "target", "operation", "path", "expected_code"},
                set(case) - {"value", "rehash"},
                case["case_id"],
            )

    def test_invalid_case_corpus_emits_expected_primary_codes(self):
        cases = load_json(INVALID_CASES_PATH)
        for case in cases:
            input_doc = copy.deepcopy(self.input_doc)
            output_doc = copy.deepcopy(self.output_doc)
            input_doc, output_doc, observed = apply_case(case, input_doc, output_doc)
            findings = validate_daily_move_pair(input_doc, output_doc, observed)
            self.assertIn(case["expected_code"], findings, case["case_id"])


    def test_conformance_report_is_valid_candidate_evidence_only(self):
        report = conformance_report(ROOT)
        self.assertTrue(report["valid_pair"])
        self.assertEqual([], report["finding_codes"])
        self.assertEqual("propose", report["authority_ceiling"])
        self.assertEqual(0, report["external_writes"])
        self.assertEqual(report["output_content_hash"], report["expected_output_hash"])


    def test_conformance_report_uses_requested_root_for_schemas(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "schemas").mkdir(parents=True)
            (root / "evals/daily-move/io-cases").mkdir(parents=True)
            shutil.copy2(INPUT_SCHEMA_PATH, root / "schemas/daily-move-input.schema.json")
            shutil.copy2(OUTPUT_SCHEMA_PATH, root / "schemas/daily-move-output.schema.json")
            shutil.copy2(VALID_INPUT_PATH, root / "evals/daily-move/io-cases/valid-input.json")
            shutil.copy2(VALID_OUTPUT_PATH, root / "evals/daily-move/io-cases/valid-output.json")
            schema_path = root / "schemas/daily-move-input.schema.json"
            schema = load_json(schema_path)
            schema["required"].append("root_specific_required_field")
            schema_path.write_text(json.dumps(schema), encoding="utf-8")
            report = conformance_report(root)
            self.assertFalse(report["valid_pair"])
            self.assertIn("INPUT_SCHEMA_INVALID", report["finding_codes"])


if __name__ == "__main__":
    unittest.main()
