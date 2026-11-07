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
import os
import re
import sys
import time
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

from .common import LEDGER_PATH, load_schemas, sha256_json, write_files
from .context import next_run_context
from .ledger import new_ledger
from .promotion import apply_promotion, attest_promotion
from .trigger import post_run_distill
from sync_control_plane.skill_runtime import validate_manifest_integrity


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _ledger(root: Path):
    path = root / LEDGER_PATH
    return _load(path) if path.exists() else new_ledger()


LOCK_NAME = "distill-ledger.lock"
WINDOWS_LOCK_ATTEMPTS = 6
CONTENTION_ERRNOS = frozenset(
    code
    for code in (
        getattr(errno, "EDEADLOCK", None),
        getattr(errno, "EDEADLK", None),
        getattr(errno, "EACCES", None),
        getattr(errno, "EPERM", None),
    )
    if code
)


def _lock_handle(handle) -> None:
    if os.name == "nt":
        if msvcrt is None:
            raise LockUnavailable("no interprocess lock primitive available on this host")
        handle.seek(0)
        for _ in range(WINDOWS_LOCK_ATTEMPTS):
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                return
            except OSError as exc:
                if exc.errno not in CONTENTION_ERRNOS:
                    raise LockUnavailable(f"lock primitive failed: {exc}") from exc
                time.sleep(0.05)
        raise LockUnavailable(f"lock still contended after {WINDOWS_LOCK_ATTEMPTS} attempts")
    if fcntl is not None:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        except OSError as exc:
            raise LockUnavailable(f"lock primitive failed: {exc}") from exc
        return
    raise LockUnavailable("no interprocess lock primitive available on this host")


def _unlock_handle(handle) -> None:
    if os.name == "nt":
        if msvcrt is None:
            return
        handle.seek(0)
        with contextlib.suppress(OSError):
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
    elif fcntl is not None:
        with contextlib.suppress(OSError):
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextlib.contextmanager
def _ledger_lock(root: Path):
    lock_path = root / "skills" / LOCK_NAME
    try:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        handle = open(lock_path, "a+b")
    except OSError as exc:
        raise LockUnavailable(f"lock setup failed: {exc}") from exc
    locked = False
    try:
        _lock_handle(handle)
        locked = True
        yield
    finally:
        if locked:
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


def _transaction_guarded(root: Path, transaction, *, source_root: Path | None = None):
    """Run a read/compute/write transaction while holding the ledger lock.

    Lock failures and explicit write refusals return structured errors.
    Unexpected transaction errors propagate; they never report success.
    """
    try:
        with contextlib.ExitStack() as locks:
            # Check paths as supplied before resolving or creating either lock.
            for given in (root, source_root or root):
                if any(path.is_symlink() for path in
                       (given, given / "skills", given / "skills" / LOCK_NAME, given / LEDGER_PATH)):
                    raise LockUnavailable(f"{given} or its lock/ledger path is a symlink; refusing to write through it")
            # Stable ordering prevents deadlocks for opposite-direction exports.
            roots = {root.resolve(), (source_root or root).resolve()}
            for locked_root in sorted(roots, key=str):
                locks.enter_context(_ledger_lock(locked_root))
            return 0, transaction()
    except WriteRefused as exc:
        print(json.dumps({"error": exc.code, "detail": str(exc)}), file=sys.stderr)
        return 1, None
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
        return 1, None


class WriteRefused(RuntimeError):
    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code


def _write_result(root: Path, result: dict, out: Path) -> dict:
    """Check and commit a computed result while the caller holds both locks."""
    expected = result.get("ledger_input_sha256")
    if _ledger_digest_on_disk(root) != expected:
        raise WriteRefused("LEDGER_FORKED", "source ledger changed; re-run against the current ledger")
    if out.resolve() != root.resolve():
        out_ledger = out / LEDGER_PATH
        if out_ledger.exists():
            try:
                matches = _ledger_digest_on_disk(out) == expected
            except (ValueError, KeyError, TypeError):
                matches = False
            if not matches:
                raise WriteRefused("LEDGER_FORKED", "output tree holds a different or invalid ledger; refusing to replace it")
        elif _out_tree_problems(out):
            raise WriteRefused("LEDGER_FORKED", "output tree is not empty and holds no ledger; refusing to write into it")
    unsafe = _destination_problems(out, result["files"])
    if unsafe:
        raise WriteRefused("LEDGER_FORKED", "; ".join(unsafe))
    try:
        write_files(out, result["files"])
    except OSError as exc:
        raise WriteRefused("WRITE_FAILED", str(exc)) from exc
    return result


def _write_guarded(root: Path, result: dict, out: Path | None = None) -> int:
    """Commit a precomputed result with main's compare-and-swap safeguards."""
    destination = out or root
    status, _ = _transaction_guarded(
        destination, lambda: _write_result(root, result, destination), source_root=root,
    )
    return status


