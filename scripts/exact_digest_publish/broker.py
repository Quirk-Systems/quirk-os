"""Linux peer-credential broker and protected local filesystem publication sink.

Workers never receive authority, database, policy, or output write capabilities.
All calls are serialized, including revocation and the publication boundary.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import fcntl
import hashlib
import json
import os
from pathlib import Path
import socket
import socketserver
import sqlite3
import stat
import struct
import time
import uuid

from .model import (Denied, Policy, PublicationSubject, canonical, decode_json,
                    exact, identifier, integer, sha256, uuid_id)

MAX_MESSAGE = 100_000
CONFIG_KEYS = {"version", "broker_uid", "authorizer_uid", "evaluator_uid",
               "composer_uid", "state_dir", "socket_path", "destination_id",
               "authority_mode", "policy"}
ACTIONS = {
    "status": ({"authorizer", "evaluator", "composer"}, set()),
    "stage": ({"composer"}, {"artifact_id", "payload_b64"}),
    "evaluate": ({"evaluator"}, {"subject", "verdict"}),
    "grant": ({"authorizer"}, {"subject", "grant_id", "expires_at", "scope_digest", "decision"}),
    "revoke": ({"authorizer"}, {"grant_id"}),
    "set_policy": ({"authorizer"}, {"policy"}),
    "publish": ({"composer"}, {"subject", "grant_id", "request_id"}),
    "reconcile": ({"composer"}, {"request_id"}),
    "inspect": ({"authorizer"}, set()),
}


def protected(path: Path, owners: set[int], leaf_owner: int | None = None) -> None:
    """Reject writable or symlinked authority paths before opening state."""
    if not path.is_absolute() or ".." in path.parts:
        raise Denied("UNSAFE_PATH")
    parts = [*reversed(path.parents), path]
    for part in parts:
        entry = part.lstat()
        if stat.S_ISLNK(entry.st_mode) or entry.st_uid not in owners:
            raise Denied("UNTRUSTED_PATH")
        writable = entry.st_mode & 0o022
        trusted_sticky_parent = (part != path and stat.S_ISDIR(entry.st_mode)
                                 and entry.st_uid == 0 and entry.st_mode & stat.S_ISVTX)
        if writable and not trusted_sticky_parent:
            raise Denied("WRITABLE_AUTHORITY_PATH")
    if leaf_owner is not None and path.lstat().st_uid != leaf_owner:
        raise Denied("WRONG_OWNER")


def read_file(path: Path, limit: int) -> bytes:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
            raise Denied("INVALID_FILE")
        data = stream.read(limit + 1)
        if len(data) > limit:
            raise Denied("PAYLOAD_TOO_LARGE")
        return data


class Broker:
    def __init__(self, config_path: str):
        path = Path(config_path)
        protected(path, {0}, 0)
        self.config = exact(decode_json(read_file(path, 16384).decode("utf-8")), CONFIG_KEYS)
        if type(self.config["version"]) is not int or self.config["version"] != 1:
            raise Denied("CONFIG_VERSION")
        uids = [integer(self.config[k], 1, 2**31 - 1) for k in
                ("broker_uid", "authorizer_uid", "evaluator_uid", "composer_uid")]
        if len(set(uids)) != 4 or os.getuid() != uids[0] or os.geteuid() != uids[0]:
            raise Denied("IDENTITY_ISOLATION_REQUIRED")
        if os.getgroups():
            raise Denied("SUPPLEMENTARY_GROUPS_FORBIDDEN")
        self.uid = uids[0]
        self.roles = dict(zip(uids[1:], ("authorizer", "evaluator", "composer")))
        self.destination = identifier(self.config["destination_id"])
        if self.config["authority_mode"] not in ("test_fixture", "human_session"):
            raise Denied("AUTHORITY_MODE")
        self.mode = self.config["authority_mode"]
        initial_policy = Policy.parse(self.config["policy"])
        # Deploy source as an immutable root-owned package. Runtime user cannot
        # rewrite its own code, and worker-writable module paths are rejected.
        for source in Path(__file__).parent.glob("*.py"):
            protected(source.absolute(), {0}, 0)
        self.state = Path(self.config["state_dir"])
        protected(self.state, {0, self.uid}, self.uid)
        if stat.S_IMODE(self.state.stat().st_mode) != 0o700:
            raise Denied("STATE_MUST_BE_PRIVATE")
        self.socket_path = Path(self.config["socket_path"])
        if not self.socket_path.is_absolute() or len(os.fsencode(self.socket_path)) > 103:
            raise Denied("SOCKET_PATH")
        protected(self.socket_path.parent, {0, self.uid}, self.uid)
        if self.socket_path.parent == self.state:
            raise Denied("SOCKET_PARENT_MUST_BE_TRAVERSABLE")
        os.umask(0o077)
        self.lockfd = os.open(self.state / "broker.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(self.lockfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Denied("BROKER_ALREADY_RUNNING") from None
        for name in ("payloads", "published", "pending"):
            directory = self.state / name
            directory.mkdir(mode=0o700, exist_ok=True)
            protected(directory, {0, self.uid}, self.uid)
            if stat.S_IMODE(directory.stat().st_mode) != 0o700:
                raise Denied("STATE_MUST_BE_PRIVATE")
        dbpath = self.state / "state.sqlite3"
        if dbpath.exists() or dbpath.is_symlink():
            protected(dbpath, {0, self.uid}, self.uid)
        self.db = sqlite3.connect(dbpath, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,
              kind TEXT NOT NULL, actor_uid INTEGER NOT NULL, at REAL NOT NULL, record TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS evaluations(id TEXT PRIMARY KEY, subject_key TEXT NOT NULL,
              subject TEXT NOT NULL, verdict TEXT NOT NULL, at REAL NOT NULL, seq INTEGER NOT NULL);
          CREATE TABLE IF NOT EXISTS grants(id TEXT PRIMARY KEY, subject_key TEXT NOT NULL,
              subject TEXT NOT NULL, issuer_uid INTEGER NOT NULL, issued_at REAL NOT NULL,
              expires_at INTEGER NOT NULL, revoked INTEGER NOT NULL DEFAULT 0,
              used INTEGER NOT NULL DEFAULT 0, authority_mode TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY, subject TEXT NOT NULL,
              grant_id TEXT NOT NULL, evaluation_id TEXT NOT NULL, status TEXT NOT NULL,
              commit_sequence INTEGER NOT NULL, output_name TEXT NOT NULL);
        """)
        # State cannot be silently rebound to another destination or identity set
        # by restarting with a different config. Policy revisions are explicit.
        binding = {k: self.config[k] for k in ("broker_uid", "authorizer_uid", "evaluator_uid",
                   "composer_uid", "destination_id", "authority_mode")}
        existing = self.db.execute("SELECT value FROM meta WHERE key='binding'").fetchone()
        if existing and existing[0] != canonical(binding):
            raise Denied("STATE_BINDING_MISMATCH")
        self.db.execute("INSERT OR IGNORE INTO meta VALUES ('binding', ?)", (canonical(binding),))
        self.db.execute("INSERT OR IGNORE INTO meta VALUES ('policy', ?)", (canonical(initial_policy.wire()),))

    @property
    def policy(self) -> Policy:
        value = self.db.execute("SELECT value FROM meta WHERE key='policy'").fetchone()[0]
        return Policy.parse(json.loads(value))

    def event(self, kind: str, uid: int, record: dict) -> int:
        cursor = self.db.execute("INSERT INTO events(kind,actor_uid,at,record) VALUES (?,?,?,?)",
                                 (kind, uid, time.time(), canonical(record)))
        return cursor.lastrowid

    def current(self, value: dict) -> PublicationSubject:
        subject = PublicationSubject.parse(value)
        if subject.destination_id != self.destination:
            raise Denied("DESTINATION_MISMATCH")
        if subject.policy_digest != self.policy.key:
            raise Denied("POLICY_MISMATCH")
        return subject

    def request(self, uid: int, message: dict) -> dict:
        role = self.roles.get(uid)
        if role is None:
            raise Denied("UNRECOGNIZED_PEER")
        action = message.get("action")
        if type(action) is not str or action not in ACTIONS:
            raise Denied("UNKNOWN_ACTION")
        roles, fields = ACTIONS[action]
        if role not in roles:
            raise Denied("FORBIDDEN_ACTION")
        exact(message, fields | {"action"})
        args = {k: v for k, v in message.items() if k != "action"}
        return {"ok": True, **getattr(self, "do_" + action)(uid, **args)}

    def do_status(self, uid):
        return {"policy_digest": self.policy.key, "policy": self.policy.wire(),
                "destination_id": self.destination, "authority_mode": self.mode}

    def do_stage(self, uid, artifact_id, payload_b64):
        identifier(artifact_id)
        if type(payload_b64) is not str or len(payload_b64) > 90000:
            raise Denied("INVALID_PAYLOAD")
        try:
            payload = base64.b64decode(payload_b64, validate=True)
        except (ValueError, binascii.Error):
            raise Denied("INVALID_PAYLOAD") from None
        policy = self.policy
        if len(payload) > policy.max_payload_bytes:
            raise Denied("PAYLOAD_TOO_LARGE")
        key = hashlib.sha256(payload).hexdigest()
        path = self.state / "payloads" / key
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
        except FileExistsError:
            if read_file(path, 65536) != payload:
                raise Denied("SNAPSHOT_CORRUPTION")
        else:
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            self.sync_dir(path.parent)
        subject = PublicationSubject(artifact_id, key, "publish", self.destination, policy.key)
        self.event("ArtifactStaged", uid, subject.wire())
        return {"subject": subject.wire()}

    def do_evaluate(self, uid, subject, verdict):
        subject = self.current(subject)
        if type(verdict) is not str or verdict not in {"PASS", "FAIL", "INVALIDATED"}:
            raise Denied("INVALID_VERDICT")
        key = str(uuid.uuid4())
        self.db.execute("BEGIN IMMEDIATE")
        try:
            seq = self.event("EvaluationRecorded", uid, {"id": key, "subject": subject.wire(), "verdict": verdict})
            self.db.execute("INSERT INTO evaluations VALUES (?,?,?,?,?,?)",
                            (key, subject.key, canonical(subject.wire()), verdict, time.time(), seq))
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK")
            raise
        return {"evaluation_id": key}

    def do_grant(self, uid, subject, grant_id, expires_at, scope_digest, decision):
        subject = self.current(subject)
        uuid_id(grant_id)
        integer(expires_at, 1, 2**53 - 1)
        sha256(scope_digest)
        now = time.time()
        if decision != "approve" or scope_digest != subject.key:
            raise Denied("EXPLICIT_SCOPE_DECISION_REQUIRED")
        if not now < expires_at <= now + self.policy.max_grant_seconds:
            raise Denied("INVALID_GRANT_LIFETIME")
        if self.db.execute("SELECT 1 FROM grants WHERE id=?", (grant_id,)).fetchone():
            raise Denied("GRANT_ID_EXISTS")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute("INSERT INTO grants VALUES (?,?,?,?,?,?,0,0,?)",
                            (grant_id, subject.key, canonical(subject.wire()), uid, now, expires_at, self.mode))
            self.event("HumanGrantRecorded", uid, {"id": grant_id, "subject": subject.wire(),
                       "authority_mode": self.mode, "decision": "approve", "max_uses": 1,
                       "expires_at": expires_at, "issuer_source": "kernel_peer_credentials"})
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK")
            raise
        return {"grant_id": grant_id, "authority_mode": self.mode}

    def do_revoke(self, uid, grant_id):
        uuid_id(grant_id)
        if not self.db.execute("SELECT 1 FROM grants WHERE id=?", (grant_id,)).fetchone():
            raise Denied("GRANT_NOT_FOUND")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute("UPDATE grants SET revoked=1 WHERE id=?", (grant_id,))
            self.event("HumanGrantRevoked", uid, {"grant_id": grant_id})
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK")
            raise
        return {"revoked": grant_id}

    def do_set_policy(self, uid, policy):
        policy = Policy.parse(policy)
        if policy.revision <= self.policy.revision:
            raise Denied("POLICY_REVISION_MUST_ADVANCE")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute("UPDATE meta SET value=? WHERE key='policy'", (canonical(policy.wire()),))
            self.event("PolicyChanged", uid, policy.wire())
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK")
            raise
        return {"policy_digest": policy.key}

    def do_publish(self, uid, subject, grant_id, request_id):
        subject = PublicationSubject.parse(subject)
        uuid_id(grant_id)
        uuid_id(request_id)
        prior = self.db.execute("SELECT * FROM attempts WHERE id=?", (request_id,)).fetchone()
        if prior:
            if prior["subject"] != canonical(subject.wire()) or prior["grant_id"] != grant_id:
                raise Denied("REQUEST_ID_REBOUND")
            # Returning a historical receipt causes no new effect, even if the
            # original grant is now revoked. Unknown attempts require reconcile.
            return {"receipt": self.receipt(prior)}
        subject = self.current(subject.wire())
        snapshot = read_file(self.state / "payloads" / subject.payload_digest, self.policy.max_payload_bytes)
        if hashlib.sha256(snapshot).hexdigest() != subject.payload_digest:
            raise Denied("SNAPSHOT_CORRUPTION")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            # All authority mutations and dispatches share this single service
            # ordering; an exclusive state lock rejects a second broker.
            policy = self.policy
            if policy.key != subject.policy_digest:
                raise Denied("POLICY_MISMATCH")
            now = time.time()
            evaluation = self.db.execute("SELECT * FROM evaluations WHERE subject_key=? ORDER BY seq DESC LIMIT 1",
                                         (subject.key,)).fetchone()
            if (not evaluation or evaluation["verdict"] != "PASS"
                    or not 0 <= now - evaluation["at"] < policy.evaluation_ttl_seconds):
                raise Denied("CURRENT_PASS_REQUIRED")
            grant = self.db.execute("SELECT * FROM grants WHERE id=?", (grant_id,)).fetchone()
            if (not grant or grant["subject_key"] != subject.key or grant["subject"] != canonical(subject.wire())
                    or grant["issuer_uid"] != self.config["authorizer_uid"] or grant["authority_mode"] != self.mode
                    or grant["revoked"] or grant["used"] or not grant["issued_at"] <= now < grant["expires_at"]):
                raise Denied("VALID_HUMAN_GRANT_REQUIRED")
            seq = self.event("PublicationAuthorized", uid, {"request_id": request_id, "subject": subject.wire(),
                             "grant_id": grant_id, "evaluation_id": evaluation["id"]})
            self.db.execute("UPDATE grants SET used=1 WHERE id=?", (grant_id,))
            self.db.execute("INSERT INTO attempts VALUES (?,?,?,?,?,?,?)",
                            (request_id, canonical(subject.wire()), grant_id, evaluation["id"],
                             "unknown", seq, request_id + ".bin"))
            self.dispatch_not_before = max(grant["issued_at"], evaluation["at"])
            self.dispatch_deadline = min(grant["expires_at"], evaluation["at"] + policy.evaluation_ttl_seconds)
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK")
            raise
        # Authorization is consumed durably before the side effect. A crash at
        # any later point cannot reuse the grant or silently redeliver the job.
        try:
            self._dispatch(snapshot, request_id)
        except Denied:
            self.finish(uid, request_id, "not_published")
            raise
        except OSError:
            self.event("PublicationOutcomeUnknown", uid, {"request_id": request_id})
        else:
            self.finish(uid, request_id, "confirmed")
        row = self.db.execute("SELECT * FROM attempts WHERE id=?", (request_id,)).fetchone()
        return {"receipt": self.receipt(row)}

    @staticmethod
    def sync_dir(path):
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def _dispatch(self, snapshot: bytes, request_id: str) -> str:
        output_name = request_id + ".bin"
        pending = self.state / "pending" / output_name
        fd = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(snapshot)
                stream.flush()
                os.fsync(stream.fileno())
            output_fd = os.open(self.state / "published", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                # Preparing/fsyncing bytes can take time. Recheck freshness at
                # the final effect boundary, after that work and before link.
                # Other authority changes cannot interleave with this handler.
                if not self.dispatch_not_before <= time.time() < self.dispatch_deadline:
                    raise Denied("AUTHORITY_EXPIRED_BEFORE_EFFECT")
                # link() is atomic and refuses replacement, unlike rename().
                os.link(pending, output_name, dst_dir_fd=output_fd, follow_symlinks=False)
                os.fsync(output_fd)
            finally:
                os.close(output_fd)
        finally:
            pending.unlink(missing_ok=True)
        return output_name

    def receipt(self, row):
        return {"type": "PublicationReceipt", "request_id": row["id"],
                "subject": json.loads(row["subject"]), "grant_id": row["grant_id"],
                "evaluation_id": row["evaluation_id"], "commit_sequence": row["commit_sequence"],
                "status": row["status"], "output_name": row["output_name"], "authority_mode": self.mode}

    def finish(self, uid, request_id, status):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute("UPDATE attempts SET status=? WHERE id=?", (status, request_id))
            self.event("PublicationOutcomeRecorded", uid, {"request_id": request_id, "status": status})
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def do_reconcile(self, uid, request_id):
        uuid_id(request_id)
        row = self.db.execute("SELECT * FROM attempts WHERE id=?", (request_id,)).fetchone()
        if not row:
            raise Denied("ATTEMPT_NOT_FOUND")
        if row["status"] == "unknown":
            path = self.state / "published" / row["output_name"]
            try:
                data = read_file(path, 65536)
            except FileNotFoundError:
                self.finish(uid, request_id, "not_published")
            except (OSError, Denied):
                pass
            else:
                if hashlib.sha256(data).hexdigest() == json.loads(row["subject"])["payload_digest"]:
                    self.sync_dir(path.parent)
                    self.finish(uid, request_id, "confirmed")
            row = self.db.execute("SELECT * FROM attempts WHERE id=?", (request_id,)).fetchone()
        return {"receipt": self.receipt(row)}

    def do_inspect(self, uid):
        return {"grant_count": self.db.execute("SELECT count(*) FROM grants").fetchone()[0],
                "attempt_count": self.db.execute("SELECT count(*) FROM attempts").fetchone()[0],
                "event_count": self.db.execute("SELECT count(*) FROM events").fetchone()[0]}


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.request.settimeout(3)
        try:
            _, uid, _ = struct.unpack("3i", self.request.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
            line = self.rfile.readline(MAX_MESSAGE + 1)
            if len(line) > MAX_MESSAGE or not line.endswith(b"\n"):
                raise Denied("INVALID_FRAME")
            message = decode_json(line.decode("utf-8"))
            response = self.server.broker.request(uid, message)
        except Denied as error:
            response = {"ok": False, "error": str(error)}
        except (UnicodeError, ValueError, TypeError, RecursionError):
            response = {"ok": False, "error": "INVALID_REQUEST"}
        except (OSError, sqlite3.Error):
            # A storage fault never becomes a successful publication result.
            response = {"ok": False, "error": "STORAGE_OR_TRANSPORT_ERROR"}
        try:
            self.wfile.write((canonical(response) + "\n").encode("utf-8"))
        except OSError:
            pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    broker = Broker(args.config)
    # Only a stale socket owned by this broker can be replaced after acquiring
    # its exclusive state lock. Arbitrary files/symlinks are never unlinked.
    if broker.socket_path.exists() or broker.socket_path.is_symlink():
        info = broker.socket_path.lstat()
        if not stat.S_ISSOCK(info.st_mode) or info.st_uid != broker.uid:
            raise Denied("UNSAFE_SOCKET_REPLACEMENT")
        broker.socket_path.unlink()
    with socketserver.UnixStreamServer(str(broker.socket_path), Handler) as server:
        server.broker = broker
        os.chmod(broker.socket_path, 0o666)
        server.serve_forever(poll_interval=0.05)


if __name__ == "__main__":
    main()
