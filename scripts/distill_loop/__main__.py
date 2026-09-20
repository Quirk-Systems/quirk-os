"""Command line entry for the distill loop.

    PYTHONPATH=scripts python -m distill_loop distill --receipt R --trace T [--repo .] [--root DIR] [--out DIR] [--write]
    PYTHONPATH=scripts python -m distill_loop promote --receipt P --eval-suite E [--repo .] [--root DIR] [--out DIR] [--write]
    PYTHONPATH=scripts python -m distill_loop attest --receipt P
    PYTHONPATH=scripts python -m distill_loop context [--root DIR]

`--repo` is where schemas and source skills are read from; `--root` is the tree
that holds the distill ledger and distilled candidates (defaults to the repo).

`distill` and `promote` write files only with `--write`; by default they print
what they would write. Nothing here admits or activates a skill.
"""

from __future__ import annotations

import argparse
import contextlib
import errno
import json
import sys
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX hosts
    fcntl = None
try:
    import msvcrt
except ImportError:  # pragma: no cover - POSIX hosts
    msvcrt = None


class LockUnavailable(RuntimeError):
    """No reliable interprocess lock exists on this host; guarded writes fail closed."""

from .common import LEDGER_PATH, load_schemas, write_files
from .context import next_run_context
from .ledger import new_ledger
from .promotion import apply_promotion, attest_promotion
from .trigger import post_run_distill


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _ledger(root: Path):
    path = root / LEDGER_PATH
    return _load(path) if path.exists() else new_ledger()


LOCK_NAME = "distill-ledger.lock"
WINDOWS_LOCK_ATTEMPTS = 6
CONTENTION_ERRNOS = frozenset(
    code for code in (getattr(errno, "EDEADLOCK", None), getattr(errno, "EDEADLK", None)) if code
)


def _lock_handle(handle) -> None:
    if fcntl is not None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        return
    if msvcrt is not None:
        handle.seek(0)
        for _ in range(WINDOWS_LOCK_ATTEMPTS):
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
                return
            except OSError as exc:
                if exc.errno not in CONTENTION_ERRNOS:
                    raise LockUnavailable(f"lock primitive failed: {exc}") from exc
        raise LockUnavailable(f"lock still contended after {WINDOWS_LOCK_ATTEMPTS} attempts")
    raise LockUnavailable("no interprocess lock primitive available on this host")


def _unlock_handle(handle) -> None:
    if fcntl is not None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    elif msvcrt is not None:
        handle.seek(0)
        with contextlib.suppress(OSError):
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


@contextlib.contextmanager
def _ledger_lock(root: Path):
    lock_path = root / "skills" / LOCK_NAME
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(lock_path, "a+", encoding="utf-8")
    try:
        _lock_handle(handle)
        yield
    finally:
        _unlock_handle(handle)
        handle.close()


def _write_guarded(root: Path, files: dict[str, str]) -> int:
    try:
        with _ledger_lock(root):
            write_files(root, files)
    except LockUnavailable as exc:
        print(
            json.dumps(
                {
                    "error": "LOCK_UNAVAILABLE",
                    "detail": f"{exc}; refusing to write without an interprocess lock",
                }
            ),
            file=sys.stderr,
        )
        return 1
    return 0


REPO_DEFAULT = Path(__file__).resolve().parents[2]


def _add_roots(command) -> None:
    command.add_argument("--repo", type=Path, default=REPO_DEFAULT,
                         help="repository holding schemas/ and the source skills/ (default: this checkout)")
    command.add_argument("--root", type=Path, default=None,
                         help="tree holding the distill ledger and distilled candidates (default: --repo)")
    command.add_argument("--out", type=Path, default=None,
                         help="write under this root instead of --root")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="distill_loop")
    sub = parser.add_subparsers(dest="command", required=True)

    distill = sub.add_parser("distill", help="run the post-run distill trigger")
    distill.add_argument("--receipt", type=Path, required=True)
    distill.add_argument("--trace", type=Path, required=True)
    _add_roots(distill)
    distill.add_argument("--write", action="store_true")

    promote = sub.add_parser("promote", help="apply a distill promotion receipt")
    promote.add_argument("--receipt", type=Path, required=True)
    promote.add_argument("--eval-suite", type=Path, required=True)
    _add_roots(promote)
    promote.add_argument("--write", action="store_true")

    attest = sub.add_parser("attest", help="compute the attestation digest for a promotion receipt body")
    attest.add_argument("--receipt", type=Path, required=True)

    context = sub.add_parser("context", help="print the next-run context")
    _add_roots(context)

    args = parser.parse_args(argv)
    repo = getattr(args, "repo", REPO_DEFAULT).resolve()
    root = (getattr(args, "root", None) or repo).resolve()
    out = (getattr(args, "out", None) or root).resolve()

    if args.command == "attest":
        print(json.dumps(attest_promotion(_load(args.receipt)), indent=2))
        return 0

    if args.command == "context":
        print(json.dumps(next_run_context(_ledger(root), root=root), indent=2))
        return 0

    schemas = load_schemas(repo)
    if args.command == "distill":
        receipt = _load(args.receipt)
        trace = _load(args.trace)
        skill_dir = repo / "skills" / str(receipt.get("skill_id"))
        result = post_run_distill(
            receipt=receipt,
            trace=trace,
            source_manifest=_load(skill_dir / "manifest.json"),
            source_text=(skill_dir / "SKILL.md").read_text(encoding="utf-8"),
            ledger=_ledger(root),
            schemas=schemas,
        )
        summary = {key: result[key] for key in ("outcome", "finding_codes", "candidate")}
        summary["files"] = sorted(result["files"])
        print(json.dumps(summary, indent=2))
        if args.write:
            return _write_guarded(out, result["files"])
        return 0

    receipt = _load(args.receipt)
    candidate_dir = root / "skills" / receipt["candidate_id"]
    if not candidate_dir.exists():
        print(f"candidate package not found: {candidate_dir}", file=sys.stderr)
        return 1
    result = apply_promotion(
        receipt,
        candidate_manifest=_load(candidate_dir / "manifest.json"),
        candidate_source=(candidate_dir / "SKILL.md").read_text(encoding="utf-8"),
        eval_suite=_load(args.eval_suite),
        ledger=_ledger(root),
        schemas=schemas,
    )
    print(json.dumps({"outcome": result["outcome"], "errors": result["errors"], "files": sorted(result["files"])}, indent=2))
    if result["errors"]:
        return 1
    if args.write:
        return _write_guarded(out, result["files"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
