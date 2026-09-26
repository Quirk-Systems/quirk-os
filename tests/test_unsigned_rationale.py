"""Independent contract checks for unsigned comparison records.

Fixtures are illustrative. These checks establish local format and integrity
behavior; they do not establish source truth or approval to execute effects.
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from unsigned_rationale import (  # noqa: E402
    ProtocolError,
    canonical_bytes,
    capture_source,
    parse_packet,
    reopen_packet,
    validate_packet,
)


def packet_fixture():
    """Two explicitly inspected example sources, with no authority grants."""
    return {
        "format": "quirk.unsigned-rationale",
        "format_version": "0.1.0",
        "id": "trial:clarity-001",
        "revision": "candidate-1",
        "status": "CANDIDATE",
        "sources": [
            {
                "id": "source:first",
                "locator": "https://example.com/interface/first",
                "inspected_at": "2026-09-10T12:34:56+00:00",
                "revision": "screen-a-v1",
                "sha256": "a" * 64,
                "revision_unavailable_reason": None,
                "digest_unavailable_reason": None,
            },
            {
                "id": "source:second",
                "locator": "https://example.com/interface/second",
                "inspected_at": "2026-09-10T07:34:56-05:00",
                "revision": "screen-b-v1",
                "sha256": "b" * 64,
                "revision_unavailable_reason": None,
                "digest_unavailable_reason": None,
            },
        ],
        "question": "Which screen makes the next move easier to find?",
        "claims": [
            {
                "id": "claim:next-move",
                "text": "The first screen places the next move beside its finish condition.",
                "assertion_class": "observed",
                "source_ids": ["source:first"],
                "support_locator": "https://example.com/interface/first#next-move",
                "unsupported_reason": None,
            },
        ],
        "rationale": "I can find the next action and its finish condition together.",
        "outcome": "choose_first",
        "unresolved_questions": ["Does the layout remain clear on an iPhone?"],
        "restrictions": {
            "effects_allowed": False,
            "training_allowed": False,
            "preference_graph_apply_allowed": False,
        },
        "signature": None,
    }


def ordinary_json(packet):
    return json.dumps(packet, ensure_ascii=False).encode("utf-8")


class UnsignedRationaleContractTests(unittest.TestCase):
    def assert_rejected(self, action, code=None):
        with self.assertRaises(ProtocolError) as caught:
            action()
        self.assertIsInstance(caught.exception, ValueError)
        self.assertIsInstance(caught.exception.code, str)
        self.assertIsInstance(caught.exception.path, str)
        if code is not None:
            self.assertEqual(caught.exception.code, code)
        return caught.exception

    def test_valid_record_is_accepted_without_mutating_input(self):
        packet = packet_fixture()
        before = deepcopy(packet)
        self.assertEqual(validate_packet(packet), before)
        self.assertEqual(packet, before)

    def test_literal_unicode_combining_characters_and_whitespace_survive(self):
        packet = packet_fixture()
        packet["rationale"] = "  Café / Cafe\u0301 — 次の一手 🧭\n\tSecond line.\r\n  "
        packet["unresolved_questions"] = ["Why é and e\u0301?", "保持"]
        before = deepcopy(packet)
        raw = canonical_bytes(packet)
        self.assertIn("Café / Cafe\u0301".encode("utf-8"), raw)
        self.assertNotIn(b"\\u00e9", raw)
        self.assertEqual(parse_packet(raw), before)
        self.assertEqual(packet, before)

    def test_canonical_export_ignores_mapping_order_and_has_one_final_lf(self):
        def reversed_mappings(value):
            if isinstance(value, dict):
                return {key: reversed_mappings(value[key]) for key in reversed(value)}
            if isinstance(value, list):
                return [reversed_mappings(item) for item in value]
            return value

        packet = packet_fixture()
        canonical = canonical_bytes(packet)
        self.assertEqual(canonical, canonical_bytes(reversed_mappings(packet)))
        self.assertTrue(canonical.startswith(b'{"claims":['))
        self.assertTrue(canonical.endswith(b"}\n"))
        self.assertFalse(canonical.endswith(b"\n\n"))
        self.assertNotIn(b"\r", canonical)
        self.assertNotIn(b'": ', canonical)
        self.assertEqual(parse_packet(canonical)["sources"], packet["sources"])

    def test_export_succeeds_before_self_promotion_is_rejected(self):
        packet = packet_fixture()
        exported = canonical_bytes(packet)
        self.assertEqual(reopen_packet(exported)["packet"], packet)
        for field, value in [("status", "ACTIVE"), ("signature", "approved-by-agent")]:
            with self.subTest(field=field):
                promoted = json.loads(exported)
                promoted[field] = value
                self.assert_rejected(lambda: parse_packet(ordinary_json(promoted)))

    def test_unknown_fields_and_missing_required_fields_are_rejected(self):
        for location in ("packet", "source", "claim", "restrictions"):
            with self.subTest(extra_at=location):
                packet = packet_fixture()
                target = {
                    "packet": packet,
                    "source": packet["sources"][0],
                    "claim": packet["claims"][0],
                    "restrictions": packet["restrictions"],
                }[location]
                target["grants"] = ["execute"]
                self.assert_rejected(lambda: validate_packet(packet))
        for field in ("sources", "restrictions", "signature"):
            with self.subTest(missing=field):
                packet = packet_fixture()
                del packet[field]
                self.assert_rejected(lambda: validate_packet(packet))

    def test_restrictions_must_be_literal_false(self):
        for field in packet_fixture()["restrictions"]:
            for value in (True, None, "false", 0):
                with self.subTest(field=field, value=value):
                    packet = packet_fixture()
                    packet["restrictions"][field] = value
                    self.assert_rejected(lambda: validate_packet(packet))

    def test_unsupported_version_is_distinguished(self):
        packet = packet_fixture()
        packet["format_version"] = "99.0.0"
        self.assert_rejected(lambda: validate_packet(packet), "UNSUPPORTED_VERSION")

    def test_exactly_two_distinct_sources_are_required(self):
        for count in (0, 1, 3):
            with self.subTest(count=count):
                packet = packet_fixture()
                packet["sources"] = (packet["sources"] * 2)[:count]
                self.assert_rejected(lambda: validate_packet(packet))
        packet = packet_fixture()
        packet["sources"][1]["id"] = packet["sources"][0]["id"]
        self.assert_rejected(lambda: validate_packet(packet))

    def test_claim_references_and_ids_must_be_unique_and_resolve(self):
        for source_ids in ([], ["source:missing"], ["source:first", "source:first"]):
            with self.subTest(source_ids=source_ids):
                packet = packet_fixture()
                packet["claims"][0]["source_ids"] = source_ids
                self.assert_rejected(lambda: validate_packet(packet))
        packet = packet_fixture()
        packet["claims"].append(deepcopy(packet["claims"][0]))
        self.assert_rejected(lambda: validate_packet(packet))

    def test_claim_support_requires_one_honest_support_or_gap_description(self):
        packet = packet_fixture()
        claim = packet["claims"][0]
        claim["support_locator"] = None
        claim["unsupported_reason"] = "The screenshot itself has not been supplied."
        self.assertEqual(validate_packet(packet), packet)
        for support, reason in ((None, None), ("", ""), ("https://example.com/proof", "Also missing")):
            with self.subTest(support=support, reason=reason):
                invalid = deepcopy(packet)
                invalid["claims"][0]["support_locator"] = support
                invalid["claims"][0]["unsupported_reason"] = reason
                self.assert_rejected(lambda: validate_packet(invalid))

    def test_missing_source_evidence_requires_reasons_and_known_evidence_has_none(self):
        packet = packet_fixture()
        source = packet["sources"][0]
        source.update(revision=None, sha256=None,
                      revision_unavailable_reason="Source has no revision label.",
                      digest_unavailable_reason="Original bytes unavailable.")
        self.assertEqual(validate_packet(packet), packet)
        for field in ("revision_unavailable_reason", "digest_unavailable_reason"):
            with self.subTest(missing_reason=field):
                invalid = deepcopy(packet)
                invalid["sources"][0][field] = None
                self.assert_rejected(lambda: validate_packet(invalid))
            with self.subTest(spurious_reason=field):
                invalid = packet_fixture()
                invalid["sources"][0][field] = "Unknown"
                self.assert_rejected(lambda: validate_packet(invalid))
        for digest in ("A" * 64, "a" * 63, "g" * 64):
            with self.subTest(digest=digest):
                invalid = packet_fixture()
                invalid["sources"][0]["sha256"] = digest
                self.assert_rejected(lambda: validate_packet(invalid))

    def test_inspection_timestamp_requires_a_valid_date_and_explicit_offset(self):
        for timestamp in ("2026-09-10", "2026-09-10T12:34:56", "2026-02-30T12:00:00Z"):
            with self.subTest(timestamp=timestamp):
                packet = packet_fixture()
                packet["sources"][0]["inspected_at"] = timestamp
                self.assert_rejected(lambda: validate_packet(packet))

    def test_locators_reject_executable_urls_credentials_and_signed_tokens(self):
        unsafe = (
            "javascript:alert(1)",
            "data:text/html,hello",
            "https://user:password@example.com/image",
            "https://example.com/image?token=secret",
            "https://example.com/image?X-Amz-Signature=secret",
            "https://example.com/image?X-Goog-Signature=secret",
        )
        for locator in unsafe:
            for location in ("source", "support"):
                with self.subTest(locator=locator, location=location):
                    packet = packet_fixture()
                    if location == "source":
                        packet["sources"][0]["locator"] = locator
                    else:
                        packet["claims"][0]["support_locator"] = locator
                    self.assert_rejected(lambda: validate_packet(packet))

    def test_identifiers_reject_invisible_controls_and_non_identifier_characters(self):
        for identifier in ("", "has space", "bad/id", "invisible\u200b", "line\nfeed", "bidi\u202e"):
            with self.subTest(identifier=repr(identifier)):
                packet = packet_fixture()
                packet["id"] = identifier
                self.assert_rejected(lambda: validate_packet(packet))

    def test_text_enums_and_claim_count_are_bounded(self):
        for field, value in (("question", ""), ("rationale", ""), ("outcome", "approved")):
            with self.subTest(field=field):
                packet = packet_fixture()
                packet[field] = value
                self.assert_rejected(lambda: validate_packet(packet))
        packet = packet_fixture()
        packet["claims"][0]["assertion_class"] = "CANON"
        self.assert_rejected(lambda: validate_packet(packet))
        packet = packet_fixture()
        template = packet["claims"][0]
        packet["claims"] = [dict(template, id=f"claim:{i}") for i in range(128)]
        self.assertEqual(len(validate_packet(packet)["claims"]), 128)
        packet["claims"].append(dict(template, id="claim:128"))
        self.assert_rejected(lambda: validate_packet(packet))

    def test_invalid_utf8_and_trailing_json_content_are_rejected(self):
        for raw in (b"\xff", ordinary_json(packet_fixture()) + b" {}"):
            with self.subTest(raw_length=len(raw)):
                self.assert_rejected(lambda: parse_packet(raw), "INVALID_JSON")

    def test_duplicate_keys_are_rejected_even_when_the_values_match(self):
        raw = ordinary_json(packet_fixture())
        for duplicate in (
            raw.replace(b'"status": "CANDIDATE"', b'"status": "CANDIDATE", "status": "CANDIDATE"'),
            raw.replace(b'"effects_allowed": false', b'"effects_allowed": false, "effects_allowed": false'),
        ):
            with self.subTest(raw_length=len(duplicate)):
                self.assert_rejected(lambda: parse_packet(duplicate), "INVALID_JSON")

    def test_all_json_number_forms_are_rejected(self):
        raw = ordinary_json(packet_fixture())
        for number in (b"0", b"-1", b"1.5", b"1e2"):
            with self.subTest(number=number):
                numbered = raw.replace(b'"signature": null', b'"signature": ' + number)
                self.assert_rejected(lambda: parse_packet(numbered))

    def test_nonfinite_values_and_lone_surrogates_are_rejected(self):
        raw = ordinary_json(packet_fixture())
        for value in (b"NaN", b"Infinity", b"-Infinity", b'"\\ud800"', b'"\\udfff"'):
            with self.subTest(value=value):
                malformed = raw.replace(b'"signature": null', b'"signature": ' + value)
                self.assert_rejected(lambda: parse_packet(malformed))

    def test_raw_packet_size_limit_is_enforced(self):
        packet = packet_fixture()
        packet["rationale"] = "x" * (1024 * 1024)
        self.assert_rejected(lambda: parse_packet(ordinary_json(packet)), "LIMIT_EXCEEDED")

    def test_excessive_nesting_is_rejected_as_a_limit(self):
        raw = b"[" * 33 + b"null" + b"]" * 33
        self.assert_rejected(lambda: parse_packet(raw), "LIMIT_EXCEEDED")

    def test_raw_sidecar_digest_matches_the_received_bytes(self):
        packet = packet_fixture()
        raw = json.dumps(packet, ensure_ascii=False, indent=2).encode("utf-8")
        raw_digest = hashlib.sha256(raw).hexdigest()
        result = reopen_packet(raw, expected_sha256=raw_digest)
        self.assertEqual(result["packet"], packet)
        self.assertEqual(result["integrity"]["raw_sha256"], raw_digest)
        self.assertEqual(result["integrity"]["canonical_sha256"],
                         hashlib.sha256(canonical_bytes(packet)).hexdigest())
        self.assertNotEqual(result["integrity"]["raw_sha256"], result["integrity"]["canonical_sha256"])
        self.assertEqual(result["integrity"]["sidecar"], "matched")

    def test_equivalent_json_with_changed_bytes_does_not_match_the_old_sidecar(self):
        raw = canonical_bytes(packet_fixture())
        changed = raw.rstrip(b"\n")
        self.assertEqual(json.loads(raw), json.loads(changed))
        self.assert_rejected(
            lambda: reopen_packet(changed, expected_sha256=hashlib.sha256(raw).hexdigest()),
            "INTEGRITY_MISMATCH",
        )

    def test_reopening_without_observations_does_not_claim_source_freshness(self):
        result = reopen_packet(canonical_bytes(packet_fixture()))
        self.assertEqual(result["integrity"]["sidecar"], "absent")
        self.assertEqual(result["source_states"], [
            {"source_id": "source:first", "state": "not_checked", "compared": []},
            {"source_id": "source:second", "state": "not_checked", "compared": []},
        ])

    def test_any_comparable_mismatch_overrides_a_matching_observation(self):
        raw = canonical_bytes(packet_fixture())
        observations = {
            "source:first": {"available": True, "revision": "screen-a-v1", "sha256": "c" * 64},
            "source:second": {"available": True, "revision": "changed", "sha256": "b" * 64},
        }
        before = deepcopy(observations)
        result = reopen_packet(raw, observations=observations)
        self.assertEqual([state["state"] for state in result["source_states"]], ["stale", "stale"])
        self.assertEqual(result["source_states"][0]["compared"], ["revision", "sha256"])
        self.assertEqual(observations, before)

    def test_one_comparable_match_is_sufficient_for_unchanged(self):
        observations = {
            "source:first": {"available": True, "revision": "screen-a-v1", "sha256": None},
            "source:second": {"available": True, "revision": None, "sha256": "b" * 64},
        }
        result = reopen_packet(canonical_bytes(packet_fixture()), observations=observations)
        self.assertEqual(result["source_states"], [
            {"source_id": "source:first", "state": "unchanged", "compared": ["revision"]},
            {"source_id": "source:second", "state": "unchanged", "compared": ["sha256"]},
        ])

    def test_unavailable_and_available_but_unverifiable_sources_stay_distinct(self):
        observations = {
            "source:first": {"available": False, "revision": None, "sha256": None},
            "source:second": {"available": True, "revision": None, "sha256": None},
        }
        result = reopen_packet(canonical_bytes(packet_fixture()), observations=observations)
        self.assertEqual(result["source_states"], [
            {"source_id": "source:first", "state": "unavailable", "compared": []},
            {"source_id": "source:second", "state": "unverified", "compared": []},
        ])
        packet = packet_fixture()
        packet["sources"][0].update(revision=None, sha256=None,
                                    revision_unavailable_reason="Not supplied",
                                    digest_unavailable_reason="Not supplied")
        current = {"source:first": {"available": True, "revision": "newly-supplied", "sha256": "c" * 64}}
        result = reopen_packet(canonical_bytes(packet), observations=current)
        self.assertEqual(result["source_states"][0]["state"], "unverified")
        self.assertEqual(result["source_states"][1]["state"], "not_checked")

    def test_unknown_or_malformed_observations_cannot_claim_freshness(self):
        raw = canonical_bytes(packet_fixture())
        cases = (
            {"source:missing": {"available": True, "revision": None, "sha256": None}},
            {"source:first": {"available": "yes", "revision": None, "sha256": None}},
            {"source:first": {"available": True, "revision": None, "sha256": "bad"}},
            {"source:first": {"available": True, "revision": None, "sha256": None, "approved": True}},
        )
        for observations in cases:
            with self.subTest(observations=observations):
                self.assert_rejected(lambda: reopen_packet(raw, observations=observations))

    def test_capture_hashes_original_bytes_without_decoding_or_normalizing(self):
        raw = b"\xff\x00example\r\n"
        source = capture_source(raw, source_id="source:raw", locator="https://example.com/raw",
                                inspected_at="2026-09-10T12:34:56Z")
        self.assertEqual(source["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertIsNone(source["revision"])
        self.assertEqual(source["revision_unavailable_reason"], "Not supplied")
        self.assertIsNone(source["digest_unavailable_reason"])

    def test_capture_never_infers_revision_from_source_content(self):
        raw = b'{"revision":"content-is-not-an-inspection-revision"}'
        kwargs = {"source_id": "source:raw", "locator": "https://example.com/raw",
                  "inspected_at": "2026-09-10T12:34:56Z"}
        without_revision = capture_source(raw, **kwargs)
        self.assertIsNone(without_revision["revision"])
        explicit = capture_source(raw, revision="inspected-v2", **kwargs)
        self.assertEqual(explicit["revision"], "inspected-v2")
        self.assertIsNone(explicit["revision_unavailable_reason"])
        self.assertEqual(explicit["sha256"], without_revision["sha256"])


if __name__ == "__main__":
    unittest.main()
