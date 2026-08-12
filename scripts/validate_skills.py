from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker


EXPECTED_SKILLS = {
    "quirk-source-authority-resolver",
    "quirk-object-contract-engineer",
    "quirk-data-refinery",
    "quirk-semantic-label-foundry",
    "quirk-research-cartographer",
    "quirk-distillation-synthesizer",
    "quirk-evidence-instrumenter",
    "quirk-control-loop-designer",
    "quirk-probabilistic-forecaster",
    "quirk-roadmap-board-orchestrator",
    "quirk-value-foundry",
}
# Draft skills evaluated by other candidate packs. They may live under skills/
# with SKILL.md only, but they are not part of the Skills v0.2 registry set and
# must not receive runtime admission through this validator.
DRAFT_CANDIDATE_SKILLS = {
    "quirk-deck-compiler",
}
REQUIRED_KINDS = {"positive", "adversarial", "regression", "authority"}
PLACEHOLDER_MARKERS = ("TO" + "DO", "FIX" + "ME", "T" + "BD", "X" + "XX")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def parse_frontmatter(text: str, path: Path) -> dict[str, Any]:
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: missing YAML frontmatter")
    pieces = text.split("---", 2)
    if len(pieces) != 3:
        raise ValueError(f"{path}: malformed YAML frontmatter")
    data = yaml.safe_load(pieces[1])
    if not isinstance(data, dict):
        raise ValueError(f"{path}: frontmatter must be an object")
    return data


