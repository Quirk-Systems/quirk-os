"""Bounded, non-executing scanner for explicitly supplied plugin directories."""

from __future__ import annotations

import json
import os
import stat
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .core import API_VERSION, sha256

IDENTITY_PATHS = (Path(".codex-plugin/plugin.json"), Path("manifest.json"), Path("plugin.json"), Path("package.json"))


@dataclass(frozen=True)
class ScanLimits:
    max_files: int = 500
    max_directories: int = 2_000
    max_bytes_per_file: int = 1_000_000
    max_total_bytes: int = 20_000_000


def _inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def _safe_read(path: Path, root: Path, limit: int) -> bytes:
    if path.is_symlink() or not _inside(root, path.resolve(strict=True)):
        raise ValueError("PATH_SCOPE_VIOLATION")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        file_stat = os.fstat(descriptor)
        if not stat.S_ISREG(file_stat.st_mode):
            raise ValueError("NOT_REGULAR_FILE")
        if file_stat.st_size > limit:
            raise ValueError("BYTE_LIMIT")
        chunks: list[bytes] = []
        remaining = limit + 1
        while remaining:
            chunk = os.read(descriptor, min(64 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        if len(payload) > limit:
            raise ValueError("BYTE_LIMIT")
        return payload
    finally:
        os.close(descriptor)


def _identity(plugin_dir: Path, root: Path, limit: int) -> tuple[str | None, str | None, list[str], list[str], dict[Path, bytes]]:
    package_id = version = None
    contradictions: list[str] = []
    quarantine: list[str] = []
    seen: list[tuple[str, str, str]] = []
    captured: dict[Path, bytes] = {}
    for relative in IDENTITY_PATHS:
        path = plugin_dir / relative
        if not path.is_file():
            continue
        try:
            raw = _safe_read(path, root, limit)
            captured[path] = raw
            data = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            quarantine.append(f"{str(exc) if isinstance(exc, ValueError) else 'malformed'}:{relative}")
            continue
        candidate_id = data.get("id") or data.get("name") or data.get("package")
        candidate_version = data.get("version")
        if isinstance(candidate_id, str) and isinstance(candidate_version, str):
            seen.append((str(relative), candidate_id, candidate_version))
            package_id = package_id or candidate_id
            version = version or candidate_version
    for name, candidate_id, candidate_version in seen:
        if candidate_id != package_id:
            contradictions.append(f"identity:{name}:{candidate_id}!={package_id}")
        if candidate_version != version:
            contradictions.append(f"version:{name}:{candidate_version}!={version}")
    if package_id is None or version is None:
        quarantine.append("identity_unresolved")
    return package_id, version, contradictions, quarantine, captured


def _discover_plugin_roots(base: Path, limits: ScanLimits) -> tuple[set[Path], list[dict[str, Any]]]:
    """Find declared roots without unbounded recursion or following symlinks."""
    declared: set[Path] = set()
    quarantine: list[dict[str, Any]] = []
    directories_seen = 0
    for current, directories, files in os.walk(base, topdown=True, followlinks=False):
        directories[:] = sorted(name for name in directories if not (Path(current) / name).is_symlink())
        directories_seen += 1
        if directories_seen > limits.max_directories:
            quarantine.append({"path": ".", "reason": "DIRECTORY_LIMIT"})
            break
        current_path = Path(current)
        if current_path.name == ".codex-plugin" and "plugin.json" in files:
            declared.add(current_path.parent)
            directories[:] = []
    if not declared:
        for path in sorted(base.iterdir()):
            if path.is_dir() and not path.is_symlink() and any((path / rel).is_file() for rel in IDENTITY_PATHS):
                declared.add(path)
                if len(declared) > limits.max_files:
                    quarantine.append({"path": ".", "reason": "FILE_LIMIT"})
                    break
    return declared, quarantine


def scan_plugin_root(root: str | Path, limits: ScanLimits = ScanLimits(), observed_at: str | None = None) -> dict[str, Any]:
    """Inspect allowlisted files only; never import, invoke, install, or mutate."""
    base = Path(root).resolve(strict=True)
    if not base.is_dir():
        raise ValueError("plugin root must be a directory")
    observed = observed_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    fresh_until = (datetime.fromisoformat(observed.replace("Z", "+00:00")) + timedelta(days=7)).isoformat().replace("+00:00", "Z")
    observations: list[dict[str, Any]] = []
    quarantine: list[dict[str, Any]] = []
    total_bytes = 0
    files_seen = 0
    declared_roots, discovery_quarantine = _discover_plugin_roots(base, limits)
    quarantine.extend(discovery_quarantine)
    plugin_dirs = sorted(declared_roots)
    for plugin_dir in plugin_dirs:
        resolved_dir = plugin_dir.resolve()
        if not _inside(base, resolved_dir):
            quarantine.append({"path": str(plugin_dir), "reason": "PATH_SCOPE_VIOLATION"})
            continue
        package_id, version, contradictions, identity_quarantine, identity_content = _identity(plugin_dir, base, limits.max_bytes_per_file)
        for reason in identity_quarantine:
            quarantine.append({"path": str(plugin_dir.relative_to(base)), "reason": reason})
        if contradictions:
            quarantine.append({"path": str(plugin_dir.relative_to(base)), "reason": "identity_conflict", "contradictions": contradictions})
            continue
        if package_id is None or version is None:
            continue
        candidates = [plugin_dir / rel for rel in IDENTITY_PATHS]
        candidates.extend(sorted((plugin_dir / "skills").glob("*/SKILL.md")) if (plugin_dir / "skills").is_dir() else [])
        for path in candidates:
            if not path.is_file():
                continue
            files_seen += 1
            if files_seen > limits.max_files:
                quarantine.append({"path": str(path.relative_to(base)), "reason": "FILE_LIMIT"})
                break
            if path in identity_content:
                raw = identity_content[path]
            else:
                try:
                    raw = _safe_read(path, base, limits.max_bytes_per_file)
                except (OSError, ValueError) as exc:
                    quarantine.append({"path": str(path.relative_to(base)), "reason": str(exc)})
                    continue
            if total_bytes + len(raw) > limits.max_total_bytes:
                quarantine.append({"path": str(path.relative_to(base)), "reason": "BYTE_LIMIT"})
                continue
            total_bytes += len(raw)
            kind = "skill" if path.name == "SKILL.md" else "manifest"
            observations.append({
                "api_version": API_VERSION,
                "kind": "PluginSurfaceObservation",
                "identity": {"plugin_id": package_id, "package_id": package_id, "declared_version": version, "resolved_version": version},
                "surface": {
                    "type": kind, "id": path.name, "relative_path": str(path.relative_to(base)),
                    "sha256": sha256(raw), "installed": "observed",
                    "exposed": "unknown", "callable": "unknown",
                },
                "rights": {"status": "unclear", "license_ref": None},
                "effects": {"documented": ["unknown"], "observed": []},
                "authority": {"required": ["unknown"], "granted": False},
                "contradictions": contradictions,
                "observed_at": observed,
                "fresh_until": fresh_until,
            })
    observations.sort(key=lambda item: (
        item["identity"]["plugin_id"], item["identity"]["resolved_version"],
        item["surface"]["type"], item["surface"]["relative_path"],
    ))
    quarantine_fingerprint = sha256(quarantine)
    return {
        "api_version": API_VERSION,
        "kind": "PluginRootScan",
        "root_fingerprint": sha256({"observations": [{
            "identity": item["identity"], "surface": item["surface"],
            "rights": item["rights"], "contradictions": item["contradictions"]
        } for item in observations], "quarantine_sha256": quarantine_fingerprint}),
        "quarantine_set_sha256": quarantine_fingerprint,
        "observations": observations,
        "quarantine": quarantine,
        "limits": limits.__dict__,
        "no_code_executed": True,
        "authority_effect": "none",
    }
