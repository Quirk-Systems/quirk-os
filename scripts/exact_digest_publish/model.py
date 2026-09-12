"""Strict wire values. These are runtime records, not new Quirk foundation types."""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import asdict, dataclass
from typing import Any


class Denied(Exception):
    """A stable denial code safe to return across the process boundary."""


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("ascii")).hexdigest()


def exact(value: Any, keys: set[str]) -> dict:
    if type(value) is not dict or set(value) != keys:
        raise Denied("INVALID_FIELDS")
    return value


def identifier(value: Any) -> str:
    if type(value) is not str or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", value):
        raise Denied("INVALID_IDENTIFIER")
    return value


def sha256(value: Any) -> str:
    if type(value) is not str or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise Denied("INVALID_DIGEST")
    return value


def integer(value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise Denied("INVALID_INTEGER")
    return value


def uuid_id(value: Any) -> str:
    if type(value) is not str:
        raise Denied("INVALID_UUID")
    try:
        if str(uuid.UUID(value)) != value:
            raise ValueError()
    except ValueError:
        raise Denied("INVALID_UUID") from None
    return value


@dataclass(frozen=True)
class PublicationSubject:
    artifact_id: str
    payload_digest: str
    operation: str
    destination_id: str
    policy_digest: str

    @classmethod
    def parse(cls, value: Any) -> PublicationSubject:
        exact(value, set(cls.__dataclass_fields__))
        identifier(value["artifact_id"])
        sha256(value["payload_digest"])
        identifier(value["destination_id"])
        sha256(value["policy_digest"])
        if value["operation"] != "publish":
            raise Denied("INVALID_OPERATION")
        return cls(**value)

    def wire(self) -> dict:
        return asdict(self)

    @property
    def key(self) -> str:
        return digest(self.wire())


@dataclass(frozen=True)
class Policy:
    id: str
    revision: int
    evaluation_ttl_seconds: int
    max_grant_seconds: int
    max_payload_bytes: int

    @classmethod
    def parse(cls, value: Any) -> Policy:
        exact(value, set(cls.__dataclass_fields__))
        identifier(value["id"])
        integer(value["revision"], 1, 2**31 - 1)
        integer(value["evaluation_ttl_seconds"], 1, 86400)
        integer(value["max_grant_seconds"], 1, 86400)
        integer(value["max_payload_bytes"], 1, 65536)
        return cls(**value)

    def wire(self) -> dict:
        return asdict(self)

    @property
    def key(self) -> str:
        return digest(self.wire())


def decode_json(text: str) -> dict:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise Denied("DUPLICATE_FIELD")
            result[key] = value
        return result

    def constant(_):
        raise Denied("NONFINITE_NUMBER")

    try:
        result = json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, RecursionError):
        raise Denied("INVALID_JSON") from None
    if type(result) is not dict:
        raise Denied("INVALID_ENVELOPE")
    return result
