"""Linux process-isolation proof for the candidate exact-digest publisher.

Run as a root test supervisor (never as a root broker):
    python -m unittest discover -s tests/exact_digest_publish -v

Every authority is a distinct non-root numeric UID. The authorizer is a
synthetic fixture principal; these tests do not establish a real human UI,
authentication ceremony, or production deployment boundary.
"""

import base64
import copy
import errno
import hashlib
import json
import os
from pathlib import Path
import pwd
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ENV = {"PATH": os.defpath, "PYTHONDONTWRITEBYTECODE": "1", "LANG": "C.UTF-8"}
PAYLOAD = b"Quirk candidate: evidence does not issue authority.\n"


def canonical_digest(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def demote(uid):
    def drop():
        os.setgroups([])
        os.setgid(uid)
        os.setuid(uid)
        os.umask(0o077)
    return drop


def unused_uids():
    def mapped_ranges(kind):
        result = []
        for line in Path("/proc/self/" + kind + "_map").read_text().splitlines():
            start, _, length = map(int, line.split())
            result.append((start, start + length))
        return result

    uid_ranges, gid_ranges = mapped_ranges("uid"), mapped_ranges("gid")
    available = [(max(1, u0, g0), min(u1, g1))
                 for u0, u1 in uid_ranges for g0, g1 in gid_ranges
                 if max(1, u0, g0) < min(u1, g1)]
    occupied = {entry.pw_uid for entry in pwd.getpwall()}
    # Include running numeric identities that have no passwd entry.
    for process in Path("/proc").iterdir():
        if process.name.isdigit():
            try:
                for line in (process / "status").read_text().splitlines():
                    if line.startswith("Uid:"):
                        occupied.update(map(int, line.split()[1:]))
            except (OSError, ValueError):
                pass
    selected = []
    # Prefer identities outside common system-account ranges, then use any
    # mapped unused numeric identities if this namespace has a smaller range.
    search_ranges = [(max(low, 61001), min(high, 65000)) for low, high in available] + available
    for low, high in search_ranges:
        for candidate in range(low, high):
            if candidate not in occupied and candidate not in selected:
                selected.append(candidate)
                if len(selected) == 5:
                    return dict(zip(("broker", "authorizer", "evaluator", "composer", "stranger"), selected))
    raise RuntimeError(
        "Security proof BLOCKED: this user namespace does not map five unused non-root UID/GID pairs. "
        "Run on a Linux host or CI runner with those identities mapped; synthetic same-UID roles cannot substitute. "
        f"uid_map={uid_ranges!r}; gid_map={gid_ranges!r}"
    )


class Fixture:
    def __init__(self, policy_changes=None):
        self.temp = tempfile.TemporaryDirectory(prefix="quirk-publish-proof-")
        self.root = Path(self.temp.name)
        self.root.chmod(0o755)
        self.uids = unused_uids()
        self.code = self.root / "code"
        self.code.mkdir(mode=0o755)
        (self.code / "scripts").mkdir(mode=0o755)
        (self.code / "scripts" / "__init__.py").write_text("")
        source = ROOT / "scripts" / "exact_digest_publish"
        if not (source / "broker.py").is_file():
            self.temp.cleanup()
            raise RuntimeError("broker implementation is missing; security proof cannot pass")
        shutil.copytree(source, self.code / "scripts" / "exact_digest_publish",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copyfile(HERE / "peer_client.py", self.code / "peer_client.py")
        (self.code / "crash_driver.py").write_text(
            "import os, sys, time\n"
            "from scripts.exact_digest_publish.broker import Broker, main\n"
            "position = sys.argv.pop(1)\n"
            "original = Broker._dispatch\n"
            "def crash(self, snapshot, request_id):\n"
            "    if position == 'before': os._exit(97)\n"
            "    if position == 'delay':\n"
            "        time.sleep(2.2)\n"
            "        return original(self, snapshot, request_id)\n"
            "    result = original(self, snapshot, request_id)\n"
            "    os._exit(97)\n"
            "Broker._dispatch = crash\n"
            "main()\n"
        )
        for path in [self.code, *self.code.rglob("*")]:
            os.chown(path, 0, 0)
            path.chmod(0o755 if path.is_dir() else 0o644)
        self.state = self.root / "state"
        self.socket_dir = self.root / "socket"
        for path, mode in ((self.state, 0o700), (self.socket_dir, 0o755)):
            path.mkdir(mode=mode)
            os.chown(path, self.uids["broker"], self.uids["broker"])
            path.chmod(mode)
        self.socket = self.socket_dir / "broker.sock"
        self.config_path = self.root / "config.json"
        self.policy = {"id": "publish.v1", "revision": 1,
                       "evaluation_ttl_seconds": 300, "max_grant_seconds": 300,
                       "max_payload_bytes": 65536}
        self.policy.update(policy_changes or {})
        self.config = {"version": 1, "broker_uid": self.uids["broker"],
                       "authorizer_uid": self.uids["authorizer"],
                       "evaluator_uid": self.uids["evaluator"],
                       "composer_uid": self.uids["composer"],
                       "state_dir": str(self.state), "socket_path": str(self.socket),
                       "destination_id": "local:fixture-owner:private",
                       "authority_mode": "test_fixture", "policy": self.policy}
        self.config_path.write_text(json.dumps(self.config))
        self.config_path.chmod(0o644)
        self.process = None
        self.log_path = self.root / "broker.log"
        self.log = self.log_path.open("ab", buffering=0)
        try:
            self.start()
        except BaseException:
            self.close()
            raise

    def command(self, crash=None):
        if crash:
            return [sys.executable, "-B", "crash_driver.py", crash, "--config", str(self.config_path)]
        return [sys.executable, "-B", "-m", "scripts.exact_digest_publish.broker",
                "--config", str(self.config_path)]

    def spawn(self, crash=None):
        return subprocess.Popen(self.command(crash), cwd=self.code, env=ENV,
                                stdin=subprocess.DEVNULL, stdout=self.log, stderr=self.log,
                                close_fds=True, preexec_fn=demote(self.uids["broker"]))

    def start(self, crash=None):
        self.process = self.spawn(crash)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError("broker startup failed: " + self.log_path.read_text(errors="replace"))
            if self.socket.exists():
                response = self.rpc("composer", {"action": "status"})
                if response.get("ok") is True:
                    self.status = response
                    return
            time.sleep(0.02)
        raise RuntimeError("broker startup timed out: " + self.log_path.read_text(errors="replace"))

    def stop(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=3)

    def close(self):
        self.stop()
        self.log.close()
        self.temp.cleanup()

    def client(self, role, command):
        result = subprocess.run([sys.executable, "-I", str(self.code / "peer_client.py")],
                                input=json.dumps(command), text=True, capture_output=True,
                                cwd=self.code, env=ENV, preexec_fn=demote(self.uids[role]),
                                close_fds=True, timeout=30)
        if result.returncode != 0:
            raise RuntimeError("fixture client failed: " + result.stderr)
        return json.loads(result.stdout)

    def rpc(self, role, request):
        return self.client(role, {"mode": "rpc", "socket_path": str(self.socket), "request": request})

    def stage(self, payload=PAYLOAD, artifact_id="fixture.artifact"):
        response = self.rpc("composer", {"action": "stage", "artifact_id": artifact_id,
                                        "payload_b64": base64.b64encode(payload).decode()})
        if response.get("ok") is not True:
            raise AssertionError(response)
        return response["subject"]

    def evaluate(self, subject, verdict="PASS"):
        return self.rpc("evaluator", {"action": "evaluate", "subject": subject, "verdict": verdict})

    def grant_request(self, subject, grant_id=None, expires_at=None):
        return {"action": "grant", "subject": subject, "grant_id": grant_id or str(uuid.uuid4()),
                "expires_at": expires_at or int(time.time()) + 120,
                "scope_digest": canonical_digest(subject), "decision": "approve"}

    def grant(self, subject, **kwargs):
        request = self.grant_request(subject, **kwargs)
        response = self.rpc("authorizer", request)
        if response.get("ok") is not True:
            raise AssertionError(response)
        return request["grant_id"]

    def publish(self, subject, grant_id, request_id=None):
        return self.rpc("composer", {"action": "publish", "subject": subject, "grant_id": grant_id,
                                     "request_id": request_id or str(uuid.uuid4())})

    def reconcile(self, request_id):
        return self.rpc("composer", {"action": "reconcile", "request_id": request_id})

    def ready(self, payload=PAYLOAD, artifact_id="fixture.artifact"):
        subject = self.stage(payload, artifact_id)
        result = self.evaluate(subject)
        if result.get("ok") is not True:
            raise AssertionError(result)
        grant_id = self.grant(subject)
        return subject, grant_id

    def outputs(self):
        directory = self.state / "published"
        return sorted(directory.iterdir()) if directory.exists() else []

    def inspect(self):
        response = self.rpc("authorizer", {"action": "inspect"})
        if response.get("ok") is not True:
            raise AssertionError(response)
        return response

    def grant_rows(self):
        # This is root-supervisor observation, never a client capability.
        with sqlite3.connect(f"file:{self.state / 'state.sqlite3'}?mode=ro", uri=True) as db:
            return db.execute("SELECT * FROM grants ORDER BY id").fetchall()


class EnforcementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if sys.platform != "linux" or os.geteuid() != 0:
            raise RuntimeError("Security suite requires Linux and root only as test supervisor; no green skips")
        unused_uids()

    def setUp(self):
        self.fixture = Fixture()
        self.addCleanup(self.fixture.close)

    def denied(self, response):
        self.assertIs(response.get("ok"), False, response)
        self.assertIsInstance(response.get("error"), str, response)
        self.assertTrue(response["error"], response)

    def confirmed(self, response, subject, request_id, grant_id):
        self.assertIs(response.get("ok"), True, response)
        receipt = response["receipt"]
        self.assertEqual(receipt["type"], "PublicationReceipt")
        self.assertEqual(receipt["authority_mode"], "test_fixture")
        self.assertEqual(receipt["status"], "confirmed", receipt)
        self.assertEqual(receipt["subject"], subject)
        self.assertEqual(receipt["request_id"], request_id)
        self.assertEqual(receipt["grant_id"], grant_id)
        self.assertTrue(receipt["evaluation_id"])
        self.assertIsInstance(receipt["commit_sequence"], int)
        self.assertEqual(receipt["output_name"], request_id + ".bin")
        self.assertEqual((self.fixture.state / "published" / receipt["output_name"]).read_bytes(), PAYLOAD)
        return receipt

    def test_01_synthetic_authorizer_permits_exact_bytes_and_receipt(self):
        f = self.fixture
        self.assertEqual(f.status["authority_mode"], "test_fixture")
        self.assertEqual(len(set(f.uids.values())), 5)
        self.assertNotIn(0, f.uids.values())
        for role in ("authorizer", "evaluator", "composer"):
            identity = f.client(role, {"mode": "identity"})
            self.assertEqual(identity["uid"], f.uids[role])
            self.assertEqual(identity["euid"], f.uids[role])
            self.assertEqual(identity["gid"], f.uids[role])
            self.assertEqual(identity["groups"], [])
            # CPython may add LC_CTYPE while coercing a locale. No inherited
            # repository credentials, CI secrets, or arbitrary PATH survive.
            self.assertLessEqual(set(identity["environment_keys"]), set(ENV) | {"LC_CTYPE"})
        broker_environment = (Path("/proc") / str(f.process.pid) / "environ").read_bytes()
        broker_keys = {entry.split(b"=", 1)[0].decode()
                       for entry in broker_environment.split(b"\0") if entry}
        self.assertEqual(broker_keys, set(ENV))
        subject, grant_id = f.ready()
        self.assertEqual(subject["payload_digest"], hashlib.sha256(PAYLOAD).hexdigest())
        request_id = str(uuid.uuid4())
        self.confirmed(f.publish(subject, grant_id, request_id), subject, request_id, grant_id)
        self.assertEqual(len(f.outputs()), 1)

    def test_02_one_thousand_evaluations_cannot_create_any_grant(self):
        f = self.fixture
        subject = f.stage()
        before = f.inspect()["grant_count"]
        before_rows = f.grant_rows()
        result = f.client("evaluator", {"mode": "repeat_rpc", "socket_path": str(f.socket),
                                      "count": 1000,
                                      "request": {"action": "evaluate", "subject": subject, "verdict": "PASS"}})
        self.assertEqual(result["count"], 1000)
        self.assertIs(result["all_ok"], True, result)
        self.assertEqual(f.inspect()["grant_count"], before)
        self.assertEqual(f.grant_rows(), before_rows)
        self.assertEqual(before_rows, [])
        self.assertEqual(before, 0)
        self.denied(f.publish(subject, str(uuid.uuid4())))
        self.assertEqual(f.outputs(), [])

    def test_03_evaluator_and_composer_cannot_issue_or_forge_human_grants(self):
        f = self.fixture
        subject = f.stage()
        for role in ("evaluator", "composer"):
            with self.subTest(role=role):
                self.denied(f.rpc(role, f.grant_request(subject)))
                forged = f.grant_request(subject)
                forged.update({"role": "authorizer", "approved": True,
                               "uid": f.uids["authorizer"]})
                self.denied(f.rpc(role, forged))
        self.assertEqual(f.inspect()["grant_count"], 0)
        self.assertEqual(f.outputs(), [])

    def test_04_additional_fields_cannot_turn_evidence_into_authority(self):
        f = self.fixture
        subject = f.stage()
        self.denied(f.rpc("evaluator", {"action": "evaluate", "subject": subject,
                                        "verdict": "PASS", "approved": True}))
        forged = copy.deepcopy(subject)
        forged["approved"] = True
        self.denied(f.evaluate(forged))
        self.assertEqual(f.inspect()["grant_count"], 0)

    def test_05_kernel_denies_both_workers_direct_writes(self):
        f = self.fixture
        subject, grant_id = f.ready()
        request_id = str(uuid.uuid4())
        f.publish(subject, grant_id, request_id)
        paths = {"grant_store": str(f.state / "state.sqlite3"),
                 "grant_store_replacement": str(f.state / "forged-grants.json"),
                 "configuration": str(f.config_path),
                 "guard_code": str(f.code / "scripts" / "exact_digest_publish" / "broker.py"),
                 "code_injection": str(f.code / "scripts" / "exact_digest_publish" / "forged.py"),
                 "existing_output": str(f.state / "published" / (request_id + ".bin")),
                 "alternate_output": str(f.state / "published" / "bypass.bin"),
                 "snapshot_injection": str(f.state / "payloads" / "bypass.bin"),
                 "socket_replacement": str(f.socket_dir / "substitute.sock")}
        for role in ("evaluator", "composer"):
            result = f.client(role, {"mode": "write_probes", "paths": paths})
            for boundary, evidence in result.items():
                with self.subTest(role=role, boundary=boundary):
                    self.assertIs(evidence["denied"], True, evidence)
                    self.assertIn(evidence["errno"], (errno.EACCES, errno.EPERM))
        self.assertEqual(len(f.outputs()), 1)

    def test_06_kernel_peer_identity_cannot_be_impersonated(self):
        f = self.fixture
        subject = f.stage()
        for role in ("evaluator", "composer"):
            result = f.client(role, {"mode": "impersonate", "target_uid": f.uids["authorizer"],
                                     "socket_path": str(f.socket), "request": f.grant_request(subject)})
            self.assertIs(result["setuid_denied"], True, result)
            self.assertEqual(result["uid"], f.uids[role])
            self.denied(result["response"])
        self.denied(f.rpc("stranger", {"action": "status"}))

    def test_07_roles_cannot_borrow_each_others_actions(self):
        f = self.fixture
        subject, grant_id = f.ready()
        requests = {"grant": f.grant_request(subject),
                    "evaluate": {"action": "evaluate", "subject": subject, "verdict": "PASS"},
                    "publish": {"action": "publish", "subject": subject, "grant_id": grant_id,
                                "request_id": str(uuid.uuid4())},
                    "revoke": {"action": "revoke", "grant_id": grant_id},
                    "set_policy": {"action": "set_policy", "policy": dict(f.policy, revision=2)}}
        forbidden = {"evaluator": ("grant", "publish", "revoke", "set_policy"),
                     "composer": ("grant", "evaluate", "revoke", "set_policy"),
                     "authorizer": ("evaluate", "publish")}
        for role, operations in forbidden.items():
            for operation in operations:
                with self.subTest(role=role, operation=operation):
                    self.denied(f.rpc(role, requests[operation]))
        self.assertEqual(f.outputs(), [])

    def test_08_each_subject_dimension_is_bound_to_approval(self):
        f = self.fixture
        subject, grant_id = f.ready()
        mutations = {"payload_digest": "0" * 64, "artifact_id": "another.artifact",
                     "operation": "delete", "destination_id": "local:other:public",
                     "policy_digest": "f" * 64}
        for field, replacement in mutations.items():
            with self.subTest(field=field):
                altered = dict(subject, **{field: replacement})
                self.denied(f.publish(altered, grant_id))
        # Give a second valid identity its own passing evidence, so this case
        # cannot pass merely because the changed subject lacks an evaluation.
        another_identity = f.stage(PAYLOAD, "another.artifact")
        self.assertIs(f.evaluate(another_identity)["ok"], True)
        self.denied(f.publish(another_identity, grant_id))
        self.assertEqual(f.outputs(), [])
        request_id = str(uuid.uuid4())
        self.confirmed(f.publish(subject, grant_id, request_id), subject, request_id, grant_id)

    def test_09_scope_digest_and_decision_must_match_human_request(self):
        f = self.fixture
        subject = f.stage()
        wrong_digest = f.grant_request(subject)
        wrong_digest["scope_digest"] = "0" * 64
        self.denied(f.rpc("authorizer", wrong_digest))
        wrong_decision = f.grant_request(subject)
        wrong_decision["decision"] = "PASS"
        self.denied(f.rpc("authorizer", wrong_decision))
        self.assertEqual(f.inspect()["grant_count"], 0)

    def test_10_current_evaluation_must_pass_and_not_be_invalidated(self):
        f = self.fixture
        subject = f.stage()
        grant_id = f.grant(subject)
        self.denied(f.publish(subject, grant_id))
        for verdict in ("FAIL", "INVALIDATED"):
            self.assertIs(f.evaluate(subject)["ok"], True)
            self.assertIs(f.evaluate(subject, verdict)["ok"], True)
            self.denied(f.publish(subject, grant_id))
        self.assertEqual(f.outputs(), [])

    def test_11_policy_revision_invalidates_old_evidence_and_grant(self):
        f = self.fixture
        subject, grant_id = f.ready()
        response = f.rpc("authorizer", {"action": "set_policy", "policy": dict(f.policy, revision=2)})
        self.assertIs(response.get("ok"), True, response)
        self.denied(f.publish(subject, grant_id))
        new_subject = f.stage()
        self.assertNotEqual(new_subject["policy_digest"], subject["policy_digest"])
        self.assertIs(f.evaluate(new_subject)["ok"], True)
        self.denied(f.publish(new_subject, grant_id))
        fresh_grant = f.grant(new_subject)
        request_id = str(uuid.uuid4())
        self.confirmed(f.publish(new_subject, fresh_grant, request_id), new_subject, request_id, fresh_grant)

    def test_12_revocation_before_dispatch_blocks_publication(self):
        f = self.fixture
        subject, grant_id = f.ready()
        response = f.rpc("authorizer", {"action": "revoke", "grant_id": grant_id})
        self.assertIs(response.get("ok"), True, response)
        self.denied(f.publish(subject, grant_id))
        self.assertEqual(f.outputs(), [])

    def test_13_expired_approval_is_not_effective(self):
        f = self.fixture
        subject = f.stage()
        self.assertIs(f.evaluate(subject)["ok"], True)
        expires_at = int(time.time()) + 2
        grant_id = f.grant(subject, expires_at=expires_at)
        time.sleep(max(0, expires_at - time.time()) + 0.05)
        self.denied(f.publish(subject, grant_id))
        self.assertEqual(f.outputs(), [])

    def test_14_stale_evaluation_cannot_use_current_grant(self):
        f = self.fixture
        response = f.rpc("authorizer", {"action": "set_policy",
                                        "policy": dict(f.policy, revision=2, evaluation_ttl_seconds=1)})
        self.assertIs(response.get("ok"), True, response)
        subject, grant_id = f.ready()
        time.sleep(1.1)
        self.denied(f.publish(subject, grant_id))
        self.assertEqual(f.outputs(), [])

    def test_15_grant_is_single_use_and_request_replay_has_no_duplicate_effect(self):
        f = self.fixture
        subject, grant_id = f.ready()
        request_id = str(uuid.uuid4())
        receipt = self.confirmed(f.publish(subject, grant_id, request_id), subject, request_id, grant_id)
        replay = f.publish(subject, grant_id, request_id)
        self.assertIs(replay.get("ok"), True, replay)
        self.assertEqual(replay["receipt"], receipt)
        self.denied(f.publish(subject, grant_id, str(uuid.uuid4())))
        self.assertEqual(len(f.outputs()), 1)

    def test_16_grant_and_request_ids_cannot_be_rebound(self):
        f = self.fixture
        subject, grant_id = f.ready()
        other = f.stage(b"Different candidate.\n", "fixture.other")
        self.assertIs(f.evaluate(other)["ok"], True)
        self.denied(f.rpc("authorizer", f.grant_request(other, grant_id=grant_id)))
        self.assertEqual(f.inspect()["grant_count"], 1)
        request_id = str(uuid.uuid4())
        self.confirmed(f.publish(subject, grant_id, request_id), subject, request_id, grant_id)
        other_grant = f.grant(other)
        self.denied(f.publish(other, other_grant, request_id))
        self.assertEqual(len(f.outputs()), 1)

    def test_17_staging_new_bytes_does_not_redirect_old_approval(self):
        f = self.fixture
        subject, grant_id = f.ready()
        changed = f.stage(b"A source changed after its first staging.\n")
        self.assertNotEqual(changed["payload_digest"], subject["payload_digest"])
        self.assertIs(f.evaluate(changed)["ok"], True)
        self.denied(f.publish(changed, grant_id))
        request_id = str(uuid.uuid4())
        self.confirmed(f.publish(subject, grant_id, request_id), subject, request_id, grant_id)

    def test_18_changed_snapshot_bytes_fail_closed(self):
        f = self.fixture
        subject, grant_id = f.ready()
        snapshots = [path for path in (f.state / "payloads").rglob("*") if path.is_file()]
        self.assertEqual(len(snapshots), 1)
        # Root supervisor simulates damaged trusted storage. Worker access to
        # this same directory is separately denied by the kernel in test 05.
        snapshots[0].write_bytes(b"Corrupted staging bytes.\n")
        self.denied(f.publish(subject, grant_id))
        self.assertEqual(f.outputs(), [])

    def test_19_second_broker_cannot_own_the_same_state(self):
        f = self.fixture
        second = f.spawn()
        try:
            returncode = second.wait(timeout=5)
        except subprocess.TimeoutExpired:
            second.kill()
            second.wait(timeout=3)
            self.fail("second broker stayed alive instead of rejecting exclusive state ownership")
        self.assertNotEqual(returncode, 0)
        self.assertIs(f.rpc("composer", {"action": "status"}).get("ok"), True)

    def test_20_revocation_after_dispatch_preserves_historical_receipt(self):
        f = self.fixture
        subject, grant_id = f.ready()
        request_id = str(uuid.uuid4())
        receipt = self.confirmed(f.publish(subject, grant_id, request_id), subject, request_id, grant_id)
        self.assertIs(f.rpc("authorizer", {"action": "revoke", "grant_id": grant_id})["ok"], True)
        result = f.reconcile(request_id)
        self.assertIs(result.get("ok"), True, result)
        self.assertEqual(result["receipt"], receipt)
        self.denied(f.publish(subject, grant_id))
        self.assertEqual(len(f.outputs()), 1)

    def test_21_expiry_after_dispatch_preserves_historical_receipt(self):
        f = self.fixture
        subject = f.stage()
        self.assertIs(f.evaluate(subject)["ok"], True)
        expires_at = int(time.time()) + 2
        grant_id = f.grant(subject, expires_at=expires_at)
        request_id = str(uuid.uuid4())
        receipt = self.confirmed(f.publish(subject, grant_id, request_id), subject, request_id, grant_id)
        time.sleep(max(0, expires_at - time.time()) + 0.05)
        self.assertEqual(f.reconcile(request_id)["receipt"], receipt)
        self.denied(f.publish(subject, grant_id))
        self.assertEqual(len(f.outputs()), 1)

    def test_22_crash_before_dispatch_consumes_grant_and_does_not_retry(self):
        f = self.fixture
        subject, grant_id = f.ready()
        request_id = str(uuid.uuid4())
        f.stop()
        f.start(crash="before")
        response = f.publish(subject, grant_id, request_id)
        self.assertIn("transport_error", response, response)
        self.assertEqual(f.process.wait(timeout=5), 97)
        f.start()
        recovered = f.reconcile(request_id)
        self.assertIs(recovered.get("ok"), True, recovered)
        self.assertEqual(recovered["receipt"]["status"], "not_published")
        self.assertEqual(f.outputs(), [])
        replay = f.publish(subject, grant_id, request_id)
        self.assertIs(replay.get("ok"), True, replay)
        self.assertEqual(replay["receipt"]["status"], "not_published")
        self.denied(f.publish(subject, grant_id))
        self.assertEqual(f.outputs(), [])

    def test_23_crash_after_dispatch_reconciles_one_exact_effect(self):
        f = self.fixture
        subject, grant_id = f.ready()
        request_id = str(uuid.uuid4())
        f.stop()
        f.start(crash="after")
        response = f.publish(subject, grant_id, request_id)
        self.assertIn("transport_error", response, response)
        self.assertEqual(f.process.wait(timeout=5), 97)
        self.assertEqual(len(f.outputs()), 1)
        f.start()
        self.confirmed(f.reconcile(request_id), subject, request_id, grant_id)
        self.confirmed(f.publish(subject, grant_id, request_id), subject, request_id, grant_id)
        self.denied(f.publish(subject, grant_id))
        self.assertEqual(len(f.outputs()), 1)

    def test_24_unexpected_output_is_unknown_and_never_redispatched(self):
        f = self.fixture
        subject, grant_id = f.ready()
        request_id = str(uuid.uuid4())
        f.stop()
        f.start(crash="after")
        f.publish(subject, grant_id, request_id)
        self.assertEqual(f.process.wait(timeout=5), 97)
        output = f.state / "published" / (request_id + ".bin")
        output.write_bytes(b"Unexpected bytes in trusted sink.\n")
        f.start()
        recovered = f.reconcile(request_id)
        self.assertIs(recovered.get("ok"), True, recovered)
        self.assertEqual(recovered["receipt"]["status"], "unknown")
        replay = f.publish(subject, grant_id, request_id)
        self.assertEqual(replay["receipt"]["status"], "unknown")
        self.assertEqual(output.read_bytes(), b"Unexpected bytes in trusted sink.\n")
        self.assertEqual(len(f.outputs()), 1)

    def test_25_grant_expiry_during_dispatch_preparation_blocks_effect(self):
        f = self.fixture
        subject = f.stage()
        self.assertIs(f.evaluate(subject)["ok"], True)
        f.stop()
        f.start(crash="delay")
        grant_id = f.grant(subject, expires_at=int(time.time()) + 2)
        request_id = str(uuid.uuid4())
        response = f.publish(subject, grant_id, request_id)
        self.denied(response)
        self.assertEqual(response["error"], "AUTHORITY_EXPIRED_BEFORE_EFFECT")
        # An admitted attempt proves this reached dispatch while valid, then
        # expired during preparation. An early rejection cannot pass the test.
        self.assertEqual(f.inspect()["attempt_count"], 1)
        receipt = f.reconcile(request_id)["receipt"]
        self.assertEqual(receipt["status"], "not_published")
        self.assertEqual(f.outputs(), [])
        self.assertEqual(f.publish(subject, grant_id, request_id)["receipt"], receipt)
        self.denied(f.publish(subject, grant_id))
        self.assertEqual(f.outputs(), [])

    def test_26_evaluation_expiry_during_dispatch_preparation_blocks_effect(self):
        f = self.fixture
        response = f.rpc("authorizer", {"action": "set_policy",
                                        "policy": dict(f.policy, revision=2, evaluation_ttl_seconds=1)})
        self.assertIs(response.get("ok"), True, response)
        subject = f.stage()
        grant_id = f.grant(subject)
        f.stop()
        f.start(crash="delay")
        self.assertIs(f.evaluate(subject)["ok"], True)
        request_id = str(uuid.uuid4())
        response = f.publish(subject, grant_id, request_id)
        self.denied(response)
        self.assertEqual(response["error"], "AUTHORITY_EXPIRED_BEFORE_EFFECT")
        self.assertEqual(f.inspect()["attempt_count"], 1)
        receipt = f.reconcile(request_id)["receipt"]
        self.assertEqual(receipt["status"], "not_published")
        self.assertEqual(f.outputs(), [])
        # Refreshing evidence cannot refill an already consumed human grant.
        self.assertIs(f.evaluate(subject)["ok"], True)
        self.denied(f.publish(subject, grant_id))
        self.assertEqual(f.outputs(), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
