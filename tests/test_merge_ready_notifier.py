import copy
import unittest
from unittest.mock import Mock

from scripts.notify_merge_ready import GitHub, blockers, marker, notify


def ready_pr():
    return {
        "state": "OPEN", "isDraft": False, "headRefOid": "a" * 40,
        "baseRefOid": "b" * 40, "mergeable": "MERGEABLE",
        "mergeStateStatus": "CLEAN", "reviewDecision": "APPROVED",
        "reviewThreads": {"nodes": [], "pageInfo": {"hasNextPage": False}},
        "commits": {"nodes": [{"commit": {"statusCheckRollup": {"state": "SUCCESS"}}}]},
    }


def runs():
    return [{"id": 1, "workflow_id": 7, "event": "pull_request",
             "head_sha": "a" * 40, "status": "completed", "conclusion": "success"}]


class MergeReadyNotifierTests(unittest.TestCase):
    def api(self):
        api = Mock(repository="Quirk-Systems/quirk-os")
        api.pull_request.return_value = ready_pr()
        api.runs.return_value = runs()
        api.pages.return_value = []
        return api

    def test_ready(self):
        self.assertEqual([], blockers(ready_pr(), runs()))

    def test_draft_reviews_and_mergeability_fail_closed(self):
        for field, value in [
            ("state", "CLOSED"), ("isDraft", True), ("isDraft", None),
            ("reviewDecision", "CHANGES_REQUESTED"), ("reviewDecision", None),
            ("mergeable", "UNKNOWN"), ("mergeStateStatus", "BEHIND"),
            ("mergeStateStatus", "BLOCKED"),
        ]:
            with self.subTest(field=field, value=value):
                pr = ready_pr()
                pr[field] = value
                self.assertTrue(blockers(pr, runs()))

    def test_incomplete_or_unresolved_review_threads(self):
        for threads in [{}, {"nodes": [{"isResolved": False}], "pageInfo": {"hasNextPage": False}},
                        {"nodes": [], "pageInfo": {"hasNextPage": True}}]:
            pr = ready_pr()
            pr["reviewThreads"] = threads
            self.assertTrue(blockers(pr, runs()))

    def test_missing_or_pending_checks(self):
        for rollup in [None, {"state": "PENDING"}, {"state": "FAILURE"}]:
            pr = ready_pr()
            pr["commits"]["nodes"][0]["commit"]["statusCheckRollup"] = rollup
            self.assertTrue(blockers(pr, runs()))

    def test_actions_without_checks_still_block(self):
        for status, conclusion in [
            ("completed", "action_required"), ("queued", None),
            ("completed", "failure"), ("completed", "cancelled"),
            ("completed", "skipped"),
        ]:
            run = runs()
            run[0].update(status=status, conclusion=conclusion)
            self.assertTrue(blockers(ready_pr(), run))
        self.assertTrue(blockers(ready_pr(), []))

    def test_latest_run_supersedes_failure_but_not_other_event(self):
        failed = runs()[0]
        failed["conclusion"] = "failure"
        passing = runs()[0]
        passing["id"] = 2
        self.assertEqual([], blockers(ready_pr(), [failed, passing]))
        passing["event"] = "push"
        self.assertTrue(blockers(ready_pr(), [failed, passing]))

    def test_old_sha_not_evidence(self):
        run = runs()
        run[0]["head_sha"] = "c" * 40
        self.assertTrue(blockers(ready_pr(), run))

    def test_comment_is_advisory_and_deduplicated(self):
        api = self.api()
        self.assertTrue(notify(api, 114))
        body = api.request.call_args.args[1]["body"]
        self.assertIn("does not authorize", body)
        api = self.api()
        api.pages.return_value = [{"user": {"login": "github-actions[bot]"},
                                  "body": marker(ready_pr())}]
        self.assertFalse(notify(api, 114))
        api.request.assert_not_called()

    def test_user_cannot_spoof_dedup_marker(self):
        api = self.api()
        api.pages.return_value = [{"user": {"login": "someone"}, "body": marker(ready_pr())}]
        self.assertTrue(notify(api, 114))

    def test_head_base_and_readiness_races_do_not_post(self):
        for field, value in [("headRefOid", "c" * 40), ("baseRefOid", "d" * 40),
                             ("reviewDecision", "CHANGES_REQUESTED")]:
            api = self.api()
            fresh = copy.deepcopy(ready_pr())
            fresh[field] = value
            api.pull_request.side_effect = [ready_pr(), fresh]
            self.assertFalse(notify(api, 114))
            api.request.assert_not_called()

    def test_pagination_fetches_all_comments(self):
        api = GitHub("test-placeholder", "Quirk-Systems/quirk-os")
        api.request = Mock(side_effect=[[{}] * 100, [{"body": "last"}]])
        self.assertEqual(101, len(api.pages("/comments")))
        self.assertIn("page=2", api.request.call_args.args[0])

    def test_pr114_snapshot_does_not_post(self):
        api = self.api()
        pr = ready_pr()
        pr.update(isDraft=True, reviewDecision="CHANGES_REQUESTED",
                  mergeStateStatus="UNSTABLE")
        api.pull_request.return_value = pr
        api.runs.return_value[0]["conclusion"] = "action_required"
        self.assertFalse(notify(api, 114))
        api.request.assert_not_called()

    def test_actions_search_cap_and_truncation_fail_closed(self):
        for count, batch in [(1000, [{}] * 100), (1001, [{}] * 100), (2, [{}])]:
            api = GitHub("test-placeholder", "Quirk-Systems/quirk-os")
            api.request = Mock(return_value={"total_count": count, "workflow_runs": batch})
            with self.subTest(count=count), self.assertRaises(RuntimeError):
                api.pages("/actions/runs?head_sha=" + "a" * 40, "workflow_runs")
