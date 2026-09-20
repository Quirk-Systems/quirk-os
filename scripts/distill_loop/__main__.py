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


def _lock_handle(handle) -> None:
    """Take an exclusive, blocking interprocess lock or raise LockUnavailable.

    POSIX uses flock. Windows uses msvcrt.locking, which blocks in ten one-second
    attempts per call, so it is retried until it succeeds. Any other host has no
    reliable primitive and must not write at all: an unlocked check-then-write is
    exactly the lost-update the guard exists to prevent.
    """
    if fcntl is not None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        return
    if msvcrt is not None:  # pragma: no cover - exercised on Windows only
        handle.seek(0)
        while True:
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
                return
            except OSError:
                continue
    raise LockUnavailable("no interprocess lock primitive available on this host")


def _unlock_handle(handle) -> None:
    if fcntl is not None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    elif msvcrt is not None:  # pragma: no cover - exercised on Windows only
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


@contextlib.contextmanager
def _ledger_lock(*roots: Path):
    """Hold an exclusive interprocess lock on every tree we will check or write.

    The lock makes check-then-write one step: a second writer that computed its
    result against the same input ledger blocks here, then re-reads a ledger
    that has moved and is refused instead of silently replacing the first write.
    Raises LockUnavailable before touching anything when no lock exists.
    """
    handles = []
    try:
        for root in sorted({r.resolve() for r in roots}):
            lock_path = root / "skills" / LOCK_NAME
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            handle = open(lock_path, "a+", encoding="utf-8")
            try:
                _lock_handle(handle)
            except LockUnavailable:
                handle.close()
                raise
            handles.append(handle)
        yield
    finally:
        for handle in reversed(handles):
            _unlock_handle(handle)
            handle.close()


def _ledger_digest_on_disk(root: Path) -> str:
    path = root / LEDGER_PATH
    return _load(path)["ledger_sha256"] if path.exists() else new_ledger()["ledger_sha256"]


def _write_guarded(root: Path, result: dict, out: Path | None = None) -> int:
    """Compare-and-swap the ledger under lock.

    `root` is the tree whose ledger this operation read; `out` is where it writes
    (default: `root`). Under the lock, the source ledger must still carry the digest
    the operation read. When writing elsewhere, the output tree must either be
    empty (it is initialized from the input ledger) or already carry that same
    digest; anything else is a fork and is refused.
    """
    out = out or root
    expected = result.get("ledger_input_sha256")
    try:
        lock = _ledger_lock(root, out)
        lock.__enter__()
    except LockUnavailable as exc:
        print(json.dumps({"error": "LOCK_UNAVAILABLE", "detail": f"{exc}; refusing to write without an interprocess lock"}), file=sys.stderr)
        return 1
    with contextlib.ExitStack() as stack:
        stack.push(lock)
        if _ledger_digest_on_disk(root) != expected:
            print(json.dumps({"error": "LEDGER_FORKED", "detail": "source ledger changed since this operation read it; re-run against the current ledger"}), file=sys.stderr)
            return 1
        if out.resolve() != root.resolve() and (out / LEDGER_PATH).exists() and _ledger_digest_on_disk(out) != expected:
            print(json.dumps({"error": "LEDGER_FORKED", "detail": "output tree already holds a different ledger; refusing to replace it"}), file=sys.stderr)
            return 1
        write_files(out, result["files"])
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
    registry = _load(repo / "skills" / "registry.json")
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
            registry=registry,
        )
        summary = {key: result[key] for key in ("outcome", "finding_codes", "candidate")}
        summary["files"] = sorted(result["files"])
        print(json.dumps(summary, indent=2))
        if args.write:
            return _write_guarded(root, result, out)
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
        return _write_guarded(root, result, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
