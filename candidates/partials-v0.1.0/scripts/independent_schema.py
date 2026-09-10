"""Independent structural validation only; Node assertRecord owns cross-field semantics."""
import copy
import json
import re
from datetime import datetime
from pathlib import Path
from importlib.metadata import version
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

root = Path(__file__).resolve().parents[1]
schema = json.loads((root / "schemas/partial-record.schema.json").read_text())
Draft202012Validator.check_schema(schema)
formats = FormatChecker()
# jsonschema installs without its optional RFC3339 checker in some environments.
# Register an independent stdlib implementation so a missing extra never skips dates.
@formats.checks("date-time", raises=(ValueError, TypeError))
def valid_timestamp(value):
    if not isinstance(value, str):
        return True
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d+)?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)", value):
        return False
    return datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is not None
validator = Draft202012Validator(schema, format_checker=formats)
records = []
for path in sorted((root / "fixtures").glob("*.json")):
    record = json.loads(path.read_text())
    if record.get("schema_version") == "quirk.partials/v1alpha1":
        validator.validate(record)
        records.append((path.name, record))
assert len(records) >= 8, "Expected shared records from all three adapters and edge fixtures"
sample = records[0][1]
invalid = []
for field in ["effect_execution_allowed", "calendar_write_allowed", "canon_promotion_allowed", "graph_application_allowed", "training_allowed"]:
    record = copy.deepcopy(sample)
    record["authority"][field] = True
    invalid.append(record)
record = copy.deepcopy(sample)
record["unexpected"] = True
invalid.append(record)
record = copy.deepcopy(sample)
record["provenance"]["captured_at"] = "2026-02-30T12:00:00Z"
invalid.append(record)
record = copy.deepcopy(sample)
record["knowledge"]["lower_bound"] = -1
invalid.append(record)
record = copy.deepcopy(sample)
record["evidence"]["missing"] = ["duplicate", "duplicate"]
invalid.append(record)
record = copy.deepcopy(sample)
del record["authority"]
invalid.append(record)
for record in invalid:
    assert not validator.is_valid(record), "Independent validator accepted a structural negative"
registry = Registry().with_resource(schema['$id'], Resource.from_contents(schema))
review_checks = []
for name in ['review-request', 'review-result']:
    shape = json.loads((root / f'schemas/{name}.schema.json').read_text())
    Draft202012Validator.check_schema(shape)
    check = Draft202012Validator(shape, registry=registry, format_checker=formats)
    record = json.loads((root / f'fixtures/{name}.json').read_text())
    check.validate(record)
    if name == 'review-request':
        record['entries'] *= 33
    else:
        record['authority']['effect_execution_allowed'] = True
    assert not check.is_valid(record), 'Review structural negative accepted'
    review_checks.append(name)
print(json.dumps({"validator": "python-jsonschema", "version": version("jsonschema"), "dialect": "2020-12", "valid_fixtures": [name for name, _ in records], "invalid_cases_rejected": len(invalid), "review_schemas_and_fixtures_valid": review_checks, "review_negatives_rejected": 2, "scope": "structure and format; not semantic parity, authentication, authority, or human benefit"}, indent=2))
