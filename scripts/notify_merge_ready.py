#!/usr/bin/env python3
"""Report conservative GitHub merge readiness; never merge or grant authority."""

import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen


QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      number state isDraft headRefOid baseRefOid mergeable mergeStateStatus
      reviewDecision
      reviewThreads(first: 100) {
        nodes { isResolved }
        pageInfo { hasNextPage }
      }
      commits(last: 1) {
        nodes { commit { statusCheckRollup { state } } }
      }
    }
  }
}
"""


class GitHub:
    def __init__(self, token, repository):
        self.token = token
        self.repository = repository

    def request(self, path, payload=None):
        request = Request(
            "https://api.github.com" + path,
            data=None if payload is None else json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": "Bearer " + self.token,
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        with urlopen(request, timeout=30) as response:
            result = json.load(response)
        if isinstance(result, dict) and result.get("errors"):
            raise RuntimeError("GitHub GraphQL query failed")
        return result

    def pages(self, path, key=None):
        rows = []
        expected_count = 0
        for page in range(1, 101):
            separator = "&" if "?" in path else "?"
            response = self.request(path + separator + urlencode({"per_page": 100, "page": page}))
            if key is not None:
                expected_count = max(expected_count, response["total_count"])
                if key == "workflow_runs" and expected_count >= 1000:
                    raise RuntimeError("Actions search limit reached; refusing incomplete readiness data")
            batch = response if key is None else response[key]
            rows.extend(batch)
            if len(batch) < 100:
                if len(rows) < expected_count:
                    raise RuntimeError("Incomplete GitHub pagination; refusing readiness notification")
                return rows
        raise RuntimeError("Pagination limit reached; refusing incomplete readiness data")

    def pull_request(self, number):
        owner, name = self.repository.split("/")
        result = self.request("/graphql", {
            "query": QUERY,
            "variables": {"owner": owner, "name": name, "number": number},
        })
        return result["data"]["repository"]["pullRequest"]

    def runs(self, sha):
        return self.pages(
            "/repos/" + self.repository + "/actions/runs?" + urlencode({"head_sha": sha}),
            "workflow_runs",
        )


def blockers(pr, runs):
    reasons = []
    if not pr or pr.get("state") != "OPEN":
        return ["PR is not open"]
    if pr.get("isDraft") is not False:
        reasons.append("PR is draft")
    if pr.get("mergeable") != "MERGEABLE" or pr.get("mergeStateStatus") != "CLEAN":
        reasons.append("GitHub mergeability is not clean")
    # Deliberately conservative even on branches with no approval requirement.
    if pr.get("reviewDecision") != "APPROVED":
        reasons.append("required review approval is absent")
    threads = pr.get("reviewThreads", {})
    if (threads.get("pageInfo", {}).get("hasNextPage") is not False
            or any(not thread.get("isResolved") for thread in threads.get("nodes", []))):
        reasons.append("review threads are unresolved or incomplete")
    commits = pr.get("commits", {}).get("nodes", [])
    rollup = commits[-1].get("commit", {}).get("statusCheckRollup") if commits else None
    if not rollup or rollup.get("state") != "SUCCESS":
        reasons.append("head checks have not succeeded")
    # Approval-blocked Actions runs may have no check runs or rollup entries.
    latest = {}
    for run in runs:
        if run.get("head_sha") != pr.get("headRefOid"):
            continue
        key = (run["workflow_id"], run["event"])
        if key not in latest or run["id"] > latest[key]["id"]:
            latest[key] = run
    if not latest:
        reasons.append("no Actions evidence for head")
    if any(run.get("status") != "completed" or run.get("conclusion") != "success"
           for run in latest.values()):
        reasons.append("Actions are pending, blocked, or unsuccessful")
    return reasons


def marker(pr):
    return "<!-- quirk-merge-ready:" + pr["headRefOid"] + ":" + pr["baseRefOid"] + " -->"


def notify(api, number):
    pr = api.pull_request(number)
    reasons = blockers(pr, api.runs(pr["headRefOid"])) if pr else ["PR is missing"]
    if reasons:
        print("PR #" + str(number) + ": not ready — " + "; ".join(reasons))
        return False
    path = "/repos/" + api.repository + "/issues/" + str(number) + "/comments"
    comments = api.pages(path)
    if any(comment.get("user", {}).get("login") == "github-actions[bot]"
           and marker(pr) in (comment.get("body") or "") for comment in comments):
        print("PR #" + str(number) + ": already notified for this head/base")
        return False
    # Re-read immediately before posting; old checks/reviews cannot attest a new head.
    fresh = api.pull_request(number)
    if (not fresh or fresh.get("headRefOid") != pr["headRefOid"]
            or fresh.get("baseRefOid") != pr["baseRefOid"]
            or blockers(fresh, api.runs(fresh["headRefOid"]))):
        print("PR #" + str(number) + ": readiness changed; no notification")
        return False
    api.request(path, {"body": marker(pr) + "\n"
        "GitHub merge-readiness checks passed for head `" + pr["headRefOid"]
        + "` against base `" + pr["baseRefOid"] + "` at notification time. "
        "This is advisory and may become stale. A human must recheck before merging. "
        "This notification does not authorize merge, admission, activation, or deployment."})
    print("PR #" + str(number) + ": notified")
    return True


def main():
    api = GitHub(os.environ["GH_TOKEN"], os.environ["GITHUB_REPOSITORY"])
    for pr in api.pages("/repos/" + api.repository + "/pulls?state=open"):
        notify(api, pr["number"])


if __name__ == "__main__":
    main()