def schema_errors(schema: dict[str, Any], instance: Any) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path))
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Quirk Skills v0.2 candidate pack.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--output", help="Write a JSON conformance report.")
    args = parser.parse_args()

    root = Path(args.repo).resolve()
    sys.path.insert(0, str(root / "scripts"))
    from sync_control_plane.skill_runtime import (  # pylint: disable=import-outside-toplevel
        evaluate_skill_case,
        manifest_digest,
        validate_manifest_integrity,
    )

    findings: list[dict[str, str]] = []

    def fail(code: str, message: str) -> None:
        findings.append({"level": "error", "code": code, "message": message})

    schema_names = [
        "skill-package.schema.json",
        "skill-eval-case.schema.json",
        "skill-runtime-grant.schema.json",
        "skill-run-receipt.schema.json",
    ]
    schemas: dict[str, dict[str, Any]] = {}
    for name in schema_names:
        path = root / "schemas" / name
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            schemas[name] = schema
        except Exception as exc:
            fail("SCHEMA_INVALID", f"{path.relative_to(root)}: {exc}")

    skill_dirs = {path.parent.name for path in (root / "skills").glob("*/SKILL.md")}
    draft_dirs = skill_dirs & DRAFT_CANDIDATE_SKILLS
    manifested_dirs = skill_dirs - DRAFT_CANDIDATE_SKILLS
    if manifested_dirs != EXPECTED_SKILLS:
        fail(
            "SKILL_SET_DRIFT",
            f"expected {sorted(EXPECTED_SKILLS)}, found {sorted(manifested_dirs)}",
        )
    unexpected_drafts = draft_dirs - DRAFT_CANDIDATE_SKILLS
    if unexpected_drafts:
        fail(
            "SKILL_SET_DRIFT",
            f"unknown draft candidate skills: {sorted(unexpected_drafts)}",
        )
    for skill_id in sorted(draft_dirs):
        source_path = root / "skills" / skill_id / "SKILL.md"
        source_text = source_path.read_text(encoding="utf-8")
        try:
            frontmatter = parse_frontmatter(source_text, source_path.relative_to(root))
        except ValueError as exc:
            fail("DRAFT_SKILL_INVALID", str(exc))
            continue
        if frontmatter.get("name") != skill_id:
            fail(
                "DRAFT_SKILL_NAME_MISMATCH",
                f"{source_path.relative_to(root)}: frontmatter name must equal directory",
            )
        if "Status: `candidate`" not in source_text and "status: candidate" not in source_text.lower():
            fail(
                "DRAFT_SKILL_STATUS",
                f"{source_path.relative_to(root)}: draft skills must remain candidate",
            )
        if (root / "skills" / skill_id / "manifest.json").exists():
            fail(
                "DRAFT_SKILL_MANIFEST_PRESENT",
                f"{skill_id}: draft candidate skills must not join the v0.2 manifest registry until separately admitted",
            )

    manifests: dict[str, dict[str, Any]] = {}
    for skill_id in sorted(EXPECTED_SKILLS):
        skill_dir = root / "skills" / skill_id
        source_path = skill_dir / "SKILL.md"
        manifest_path = skill_dir / "manifest.json"
        if not source_path.exists():
            fail("SKILL_SOURCE_MISSING", str(source_path.relative_to(root)))
            continue
        if not manifest_path.exists():
            fail("SKILL_MANIFEST_MISSING", str(manifest_path.relative_to(root)))
            continue

        source_text = source_path.read_text(encoding="utf-8")
        if not source_text.endswith("\n"):
            fail("SOURCE_NEWLINE_MISSING", str(source_path.relative_to(root)))

        try:
            frontmatter = parse_frontmatter(source_text, source_path.relative_to(root))
        except ValueError as exc:
            fail("FRONTMATTER_INVALID", str(exc))
            continue

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            fail("MANIFEST_JSON_INVALID", f"{manifest_path.relative_to(root)}: {exc}")
            continue

        for message in schema_errors(schemas.get("skill-package.schema.json", {}), manifest):
            fail("MANIFEST_SCHEMA", f"{manifest_path.relative_to(root)}: {message}")

        expected_frontmatter = {
            "name": skill_id,
            "version": manifest.get("version"),
            "status": manifest.get("status"),
            "family": manifest.get("family"),
            "authority_ceiling": manifest.get("authority", {}).get("ceiling"),
            "manifest": "manifest.json",
            "eval_suite": "../../evals/skills/conformance.json",
        }
        for key, expected in expected_frontmatter.items():
            if frontmatter.get(key) != expected:
                fail(
                    "FRONTMATTER_DRIFT",
                    f"{source_path.relative_to(root)}: {key}={frontmatter.get(key)!r}, expected {expected!r}",
                )

        if manifest.get("id") != skill_id:
            fail("MANIFEST_ID_DRIFT", f"{manifest_path.relative_to(root)} id mismatch")
        if manifest.get("status") != "candidate":
            fail("CANDIDATE_CEILING_BREACH", f"{manifest_path.relative_to(root)} must remain candidate")
        if set(manifest.get("quality", {}).get("required_case_kinds", [])) != REQUIRED_KINDS:
            fail("EVAL_KIND_CONTRACT", f"{manifest_path.relative_to(root)} must require all four eval classes")
        if manifest.get("quality", {}).get("minimum_score") != 1.0:
            fail("EVAL_THRESHOLD_WEAKENED", f"{manifest_path.relative_to(root)} minimum score must be 1.0")

        for error in validate_manifest_integrity(manifest, source_text):
            fail("INTEGRITY_FAILURE", f"{manifest_path.relative_to(root)}: {error}")

        if manifest_digest(manifest) != manifest.get("integrity", {}).get("manifest_sha256"):
            fail("MANIFEST_DIGEST_FAILURE", str(manifest_path.relative_to(root)))

        manifests[skill_id] = manifest

    eval_path = root / "evals" / "skills" / "conformance.json"
    try:
        cases = json.loads(eval_path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail("EVAL_JSON_INVALID", f"{eval_path.relative_to(root)}: {exc}")
        cases = []

    if not isinstance(cases, list):
        fail("EVAL_SUITE_INVALID", "conformance suite must be an array")
        cases = []

    case_ids: set[str] = set()
    case_kinds: dict[str, set[str]] = defaultdict(set)
    kind_counts: Counter[str] = Counter()
    passed_cases = 0

    for index, case in enumerate(cases, start=1):
        for message in schema_errors(schemas.get("skill-eval-case.schema.json", {}), case):
            fail("EVAL_SCHEMA", f"case {index}: {message}")
        case_id = case.get("id")
        if case_id in case_ids:
            fail("EVAL_DUPLICATE_ID", str(case_id))
        case_ids.add(case_id)

        expected_id = f"QSK-{index:03d}"
        if case_id != expected_id:
            fail("EVAL_SEQUENCE_DRIFT", f"case {index}: expected {expected_id}, found {case_id}")

        skill_id = case.get("skill_id")
        kind = case.get("kind")
        case_kinds[skill_id].add(kind)
        kind_counts[kind] += 1

        manifest = manifests.get(skill_id)
        if manifest and case.get("skill_version") != manifest.get("version"):
            fail("EVAL_VERSION_DRIFT", f"{case_id}: version does not match manifest")

        try:
            actual = evaluate_skill_case(case)
        except Exception as exc:
            fail("EVAL_EXECUTION", f"{case_id}: {exc}")
            continue

        expected = case.get("expected", {})
        for key in ("result", "action", "blocked"):
            if actual.get(key) != expected.get(key):
                fail(
                    "EVAL_EXPECTATION",
                    f"{case_id}: {key}={actual.get(key)!r}, expected {expected.get(key)!r}",
                )
        actual_codes = set(actual.get("finding_codes", []))
        required_codes = set(expected.get("required_codes", []))
        prohibited_codes = set(expected.get("prohibited_codes", []))
        missing = sorted(required_codes - actual_codes)
        forbidden = sorted(prohibited_codes & actual_codes)
        if missing:
            fail("EVAL_MISSING_CODE", f"{case_id}: {missing}")
        if forbidden:
            fail("EVAL_PROHIBITED_CODE", f"{case_id}: {forbidden}")
        if not missing and not forbidden and all(
            actual.get(key) == expected.get(key) for key in ("result", "action", "blocked")
        ):
            passed_cases += 1

        if kind == "authority" and (
            actual.get("result") not in {"stop", "abstain"} or not actual.get("blocked")
        ):
            fail("AUTHORITY_FAIL_OPEN", f"{case_id}: authority attack did not fail closed")

    if len(cases) != 44:
        fail("EVAL_COUNT", f"expected 44 cases, found {len(cases)}")
    for skill_id in sorted(EXPECTED_SKILLS):
        if case_kinds.get(skill_id) != REQUIRED_KINDS:
            fail(
                "EVAL_SKILL_COVERAGE",
                f"{skill_id}: expected {sorted(REQUIRED_KINDS)}, found {sorted(case_kinds.get(skill_id, set()))}",
            )
    if set(kind_counts) != REQUIRED_KINDS or any(kind_counts[kind] != 11 for kind in REQUIRED_KINDS):
        fail("EVAL_CLASS_BALANCE", f"kind counts: {dict(kind_counts)}")

    authority_path = root / "evals" / "skills" / "authority-boundary.json"
    try:
        authority_cases = json.loads(authority_path.read_text(encoding="utf-8"))
        expected_authority = [case for case in cases if case.get("kind") == "authority"]
        if authority_cases != expected_authority:
            fail("AUTHORITY_SUBSET_DRIFT", "authority-boundary.json must equal the authority subset of conformance.json")
    except Exception as exc:
        fail("AUTHORITY_SUBSET_INVALID", str(exc))

    registry_path = root / "skills" / "registry.json"
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        if registry.get("status") != "candidate":
            fail("REGISTRY_AUTHORITY_BREACH", "registry must remain candidate")
        entries = registry.get("skills", [])
        by_id = {entry.get("id"): entry for entry in entries}
        if set(by_id) != EXPECTED_SKILLS or len(entries) != 11:
            fail("REGISTRY_SKILL_DRIFT", "registry must contain exactly the expected 11 skills")
        for skill_id, manifest in manifests.items():
            entry = by_id.get(skill_id, {})
            checks = {
                "version": manifest["version"],
                "status": manifest["status"],
                "family": manifest["family"],
                "authority_ceiling": manifest["authority"]["ceiling"],
                "source_blob_sha": manifest["integrity"]["source_blob_sha"],
                "manifest_sha256": manifest["integrity"]["manifest_sha256"],
            }
            for key, expected in checks.items():
                if entry.get(key) != expected:
                    fail("REGISTRY_MANIFEST_DRIFT", f"{skill_id}: registry {key} mismatch")
        digest_source = {key: value for key, value in registry.items() if key != "registry_sha256"}
        import hashlib
        digest = hashlib.sha256(canonical_json_bytes(digest_source)).hexdigest()
        if registry.get("registry_sha256") != digest:
            fail("REGISTRY_DIGEST_FAILURE", "registry sha256 mismatch")
    except Exception as exc:
        fail("REGISTRY_INVALID", f"{registry_path.relative_to(root)}: {exc}")

    bounded_paths = [root / "skills", root / "evals" / "skills"]
    bounded_files = [
        *[path for base in bounded_paths for path in base.rglob("*") if path.is_file()],
        root / "mappings" / "skill-package.v1.yaml",
    ]
    for path in bounded_files:
        if path.name == "conformance-results.json":
            continue
        text = path.read_text(encoding="utf-8")
        for marker in PLACEHOLDER_MARKERS:
            if marker in text:
                fail("PLACEHOLDER_DEBT", f"{path.relative_to(root)} contains {marker}")

    report = {
        "api_version": "quirk.dev/skill-conformance/v1alpha1",
        "kind": "SkillConformanceReport",
        "status": "pass" if not findings else "fail",
        "evaluated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "skill_count": len(manifests),
        "case_count": len(cases),
        "passed_case_count": passed_cases,
        "case_kind_counts": dict(sorted(kind_counts.items())),
        "manifest_digests": {
            skill_id: manifest["integrity"]["manifest_sha256"]
            for skill_id, manifest in sorted(manifests.items())
        },
        "findings": findings,
        "authority": {
            "admits_skills": False,
            "activates_skills": False,
            "promotes_canon": False,
            "meaning": "candidate-local conformance evidence only",
        },
    }

    if args.output:
        output = root / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if findings:
        for finding in findings:
            print(f"{finding['level'].upper()} {finding['code']}: {finding['message']}", file=sys.stderr)
        print(
            f"skill conformance failed: {len(findings)} finding(s), "
            f"{len(manifests)}/11 manifests, {passed_cases}/{len(cases)} cases",
            file=sys.stderr,
        )
        return 1

    print(
        "validated 11 candidate skills, 11 immutable manifests, 4 schemas, "
        "44 executable cases, registry integrity, and fail-closed runtime boundaries"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
