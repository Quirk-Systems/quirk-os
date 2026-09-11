"""Command line interface for candidate-only harvest operations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .core import ContractError, compare_surfaces, compile_prompt_candidate, fingerprint_surface
from .scanner import ScanLimits, scan_plugin_root


def _load(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="plugin-capability-harvest")
    commands = parser.add_subparsers(dest="command", required=True)
    scan = commands.add_parser("scan", help="scan an explicit root without executing plugin code")
    scan.add_argument("root")
    scan.add_argument("--max-files", type=int, default=500)
    scan.add_argument("--max-bytes-per-file", type=int, default=1_000_000)
    scan.add_argument("--max-total-bytes", type=int, default=20_000_000)
    diff = commands.add_parser("diff", help="compare fingerprint arrays")
    diff.add_argument("baseline")
    diff.add_argument("current")
    diff.add_argument("--observed-at", required=True)
    prompt = commands.add_parser("prompt", help="compile a candidate prompt from owned context")
    prompt.add_argument("packet")
    fingerprint = commands.add_parser("fingerprint", help="fingerprint separately supplied catalog, registry, app, MCP, documentation, or runtime surfaces")
    fingerprint.add_argument("surfaces")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "scan":
            result = scan_plugin_root(args.root, ScanLimits(args.max_files, args.max_bytes_per_file, args.max_total_bytes))
        elif args.command == "diff":
            result = compare_surfaces(_load(args.baseline), _load(args.current), args.observed_at)
        elif args.command == "prompt":
            result = compile_prompt_candidate(_load(args.packet))
        else:
            supplied = _load(args.surfaces)
            if not isinstance(supplied, list):
                raise ContractError("surfaces input must be a list")
            result = [fingerprint_surface(item) for item in supplied]
        print(json.dumps(result, indent=2, sort_keys=True))
        if result.get("status") == "BASELINE_UNAVAILABLE":
            return 4
        return 0
    except (ContractError, OSError, json.JSONDecodeError, ValueError) as exc:
        print(str(exc), file=__import__("sys").stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
