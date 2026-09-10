# Unsigned rationale: local export and reopen

Implementation version `0.1.0` · candidate · proposed owner: Quirk OS.

This local Python capability validates a two-source comparison, preserves its exact text in a deterministic bundle, and reopens the saved record with explicit source freshness. It implements the export/reopen boundary of the Quirk Studio build playbook. It does not implement the iPhone comparison interface.

Use [the synthetic example](../../examples/unsigned-rationale/example.json) to reproduce the mechanics. Both source descriptions were written for this fixture; its choice is an agent-authored synthetic choice. Its timestamps record local source capture. No example statement is a report of Bryan's preference, user benefit, a deployed screen, or an accepted decision.

## Run from the repository root

Python 3 with the standard library is required; no provider account or dependency installation is needed.

```bash
python3 scripts/unsigned_rationale.py validate examples/unsigned-rationale/example.json

trial_dir="$(mktemp -d)"
python3 scripts/unsigned_rationale.py export examples/unsigned-rationale/example.json --out "$trial_dir/comparison"
python3 scripts/unsigned_rationale.py reopen "$trial_dir/comparison"
```

The output directory must not exist. Reopening without observations reports source freshness as `not_checked`; bundle integrity and source freshness answer different questions. Keep the temporary directory if you need the exported artifact after the exercise.

To compare this fixture against the local source bytes, prepare caller-supplied observations:

```bash
python3 - "$trial_dir/observations.json" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

packet = json.loads(Path("examples/unsigned-rationale/example.json").read_text(encoding="utf-8"))
observations = {}
allowed_files = {
    "source-a": Path("examples/unsigned-rationale/source-a.txt"),
    "source-b": Path("examples/unsigned-rationale/source-b.txt"),
}
for source in packet["sources"]:
    local_file = allowed_files[source["id"]]
    available = local_file.is_file()
    observations[source["id"]] = {
        "available": available,
        "revision": None,
        "sha256": hashlib.sha256(local_file.read_bytes()).hexdigest() if available else None,
    }
Path(sys.argv[1]).write_text(json.dumps(observations) + "\n", encoding="utf-8")
PY
python3 scripts/unsigned_rationale.py reopen "$trial_dir/comparison" --observations "$trial_dir/observations.json"
```

This demonstration deliberately resolves only the two repository fixture files. Production adapters must establish authorization and permitted source identity before producing observations. The core does not fetch source locators or attest that an observation is trustworthy.

To fingerprint one permitted local source:

```bash
python3 scripts/unsigned_rationale.py fingerprint examples/unsigned-rationale/source-a.txt \
  --id source-a --locator examples/unsigned-rationale/source-a.txt \
  --inspected-at 2026-09-10T01:45:38Z
```

Use the real capture time for new source captures. Supply `--revision REV` only when independently known. When omitted, the fingerprint output records a null revision and `revision_unavailable_reason: "Not supplied"`. The source digest covers exact file bytes, including its encoding and final newline. Source content is not included in the packet.

## Contract and failure behavior

The [Draft 2020-12 schema](../../schemas/unsigned-rationale.schema.json) documents interoperable structure. The Python core independently checks this specific protocol. Its local tests do not establish conformance to every JSON Schema feature or interoperability with every schema validator.

| Field or rule | Required behavior |
|---|---|
| Format | Exactly `quirk.unsigned-rationale` / `0.1.0` |
| Status and permissions | `CANDIDATE`, all three restrictions false, signature null |
| Sources | Exactly two unique IDs; nonempty locator; timezone-bearing capture timestamp |
| Source identity | Revision/digest present, or an explicit nonempty unavailable reason; known values require null reasons |
| Claims | Up to 128; unique IDs; one or two unique known source IDs; supplied/observed/inference/quirk_bet label |
| Claim support | Exactly one nonempty support locator or unsupported reason; its truth remains a review responsibility |
| Decision | Nonempty question and rationale; choose first/second/neither/defer; up to 128 unresolved questions |
| Values | No numbers, duplicate JSON keys, unknown fields, unsupported versions, or unencodable Unicode |
| Strings | Maximum 16,384 characters; IDs use the schema's restricted 128-character grammar |
| Resource limits | Packet input/export at most 1 MiB; source capture at most 64 MiB; nesting bounded at 32 |

