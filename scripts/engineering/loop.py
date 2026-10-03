"""Durable, bounded candidate controller. Callbacks are trusted host code.

This local reference runner checks time between bounded operations; it cannot
preempt arbitrary blocking code. Production adapters must enforce their own
operation timeouts. The action ledger owns effect idempotency and reconciliation.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Callable


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def spec_digest(value):
    return hashlib.sha256(_json(value).encode()).hexdigest()


def _initial_state(spec):
    return {"run_id": spec["run_id"], "status": "NEW", "steps": 0, "attempts": 0,
            "candidate": None, "reasons": [], "last_fingerprint": None,
            "elapsed_seconds": 0, "inflight_started_at": None,
            "human_usefulness": None, "authority": "CANDIDATE_PREPARE"}


class LoopStore:
    """Append-only event history and replaceable current-state projection.

    SQLite triggers protect ordinary application writes, not a hostile database
    administrator or filesystem owner. History hashes provide tamper detection,
    not authentication of the observer.
    """

    def __init__(self, path):
        self.path = Path(path)
        self.connection = sqlite3.connect(self.path, timeout=5)
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript("""
          CREATE TABLE IF NOT EXISTS loop_runs (
            run_id TEXT PRIMARY KEY, spec_digest TEXT NOT NULL, spec_json TEXT NOT NULL,
            state_json TEXT NOT NULL, lease_owner TEXT, lease_until REAL
          );
          CREATE TABLE IF NOT EXISTS loop_events (
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL REFERENCES loop_runs(run_id),
            event_json TEXT NOT NULL, previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL
          );
          CREATE TRIGGER IF NOT EXISTS loop_events_no_update BEFORE UPDATE ON loop_events
            BEGIN SELECT RAISE(ABORT, 'append-only loop history'); END;
          CREATE TRIGGER IF NOT EXISTS loop_events_no_delete BEFORE DELETE ON loop_events
            BEGIN SELECT RAISE(ABORT, 'append-only loop history'); END;
        """)

    def close(self):
        self.connection.close()

    def get(self, run_id):
        row = self.connection.execute(
            "SELECT spec_digest, spec_json, state_json FROM loop_runs WHERE run_id=?", (run_id,)
        ).fetchone()
        if row is None:
            return None
        return {"spec_digest": row[0], "spec": json.loads(row[1]), "state": json.loads(row[2])}

    def open_run(self, spec):
        state = _initial_state(spec)
        with self.connection:
            self.connection.execute("INSERT OR IGNORE INTO loop_runs VALUES (?, ?, ?, ?, NULL, NULL)",
                                    (spec["run_id"], spec_digest(spec), _json(spec), _json(state)))
        existing = self.get(spec["run_id"])
        if existing["spec_digest"] != spec_digest(spec):
            raise ValueError("run spec changed; create a new candidate run with explicit provenance")
        self.verify_history(spec["run_id"])
        return existing["state"]

    def acquire(self, run_id, duration):
        owner = str(uuid.uuid4())
        instant = time.time()
        with self.connection:
            cursor = self.connection.execute(
                "UPDATE loop_runs SET lease_owner=?, lease_until=? WHERE run_id=? "
                "AND (lease_owner IS NULL OR lease_until < ?)",
                (owner, instant + duration + 5, run_id, instant),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("run already has an active controller")
        return owner

    def release(self, run_id, owner):
        with self.connection:
            self.connection.execute("UPDATE loop_runs SET lease_owner=NULL, lease_until=NULL WHERE run_id=? AND lease_owner=?", (run_id, owner))

    def record(self, state, event, owner):
        run_id = state["run_id"]
        with self.connection:
            self.connection.execute("BEGIN IMMEDIATE")
            row = self.connection.execute("SELECT lease_owner FROM loop_runs WHERE run_id=?", (run_id,)).fetchone()
            if row is None or row[0] != owner:
                raise RuntimeError("controller lease changed")
            prior = self.connection.execute("SELECT event_hash FROM loop_events WHERE run_id=? ORDER BY sequence DESC LIMIT 1", (run_id,)).fetchone()
            previous_hash = prior[0] if prior else "0" * 64
            payload = _json({"event": event, "state": state})
            digest = hashlib.sha256((previous_hash + payload).encode()).hexdigest()
            self.connection.execute("INSERT INTO loop_events(run_id,event_json,previous_hash,event_hash) VALUES (?,?,?,?)", (run_id, payload, previous_hash, digest))
            self.connection.execute("UPDATE loop_runs SET state_json=? WHERE run_id=?", (_json(state), run_id))

    def verify_history(self, run_id):
        run = self.get(run_id)
        if run["spec_digest"] != spec_digest(run["spec"]):
            raise ValueError("stored loop spec integrity mismatch")
        previous = "0" * 64
        latest = None
        for payload, prior, digest in self.connection.execute("SELECT event_json,previous_hash,event_hash FROM loop_events WHERE run_id=? ORDER BY sequence", (run_id,)):
            if prior != previous or hashlib.sha256((previous + payload).encode()).hexdigest() != digest:
                raise ValueError("loop history integrity mismatch")
            previous, latest = digest, json.loads(payload)["state"]
        if latest is not None and latest != self.get(run_id)["state"]:
            raise ValueError("loop checkpoint does not match observed event history")
        if latest is None and run["state"] != _initial_state(run["spec"]):
            raise ValueError("loop initial state has no supporting history")


def _validate_spec(spec, evaluator_digest):
    if not isinstance(spec, dict) or spec.get("schema_version") != "loop-spec/v1":
        raise ValueError("unsupported loop spec")
    for key in ("run_id", "objective", "authority"):
        if not isinstance(spec.get(key), str) or not spec[key].strip():
            raise ValueError(f"missing {key}")
    for key in ("source_digest", "evaluator_digest"):
        if not isinstance(spec.get(key), str) or not re.fullmatch(r"[0-9a-f]{64}", spec[key]):
            raise ValueError(f"invalid {key}")
    if evaluator_digest != spec["evaluator_digest"]:
        raise ValueError("evaluator digest mismatch")
    if not isinstance(spec.get("acceptance"), dict) or not spec["acceptance"]:
        raise ValueError("fixed acceptance criteria required")
    limits = spec.get("limits", {})
    for key, low, high in (("steps", 1, 100), ("repairs", 0, 99), ("seconds", 1, 3600)):
        value = limits.get(key)
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"invalid {key} budget")
    _json(spec)


class LoopRunner:
    def __init__(self, store: LoopStore):
        self.store = store

    def run(self, spec, step: Callable, verifier: Callable, *, evaluator_digest, clock=time.monotonic):
        _validate_spec(spec, evaluator_digest)
        frozen = copy.deepcopy(spec)
        state = self.store.open_run(frozen)
        if state["status"] not in {"NEW", "INTERRUPTED", "RUNNING"}:
            return state
        owner = self.store.acquire(frozen["run_id"], frozen["limits"]["seconds"])
        started = clock()
        carried_elapsed = state["elapsed_seconds"]

        def finish(status, reasons):
            state["elapsed_seconds"] = carried_elapsed + max(0, clock() - started)
            state["inflight_started_at"] = None
            if state["elapsed_seconds"] >= frozen["limits"]["seconds"]:
                status, reasons = "BUDGET_EXHAUSTED", [*reasons, "TIME_BUDGET"]
            state.update(status=status, reasons=list(dict.fromkeys(reasons)))
            self.store.record(state, status, owner)
            return copy.deepcopy(state)

        try:
            # A second caller may have completed while this caller acquired its lease.
            state = self.store.get(frozen["run_id"])["state"]
            carried_elapsed = state["elapsed_seconds"]
            if state.get("inflight_started_at") is not None:
                carried_elapsed += min(frozen["limits"]["seconds"], max(0, time.time() - state["inflight_started_at"]))
            if state["status"] not in {"NEW", "INTERRUPTED", "RUNNING"}:
                return state
            if frozen["authority"] != "CANDIDATE_PREPARE":
                return finish("PAUSED_AUTHORITY_CHANGE", ["AUTHORITY_OUT_OF_SCOPE"])
            limit = min(frozen["limits"]["steps"], frozen["limits"]["repairs"] + 1)
            while state["steps"] < limit and state["attempts"] < frozen["limits"]["steps"]:
                state["elapsed_seconds"] = carried_elapsed + max(0, clock() - started)
                if state["elapsed_seconds"] >= frozen["limits"]["seconds"]:
                    return finish("BUDGET_EXHAUSTED", [*state["reasons"], "TIME_BUDGET"])
                context = {"run_id": frozen["run_id"], "step": state["steps"],
                           "step_id": f"{frozen['run_id']}:step:{state['steps']}",
                           "acceptance": copy.deepcopy(frozen["acceptance"]),
                           "source_digest": frozen["source_digest"],
                           "prior_candidate": copy.deepcopy(state["candidate"])}
                state.update(attempts=state["attempts"] + 1, status="RUNNING", inflight_started_at=time.time())
                self.store.record(state, "STEP_DISPATCH", owner)
                try:
                    observed = step(context)
                except InterruptedError as exc:
                    return finish("INTERRUPTED", ["INTERRUPTED", str(exc)])
                except Exception as exc:
                    return finish("FAILED", ["STEP_FAILED", type(exc).__name__])
                if not isinstance(observed, dict):
                    return finish("FAILED", ["INVALID_STEP_RESULT"])
                state["steps"] += 1
                state["inflight_started_at"] = None
                state["candidate"] = copy.deepcopy(observed.get("candidate"))
                state["elapsed_seconds"] = carried_elapsed + max(0, clock() - started)
                if state["elapsed_seconds"] >= frozen["limits"]["seconds"]:
                    return finish("BUDGET_EXHAUSTED", ["TIME_BUDGET"])
                receipt = observed.get("action_receipt", {})
                if not isinstance(receipt, dict):
                    return finish("FAILED", ["INVALID_ACTION_RECEIPT"])
                if receipt.get("status") == "UNCERTAIN":
                    return finish("PAUSED_UNCERTAIN_EFFECT", ["RECONCILIATION_REQUIRED"])
                if receipt.get("status") == "REJECTED":
                    return finish("PAUSED_AUTHORITY_CHANGE", ["ACTION_REJECTED", *receipt.get("errors", [])])
                evidence = receipt.get("evidence")
                reasons = []
                if receipt.get("status") != "VERIFIED" or not isinstance(evidence, list) or not evidence:
                    reasons.append("OBSERVATION_MISSING")
                try:
                    judged = verifier(copy.deepcopy(state["candidate"]), copy.deepcopy(frozen["acceptance"]))
                except Exception as exc:
                    return finish("FAILED", ["VERIFIER_FAILED", type(exc).__name__])
                if not isinstance(judged, dict) or type(judged.get("passed")) is not bool or not isinstance(judged.get("reasons"), list):
                    return finish("FAILED", ["INVALID_VERIFIER_RESULT"])
                state["elapsed_seconds"] = carried_elapsed + max(0, clock() - started)
                if state["elapsed_seconds"] >= frozen["limits"]["seconds"]:
                    return finish("BUDGET_EXHAUSTED", ["TIME_BUDGET"])
                reasons.extend(str(reason) for reason in judged["reasons"])
                if judged["passed"] and not reasons:
                    return finish("REVIEW_READY", [])
                fingerprint = spec_digest({"strategy": observed.get("strategy"), "candidate": state["candidate"], "evidence": evidence, "reasons": reasons})
                if fingerprint == state["last_fingerprint"]:
                    return finish("STALLED", [*reasons, "UNCHANGED_FAILURE"])
                state.update(last_fingerprint=fingerprint, reasons=reasons, status="RUNNING")
                self.store.record(state, "REPAIR_NEEDED", owner)
            return finish("BUDGET_EXHAUSTED", [*state["reasons"], "REPAIR_BUDGET"])
        finally:
            self.store.release(frozen["run_id"], owner)
