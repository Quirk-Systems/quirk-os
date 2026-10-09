"""Observable file behavior and native-byte preservation for the offline CLI."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/unsigned_rationale.py"
spec = importlib.util.spec_from_file_location("unsigned_rationale_cli_test", SCRIPT)
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)
EXAMPLE = ROOT / "examples/unsigned-rationale/example.json"


class FileBoundaryTests(unittest.TestCase):
    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                              capture_output=True, text=True, timeout=10)

    def packet(self):
        return codec.parse_packet(EXAMPLE.read_bytes())

    def test_export_then_reopen_preserves_the_actual_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "result"
            result = self.cli("export", EXAMPLE, "--out", out)
            self.assertEqual(result.returncode, 0, result.stderr)
            digest = json.loads(result.stdout)["packet_sha256"]
            raw = (out / "rationale.json").read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
            self.assertEqual((out / "rationale.sha256").read_text(), digest + "\n")
            reopened = self.cli("reopen", out)
            self.assertEqual(reopened.returncode, 0, reopened.stderr)
            record = json.loads(reopened.stdout)
            self.assertEqual(record["packet"], self.packet())
            self.assertEqual(record["integrity"]["sidecar"], "matched")
            self.assertEqual({s["state"] for s in record["source_states"]}, {"not_checked"})

    def test_repeat_export_never_overwrites_a_directory_or_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "owned"
            out.mkdir()
            kept = out / "rationale.json"
            kept.write_bytes(b"unrelated preexisting content")
            result = self.cli("export", EXAMPLE, "--out", out)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stderr)["error"]["code"], "OUTPUT_EXISTS")
            self.assertEqual(kept.read_bytes(), b"unrelated preexisting content")
            self.assertEqual(list(out.iterdir()), [kept])

    def test_interrupted_bundle_is_not_reported_as_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "incomplete"
            actual_write = codec._write_new

            def fail_sidecar(path, raw):
                if path.name == "rationale.sha256":
                    raise OSError("simulated disk failure")
                actual_write(path, raw)

            with patch.object(codec, "_write_new", side_effect=fail_sidecar):
                with self.assertRaises(OSError):
                    codec.write_bundle(self.packet(), out)
            self.assertTrue((out / "rationale.json").exists())
            self.assertFalse((out / "COMMITTED.json").exists())
            result = self.cli("reopen", out)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stderr)["error"]["code"], "INCOMPLETE_BUNDLE")

    def test_tampered_packet_sidecar_and_marker_are_rejected(self):
        for target in ("rationale.json", "rationale.sha256", "COMMITTED.json"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "result"
                codec.write_bundle(self.packet(), out)
                file = out / target
                if target == "rationale.json":
                    raw = file.read_bytes().replace(b"Synthetic", b"Changed!!", 1)
                    file.write_bytes(raw)
                elif target == "rationale.sha256":
                    file.write_text("0" * 64 + "\n")
                else:
                    marker = json.loads(file.read_text())
                    marker["files"][0] = "../external.json"
                    file.write_text(json.dumps(marker))
                self.assertNotEqual(self.cli("reopen", out).returncode, 0)

    def test_symlinked_bundle_member_cannot_substitute_another_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "result"
            codec.write_bundle(self.packet(), out)
            original = (out / "rationale.json").read_bytes()
            (Path(tmp) / "outside.json").write_bytes(original)
            (out / "rationale.json").unlink()
            (out / "rationale.json").symlink_to(Path(tmp) / "outside.json")
            self.assertEqual(self.cli("reopen", out).returncode, 2)

    def test_cli_source_observations_show_change_without_editing_packet(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "result"
            packet = self.packet()
            codec.write_bundle(packet, out)
            before = (out / "rationale.json").read_bytes()
            observations = {packet["sources"][0]["id"]: {"available": True, "revision": None, "sha256": "0" * 64},
                            packet["sources"][1]["id"]: {"available": False, "revision": None, "sha256": None}}
            obs = Path(tmp) / "observations.json"
            obs.write_text(json.dumps(observations))
            result = self.cli("reopen", out, "--observations", obs)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual([s["state"] for s in json.loads(result.stdout)["source_states"]], ["stale", "unavailable"])
            self.assertEqual(before, (out / "rationale.json").read_bytes())

    def test_cli_errors_do_not_echo_private_content_or_tracebacks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "private.json"
            path.write_text('{"secret":"PRIVATE-STRING", "bad":')
            result = self.cli("validate", path)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("PRIVATE-STRING", result.stderr + result.stdout)
            self.assertNotIn("Traceback", result.stderr)
            self.assertEqual(json.loads(result.stderr)["error"]["code"], "INVALID_JSON")

    def test_invalid_calendar_and_timezone_minutes_are_rejected(self):
        for time in ("2026-09-10T00:00:00+00:99", "2026-09-10T00:00:00+24:00", "2026-02-30T00:00:00Z"):
            with self.subTest(time=time):
                packet = self.packet()
                packet["sources"][0]["inspected_at"] = time
                with self.assertRaises(codec.ProtocolError):
                    codec.validate_packet(packet)

    def test_exported_capability_cannot_promote_its_own_candidate_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            packet = self.packet()
            codec.write_bundle(packet, Path(tmp) / "good")
            promoted = copy.deepcopy(packet)
            promoted["status"] = "ACTIVE"
            with self.assertRaises(codec.ProtocolError):
                codec.write_bundle(promoted, Path(tmp) / "bad")
            self.assertFalse((Path(tmp) / "bad").exists())

    def test_native_preference_fixture_is_fingerprinted_without_reencoding(self):
        native = ROOT / "examples/unsigned-rationale/producer-event.native.json"
        raw = native.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), "6ae22b2b27319803602b692e7ea73456568d97eaa1e1624670c53dc7a656e9d6")
        record = json.loads(raw)
        payload_before = record["payload_json"].encode("utf-8")
        self.assertEqual(hashlib.sha256(payload_before).hexdigest(), record["payload_digest"])
        stamp = codec.capture_source(raw, source_id="source.preference-fixture", locator="repo:quirk-preference/producer-event",
                                    inspected_at="2026-09-10T01:00:00Z", revision="f70a713c097436172760d633ccee9bacb071483b")
        self.assertEqual(stamp["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(native.read_bytes(), raw)
        self.assertEqual(record["payload_json"].encode("utf-8"), payload_before)
        self.assertEqual(record["graph_state"], "AWAITING_INTEGRATION")
        # Native semantic admission is intentionally not asserted by a byte capture.


if __name__ == "__main__":
    unittest.main()
