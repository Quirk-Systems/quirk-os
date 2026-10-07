from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from scripts.sync_control_plane.skill_runtime import (
    build_model_tool_request_receipt,
    map_skill_tools_to_runtime_bindings,
    resolve_model_visible_tools,
    serialize_model_request,
)


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class ModelToolAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime_schema = load_json("schemas/runtime-manifest.schema.json")
        cls.registry_schema = load_json("schemas/tool-registry.schema.json")
        cls.receipt_schema = load_json("schemas/model-tool-request-receipt.schema.json")
        cls.registry = load_json("evals/sync-control-plane/tool-registry.v1.json")
        cls.fixture = load_json("evals/sync-control-plane/model-tool-request.fixture.json")

    def test_versioned_registry_and_manifest_fixture_validate(self) -> None:
        validator = Draft202012Validator
        self.assertEqual(
            [],
            list(validator(self.registry_schema, format_checker=FormatChecker()).iter_errors(self.registry)),
        )
        self.assertEqual(
            [],
            list(validator(self.runtime_schema, format_checker=FormatChecker()).iter_errors(self.fixture["manifest"])),
        )

    def test_allowed_schema_is_present_and_forbidden_schema_is_absent(self) -> None:
        resolved = resolve_model_visible_tools(self.fixture["manifest"], self.registry)
        self.assertTrue(resolved["resolved"], resolved["errors"])
        emitted = resolved["tools"]
        self.assertEqual(["quirk_runtime__read_sources"], [tool["function"]["name"] for tool in emitted])
        self.assertEqual(
            {"source_refs"},
            set(emitted[0]["function"]["parameters"]["properties"]),
        )
        self.assertNotIn("quirk_runtime__promote_canon", [tool["function"]["name"] for tool in emitted])
        self.assertNotIn("object_ref", emitted[0]["function"]["parameters"]["properties"])

    def test_canonical_skill_tool_mapping_resolves_to_a_versioned_runtime_ref(self) -> None:
        canonical_skill = {
            "tools": [
                {
                    "name": "quirk_runtime",
                    "actions": ["read_sources"],
                    "required": True,
                }
            ]
        }
        mapped = map_skill_tools_to_runtime_bindings(canonical_skill, self.registry)
        self.assertTrue(mapped["mapped"], mapped["errors"])
        self.assertEqual(
            [{"ref": "tool.quirk_runtime@1.0.0", "allowed_actions": ["read_sources"]}],
            mapped["bindings"],
        )

    def test_canonical_skill_mapping_fails_closed_for_unregistered_action(self) -> None:
        canonical_skill = {
            "tools": [{"name": "quirk_runtime", "actions": ["rewrite_history"], "required": True}]
        }
        mapped = map_skill_tools_to_runtime_bindings(canonical_skill, self.registry)
        self.assertFalse(mapped["mapped"])
        self.assertEqual([], mapped["bindings"])
        self.assertIn(
            "canonical tool actions are not registered: quirk_runtime#rewrite_history",
            mapped["errors"],
        )

    def test_serialized_request_is_the_model_visible_proof(self) -> None:
        request = serialize_model_request(
            self.fixture["manifest"],
            self.registry,
            model="proof-model",
            messages=self.fixture["messages"],
        )
        wire = json.dumps(request, sort_keys=True, separators=(",", ":"))
        self.assertIn('"name":"quirk_runtime__read_sources"', wire)
        self.assertIn('"source_refs"', wire)
        self.assertNotIn("promote_canon", wire)
        self.assertNotIn("object_ref", wire)

    def test_candidate_manifest_cannot_emit_model_tools(self) -> None:
        candidate = copy.deepcopy(self.fixture["manifest"])
        candidate["status"] = "candidate"
        candidate["requested_status"] = "candidate"
        resolved = resolve_model_visible_tools(candidate, self.registry)
        self.assertFalse(resolved["resolved"])
        self.assertEqual([], resolved["tools"])
        self.assertIn("model tool adapter rejects non-active runtime manifest", resolved["errors"])

    def test_unknown_or_forbidden_action_fails_closed(self) -> None:
        forged = copy.deepcopy(self.fixture["manifest"])
        forged["tools"][0]["allowed_actions"].append("not_registered")
        resolved = resolve_model_visible_tools(forged, self.registry)
        self.assertFalse(resolved["resolved"])
        self.assertEqual([], resolved["tools"])
        self.assertIn(
            "tool action is not registered: tool.quirk_runtime@1.0.0#not_registered",
            resolved["errors"],
        )

    def test_receipt_logs_unknown_and_observed_deltas_without_fabrication(self) -> None:
        request = serialize_model_request(
            self.fixture["manifest"],
            self.registry,
            model="proof-model",
            messages=self.fixture["messages"],
        )
        pending = build_model_tool_request_receipt(
            request,
            receipt_id="receipt.model-tool-request.pending.0001",
            serialized_at="2026-09-25T00:00:00Z",
        )
        self.assertEqual("not_observed", pending["measurement_state"])
        self.assertTrue(all(value is None for value in pending["metrics"].values()))

        observed = build_model_tool_request_receipt(
            request,
            receipt_id="receipt.model-tool-request.observed.0001",
            serialized_at="2026-09-25T00:01:00Z",
            metrics={
                "input_tokens": 128,
                "output_tokens": 32,
                "cash_cost_usd": 0.0012,
                "latency_ms": 210,
                "human_effort_minutes": 1.5,
                "updater_upkeep_minutes": 0.25,
            },
        )
        self.assertEqual("observed", observed["measurement_state"])
        errors = list(Draft202012Validator(self.receipt_schema, format_checker=FormatChecker()).iter_errors(observed))
        self.assertEqual([], errors)
        self.assertEqual(pending["request_sha256"], observed["request_sha256"])


if __name__ == "__main__":
    unittest.main()
