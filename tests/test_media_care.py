from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import media_care as care_tool
import media_kit as kit


class MediaCareTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.project = json.loads((ROOT / "examples/media-kit/project.json").read_text())
        self.care = json.loads((ROOT / "examples/media-kit/care.json").read_text())
        for item in self.project["sources"] + self.project["derivatives"]:
            target = self.directory / item["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / item["path"], target)
        self.sequence = 0
        self.rebuild()

    def rebuild(self):
        self.sequence += 1
        self.output = self.directory / f"kit-{self.sequence}.zip"
        self.packed = kit.pack(self.project, self.directory, self.output)
        self.care["kit_content_sha256"] = self.packed["content_sha256"]

    def replace_derivative_file(self, index, suffix, data):
        path = f"derivative-{index}{suffix}"
        (self.directory / path).write_bytes(data)
        self.project["derivatives"][index].update(path=path, sha256=kit.digest(data))

    def inspect(self, as_of="2026-09-10"):
        return care_tool.inspect(self.output, self.care, as_of)

    def codes(self, result=None, ref=None):
        return {item["code"] for item in (result or self.inspect())["findings"] if ref is None or item["asset_ref"] == ref}

    def test_example_care_is_bound_to_reproducible_current_kit(self):
        example = json.loads((ROOT / "examples/media-kit/care.json").read_text())
        self.assertEqual(example["kit_content_sha256"], self.packed["content_sha256"])
        result = self.inspect()
        self.assertEqual(result["status"], "needs_attention")
        self.assertEqual(len(result["assets"]), 3)
        self.assertTrue(result["selection"]["needs_attention"])
        self.assertIn("owner_needed", self.codes(result))

    def test_readable_rename_preserves_identity_and_original_bytes(self):
        before = self.output.read_bytes()
        original = self.inspect()
        self.care["assets"][1]["title"] = "A clearer inspection card"
        renamed = self.inspect()
        self.assertEqual(original["kit_content_sha256"], renamed["kit_content_sha256"])
        self.assertNotEqual(original["care_sha256"], renamed["care_sha256"])
        self.assertEqual(renamed["assets"][1]["asset_ref"], "qmd_source_first_card")
        self.assertEqual(self.output.read_bytes(), before)

    def test_rebinding_to_changed_kit_is_not_automatic(self):
        self.care["kit_content_sha256"] = "0" * 64
        with self.assertRaisesRegex(kit.KitError, "different kit"):
            self.inspect()

    def test_missing_duplicate_and_unknown_inventory_entries_are_rejected(self):
        original = copy.deepcopy(self.care)
        for change in [lambda c: c["assets"].pop(), lambda c: c["assets"].append(copy.deepcopy(c["assets"][0])), lambda c: c["assets"][0].update(asset_ref="src_unknown")]:
            self.care = copy.deepcopy(original)
            change(self.care)
            with self.assertRaisesRegex(kit.KitError, "exactly once"):
                self.inspect()

    def test_original_mixed_case_hyphenated_id_contract_is_preserved(self):
        ref = "qmd_Mixed-Case"
        self.project["derivatives"][0]["metadata"]["id"] = ref
        self.project["selection"]["derivative_id"] = ref
        self.care["assets"][1]["asset_ref"] = ref
        self.rebuild()
        self.assertEqual(self.inspect()["selection"]["asset_ref"], ref)

    def test_dates_are_explicit_real_and_deterministic(self):
        for value in ["2026-02-30", "2026-9-10", "tomorrow"]:
            with self.subTest(value=value), self.assertRaises(kit.KitError):
                self.inspect(value)
        self.assertEqual(self.inspect(), self.inspect())
        self.assertNotIn("review_due", self.codes(self.inspect("2026-09-16")))
        due = self.inspect("2026-09-17")
        self.assertIn("review_due", self.codes(due))
        self.assertIn("source_needs_review", self.codes(due, "qmd_source_first_card"))
        self.care["assets"][0]["review_on"] = "2026-02-30"
        with self.assertRaisesRegex(kit.KitError, "calendar date"):
            self.inspect()

    def test_withdrawn_source_flags_dependent_selection_without_mutation(self):
        self.care["assets"][0].update(state="withdrawn", state_reason="Source owner requests review.")
        before = self.output.read_bytes()
        result = self.inspect()
        self.assertIn("source_needs_review", self.codes(result, "qmd_source_first_card"))
        self.assertTrue(result["selection"]["needs_attention"])
        self.assertEqual(self.output.read_bytes(), before)

    def test_replacement_requires_current_included_reference_and_no_cycle(self):
        original = copy.deepcopy(self.care)
        for replacement in [None, "qmd_absent", "qmd_source_first_card"]:
            self.care = copy.deepcopy(original)
            self.care["assets"][1]["state"] = "superseded"
            if replacement:
                self.care["assets"][1]["replacement_ref"] = replacement
            with self.assertRaises(kit.KitError):
                self.inspect()
        self.care = copy.deepcopy(original)
        self.care["assets"][1].update(state="superseded", replacement_ref="qmd_family_summary")
        self.care["assets"][2].update(state="superseded", replacement_ref="qmd_source_first_card")
        with self.assertRaisesRegex(kit.KitError, "cycle"):
            self.inspect()

    def test_superseded_selection_stays_selected_and_needs_attention(self):
        self.care["assets"][1].update(state="superseded", replacement_ref="qmd_family_summary")
        result = self.inspect()
        self.assertEqual(result["selection"]["asset_ref"], "qmd_source_first_card")
        self.assertTrue(result["selection"]["needs_attention"])
        self.assertIn("asset_superseded", self.codes(result))

    def test_all_authority_escalations_and_fabricated_human_judgment_are_denied(self):
        original = copy.deepcopy(self.care)
        for field in kit.AUTHORITY:
            self.care = copy.deepcopy(original)
            self.care["authority"][field] = "live" if field == "ceiling" else True
            with self.subTest(field=field), self.assertRaises(kit.KitError):
                self.inspect()
        self.care = copy.deepcopy(original)
        self.care["art_direction"]["human_judgment"] = "approved"
        with self.assertRaises(kit.KitError):
            self.inspect()

    def test_clean_declarations_do_not_grant_effects_or_authenticate_owner(self):
        self.care["maintenance_owner"] = "Declared caretaker"
        self.care["assets"][0]["origin"] = "authored"
        for item in self.project["derivatives"]:
            item["metadata"]["rights"]["source_permissions_verified"] = True
            item["metadata"]["accessibility"]["status"] = "passed"
        self.rebuild()
        result = self.inspect()
        self.assertEqual(result["status"], "prepared_for_human_review")
        self.assertEqual(result["authority"], kit.AUTHORITY)
        self.assertEqual(result["human_benefit"], "unobserved")
        self.assertEqual(result["owner_acceptance"], "unverified")
        self.assertEqual(result["art_direction"]["human_judgment"], "unobserved")

    def test_unknown_fields_and_numeric_false_are_denied(self):
        original = copy.deepcopy(self.care)
        for change in [lambda c: c.update(delete_originals=True), lambda c: c["authority"].update(publish_allowed=0)]:
            self.care = copy.deepcopy(original)
            change(self.care)
            with self.assertRaises(kit.KitError):
                self.inspect()

    def test_ambiguous_names_are_visible_without_renaming_files(self):
        self.care["assets"][1]["title"] = self.care["assets"][2]["title"].upper()
        self.assertIn("ambiguous_title", self.codes())

    def test_misclassification_cannot_hide_audio_transcript_requirement(self):
        self.replace_derivative_file(0, ".mp3", b"opaque synthetic audio fixture")
        self.rebuild()
        result = self.inspect()
        self.assertIn("family_mismatch", self.codes(result))
        self.assertIn("review_material_missing", self.codes(result, "qmd_source_first_card"))
        self.assertEqual(result["assets"][1]["origin"], "generated")

    def test_included_transcript_removes_missing_finding_but_never_proves_quality(self):
        self.replace_derivative_file(0, ".mp3", b"opaque synthetic audio fixture")
        self.care["assets"][1]["family"] = "audio"
        self.rebuild()
        before = self.inspect()
        self.care["assets"][1]["companions"] = {"transcript": "qmd_family_summary"}
        after = self.inspect()
        self.assertIn("review_material_missing", self.codes(before, "qmd_source_first_card"))
        self.assertNotIn("review_material_missing", self.codes(after, "qmd_source_first_card"))
        self.assertEqual(after["assets"][1]["companions"]["transcript"]["quality"], "unverified")
        self.assertIn("accessibility_review_open", self.codes(after, "qmd_source_first_card"))

    def test_companion_links_must_resolve_inside_kit_and_cannot_refer_to_self(self):
        for target in ["qmd_absent", "qmd_source_first_card", "https://example.com/transcript.md", "../../outside.md"]:
            self.care["assets"][1]["companions"] = {"transcript": target}
            with self.subTest(target=target), self.assertRaisesRegex(kit.KitError, "another included asset"):
                self.inspect()

    def test_blank_binary_and_wrong_format_companions_are_findings(self):
        self.care["assets"][1]["companions"] = {"captions": "qmd_family_summary"}
        for suffix, data in [(".srt", b"  \n"), (".vtt", b"\xff\x00"), (".md", b"not a supported caption format")]:
            self.replace_derivative_file(1, suffix, data)
            self.rebuild()
            with self.subTest(suffix=suffix):
                self.assertIn("companion_unusable", self.codes())

    def test_withdrawn_companion_flags_its_consumer(self):
        self.care["assets"][1]["companions"] = {"transcript": "qmd_family_summary"}
        self.care["assets"][2].update(state="withdrawn", state_reason="Transcript needs correction.")
        self.assertIn("companion_needs_review", self.codes(ref="qmd_source_first_card"))

    def test_oversized_companion_is_not_accepted_as_review_material(self):
        self.replace_derivative_file(1, ".txt", b"x" * (kit.MAX_JSON + 1))
        self.care["assets"][1]["companions"] = {"transcript": "qmd_family_summary"}
        self.rebuild()
        self.assertIn("companion_unusable", self.codes(ref="qmd_source_first_card"))

    def test_selection_follows_companion_source_care_across_multiple_sources(self):
        self.care["maintenance_owner"] = "Declared caretaker"
        self.care["assets"][0]["origin"] = "authored"
        for item in self.project["derivatives"]:
            item["metadata"]["rights"]["source_permissions_verified"] = True
            item["metadata"]["accessibility"]["status"] = "passed"
        source = copy.deepcopy(self.project["sources"][0])
        original = self.directory / source["path"]
        source.update(id="src_companion_source", path="companion-source.md", object_ref="companion.source")
        shutil.copyfile(original, self.directory / source["path"])
        self.project["sources"].append(source)
        derivative = self.project["derivatives"][1]
        derivative["source_id"] = source["id"]
        derivative["metadata"]["canonical_source"] = {key: source[key] for key in ("object_ref", "version", "receipt_ref")}
        source_care = copy.deepcopy(self.care["assets"][0])
        source_care.update(asset_ref=source["id"], title="Source for companion")
        self.care["assets"].append(source_care)
        self.care["assets"][1]["companions"] = {"transcript": "qmd_family_summary"}
        self.rebuild()
        self.assertFalse(self.inspect()["selection"]["needs_attention"])
        source_care.update(state="withdrawn", state_reason="Companion source needs correction.")
        result = self.inspect()
        self.assertTrue(result["selection"]["needs_attention"])
        self.assertIn("src_companion_source", result["selection"]["review_refs"])

    def test_image_description_is_a_declaration_not_an_art_score(self):
        self.replace_derivative_file(0, ".heic", b"opaque synthetic image fixture")
        self.care["assets"][1].update(family="image", origin="unknown", alt_text="An unverified description.")
        self.rebuild()
        result = self.inspect()
        self.assertNotIn("review_material_missing", self.codes(result, "qmd_source_first_card"))
        self.assertEqual(result["assets"][1]["origin"], "unknown")
        self.assertEqual(result["assets"][1]["alt_text_presence"], "declared")
        self.assertEqual(result["art_direction"]["human_judgment"], "unobserved")

    def test_presentation_files_are_carried_opaquely_with_viewer_review_open(self):
        for suffix in [".pptx", ".odp"]:
            payload = b"opaque synthetic presentation fixture; intentionally not decodable"
            self.replace_derivative_file(0, suffix, payload)
            self.care["assets"][1]["family"] = "presentation"
            self.rebuild()
            with self.subTest(suffix=suffix):
                self.assertIn("document_review_needed", self.codes())
                self.assertIn("review_material_missing", self.codes(ref="qmd_source_first_card"))
                self.assertEqual(kit.verify(self.output)["integrity"], "verified")
        with self.assertRaises(kit.KitError):
            kit.safe_relative("macros.pptm")

    def test_nonpublic_and_unknown_sensitivity_require_sharing_review(self):
        for value in ["internal", "confidential", "restricted", "unknown"]:
            self.care["assets"][1]["sensitivity"] = value
            with self.subTest(value=value):
                self.assertIn("sharing_review_needed", self.codes(ref="qmd_source_first_card"))

    def test_report_escapes_untrusted_labels_and_keeps_technical_claims_bounded(self):
        self.care["assets"][1]["title"] = '<img src=x onerror="alert(1)">'
        self.care["art_direction"]["intent"] = '<script>alert("bad")</script>'
        page = care_tool.render_report(self.inspect()).decode()
        self.assertNotIn("<script", page)
        self.assertNotIn("<img", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertIn("Content-Security-Policy", page)
        self.assertIn("Human judgment and benefit remain unobserved", page)

    def test_tampered_kit_is_rejected_before_care_inspection(self):
        invalid = self.directory / "invalid.zip"
        with zipfile.ZipFile(self.output) as source, zipfile.ZipFile(invalid, "w") as target:
            for name in source.namelist():
                target.writestr(name, b"changed" if name.startswith("assets/") else source.read(name))
        with self.assertRaisesRegex(kit.KitError, "Included file changed"):
            care_tool.inspect(invalid, self.care, "2026-09-10")

    def test_cli_reports_findings_without_approval_and_preserves_existing_output(self):
        record = self.directory / "care.json"
        record.write_text(json.dumps(self.care))
        page = self.directory / "review.html"
        command = [sys.executable, str(ROOT / "scripts/media_care.py"), "inspect", str(self.output), "--care", str(record), "--as-of", "2026-09-10", "--html", str(page)]
        first = subprocess.run(command, cwd=self.directory, capture_output=True, text=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(json.loads(first.stdout)["status"], "needs_attention")
        before = page.read_bytes()
        second = subprocess.run(command, cwd=self.directory, capture_output=True, text=True)
        self.assertEqual(second.returncode, 1)
        self.assertEqual(page.read_bytes(), before)

    @unittest.skipUnless(os.name == "posix", "POSIX permission behavior")
    def test_zip_and_report_are_owner_only_even_under_permissive_umask(self):
        previous = os.umask(0)
        try:
            self.rebuild()
            page = self.directory / "private.html"
            care_tool.write_new(page, care_tool.render_report(self.inspect()))
        finally:
            os.umask(previous)
        self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(page.stat().st_mode), 0o600)

    def test_legacy_zip_replays_without_rewriting_or_changing_its_fingerprint(self):
        legacy = ROOT / "examples/media-kit/legacy-v0.1.0.zip"
        before = legacy.read_bytes()
        self.assertEqual(kit.digest(before), "a564466df56a5fbfb2287c2dad07573743157cf4dabe17a90da7e09aacc8a514")
        result = kit.verify(legacy)
        self.assertEqual(result["content_sha256"], "f76d536e6f46ba3b75672c3411e49a1cb04050dc81957e1fa4f699c7c39a8e0d")
        self.care["kit_content_sha256"] = result["content_sha256"]
        self.assertEqual(care_tool.inspect(legacy, self.care, "2026-09-10")["integrity"], "verified")
        self.assertEqual(legacy.read_bytes(), before)

    def test_registry_covers_extensions_once_and_keeps_modes_separate(self):
        registry = care_tool.classification()
        self.assertEqual(registry["workspaces"][0]["name"], "Quirk Visuals")
        self.assertEqual(registry["workspaces"][0]["modes"][0]["name"], "Quick Picks")
        self.assertEqual({item["id"] for item in registry["services"] if item["status"] == "implemented_local"}, {"pack", "verify", "inspect"})


if __name__ == "__main__":
    unittest.main()
