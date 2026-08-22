"""Canonical, deterministic helpers for candidate evidence receipts."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    """Render JSON with stable key ordering and no insignificant whitespace."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_json(value: Any) -> str:
    """Hash the UTF-8 bytes of ``value`` rendered as canonical JSON."""

    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_json_without_keys(
    value: dict[str, Any], omitted_keys: set[str]
) -> str:
    """Hash a mapping after omitting exactly the named top-level keys."""

    return sha256_json(
        {
            key: current
            for key, current in value.items()
            if key not in omitted_keys
        }
    )
