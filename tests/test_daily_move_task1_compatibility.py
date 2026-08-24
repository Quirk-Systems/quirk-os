from __future__ import annotations

import ast
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.validate_daily_move_fixtures import _implementation_markers

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATHS = {
    ".github/workflows/daily-move-io-conformance.yml",
    "docs/superpowers/plans/2026-08-21-quirk-daily-move-io.md",
    "docs/superpowers/specs/2026-08-21-quirk-daily-move-io-design.md",
    "evals/daily-move/io-cases/invalid-cases.json",
    "evals/daily-move/io-cases/valid-input.json",
    "evals/daily-move/io-cases/valid-output.json",
    "schemas/daily-move-input.schema.json",
    "schemas/daily-move-output.schema.json",
    "scripts/validate_daily_move_io.py",
    "tests/test_daily_move_io.py",
    "tests/test_daily_move_io_workflow.py",
    "tests/test_daily_move_task1_compatibility.py",
}


class DailyMoveTask1CompatibilityTests(unittest.TestCase):
    def test_exact_contract_surfaces_do_not_trigger_runtime_markers(self) -> None:
        markers = set(_implementation_markers(ROOT))
        self.assertTrue(CONTRACT_PATHS.isdisjoint(markers), sorted(CONTRACT_PATHS & markers))

    def test_nearby_alias_and_real_runtime_namespace_still_trigger(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            alias = root / "schemas/daily-move-io.schema.json"
            runtime = root / "scripts/daily_move/policy.py"
            alias.parent.mkdir(parents=True)
            runtime.parent.mkdir(parents=True)
            alias.write_text('{"title":"Daily Move IO"}\n', encoding="utf-8")
            runtime.write_text("def evaluate_daily_move_case(scenario, adapters):\n    return {}\n", encoding="utf-8")
            markers = set(_implementation_markers(root))
            self.assertIn("schemas/daily-move-io.schema.json", markers)
            self.assertIn("scripts/daily_move/policy.py", markers)

    def test_exact_untracked_contract_bytecode_is_ignored_but_alias_bytecode_is_not(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            exact_paths = (
                root / "scripts/__pycache__/validate_daily_move_io.cpython-313.pyc",
                root / "tests/__pycache__/test_daily_move_io.cpython-313.pyc",
                root / "tests/__pycache__/test_daily_move_io_workflow.cpython-313.pyc",
                root / "tests/__pycache__/test_daily_move_task1_compatibility.cpython-313.pyc",
            )
            for path in exact_paths:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"daily move contract bytecode")
            alias = root / "tests/__pycache__/test_daily_move_generator.cpython-313.pyc"
            alias.write_bytes(b"daily move runtime bytecode")
            markers = set(_implementation_markers(root))
            self.assertTrue({path.relative_to(root).as_posix() for path in exact_paths}.isdisjoint(markers))
            self.assertIn(alias.relative_to(root).as_posix(), markers)

    def test_contract_validator_has_no_runtime_or_external_effect_surface(self) -> None:
        path = ROOT / "scripts/validate_daily_move_io.py"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports = {
            name
            for node in ast.walk(tree)
            for name in (
                [alias.name.split(".", 1)[0] for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module.split(".", 1)[0]]
                if isinstance(node, ast.ImportFrom) and node.module
                else []
            )
        }
        allowed = {"__future__", "argparse", "copy", "datetime", "hashlib", "json", "jsonschema", "pathlib", "typing", "zoneinfo"}
        self.assertEqual(set(), imports - allowed)
        functions = {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.assertTrue({"evaluate_daily_move_case", "generate_daily_move", "execute_daily_move", "publish_daily_move"}.isdisjoint(functions))


if __name__ == "__main__":
    unittest.main()