Successful CLI operations return structured JSON on standard output with exit status `0`. Command execution failures return JSON on standard error with `error.code`, `error.path`, and `error.message`, and exit status `2`. Invalid command syntax uses standard argparse usage text and exit status `2`. Unsupported format versions fail with `UNSUPPORTED_VERSION`. Check exit status and structured fields before reporting success. `reopen` intentionally returns the saved packet, including rationale text, on standard output; direct it only to a permitted terminal or destination. Other commands emit summaries or source metadata. No logs are uploaded automatically.

The supported Python entry points are `validate_packet`, `parse_packet`, `canonical_bytes`, `reopen_packet`, and `capture_source`. They serve protocol validation, parsing, deterministic serialization, bundle verification/freshness, and local byte capture respectively. Their source of truth is [the implementation](../../scripts/unsigned_rationale.py).

## Bundle integrity and recovery

An exported directory contains only these protocol files:

| File | Role |
|---|---|
| `rationale.json` | UTF-8 packet with sorted object keys, compact separators, unescaped Unicode, preserved array order and string contents, and one trailing LF |
| `rationale.sha256` | SHA-256 of the exact final packet bytes |
| `COMMITTED.json` | Last-written marker naming the packet and digest files and the packet SHA-256 |

The marker format is `quirk.unsigned-rationale.bundle`, version `0.1.0`, with `packet_sha256` and `files: ["rationale.json", "rationale.sha256"]`. The packet hash is outside the packet, avoiding a self-referential digest. This serialization is a protocol rule; it does not claim general canonical JSON compliance.

Existing destinations are refused. A missing or invalid marker, altered packet, or inconsistent digest must prevent a successful reopen. Interrupted export may leave a partial directory. Preserve it for diagnosis, then retry from the original input into a new directory. Do not fabricate the missing marker or edit hashes to make a failed bundle pass. No power-loss atomicity or filesystem transaction guarantee is claimed.

A matching digest detects byte agreement with the stored digest; it does not authenticate the author, prove truthful content, or prevent someone replacing both content and hash. Local paths and bundle directories belong inside an authorized workspace.

## Source freshness

Caller-supplied observation shape is `{source_id: {available: boolean, revision: string|null, sha256: string|null}}`. A digest, when present, is 64 lowercase hexadecimal characters. Observation metadata stays outside the saved packet.

| Status | Meaning and next action |
|---|---|
| `not_checked` | No observation for this source; retain the saved comparison and label the gap |
| `unavailable` | Caller reports source unavailable; retain the rationale and recover access separately |
| `stale` | A comparable revision or digest differs; preserve this record and re-inspect into a new revision |
| `unverified` | Available source lacks enough comparable identity to establish agreement; capture missing identity |
| `unchanged` | Available comparable identity agrees; this does not prove other metadata, content claims, or caller trust |

Reopen never resolves arbitrary URLs, executes source text, edits the stored packet, applies a preference, grants training permission, or changes runtime grants. Locators are preserved opaque references; omit credentials and expiring signed URLs from durable records.

The core also rejects control characters, executable/embedded-data schemes, URL credentials, and recognized token/signature query fields in locators. This bounded rule is not a secret detector or a URL authorization policy. The caller remains responsible for the source reference it supplies.

## Reproduce local protocol tests

```bash
python3 -m unittest discover -s tests -p 'test_unsigned_rationale*.py' -v
```

The test module exercises byte preservation and integrity, source freshness and capture provenance, malformed or ambiguous JSON, input limits, unsafe locators, exact field shapes, and unchanged candidate restrictions. Consult the PR evidence receipt for the executed count, source revision, and actual result. These tests do not authenticate sources, render an interface, or prove runtime authority enforcement.

## Next proof

Integrate the module with one actual Quirk Now consumer while preserving its current result shapes and permissions. Then have Bryan inspect two real sources, record his own outcome/rationale, export, reopen on iPhone, and explain what is source evidence versus inference and unsigned versus accepted. Record interruptions, assistance, cleanup, and his helpfulness judgment. A synthetic export cannot establish that human result.

See [the capability contract](CAPABILITY.md) for ownership, composition, boundaries, and the open admission decision.

The existing Preference producer fixture is included as [unaltered source bytes](../../examples/unsigned-rationale/producer-event.native.json). Its [origin and exact digest](SOURCE-CENSUS.json) are recorded separately. The CLI test fingerprints this record without reserializing `payload_json` or converting it to the generic rationale format. It does not run the native Preference intake or prove its semantic compatibility.
