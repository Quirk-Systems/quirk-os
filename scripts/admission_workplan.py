#!/usr/bin/env python3
"""Inspect admission debt without executing actions or manufacturing approvals."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = "evals/golden-admission/hold-audit.json"
QUEUE = "proposed-moves/pr-3/queue.json"


def local_path(root: Path, value: str) -> Path:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("invalid repository path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("path escapes repository")
    result = root / path
    # Reject directory symlinks too: a safe-looking final component is insufficient.
    if any(part.is_symlink() for part in (result, *result.parents) if part != root.parent):
        raise ValueError("symlink is not admission evidence")
    if not result.resolve().is_relative_to(root.resolve()):
        raise ValueError("path escapes repository")
    return result


def read_json(root: Path, path: str) -> dict:
    value = json.loads(local_path(root, path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("expected JSON object: " + path)
    return value


def build_plan(root: Path = ROOT) -> dict:
    queue = read_json(root, QUEUE)
    audit = read_json(root, AUDIT)
    head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    source = audit["source_commit"]
    if not isinstance(source, str) or len(source) != 40 or any(c not in "0123456789abcdef" for c in source):
        raise ValueError("audit requires exact source commit")
    if subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", source, head], capture_output=True).returncode:
        raise ValueError("audit source is not an ancestor of inspected head")
    audited = {row["move_id"]: row for row in audit["moves"]}
    refs = queue["move_refs"]
    ids = [ref["id"] for ref in refs]
    if len(audited) != len(audit["moves"]) or len(set(ids)) != len(ids) or set(ids) != set(audited):
        raise ValueError("audit must cover every queue move exactly once")
    tasks = []
    for ref in refs:
        move = read_json(root, ref["path"])
        row = audited[ref["id"]]
        if move["id"] != ref["id"]:
            raise ValueError("move identity mismatch")
        if row["acceptance_checks"] != move["acceptance_checks"] or row["disposition"] != move["disposition"]:
            raise ValueError("audit is stale for " + move["id"])
        if row.get("verified") is not False:
            raise ValueError("workplan audits cannot confer verification")
        historical = json.loads(subprocess.check_output(["git", "-C", str(root), "show", source + ":" + ref["path"]], text=True))
        if historical != move:
            raise ValueError("move changed since audit: " + move["id"])
        artifacts = []
        for path in row["actual_existing_artifact_paths"]:
            target = local_path(root, path)
            artifacts.append({"path": path, "present": target.is_file(), "sha256": hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None})
        tasks.append({
            "move_id": move["id"], "lane": move["lane"], "risk": move["risk"]["class"],
            "disposition": move["disposition"], "authority_required": move["authority_required"],
            "dependencies": move.get("dependencies", []),
            "acceptance": [{"criterion": c, "status": "unassessed"} for c in move["acceptance_checks"]],
            "current_artifacts": artifacts, "acceptance_gaps": row["acceptance_gaps"],
            "next_implementation": row["recommended_next_implementation"],
            "human_evidence_needed": row["human_evidence_needed"],
            "external_evidence_needed": row["live_provider_or_external_evidence_needed"],
            "stop_conditions": ["Unmet acceptance evidence", "Unresolved dependencies", "Missing independently authenticated authority"],
        })
    known = set(ids)
    if any(dep not in known for task in tasks for dep in task["dependencies"]):
        raise ValueError("unknown task dependency")
    # Detect dependency cycles instead of handing an impossible loop to an agent.
    pending = {task["move_id"]: set(task["dependencies"]) for task in tasks}
    waves = []
    while pending:
        ready = sorted(key for key, dependencies in pending.items() if not dependencies)
        if not ready:
            raise ValueError("dependency cycle")
        waves.append(ready)
        pending = {key: dependencies - set(ready) for key, dependencies in pending.items() if key not in ready}
    return {"schema_version": "admission-workplan.v1", "inspected_head": head, "audit_source": source,
            "execution_mode": "inspect_only", "authority_effect": "none", "admission_effect": "none",
            "verified_moves": 0, "holds": len(queue["blocking_move_ids"]), "dependency_waves": waves, "tasks": tasks}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        plan = build_plan()
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Admission workplan refused: {exc}\n")
    payload = json.dumps(plan, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
