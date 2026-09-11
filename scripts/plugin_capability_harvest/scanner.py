"""Bounded, non-executing scanner for explicitly supplied plugin directories."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .core import API_VERSION, sha256

ALLOWLIST = {"package.json", "manifest.json", "plugin.json", "SKILL.md"}


@dataclass(frozen=True)
class ScanLimits:
    max_files: int = 500
    max_bytes_per_file: int = 1_000_000
    max_total_bytes: int = 20_000_000


def _inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def _identity(plugin_dir: Path) -> tuple[str | None, str | None, list[str], list[str]]:
    package_id = version = None
    contradictions: list[str] = []
    quarantine: list[str] = []
    seen: list[tuple[str, str, str]] = []
    for name in ("manifest.json", "plugin.json", "package.json"):
        path = plugin_dir / name
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            quarantine.append(f"malformed:{path.name}")
            continue
        candidate_id = data.get("id") or data.get("name") or data.get("package")
        candidate_version = data.get("version")
        if isinstance(candidate_id, str) and isinstance(candidate_version, str):
            seen.append((name, candidate_id, candidate_version))
            package_id = package_id or candidate_id
            version = version or candidate_version
    for name, candidate_id, candidate_version in seen:
        if candidate_id != package_id:
            contradictions.append(f"identity:{name}:{candidate_id}!={package_id}")
        if candidate_version != version:
            contradictions.append(f"version:{name}:{candidate_version}!={version}")
    if package_id is None or version is None:
        quarantine.append("identity_unresolved")
    return package_id, version, contradictions, quarantine


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
    plugin_dirs = sorted({path.parent for path in base.rglob("*") if path.name in ALLOWLIST})
    for plugin_dir in plugin_dirs:
        resolved_dir = plugin_dir.resolve()
        if not _inside(base, resolved_dir):
            quarantine.append({"path": str(plugin_dir), "reason": "PATH_SCOPE_VIOLATION"})
            continue
        package_id, version, contradictions, identity_quarantine = _identity(plugin_dir)
        for reason in identity_quarantine:
            quarantine.append({"path": str(plugin_dir.relative_to(base)), "reason": reason})
        if package_id is None or version is None:
            continue
        for path in sorted(plugin_dir.iterdir()):
            if path.name not in ALLOWLIST or not path.is_file():
                continue
            files_seen += 1
            if files_seen > limits.max_files:
                quarantine.append({"path": str(path.relative_to(base)), "reason": "FILE_LIMIT"})
                break
            resolved = path.resolve()
            if not _inside(base, resolved):
                quarantine.append({"path": str(path.relative_to(base)), "reason": "PATH_SCOPE_VIOLATION"})
                continue
            size = resolved.stat().st_size
            if size > limits.max_bytes_per_file or total_bytes + size > limits.max_total_bytes:
                quarantine.append({"path": str(path.relative_to(base)), "reason": "BYTE_LIMIT"})
                continue
            raw = resolved.read_bytes()
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
    return {
        "api_version": API_VERSION,
        "kind": "PluginRootScan",
        "root_fingerprint": sha256([item["surface"]["sha256"] for item in observations]),
        "observations": observations,
        "quarantine": quarantine,
        "limits": limits.__dict__,
        "no_code_executed": True,
        "authority_effect": "none",
    }
