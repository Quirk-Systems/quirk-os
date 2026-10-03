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
# msvcrt.locking(LK_LOCK) blocks for up to ten one-second attempts per call and reports
# contention as EDEADLOCK. Retrying that a bounded number of times is a wait; retrying
# anything else, or forever, would be a spin that never fails closed.
WINDOWS_LOCK_ATTEMPTS = 6
CONTENTION_ERRNOS = frozenset(code for code in (getattr(errno, "EDEADLOCK", None), getattr(errno, "EDEADLK", None)) if code)


def _lock_handle(handle) -> None:
    """Take an exclusive, blocking interprocess lock or raise LockUnavailable.

    POSIX uses flock. Windows uses msvcrt.locking, retried only on confirmed
    contention and only a bounded number of times. Any other host has no reliable
    primitive and must not write at all: an unlocked check-then-write is exactly
    the lost-update the guard exists to prevent.
    """
    if fcntl is not None:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        except OSError as exc:
            raise LockUnavailable(f"lock primitive failed: {exc}") from exc
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
        with contextlib.suppress(OSError):
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    elif msvcrt is not None:
        handle.seek(0)
        with contextlib.suppress(OSError):
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
        # Never create the lock through a planted link: the tree, its skills directory,
        # and the lock file must be real entries as given, before any resolution, so
        # nothing this command writes can be redirected outside the tree it was pointed at.
        for given in roots:
            if given.is_symlink() or (given / "skills").is_symlink() or (given / "skills" / LOCK_NAME).is_symlink():
                raise LockUnavailable(f"{given} or its lock path is a symlink; refusing to lock or write through it")
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


def _out_tree_problems(out: Path) -> list[str]:
    """Entries a redirected --out may hold before initialization: nothing, or the lock we made.

    Every pre-existing entry is inspected without following links. A directory symlink
    (for example `skills -> elsewhere`) counts as content even when its target is empty,
    because writing through it would land files outside the selected tree.
    """
    if out.is_symlink():
        return ["output tree itself is a symlink"]
    if not out.exists():
        return []
    skills = out / "skills"
    lock = skills / LOCK_NAME
    problems: list[str] = []
    for entry in out.iterdir():
        if entry != skills:
            problems.append(f"pre-existing entry {entry.name}")
            continue
        if entry.is_symlink() or not entry.is_dir():
            problems.append("skills entry is not a real directory")
            continue
        for inner in entry.iterdir():
            if inner != lock or inner.is_symlink() or not inner.is_file():
                problems.append(f"pre-existing entry skills/{inner.name}")
    return problems


def _destination_problems(out: Path, relative_paths) -> list[str]:
    """Refuse any destination whose existing components include a link or a non-directory.

    Checked without following links, one component at a time, for every file about
    to be written. This holds whether or not the output tree already carries a
    ledger: a matching ledger says nothing about links planted deeper in the tree.
    """
    problems: list[str] = []
    for relative in sorted(relative_paths):
        current = out
        parts = Path(relative).parts
        for index, part in enumerate(parts):
            current = current / part
            is_last = index == len(parts) - 1
            if current.is_symlink():
                problems.append(f"{relative}: component {part!r} is a symlink")
                break
            if not current.exists():
                break
            if not is_last and not current.is_dir():
                problems.append(f"{relative}: component {part!r} is not a directory")
                break
            if is_last and not current.is_file():
                problems.append(f"{relative}: destination exists and is not a regular file")
                break
    return problems


def _write_guarded(root: Path, result: dict, out: Path | None = None) -> int:
    """Compare-and-swap the ledger under lock.

    `root` is the tree whose ledger this operation read; `out` is where it writes
    (default: `root`). Under the lock, the source ledger must still carry the digest
    the operation read. When writing elsewhere, the output tree must either be
    truly empty (it is initialized from the input ledger) or already carry that same
    digest; a tree with other files and no ledger, or a different ledger, is refused.
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
        if out.resolve() != root.resolve():
            out_ledger = out / LEDGER_PATH
            if out_ledger.is_symlink():
                print(json.dumps({"error": "LEDGER_FORKED", "detail": "output ledger is a symlink; refusing to write through it"}), file=sys.stderr)
                return 1
            if out_ledger.exists():
                if _ledger_digest_on_disk(out) != expected:
                    print(json.dumps({"error": "LEDGER_FORKED", "detail": "output tree already holds a different ledger; refusing to replace it"}), file=sys.stderr)
                    return 1
            else:
                problems = _out_tree_problems(out)
                if problems:
                    print(json.dumps({"error": "LEDGER_FORKED", "detail": "output tree is not empty and holds no ledger; refusing to write into it", "entries": problems}), file=sys.stderr)
                    return 1
        unsafe = _destination_problems(out, result["files"])
        if unsafe:
            print(json.dumps({"error": "LEDGER_FORKED", "detail": "a destination path passes through a symlink or non-directory; refusing to write", "paths": unsafe}), file=sys.stderr)
            return 1
        try:
            write_files(out, result["files"])
        except OSError as exc:
            # write_files creates temps exclusively and writes the ledger last, so a
            # failure here leaves the ledger untouched; report it and fail closed.
            print(json.dumps({"error": "WRITE_FAILED", "detail": str(exc)}), file=sys.stderr)
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
    # Paths are made absolute but deliberately NOT resolved here: the write guard must
    # see a symlinked --root or --out as given so it can refuse it before anything is
    # created through it. Resolution happens inside the guard, after that refusal.
    repo = getattr(args, "repo", REPO_DEFAULT).absolute()
    root = (getattr(args, "root", None) or repo).absolute()
    out = (getattr(args, "out", None) or root).absolute()

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
