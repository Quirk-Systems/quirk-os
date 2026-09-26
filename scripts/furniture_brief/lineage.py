"""Parent/child asset lineage validation.

A batch is exactly one ``reality_shard`` root plus zero or more children.
Every child's ``parent_ids`` must resolve inside the same batch, the root
must have no parents, and the parent graph must be acyclic.
"""
from __future__ import annotations

from typing import Any


def validate(assets: list[dict[str, Any]]) -> dict[str, Any]:
    problems: list[str] = []

    ids = [asset.get("asset_id") for asset in assets]
    duplicate_ids = {asset_id for asset_id in ids if ids.count(asset_id) > 1}
    if duplicate_ids:
        problems.append(f"duplicate asset_id(s): {sorted(duplicate_ids)}")

    id_set = set(ids)
    by_id = {asset.get("asset_id"): asset for asset in assets}

    roots = [asset for asset in assets if asset.get("asset_type") == "reality_shard"]
    if len(roots) != 1:
        problems.append(f"expected exactly one reality_shard root, found {len(roots)}")
    else:
        root = roots[0]
        if root.get("parent_ids"):
            problems.append("reality_shard root must not have parent_ids")

    for asset in assets:
        if asset.get("asset_type") == "reality_shard":
            continue
        for parent_id in asset.get("parent_ids", []):
            if parent_id not in id_set:
                problems.append(
                    f"{asset.get('asset_id')} references missing parent_id {parent_id!r}"
                )

    # Cycle detection (DFS with recursion-stack tracking).
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {asset_id: WHITE for asset_id in id_set}

    def visit(asset_id: str) -> bool:
        color[asset_id] = GRAY
        asset = by_id.get(asset_id)
        for parent_id in (asset.get("parent_ids", []) if asset else []):
            if parent_id not in color:
                continue
            if color[parent_id] == GRAY:
                return True
            if color[parent_id] == WHITE and visit(parent_id):
                return True
        color[asset_id] = BLACK
        return False

    has_cycle = False
    for asset_id in id_set:
        if color.get(asset_id) == WHITE:
            if visit(asset_id):
                has_cycle = True
                break
    if has_cycle:
        problems.append("lineage graph contains a cycle")

    return {"valid": not problems, "problems": problems}
