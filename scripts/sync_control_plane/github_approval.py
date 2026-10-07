"""Verify an exact-head human GitHub review before protected DB ingestion.

Only a dedicated approval-ingestor connection can write. This module never
creates GitHub reviews and a code PR approval does not automatically issue grants.
"""
from __future__ import annotations

import base64
import copy
import json
import re
from datetime import datetime, timezone
from urllib.parse import quote
from urllib.request import Request, build_opener, HTTPRedirectHandler

REPOSITORY = "Quirk-Systems/quirk-os"
REVIEWER_ID = 207279
REVIEWER_LOGIN = "bryansayler"
APPROVER = "human.bryan"
CONTRACT_FIELDS = ("manifest_key", "manifest_kind", "version", "canonical_uri", "authority_ceiling",
                   "domains", "tools", "inputs_schema_ref", "outputs_schema_ref", "trigger_contract",
                   "skill_refs", "rights_review", "eval_refs", "stop_conditions", "metadata")


def manifest_contract(manifest: dict) -> dict:
    defaults = {"domains": [], "tools": [], "skill_refs": [], "eval_refs": [],
                "stop_conditions": [], "metadata": {}}
    return {key: copy.deepcopy(manifest.get(key, defaults.get(key))) for key in CONTRACT_FIELDS}


