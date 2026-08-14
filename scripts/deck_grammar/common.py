from __future__ import annotations
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable
import json
import re
import yaml

AUTHORITY_ORDER = {'observe': 0, 'infer': 1, 'propose': 2, 'execute_reversible': 3, 'enforce_invariant': 4, 'execute_protected': 5}


class DeckGrammarError(ValueError):
    pass

def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

def content_hash(value: Any) -> str:
    return sha256(canonical_json(value).encode('utf-8')).hexdigest()

def parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    normalized = value.replace('Z', '+00:00')
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)

def is_active_entitlement(entitlement: dict[str, Any], as_of: datetime) -> bool:
    if entitlement.get('state') != 'active':
        return False
    starts = parse_datetime(entitlement.get('starts_at'))
    ends = parse_datetime(entitlement.get('ends_at'))
    if starts and as_of < starts:
        return False
    if ends and as_of >= ends:
        return False
    return entitlement.get('authority_effect') == 'none'

def wildcard_match(values: Iterable[str], candidate: str) -> bool:
    materialized = set(values)
    return not materialized or '*' in materialized or candidate in materialized

def authority_not_above(card_ceiling: str, external_ceiling: str) -> bool:
    return AUTHORITY_ORDER[card_ceiling] <= AUTHORITY_ORDER[external_ceiling]

def _slug(value: str) -> str:
    return re.sub('[^a-z0-9._-]+', '-', value.lower()).strip('-')

def load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding='utf-8'))
    if not isinstance(loaded, dict):
        raise DeckGrammarError(f'{path}: expected YAML object')
    return loaded

def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))
