from __future__ import annotations

import copy
import json
import unittest
from unittest.mock import Mock
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from scripts.sync_control_plane.skill_runtime import (
    build_model_tool_request_receipt,
    map_skill_tools_to_runtime_bindings,
    resolve_model_visible_tools,
    manifest_digest,
    projection_digest,
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

    def setUp(self):
        self.fixture = copy.deepcopy(type(self).fixture)
        self.registry = copy.deepcopy(type(self).registry)
        self.skill = self.fixture["skill_manifest"]
        self.source = (ROOT / self.skill["provenance"]["source_path"]).read_text()
        self.grant = self.fixture["grant"]
        self.authoritative = copy.deepcopy(self.grant)
        self.approval_registry = Mock(allows=Mock(return_value=True))
        admission = copy.deepcopy(self.fixture["manifest"]["admission"])
        record = {key: admission[key] for key in (
            "decision_ref", "authority_grant_ref", "transition_ref", "approved_by", "decided_at")}
        record["subject"] = {key: admission[key] for key in ("requested_by", "evidence_refs")}
        self.verifier = Mock(verify=Mock(return_value=record))
        self.activation_context = {"fixture_only": True}

    def context(self):
        return dict(skill_manifest=self.skill, source_text=self.source, grant=self.grant,
                    lookup_grant=lambda grant_id: self.authoritative if self.authoritative and
                    grant_id == self.authoritative["grant_id"] else None,
                    object_scope=["source.fixture"], now="2026-10-03T08:00:00Z",
                    approval_registry=self.approval_registry, verifier=self.verifier,
                    context=self.activation_context)

    def resolve(self, manifest=None, **overrides):
        context = self.context()
        context.update(overrides)
        return resolve_model_visible_tools(manifest if manifest is not None else self.fixture["manifest"],
                                           self.registry, **context)

    def assert_denied(self, result, reason):
        self.assertFalse(result["resolved"])
        self.assertEqual([], result["tools"])
        self.assertTrue(any(reason in error for error in result["errors"]), result["errors"])

    def assert_both_paths_denied(self, reason, **overrides):
        self.assert_denied(self.resolve(**overrides), reason)
        context = self.context()
        context.update(overrides)
        with self.assertRaisesRegex(ValueError, reason):
            serialize_model_request(self.fixture["manifest"], self.registry,
                                    model="proof", messages=self.fixture["messages"], **context)

    def test_approval_registry_is_required_on_both_paths(self):
        self.assert_both_paths_denied("trusted GitHub approval registry is required",
                                     approval_registry=None)

    def test_manifest_and_skill_registry_bindings_are_each_checked(self):
        self.assertTrue(self.resolve()["resolved"])
        bindings = self.approval_registry.allows.call_args_list
        self.assertEqual(["manifest", "skill"], [call.kwargs["subject_kind"] for call in bindings])
        skill = bindings[1].kwargs
        self.assertEqual(self.grant["grant_id"], skill["grant_id"])
        self.assertEqual(manifest_digest(self.skill), skill["subject_digest"])
        self.assertEqual(self.grant["allowed_actions"], skill["allowed_actions"])
        self.assertEqual(self.grant["approved_by"], skill["approved_by"])
        self.assertEqual(self.grant["admission_ref"], skill["decision_ref"])
        for denied_kind in ("manifest", "skill"):
            with self.subTest(denied_kind=denied_kind):
                self.approval_registry.allows.side_effect = lambda **binding: binding["subject_kind"] != denied_kind
                self.assert_both_paths_denied("trusted GitHub approval is absent")

    def test_registry_revocation_is_checked_after_success_on_both_paths(self):
        self.assertTrue(self.resolve()["resolved"])
        self.approval_registry.allows.return_value = False
        self.assert_both_paths_denied("trusted GitHub approval is absent")

    def test_registry_failure_and_non_boolean_approval_fail_closed(self):
        self.approval_registry.allows.side_effect = RuntimeError("database unavailable")
        self.assert_both_paths_denied("trusted GitHub approval lookup failed")
        self.approval_registry.allows.side_effect = None
        self.approval_registry.allows.return_value = 1
        self.assert_both_paths_denied("trusted GitHub approval is absent")

    def test_manifest_requires_trusted_verifier_and_context(self):
        for missing in ({"verifier": None}, {"context": None}):
            with self.subTest(missing=missing):
                self.assert_both_paths_denied("trusted approval verifier and activation context required", **missing)

    def test_manifest_approval_verifier_denial_stops_both_paths(self):
        from scripts.sync_control_plane.attestation import ApprovalError
        # policy and runtime may also be imported by the CLI as sync_control_plane.
        self.verifier.verify.side_effect = ApprovalError("synthetic approval revoked")
        self.assert_both_paths_denied("synthetic approval revoked")

    def test_schema_invalid_extended_grants_fail_without_tools_or_request(self):
        for field, value in (("allowed_actions", {}), ("requested_by", []),
                             ("issued_at", "not-a-time"), ("source_refs", [False])):
            with self.subTest(field=field):
                grant = copy.deepcopy(self.grant)
                grant[field] = value
                self.assert_both_paths_denied("model-tool-grant.schema.json", grant=grant)

    def test_current_grant_cannot_bypass_independent_principal_checks(self):
        for field, value, reason in (
            ("requested_by", "bogus requester", "well-formed principal"),
            ("approved_by", "agent.synthetic", "independent human principal"),
            ("approved_by", self.grant["requested_by"], "must be distinct"),
        ):
            with self.subTest(field=field, value=value):
                grant = copy.deepcopy(self.grant)
                grant[field] = value
                self.assert_both_paths_denied(reason, grant=grant, lookup_grant=lambda _: grant)

    def test_skill_admission_principals_are_checked_with_matching_digests(self):
        self.skill["admission"]["approved_by"] = "agent.synthetic"
        self.skill["integrity"]["manifest_sha256"] = manifest_digest(self.skill)
        self.grant["skill_manifest_sha256"] = self.skill["integrity"]["manifest_sha256"]
        self.authoritative = copy.deepcopy(self.grant)
        self.assert_both_paths_denied("skill admission requires approval by an independent human principal")

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
        resolved = self.resolve()
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
            **self.context(),
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
        resolved = self.resolve(candidate)
        self.assertFalse(resolved["resolved"])
        self.assertEqual([], resolved["tools"])
        self.assertIn("model tool adapter rejects non-active runtime manifest", resolved["errors"])

    def test_unknown_or_forbidden_action_fails_closed(self) -> None:
        forged = copy.deepcopy(self.fixture["manifest"])
        forged["tools"][0]["allowed_actions"].append("not_registered")
        resolved = self.resolve(forged)
        self.assertFalse(resolved["resolved"])
        self.assertEqual([], resolved["tools"])
        self.assertIn("runtime projection digest mismatch", resolved["errors"])

    def test_changed_allowed_actions_retaining_admission_hashes_fails(self):
        self.fixture["manifest"]["tools"][0]["allowed_actions"].append("promote_canon")
        self.assert_denied(self.resolve(), "runtime projection digest mismatch")

    def test_grant_tampering_cannot_mint_authority(self):
        for field, value in [("allowed_actions", ["read_sources", "promote_canon"]),
                             ("object_scope", ["source.other"]),
                             ("authorities", ["canon.promote"]),
                             ("expires_at", "2027-10-03T09:00:00Z")]:
            with self.subTest(field=field):
                grant = copy.deepcopy(self.grant)
                grant[field] = value
                self.assert_denied(self.resolve(grant=grant), "missing, revoked, or changed")

    def test_expired_and_not_yet_valid_grants_fail(self):
        for now, reason in [("2026-10-03T09:00:00Z", "expired"),
                            ("2026-10-03T06:59:59Z", "not yet valid")]:
            self.assert_denied(self.resolve(now=now), reason)

    def test_revocation_is_rechecked_after_success(self):
        self.assertTrue(self.resolve()["resolved"])
        self.authoritative = None
        self.assert_denied(self.resolve(), "missing, revoked, or changed")
        with self.assertRaises(ValueError):
            serialize_model_request(self.fixture["manifest"], self.registry,
                                    model="proof", messages=self.fixture["messages"], **self.context())

    def test_unavailable_authority_store_fails_closed(self):
        def unavailable(_):
            raise RuntimeError("offline")
        self.assert_denied(self.resolve(lookup_grant=unavailable), "authority lookup failed")

    def test_wrong_requested_scope_fails(self):
        self.assert_denied(self.resolve(object_scope=["source.other"]), "object scope exceeds")
        self.assert_denied(self.resolve(object_scope=[]), "nonempty")

    def test_binding_scope_and_authority_are_enforced_even_with_matching_digest(self):
        for field, value, reason in [("object_scope", ["source.other"], "exceeds tool binding"),
                                     ("requires_authority", ["canon.promote"], "required authority mismatch")]:
            with self.subTest(field=field):
                manifest = copy.deepcopy(self.fixture["manifest"])
                manifest["tools"][0][field] = value
                grant = copy.deepcopy(self.grant)
                grant["runtime_manifest_sha256"] = projection_digest(manifest)
                self.authoritative = copy.deepcopy(grant)
                self.assert_denied(self.resolve(manifest, grant=grant), reason)

    def test_runtime_ceiling_is_enforced(self):
        manifest = copy.deepcopy(self.fixture["manifest"])
        manifest["authority_ceiling"] = "observe"
        self.grant["runtime_manifest_sha256"] = projection_digest(manifest)
        self.authoritative = copy.deepcopy(self.grant)
        self.approval_registry = Mock(allows=Mock(return_value=True))
        admission = copy.deepcopy(self.fixture["manifest"]["admission"])
        record = {key: admission[key] for key in (
            "decision_ref", "authority_grant_ref", "transition_ref", "approved_by", "decided_at")}
        record["subject"] = {key: admission[key] for key in ("requested_by", "evidence_refs")}
        self.verifier = Mock(verify=Mock(return_value=record))
        self.activation_context = {"fixture_only": True}
        self.assert_denied(self.resolve(manifest), "runtime authority ceiling")

    def test_skill_source_and_manifest_tampering_fail(self):
        self.assert_denied(self.resolve(source_text=self.source + "tampered"), "source blob sha")
        self.skill["tools"][0]["actions"].append("promote_canon")
        self.assert_denied(self.resolve(), "manifest sha256")

    def test_registry_tampering_fails(self):
        self.registry["tools"][0]["actions"][0]["description"] += " changed"
        self.assert_denied(self.resolve(), "tool registry digest mismatch")

    def test_resolver_enforces_schemas_before_nested_access(self):
        for manifest in [None, [], {"status": "active"}, dict(self.fixture["manifest"], tools=[None])]:
            with self.subTest(manifest=manifest):
                result = resolve_model_visible_tools(manifest, self.registry, **self.context())
                self.assert_denied(result, "runtime-manifest.schema.json")
        for registry in [None, {}, dict(self.registry, tools=[None])]:
            self.assert_denied(resolve_model_visible_tools(self.fixture["manifest"], registry,
                                                          **self.context()), "tool-registry.schema.json")
        self.assert_denied(self.resolve(grant={}), "model-tool-grant.schema.json")

    def test_missing_binding_constraints_fail_closed(self):
        for field, reason in [("object_scope", "exceeds tool binding"),
                              ("requires_authority", "must declare required authority")]:
            manifest = copy.deepcopy(self.fixture["manifest"])
            del manifest["tools"][0][field]
            grant = copy.deepcopy(self.grant)
            grant["runtime_manifest_sha256"] = projection_digest(manifest)
            self.authoritative = copy.deepcopy(grant)
            self.assert_denied(self.resolve(manifest, grant=grant), reason)

    def test_grant_action_subset_is_enforced_with_valid_digests(self):
        # Canonical skill and registry both declare this action, but the grant does not.
        self.skill["tools"][0]["actions"].append("promote_canon")
        self.skill["integrity"]["manifest_sha256"] = manifest_digest(self.skill)
        self.fixture["manifest"]["tools"][0]["allowed_actions"].append("promote_canon")
        self.grant["skill_manifest_sha256"] = self.skill["integrity"]["manifest_sha256"]
        self.grant["runtime_manifest_sha256"] = projection_digest(self.fixture["manifest"])
        self.authoritative = copy.deepcopy(self.grant)
        self.approval_registry = Mock(allows=Mock(return_value=True))
        admission = copy.deepcopy(self.fixture["manifest"]["admission"])
        record = {key: admission[key] for key in (
            "decision_ref", "authority_grant_ref", "transition_ref", "approved_by", "decided_at")}
        record["subject"] = {key: admission[key] for key in ("requested_by", "evidence_refs")}
        self.verifier = Mock(verify=Mock(return_value=record))
        self.activation_context = {"fixture_only": True}
        self.assert_denied(self.resolve(), "binding actions exceed")

    def test_unknown_action_fails_even_with_trusted_grant_and_matching_digests(self):
        self.skill["tools"][0]["actions"].append("not_registered")
        self.skill["integrity"]["manifest_sha256"] = manifest_digest(self.skill)
        self.fixture["manifest"]["tools"][0]["allowed_actions"].append("not_registered")
        self.grant["allowed_actions"].append("not_registered")
        self.grant["skill_manifest_sha256"] = self.skill["integrity"]["manifest_sha256"]
        self.grant["runtime_manifest_sha256"] = projection_digest(self.fixture["manifest"])
        self.authoritative = copy.deepcopy(self.grant)
        self.approval_registry = Mock(allows=Mock(return_value=True))
        admission = copy.deepcopy(self.fixture["manifest"]["admission"])
        record = {key: admission[key] for key in (
            "decision_ref", "authority_grant_ref", "transition_ref", "approved_by", "decided_at")}
        record["subject"] = {key: admission[key] for key in ("requested_by", "evidence_refs")}
        self.verifier = Mock(verify=Mock(return_value=record))
        self.activation_context = {"fixture_only": True}
        self.assert_denied(self.resolve(), "canonical tool actions are not registered")

    def test_receipt_logs_unknown_and_observed_deltas_without_fabrication(self) -> None:
        request = serialize_model_request(
            self.fixture["manifest"],
            self.registry,
            model="proof-model",
            messages=self.fixture["messages"],
            **self.context(),
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
