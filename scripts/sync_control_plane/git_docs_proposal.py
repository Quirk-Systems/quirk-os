"""Inert Git-template -> plain-text Docs request preparation; no credentials/writes.

Provider reads must come from an authenticated coordinator. Hash verification
binds bytes, not authorship, freshness, grants, or distributed transactions.
"""
import hashlib
import re
from .change_maintenance import START, END, digest, plan_changes, prepare_marked_update


def prepare_git_docs_proposal(*, repository, commit, path, blob_sha, source_text,
                              document_id, revision_id, tab_id, current_text,
                              expected_digest, owner):
    """Prepare a revision-leased batch for one verified plain-text tab.

    The caller must reject rich elements, suggestions, headers and other tabs
    before supplying normalized text. No effect or authority is admitted here.
    """
    for value in (repository, path, document_id, revision_id, tab_id, owner):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("binding required")
    if not re.fullmatch(r"[^/\s]+/[^/\s]+", repository):
        raise ValueError("repository identity")
    if path.startswith("/") or any(p in {"", ".", ".."} for p in path.split("/")):
        raise ValueError("source path")
    if not isinstance(commit, str) or not re.fullmatch(r"[a-f0-9]{40}", commit):
        raise ValueError("exact source commit required")
    if not isinstance(source_text, str):
        raise ValueError("source text")
    raw = source_text.encode("utf-8")
    actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if actual != blob_sha:
        raise ValueError("source blob mismatch")
    prepared = prepare_marked_update(current_text, expected_digest, source_text)
    source_version = commit + ":" + blob_sha + ":" + digest(source_text)
    target_version = revision_id + ":" + digest(current_text)
    nodes = [dict(object_key="template", version=source_version, kind="template",
                  platform="github", owner=owner, binding_id=repository + ":" + path,
                  dependencies=[], availability="online"),
             dict(object_key="document", version=target_version, kind="document",
                  platform="drive", owner=owner, binding_id=document_id + ":" + tab_id,
                  dependencies=["template"], availability="online")]
    plan = plan_changes(nodes, dict(object_key="template", version=source_version,
                                   disposition="proposed"))
    requests = []
    if prepared["status"] != "unchanged":
        # Docs ranges count UTF-16 code units, not Python code points.
        units = lambda s: len(s.encode("utf-16-le")) // 2
        if START in current_text:
            left = current_text.index(START)
            right = current_text.index(END) + len(END)
            index = 1 + units(current_text[:left])
            requests.append({"deleteContentRange": {"range": {
                "startIndex": index, "endIndex": 1 + units(current_text[:right]), "tabId": tab_id}}})
            replacement = START + "\n" + source_text + "\n" + END
        else:
            # The final Docs newline is structural; require an existing marked block.
            raise ValueError("marked block required for Docs adapter")
        requests.append({"insertText": {"location": {"index": index, "tabId": tab_id},
                                        "text": replacement}})
    return dict(plan=plan, source_ref=f"https://github.com/{repository}/blob/{commit}/{path}",
                source_blob=blob_sha, expected_document_version=target_version,
                prepared=prepared, batch=dict(document_id=document_id, requests=requests,
                                             write_control=dict(requiredRevisionId=revision_id)),
                executable=False, effects_executed=0,
                next_gate="INDEPENDENT_AUTHORITY_AND_SOURCE_REVALIDATION")
