from __future__ import annotations

import copy
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import media_kit as kit


class MediaKitTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.project = json.loads((ROOT / "examples/media-kit/project.json").read_text())
        self.output = self.directory / "kit.zip"

    def build(self, project=None, output=None):
        return kit.pack(project or self.project, ROOT, output or self.output)

    def rewrite(self, *, mutate_manifest=None, mutate_files=None, extra=None):
        with zipfile.ZipFile(self.output) as archive:
            members = {name: archive.read(name) for name in archive.namelist()}
        if mutate_manifest:
            manifest = json.loads(members["kit-manifest.json"])
            mutate_manifest(manifest)
            members["kit-manifest.json"] = kit.canonical(manifest)
        if mutate_files:
            mutate_files(members)
        target = self.directory / "altered.zip"
        with zipfile.ZipFile(target, "w") as archive:
            for name, data in members.items():
                archive.writestr(name, data)
            if extra:
                archive.writestr(*extra)
        return target

    @staticmethod
    def rehash(manifest):
        manifest["project_sha256"] = kit.digest(kit.canonical(manifest["project"]))
        manifest["content_sha256"] = kit.digest(kit.canonical({key: value for key, value in manifest.items() if key != "content_sha256"}))

    def test_roundtrip_carries_originals_alternatives_and_selection(self):
        before = copy.deepcopy(self.project)
        built = self.build()
        reopened = kit.verify(self.output)
        self.assertEqual(built["content_sha256"], reopened["content_sha256"])
        self.assertEqual(reopened["file_count"], 3)
        self.assertEqual(self.project, before)
        with zipfile.ZipFile(self.output) as archive:
            manifest = json.loads(archive.read("kit-manifest.json"))
            self.assertEqual(manifest["project"]["selection"], before["selection"])
            for entry, item in zip(manifest["files"], before["sources"] + before["derivatives"]):
                self.assertEqual(archive.read(entry["archive_path"]), (ROOT / item["path"]).read_bytes())

    def test_same_inputs_produce_identical_zip_bytes(self):
        self.build()
        second = self.directory / "second.zip"
        self.build(output=second)
        self.assertEqual(self.output.read_bytes(), second.read_bytes())

    def test_success_cannot_promote_authority_or_invent_human_benefit(self):
        result = self.build()
        self.assertEqual(result["authority"], kit.AUTHORITY)
        self.assertEqual(result["human_benefit"], "unobserved")
        self.assertEqual(result["signature_status"], "unsigned")
        self.assertEqual(result["selection_actor_type"], "agent")
        self.assertEqual(len(result["open_reviews"]["rights"]), 2)

    def test_each_authority_flag_rejects_escalation(self):
        for key in kit.AUTHORITY:
            with self.subTest(key=key):
                changed = copy.deepcopy(self.project)
                changed["authority"][key] = "live" if key == "ceiling" else True
                with self.assertRaises(kit.KitError):
                    kit.validate_project(changed)

    def test_upstream_approved_or_released_status_is_denied_by_candidate_profile(self):
        for status in ["approved", "released", "superseded", "withdrawn"]:
            with self.subTest(status=status):
                changed = copy.deepcopy(self.project)
                changed["derivatives"][0]["metadata"]["status"] = status
                with self.assertRaisesRegex(kit.KitError, "draft/review"):
                    kit.validate_project(changed)

    def test_release_receipt_cannot_launder_approval(self):
        self.project["derivatives"][0]["metadata"]["release_receipt_ref"] = "self-approved"
        with self.assertRaisesRegex(kit.KitError, "release receipt"):
            self.build()

    def test_unknown_project_effect_and_signed_selection_are_rejected(self):
        for edit in [lambda p: p.update(publish=True), lambda p: p["selection"].update(signature_status="signed")]:
            changed = copy.deepcopy(self.project)
            edit(changed)
            with self.assertRaises(kit.KitError):
                kit.validate_project(changed)

    def test_missing_source_is_rejected(self):
        self.project["derivatives"][0]["source_id"] = "src_missing"
        with self.assertRaisesRegex(kit.KitError, "missing source"):
            self.build()

    def test_source_identity_version_and_capture_reference_are_bound(self):
        for key in ["object_ref", "version", "receipt_ref"]:
            with self.subTest(key=key):
                changed = copy.deepcopy(self.project)
                changed["derivatives"][0]["metadata"]["canonical_source"][key] = "different"
                with self.assertRaisesRegex(kit.KitError, "does not match"):
                    kit.validate_project(changed)

    def test_unlisted_selection_is_rejected(self):
        self.project["selection"]["derivative_id"] = "qmd_absent"
        with self.assertRaisesRegex(kit.KitError, "included derivative"):
            self.build()

    def test_missing_selection_rationale_and_blank_completion_are_rejected(self):
        for key, value in [("rationale", ""), ("completion_condition", "   ")]:
            changed = copy.deepcopy(self.project)
            changed["selection"][key] = value
            with self.assertRaises(kit.KitError):
                kit.validate_project(changed)

    def test_duplicate_ids_and_paths_are_rejected(self):
        for group in ["sources", "derivatives"]:
            changed = copy.deepcopy(self.project)
            changed[group].append(copy.deepcopy(changed[group][0]))
            with self.assertRaisesRegex(kit.KitError, "unique"):
                kit.validate_project(changed)
        self.project["derivatives"][1]["path"] = self.project["derivatives"][0]["path"]
        with self.assertRaisesRegex(kit.KitError, "distinct"):
            self.build()

    def test_changed_source_pin_is_rejected_before_output(self):
        self.project["sources"][0]["sha256"] = "0" * 64
        # The inherited metadata shape cannot check the source bytes. This
        # matched control isolates what the kit adds without changing that schema.
        schema = json.loads((ROOT / "schemas/media-derivative.schema.json").read_text())
        kit.validate_shape(self.project["derivatives"][0]["metadata"], schema, {})
        with self.assertRaisesRegex(kit.KitError, "SHA-256 mismatch"):
            self.build()
        self.assertFalse(self.output.exists())

    def test_changed_derivative_pin_is_rejected(self):
        self.project["derivatives"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(kit.KitError, "SHA-256 mismatch"):
            self.build()

    def test_missing_source_file_is_rejected(self):
        self.project["sources"][0]["path"] = "absent.md"
        with self.assertRaisesRegex(kit.KitError, "Missing regular file"):
            self.build()

    def test_traversal_absolute_backslash_url_and_active_file_types_are_rejected(self):
        for path in ["../escape.txt", "/tmp/file.txt", "a/../b.txt", "a//b.txt", "a/./b.txt", "C:/file.txt", "a\\b.txt", "https://host/file.txt", "bad.html", "bad.svg", "bad.js", "a /b.txt"]:
            with self.subTest(path=path), self.assertRaises(kit.KitError):
                kit.safe_relative(path)

    def test_symlink_sources_are_rejected(self):
        link = self.directory / "linked.md"
        link.symlink_to(ROOT / self.project["sources"][0]["path"])
        with self.assertRaisesRegex(kit.KitError, "Symlinks"):
            kit.read_declared(self.directory, "linked.md")

    def test_existing_output_is_preserved(self):
        self.output.write_bytes(b"keep me")
        with self.assertRaisesRegex(kit.KitError, "already exists"):
            self.build()
        self.assertEqual(self.output.read_bytes(), b"keep me")

    def test_file_and_total_size_limits(self):
        with patch.object(kit, "MAX_FILE", 10), self.assertRaisesRegex(kit.KitError, "file exceeds"):
            self.build()
        with patch.object(kit, "MAX_TOTAL", 10), self.assertRaisesRegex(kit.KitError, "total file limit"):
            self.build()

    def test_duplicate_json_keys_and_nonfinite_numbers_are_rejected(self):
        for data in [b'{"status":"candidate","status":"live"}', b'{"value":NaN}', b'{"value":Infinity}']:
            with self.assertRaises(kit.KitError):
                kit.parse_json(data, "test")

    def test_oversized_json_is_rejected(self):
        with patch.object(kit, "MAX_JSON", 5), self.assertRaisesRegex(kit.KitError, "JSON exceeds"):
            kit.parse_json(b'{"long":true}', "test")

    def test_number_is_not_accepted_as_boolean(self):
        self.project["authority"]["publish_allowed"] = 0
        with self.assertRaisesRegex(kit.KitError, "expected boolean"):
            self.build()

    def test_missing_upstream_fields_and_unknown_schema_features_fail_closed(self):
        metadata = self.project["derivatives"][0]["metadata"]
        upstream = json.loads((ROOT / "schemas/media-derivative.schema.json").read_text())
        for required in upstream["required"]:
            with self.subTest(field=required):
                invalid = copy.deepcopy(self.project)
                del invalid["derivatives"][0]["metadata"][required]
                with self.assertRaises(kit.KitError):
                    kit.validate_project(invalid)
        with self.assertRaisesRegex(kit.KitError, "Unsupported schema keywords"):
            kit.validate_shape(metadata, {**upstream, "if": {}}, {})
        with self.assertRaisesRegex(kit.KitError, "Unsupported schema reference"):
            kit.validate_shape({}, {"$ref": "https://untrusted/schema.json"}, {})

    def test_changed_included_bytes_are_rejected(self):
        self.build()
        target = self.rewrite(mutate_files=lambda files: files.update({next(name for name in files if name.startswith("assets/")): b"changed"}))
        with self.assertRaisesRegex(kit.KitError, "Included file changed"):
            kit.verify(target)

    def test_missing_included_file_is_rejected(self):
        self.build()
        target = self.rewrite(mutate_files=lambda files: files.pop(next(name for name in files if name.startswith("assets/"))))
        with self.assertRaisesRegex(kit.KitError, "Missing included file"):
            kit.verify(target)

    def test_modified_choice_without_rehash_is_rejected(self):
        self.build()
        target = self.rewrite(mutate_manifest=lambda m: m["project"]["selection"].update(rationale="changed"))
        with self.assertRaisesRegex(kit.KitError, "selection fingerprint mismatch"):
            kit.verify(target)

    def test_rehashed_self_promotion_still_fails(self):
        self.build()
        def escalate(manifest):
            manifest["project"]["authority"]["publish_allowed"] = True
            self.rehash(manifest)
        target = self.rewrite(mutate_manifest=escalate)
        with self.assertRaises(kit.KitError):
            kit.verify(target)

    def test_rehashed_inventory_omission_is_rejected(self):
        self.build()
        def omit(manifest):
            manifest["files"].pop()
            self.rehash(manifest)
        target = self.rewrite(mutate_manifest=omit)
        with self.assertRaisesRegex(kit.KitError, "inventory does not match"):
            kit.verify(target)

    def test_rehashed_archive_path_change_is_rejected(self):
        self.build()
        def redirect(manifest):
            manifest["files"][0]["archive_path"] = "../escape.md"
            self.rehash(manifest)
        target = self.rewrite(mutate_manifest=redirect)
        with self.assertRaisesRegex(kit.KitError, "identity or path mismatch"):
            kit.verify(target)

    def test_unlisted_archive_member_is_rejected_without_extraction(self):
        self.build()
        target = self.rewrite(extra=("../escape.txt", b"unlisted"))
        with self.assertRaisesRegex(kit.KitError, "unlisted ZIP members"):
            kit.verify(target)
        self.assertFalse((self.directory.parent / "escape.txt").exists())

    def test_zip_symlink_is_rejected(self):
        self.build()
        info = zipfile.ZipInfo("assets/link.txt")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        target = self.rewrite(extra=(info, b"../../outside"))
        with self.assertRaisesRegex(kit.KitError, "symlinks"):
            kit.verify(target)

    def test_duplicate_zip_name_is_rejected(self):
        self.build()
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            target = self.rewrite(extra=("index.html", b"second version"))
        with self.assertRaisesRegex(kit.KitError, "duplicate ZIP members"):
            kit.verify(target)

    def test_oversized_zip_member_is_rejected_before_reading(self):
        self.build()
        with patch.object(kit, "MAX_FILE", 10), self.assertRaisesRegex(kit.KitError, "size limit"):
            kit.verify(self.output)

    def test_index_cannot_disagree_with_manifest(self):
        self.build()
        target = self.rewrite(mutate_files=lambda files: files.update({"index.html": b"<p>Approved for publication</p>"}))
        with self.assertRaisesRegex(kit.KitError, "index differs"):
            kit.verify(target)

    def test_untrusted_text_is_escaped_in_script_free_index(self):
        self.project["title"] = '<script>alert("bad")</script>'
        self.project["selection"]["rationale"] = '<img src=x onerror="alert(1)">'
        self.build()
        with zipfile.ZipFile(self.output) as archive:
            page = archive.read("index.html").decode()
        self.assertNotIn("<script", page)
        self.assertNotIn("<img", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertIn("Content-Security-Policy", page)

    def test_unknown_manifest_version_and_invalid_zip_have_actionable_errors(self):
        self.build()
        target = self.rewrite(mutate_manifest=lambda m: m.update(schema_version="media-kit.v9000"))
        with self.assertRaisesRegex(kit.KitError, "Unsupported kit/tool version"):
            kit.verify(target)
        invalid = self.directory / "invalid.zip"
        invalid.write_bytes(b"not a zip")
        with self.assertRaisesRegex(kit.KitError, "Unreadable"):
            kit.verify(invalid)

    def test_corrupted_deflate_has_an_actionable_error(self):
        compressed = self.directory / "compressed.zip"
        with zipfile.ZipFile(compressed, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("kit-manifest.json", b'{"source":"example"}' * 50)
        data = bytearray(compressed.read_bytes())
        offset = 30 + len("kit-manifest.json")
        data[offset] = 0xff  # Reserved DEFLATE block type.
        compressed.write_bytes(data)
        with self.assertRaisesRegex(kit.KitError, "Unreadable"):
            kit.verify(compressed)

    def test_cli_reopens_kit_from_fresh_directory_without_source_checkout_files(self):
        self.build()
        result = subprocess.run([sys.executable, str(ROOT / "scripts/media_kit.py"), "verify", str(self.output)], cwd=self.directory, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["integrity"], "verified")

    def test_cli_bad_project_does_not_leave_output(self):
        invalid = self.directory / "invalid.json"
        invalid.write_text('{"publish":true}')
        result = subprocess.run([sys.executable, str(ROOT / "scripts/media_kit.py"), "pack", "--project", str(invalid), "--root", str(ROOT), "--output", str(self.output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL:", result.stderr)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