def _instant(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("approval timestamps require timezone")
    return result.astimezone(timezone.utc)


def strict_json(raw: bytes) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    result = json.loads(raw, object_pairs_hook=unique)
    if not isinstance(result, dict):
        raise ValueError("approval document must be an object")
    return result


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward an authenticated request to a redirect destination.
        return None


class GitHubAPI:
    def __init__(self, token: str):
        self.token = token

    def get(self, path: str):
        # Callers construct paths; input cannot supply another API host.
        request = Request("https://api.github.com/repos/" + REPOSITORY + "/" + path,
                          headers={"Authorization": "Bearer " + self.token,
                                   "Accept": "application/vnd.github+json",
                                   "X-GitHub-Api-Version": "2022-11-28"})
        with build_opener(_NoRedirect()).open(request, timeout=20) as response:
            if response.geturl().split("/")[2] != "api.github.com":
                raise ValueError("unexpected GitHub redirect")
            return json.load(response)

    def document(self, path: str, commit: str) -> dict:
        if not re.fullmatch(r"[a-zA-Z0-9_./-]+\.json", path) or ".." in path.split("/"):
            raise ValueError("unsafe subject path")
        file = self.get("contents/" + quote(path, safe="/") + "?ref=" + commit)
        if file.get("type") != "file" or file.get("encoding") != "base64":
            raise ValueError("GitHub document is not an inline file")
        return strict_json(base64.b64decode(file["content"], validate=False))


def verified_record(api, pr_number: int, request_path: str, *, now: str) -> dict:
    if type(pr_number) is not int or pr_number <= 0:
        raise ValueError("invalid approval PR number")
    if not re.fullmatch(r"\.quirk/approval-requests/[a-z0-9._-]+\.json", request_path):
        raise ValueError("approval must use a dedicated request file")
    pr = api.get(f"pulls/{pr_number}")
    commit = pr["head"]["sha"]
    if not re.fullmatch(r"[a-f0-9]{40}", commit):
        raise ValueError("invalid request commit")
    if pr["base"]["repo"]["full_name"] != REPOSITORY or pr["base"]["ref"] != "main":
        raise ValueError("approval request must target canonical repository main")
    if pr.get("draft") is not False or not (pr.get("state") == "open" or pr.get("merged") is True):
        raise ValueError("approval PR must be ready or merged")
    request = api.document(request_path, commit)
    required = {"grant_id", "subject_kind", "subject_id", "subject_version", "subject_digest",
                "subject_path", "authority_ceiling", "allowed_actions", "requested_by", "approved_by",
                "decision_ref", "issued_at", "expires_at", "purpose"}
    if set(request) != required:
        raise ValueError("approval request fields must match the version 1 contract")
    if request["approved_by"] != APPROVER or request["requested_by"] == APPROVER:
        raise ValueError("approval requester must be distinct from designated human")
    if not isinstance(request["purpose"], str) or len(request["purpose"]) < 12:
        raise ValueError("approval requires a concrete purpose")
    if not re.fullmatch(r"grant\.[a-z0-9._-]+", request["grant_id"]):
        raise ValueError("invalid grant identity")
    if request_path != f".quirk/approval-requests/{request['grant_id']}.json":
        raise ValueError("request path must match grant identity")
    if not re.fullmatch(r"(?:agent|human|service|system)\.[a-z0-9._-]+", request["requested_by"]):
        raise ValueError("malformed requesting principal")
    if not isinstance(request["allowed_actions"], list) or not request["allowed_actions"] or any(
        not isinstance(a, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", a) for a in request["allowed_actions"]
    ) or len(set(request["allowed_actions"])) != len(request["allowed_actions"]):
        raise ValueError("invalid operation scope")
    instant = _instant(now)
    if not (_instant(request["issued_at"]) <= instant < _instant(request["expires_at"])):
        raise ValueError("approval request is not currently valid")
    subject = api.document(request["subject_path"], commit)
    if request["subject_kind"] == "skill":
        from .skill_runtime import manifest_digest, declared_actions, AUTHORITY_RANK
        digest = manifest_digest(subject)
        identity, version = subject.get("id"), subject.get("version")
        if request["authority_ceiling"] not in AUTHORITY_RANK or AUTHORITY_RANK[request["authority_ceiling"]] > AUTHORITY_RANK.get(subject.get("authority", {}).get("ceiling"), -1):
            raise ValueError("request exceeds subject authority")
        if not set(request["allowed_actions"]) <= declared_actions(subject):
            raise ValueError("request exceeds subject operations")
        contract = {}
    elif request["subject_kind"] == "manifest":
        digest = subject.get("content_hash")
        identity, version = subject.get("manifest_key"), subject.get("version")
        contract = manifest_contract(subject)
        if request["allowed_actions"] != ["activate_manifest"] or request["authority_ceiling"] != subject.get("authority_ceiling"):
            raise ValueError("manifest approval scope mismatch")
    else:
        raise ValueError("unknown approval subject kind")
    if (request["subject_id"], request["subject_version"], request["subject_digest"]) != (identity, version, digest):
        raise ValueError("approval subject binding mismatch")
    if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
        raise ValueError("invalid subject digest")
    # Paginate completely. Conservative latest-review semantics deny comments,
    # dismissal, and changes requested after an approval; a fresh approval restores it.
    reviews = []
    for page in range(1, 101):
        batch = api.get(f"pulls/{pr_number}/reviews?per_page=100&page={page}")
        if not isinstance(batch, list):
            raise ValueError("invalid GitHub review response")
        reviews.extend(batch)
        if len(batch) < 100:
            break
    else:
        raise ValueError("approval review pagination limit exceeded")
    human = [r for r in reviews if r.get("user", {}).get("id") == REVIEWER_ID and r.get("submitted_at")]
    if not human:
        raise ValueError("designated human has not approved")
    review = max(human, key=lambda r: (_instant(r["submitted_at"]), r["id"]))
    if review.get("state") != "APPROVED" or review.get("commit_id") != commit or review.get("user", {}).get("type") != "User" or review["user"].get("login") != REVIEWER_LOGIN:
        raise ValueError("latest designated human review does not approve exact request head")
    if _instant(review["submitted_at"]) > instant:
        raise ValueError("approval review is in the future")
    final_pr = api.get(f"pulls/{pr_number}")
    if final_pr["head"]["sha"] != commit or final_pr["base"] != pr["base"] or final_pr.get("draft") is not False or not (final_pr.get("state") == "open" or final_pr.get("merged") is True):
        raise ValueError("approval request changed during verification")
    record = {key: value for key, value in request.items() if key not in {"subject_path", "purpose"}}
    record.update(repository=REPOSITORY, request_commit=commit, request_path=request_path,
                  pr_number=pr_number, review_id=review["id"], reviewer_id=REVIEWER_ID,
                  reviewer_login=REVIEWER_LOGIN, verified_at=now, revoked_at=None, subject_contract=contract)
    return record


def ingest(connection, api, pr_number: int, request_path: str, *, now: str) -> dict:
    record = verified_record(api, pr_number, request_path, now=now)
    with connection.cursor() as cursor:
        cursor.execute("select current_user")
        if cursor.fetchone()[0] != "quirk_approval_ingestor":
            raise ValueError("dedicated approval-ingestor role is required")
        columns = tuple(record)
        values = tuple(json.dumps(record[k]) if k in {"allowed_actions", "subject_contract"} else record[k] for k in columns)
        placeholders = ["%s::jsonb" if k in {"allowed_actions", "subject_contract"} else "%s" for k in columns]
        # No upsert: changed bindings cannot revive/rewrite an existing grant.
        cursor.execute("insert into quirk_sync.github_approval_registry (" + ",".join(columns) + ") values (" + ",".join(placeholders) + ")", values)
    return record


def refresh(connection, api, grant_id: str, *, now: str) -> bool:
    """Recheck original exact review; sticky revocation on observed invalidation.

Transport outages do not refresh verified_at. The DB freshness cap denies use.
The trusted worker commits its transaction, and never shares its connection.
"""
    with connection.cursor() as cursor:
        cursor.execute("select current_user")
        if cursor.fetchone()[0] != "quirk_approval_ingestor":
            raise ValueError("dedicated approval-ingestor role is required")
        cursor.execute("select pr_number, request_path, request_commit, review_id, revoked_at from quirk_sync.github_approval_registry where grant_id=%s for update", (grant_id,))
        row = cursor.fetchone()
        if not row or row[4] is not None:
            return False
        try:
            record = verified_record(api, row[0], row[1], now=now)
            valid = (record["grant_id"], record["request_commit"], record["review_id"]) == (grant_id, row[2], row[3])
        except (ValueError, KeyError, TypeError):
            valid = False
        if valid:
            cursor.execute("update quirk_sync.github_approval_registry set verified_at=%s where grant_id=%s", (now, grant_id))
        else:
            cursor.execute("update quirk_sync.github_approval_registry set revoked_at=%s where grant_id=%s", (now, grant_id))
        return valid
