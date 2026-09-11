from __future__ import annotations

from copy import deepcopy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from applause_gate.json_io import load_json_strict
from applause_gate.classifier import classify_review_request, fixture_to_request

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "applause-review.schema.json"
EXAMPLE = ROOT / "examples" / "applause-gate" / "applause-review.valid.json"

REQUEST_REQUIRED = [
    "object_type",
    "schema_version",
    "request_id",
    "candidate_id",
    "subject",
    "claim",
    "signal",
    "evaluated_version",
    "observation_window",
    "evidence_assessments",
    "primary_outcome_state",
    "causal_support",
    "guardrail_state",
    "contradiction_state",
    "version_binding",
    "freshness_state",
    "integrity_state",
    "commitment_risk",
]

REVIEW_REQUIRED = [
    "object_type",
    "schema_version",
    "request_id",
    "candidate_id",
    "request_payload_sha256",
    "diagnostic_facts_sha256",
    "primary_outcome_state",
    "causal_support",
    "guardrail_state",
    "contradiction_state",
    "version_binding",
    "freshness_state",
    "integrity_state",
    "commitment_risk",
    "verdict",
    "required_codes",
    "withheld_claims",
    "missing_proof",
    "contradiction_refs",
    "evidence_refs",
    "warnings",
    "next_move",
    "authority_effect",
    "runtime_effect",
    "canon_effect",
    "admission_effect",
    "release_publication_effect",
]

VERDICTS = [
    "SIGNAL_ONLY",
    "SUPPORTED_DIAGNOSIS",
    "VERIFIED_SUCCESS",
    "FALSE_POSITIVE",
    "UNRESOLVED",
    "EVIDENCE_INTEGRITY_FAILURE",
]


class ApplauseReviewSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_json_strict(SCHEMA.read_text(encoding="utf-8"))
        cls.example = load_json_strict(EXAMPLE.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(cls.schema)

    def validator(self, definition):
        return Draft202012Validator(
            self.schema["$defs"][definition],
            format_checker=FormatChecker(),
        )

    def assert_valid(self, definition, value):
        errors = sorted(
            self.validator(definition).iter_errors(value),
            key=lambda error: list(error.absolute_path),
        )
        self.assertEqual([error.message for error in errors], [])

    def assert_invalid(self, definition, value):
        self.assertFalse(self.validator(definition).is_valid(value))

    def test_schema_is_candidate_only_and_non_authorizing(self):
        self.assertEqual(SCHEMA.relative_to(ROOT).as_posix(), "schemas/applause-review.schema.json")
        self.assertEqual(
            {
                key: self.schema[key]
                for key in (
                    "x-quirk-status",
                    "x-quirk-semantic-authority",
                    "x-quirk-runtime-authority",
                    "x-quirk-canon-effect",
                )
            },
            {
                "x-quirk-status": "candidate",
                "x-quirk-semantic-authority": False,
                "x-quirk-runtime-authority": False,
                "x-quirk-canon-effect": "none",
            },
        )

    def test_valid_request_and_review_are_accepted(self):
        self.assert_valid("review_request", self.example["request"])
        self.assert_valid("applause_review", self.example["review"])

    def test_root_contract_preserves_existing_classifier_interface(self):
        corpus = load_json_strict(
            (ROOT / "evals/applause-gate/cases.json").read_text(encoding="utf-8")
        )
        validator = Draft202012Validator(self.schema)
        for case in corpus["cases"]:
            with self.subTest(case=case["id"]):
                review = classify_review_request(fixture_to_request(case))
                self.assertTrue(validator.is_valid(review))
                for field in review:
                    incomplete = deepcopy(review)
                    del incomplete[field]
                    self.assertFalse(validator.is_valid(incomplete), field)

    def test_root_contract_rejects_malformed_and_authorizing_payloads(self):
        validator = Draft202012Validator(self.schema)
        malformed = (None, False, 0, "review", [], {}, {"authority_effect": "admit"})
        for value in malformed:
            with self.subTest(value=value):
                self.assertFalse(validator.is_valid(value))

        corpus = load_json_strict(
            (ROOT / "evals/applause-gate/cases.json").read_text(encoding="utf-8")
        )
        review = classify_review_request(fixture_to_request(corpus["cases"][0]))
        for field, value in (
            ("authority_effect", "admit"),
            ("verdict", "AUTHORIZED_SUCCESS"),
            ("success_score", 0.99),
            ("runtime_effect", "activate"),
            ("required_codes", "not-an-array"),
        ):
            with self.subTest(field=field):
                invalid = deepcopy(review)
                invalid[field] = value
                self.assertFalse(validator.is_valid(invalid))

    def test_every_required_field_is_enforced(self):
        for definition, example_key, fields in (
            ("review_request", "request", REQUEST_REQUIRED),
            ("applause_review", "review", REVIEW_REQUIRED),
        ):
            for field in fields:
                with self.subTest(definition=definition, field=field):
                    mutated = deepcopy(self.example[example_key])
                    del mutated[field]
                    self.assert_invalid(definition, mutated)

    def test_enum_and_constant_values_are_closed(self):
        mutations = [
            ("review_request", "request", ("object_type",), "other_request"),
            ("review_request", "request", ("schema_version",), "applause-review-request.v2"),
            ("review_request", "request", ("candidate_id",), "other-candidate"),
            ("review_request", "request", ("observation_window", "state"), "assumed_complete"),
            ("review_request", "request", ("evidence_assessments", 0, "evidence_kind"), "score"),
            ("review_request", "request", ("evidence_assessments", 0, "assertion_state"), "proves"),
            ("review_request", "request", ("primary_outcome_state",), "successful"),
            ("review_request", "request", ("causal_support",), "certain"),
            ("review_request", "request", ("guardrail_state",), "ignored"),
            ("review_request", "request", ("contradiction_state",), "hidden"),
            ("review_request", "request", ("version_binding",), "implicit"),
            ("review_request", "request", ("freshness_state",), "assumed_current"),
            ("review_request", "request", ("integrity_state",), "unchecked"),
            ("review_request", "request", ("commitment_risk",), "absolute"),
            ("applause_review", "review", ("verdict",), "AUTHORIZED_SUCCESS"),
            ("applause_review", "review", ("next_move", "kind"), "execute_rollout"),
        ]
        for definition, example_key, path, value in mutations:
            with self.subTest(definition=definition, path=path):
                mutated = deepcopy(self.example[example_key])
                target = mutated
                for part in path[:-1]:
                    target = target[part]
                target[path[-1]] = value
                self.assert_invalid(definition, mutated)

        self.assertEqual(
            self.schema["$defs"]["applause_review"]
            .get("properties", {})
            .get("verdict", {})
            .get("enum"),
            VERDICTS,
        )

    def test_types_and_nested_required_fields_are_enforced(self):
        mutations = [
            ("review_request", "request", ("claim",), 1),
            ("review_request", "request", ("observation_window",), "one week"),
            ("review_request", "request", ("evidence_assessments",), {}),
            ("review_request", "request", ("observation_window", "start"), "not-a-date"),
            ("applause_review", "review", ("required_codes",), "GUARDRAILS_STABLE"),
            ("applause_review", "review", ("contradiction_refs",), [1]),
            ("applause_review", "review", ("next_move",), "record evidence"),
        ]
        for definition, example_key, path, value in mutations:
            with self.subTest(definition=definition, path=path):
                mutated = deepcopy(self.example[example_key])
                target = mutated
                for part in path[:-1]:
                    target = target[part]
                target[path[-1]] = value
                self.assert_invalid(definition, mutated)

        for field in ("start", "end", "state"):
            with self.subTest(field=field):
                request = deepcopy(self.example["request"])
                del request["observation_window"][field]
                self.assert_invalid("review_request", request)

        for field in (
            "evidence_ref",
            "evidence_kind",
            "assertion_state",
            "version_ref",
            "content_digest",
            "integrity_state",
        ):
            with self.subTest(field=field):
                request = deepcopy(self.example["request"])
                del request["evidence_assessments"][0][field]
                self.assert_invalid("review_request", request)

        for field in ("kind", "description", "execution_authorized"):
            with self.subTest(field=field):
                review = deepcopy(self.example["review"])
                del review["next_move"][field]
                self.assert_invalid("applause_review", review)

    def test_unexpected_fields_are_rejected_at_every_object_boundary(self):
        mutations = [
            ("review_request", "request", (), "unexpected"),
            ("review_request", "request", ("observation_window",), "unexpected"),
            ("review_request", "request", ("evidence_assessments", 0), "unexpected"),
            ("applause_review", "review", (), "unexpected"),
            ("applause_review", "review", ("next_move",), "unexpected"),
        ]
        for definition, example_key, path, field in mutations:
            with self.subTest(definition=definition, path=path):
                mutated = deepcopy(self.example[example_key])
                target = mutated
                for part in path:
                    target = target[part]
                target[field] = True
                self.assert_invalid(definition, mutated)

    def test_reference_lists_are_nonempty_unique_and_bound(self):
        request = deepcopy(self.example["request"])
        request["evidence_assessments"] = []
        self.assert_invalid("review_request", request)

        request = deepcopy(self.example["request"])
        request["evidence_assessments"].append(deepcopy(request["evidence_assessments"][0]))
        self.assert_invalid("review_request", request)

        review = deepcopy(self.example["review"])
        review["evidence_refs"] = []
        self.assert_invalid("applause_review", review)

        review = deepcopy(self.example["review"])
        review["evidence_refs"].append(review["evidence_refs"][0])
        self.assert_invalid("applause_review", review)

        request = deepcopy(self.example["request"])
        duplicate = deepcopy(request["evidence_assessments"][0])
        duplicate["evidence_kind"] = "integrity"
        duplicate["content_digest"] = "f" * 64
        request["evidence_assessments"].append(duplicate)
        with self.assertRaisesRegex(ValueError, "duplicate evidence_ref"):
            load_json_strict(json.dumps(request))

    def test_digests_are_lowercase_sha256(self):
        mutations = [
            ("review_request", "request", ("evidence_assessments", 0, "content_digest")),
            ("applause_review", "review", ("request_payload_sha256",)),
            ("applause_review", "review", ("diagnostic_facts_sha256",)),
        ]
        for definition, example_key, path in mutations:
            with self.subTest(definition=definition, path=path):
                mutated = deepcopy(self.example[example_key])
                target = mutated
                for part in path[:-1]:
                    target = target[part]
                target[path[-1]] = "ABC123"
                self.assert_invalid(definition, mutated)

    def test_scores_and_implicit_authority_fields_are_rejected(self):
        forbidden_fields = (
            "success_score",
            "confidence_score",
            "execution_effect",
            "provider_effect",
            "publication_effect",
            "release_authorized",
        )
        for definition, example_key in (
            ("review_request", "request"),
            ("applause_review", "review"),
        ):
            for field in forbidden_fields:
                with self.subTest(definition=definition, field=field):
                    mutated = deepcopy(self.example[example_key])
                    mutated[field] = 0.99 if field.endswith("score") else "none"
                    self.assert_invalid(definition, mutated)

    def test_review_effects_and_next_move_never_authorize_action(self):
        for field in (
            "authority_effect",
            "runtime_effect",
            "canon_effect",
            "admission_effect",
            "release_publication_effect",
        ):
            with self.subTest(field=field):
                review = deepcopy(self.example["review"])
                review[field] = "authorize"
                self.assert_invalid("applause_review", review)

        review = deepcopy(self.example["review"])
        review["next_move"]["execution_authorized"] = True
        self.assert_invalid("applause_review", review)

    def test_set_like_arrays_declare_normalization(self):
        request_properties = self.schema["$defs"].get("review_request", {}).get("properties", {})
        evidence_assessments = request_properties.get("evidence_assessments", {})
        self.assertIs(evidence_assessments.get("x-quirk-set-like"), True)
        self.assertIs(evidence_assessments.get("uniqueItems"), True)
        self.assertEqual(
            evidence_assessments.get("x-quirk-sort-by"),
            ["evidence_ref", "evidence_kind", "content_digest"],
        )

        review_properties = self.schema["$defs"].get("applause_review", {}).get("properties", {})
        for field in (
            "required_codes",
            "withheld_claims",
            "missing_proof",
            "contradiction_refs",
            "evidence_refs",
            "warnings",
        ):
            with self.subTest(field=field):
                value = review_properties.get(field, {})
                self.assertIs(value.get("x-quirk-set-like"), True)
                self.assertIs(value.get("uniqueItems"), True)
                self.assertEqual(value.get("x-quirk-sort"), "utf8-bytes")

    def test_strict_loader_rejects_duplicate_keys_and_nonfinite_numbers(self):
        malformed = (
            '{"claim":"first","claim":"second"}',
            '{"value":NaN}',
            '{"value":Infinity}',
            '{"value":-Infinity}',
        )
        for text in malformed:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    load_json_strict(text)


if __name__ == "__main__":
    unittest.main()