def _complete_export(root: Path, out: Path, result: dict) -> dict:
    """Include and validate all packages and suites before writing their ledger."""
    if root.resolve() == out.resolve() or result.get("errors"):
        return result
    files = dict(result["files"])
    latest = {}
    for entry in result["ledger"]["entries"]:
        if entry["kind"] in {"distilled", "promoted", "rejected"}:
            latest[entry["candidate_id"]] = entry["refs"]
    try:
        for candidate_id, refs in latest.items():
            if not re.fullmatch(r"quirk-distilled-[a-z0-9-]+", candidate_id):
                raise ValueError("invalid candidate id in export ledger")
            manifest_path = f"skills/{candidate_id}/manifest.json"
            source_path = f"skills/{candidate_id}/SKILL.md"
            suite_path = f"evals/skills/distilled/{candidate_id}.json"
            if refs.get("eval_suite_ref") != suite_path:
                raise ValueError(f"{candidate_id}: unexpected eval suite path")
            for relative in (manifest_path, source_path, suite_path):
                if relative not in files:
                    unsafe = _destination_problems(root, [relative])
                    if unsafe:
                        raise ValueError("; ".join(unsafe))
                    files[relative] = (root / relative).read_bytes()
            manifest = json.loads(files[manifest_path])
            source = files[source_path]
            if isinstance(source, bytes):
                source = source.decode("utf-8")
            # Match text-mode reads in promotion and next-run context.
            source = source.replace("\r\n", "\n").replace("\r", "\n")
            problems = validate_manifest_integrity(manifest, source)
            if manifest.get("id") != candidate_id or manifest.get("status") != "candidate":
                problems.append("candidate identity or status drifted")
            integrity = manifest.get("integrity", {})
            if (integrity.get("manifest_sha256") != refs.get("manifest_sha256")
                    or integrity.get("source_blob_sha") != refs.get("source_blob_sha")):
                problems.append("package digests differ from ledger provenance")
            suite = json.loads(files[suite_path])
            if not isinstance(suite, list):
                problems.append("eval suite is not a list")
            if refs.get("eval_suite_sha256") and sha256_json(suite) != refs["eval_suite_sha256"]:
                problems.append("eval suite digest differs from ledger provenance")
            if problems:
                raise ValueError(f"{candidate_id}: " + "; ".join(problems))
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise WriteRefused("EXPORT_INCOMPLETE", str(exc)) from exc
    return {**result, "files": files}


REPO_DEFAULT = Path(__file__).resolve().parents[2]


def _add_roots(command) -> None:
    command.add_argument("--repo", type=Path, default=REPO_DEFAULT,
                         help="repository holding schemas/ and the source skills/ (default: this checkout)")
    command.add_argument("--root", type=Path, default=None,
                         help="tree holding the distill ledger and distilled candidates (default: --repo)")
    command.add_argument("--out", type=Path, default=None,
                         help="export from the --root ledger to this destination; destination ledger is not an input")


def _main(argv: list[str] | None = None) -> int:
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
        source_manifest = _load(skill_dir / "manifest.json")
        source_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")

        def distill(ledger):
            result = post_run_distill(
                receipt=receipt,
                trace=trace,
                source_manifest=source_manifest,
                source_text=source_text,
                ledger=ledger,
                schemas=schemas,
                registry=registry,
            )
            return _complete_export(root, out, result)

        if args.write:
            def write_distill():
                result = distill(_ledger(root))
                _write_result(root, result, out)
                return result

            status, result = _transaction_guarded(out, write_distill, source_root=root)
            if result is None:
                return status
        else:
            result = distill(_ledger(root))
        summary = {key: result[key] for key in ("outcome", "finding_codes", "candidate")}
        summary["files"] = sorted(result["files"])
        print(json.dumps(summary, indent=2))
        if args.write:
            return status
        return 0

    receipt = _load(args.receipt)
    candidate_dir = root / "skills" / receipt["candidate_id"]
    if not candidate_dir.exists():
        print(f"candidate package not found: {candidate_dir}", file=sys.stderr)
        return 1
    eval_suite = _load(args.eval_suite)

    def promote(ledger):
        result = apply_promotion(
            receipt,
            candidate_manifest=_load(candidate_dir / "manifest.json"),
            candidate_source=(candidate_dir / "SKILL.md").read_text(encoding="utf-8"),
            eval_suite=eval_suite,
            ledger=ledger,
            schemas=schemas,
        )
        return _complete_export(root, out, result)

    if args.write:
        def write_promotion():
            result = promote(_ledger(root))
            if not result["errors"]:
                _write_result(root, result, out)
            return result

        status, result = _transaction_guarded(out, write_promotion, source_root=root)
        if result is None:
            return status
    else:
        result = promote(_ledger(root))
    print(json.dumps({"outcome": result["outcome"], "errors": result["errors"], "files": sorted(result["files"])}, indent=2))
    if result["errors"]:
        return 1
    if args.write:
        return status
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        return _main(argv)
    except WriteRefused as exc:
        print(json.dumps({"error": exc.code, "detail": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
