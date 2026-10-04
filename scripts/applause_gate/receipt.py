from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_json_without_keys(value: dict[str, Any], omitted_keys: set[str]) -> str:
    return sha256_json({key: current for key, current in value.items() if key not in omitted_keys})
