"""Pure candidate planning and marked-text preparation; no provider effects."""

import hashlib
import json

VERSION = "change-maintenance.v0.1.0"
KINDS = {"authority": 0, "contract": 1, "goal": 2, "plan": 3,
         "config": 4, "agent": 4, "template": 5, "vocabulary": 5,
         "code": 6, "document": 7, "design": 7, "media": 7, "projection": 8}
PLATFORMS = {"github", "supabase", "drive", "airtable", "notion", "vercel", "device"}
DISPOSITIONS = {"proposed", "accepted", "closed", "superseded"}
START = "<!-- quirk-change:start -->"
END = "<!-- quirk-change:end -->"


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _text(value):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= 2048


def plan_changes(objects, event, *, completed_keys=()):
    """Resolve an observed snapshot into ordered inert proposals.

    Inputs are asserted observations. This function authenticates no authority,
    persists no deduplication state, and never invokes an adapter.
    """
    fields = {"object_key", "version", "kind", "platform", "owner", "binding_id",
              "dependencies", "availability"}
    if not isinstance(objects, list) or not 1 <= len(objects) <= 256:
        raise ValueError("object budget")
    nodes = {}
    edges = 0
    for node in objects:
        if not isinstance(node, dict) or set(node) != fields:
            raise ValueError("object contract")
        if any(not _text(node[k]) for k in fields - {"dependencies"}):
            raise ValueError("object identity")
        if (node["kind"] not in KINDS or node["platform"] not in PLATFORMS
                or node["availability"] not in {"online", "offline", "unknown"}):
            raise ValueError("object enum")
        key = node["object_key"]
        if key in nodes:
            raise ValueError("duplicate object identity")
        deps = node["dependencies"]
        if not isinstance(deps, list) or any(not _text(d) for d in deps):
            raise ValueError("dependency contract")
        if len(deps) != len(set(deps)):
            raise ValueError("duplicate dependency")
        edges += len(deps)
        nodes[key] = node
    if edges > 1024:
        raise ValueError("edge budget")
    bindings = [(n["platform"], n["binding_id"]) for n in objects]
    if len(bindings) != len(set(bindings)):
        raise ValueError("binding collision")
    if any(d not in nodes for n in objects for d in n["dependencies"]):
        raise ValueError("unresolved dependency")
    if (not isinstance(event, dict) or set(event) != {"object_key", "version", "disposition"}
            or not _text(event["object_key"]) or not _text(event["version"])
            or not _text(event["disposition"]) or event["disposition"] not in DISPOSITIONS):
        raise ValueError("event contract")
    source = event["object_key"]
    if source not in nodes:
        raise ValueError("unbound event")
    if not isinstance(completed_keys, (list, tuple, set)) or any(not _text(k) for k in completed_keys):
        raise ValueError("completion ledger contract")

    # Validate the entire bounded snapshot, including disconnected cycles.
    remaining, order = set(nodes), []
    while remaining:
        ready = [k for k in remaining if not (set(nodes[k]["dependencies"]) & remaining)]
        if not ready:
            raise ValueError("dependency cycle")
        key = min(ready, key=lambda k: (KINDS[nodes[k]["kind"]], k))
        order.append(key)
        remaining.remove(key)
    affected, ancestors = {source}, {}
    for key in order:
        ancestors[key] = set(nodes[key]["dependencies"])
        for dep in nodes[key]["dependencies"]:
            ancestors[key].update(ancestors[dep])
        if any(d in affected for d in nodes[key]["dependencies"]):
            affected.add(key)
    actions, blocked = [], set()
    for key in order:
        if key not in affected:
            continue
        node = nodes[key]
        # Upstream versions enter the key: downstream unchanged text can still be stale.
        lineage = [[d, nodes[d]["version"], nodes[d]["platform"], nodes[d]["binding_id"],
                    nodes[d]["owner"], nodes[d]["kind"]] for d in sorted(ancestors[key] | {key})]
        payload = [VERSION, source, nodes[source]["version"], event["disposition"], key, lineage]
        token = digest(json.dumps(payload, separators=(",", ":")))
        unavailable = [d for d in node["dependencies"] if nodes[d]["availability"] != "online"]
        if node["availability"] != "online" or unavailable or any(d in blocked for d in node["dependencies"]):
            state, gate = "deferred", "FRESH_PROVIDER_READ"
            blocked.add(key)
        elif token in completed_keys:
            state, gate = "unchanged", None
        else:
            state = "proposed"
            gate = "HUMAN_DECISION" if node["kind"] == "authority" else "VERSION_BOUND_EVIDENCE"
        actions.append({"object_key": key, "version": node["version"], "owner": node["owner"],
                        "platform": node["platform"], "idempotency_key": token,
                        "state": state, "next_gate": gate, "executable": False,
                        "requires": sorted(node["dependencies"]),
                        "operation": "prepare_change_receipt" if key == source else "review_dependency_impact"})
    return {"version": VERSION, "source_version": nodes[source]["version"],
            "event_version_stale": event["version"] != nodes[source]["version"],
            "actions": actions, "effects_executed": 0, "authority_effect": False}


def prepare_marked_update(current_text, expected_digest, entry):
    """Return replacement text only for the observed version; never write it."""
    if not all(isinstance(v, str) for v in (current_text, expected_digest, entry)):
        raise ValueError("text contract")
    if digest(current_text) != expected_digest:
        raise ValueError("concurrent edit")
    if not entry.strip() or START in entry or END in entry:
        raise ValueError("entry contract")
    ns, ne = current_text.count(START), current_text.count(END)
    if (ns or ne) and (ns != 1 or ne != 1 or current_text.index(START) > current_text.index(END)):
        raise ValueError("ambiguous markers")
    block = START + "\n" + entry + "\n" + END
    if ns:
        updated = current_text[:current_text.index(START)] + block + current_text[current_text.index(END) + len(END):]
    else:
        updated = current_text + ("\n\n" if current_text else "") + block
    return {"status": "unchanged" if updated == current_text else "prepared",
            "text": updated, "expected_digest": expected_digest, "effects_executed": 0}
