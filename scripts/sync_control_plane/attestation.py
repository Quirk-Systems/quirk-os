"""Live GitHub approval resolution for ADR-0002.

Only the host may install policy/transport dependencies. Passing a dictionary
from the submitted manifest as policy is not a supported trust boundary.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
from datetime import datetime, timezone
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .content import HASH_PROFILE, manifest_content_hash, strict_json_loads


MAX_GITHUB_REQUESTS = 64


class ApprovalError(ValueError):
    pass


class _NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class GitHubReader:
    """GET-only fixed-origin transport. Credentials never follow redirects."""
    def __init__(self, token: str):
        if not token:
            raise ApprovalError("authenticated GitHub reader required")
        self._token = token

    def get(self, endpoint: str):
        if not endpoint.startswith("/repos/") or ".." in endpoint or "#" in endpoint:
            raise ApprovalError("invalid GitHub endpoint")
        request = Request("https://api.github.com" + endpoint, headers={
            "Authorization": "Bearer " + self._token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        try:
            with build_opener(_NoRedirects()).open(request, timeout=20) as response:
                raw = response.read(1_048_577)
            if len(raw) > 1_048_576:
                raise ApprovalError("GitHub response exceeds bound")
            return strict_json_loads(raw)
        except Exception as exc:
            # Do not echo headers, credentials or provider response bodies.
            raise ApprovalError("GitHub resolution unavailable or invalid") from exc


def _time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ApprovalError("approval timestamps require a timezone")
    return parsed.astimezone(timezone.utc)


def decision_ref(repository: str, pr_number: int, review_id: int) -> str:
    return f"https://github.com/{repository}/pull/{pr_number}#pullrequestreview-{review_id}"


def grant_ref(review_id: int, subject: dict) -> str:
    raw = json.dumps(subject, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return f"grant.github.review.{review_id}." + hashlib.sha256(raw.encode()).hexdigest()


def approval_subject(body: str) -> dict:
    # A deliberately narrow consent format: the entire review is one exact,
    # unindented fence. Prose, quoted/list/HTML examples, nested/longer fences,
    # and incomplete or multiple blocks cannot convey consent accidentally.
    match = re.fullmatch(r"```quirk-manifest-approval[ \t]*\r?\n(.*?)\r?\n```[ \t]*", body.strip("\r\n"), re.S)
    if match is None:
        raise ApprovalError("one explicit manifest approval block occupying the entire review required")
    subject = strict_json_loads(match[1])
    from jsonschema import Draft202012Validator, FormatChecker
    from pathlib import Path
    schema = strict_json_loads((Path(__file__).resolve().parents[2] /
                               "schemas/manifest-approval-attestation.schema.json").read_bytes())
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(subject))
    if errors:
        raise ApprovalError("approval record schema: " + errors[0].message)
    return subject


class GitHubApprovalVerifier:
    """Uses an admitted host policy and live authenticated reader, never input claims."""
    def __init__(self, policy: dict, reader):
        self.policy = strict_json_loads(json.dumps(policy, allow_nan=False))
        self.reader = reader
        self._trees = {}
        self._requests = 0

    def _get(self, endpoint: str):
        # Count before transport, including failed calls. Each verification has
        # a fixed aggregate authenticated request budget, independent of input.
        if self._requests >= MAX_GITHUB_REQUESTS:
            raise ApprovalError("GitHub request budget exceeded")
        self._requests += 1
        return self.reader.get(endpoint)

    @staticmethod
    def _identity(pr: dict) -> tuple:
        return tuple((pr[side]["sha"], pr[side]["ref"],
                      pr[side]["repo"]["full_name"], pr[side]["repo"]["id"])
                     for side in ("base", "head")) + (pr["user"]["id"],)

    def _file(self, root: str, path: str, revision: str) -> bytes:
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise ApprovalError("immutable source revision required")
        if not isinstance(path, str) or not path or path.startswith("/") or "\\" in path or any(ord(c) < 32 for c in path) or any(p in ("", ".", "..") for p in path.split("/")):
            raise ApprovalError("invalid source path")
        tree_key = (root, revision)
        if tree_key not in self._trees:
            tree = self._get(f"{root}/git/trees/{revision}?recursive=1")
            if tree.get("truncated") is not False or not isinstance(tree.get("tree"), list):
                raise ApprovalError("complete immutable source tree required")
            self._trees[tree_key] = {entry["path"]: entry for entry in tree["tree"]}
        entry = self._trees[tree_key].get(path, {})
        if entry.get("type") != "blob" or entry.get("mode") not in ("100644", "100755"):
            raise ApprovalError("source must be a regular Git file")
        result = self._get(f"{root}/contents/{quote(path, safe='/')}?ref={revision}")
        if result.get("type") != "file" or result.get("encoding") != "base64":
            raise ApprovalError("source must be a regular file")
        if result.get("sha") != entry["sha"]:
            raise ApprovalError("source response does not match immutable Git tree")
        return base64.b64decode(result["content"].replace("\n", ""), validate=True)

    def verify(self, manifest: dict, context: dict, *, now: datetime | None = None) -> dict:
        self._requests = 0
        self._trees = {}
        try:
            return self._verify(manifest, context, now or datetime.now(timezone.utc))
        except ApprovalError:
            raise
        except Exception as exc:
            raise ApprovalError("approval resolution invalid or incomplete") from exc

    def _verify(self, manifest: dict, context: dict, now: datetime) -> dict:
        policy = self.policy
        if policy.get("enabled") is not True or policy.get("protection_verified") is not True:
            raise ApprovalError("verifier policy is not admitted; bootstrap required")
        revoked = policy.get("revoked_review_ids", [])
        if not isinstance(revoked, list) or any(type(value) is not int or value <= 0 for value in revoked):
            raise ApprovalError("revoked_review_ids must be a list of positive integers")
        repo = policy["repository"]
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise ApprovalError("invalid trusted repository")
        root = f"/repos/{repo}"
        pr_number, review_id = context["pr_number"], context["review_id"]
        if type(pr_number) is not int or type(review_id) is not int or min(pr_number, review_id) < 1:
            raise ApprovalError("invalid review identity")
        pr = self._get(f"{root}/pulls/{pr_number}")
        if pr.get("state") != "open" or pr.get("draft") or pr.get("merged"):
            raise ApprovalError("open reviewable candidate required")
        head, base = pr["head"]["sha"], pr["base"]["sha"]
        if pr["base"]["ref"] != policy["base_branch"]:
            raise ApprovalError("unapproved target branch")
        if pr["base"]["repo"]["full_name"] != repo or pr["head"]["repo"]["full_name"] != repo:
            raise ApprovalError("cross-repository activation is unsupported")
        identity = self._identity(pr)
        review = self._get(f"{root}/pulls/{pr_number}/reviews/{review_id}")
        if review["state"] != "APPROVED" or review["commit_id"] != head or not review.get("submitted_at"):
            raise ApprovalError("current exact-head approved review required")
        author = review["user"]
        principal = policy["human_principals"].get(str(author["id"]))
        if author.get("type") != "User" or not principal or not re.fullmatch(r"human\.[a-z0-9._-]+", principal):
            raise ApprovalError("reviewer is not an authorized human")
        if author["login"] != policy["human_logins"].get(str(author["id"])):
            raise ApprovalError("reviewer identity mapping changed")
        if author["id"] == pr["user"]["id"]:
            raise ApprovalError("PR author may not approve its own activation")
        owners = self._file(root, ".github/CODEOWNERS", base)
        if hashlib.sha256(owners).hexdigest() != policy["codeowners_sha256"]:
            raise ApprovalError("base ownership policy changed or unadmitted")
        # Initial scope intentionally supports one explicit universal owner only.
        # A broader CODEOWNERS grammar needs a separately tested policy revision.
        lines = [line.strip() for line in owners.decode().splitlines()
                 if line.strip() and not line.lstrip().startswith("#")]
        expected = [f"* @{author['login']}", f"/.github/CODEOWNERS @{author['login']}"]
        if lines != expected:
            raise ApprovalError("unsupported or missing CODEOWNER coverage")
        subject = approval_subject(review["body"])
        digest = manifest_content_hash(manifest)
        expected_fields = {
            "repository": repo, "pr_number": pr_number, "head_sha": head, "base_sha": base,
            "manifest_key": manifest["manifest_key"], "manifest_version": manifest["version"],
            "hash_profile": HASH_PROFILE, "content_hash": digest,
            "authority_ceiling": manifest["authority_ceiling"],
            "action": "activate_manifest", "to_status": "active", "requested_status": "active",
        }
        for field in ("manifest_path", "environment", "requested_by", "from_status", "allowed_actions", "object_scope"):
            expected_fields[field] = context[field]
        for key, value in expected_fields.items():
            if subject.get(key) != value:
                raise ApprovalError("approval scope mismatch: " + key)
        for field in ("allowed_actions", "object_scope"):
            actual = sorted({value for tool in manifest.get("tools", []) for value in tool.get(field, [])})
            if subject[field] != actual:
                raise ApprovalError("approval capability scope differs from manifest: " + field)
        if subject["evaluation_ref"] not in manifest.get("eval_refs", []) or subject["evaluation_ref"] not in subject["evidence_refs"]:
            raise ApprovalError("approval evidence must include the manifest evaluation")
        if subject["environment"] not in policy["environments"]:
            raise ApprovalError("unadmitted target environment")
        if subject["requested_by"] == principal or str(author["id"]) == str(context.get("requester_github_id")):
            raise ApprovalError("requester may not approve its own activation")
        if subject["from_status"] not in ("candidate", "paused", "active"):
            raise ApprovalError("illegal activation transition")
        if not _time(subject["valid_from"]) <= now < _time(subject["expires_at"]):
            raise ApprovalError("approval expired or not yet valid")
        # The review body is composed before GitHub assigns submitted_at. An
        # earlier requested start is harmless: authority begins only after
        # the actual submitted review, whose timestamp becomes decided_at.
        if _time(review["submitted_at"]) > now:
            raise ApprovalError("invalid approval validity interval")
        if review_id in revoked:
            raise ApprovalError("approval revoked")
        source = strict_json_loads(self._file(root, subject["manifest_path"], head))
        if source.get("status") not in ("candidate", "paused") or source.get("admission") is not None:
            raise ApprovalError("review source must be an unadmitted candidate")
        if source["content_hash"] != digest or manifest_content_hash(source) != digest:
            raise ApprovalError("reviewed source content differs from submitted content")
        evaluation = strict_json_loads(self._file(root, subject["evaluation_ref"], head))
        from jsonschema import Draft202012Validator, FormatChecker
        from pathlib import Path
        evaluation_schema = strict_json_loads((Path(__file__).resolve().parents[2] /
                                               "schemas/manifest-evaluation.schema.json").read_bytes())
        if list(Draft202012Validator(evaluation_schema, format_checker=FormatChecker()).iter_errors(evaluation)):
            raise ApprovalError("invalid manifest evaluation record")
        eval_subject = {"schema_version": "manifest-evaluation.v1", "manifest_key": manifest["manifest_key"],
                        "manifest_version": manifest["version"], "hash_profile": HASH_PROFILE,
                        "content_hash": digest, "decision": "pass", "authority_effect": "none"}
        if any(evaluation.get(k) != v for k, v in eval_subject.items()) or not evaluation.get("materials"):
            raise ApprovalError("evaluation does not bind reviewed content")
        for material in evaluation["materials"]:
            actual = self._file(root, material["path"], head)
            if hashlib.sha256(actual).hexdigest() != material["sha256"]:
                raise ApprovalError("evaluation material digest mismatch")
        reviews = []
        for page in range(1, 21):
            batch = self._get(f"{root}/pulls/{pr_number}/reviews?per_page=100&page={page}")
            if not isinstance(batch, list):
                raise ApprovalError("invalid review census")
            reviews.extend(batch)
            if len(batch) < 100:
                break
        else:
            raise ApprovalError("review census exceeds bound")
        if not any(r["id"] == review_id and r["state"] == "APPROVED" for r in reviews):
            raise ApprovalError("selected approval is no longer current")
        scoped = []
        for item in reviews:
            if str(item["user"]["id"]) not in policy["human_principals"]:
                continue
            if item["id"] != review_id and item.get("submitted_at") and _time(item["submitted_at"]) >= _time(review["submitted_at"]):
                if item["state"] == "CHANGES_REQUESTED" or "quirk-manifest-revocation" in item.get("body", ""):
                    raise ApprovalError("approval superseded or revoked by later review")
            if item["state"] == "APPROVED" and item["commit_id"] == head and "quirk-manifest-approval" in item.get("body", ""):
                other = approval_subject(item["body"])
                if other["manifest_key"] == subject["manifest_key"]:
                    scoped.append(item["id"])
        if scoped != [review_id]:
            raise ApprovalError("ambiguous activation approvals")
        # Re-read immediately before yielding: head/base/review changes during
        # resolution invalidate the observation; no cross-provider atomicity claim.
        final = self._get(f"{root}/pulls/{pr_number}")
        final_review = self._get(f"{root}/pulls/{pr_number}/reviews/{review_id}")
        if self._identity(final) != identity or final.get("state") != "open" or final.get("draft") or final.get("merged"):
            raise ApprovalError("candidate changed during verification")
        if final_review != review:
            raise ApprovalError("review changed during verification")
        return {"schema_version": "verified-manifest-approval.v1", "subject": subject,
                "decision_ref": decision_ref(repo, pr_number, review_id),
                "authority_grant_ref": grant_ref(review_id, subject),
                "transition_ref": f"transition.github.review.{review_id}",
                "approved_by": principal, "reviewer_account_id": author["id"],
                "decided_at": review["submitted_at"], "verified_at": now.isoformat(),
                "database_verification": "projection", "authority_effect": "none"}
