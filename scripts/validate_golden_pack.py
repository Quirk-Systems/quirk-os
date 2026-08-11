#!/usr/bin/env python3
"""Fail-closed structural checks for the Quirk Core Golden Project Pack."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "docs/golden-project-pack/README.md",
    "docs/golden-project-pack/ARCHITECTURE.md",
    "docs/golden-project-pack/CURRENT-RESEARCH.md",
    "docs/golden-project-pack/TOP-MINDS.md",
    "docs/golden-project-pack/MULTIMEDIA-MULTIPLIZIERT.md",
    "prompts/QUIRK-GOLDEN-PROMPTS.md",
    "schemas/ledger-transition.schema.json",
    "schemas/proposed-move.schema.json",
    "schemas/research-claim.schema.json",
    "schemas/media-derivative.schema.json",
]

CORE_LAWS = [
    "Every consequential mutation owes a receipt.",
    "History is not authority.",
    "Storage is not consent.",
    "Comments are not commands.",
    "No Zombie Truth.",
    "Every decision eventually owes an outcome.",
]

PROMPT_IDS = [
    "prompt.golden_project_pack_compiler",
    "prompt.accountable_transition_designer",
    "prompt.ledger_fuckery_detector",
    "prompt.eval_suite_foundry",
    "prompt.golden_gate_architect",
    "prompt.capability_and_agent_skill_forge",
    "prompt.proposed_move_queue_operator",
    "prompt.current_research_currentizer",
    "prompt.top_minds_council",
    "prompt.multimedia_multipliziert",
    "prompt.ship_it_without_bryan_tribunal",
]

FORBIDDEN_PLACEHOLDERS = ("TODO", "FIXME", "[INSERT", "LOREM IPSUM")


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)


def main() -> int:
    errors = 0

    for relative in REQUIRED_FILES:
        path = ROOT / relative
        if not path.is_file():
            fail(f"missing required file: {relative}")
            errors += 1

    for path in sorted((ROOT / "schemas").glob("*.schema.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
            errors += 1
            continue

        for key in ("$schema", "$id", "title", "type"):
            if key not in value:
                fail(f"{path.relative_to(ROOT)} missing {key}")
                errors += 1

    pack_path = ROOT / "docs/golden-project-pack/README.md"
    if pack_path.is_file():
        pack = pack_path.read_text(encoding="utf-8")
        for law in CORE_LAWS:
            if law not in pack:
                fail(f"core law missing from pack: {law}")
                errors += 1

    prompt_path = ROOT / "prompts/QUIRK-GOLDEN-PROMPTS.md"
    if prompt_path.is_file():
        prompt_text = prompt_path.read_text(encoding="utf-8")
        for prompt_id in PROMPT_IDS:
            if prompt_id not in prompt_text:
                fail(f"Golden Prompt missing: {prompt_id}")
                errors += 1

    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() not in {".md", ".json", ".yaml", ".yml", ".py"}:
            continue
        if path.resolve() == Path(__file__).resolve():
            continue
        text = path.read_text(encoding="utf-8", errors="replace").upper()
        for placeholder in FORBIDDEN_PLACEHOLDERS:
            if placeholder in text:
                fail(f"unresolved placeholder {placeholder!r} in {path.relative_to(ROOT)}")
                errors += 1

    if errors:
        print(f"Golden gates failed with {errors} error(s).", file=sys.stderr)
        return 1

    print("Golden structural gates passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
