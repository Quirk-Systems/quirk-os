"""Run the local candidate pilot with pointer-only source metadata.

No live skill is admitted, no remote write is dispatched, and no human judgment
is simulated. Host fixture grants exercise the action contract only for this
built-in local adapter. --now is a deterministic fixture clock, not live authority.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.engineering.actions import ActionExecutor, LocalAdapter, TrustedGrantRegistry, digest_json, digest_text
from scripts.engineering.ledger import ActionLedger
from scripts.engineering.graph import EvidenceGraph
from scripts.engineering.loop import LoopRunner, LoopStore

EVALUATOR = {"id": "quirk-now-local-disposition/v1", "requires": ["next_proof", "source_ref", "source_head", "behavioral_proof"], "human_usefulness": "not_evaluated"}
EVALUATOR_DIGEST = digest_json(EVALUATOR)


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _validate_source(source):
    allowed = {"candidate_id", "source_url", "head_sha", "observed_at", "reported_build", "reported_behavior", "authority"}
    if not isinstance(source, dict) or set(source) != allowed:
        raise ValueError("missing or unknown source fields; only pointer metadata is accepted")
    if source["authority"] != "PREPARE":
        raise ValueError("source authority is outside the candidate PREPARE boundary")
    if not isinstance(source["candidate_id"], str) or not re.fullmatch(r"[a-zA-Z0-9._-]{1,120}", source["candidate_id"]):
        raise ValueError("invalid candidate identity")
    if not isinstance(source["head_sha"], str) or not re.fullmatch(r"[0-9a-f]{40}", source["head_sha"]):
        raise ValueError("exact Git source head required")
    if not isinstance(source["source_url"], str) or not re.fullmatch(
        r"https://github\.com/[A-Za-z0-9_-]{1,100}/[A-Za-z0-9_.-]{1,100}/pull/[1-9][0-9]{0,9}", source["source_url"]
    ):
        raise ValueError("source must be a canonical credential-free GitHub PR pointer")
    if source["reported_build"] not in {"passed", "failed", "unknown"} or source["reported_behavior"] not in {"passed", "failed", "not_proven", "unknown"}:
        raise ValueError("unknown reported evidence state")
    observed = datetime.fromisoformat(source["observed_at"].replace("Z", "+00:00"))
    if observed.tzinfo is None:
        raise ValueError("observation timezone required")


def _graph(source, previous=None):
    cid = source["candidate_id"]
    sid, bid = cid + ".source", cid + ".build-report"
    digest = digest_json(source)
    objects = [{"object_id": cid, "digest": digest, "kind": "artifact", "tenant_id": "quirk"},
               {"object_id": sid, "digest": digest, "kind": "evidence", "tenant_id": "quirk"},
               {"object_id": bid, "digest": digest_json({"reported_build": source["reported_build"]}), "kind": "claim", "tenant_id": "quirk"}]
    def edge(eid, target, target_digest, predicate, status, version_source):
        binding = digest_json(version_source)
        return {"assertion_id": eid, "subject_id": cid, "subject_digest": binding, "predicate": predicate,
                "object_id": target, "object_digest": target_digest, "source_ref": sid, "source_digest": binding,
                "observer": "local-pointer-intake/v1", "observed_at": version_source["observed_at"],
                "valid_from": version_source["observed_at"], "valid_until": None, "status": status}
    assertions = [edge("assertion.build-report", bid, objects[2]["digest"], "supported_by", "declared", source),
                  edge("assertion.source-dependency", sid, digest, "depends_on", "observed", source)]
    if previous is not None and digest_json(previous) != digest:
        assertions.append(edge("assertion.previous-source", sid, digest_json(previous), "depends_on", "observed", previous))
    return EvidenceGraph(objects, assertions, tenant_id="quirk"), sid


def plan_revalidation(graph, changed_object_id):
    impact = graph.impact_of(changed_object_id, max_depth=8)
    return {**impact, "next_operation": "prepare_candidate", "admission_effect": "none", "dispatch_authorized": False}


def _verify(candidate, criteria):
    if not isinstance(candidate, dict):
        return {"passed": False, "reasons": ["CANDIDATE_MISSING"]}
    reasons = ["MISSING_" + key.upper() for key in criteria["required"] if not candidate.get(key)]
    for key in ("source_ref", "source_head", "authority"):
        if candidate.get(key) != criteria[key]:
            reasons.append("MISMATCH_" + key.upper())
    if candidate.get("behavioral_proof") != "not_observed":
        reasons.append("UNOBSERVED_BEHAVIOR_CLAIM")
    return {"passed": not reasons, "reasons": reasons}


def run_pilot(source, state_dir, *, now=None):
    _validate_source(source)
    now = now or datetime.now(timezone.utc).isoformat()
    instant = datetime.fromisoformat(now.replace("Z", "+00:00"))
    if instant.tzinfo is None:
        raise ValueError("now requires timezone")
    if datetime.fromisoformat(source["observed_at"].replace("Z", "+00:00")) > instant:
        raise ValueError("source has not yet been observed")
    state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    current_path = state_dir / (source["candidate_id"] + ".current.json")
    previous = json.loads(current_path.read_text()) if current_path.exists() else None
    if previous is not None:
        _validate_source(previous)
    graph, source_node = _graph(source, previous)
    source_digest = digest_json(source)
    run_id = "run.engineering." + source_digest[:20]
    target = "resource." + source["candidate_id"]
    candidate = {"candidate_id": source["candidate_id"], "source_ref": source["source_url"],
                 "source_head": source["head_sha"], "authority": "CANDIDATE_PREPARE",
                 "next_proof": "Run the existing behavioral fixtures at the exact source head and attach an observed receipt.",
                 "build_proof": "reported_" + source["reported_build"], "behavioral_proof": "not_observed",
                 "why": "Reported build status does not establish behavioral execution.", "admission_effect": "none"}
    arguments = {"title": "Next proof for " + source["candidate_id"], "body": _canonical(candidate)}
    limits = {"max_resources": 1, "max_bytes": 65536, "max_spend": 0}
    grant_id = "grant.local-fixture." + source_digest[:20]
    action = {"schema_version": "action-contract/v1", "action_id": "action." + source_digest[:20],
              "idempotency_key": run_id + ":step:0", "grant_id": grant_id,
              "skill_id": "quirk-fixture-engineering", "skill_version": "0.1.0",
              "skill_manifest_sha256": digest_json({"fixture": True, "adapter": "local-adapter/v1"}),
              "operation": "prepare_candidate", "target": target, "target_sha256": digest_text(_canonical(source)),
              "arguments": arguments, "arguments_sha256": digest_json(arguments),
              "objective": "Prepare an evidenced next-proof candidate", "postcondition": "candidate_prepared",
              "effect_limit": limits, "recovery": {"retry": "reconcile_only", "timeout_seconds": 30}}
    grant_path = state_dir / (run_id + ".host-fixture-grant.json")
    if grant_path.exists():
        grant = json.loads(grant_path.read_text())
    else:
        grant = {"schema_version": "action-grant/v1", "runtime_grant": {
            "grant_id": grant_id, "skill_id": action["skill_id"], "skill_version": action["skill_version"],
            "skill_manifest_sha256": action["skill_manifest_sha256"], "decision": "approved",
            "admission_ref": "decision.local-fixture-only", "requested_by": "fixture.operator", "approved_by": "fixture.host",
            "issued_at": (instant - timedelta(minutes=1)).isoformat(), "expires_at": (instant + timedelta(hours=1)).isoformat(),
            "authority_ceiling": "propose", "allowed_actions": ["prepare_candidate"], "purpose": "Built-in local candidate fixture only"},
            "target": target, "target_sha256": action["target_sha256"], "arguments_sha256": action["arguments_sha256"],
            "policy_ref": "policy.local-candidate.v1", "effect_limit": limits}
        with grant_path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(grant, indent=2) + "\n")
    loop_spec = {"schema_version": "loop-spec/v1", "run_id": run_id, "objective": action["objective"],
                 "source_digest": source_digest, "evaluator_digest": EVALUATOR_DIGEST,
                 "acceptance": {"required": EVALUATOR["requires"], "source_ref": source["source_url"], "source_head": source["head_sha"], "authority": "CANDIDATE_PREPARE"},
                 "authority": "CANDIDATE_PREPARE", "limits": {"steps": 3, "repairs": 2, "seconds": 30}}
    with ActionLedger(state_dir / "actions.sqlite") as ledger:
        executor = ActionExecutor(ledger, TrustedGrantRegistry({grant_id: grant}), LocalAdapter({target: _canonical(source)}))
        def step(context):
            receipt = executor.execute(action, now=now)
            value = receipt.get("output")
            prepared = json.loads(value["candidate"]["body"]) if value is not None else None
            return {"strategy": "exact-source-next-proof", "candidate": prepared, "action_receipt": receipt}
        loop_store = LoopStore(state_dir / "loops.sqlite")
        try:
            loop = LoopRunner(loop_store).run(loop_spec, step, _verify, evaluator_digest=EVALUATOR_DIGEST)
        finally:
            loop_store.close()
        recorded = ledger.get(action["idempotency_key"])
        receipt = recorded["outcome"] if recorded else None
        # A terminal loop is historical evidence. Reuse still has to pass the
        # current host grant and resource checks; never rerun an uncertain effect.
        current = executor.execute(action, now=now) if receipt is not None else None
        applicability = {"checked_at": now, "applicable": current is not None and current["status"] == "VERIFIED",
                         "status": current["status"] if current else "NOT_OBSERVED",
                         "errors": current.get("errors", []) if current else ["OBSERVATION_MISSING"],
                         "historical_receipt_preserved": True}
        status = loop["status"]
        if current and current["status"] == "REJECTED":
            status = "PAUSED_AUTHORITY_CHANGE"
        elif current and current["status"] == "UNCERTAIN":
            status = "PAUSED_UNCERTAIN_EFFECT"
        events = len(ledger.events(action["idempotency_key"]))
    result = {"schema_version": "engineering-pilot/v1", "mode": "LOCAL_CANDIDATE_SIMULATION",
              "status": status, "current_applicability": applicability,
              "source": source, "loop": loop, "action_receipt": receipt, "action_event_count": events,
              "graph_support": graph.support_for(source["candidate_id"], source_digest, now=now),
              "context": graph.context_for(source["candidate_id"], source_digest, now=now, max_items=20),
              "revalidation": plan_revalidation(graph, source_node), "evaluator_digest": EVALUATOR_DIGEST,
              "admission_effect": "none", "external_writes": 0,
              "limitations": ["Host fixture grant is not live skill admission", "Reported upstream checks remain declarations", "Human usefulness not measured"]}
    temporary = current_path.with_suffix(".tmp")
    temporary.write_text(json.dumps(source, indent=2) + "\n")
    temporary.replace(current_path)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--state-dir", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--now", help="Optional deterministic local fixture clock")
    args = parser.parse_args()
    result = run_pilot(json.loads(args.input.read_text()), args.state_dir, now=args.now)
    output = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(output)
    print(json.dumps({"status": result["status"], "run_id": result["loop"]["run_id"], "action_event_count": result["action_event_count"], "admission_effect": "none", "human_usefulness": None}))
    return 0 if result["status"] == "REVIEW_READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
