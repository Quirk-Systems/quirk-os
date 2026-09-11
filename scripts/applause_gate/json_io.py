from __future__ import annotations

import json
from typing import Any


def load_json_strict(text: str) -> Any:
    return json.loads(text)
