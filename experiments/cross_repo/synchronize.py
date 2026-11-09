"""One bounded local refresh: immutable snapshot + locked compare-and-swap pointer."""
import hashlib
import json
import os
from pathlib import Path
import re
import uuid
from datetime import datetime, timezone

from compiler import canonical, compile_pack, digest, load, write_pack


def sync(source, destination, expected_current=None):
    pack = compile_pack(source)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    lock = destination / ".sync-lock"
    lock.mkdir()  # Exclusive local lock. A stale lock requires explicit recovery.
    try:
        pointer = destination / "current.json"
        previous = load(pointer) if pointer.exists() else None
        actual = previous["snapshot"] if previous else None
        if actual is not None and not re.fullmatch("[a-f0-9]{64}", actual):
            raise ValueError("invalid current snapshot")
        if actual != expected_current:
            raise ValueError("current snapshot changed; reread before retry")
        if actual is not None:
            old_source = load(destination / "snapshots" / actual / "pack.json")["source"]
            if old_source["id"] != source["id"]:
                raise ValueError("a local stream cannot silently switch source identity")
            if old_source["revision"] == source["revision"] and old_source != source:
                raise ValueError("source revision reused for changed meaning")
        style_version = digest(load(Path(__file__).with_name("styles") / "style-lock.json"))
        snapshot = digest({"pack": pack, "style_version": style_version})
        snapshots = destination / "snapshots"
        target = snapshots / snapshot
        if target.exists():
            if load(target / "pack.json") != pack:
                raise ValueError("snapshot contents changed")
            receipt = load(target / "receipt.json")
            allowed = {"pack.json", "music.json", "arcade.json", "town.json", "index.html", "quirk.css", "style-lock.json"}
            if set(receipt["output_sha256"]) != allowed:
                raise ValueError("snapshot receipt incomplete")
            for name, expected in receipt["output_sha256"].items():
                if hashlib.sha256((target / name).read_bytes()).hexdigest() != expected:
                    raise ValueError("snapshot output changed")
        else:
            write_pack(pack, target)
        if actual == snapshot:
            return {"status": "unchanged", "snapshot": snapshot}
        started = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        next_pointer = {"snapshot": snapshot, "source_revision": source["revision"], "previous": actual}
        transaction = uuid.uuid4().hex
        pending = destination / ("." + transaction + ".json")
        receipt_path = destination / "receipts" / (transaction + ".json")
        receipt_path.parent.mkdir(exist_ok=True)
        receipt = {
            "receiptId": "receipt_sync_" + transaction, "actionId": "action_local_sync",
            "actorId": "local_operator", "target": str(pointer),
            "authority": ["user_authorized_local_reversible_preparation"],
            "inputs": [pack["source_sha256"]], "outputs": [snapshot],
            "startedAt": started, "completedAt": started, "result": "success",
            "changes": [{"path": "current.json", "before": previous, "after": next_pointer}],
            "rollback": {"supported": True, "reference": "Select prior verified snapshot under the same local lock; retain receipts and snapshots"},
        }
        pending.write_text(canonical(next_pointer) + "\n", encoding="utf-8")
        # Provisional record cannot claim success before the pointer is actually delivered.
        provisional = dict(receipt, result="cancelled", changes=[], outputs=[])
        receipt_path.write_text(canonical(provisional) + "\n", encoding="utf-8")
        try:
            os.replace(pending, pointer)
            if load(pointer) != next_pointer:
                raise ValueError("pointer postcondition failed")
            receipt["completedAt"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            receipt_path.write_text(canonical(receipt) + "\n", encoding="utf-8")
        except BaseException:
            receipt["result"] = "failed"
            receipt["changes"] = []
            receipt["outputs"] = []
            if pointer.exists() and load(pointer) == next_pointer:
                if previous is None:
                    pointer.unlink()
                else:
                    pending.write_text(canonical(previous) + "\n", encoding="utf-8")
                    os.replace(pending, pointer)
            receipt_path.write_text(canonical(receipt) + "\n", encoding="utf-8")
            pending.unlink(missing_ok=True)
            raise
        return {"status": "updated", "snapshot": snapshot, "receipt": str(receipt_path)}
    finally:
        lock.rmdir()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--expected-current")
    args = parser.parse_args()
    print(json.dumps(sync(load(args.source), args.destination, args.expected_current), sort_keys=True))
