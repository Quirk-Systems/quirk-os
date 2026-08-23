from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.validate_daily_move_io import (
    expected_output_hash,
    input_fingerprint,
    validate_daily_move_pair,
)

ROOT = Path(__file__).resolve().parents[1]
INPUT_SCHEMA_PATH = ROOT / "schemas/daily-move-input.schema.json"
OUTPUT_SCHEMA_PATH = ROOT / "schemas/daily-move-output.schema.json"
VALID_INPUT_PATH = ROOT / "evals/daily-move/io-cases/valid-input.json"
VALID_OUTPUT_PATH = ROOT / "evals/daily-move/io-cases/valid-output.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def rehash(output_doc):
    output_doc["content_hash"] = expected_output_hash(output_doc)
    return output_doc


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


if __name__ == "__main__":
    unittest.main()
