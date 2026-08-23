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


if __name__ == "__main__":
    unittest.main()
