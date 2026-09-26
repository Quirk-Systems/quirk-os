#!/usr/bin/env python3
"""Strict, offline candidate rationale interchange. Never an authority evaluator."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

VERSION = "0.1.0"
MAX_BYTES = 1024 * 1024
MAX_SOURCE_BYTES = 64 * 1024 * 1024
MAX_DEPTH = 32
MAX_STRING = 16384
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
TIMESTAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](?:\.[0-9]{1,6})?(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])\Z")
RESTRICTIONS = {
    "effects_allowed": False,
    "training_allowed": False,
    "preference_graph_apply_allowed": False,
}
SOURCE_KEYS = {
    "id", "locator", "inspected_at", "revision", "sha256",
    "revision_unavailable_reason", "digest_unavailable_reason",
}
PACKET_KEYS = {
    "format", "format_version", "id", "revision", "status", "sources",
    "question", "claims", "rationale", "outcome", "unresolved_questions",
    "restrictions", "signature",
}


class ProtocolError(ValueError):
    """A stable error code and field path, without echoing source contents."""

    def __init__(self, code: str, path: str, message: str):
        super().__init__(message)
        self.code, self.path = code, path

    def as_dict(self):
        return {"code": self.code, "path": self.path, "message": str(self)}


def require(condition, path, message, code="VALIDATION_FAILED"):
    if not condition:
        raise ProtocolError(code, path, message)


def text(value, path):
    require(type(value) is str and bool(value.strip()), path, "Expected nonempty text")
    require(len(value) <= MAX_STRING, path, "Text exceeds limit", "LIMIT_EXCEEDED")


def shape(value, keys, path):
    require(type(value) is dict, path, "Expected object")
    require(set(value) == set(keys), path, "Missing or unsupported fields")


def identifier(value, path):
    text(value, path)
    require(bool(ID.fullmatch(value)), path, "Invalid identifier")


def sha256_value(value, path):
    require(type(value) is str and bool(SHA.fullmatch(value)), path, "Expected lowercase SHA-256")


def _tree(value, path="$", depth=0):
    require(depth <= MAX_DEPTH, path, "Nesting exceeds limit", "LIMIT_EXCEEDED")
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        require(len(value) <= MAX_STRING, path, "Text exceeds limit", "LIMIT_EXCEEDED")
        require(not any(0xD800 <= ord(ch) <= 0xDFFF for ch in value), path, "Lone Unicode surrogate")
        return
    if type(value) is dict:
        for key, child in value.items():
            require(type(key) is str, path, "Object keys must be strings")
            _tree(key, path, depth + 1)
            _tree(child, path + "/" + key, depth + 1)
        return
    if type(value) is list:
        require(len(value) <= 128, path, "Array exceeds limit", "LIMIT_EXCEEDED")
        for index, child in enumerate(value):
            _tree(child, f"{path}/{index}", depth + 1)
        return
    raise ProtocolError("VALIDATION_FAILED", path, "Only objects, arrays, strings, booleans and null are allowed")


def locator(value, path):
    text(value, path)
    require(not any(ord(ch) < 32 or ord(ch) == 127 for ch in value), path, "Control character in locator")
    try:
        parsed = urlsplit(value)
        require(parsed.scheme.lower() not in {"javascript", "data", "vbscript"}, path, "Executable or embedded-data locator")
        require(parsed.username is None and parsed.password is None, path, "Credentials in locator")
        forbidden = {"token", "access_token", "id_token", "refresh_token", "authorization", "api_key", "apikey", "signature", "sig"}
        for key, _ in parse_qsl(parsed.query, keep_blank_values=True):
            key = key.casefold()
            require(key not in forbidden and not key.startswith(("x-amz-", "x-goog-")), path, "Credential or signed-access query in locator")
    except ValueError as exc:
        if isinstance(exc, ProtocolError):
            raise
        raise ProtocolError("VALIDATION_FAILED", path, "Malformed locator") from exc


def timestamp(value, path):
    text(value, path)
    require(bool(TIMESTAMP.fullmatch(value)), path, "Timestamp must use extended ISO time and timezone")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        require("T" in value and parsed.tzinfo is not None and parsed.utcoffset() is not None, path, "Timestamp requires time and timezone")
    except ValueError as exc:
        if isinstance(exc, ProtocolError):
            raise
        raise ProtocolError("VALIDATION_FAILED", path, "Invalid timestamp") from exc


def validate_source(source, path="$/sources"):
    shape(source, SOURCE_KEYS, path)
    identifier(source["id"], path + "/id")
    locator(source["locator"], path + "/locator")
    timestamp(source["inspected_at"], path + "/inspected_at")
    for key, reason in (("revision", "revision_unavailable_reason"), ("sha256", "digest_unavailable_reason")):
        if source[key] is None:
            text(source[reason], path + "/" + reason)
        else:
            (sha256_value if key == "sha256" else text)(source[key], path + "/" + key)
            require(source[reason] is None, path + "/" + reason, "Known value requires null unavailable reason")
    return source


def validate_packet(packet):
    """Validate this exact version and semantic references; never mutate input."""
    _tree(packet)
    shape(packet, PACKET_KEYS, "$")
    require(packet["format"] == "quirk.unsigned-rationale" and packet["format_version"] == VERSION,
            "$/format_version", "Unsupported rationale format/version", "UNSUPPORTED_VERSION")
    identifier(packet["id"], "$/id")
    text(packet["revision"], "$/revision")
    require(packet["status"] == "CANDIDATE", "$/status", "Only CANDIDATE is supported")
    require(packet["signature"] is None, "$/signature", "Only unsigned records are supported")
    shape(packet["restrictions"], RESTRICTIONS, "$/restrictions")
    for key in RESTRICTIONS:
        require(packet["restrictions"][key] is False, "$/restrictions/" + key, "Restriction must remain false")
    for key in ("question", "rationale"):
        text(packet[key], "$/" + key)
    require(packet["outcome"] in ("choose_first", "choose_second", "choose_neither", "defer"), "$/outcome", "Unsupported comparison outcome")
    require(type(packet["sources"]) is list and len(packet["sources"]) == 2, "$/sources", "Exactly two sources are required")
    for index, source in enumerate(packet["sources"]):
        validate_source(source, f"$/sources/{index}")
    source_ids = [source["id"] for source in packet["sources"]]
    require(len(set(source_ids)) == 2, "$/sources", "Source identifiers must be unique")
    require(type(packet["claims"]) is list, "$/claims", "Expected claims array")
    seen = set()
    for index, claim in enumerate(packet["claims"]):
        path = f"$/claims/{index}"
        shape(claim, {"id", "text", "assertion_class", "source_ids", "support_locator", "unsupported_reason"}, path)
        identifier(claim["id"], path + "/id")
        require(claim["id"] not in seen, path + "/id", "Duplicate claim identifier")
        seen.add(claim["id"])
        text(claim["text"], path + "/text")
        require(claim["assertion_class"] in ("supplied", "observed", "inference", "quirk_bet"), path + "/assertion_class", "Unsupported assertion class")
        refs = claim["source_ids"]
        require(type(refs) is list and 1 <= len(refs) <= 2, path + "/source_ids", "One or two source references required")
        for ref in refs:
            identifier(ref, path + "/source_ids")
        require(len(set(refs)) == len(refs) and set(refs) <= set(source_ids), path + "/source_ids", "Unknown or repeated source reference")
        if claim["support_locator"] is None:
            text(claim["unsupported_reason"], path + "/unsupported_reason")
        else:
            locator(claim["support_locator"], path + "/support_locator")
            require(claim["unsupported_reason"] is None, path + "/unsupported_reason", "Support and unsupported reason are mutually exclusive")
    questions = packet["unresolved_questions"]
    require(type(questions) is list, "$/unresolved_questions", "Expected question array")
    for index, question in enumerate(questions):
        text(question, f"$/unresolved_questions/{index}")
    return packet


def _object_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "$", "Duplicate JSON key", "INVALID_JSON")
        result[key] = value
    return result


def _reject_number(_):
    raise ProtocolError("INVALID_JSON", "$", "Numeric values are unsupported in this format")


def _decode(raw):
    require(type(raw) is bytes, "$", "Expected UTF-8 bytes", "INVALID_JSON")
    require(len(raw) <= MAX_BYTES, "$", "Packet exceeds byte limit", "LIMIT_EXCEEDED")
    try:
        decoded = raw.decode("utf-8", errors="strict")
        depth, quoted, escaped = 0, False, False
        for char in decoded:
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char in "[{":
                depth += 1
                require(depth <= MAX_DEPTH, "$", "Nesting exceeds limit", "LIMIT_EXCEEDED")
            elif char in "]}":
                depth -= 1
        return json.loads(decoded, object_pairs_hook=_object_pairs, parse_int=_reject_number,
                          parse_float=_reject_number, parse_constant=_reject_number)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ProtocolError("INVALID_JSON", "$", "Malformed UTF-8 JSON") from exc


def parse_packet(raw):
    return validate_packet(_decode(raw))


def _serialize(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def canonical_bytes(packet):
    raw = _serialize(validate_packet(packet))
    require(len(raw) <= MAX_BYTES, "$", "Canonical packet exceeds byte limit", "LIMIT_EXCEEDED")
    return raw


def capture_source(raw, *, source_id, locator, inspected_at, revision=None, revision_unavailable_reason="Not supplied"):
    """Hash supplied bytes exactly; performs no fetch, parsing, or authenticity claim."""
    require(type(raw) is bytes, "$", "Source must be supplied as bytes")
    require(len(raw) <= MAX_SOURCE_BYTES, "$", "Source exceeds byte limit", "LIMIT_EXCEEDED")
    source = {
        "id": source_id, "locator": locator, "inspected_at": inspected_at,
        "revision": revision, "sha256": hashlib.sha256(raw).hexdigest(),
        "revision_unavailable_reason": revision_unavailable_reason if revision is None else None,
        "digest_unavailable_reason": None,
    }
    _tree(source)
    return validate_source(source)


def _freshness(packet, observations):
    if observations is None:
        observations = {}
    _tree(observations)
    require(type(observations) is dict, "$/observations", "Expected observation object")
    known = {source["id"] for source in packet["sources"]}
    require(set(observations) <= known, "$/observations", "Observation refers to unknown source")
    states = []
    for source in packet["sources"]:
        observed = observations.get(source["id"])
        compared = []
        if source["id"] not in observations:
            state = "not_checked"
        else:
            path = "$/observations/" + source["id"]
            shape(observed, {"available", "revision", "sha256"}, path)
            require(type(observed["available"]) is bool, path + "/available", "Expected explicit availability")
            for key in ("revision", "sha256"):
                if observed[key] is not None:
                    (sha256_value if key == "sha256" else text)(observed[key], path + "/" + key)
            if observed["available"] is False:
                require(observed["revision"] is None and observed["sha256"] is None, path, "Unavailable observation cannot claim current revision/digest")
                state = "unavailable"
            else:
                compared = [key for key in ("revision", "sha256") if source[key] is not None and observed[key] is not None]
                mismatch = any(source[key] != observed[key] for key in compared)
                state = "stale" if mismatch else "unchanged" if compared else "unverified"
        states.append({"source_id": source["id"], "state": state, "compared": compared})
    return states


def reopen_packet(raw, expected_sha256=None, observations=None):
    packet = parse_packet(raw)
    raw_digest = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None:
        sha256_value(expected_sha256, "$/expected_sha256")
        require(raw_digest == expected_sha256, "$", "Packet bytes do not match supplied digest", "INTEGRITY_MISMATCH")
    return {
        "packet": packet,
        "integrity": {"raw_sha256": raw_digest, "canonical_sha256": hashlib.sha256(canonical_bytes(packet)).hexdigest(),
                      "sidecar": "matched" if expected_sha256 is not None else "absent"},
        "source_states": _freshness(packet, observations),
    }


def _read(path, limit=MAX_BYTES):
    with Path(path).open("rb") as handle:
        raw = handle.read(limit + 1)
    require(len(raw) <= limit, "$", "File exceeds byte limit", "LIMIT_EXCEEDED")
    return raw


def _write_new(path, raw):
    with path.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())


def write_bundle(packet, output):
    """Reserve a new directory, then write the completion marker last."""
    raw = canonical_bytes(packet)
    digest = hashlib.sha256(raw).hexdigest()
    output = Path(output)
    try:
        output.mkdir()  # Exclusive reservation. Never replace an existing directory.
    except FileExistsError as exc:
        raise ProtocolError("OUTPUT_EXISTS", "$", "Output already exists; use a new directory") from exc
    marker = {"format": "quirk.unsigned-rationale.bundle", "format_version": VERSION,
              "packet_sha256": digest, "files": ["rationale.json", "rationale.sha256"]}
    # Preserve an incomplete attempt on failure. Never delete an uninspected file
    # that another actor may have created. Reopen requires the marker and digests.
    for name, content in (("rationale.json", raw), ("rationale.sha256", (digest + "\n").encode("ascii")),
                          ("COMMITTED.json", _serialize(marker))):
        _write_new(output / name, content)
    return {"status": "CANDIDATE", "packet_id": packet["id"], "packet_sha256": digest,
            "directory": str(output), "signature": None, "restrictions": dict(RESTRICTIONS)}


def reopen_bundle(directory, observations=None):
    directory = Path(directory)
    for name in ("COMMITTED.json", "rationale.json", "rationale.sha256"):
        require((directory / name).is_file() and not (directory / name).is_symlink(), "$", "Incomplete or invalid bundle", "INCOMPLETE_BUNDLE")
    marker = _decode(_read(directory / "COMMITTED.json"))
    shape(marker, {"format", "format_version", "packet_sha256", "files"}, "$/marker")
    require(marker["format"] == "quirk.unsigned-rationale.bundle" and marker["format_version"] == VERSION,
            "$/marker", "Unsupported bundle format/version", "UNSUPPORTED_VERSION")
    require(marker["files"] == ["rationale.json", "rationale.sha256"], "$/marker/files", "Only fixed bundle members are supported")
    sha256_value(marker["packet_sha256"], "$/marker/packet_sha256")
    require(_read(directory / "rationale.sha256", 65) == (marker["packet_sha256"] + "\n").encode("ascii"),
            "$/marker", "Digest sidecar does not match commit marker", "INTEGRITY_MISMATCH")
    return reopen_packet(_read(directory / "rationale.json"), marker["packet_sha256"], observations)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("input")
    export = commands.add_parser("export")
    export.add_argument("input")
    export.add_argument("--out", required=True)
    reopen = commands.add_parser("reopen")
    reopen.add_argument("directory")
    reopen.add_argument("--observations")
    fingerprint = commands.add_parser("fingerprint")
    fingerprint.add_argument("file")
    fingerprint.add_argument("--id", required=True)
    fingerprint.add_argument("--locator", required=True)
    fingerprint.add_argument("--inspected-at", required=True)
    fingerprint.add_argument("--revision")
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            packet = parse_packet(_read(args.input))
            result = {"valid": True, "packet_id": packet["id"], "status": packet["status"],
                      "canonical_sha256": hashlib.sha256(canonical_bytes(packet)).hexdigest(), "restrictions": dict(RESTRICTIONS)}
        elif args.command == "export":
            result = write_bundle(parse_packet(_read(args.input)), args.out)
        elif args.command == "reopen":
            observations = _decode(_read(args.observations)) if args.observations else None
            result = reopen_bundle(args.directory, observations)
        else:
            result = capture_source(_read(args.file, MAX_SOURCE_BYTES), source_id=args.id, locator=args.locator,
                                    inspected_at=args.inspected_at, revision=args.revision)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except ProtocolError as exc:
        print(json.dumps({"error": exc.as_dict()}), file=sys.stderr)
        return 2
    except (OSError, UnicodeError) as exc:
        # Paths, contents and exception repr may contain private input; don't echo.
        error = {"code": "IO_ERROR", "path": "$", "message": "Local file operation failed"}
        print(json.dumps({"error": error}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
