"""Durable candidate action intent/outcome history; not tamper-proof storage.

SQLite serializes intent reservation across processes. Triggers reject ordinary
updates/deletes; a database owner can alter/drop them, so receipts never claim
storage immutability. An intent without a final outcome is an uncertain effect.
"""
from __future__ import annotations
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


class ActionLedger:
    def __init__(self, path: str | Path):
        self.connection = sqlite3.connect(str(path), timeout=30)
        self.connection.execute('PRAGMA journal_mode=WAL')
        self.connection.execute('PRAGMA synchronous=FULL')
        self.connection.executescript('''
            CREATE TABLE IF NOT EXISTS action_events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                idempotency_key TEXT NOT NULL,
                event_type TEXT NOT NULL CHECK(event_type IN ('intent', 'outcome')),
                action_digest TEXT NOT NULL,
                payload TEXT NOT NULL,
                recorded_at TEXT NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS one_action_intent
                ON action_events(idempotency_key) WHERE event_type = 'intent';
            CREATE UNIQUE INDEX IF NOT EXISTS one_action_outcome
                ON action_events(idempotency_key) WHERE event_type = 'outcome';
            CREATE TRIGGER IF NOT EXISTS action_events_no_update
                BEFORE UPDATE ON action_events BEGIN
                SELECT RAISE(ABORT, 'action history is append-only'); END;
            CREATE TRIGGER IF NOT EXISTS action_events_no_delete
                BEFORE DELETE ON action_events BEGIN
                SELECT RAISE(ABORT, 'action history is append-only'); END;
        ''')

    def close(self):
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def events(self, key: str | None = None) -> list[dict]:
        query = 'SELECT sequence,idempotency_key,event_type,action_digest,payload,recorded_at FROM action_events'
        params = ()
        if key is not None:
            query += ' WHERE idempotency_key=?'; params = (key,)
        rows = self.connection.execute(query + ' ORDER BY sequence', params)
        return [dict(sequence=row[0], idempotency_key=row[1], event_type=row[2],
                     action_digest=row[3], payload=json.loads(row[4]), recorded_at=row[5]) for row in rows]

    def get(self, idempotency_key: str) -> dict | None:
        events = self.events(idempotency_key)
        if not events:
            return None
        return {'action_digest': events[0]['action_digest'], 'action': events[0]['payload'],
                'outcome': next((e['payload'] for e in events if e['event_type'] == 'outcome'), None)}

    def record_intent(self, action: dict) -> tuple[bool, dict]:
        payload = _canonical(action)
        digest = hashlib.sha256(payload.encode('utf-8')).hexdigest()
        key = action['idempotency_key']
        with self.connection:
            self.connection.execute('BEGIN IMMEDIATE')
            existing = self.get(key)
            if existing:
                return False, existing
            self.connection.execute('INSERT INTO action_events '
                '(idempotency_key,event_type,action_digest,payload,recorded_at) VALUES (?,?,?,?,?)',
                (key, 'intent', digest, payload, datetime.now(timezone.utc).isoformat()))
        return True, {'action_digest': digest, 'action': json.loads(payload), 'outcome': None}

    def record_outcome(self, key: str, result: dict) -> dict:
        with self.connection:
            self.connection.execute('BEGIN IMMEDIATE')
            existing = self.get(key)
            if not existing:
                raise ValueError('an outcome requires a durable intent')
            if existing['outcome'] is not None:
                return existing['outcome']
            self.connection.execute('INSERT INTO action_events '
                '(idempotency_key,event_type,action_digest,payload,recorded_at) VALUES (?,?,?,?,?)',
                (key, 'outcome', existing['action_digest'], _canonical(result),
                 datetime.now(timezone.utc).isoformat()))
        return json.loads(_canonical(result))
